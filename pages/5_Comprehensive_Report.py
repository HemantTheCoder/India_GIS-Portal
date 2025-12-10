import streamlit as st
import ee
import folium
from streamlit_folium import st_folium
from services.sustainability_report import generate_sustainability_report
from india_cities import INDIA_CITIES
import geopandas as gpd
import json
import base64

st.set_page_config(layout="wide", page_title="Comprehensive Sustainability Report")

# --- CSS Styling for Premium Report Look ---
st.markdown("""
<style>
    .report-title {
        font-size: 3em; 
        font-weight: 800; 
        background: -webkit-linear-gradient(45deg, #00C9FF, #92FE9D); 
        -webkit-background-clip: text; 
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 0.5em;
    }
    .score-card {
        background-color: #1E1E1E;
        border-radius: 15px;
        padding: 20px;
        text-align: center;
        border: 1px solid #333;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }
    .score-value {
        font-size: 2.5em;
        font-weight: 700;
        margin-bottom: 5px;
    }
    .score-label {
        font-size: 1em;
        color: #ddd;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .score-excellent { color: #4ade80; }
    .score-moderate { color: #facc15; }
    .score-poor { color: #fb923c; }
    .score-critical { color: #f87171; }
    
    .section-header {
        font-size: 1.8em;
        font-weight: 600;
        color: #fff;
        margin-top: 1.5em;
        margin-bottom: 0.8em;
        border-bottom: 2px solid #444;
        padding-bottom: 10px;
    }
    .subsection-header {
        font-size: 1.3em;
        color: #aaa;
        margin-top: 1em;
    }
    .reco-box {
        background-color: #2D3748;
        border-left: 5px solid #4299E1;
        padding: 15px;
        border-radius: 5px;
        margin: 10px 0;
    }
    .report-text {
        font-size: 1.1em;
        line-height: 1.6;
        color: #e0e0e0;
        text-align: justify;
    }
</style>
""", unsafe_allow_html=True)


# --- Initialize EE ---
try:
    ee.Initialize(project='ee-antigravity')
except Exception as e:
    st.error(f"Earth Engine Authentication Error: {e}")
    st.stop()


# --- Sidebar: Location Selection ---
with st.sidebar:
    st.title("Report Parameters")
    
    analysis_type = st.radio(
        "Select Area Source",
        ["Preset City/State", "Upload Shapefile/GeoJSON"]
    )
    
    selected_region = None
    region_name = "Selected Region"
    
    if analysis_type == "Preset City/State":
        state = st.selectbox("State", sorted(list(INDIA_CITIES.keys())))
        city = st.selectbox("City/District", sorted(list(INDIA_CITIES[state].keys())))
        if city:
            coords = INDIA_CITIES[state][city]
            selected_region = ee.Geometry.Point([coords["lon"], coords["lat"]]).buffer(10000) # 10km buffer by default
            region_name = f"{city}, {state}"
            
    else: # Upload
        uploaded_file = st.file_uploader("Upload .geojson or .zip (Shapefile)", type=["geojson", "zip", "kml"])
        if uploaded_file:
            try:
                if uploaded_file.name.endswith('.geojson'):
                    gdf = gpd.read_file(uploaded_file)
                else:
                    # For zip/kml simplified for demo: assume geojson for now or basic read
                    # Real app needs temp file handling for fiona
                    st.warning("For this demo, please use GeoJSON for best results.")
                    gdf = None

                if gdf is not None:
                     # Convert to EE
                    json_text = gdf.to_json()
                    geojson_dict = json.loads(json_text)
                    features = geojson_dict.get('features', [])
                    if features:
                         # Take first feature geometry
                         geom = features[0]['geometry']
                         selected_region = ee.Geometry(geom)
                         region_name = "Uploaded Region"
            except Exception as e:
                st.error(f"Error reading file: {e}")

    generate_btn = st.button("Generate Comprehensive Report", type="primary")

# --- Main Content ---
st.markdown('<div class="report-title">Urban Sustainability Report</div>', unsafe_allow_html=True)
st.markdown(f"<h3 style='text-align: center; color: #888;'>for {region_name} | {2024}</h3>", unsafe_allow_html=True)

