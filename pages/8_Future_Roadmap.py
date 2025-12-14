import streamlit as st
from components.ui import apply_enhanced_css, render_page_header

st.set_page_config(layout="wide", page_title="Future Roadmap", page_icon="🚀")

apply_enhanced_css()

render_page_header(
    "🚀 Future Roadmap",
    "Explore upcoming features and the development timeline for the India GIS Portal."
)

st.markdown("""
<div style="background-color: rgba(30, 41, 59, 0.5); padding: 2rem; border-radius: 10px; border: 1px solid rgba(56, 189, 248, 0.2);">
    <h3 style="color: #38bdf8; margin-bottom: 1.5rem;">📅 Q1 2026 Objectives</h3>
    <ul style="list-style-type: none; padding-left: 0; color: #cbd5e1;">
        <li style="margin-bottom: 1rem; display: flex; align-items: flex-start;">
            <span style="font-size: 1.2rem; margin-right: 0.8rem;">🌊</span>
            <div>
                <strong style="color: #f1f5f9;">Real-time Flood Monitoring System</strong>
                <p style="font-size: 0.9rem; opacity: 0.8;">Integration with SAR data for flood extent mapping and damage assessment.</p>
            </div>
        </li>
        <li style="margin-bottom: 1rem; display: flex; align-items: flex-start;">
            <span style="font-size: 1.2rem; margin-right: 0.8rem;">📱</span>
            <div>
                <strong style="color: #f1f5f9;">Mobile Application</strong>
                <p style="font-size: 0.9rem; opacity: 0.8;">Native mobile app for field data collection and on-the-go alerts.</p>
            </div>
        </li>
        <li style="margin-bottom: 1rem; display: flex; align-items: flex-start;">
            <span style="font-size: 1.2rem; margin-right: 0.8rem;">💾</span>
            <div>
                <strong style="color: #f1f5f9;">Offline Mode</strong>
                <p style="font-size: 0.9rem; opacity: 0.8;">Allow users to cache maps and reports for use in low-connectivity areas.</p>
            </div>
        </li>
         <li style="margin-bottom: 1rem; display: flex; align-items: flex-start;">
            <span style="font-size: 1.2rem; margin-right: 0.8rem;">📡</span>
            <div>
                <strong style="color: #f1f5f9;">API Access</strong>
                <p style="font-size: 0.9rem; opacity: 0.8;">Developer API for programmatic access to processed environmental data.</p>
            </div>
        </li>
    </ul>
</div>

<div style="margin-top: 2rem; background-color: rgba(30, 41, 59, 0.5); padding: 2rem; border-radius: 10px; border: 1px solid rgba(16, 185, 129, 0.2);">
    <h3 style="color: #34d399; margin-bottom: 1.5rem;">✅ Completed Milestones</h3>
    <ul style="list-style-type: none; padding-left: 0; color: #cbd5e1;">
         <li style="margin-bottom: 0.8rem;">✔️ <strong>LULC & Vegetation Analysis</strong> (Sentinel-2 Integration)</li>
         <li style="margin-bottom: 0.8rem;">✔️ <strong>Air Quality Monitoring</strong> (Sentinel-5P Integration)</li>
         <li style="margin-bottom: 0.8rem;">✔️ <strong>Urban Heat Island Tracking</strong> (MODIS Integration)</li>
         <li style="margin-bottom: 0.8rem;">✔️ <strong>AI-Powered Forecasting</strong> (Prophet/Random Forest)</li>
         <li style="margin-bottom: 0.8rem;">✔️ <strong>Earthquake Hazard Module</strong> (USGS Real-time Feed)</li>
         <li style="margin-bottom: 0.8rem;">✔️ <strong>Regional Comparison Module</strong></li>
         <li style="margin-bottom: 0.8rem;">✔️ <strong>Comprehensive PDF Reporting</strong></li>
    </ul>
</div>
""", unsafe_allow_html=True)
