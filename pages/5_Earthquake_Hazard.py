
import streamlit as st
import folium
from streamlit_folium import st_folium
import ee
import pandas as pd
from datetime import datetime, timedelta
import json
import os
import tempfile
import geopandas as gpd

from services.gee_core import auto_initialize_gee
from services import earthquake_core as eq_core
from services import earthquake_export as eq_export
from india_cities import INDIA_DATA as INDIA_CITIES
from components.ui import apply_enhanced_css, render_page_header
from components.maps import create_base_map, add_tile_layer, add_layer_control

st.set_page_config(layout="wide", page_title="Earthquake Hazard & Monitoring", page_icon=" भूकंप ")

# Initialize
auto_initialize_gee()
apply_enhanced_css()

# Session State
if 'eq_data' not in st.session_state: st.session_state.eq_data = []
if 'hazard_layer' not in st.session_state: st.session_state.hazard_layer = None
if 'analysis_results' not in st.session_state: st.session_state.analysis_results = None
if 'preview_map_center' not in st.session_state: st.session_state.preview_map_center = [20.5937, 78.9629]
if 'preview_map_zoom' not in st.session_state: st.session_state.preview_map_zoom = 5

# Custom CSS
st.markdown("""
<style>
    .metric-card {
        background: linear-gradient(135deg, #1e293b, #0f172a);
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid rgba(255,255,255,0.1);
        text-align: center;
    }
    .metric-val {
        font-size: 2rem;
        font-weight: 700;
        background: linear-gradient(90deg, #f97316, #fbbf24);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .metric-lbl {
        color: #94a3b8;
        font-size: 0.9rem;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .risk-badge {
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: bold;
        display: inline-block;
        margin-top: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Header
render_page_header(
    "🏔️ Earthquake Hazard & Real-Time Monitoring",
    "Real-time seismic activity tracking, Probabilistic Hazard Mapping (GEE), and Automated Risk Reporting."
)

# --- Sidebar: AOI & Params ---
with st.sidebar:
    st.markdown("### 📍 Analysis Region")
    
    # 1. AOI Selection (Standard Pattern)
    analysis_type = st.radio("Selection Method", ["City/State", "Upload Shapefile/GeoJSON"], horizontal=True)
    
    geometry = None
    region_name = "India"
    center_coords = [20.5937, 78.9629] # India Center
    zoom_level = 5
    
    if analysis_type == "City/State":
        state = st.selectbox("State", sorted(list(INDIA_CITIES.keys())), index=0)
        cities = sorted(list(INDIA_CITIES[state].keys()))
        city = st.selectbox("City/District", cities, index=0)
        
        buffer_km = st.slider("Buffer Radius (km)", 10, 200, 50)
        
        if city:
            coords = INDIA_CITIES[state][city]
            center_coords = [coords["lat"], coords["lon"]]
            geometry = ee.Geometry.Point([coords["lon"], coords["lat"]]).buffer(buffer_km * 1000)
            region_name = f"{city}, {state}"
            zoom_level = 9
            
            # Update Preview State immediately
            st.session_state.preview_map_center = center_coords
            st.session_state.preview_map_zoom = zoom_level
            
    else:
        uploaded_file = st.file_uploader("Upload GeoJSON/KML/Shapefile", type=["geojson", "json", "kml", "zip"])
        if uploaded_file:
            # Simple GeoJSON loading wrapper (reuse simplify logic)
            try:
                if uploaded_file.name.endswith('.zip'):
                    import zipfile
                    with tempfile.TemporaryDirectory() as tmpdir:
                        zip_path = os.path.join(tmpdir, "upload.zip")
                        with open(zip_path, 'wb') as f: f.write(uploaded_file.getvalue())
                        with zipfile.ZipFile(zip_path, 'r') as z: z.extractall(tmpdir)
                        shp = [f for f in os.listdir(tmpdir) if f.endswith('.shp')][0]
                        gdf = gpd.read_file(os.path.join(tmpdir, shp))
                else:
                    gdf = gpd.read_file(uploaded_file)
                
                if not gdf.empty:
                    gdf = gdf.to_crs("EPSG:4326")
                    bounds = gdf.total_bounds
                    center_coords = [(bounds[1]+bounds[3])/2, (bounds[0]+bounds[2])/2]
                    geojson = json.loads(gdf.to_json())
                    # Take first feature or union
                    geom_json = geojson['features'][0]['geometry']
                    geometry = ee.Geometry(geom_json)
                    region_name = "Uploaded Region"
                    zoom_level = 9
                    st.success(f"Loaded region: {len(gdf)} features")
                    
                    # Update Preview State immediately
                    st.session_state.preview_map_center = center_coords
                    st.session_state.preview_map_zoom = zoom_level
            except Exception as e:
                st.error(f"Error loading file: {e}")

    st.markdown("---")
    st.markdown("### 🔍 Filter Settings")
    
    min_mag = st.slider("Min Magnitude", 1.0, 9.0, 2.5, 0.1)
    
    days_back = st.slider("Lookback Period (Days)", 1, 365, 30)
    start_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
    end_date = datetime.now().strftime('%Y-%m-%d')
    
    show_historical = st.checkbox("Show Historical Earthquakes", value=True)
    show_hazard = st.checkbox("Overlay Hazard Map (GEE)", value=True)
    
    st.markdown("---")
    if st.button("🚀 Run Analysis", type="primary", use_container_width=True):
        if geometry:
            with st.spinner("Fetching USGS Data & Computing GEE Hazard..."):
                # 1. Fetch USGS
                # Get bounds from geometry
                bounds = geometry.bounds().getInfo() 
                # bounds is {'type': 'Polygon', 'coordinates': [[...]]}
                # Simplify: just use lat/lon box for API, clip later
                coords_list = bounds['coordinates'][0]
                lons = [c[0] for c in coords_list]
                lats = [c[1] for c in coords_list]
                
                usgs_data = eq_core.fetch_usgs_earthquakes(
                    min_lat=min(lats), max_lat=max(lats),
                    min_lon=min(lons), max_lon=max(lons),
                    min_mag=min_mag,
                    start_date=start_date,
                    end_date=end_date
                )
                processed_quakes = eq_core.process_earthquake_data(usgs_data)
                
                # 2. Zone & Risk
                zone_info = eq_core.get_seismic_zone(center_coords[0], center_coords[1], region_name)
                
                # 3. GEE Hazard
                hazard_stats = eq_core.analyze_seismic_hazard(geometry) if show_hazard else {}
                
                # 4. Risk Score
                # Proxy density: avg 5000/km2 for urban, using a static for now or derived
                risk_score = eq_core.calculate_seismic_risk_score(
                    pga=hazard_stats.get('mean_pga', 0.15),
                    zone=zone_info['zone'],
                    historical_count=len(processed_quakes),
                    exposure_index=0.8 # Mocked high exposure for urban areas
                )
                
                st.session_state.analysis_results = {
                    'region_name': region_name,
                    'time_range': f"{start_date} to {end_date}",
                    'quakes': processed_quakes,
                    'zone_info': zone_info,
                    'hazard_stats': hazard_stats,
                    'risk_score': risk_score,
                    'stats': {
                        'total_events': len(processed_quakes),
                        'max_mag': max([q['magnitude'] for q in processed_quakes]) if processed_quakes else 0,
                        'avg_depth': sum([q['depth'] for q in processed_quakes])/len(processed_quakes) if processed_quakes else 0
                    }
                }
                st.success("Analysis Complete!")
        else:
            st.error("Please select a valid region.")

# --- Results Presentation ---
res = st.session_state.analysis_results

if res:
    # Kpis
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-lbl">Resultant Risk Score</div>
            <div class="metric-val">{res['risk_score']['total_score']}</div>
            <div style="color: #64748b; font-size: 0.8rem;">/ 100</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col2:
        risk_color = "#ef4444" if "High" in res['zone_info']['risk'] else "#eab308"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-lbl">Seismic Zone</div>
            <div class="metric-val" style="color: {risk_color}; text-shadow: 0 0 10px {risk_color}40;">{res['zone_info']['zone']}</div>
            <div style="color: {risk_color}; font-weight: bold;">{res['zone_info']['risk']}</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-lbl">Recorded Events</div>
            <div class="metric-val">{res['stats']['total_events']}</div>
            <div style="color: #64748b; font-size: 0.8rem;">Max Mag: {res['stats']['max_mag']}</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col4:
        pga = res['hazard_stats'].get('mean_pga', 0)
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-lbl">Mean Probability (PGA)</div>
            <div class="metric-val">{pga:.2f}g</div>
            <div style="color: #64748b; font-size: 0.8rem;">Moderate Shaking Exp.</div>
        </div>
        """, unsafe_allow_html=True)
    st.markdown("---")