if generate_btn and selected_region:
    with st.spinner(f"Aggregating multi-module satellite data for {region_name}... This may take a moment."):
        
        # Call the Logic
        report_data = generate_sustainability_report(selected_region, region_name=region_name, year=2023)
        
        if report_data:
            scores = report_data['scores']
            texts = report_data['text_sections']
            
            # --- 1. Score Dashboard ---
            uss = scores['Total USS']
            cls = scores['Classification']
            
            cls_color = "score-excellent" if cls == "Excellent" else "score-moderate" if cls == "Moderate" else "score-poor" if cls == "Poor" else "score-critical"
            
            col_main, col_breakdown = st.columns([1, 2])
            
            with col_main:
                st.markdown(f"""
                <div class="score-card" style="border: 2px solid #fff;">
                    <div class="score-label">Overall USS</div>
                    <div class="score-value {cls_color}" style="font-size: 4em;">{uss:.1f}</div>
                    <div class="score-label" style="font-size: 1.5em; color: #fff;">{cls}</div>
                </div>
                """, unsafe_allow_html=True)
                
            with col_breakdown:
                c1, c2, c3, c4 = st.columns(4)
                
                parts = [
                    ("Vegetation", scores['Vegetation']),
                    ("Air Quality", scores['Air Quality']),
                    ("Urban Heat", scores['Urban Heat']),
                    ("Future Risk", scores['Prediction'])
                ]
                
                cols = [c1, c2, c3, c4]
                
                for i, (name, data) in enumerate(parts):
                    with cols[i]:
                        st.markdown(f"""
                        <div class="score-card">
                            <div class="score-value" style="font-size: 1.8em;">{data['score']:.1f}<span style="font-size:0.5em; color:#888;">/25</span></div>
                            <div class="score-label" style="font-size: 0.8em;">{name}</div>
                            <div style="font-size: 0.7em; color: #aaa; margin-top:5px;">{data['metric']}: {data['value']:.1f}</div>
                        </div>
                        """, unsafe_allow_html=True)

            # --- 2. Sections ---
            
            # A. Overview
            st.markdown('<div class="section-header">A. Environmental Overview</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="report-text">{texts["overview"]}</div>', unsafe_allow_html=True)
            
            # B. Module Analysis
            st.markdown('<div class="section-header">B. Multi-Dimensional Deep Dive</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="report-text">{texts["analysis"]}</div>', unsafe_allow_html=True)
            
            # C. Data Breakdown (Table)
            st.markdown('<div class="section-header">C. Quantitative Breakdown</div>', unsafe_allow_html=True)
            raw = report_data['raw_metrics']
            breakdown_data = {
                "Metric": ["NDVI (Vegetation Density)", "Impervious Surface Ratio", "AQI (Air Quality Index)", "PM2.5 Concentration", "Land Surface Temp (LST)", "Predictive Risk Index"],
                "Value": [f"{raw['ndvi']:.3f}", f"{raw['impervious']*100:.1f}%", f"{raw['aqi']:.0f}", f"{raw['pm25']:.1f} µg/m³", f"{raw['lst']:.1f} °C", f"{raw['risk']:.2f}"],
                "Threshold / Reference": ["> 0.4 (Healthy)", "< 30% (Sustainable)", "< 100 (Satisfactory)", "< 60 µg/m³ (Standard)", "< 30°C (Comfort)", "< 0.2 (Low Risk)"]
            }
            st.table(breakdown_data)
            
            # D. Critical Focus
            st.markdown('<div class="section-header">D. Critical Focus Area</div>', unsafe_allow_html=True)
            st.error(f"The weakest performing sector is **{report_data['weakest_sector']}**. This requires immediate policy attention.")
            st.markdown(f'<div class="report-text">{texts["improvement"]}</div>', unsafe_allow_html=True)
            
            # E. Mitigation
            st.markdown('<div class="section-header">E. Strategic Mitigation Plan</div>', unsafe_allow_html=True)
            st.info("The following strategies are customized based on the region's lowest scoring dimension.")
            st.markdown(f'<div class="reco-box">{texts["mitigation"]}</div>', unsafe_allow_html=True)
            
            # G. Action Roadmap
            st.markdown('<div class="section-header">F. Action Roadmap</div>', unsafe_allow_html=True)
            st.markdown(texts['roadmap'])
            
            # Download Button
            report_str = f"""
            Urban Sustainability Report for {region_name}
            ------------------------------------------------
            Overall Score: {uss:.1f}/100 ({cls})
            
            Scores:
            - Vegetation: {scores['Vegetation']['score']:.1f}/25
            - Air Quality: {scores['Air Quality']['score']:.1f}/25
            - Urban Heat: {scores['Urban Heat']['score']:.1f}/25
            - Prediction: {scores['Prediction']['score']:.1f}/25
            
            Overview:
            {texts['overview']}
            
            Analysis:
            {texts['analysis']}
            
            Mitigation Strategies:
            {texts['mitigation']}
            
            Roadmap:
            {texts['roadmap']}
            """
            
            b64_report = base64.b64encode(report_str.encode()).decode()
            href = f'<a href="data:file/txt;base64,{b64_report}" download="Sustainability_Report_{region_name}.txt" style="display: inline-block; padding: 0.5em 1em; background: #FFF; color: #000; font-weight: bold; text-decoration: none; border-radius: 5px; margin-top: 20px;">Download Full Report (TXT)</a>'
            st.markdown(href, unsafe_allow_html=True)
            
        else:
            st.error("Failed to generate report data. Please check logs or try a different region.")

elif generate_btn and not selected_region:
    st.warning("Please select a valid region first.")

st.markdown("---")
st.caption("Generated by AI-Powered Urban Sustainability Engine | Powered by Google Earth Engine")
