import streamlit as st
import sys

sys.path.append(
    r"C:\Users\heman\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.13_qbz5n2kfra8p0\LocalCache\local-packages\Python313\site-packages"
)

from services.gee_core import auto_initialize_gee
from components.ui import apply_enhanced_css, render_page_header, init_common_session_state

st.set_page_config(
    page_title="India GIS & Remote Sensing Portal",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Fix for module reloading
if 'components' in sys.modules:
    import importlib
    import components.ui
    importlib.reload(components.ui)

from services.gee_core import auto_initialize_gee
from components.ui import apply_enhanced_css, render_page_header, init_common_session_state

auto_initialize_gee()
init_common_session_state()
apply_enhanced_css()

# Hero Section
st.markdown("""
<div class="animate-fade-in" style="text-align: center; margin-bottom: 3rem;">
    <div class="main-header">
        India GIS & Remote Sensing Portal
    </div>
    <div class="sub-header">
        Advanced Earth Observation and Environmental Analysis platform powered by Google Earth Engine.
        Monitor LULC changes, Air Quality, and Urban Heat trends with precision.
    </div>
</div>
""",
            unsafe_allow_html=True)

with st.sidebar:
    st.markdown("## 🔐 GEE Status")
    if st.session_state.gee_initialized:
        st.success("GEE Connected")
    else:
        st.error("GEE Not Connected - Check secrets.toml")

# Main Features Grid
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown("""
    <div class="feature-card animate-fade-in" style="height: 100%;">
        <div class="card-header">
            <span style="font-size: 1.5rem;">🌍</span> LULC & Vegetation
        </div>
        <p style="color: #cbd5e1; margin-bottom: 1.5rem;">
            Analyze Land Use, Land Cover, and Vegetation Indices using Sentinel-2 and Dynamic World data.
        </p>
        <ul style="color: #f1f5f9; font-size: 0.9rem; margin-bottom: 1.5rem; padding-left: 1.2rem;">
            <li>Dynamic World (9 classes)</li>
            <li>Vegetation Indices (NDVI)</li>
            <li>Change Detection</li>
        </ul>
    </div>
    """,
                unsafe_allow_html=True)

    if st.button("Explore LULC Analysis →",
                 use_container_width=True,
                 type="primary"):
        st.switch_page("pages/1_LULC_Vegetation.py")

with col2:
    st.markdown("""
    <div class="feature-card animate-fade-in" style="height: 100%; animation-delay: 0.1s;">
        <div class="card-header">
            <span style="font-size: 1.5rem;">🌫️</span> Air Quality
        </div>
        <p style="color: #cbd5e1; margin-bottom: 1.5rem;">
            Monitor atmospheric pollutants and visualize trends using high-resolution Sentinel-5P imagery.
        </p>
        <ul style="color: #f1f5f9; font-size: 0.9rem; margin-bottom: 1.5rem; padding-left: 1.2rem;">
            <li>6 Major Pollutants</li>
            <li>Anomaly Mapping</li>
            <li>Multi-pollutant Dashboard</li>
        </ul>
    </div>
    """,
                unsafe_allow_html=True)

    if st.button("Explore AQI Analysis →",
                 use_container_width=True,
                 type="primary"):
        st.switch_page("pages/2_AQI_Analysis.py")

with col3:
    st.markdown("""
    <div class="feature-card animate-fade-in" style="height: 100%; animation-delay: 0.2s;">
        <div class="card-header">
            <span style="font-size: 1.5rem;">🌡️</span> Urban Heat
        </div>
        <p style="color: #cbd5e1; margin-bottom: 1.5rem;">
            Investigate Land Surface Temperature patterns and Urban Heat Island effects using MODIS data.
        </p>
        <ul style="color: #f1f5f9; font-size: 0.9rem; margin-bottom: 1.5rem; padding-left: 1.2rem;">
            <li>LST & UHI Intensity</li>
            <li>Cooling Zones</li>
            <li>Warming Trends</li>
        </ul>
    </div>
    """,
                unsafe_allow_html=True)

    if st.button("Explore Heat Analysis →",
                 use_container_width=True,
                 type="primary"):
        st.switch_page("pages/3_Urban_Heat_Climate.py")

with col4:
    st.markdown("""
    <div class="feature-card animate-fade-in" style="height: 100%; animation-delay: 0.3s; border-color: #8b5cf6;">
        <div class="card-header">
            <span style="font-size: 1.5rem;">🔮</span> AI Prediction
        </div>
        <p style="color: #cbd5e1; margin-bottom: 1.5rem;">
            Forecast future environmental trends using Machine Learning and historical data.
        </p>
        <ul style="color: #f1f5f9; font-size: 0.9rem; margin-bottom: 1.5rem; padding-left: 1.2rem;">
            <li>Forecast NDVI & LST</li>
            <li>Predict Air Quality</li>
            <li>Linear/Random Forest</li>
        </ul>
    </div>
    """,
                unsafe_allow_html=True)

    if st.button("Explore Prediction →",
                 use_container_width=True,
                 type="primary"):
        st.switch_page("pages/4_Predictive_Analysis.py")

st.markdown("---")

st.markdown(
    '<h3 style="color: #f1f5f9; margin-bottom: 1rem;">🛰️ Integrated Data Sources</h3>',
    unsafe_allow_html=True)

data_col1, data_col2, data_col3, data_col4 = st.columns(4)

source_style = """
<div class="feature-card" style="padding: 1rem; text-align: center;">
    <div style="font-weight: 700; color: #f1f5f9; margin-bottom: 0.25rem;">{title}</div>
    <div style="font-size: 0.8rem; color: #cbd5e1;">{desc}</div>
</div>
"""

with data_col1:
    st.markdown(source_style.format(title="Sentinel-2",
                                    desc="10m Optical • 5-day Revisit"),
                unsafe_allow_html=True)
with data_col2:
    st.markdown(source_style.format(title="Landsat 8/9",
                                    desc="30m Thermal • 16-day Revisit"),
                unsafe_allow_html=True)
with data_col3:
    st.markdown(source_style.format(title="Sentinel-5P",
                                    desc="Air Quality • Daily Global"),
                unsafe_allow_html=True)
with data_col4:
    st.markdown(source_style.format(title="MODIS",
                                    desc="LST & Climate • Daily"),
                unsafe_allow_html=True)

st.markdown("---")
st.markdown(
    """
    <div style="text-align: center; color: #94a3b8; padding: 2rem; font-size: 0.9rem;">
        Made with ❤️ by <strong>Hemant Kumar</strong> • 
        <a href="https://www.linkedin.com/in/hemantkumar2430" target="_blank" style="color: #60a5fa; text-decoration: none;">LinkedIn</a>
        <br>
        <span style="opacity: 0.8;">Powered by Streamlit & Google Earth Engine</span>
    </div>
    """,
    unsafe_allow_html=True,
)