# Main Map Section (Always Visible)
st.markdown("### 🗺️ Interactive Hazard Map")
m_col, d_col = st.columns([2, 1])

with m_col:
    # Use session state or current selection for map center
    map_center = st.session_state.preview_map_center
    map_zoom = st.session_state.preview_map_zoom
    
    m = create_base_map(map_center[0], map_center[1], zoom=map_zoom)
    
    # Render Overlay if Analysis Done
    if res:
        # Overlay Hazard
        if show_hazard and 'tile_url' in res['hazard_stats']:
            add_tile_layer(m, res['hazard_stats']['tile_url'], "Seismic Hazard Risk (Proxy)")
            
        # Overlay Quakes
        if show_historical:
            for q in res['quakes']:
                color = '#ff0000' if q['magnitude'] >= 5 else '#ff7e00' if q['magnitude'] >= 4 else '#ffff00'
                radius = q['magnitude'] * 2
                folium.CircleMarker(
                    location=[q['lat'], q['lon']],
                    radius=radius, color=color, fill=True, fill_color=color, fill_opacity=0.7,
                    popup=folium.Popup(f"<b>M{q['magnitude']}</b><br>{q['place']}<br>{q['time']}<br>Depth: {q['depth']}km")
                ).add_to(m)
    
    # Always render AOI if geometry exists
    if geometry:
        # Since we are using Streamlit reload, geometry object persists in this run
        # Visual feedback: Marker at center
        folium.Marker(
            location=center_coords,
            popup=f"Selected Region: {region_name}",
            tooltip="AOI Center"
        ).add_to(m)
        
        # If possible, draw the buffer circle
        # For simplicity, just the marker + base map centered is "Immediate Map Display"
        folium.Circle(
             location=center_coords,
             radius=buffer_km * 1000 if analysis_type == "City/State" else 50000, # Approx if not simple buffer
             color="#38bdf8",
             weight=2,
             fill=True,
             fill_opacity=0.1
        ).add_to(m)
            
    add_layer_control(m)
    st_folium(m, height=500, use_container_width=True)

