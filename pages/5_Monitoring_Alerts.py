import streamlit as st
import pandas as pd
import json
import time
from services.storage import (
    save_preference, get_preference, add_region, get_all_regions, delete_region,
    set_threshold, get_thresholds, get_recent_alerts, get_unread_count, mark_all_read
)
from services.monitoring import run_monitoring_job
from components.ui import apply_enhanced_css, render_page_header
from india_cities import get_states, get_cities, get_city_coordinates
from services.gee_core import get_city_geometry

st.set_page_config(layout="wide", page_title="Monitoring & Alerts")
apply_enhanced_css()

render_page_header("🔔 Continuous Monitoring", "Automated Environmental Surveillance System")

# check deps
try:
    import apscheduler
except ImportError:
    st.error("APScheduler not installed. Please add it to requirements.txt")
    st.stop()

# --- tabs ---
tab_dashboard, tab_regions, tab_settings = st.tabs(["📊 Alert Dashboard", "🌍 Monitored Regions", "⚙️ Configuration"])

# --- DASHBOARD ---
with tab_dashboard:
    st.subheader("Live Status")
    
    col1, col2, col3 = st.columns(3)
    
    # Check if scheduler is running (we can't check variable directly across threads easily, 
    # but we can assume it's running if app.py started it. We'll show last run time if we logged it, 
    # but for now we'll show alert stats)
    
    unread = get_unread_count()
    with col1:
        st.metric("Unread Alerts", unread, delta_color="inverse" if unread > 0 else "normal")
    
    with col2:
        st.metric("Monitored Regions", len(get_all_regions()))
    
    with col3:
        if st.button("🔄 Trigger Run Now"):
            with st.spinner("Running monitoring job manually..."):
                run_monitoring_job()
            st.success("Job Complete! Check alerts below.")
            time.sleep(1)
            st.rerun()

    st.divider()
    st.subheader("📜 Alert History")
    
    if unread > 0:
        if st.button("Mark All Read"):
            mark_all_read()
            st.rerun()
    
    alerts = get_recent_alerts(20)
    if alerts:
        for alert in alerts:
            icon = "🔴" if alert['read'] == 0 else "⚪"
            with st.expander(f"{icon} {alert['timestamp']} - {alert['region_name']} ({alert['metric']})"):
                st.markdown(f"**Value:** {alert['value']:.2f}")
                st.info(alert['message'])
    else:
        st.caption("No recent alerts.")

# --- REGIONS ---
with tab_regions:
    st.subheader("Manage Areas of Interest")
    
    # Add new region
    with st.expander("➕ Add New Region", expanded=False):
        states = get_states()
        s_state = st.selectbox("State", states)
        cities = get_cities(s_state)
        s_city = st.selectbox("City", cities)
        
        if st.button("Add Region"):
            if s_city:
                coords = get_city_coordinates(s_state, s_city)
                if coords:
                    geom = get_city_geometry(coords['lat'], coords['lon'])
                    # Convert EE geometry to simple dict for storage/JSON
                    # EE geometry needs .getInfo() to get the dict structure used by our storage
                    try:
                        geom_dict = geom.getInfo() # Client-side call
                        if add_region(s_city, geom_dict):
                            st.success(f"Added {s_city}")
                            st.rerun()
                        else:
                            st.error("Region already exists or error saving.")
                    except Exception as e:
                        st.error(f"Error resolving geometry: {e}")
    
    # List regions
    regions = get_all_regions()
    if regions:
        for reg in regions:
            with st.container():
                c1, c2, c3 = st.columns([3, 4, 1])
                with c1:
                    st.markdown(f"### 📍 {reg['name']}")
                    st.caption(f"Added: {reg['created_at']}")
                
                with c2:
                    current_thresh = get_thresholds(reg['id'])
                    if current_thresh:
                        st.markdown("**Active Thresholds:**")
                        for t in current_thresh:
                            if t['enabled']:
                                st.markdown(f"- {t['metric']} {t['operator']} {t['value']}")
                    else:
                        st.warning("No thresholds set")
                    
                    # Add/Edit Threshold (Inline simplistic UI)
                    with st.popover("⚙️ Edit Thresholds"):
                        metric = st.selectbox(f"Metric ({reg['name']})", ["NO2", "PM25", "LST_Day", "LST_Night"], key=f"m_{reg['id']}")
                        op = st.selectbox(f"Operator ({reg['name']})", [">", "<"], key=f"o_{reg['id']}")
                        val = st.number_input(f"Value ({reg['name']})", value=50.0, key=f"v_{reg['id']}")
                        
                        if st.button("Save Threshold", key=f"btn_{reg['id']}"):
                            set_threshold(reg['id'], metric, op, val)
                            st.success("Saved!")
                            st.rerun()

                with c3:
                    if st.button("🗑️", key=f"del_{reg['id']}"):
                        delete_region(reg['id'])
                        st.rerun()
                st.divider()
    else:
        st.info("No monitored regions configured.")

# --- SETTINGS ---
with tab_settings:
    st.subheader("📞 Notification Channels")
    
    st.markdown("Configure where you want to receive alerts.")
    
    # Email
    st.checkbox("Enable Email Alerts", value=(get_preference("enable_email", "false")=="true"), 
                key="chk_email", on_change=lambda: save_preference("enable_email", st.session_state.chk_email))
    st.text_input("Recipient Email", value=get_preference("alert_email", ""), 
                  key="txt_email", on_change=lambda: save_preference("alert_email", st.session_state.txt_email))
    
    st.divider()
    
    # WhatsApp
    st.checkbox("Enable WhatsApp Alerts", value=(get_preference("enable_whatsapp", "false")=="true"), 
                key="chk_wa", on_change=lambda: save_preference("enable_whatsapp", st.session_state.chk_wa))
    st.caption("Requires Twilio configuration in secrets.toml")
    st.text_input("Recipient Phone (WhatsApp)", value=get_preference("alert_phone", ""), help="e.g. whatsapp:+919999999999",
                  key="txt_wa", on_change=lambda: save_preference("alert_phone", st.session_state.txt_wa))
    
    st.divider()
    
    st.info("System Configuration")
    st.text(f"Database Path: services/monitoring.db")
