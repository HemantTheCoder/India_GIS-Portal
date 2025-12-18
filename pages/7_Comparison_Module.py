
import streamlit as st
import ee
import folium
from streamlit_folium import st_folium
import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import tempfile
import os
import io

from services.comparison_service import perform_comparison
from services.comparison_export import generate_comparison_pdf
from services.gee_core import auto_initialize_gee
from india_cities import INDIA_DATA as INDIA_CITIES
from components.ui import apply_enhanced_css, render_page_header, init_common_session_state, custom_spinner
from components.theme_manager import ThemeManager
from components.maps import create_base_map, add_tile_layer, add_layer_control

st.set_page_config(layout="wide", page_title="Regional Comparison", page_icon="⚖️")
st.markdown("""
<style>
/* Remove Streamlit default padding */
.block-container {
    padding-top: 0rem !important;
    padding-bottom: 0rem !important;
    padding-left: 1rem !important;
    padding-right: 1rem !important;
}

/* Hide header & footer */
header {visibility: hidden;}
footer {visibility: hidden;}

/* Remove "Built with Streamlit" space */
.viewerBadge_container__1QSob {
    display: none !important;
}

/* Prevent double scrollbars */
html, body {
    overflow: hidden;
}
</style>
""", unsafe_allow_html=True)
apply_enhanced_css()

# Custom CSS for Comparison
st.markdown("""
<style>
    .comp-header {
        text-align: center;
        padding: 1rem;
        background: rgba(15, 23, 42, 0.6);
        border-radius: 10px;
        margin-bottom: 2rem;
        border: 1px solid rgba(56, 189, 248, 0.2);
    }
    .comp-vs {
        font-size: 1.5rem;
        font-weight: 800;
        color: #94a3b8;
        margin: 0 1rem;
    }
    .region-name {
        font-size: 1.8rem;
        font-weight: 700;
        background: linear-gradient(135deg, #38bdf8, #818cf8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .metric-card-comp {
        background: rgba(30, 41, 59, 0.5);
        border-radius: 10px;
        padding: 1rem;
        text-align: center;
        height: 100%;
    }
    .comp-diff-pos { color: #22c55e; font-weight: bold; }
    .comp-diff-neg { color: #ef4444; font-weight: bold; }
    .comp-diff-neu { color: #94a3b8; }
</style>
""", unsafe_allow_html=True)

auto_initialize_gee()
init_common_session_state()
apply_enhanced_css()

# Theme Integration
theme_manager = ThemeManager()
theme_manager.apply_theme()

render_page_header(
    theme_manager.get_text("⚖️ Regional Comparison Module"),
    theme_manager.get_text(
        "Compare environmental metrics side-by-side between two regions.",
        "⚙️ DIMENSIONAL RIFT COMPARE: Assessing divergence between two reality zones."
    )
)

# --- Sidebar Inputs ---

def render_region_input(key_prefix, label):
    st.markdown(f"### {label}")
    type_key = f"{key_prefix}_type"
    
    input_type = st.radio(
        "Input Method",
        ["City/State", "Upload Shapefile"],
        key=type_key,
        horizontal=True,
        label_visibility="collapsed"
    )
    
    geometry = None
    name = None
    center = None
    
    if input_type == "City/State":
        state_key = f"{key_prefix}_state"
        city_key = f"{key_prefix}_city"
        
        state = st.selectbox("State", sorted(list(INDIA_CITIES.keys())), key=state_key)
        cities = sorted(list(INDIA_CITIES[state].keys()))
        city = st.selectbox("City", cities, key=city_key)
        
        if city:
            coords = INDIA_CITIES[state][city]
            center = [coords["lat"], coords["lon"]]
            geometry = ee.Geometry.Point([coords["lon"], coords["lat"]]).buffer(15000) # Default 15km
            name = f"{city}"
            
    else:
        file_key = f"{key_prefix}_file"
        uploaded = st.file_uploader("Upload GeoJSON/Zip", type=["geojson", "json", "zip"], key=file_key)
        
        if uploaded:
             try:
                # Basic file handling reuse from other modules
                if uploaded.name.endswith(('.geojson', '.json')):
                    gdf = gpd.read_file(uploaded)
                elif uploaded.name.endswith('.zip'):
                    with tempfile.TemporaryDirectory() as tmpdir:
                        zip_path = os.path.join(tmpdir, "upload.zip")
                        with open(zip_path, 'wb') as f: f.write(uploaded.getvalue())
                        import zipfile
                        with zipfile.ZipFile(zip_path, 'r') as zip_ref: zip_ref.extractall(tmpdir)
                        shp_files = [f for f in os.listdir(tmpdir) if f.endswith('.shp')]
                        if shp_files: gdf = gpd.read_file(os.path.join(tmpdir, shp_files[0]))
                        else: gdf = None
                
                if gdf is not None:
                     if gdf.crs.to_string() != "EPSG:4326":
                         gdf = gdf.to_crs("EPSG:4326")
                     combined = gdf.geometry.unary_union
                     import json
                     geometry = ee.Geometry(json.loads(gpd.GeoSeries([combined]).to_json())['features'][0]['geometry'])
                     centroid = combined.centroid
                     center = [centroid.y, centroid.x]
                     name = "Custom Region"
                     st.success("Loaded")
             except Exception as e:
                 st.error(f"Error: {e}")
                 
    return {"geometry": geometry, "name": name, "center": center}

