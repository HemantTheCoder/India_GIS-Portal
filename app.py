import streamlit as st

from services.gee_core import auto_initialize_gee
from components.ui import apply_enhanced_css, render_page_header, init_common_session_state

st.set_page_config(
    page_title="India GIS & Remote Sensing Portal",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="expanded",
)

auto_initialize_gee()
init_common_session_state()
apply_enhanced_css()

render_page_header(
    "🛰️ India GIS & Remote Sensing Portal",
    "Advanced Earth Observation and Environmental Analysis for India"
)

with st.sidebar:
    st.markdown("## 🔐 GEE Status")
    if st.session_state.gee_initialized:
        st.success("GEE Connected")
    else:
        st.error("GEE Not Connected - Check secrets.toml")
    
    st.markdown("---")
    st.markdown("## 🧭 Navigation")
    st.markdown("Use the pages in the sidebar to access different analysis modules.")
    
    st.markdown("---")
    st.markdown("### Quick Links")
    st.page_link("pages/1_LULC_Vegetation.py", label="🌍 LULC & Vegetation", icon="🌍")
    st.page_link("pages/2_AQI_Analysis.py", label="🌫️ AQI Analysis", icon="🌫️")

st.markdown("---")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    <div class="card">
        <div class="card-header">🌍 LULC & Vegetation Analysis</div>
        <p>Analyze Land Use, Land Cover, and Vegetation Indices for any Indian city.</p>
        <ul>
            <li><b>LULC Mapping:</b> 9 land cover classes using Dynamic World</li>
            <li><b>Vegetation Indices:</b> NDVI, NDWI, NDBI, EVI, SAVI</li>
            <li><b>Time Series:</b> Compare changes between years</li>
            <li><b>Custom AOI:</b> Draw your own analysis areas</li>
            <li><b>Pixel Inspector:</b> Click to view index values</li>
            <li><b>Export:</b> CSV statistics, GeoTIFF downloads, PDF reports</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("Open LULC Analysis →", use_container_width=True, type="primary"):
        st.switch_page("pages/1_LULC_Vegetation.py")

with col2:
    st.markdown("""
    <div class="card">
        <div class="card-header">🌫️ Air Quality Analysis</div>
        <p>Monitor air pollutants using Sentinel-5P satellite data.</p>
        <ul>
            <li><b>Pollutants:</b> NO₂, SO₂, CO, O₃, UVAI, CH₄</li>
            <li><b>AOI Statistics:</b> Mean, median, std dev, percentiles</li>
            <li><b>Anomaly Maps:</b> Compare to 2019 baseline</li>
            <li><b>Hotspot Detection:</b> Identify pollution hotspots</li>
            <li><b>Time Series:</b> Track pollutant trends over time</li>
            <li><b>Dashboard:</b> Multi-pollutant correlations & radar charts</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("Open AQI Analysis →", use_container_width=True, type="primary"):
        st.switch_page("pages/2_AQI_Analysis.py")

st.markdown("---")

st.markdown("### 🛰️ Data Sources")

data_col1, data_col2, data_col3 = st.columns(3)

with data_col1:
    st.markdown("""
    <div class="card">
        <div class="card-header">Sentinel-2</div>
        <p><b>Resolution:</b> 10m (RGB, NIR)</p>
        <p><b>Revisit:</b> ~5 days</p>
        <p><b>Available:</b> 2017-present</p>
        <p>Best for detailed vegetation and land cover analysis.</p>
    </div>
    """, unsafe_allow_html=True)

with data_col2:
    st.markdown("""
    <div class="card">
        <div class="card-header">Landsat 8/9</div>
        <p><b>Resolution:</b> 30m</p>
        <p><b>Revisit:</b> ~16 days</p>
        <p><b>Available:</b> 2013-present</p>
        <p>Best for long-term studies and historical analysis.</p>
    </div>
    """, unsafe_allow_html=True)

with data_col3:
    st.markdown("""
    <div class="card">
        <div class="card-header">Sentinel-5P</div>
        <p><b>Resolution:</b> 1-7 km</p>
        <p><b>Revisit:</b> Daily</p>
        <p><b>Available:</b> 2018-present</p>
        <p>Atmospheric composition monitoring for air quality.</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

st.markdown("### 📊 Index Reference")

idx_col1, idx_col2 = st.columns(2)

with idx_col1:
    st.markdown("""
    | Index | Range | Description |
    |-------|-------|-------------|
    | **NDVI** | -1 to 1 | Vegetation health and density |
    | **NDWI** | -1 to 1 | Water body detection |
    | **NDBI** | -1 to 1 | Built-up area identification |
    | **EVI** | -1 to 1 | Enhanced vegetation index |
    | **SAVI** | 0 to 1 | Soil-adjusted vegetation |
    """)

with idx_col2:
    st.markdown("""
    | Pollutant | Unit | Source |
    |-----------|------|--------|
    | **NO₂** | µmol/m² | Vehicles, industry |
    | **SO₂** | µmol/m² | Power plants |
    | **CO** | mmol/m² | Combustion |
    | **O₃** | mmol/m² | Atmospheric |
    | **UVAI** | Index | Smoke, dust |
    | **CH₄** | ppb | Natural gas, agriculture |
    """)

st.markdown("---")

st.markdown("### 🆕 What's New")

new_col1, new_col2 = st.columns(2)

with new_col1:
    st.markdown("""
    #### Enhanced UI
    - Full-width responsive map with rounded corners
    - Collapsible legends with opacity controls
    - Pixel value inspector on click
    - Improved statistics with pie/bar charts
    """)

with new_col2:
    st.markdown("""
    #### New AQI Module
    - 6 pollutants from Sentinel-5P
    - Anomaly and hotspot detection
    - Time series with rolling averages
    - Multi-pollutant correlation dashboard
    """)

st.markdown("---")
st.markdown(
    """
    <div style="text-align: center; color: #666; padding: 1rem;">
        Made with ❤️ by <strong>Hemant Kumar</strong> • 
        <a href="https://www.linkedin.com/in/hemantkumar2430" target="_blank">LinkedIn</a>
        <br>
        Powered by Streamlit & Google Earth Engine
    </div>
    """,
    unsafe_allow_html=True,
)