with d_col:
    st.markdown("### 📋 Events Data")
    if res and res['quakes']:
        df = pd.DataFrame(res['quakes'])
        st.dataframe(
            df[['time', 'magnitude', 'depth', 'place']].sort_values('time', ascending=False),
            column_config={
                "time": "Date",
                "magnitude": st.column_config.NumberColumn("Mag", format="%.1f"),
                "depth": "Depth (km)",
                "place": "Location"
            },
            height=400,
            hide_index=True
        )
    elif res:
        st.info("No earthquakes found in this region.")
    else:
        st.info("Select a region to view AOI on map. Click 'Run Analysis' to fetch earthquake data.")

if res:
    st.markdown("---")
    # Report Generation
    st.subheader("📑 Automated Report Generation")
    col_r1, col_r2 = st.columns([3, 1])
    with col_r1:
        st.markdown("Generate a PDF report compliant with safety standards, including hazard maps, historical data analysis, and mitigation recommendations.")
    with col_r2:
        if st.button("Download PDF Report", use_container_width=True):
            pdf_bytes = eq_export.generate_earthquake_pdf_report({
                'region_name': res['region_name'],
                'time_range': res['time_range'],
                'zone_info': res['zone_info'],
                'risk_score': res['risk_score'],
                'hazard_stats': res['hazard_stats'],
                'recent_quakes': res['quakes'],
                'stats': res['stats']
            })
            
            st.download_button(
                label="📄 Click to Save PDF",
                data=pdf_bytes,
                file_name=f"Earthquake_Hazard_Report_{res['region_name']}_{datetime.now().strftime('%Y%m%d')}.pdf",
                mime="application/pdf"
            )
elif not geometry:
    st.info("👈 Use the sidebar to select a region (State/City or Upload) to begin.")