with st.sidebar:
    st.info("Select two regions to compare")
    
    st.markdown("---")
    region_a = render_region_input("reg_a", "📍 Region A")
    
    st.markdown("---")
    region_b = render_region_input("reg_b", "📍 Region B")
    
    st.markdown("---")
    year = st.selectbox("📅 Analysis Year", range(2024, 2017, -1))
    
    run_btn = st.button("🚀 Run Comparison", type="primary", use_container_width=True)

# --- Main Layout ---

# 1. Module Selection
modules = st.multiselect(
    "Select Analyses to Compare",
    ["Vegetation", "Air Quality", "Urban Heat", "Future Risk", "Earthquake Safety"],
    default=["Vegetation", "Air Quality", "Urban Heat", "Future Risk", "Earthquake Safety"]
)

if run_btn and region_a['geometry'] and region_b['geometry']:
    with st.status("Performing Comparative Analysis...", expanded=True) as status:
        st.write("⚙️ Initializing modules...")
        
        def update_progress(msg):
            st.write(f"⚙️ {msg}")
            
        try:
            comparison_results = perform_comparison(
                region_a, region_b, modules, year, status_callback=update_progress
            )
            st.session_state.comparison_results = comparison_results
            status.update(label="Comparison Complete!", state="complete", expanded=False)
            
        except Exception as e:
            status.update(label="Comparison Failed", state="error")
            st.error(str(e))

