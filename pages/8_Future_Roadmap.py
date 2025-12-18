import streamlit as st
import sys
from components.ui import apply_enhanced_css, render_page_header

st.set_page_config(layout="wide", page_title="Future Roadmap")

apply_enhanced_css()

# Custom CSS for this page to handle layout specifics
st.markdown("""
<style>
/* Remove Streamlit default padding for cleaner look */
.block-container {
    padding-top: 0rem !important;
    padding-bottom: 0rem !important;
    padding-left: 2rem !important;
    padding-right: 2rem !important;
}

/* Hide Streamlit elements */
header {visibility: hidden;}
footer {visibility: hidden;}
.viewerBadge_container__1QSob { display: none !important; }

/* Prevent double scrollbars handled in global css usually, but ensuring here */
html, body {
    overflow-x: hidden;
}
</style>
""", unsafe_allow_html=True)

render_page_header("🚀 Feature Roadmap",
                   "Strategic vision for platform evolution and advanced capabilities")

# Introductory Note
st.markdown("""
<div style="
    background: rgba(15, 23, 42, 0.6); 
    border-left: 4px solid #38bdf8; 
    padding: 1rem 1.5rem; 
    margin-bottom: 2.5rem; 
    border-radius: 4px;
    border: 1px solid rgba(56, 189, 248, 0.1);
">
    <p style="margin: 0; color: #cbd5e1; font-size: 0.95rem; line-height: 1.6;">
        <strong>Note:</strong> This roadmap outlines the research trajectory, analytical enhancements, and platform extensions currently in planning or development stages. 
        It represents our long-term vision to deliver state-of-the-art spatial intelligence and decision support capabilities beyond the current stable release.
    </p>
</div>
""", unsafe_allow_html=True)

# Roadmap Phases and Items Data Structure
roadmap_phases = {
    "Advanced Hazard Modules": [
        {
            "title": "Cyclone Tracking",
            "icon": "🌀",
            "desc": "Real-time cyclone path predictions and impact analysis using meteorological data feeds.",
            "status": "Advanced Analytics"
        },
        {
            "title": "Hydrological Flood Mapping",
            "icon": "💧",
            "desc": "Integrated flood simulation models for river basins using high-resolution terrain data.",
            "status": "In Development"
        },
        {
            "title": "Cross-Hazard Interaction",
            "icon": "⚡", 
            "desc": "Evaluating cascading effects where one hazard triggers or amplifies another (e.g., flood leading to landslide).",
            "status": "Planned"
        },
         {
            "title": "Exposure & Vulnerability",
            "icon": "🏘️",
            "desc": "Detailed assessment of population and infrastructure exposure to specific hazard intensities.",
            "status": "Research Phase"
        }
    ],
    "Environmental & Sustainability Analytics": [
        {
            "title": "Carbon Sequestration",
            "icon": "🌳",
            "desc": "Quantifying biomass carbon stocks and potential sequestration zones using multispectral satellite indices.",
            "status": "Coming Soon"
        },
         {
            "title": "Drought Monitoring",
            "icon": "🏜️",
            "desc": "Satellite-based drought indices (VCI, TCI) to assess agricultural stress and water scarcity.",
             "status": "In Development"
        },
        {
            "title": "Soil Moisture & Degradation",
            "icon": "📉",
            "desc": "Assessment of soil moisture variability and identification of land degradation hotspots employing remote sensing data.",
             "status": "Research Phase"
        },
         {
            "title": "SDG Mapping & Indicators",
            "icon": "🌐",
            "desc": "Monitoring progress towards Sustainable Development Goals with spatial indicators.",
             "status": "Planned"
        }
    ],
     "Spatial Intelligence & GIS Enhancements": [
        {
            "title": "Rainfall Trend Analysis",
            "icon": "☔",
            "desc": "Long-term precipitation pattern recognition and deviation detection for agricultural insights.",
             "status": "Coming Soon"
        },
        {
            "title": "Hotspot & Cluster Analysis",
            "icon": "🔥",
            "desc": "Statistical identification of spatial clusters and significant hotspots for various phenomena.",
             "status": "Advanced Analytics"
        },
         {
            "title": "Multi-Year Change Detection",
            "icon": "📅",
            "desc": "Automated detection of land cover implementation changes over long temporal baselines.",
             "status": "Planned"
        }
    ],
    "Decision Support & Scenario Analysis": [
        {
            "title": "Scenario-Based What-If Analysis",
            "icon": "🎲",
            "desc": "Interactive modeling to simulate outcomes of different policy or climate scenarios.",
             "status": "Conceptual"
        },
         {
            "title": "Urban Resilience Index",
            "icon": "🏙️",
            "desc": "Composite scoring system to measure the ability of urban areas to withstand and recover from shocks.",
             "status": "Research Phase"
        }
    ],
    "Platform & Research Extensions": [
        {
             "title": "Uncertainty Assessment",
            "icon": "📊",
            "desc": "Quantifying uncertainties in model outputs and analyzing sensitivity to input parameters.",
             "status": "Research Phase"
        }
    ]
}

def render_roadmap_card(item):
    """
    Renders a consistent roadmap card with status badge and description.
    """
    st.markdown(f"""
<div class="coming-soon-card animate-fade-in" style="height: 100%; min-height: 280px; display: flex; flex-direction: column;">
<div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 1rem;">
<div class="coming-soon-badge" style="margin-bottom: 0;">{item['status']}</div>
</div>
<div class="card-header" style="color: #cbd5e1; font-size: 1.15rem; margin-bottom: 1rem;">
<span style="font-size: 1.5rem; filter: grayscale(100%); margin-right: 10px;">{item['icon']}</span> {item['title']}
</div>
<p style="color: #94a3b8; font-size: 0.9rem; line-height: 1.5; margin-bottom: 1.5rem; flex-grow: 1;">
{item['desc']}
</p>
<div style="margin-top: auto; opacity: 0.4; border-top: 1px solid rgba(255,255,255,0.05); padding-top: 0.75rem;">
<div style="font-size: 0.75rem; color: #64748b; font-weight: 500; text-transform: uppercase; letter-spacing: 0.05em;">
Future Capability
</div>
</div>
</div>
""", unsafe_allow_html=True)

# Main Render Loop
# Iterate through each phase and render a section
for phase, items in roadmap_phases.items():
    st.markdown(f"""
<div style="display: flex; align-items: center; margin-top: 2.5rem; margin-bottom: 1.5rem;">
<h3 style="color: #f1f5f9; margin: 0; font-size: 1.4rem; font-weight: 600;">{phase}</h3>
<div style="flex-grow: 1; height: 1px; background: rgba(51, 65, 85, 0.5); margin-left: 1.5rem;"></div>
</div>
""", unsafe_allow_html=True)
    
    # Grid layout for cards
    # We use 3 columns for desktop
    cols = st.columns(3)
    for i, item in enumerate(items):
        with cols[i % 3]:
            render_roadmap_card(item)

# Footer Note
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #64748b; padding: 3rem 1rem; font-size: 0.85rem; max-width: 800px; margin: 0 auto;">
    <em>Disclaimer: All roadmap timelines and feature specifications are indicative and subject to user feedback, academic validation, mentor review, and research feasibility. 
    Priorities may evolve as we incorporate new insights and data sources.</em>
</div>
""", unsafe_allow_html=True)
