import streamlit as st
import ee
import folium
from streamlit_folium import st_folium
from datetime import datetime
import json
import base64
import tempfile
import os

from services.sustainability_report import generate_comprehensive_report
from services.gee_core import auto_initialize_gee
from india_cities import INDIA_DATA as INDIA_CITIES
from components.ui import apply_enhanced_css, render_page_header, render_stat_card
from components.maps import create_base_map, add_tile_layer, add_layer_control

import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
import numpy as np

st.set_page_config(layout="wide", page_title="Comprehensive Sustainability Report", page_icon="📊")

apply_enhanced_css()

st.markdown("""
<style>
    .uss-gauge {
        text-align: center;
        padding: 2rem;
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        border-radius: 20px;
        border: 2px solid rgba(56, 189, 248, 0.3);
        box-shadow: 0 10px 40px rgba(0,0,0,0.4);
    }
    .uss-value {
        font-size: 5rem;
        font-weight: 800;
        background: linear-gradient(135deg, #38bdf8, #22c55e);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-shadow: 0 0 40px rgba(56, 189, 248, 0.3);
    }
    .uss-label {
        font-size: 1.2rem;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 3px;
        margin-bottom: 0.5rem;
    }
    .uss-class {
        font-size: 1.8rem;
        font-weight: 700;
        margin-top: 0.5rem;
        padding: 0.5rem 1.5rem;
        border-radius: 50px;
        display: inline-block;
    }
    .module-card {
        background: rgba(15, 23, 42, 0.8);
        border-radius: 15px;
        padding: 1.5rem;
        border: 1px solid rgba(255,255,255,0.1);
        text-align: center;
        transition: all 0.3s;
    }
    .module-card:hover {
        border-color: rgba(56, 189, 248, 0.5);
        transform: translateY(-5px);
    }
    .module-score {
        font-size: 2.5rem;
        font-weight: 700;
    }
    .module-grade {
        font-size: 1.2rem;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        display: inline-block;
        margin-top: 0.5rem;
    }
    .module-label {
        font-size: 0.9rem;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-top: 0.5rem;
    }
    .section-title {
        font-size: 1.5rem;
        font-weight: 700;
        color: #f1f5f9;
        margin: 2rem 0 1rem 0;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid rgba(56, 189, 248, 0.3);
    }
    .metric-table {
        width: 100%;
        border-collapse: collapse;
        margin: 1rem 0;
    }
    .metric-table th, .metric-table td {
        padding: 0.75rem 1rem;
        text-align: left;
        border-bottom: 1px solid rgba(255,255,255,0.1);
    }
    .metric-table th {
        background: rgba(15, 23, 42, 0.8);
        color: #94a3b8;
        text-transform: uppercase;
        font-size: 0.8rem;
        letter-spacing: 1px;
    }
    .metric-table td {
        color: #e2e8f0;
    }
    .status-good { color: #22c55e; }
    .status-moderate { color: #eab308; }
    .status-poor { color: #f97316; }
    .status-critical { color: #ef4444; }
    .roadmap-phase {
        background: rgba(15, 23, 42, 0.6);
        border-left: 4px solid #38bdf8;
        padding: 1rem 1.5rem;
        margin: 1rem 0;
        border-radius: 0 8px 8px 0;
    }
    .roadmap-title {
        font-weight: 700;
        color: #38bdf8;
        margin-bottom: 0.5rem;
    }
    .insight-box {
        background: rgba(34, 197, 94, 0.1);
        border: 1px solid rgba(34, 197, 94, 0.3);
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    .warning-box {
        background: rgba(249, 115, 22, 0.1);
        border: 1px solid rgba(249, 115, 22, 0.3);
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

auto_initialize_gee()

render_page_header(
    "📊 Comprehensive Sustainability Report",
    "Multi-dimensional environmental assessment combining vegetation, air quality, urban heat, and predictive analytics"
)

if 'report_data' not in st.session_state:
    st.session_state.report_data = None
if 'report_geometry' not in st.session_state:
    st.session_state.report_geometry = None
if 'report_center' not in st.session_state:
    st.session_state.report_center = [20.5937, 78.9629]
if 'preview_geojson' not in st.session_state:
    st.session_state.preview_geojson = None
if 'preview_center' not in st.session_state:
    st.session_state.preview_center = [20.5937, 78.9629]
if 'preview_zoom' not in st.session_state:
    st.session_state.preview_zoom = 5
if 'preview_region_name' not in st.session_state:
    st.session_state.preview_region_name = None

with st.sidebar:
    st.markdown("### 📍 Report Parameters")
    
    analysis_type = st.radio(
        "Area Selection Method",
        ["City/State", "Upload Shapefile/GeoJSON"],
        horizontal=True
    )
    
    geometry = None
    region_name = "Selected Region"
    center_coords = [20.5937, 78.9629]
    
    if analysis_type == "City/State":
        state = st.selectbox("State", sorted(list(INDIA_CITIES.keys())), index=0)
        cities = sorted(list(INDIA_CITIES[state].keys()))
        city = st.selectbox("City/District", cities, index=0)
        
        buffer_km = st.slider("Analysis Radius (km)", 5, 50, 15)
        
        if city:
            coords = INDIA_CITIES[state][city]
            center_coords = [coords["lat"], coords["lon"]]
            geometry = ee.Geometry.Point([coords["lon"], coords["lat"]]).buffer(buffer_km * 1000)
            region_name = f"{city}, {state}"
            st.session_state.report_center = center_coords
            
            from shapely.geometry import Point
            circle_geojson = Point(coords["lon"], coords["lat"]).buffer(buffer_km / 111.0).__geo_interface__
            st.session_state.preview_geojson = circle_geojson
            st.session_state.preview_center = center_coords
            st.session_state.preview_zoom = max(8, 12 - buffer_km // 10)
            st.session_state.preview_region_name = region_name
    else:
        uploaded_file = st.file_uploader(
            "Upload GeoJSON or Shapefile (.zip)",
            type=["geojson", "json", "zip"]
        )
        
        if uploaded_file:
            try:
                if uploaded_file.name.endswith(('.geojson', '.json')):
                    gdf = gpd.read_file(uploaded_file)
                elif uploaded_file.name.endswith('.zip'):
                    with tempfile.TemporaryDirectory() as tmpdir:
                        zip_path = os.path.join(tmpdir, "upload.zip")
                        with open(zip_path, 'wb') as f:
                            f.write(uploaded_file.getvalue())
                        import zipfile
                        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                            zip_ref.extractall(tmpdir)
                        shp_files = [f for f in os.listdir(tmpdir) if f.endswith('.shp')]
                        if shp_files:
                            gdf = gpd.read_file(os.path.join(tmpdir, shp_files[0]))
                        else:
                            st.error("No .shp file found in zip")
                            gdf = None
                else:
                    gdf = None
                    
                if gdf is not None and len(gdf) > 0:
                    if gdf.crs and gdf.crs != "EPSG:4326":
                        gdf = gdf.to_crs("EPSG:4326")
                    
                    combined_geom = gdf.geometry.unary_union
                    centroid = combined_geom.centroid
                    center_coords = [centroid.y, centroid.x]
                    
                    geojson_dict = json.loads(gdf.to_json())
                    features = geojson_dict.get('features', [])
                    if features:
                        geom = features[0]['geometry']
                        geometry = ee.Geometry(geom)
                        region_name = "Uploaded Region"
                        st.session_state.report_center = center_coords
                        st.success(f"Loaded {len(gdf)} features")
                        
                        combined_geojson = combined_geom.__geo_interface__
                        st.session_state.preview_geojson = combined_geojson
                        st.session_state.preview_center = center_coords
                        bounds = combined_geom.bounds
                        extent = max(bounds[2] - bounds[0], bounds[3] - bounds[1])
                        st.session_state.preview_zoom = max(6, min(12, int(10 - extent * 2)))
                        st.session_state.preview_region_name = region_name
                        
            except Exception as e:
                st.error(f"Error reading file: {e}")
        
        buffer_km = 0
    
    st.markdown("---")
    
    year = st.selectbox("Analysis Year", list(range(2024, 2017, -1)), index=0)
    
    st.markdown("---")
    
    generate_btn = st.button("🚀 Generate Report", type="primary", use_container_width=True)

if st.session_state.preview_geojson and not st.session_state.report_data:
    st.markdown("### 📍 Selected Area Preview")
    
    preview_map = create_base_map(
        st.session_state.preview_center[0], 
        st.session_state.preview_center[1], 
        zoom=st.session_state.preview_zoom
    )
    
    folium.GeoJson(
        st.session_state.preview_geojson,
        name="Selected Area",
        style_function=lambda x: {
            'fillColor': '#38bdf8',
            'color': '#f97316',
            'weight': 3,
            'fillOpacity': 0.15
        }
    ).add_to(preview_map)
    
    folium.Marker(
        location=st.session_state.preview_center,
        popup=st.session_state.preview_region_name or "Selected Location",
        icon=folium.Icon(color='orange', icon='info-sign')
    ).add_to(preview_map)
    
    add_layer_control(preview_map)
    st_folium(preview_map, height=400, use_container_width=True, key="preview_map")
    
    if st.session_state.preview_region_name:
        st.info(f"Selected region: **{st.session_state.preview_region_name}**. Click 'Generate Report' in the sidebar to analyze this area.")

if generate_btn and geometry:
    with st.spinner(f"Analyzing {region_name}... This may take 1-2 minutes."):
        try:
            report_data = generate_comprehensive_report(
                geometry, 
                region_name=region_name, 
                year=year,
                buffer_km=buffer_km
            )
            st.session_state.report_data = report_data
            st.session_state.report_geometry = geometry
            st.success("Report generated successfully!")
        except Exception as e:
            st.error(f"Error generating report: {str(e)}")
            st.session_state.report_data = None

elif generate_btn and not geometry:
    st.warning("Please select a valid region first.")

if st.session_state.report_data:
    report = st.session_state.report_data
    scores = report['scores']
    
    st.markdown(f"<h2 style='text-align: center; color: #94a3b8; margin-bottom: 2rem;'>📍 {report['region_name']} | {report['year']}</h2>", unsafe_allow_html=True)
    
    col_uss, col_modules = st.columns([1, 2])
    
    with col_uss:
        st.markdown(f"""
        <div class="uss-gauge">
            <div class="uss-label">Urban Sustainability Score</div>
            <div class="uss-value">{scores['total_uss']:.0f}</div>
            <div class="uss-class" style="background: {scores['class_color']}20; color: {scores['class_color']};">
                {scores['classification']}
            </div>
            <p style="color: #94a3b8; margin-top: 1rem; font-size: 0.9rem;">{scores['class_desc']}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col_modules:
        m_cols = st.columns(4)
        
        modules = [
            ("🌿 Vegetation", scores['vegetation']),
            ("💨 Air Quality", scores['aqi']),
            ("🌡️ Urban Heat", scores['heat']),
            ("🔮 Future Risk", scores['prediction'])
        ]
        
        for i, (name, data) in enumerate(modules):
            with m_cols[i]:
                st.markdown(f"""
                <div class="module-card">
                    <div class="module-score" style="color: {data['color']};">{data['score']:.1f}</div>
                    <div style="font-size: 0.8rem; color: #64748b;">/25</div>
                    <div class="module-grade" style="background: {data['color']}20; color: {data['color']};">
                        Grade {data['grade']}
                    </div>
                    <div class="module-label">{name}</div>
                    <div style="font-size: 0.75rem; color: #64748b; margin-top: 0.5rem;">
                        {data['metric']}: {data['value']:.2f}
                    </div>
                </div>
                """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    st.markdown('<div class="section-title">🗺️ Environmental Maps</div>', unsafe_allow_html=True)
    
    map_cols = st.columns(2)
    
    tile_urls = report.get('tile_urls', {})
    
    center = st.session_state.report_center
    
    with map_cols[0]:
        st.markdown("**NDVI - Vegetation Health**")
        m1 = create_base_map(center[0], center[1], zoom=10)
        if 'ndvi' in tile_urls and tile_urls['ndvi']:
            add_tile_layer(m1, tile_urls['ndvi'], "NDVI", opacity=0.8)
        add_layer_control(m1)
        st_folium(m1, height=300, use_container_width=True, key="map_ndvi")
        
    with map_cols[1]:
        st.markdown("**Land Use/Land Cover**")
        m2 = create_base_map(center[0], center[1], zoom=10)
        if 'lulc' in tile_urls and tile_urls['lulc']:
            add_tile_layer(m2, tile_urls['lulc'], "LULC", opacity=0.8)
        add_layer_control(m2)
        st_folium(m2, height=300, use_container_width=True, key="map_lulc")
    
    map_cols2 = st.columns(2)
    
    with map_cols2[0]:
        st.markdown("**PM2.5 Concentration**")
        m3 = create_base_map(center[0], center[1], zoom=10)
        if 'pm25' in tile_urls and tile_urls['pm25']:
            add_tile_layer(m3, tile_urls['pm25'], "PM2.5", opacity=0.8)
        add_layer_control(m3)
        st_folium(m3, height=300, use_container_width=True, key="map_pm25")
        
    with map_cols2[1]:
        st.markdown("**Land Surface Temperature**")
        m4 = create_base_map(center[0], center[1], zoom=10)
        if 'lst' in tile_urls and tile_urls['lst']:
            add_tile_layer(m4, tile_urls['lst'], "LST", opacity=0.8)
        add_layer_control(m4)
        st_folium(m4, height=300, use_container_width=True, key="map_lst")
    
    st.markdown("---")
    
    st.markdown('<div class="section-title">📈 Score Analysis</div>', unsafe_allow_html=True)
    
    chart_cols = st.columns(2)
    
    with chart_cols[0]:
        score_data = {
            'Module': ['Vegetation', 'Air Quality', 'Urban Heat', 'Future Risk'],
            'Score': [scores['vegetation']['score'], scores['aqi']['score'], 
                     scores['heat']['score'], scores['prediction']['score']],
            'Max': [25, 25, 25, 25]
        }
        
        fig, ax = plt.subplots(figsize=(8, 5), facecolor='#0f172a')
        ax.set_facecolor('#0f172a')
        
        colors = [scores['vegetation']['color'], scores['aqi']['color'], 
                  scores['heat']['color'], scores['prediction']['color']]
        
        bars = ax.barh(score_data['Module'], score_data['Score'], color=colors, height=0.6)
        ax.barh(score_data['Module'], [25-s for s in score_data['Score']], 
                left=score_data['Score'], color='#1e293b', height=0.6)
        
        for bar, score in zip(bars, score_data['Score']):
            ax.text(score + 0.5, bar.get_y() + bar.get_height()/2, 
                   f'{score:.1f}/25', va='center', color='#f1f5f9', fontsize=10)
        
        ax.set_xlim(0, 25)
        ax.set_xlabel('Score', color='#94a3b8')
        ax.tick_params(colors='#94a3b8')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_color('#475569')
        ax.spines['left'].set_color('#475569')
        
        plt.tight_layout()
        st.pyplot(fig)
        plt.close()
    
    with chart_cols[1]:
        if report.get('lulc_stats') and 'classes' in report['lulc_stats']:
            lulc_classes = report['lulc_stats']['classes']
            labels = list(lulc_classes.keys())
            sizes = [lulc_classes[k]['percentage'] for k in labels]
            
            lulc_colors = {
                'Water': '#419BDF', 'Trees': '#397D49', 'Grass': '#88B053',
                'Flooded Vegetation': '#7A87C6', 'Crops': '#E49635',
                'Shrub & Scrub': '#DFC35A', 'Built Area': '#C4281B',
                'Bare Ground': '#A59B8F', 'Snow & Ice': '#B39FE1'
            }
            colors = [lulc_colors.get(l, '#888888') for l in labels]
            
            fig, ax = plt.subplots(figsize=(8, 5), facecolor='#0f172a')
            pie_result = ax.pie(
                sizes, labels=None, autopct='%1.1f%%',
                colors=colors, startangle=90,
                textprops={'color': '#f1f5f9', 'fontsize': 8}
            )
            wedges = pie_result[0]
            ax.legend(wedges, labels, loc='center left', bbox_to_anchor=(1, 0.5),
                     fontsize=8, facecolor='#0f172a', edgecolor='#475569',
                     labelcolor='#f1f5f9')
            ax.set_title('Land Use Distribution', color='#f1f5f9', fontsize=12)
            plt.tight_layout()
            st.pyplot(fig)
            plt.close()
        else:
            st.info("LULC distribution data not available")
    
    st.markdown("---")
    
    st.markdown('<div class="section-title">📋 Detailed Analysis</div>', unsafe_allow_html=True)
    
    st.markdown(report['text_sections']['overview'])
    
    with st.expander("🌿 Vegetation & Land Use Analysis", expanded=True):
        st.markdown(report['text_sections']['analysis']['vegetation'])
        
    with st.expander("💨 Air Quality Analysis"):
        st.markdown(report['text_sections']['analysis']['aqi'])
        
    with st.expander("🌡️ Urban Heat Analysis"):
        st.markdown(report['text_sections']['analysis']['heat'])
        
    with st.expander("🔮 Predictive Risk Analysis"):
        st.markdown(report['text_sections']['analysis']['prediction'])
    
    st.markdown("---")
    
    st.markdown('<div class="section-title">📊 Key Metrics Summary</div>', unsafe_allow_html=True)
    
    metrics = report['raw_metrics']
    
    def get_status_class(metric, value):
        thresholds = {
            'ndvi': [(0.5, 'good'), (0.3, 'moderate'), (0.2, 'poor'), (0, 'critical')],
            'impervious': [(0.3, 'good'), (0.5, 'moderate'), (0.7, 'poor'), (1, 'critical')],
            'aqi': [(50, 'good'), (100, 'moderate'), (150, 'poor'), (500, 'critical')],
            'pm25': [(15, 'good'), (35, 'moderate'), (55, 'poor'), (500, 'critical')],
            'lst': [(30, 'good'), (35, 'moderate'), (40, 'poor'), (60, 'critical')],
            'risk': [(0.3, 'good'), (0.5, 'moderate'), (0.7, 'poor'), (1, 'critical')]
        }
        for threshold, status in thresholds.get(metric, []):
            if value <= threshold:
                return status
        return 'critical'
    
    st.markdown(f"""
    <table class="metric-table">
        <tr>
            <th>Metric</th>
            <th>Value</th>
            <th>Reference/Threshold</th>
            <th>Status</th>
        </tr>
        <tr>
            <td>NDVI (Vegetation Density)</td>
            <td>{metrics['ndvi']:.3f}</td>
            <td>> 0.4 (Healthy)</td>
            <td class="status-{get_status_class('ndvi', metrics['ndvi'])}">{'Good' if metrics['ndvi'] > 0.4 else 'Needs Improvement'}</td>
        </tr>
        <tr>
            <td>Impervious Surface Ratio</td>
            <td>{metrics['impervious']*100:.1f}%</td>
            <td>< 30% (Sustainable)</td>
            <td class="status-{get_status_class('impervious', metrics['impervious'])}">{'Sustainable' if metrics['impervious'] < 0.3 else 'High Urbanization'}</td>
        </tr>
        <tr>
            <td>Air Quality Index (AQI)</td>
            <td>{metrics['aqi']:.0f}</td>
            <td>< 100 (Satisfactory)</td>
            <td class="status-{get_status_class('aqi', metrics['aqi'])}">{'Satisfactory' if metrics['aqi'] < 100 else 'Unhealthy' if metrics['aqi'] < 150 else 'Poor'}</td>
        </tr>
        <tr>
            <td>PM2.5 Concentration</td>
            <td>{metrics['pm25']:.1f} µg/m³</td>
            <td>< 15 µg/m³ (WHO)</td>
            <td class="status-{get_status_class('pm25', metrics['pm25'])}">{'Meets WHO' if metrics['pm25'] < 15 else 'Exceeds WHO'}</td>
        </tr>
        <tr>
            <td>Land Surface Temperature</td>
            <td>{metrics['lst']:.1f}°C</td>
            <td>< 32°C (Comfortable)</td>
            <td class="status-{get_status_class('lst', metrics['lst'])}">{'Comfortable' if metrics['lst'] < 32 else 'Warm' if metrics['lst'] < 38 else 'Hot'}</td>
        </tr>
        <tr>
            <td>Future Risk Index</td>
            <td>{metrics['risk']:.2f}</td>
            <td>< 0.3 (Low Risk)</td>
            <td class="status-{get_status_class('risk', metrics['risk'])}">{'Low Risk' if metrics['risk'] < 0.3 else 'Moderate' if metrics['risk'] < 0.6 else 'High Risk'}</td>
        </tr>
    </table>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    st.markdown(f'<div class="section-title">⚠️ Priority Focus: {report["weakest_sector"]}</div>', unsafe_allow_html=True)
    
    st.markdown(f"""
    <div class="warning-box">
        <strong>Critical Finding:</strong> The <strong>{report['weakest_sector']}</strong> sector has the lowest score 
        ({scores[report['weakest_sector'].lower().replace(' ', '_').replace('future_risk', 'prediction')]['score'] if report['weakest_sector'] != 'Future Risk' else scores['prediction']['score']:.1f}/25) 
        and requires immediate attention.
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### Recommended Interventions")
    
    mitigations = report['text_sections']['mitigations_full'].get(report['weakest_sector'], [])
    for i, mitigation in enumerate(mitigations, 1):
        st.markdown(f"**{i}.** {mitigation}")
    
    st.markdown("---")
    
    st.markdown('<div class="section-title">🗓️ Implementation Roadmap</div>', unsafe_allow_html=True)
    
    for phase in report['text_sections']['roadmap']:
        st.markdown(f"""
        <div class="roadmap-phase">
            <div class="roadmap-title">{phase['phase']} (+{phase['expected_gain']} USS points expected)</div>
            <ul style="color: #e2e8f0; margin: 0.5rem 0;">
                {''.join([f'<li>{action}</li>' for action in phase['actions']])}
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    st.markdown('<div class="section-title">📥 Download Report</div>', unsafe_allow_html=True)
    
    from services.exports import generate_sustainability_pdf_report
    
    col_dl1, col_dl2 = st.columns(2)
    
    with col_dl1:
        pdf_data = generate_sustainability_pdf_report(report)
        if pdf_data:
            st.download_button(
                "📄 Download Report (PDF)",
                data=pdf_data,
                file_name=f"Sustainability_Report_{report['region_name'].replace(' ', '_').replace(',', '')}_{report['year']}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        else:
            st.error("Unable to generate PDF report")
    
    with col_dl2:
        import csv
        import io
        
        csv_buffer = io.StringIO()
        writer = csv.writer(csv_buffer)
        writer.writerow(['Metric', 'Value', 'Unit', 'Score', 'Grade'])
        writer.writerow(['NDVI', f"{metrics['ndvi']:.3f}", 'index', f"{scores['vegetation']['score']:.1f}", scores['vegetation']['grade']])
        writer.writerow(['Impervious Surface', f"{metrics['impervious']*100:.1f}", '%', '', ''])
        writer.writerow(['AQI', f"{metrics['aqi']:.0f}", 'index', f"{scores['aqi']['score']:.1f}", scores['aqi']['grade']])
        writer.writerow(['PM2.5', f"{metrics['pm25']:.1f}", 'µg/m³', '', ''])
        writer.writerow(['LST', f"{metrics['lst']:.1f}", '°C', f"{scores['heat']['score']:.1f}", scores['heat']['grade']])
        writer.writerow(['Risk Index', f"{metrics['risk']:.2f}", 'index', f"{scores['prediction']['score']:.1f}", scores['prediction']['grade']])
        writer.writerow(['Total USS', f"{scores['total_uss']:.1f}", '/100', '', scores['classification']])
        
        st.download_button(
            "📊 Download Metrics (CSV)",
            data=csv_buffer.getvalue(),
            file_name=f"Sustainability_Metrics_{report['region_name'].replace(' ', '_').replace(',', '')}_{report['year']}.csv",
            mime="text/csv",
            use_container_width=True
        )

else:
    st.info("👈 Select a region and click 'Generate Report' to create your comprehensive sustainability assessment.")
    
    st.markdown("### What This Report Includes")
    
    feature_cols = st.columns(4)
    
    features = [
        ("🌿", "Vegetation Analysis", "NDVI, land cover, impervious surfaces"),
        ("💨", "Air Quality", "PM2.5, AQI, pollution mapping"),
        ("🌡️", "Urban Heat", "LST, thermal comfort analysis"),
        ("🔮", "Risk Prediction", "5-year trend analysis, future projections")
    ]
    
    for i, (icon, title, desc) in enumerate(features):
        with feature_cols[i]:
            st.markdown(f"""
            <div class="module-card">
                <div style="font-size: 2.5rem;">{icon}</div>
                <div style="font-weight: 600; margin: 0.5rem 0; color: #f1f5f9;">{title}</div>
                <div style="font-size: 0.85rem; color: #94a3b8;">{desc}</div>
            </div>
            """, unsafe_allow_html=True)

st.markdown("---")
st.caption("Generated by India GIS & Remote Sensing Portal | Powered by Google Earth Engine")
