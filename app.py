import streamlit as st
import sys

from services.gee_core import auto_initialize_gee
from components.ui import (
    apply_enhanced_css, render_page_header, render_feature_card,
    init_common_session_state,
)

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
from components.ui import apply_enhanced_css, render_page_header, render_feature_card, init_common_session_state

auto_initialize_gee()
init_common_session_state()
apply_enhanced_css()

render_page_header(
    "🛰️ India GIS & Remote Sensing Portal",
    "Advanced Earth Observation and Environmental Analysis platform powered by Google Earth Engine. "
    "Monitor LULC changes, Air Quality, and Urban Heat trends with precision.",
    hero=True
)

with st.sidebar:
    st.markdown("## 🔐 GEE Status")
    if st.session_state.gee_initialized:
        st.success("GEE Connected")
    else:
        st.error("GEE Not Connected - Check secrets.toml")

# Feature modules: (icon, title, description, bullets, accent, button label, page path)
FEATURES = [
    ("🌍", "LULC & Vegetation",
     "Analyze Land Use, Land Cover, and Vegetation Indices using Sentinel-2 and Dynamic World data.",
     ["Dynamic World (9 classes)", "Vegetation Indices (NDVI)", "Change Detection"],
     "#34d399", "Explore LULC Analysis →", "pages/1_LULC_Vegetation.py"),

    ("🌫️", "Air Quality",
     "Monitor atmospheric pollutants and visualize trends using high-resolution Sentinel-5P imagery.",
     ["6 Major Pollutants", "Anomaly Mapping", "Multi-pollutant Dashboard"],
     "#fbbf24", "Explore AQI Analysis →", "pages/2_AQI_Analysis.py"),

    ("🌡️", "Urban Heat",
     "Investigate Land Surface Temperature patterns and Urban Heat Island effects using MODIS data.",
     ["LST & UHI Intensity", "Cooling Zones", "Warming Trends"],
     "#fb7185", "Explore Heat Analysis →", "pages/3_Urban_Heat_Climate.py"),

    ("🔮", "AI Prediction",
     "Forecast future environmental trends using Machine Learning and historical data.",
     ["Forecast NDVI & LST", "Predict Air Quality", "Linear/Random Forest"],
     "#a78bfa", "Explore Prediction →", "pages/4_Predictive_Analysis.py"),

    ("🏔️", "Earthquake Hazard",
     "Real-time seismic activity tracking, Probabilistic Hazard Mapping, and Risk Reporting.",
     ["Real-time USGS Feed", "Seismic Hazard Zones", "Risk Scores"],
     "#fb923c", "Explore Hazards →", "pages/5_Earthquake_Hazard.py"),

    ("📊", "Comprehensive Report",
     "Generate holistic sustainability reports combining all environmental data points.",
     ["Sustainability Score", "Actionable Roadmap", "PDF Export"],
     "#2dd4bf", "Generate Report →", "pages/6_Comprehensive_Report.py"),

    ("⚖️", "Comparison Module",
     "Compare environmental metrics side-by-side between two different regions.",
     ["Side-by-side Maps", "Diff Calculation", "Radar Chart Overlay"],
     "#38bdf8", "Explore Comparison →", "pages/7_Comparison_Module.py"),

    ("🚀", "Future Roadmap",
     "Explore upcoming features, development timelines, and project milestones.",
     ["Carbon Sequestration", "Soil Moisture & Degradation", "Cyclone Tracking"],
     "#e879f9", "View Roadmap →", "pages/8_Future_Roadmap.py"),

    ("📚", "Methodology & Limitations",
     "Understand the technical details, data sources, and scoring logic behind the platform.",
     ["Data Sources", "Scoring Algorithms", "Limitations & Disclaimer"],
     "#818cf8", "Read Methodology →", "pages/9_Methodology_Limitations.py"),

    ("💧", "Jal-AI: Water Resilience",
     "Advanced hydrological monitoring for floods, droughts, and real-time surface water dynamics. "
     "Developed for Water Hackathon 2026.",
     ["Flood Watch (SAR Radar)", "Surface Water Area (NDWI)", "Gender-Socio Resilience"],
     "#60a5fa", "Explore Jal-AI →", "pages/10_Jal_AI_Water_Resilience.py"),
]

for row_start in range(0, len(FEATURES), 4):
    row = FEATURES[row_start:row_start + 4]
    cols = st.columns(4)
    for i, (col, (icon, title, desc, bullets, accent, label, path)) in enumerate(zip(cols, row)):
        with col:
            clicked = render_feature_card(
                icon, title, desc, bullets, accent, label, path,
                delay=(row_start + i) * 0.08,
            )
            if clicked:
                st.switch_page(path)
    st.markdown("<div style='margin-top: 0.5rem;'></div>", unsafe_allow_html=True)

st.markdown("---")

st.markdown(
    '<h3 style="color: var(--text-primary); margin-bottom: 1rem;">🛰️ Integrated Data Sources</h3>',
    unsafe_allow_html=True)

data_sources = [
    ("Sentinel-2", "10m Optical • 5-day Revisit"),
    ("Landsat 8/9", "30m Thermal • 16-day Revisit"),
    ("Sentinel-5P", "Air Quality • Daily Global"),
    ("MODIS", "LST & Climate • Daily"),
]

source_style = """
<div class="feature-card" style="height: auto; padding: 1rem; text-align: center;">
    <div style="font-weight: 700; color: var(--text-primary); margin-bottom: 0.25rem;">{title}</div>
    <div style="font-size: 0.8rem; color: var(--text-secondary);">{desc}</div>
</div>
"""

for col, (title, desc) in zip(st.columns(4), data_sources):
    with col:
        st.markdown(source_style.format(title=title, desc=desc), unsafe_allow_html=True)

st.markdown("---")
st.markdown(
    """
    <div style="text-align: center; color: var(--text-muted); padding: 2rem; font-size: 0.9rem;">
        Made with ❤️ by <strong style="color: var(--text-primary);">Hemant Kumar</strong> •
        <a href="https://www.linkedin.com/in/hemantkumar2430" target="_blank" style="color: var(--accent); text-decoration: none;">LinkedIn</a>
        <br>
        <span style="opacity: 0.8;">Powered by Streamlit & Google Earth Engine</span>
    </div>
    """,
    unsafe_allow_html=True,
)