if 'comparison_results' in st.session_state:
    res = st.session_state.comparison_results
    data_a = res['region_a']
    data_b = res['region_b']
    
    # 2. Header Summary
    st.markdown(f"""
    <div class="comp-header">
        <span class="region-name">{data_a['region_name']}</span>
        <span class="comp-vs">vs</span>
        <span class="region-name">{data_b['region_name']}</span>
        <div style="margin-top: 1rem; color: #e2e8f0;">
            {res['summary']}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 3. Overall Score
    col1, col2, col3 = st.columns([1, 0.2, 1])
    with col1:
        st.metric("Total Sustainability Score", f"{data_a['total_uss']:.1f}", 
                  delta=f"{data_a['total_uss'] - data_b['total_uss']:.1f}", help="Out of 100")
    with col3:
        st.metric("Total Sustainability Score", f"{data_b['total_uss']:.1f}", 
                  delta=f"{data_b['total_uss'] - data_a['total_uss']:.1f}", help="Out of 100")

    st.markdown("---")

    # 4. Module-wise Comparison Grid
    for module in modules:
        res_a = data_a['results'].get(module, {})
        res_b = data_b['results'].get(module, {})
        
        st.markdown(f"### {module}")
        
        # Grid: [Map A] [Metrics] [Map B]
        c1, c2, c3 = st.columns([1.5, 1, 1.5])
        
        # Center: Metrics
        with c2:
            val_a = res_a.get('value', 0)
            val_b = res_b.get('value', 0)
            metric_unit = res_a.get('metric', '')
            
            # Formating
            if isinstance(val_a, (float, int)):
                 delta = val_a - val_b
                 delta_str = f"{delta:+.2f}"
            else:
                 delta_str = None
                 
            st.markdown(f"""
            <div style="text-align: center; padding: 10px;">
                <div style="font-size: 0.9rem; color: #94a3b8;">{metric_unit}</div>
                <div style="font-size: 1.5rem; font-weight: bold;">{val_a:.2f} <span style="font-size: 1rem; color: #64748b;">vs</span> {val_b:.2f}</div>
                <div style="color: {'#22c55e' if delta > 0 else '#ef4444' if delta < 0 else '#94a3b8'}; font-weight: bold;">
                    Dif: {delta_str}
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Specific extra metrics
            if module == "Vegetation":
                 st.caption(f"Impervious: {res_a.get('impervious',0)*100:.1f}% vs {res_b.get('impervious',0)*100:.1f}%")
            if module == "Air Quality":
                 st.caption(f"PM2.5: {res_a.get('pm25',0):.1f} vs {res_b.get('pm25',0):.1f}")
        
        # Side Maps
        zoom = 10
        
        with c1:
            m_a = create_base_map(region_a['center'][0], region_a['center'][1], zoom=zoom)
            
            # Add layers based on module
            layer_key = None
            if module == "Vegetation": layer_key = 'ndvi' 
            elif module == "Air Quality": layer_key = 'pm25'
            elif module == "Urban Heat": layer_key = 'lst'
            elif module == "Earthquake Safety": layer_key = 'earthquake'
            
            if layer_key and layer_key in data_a['tile_urls']:
                add_tile_layer(m_a, data_a['tile_urls'][layer_key], module, 0.7)
                
            st_folium(m_a, height=250, use_container_width=True, key=f"map_a_{module}")
            st.caption(f"{data_a['region_name']}")

        with c3:
            m_b = create_base_map(region_b['center'][0], region_b['center'][1], zoom=zoom)
            
            if layer_key and layer_key in data_b['tile_urls']:
                add_tile_layer(m_b, data_b['tile_urls'][layer_key], module, 0.7)
                
            st_folium(m_b, height=250, use_container_width=True, key=f"map_b_{module}")
            st.caption(f"{data_b['region_name']}")
            
        st.divider()

    # 5. Radar Chart Comparison
    st.markdown("### 🕸️ Comparative Profile")
    
    chart_cols = st.columns([1, 2, 1])
    with chart_cols[1]:
        # Simple Radar Chart
        labels = modules
        stats_a = [data_a['results'][m]['score'] for m in modules]
        stats_b = [data_b['results'][m]['score'] for m in modules]
        
        angles = np.linspace(0, 2*np.pi, len(labels), endpoint=False).tolist()
        stats_a += stats_a[:1]
        stats_b += stats_b[:1]
        angles += angles[:1]
        
        fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
        ax.fill(angles, stats_a, color='#38bdf8', alpha=0.25)
        ax.plot(angles, stats_a, color='#38bdf8', linewidth=2, label=data_a['region_name'])
        
        ax.fill(angles, stats_b, color='#22c55e', alpha=0.25)
        ax.plot(angles, stats_b, color='#22c55e', linewidth=2, label=data_b['region_name'])
        
        ax.set_yticklabels([])
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(labels)
        
        # Theme adjustment
        ax.set_facecolor('none')
        fig.patch.set_facecolor('none')
        ax.spines['polar'].set_color('#475569')
        ax.tick_params(colors='#e2e8f0')
        ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1))
        
        st.pyplot(fig)

    # 6. Export
    st.markdown("---")
    st.subheader("📥 Export Comparison")
    
    pdf_bytes = generate_comparison_pdf(res)
    
    st.download_button(
        "📄 Download Comparison Report (PDF)",
        data=pdf_bytes,
        file_name=f"Comparison_{data_a['region_name']}_vs_{data_b['region_name']}.pdf",
        mime="application/pdf",
        use_container_width=True
    )
    
elif not run_btn:
    if region_a['center'] or region_b['center']:
        st.subheader("📍 Selection Preview")
        p_col1, p_col2 = st.columns(2)
        
        with p_col1:
            if region_a['center']:
                st.markdown(f"**Region A: {region_a['name']}**")
                m_prev_a = create_base_map(region_a['center'][0], region_a['center'][1], zoom=10)
                # Add marker/circle
                folium.Marker(region_a['center'], popup=region_a['name'], icon=folium.Icon(color='blue')).add_to(m_prev_a)
                if region_a['geometry']:
                     # Visualizing geometry structure roughly if simple
                     pass 
                st_folium(m_prev_a, height=300, use_container_width=True, key="prev_map_a")
            else:
                st.info("Select Region A in Sidebar")
                
        with p_col2:
            if region_b['center']:
                st.markdown(f"**Region B: {region_b['name']}**")
                m_prev_b = create_base_map(region_b['center'][0], region_b['center'][1], zoom=10)
                folium.Marker(region_b['center'], popup=region_b['name'], icon=folium.Icon(color='green')).add_to(m_prev_b)
                st_folium(m_prev_b, height=300, use_container_width=True, key="prev_map_b")
            else:
                st.info("Select Region B in Sidebar")
                
    else:
        st.markdown("""
        <div style="text-align: center; padding: 3rem; color: #64748b;">
            <h3>👈 Review Sidebar Settings</h3>
            <p>Select two regions and click "Run Comparison" to begin.</p>
        </div>
        """, unsafe_allow_html=True)
