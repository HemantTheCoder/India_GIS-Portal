import streamlit as st
import sys
from components.ui import apply_enhanced_css, render_page_header

st.set_page_config(layout="wide", page_title="Future Roadmap")

apply_enhanced_css()
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
render_page_header("🚀 Feature Roadmap",
                   "Upcoming modules and advanced analytics under development")

# Helper to render coming soon card
def render_coming_soon_card(icon, title, desc):
    st.markdown(f"""
    <div class="coming-soon-card animate-fade-in">
        <div class="coming-soon-badge">Coming Soon</div>
        <div class="card-header" style="color: #cbd5e1;">
            <span style="font-size: 1.5rem; filter: grayscale(100%);">{icon}</span> {title}
        </div>
        <p style="color: #64748b; margin-bottom: 1.5rem;">
            {desc}
        </p>
        <div style="opacity: 0.5; pointer-events: none;">
             <button style="
                background: transparent;
                border: 1px solid #475569;
                color: #64748b;
                padding: 0.5rem 1rem;
                border-radius: 0.5rem;
                width: 100%;
                font-weight: 600;
                cursor: not-allowed;
             ">Under Development</button>
        </div>
    </div>
    """,
                unsafe_allow_html=True)

# Grid Layout
col1, col2 = st.columns(2)

with col1:
    render_coming_soon_card("🌀", "Cyclone Tracking",
                            "Real-time cyclone path predictions and impact analysis using meteorological data feeds.")
    
    render_coming_soon_card("💧", "Hydrological Flood Mapping",
                             "Integrated flood simulation models for river basins using high-resolution terrain data.")

with col2:
    render_coming_soon_card("☔", "Rainfall Trend Analysis",
                            "Long-term precipitation pattern recognition and deviation detection for agricultural insights.")
    
    render_coming_soon_card("🏜️", "Drought Monitoring",
                            "Satellite-based drought indices (VCI, TCI) to assess agricultural stress and water scarcity.")

st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #64748b; padding: 2rem;">
    <em>These modules are currently in the R&D phase. Stay tuned for updates!</em>
</div>
""", unsafe_allow_html=True)
