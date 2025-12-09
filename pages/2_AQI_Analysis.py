import streamlit as st
import folium
from streamlit_folium import st_folium
from datetime import datetime, date, timedelta
import pandas as pd

from india_cities import get_states, get_cities, get_city_coordinates
from services.gee_core import (
    auto_initialize_gee, get_city_geometry, get_tile_url, 
    geojson_to_ee_geometry, get_safe_download_url,
    process_shapefile_upload, geojson_file_to_ee_geometry
)
from services.gee_aqi import (
    POLLUTANT_INFO, get_pollutant_image, get_pollutant_vis_params,
    calculate_pollutant_statistics, get_baseline_image, calculate_anomaly_map,
    get_anomaly_vis_params, create_smoothed_map, create_hotspot_mask,
    calculate_pollutant_correlations
)
from services.insights import generate_aqi_insights
from components.ui import (
    apply_enhanced_css, render_page_header, render_stat_card,
    render_info_box, init_common_session_state, render_pollutant_stat_card
)
from components.maps import (
    create_base_map, add_tile_layer, add_marker, add_buffer_circle, add_layer_control,
    add_geojson_boundary
)
from components.legends import (
    render_pollutant_legend_with_opacity, render_anomaly_legend, render_hotspot_legend
)
from components.charts import (
    render_line_chart, render_multi_pollutant_chart, 
    render_correlation_heatmap, render_radar_chart
)
from services.exports import (
    generate_aqi_csv, generate_time_series_csv, generate_aqi_pdf_report,
    calculate_aqi_compliance_score
)

def format_aqi_value(value, decimals=2):
    if value is None:
        return "N/A"
    if abs(value) >= 10000:
        return f"{value:.2e}"
    elif abs(value) >= 1000:
        return f"{value:,.0f}"
    elif abs(value) >= 100:
        return f"{value:.1f}"
    elif abs(value) >= 10:
        return f"{value:.2f}"
    elif abs(value) >= 1:
        return f"{value:.3f}"
    elif abs(value) >= 0.01:
        return f"{value:.4f}"
    elif value == 0:
        return "0"
    else:
        return f"{value:.2e}"

st.set_page_config(
    page_title="AQI Analysis",
    page_icon="🌫️",
    layout="wide",
    initial_sidebar_state="expanded",
)

auto_initialize_gee()
init_common_session_state()
apply_enhanced_css()

render_page_header(
    "🌫️ Air Quality Analysis",
    "Analyze Air Pollutants using Sentinel-5P Data"
)

if "aqi_analysis_complete" not in st.session_state:
    st.session_state.aqi_analysis_complete = False
if "aqi_time_series" not in st.session_state:
    st.session_state.aqi_time_series = {}
if "aqi_tile_urls" not in st.session_state:
    st.session_state.aqi_tile_urls = {}

with st.sidebar:
    st.markdown("## 🔐 GEE Status")
    if st.session_state.gee_initialized:
        st.success("GEE Connected")
    else:
        st.error("GEE Not Connected")
    
    st.markdown("---")
    st.markdown("## 📍 Location")
    
    location_mode = st.radio(
        "Input Method",
        ["City Selection", "Upload Shapefile/GeoJSON"],
        key="aqi_location_mode",
        horizontal=True
    )
    
    selected_city = None
    city_coords = None
    uploaded_geometry = None
    uploaded_center = None
    uploaded_geojson = None
    
    if location_mode == "City Selection":
        states = get_states()
        selected_state = st.selectbox("State", ["Select..."] + states, key="aqi_state")
        
        if selected_state != "Select...":
            cities = get_cities(selected_state)
            selected_city = st.selectbox("City", ["Select..."] + cities, key="aqi_city")
            
            if selected_city != "Select...":
                city_coords = get_city_coordinates(selected_state, selected_city)
                if city_coords:
                    st.success(f"📍 {selected_city}, {selected_state}")
    else:
        selected_state = "Custom AOI"
        st.markdown("##### Upload Files")
        st.caption("Upload Shapefile (.shp + .shx + .dbf + .prj), .zip, or GeoJSON file.")
        
        uploaded_files = st.file_uploader(
            "Choose files",
            type=["shp", "shx", "dbf", "prj", "cpg", "zip", "geojson", "json"],
            accept_multiple_files=True,
            key="aqi_shapefile_upload"
        )
        
        if uploaded_files:
            geojson_files = [f for f in uploaded_files if f.name.endswith(('.geojson', '.json'))]
            zip_files = [f for f in uploaded_files if f.name.endswith('.zip')]
            shp_files = [f for f in uploaded_files if f.name.endswith('.shp')]
            
            if geojson_files:
                geom, center, geojson_data, error = geojson_file_to_ee_geometry(geojson_files[0])
                if error:
                    st.error(error)
                else:
                    uploaded_geometry = geom
                    uploaded_center = center
                    uploaded_geojson = geojson_data
                    city_coords = center
                    selected_city = "Custom Area"
                    st.success(f"✅ GeoJSON loaded! Center: {center['lat']:.4f}, {center['lon']:.4f}")
            elif zip_files or shp_files:
                geom, center, geojson_data, error = process_shapefile_upload(uploaded_files)
                if error:
                    st.error(error)
                else:
                    uploaded_geometry = geom
                    uploaded_center = center
                    uploaded_geojson = geojson_data
                    city_coords = center
                    selected_city = "Custom Area"
                    st.success(f"✅ Shapefile loaded! Center: {center['lat']:.4f}, {center['lon']:.4f}")
            else:
                st.warning("Please upload all required shapefile components or a .zip file")
    
    st.markdown("---")
    st.markdown("## 📅 Time Period")
    
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input(
            "Start",
            value=date.today() - timedelta(days=30),
            max_value=date.today(),
            key="aqi_start"
        )
    with col2:
        end_date = st.date_input(
            "End",
            value=date.today(),
            max_value=date.today(),
            key="aqi_end"
        )
    
    st.markdown("---")
    st.markdown("## 🌫️ Pollutants")
    
    pollutant_options = list(POLLUTANT_INFO.keys())
    selected_pollutants = st.multiselect(
        "Select Pollutants",
        pollutant_options,
        default=["NO2"],
        key="aqi_pollutants"
    )
    
    primary_pollutant = None
    if selected_pollutants:
        primary_pollutant = st.selectbox(
            "Primary (for map)",
            selected_pollutants,
            key="aqi_primary"
        )
    
    st.markdown("---")
    st.markdown("## 🗺️ Map Layers")
    
    show_base_layer = st.checkbox("Base Concentration", value=True, key="aqi_base")
    show_anomaly = st.checkbox("Anomaly Map", value=False, key="aqi_anomaly")
    show_smoothed = st.checkbox("Smoothed/Plume", value=False, key="aqi_smoothed")
    show_hotspots = st.checkbox("Hotspot Mask", value=False, key="aqi_hotspots")
    
    buffer_km = st.slider("Radius (km)", 10, 100, 30, key="aqi_buffer")
    
    st.markdown("---")
    st.markdown("## 📈 Analysis Options")
    
    show_time_series = st.checkbox("Time Series Analysis", value=False, key="aqi_time_series_opt")
    show_dashboard = st.checkbox("Multi-Pollutant Dashboard", value=False, key="aqi_dashboard")

if city_coords and st.session_state.gee_initialized and selected_pollutants:
    use_uploaded_aoi = uploaded_geometry is not None
    
    run_analysis = st.sidebar.button("🚀 Run Analysis", use_container_width=True, type="primary")
    
    base_map = create_base_map(city_coords["lat"], city_coords["lon"], zoom=10)
    
    if not use_uploaded_aoi:
        add_marker(base_map, city_coords["lat"], city_coords["lon"], 
                   popup=f"{selected_city}", tooltip=selected_city)
        add_buffer_circle(base_map, city_coords["lat"], city_coords["lon"], buffer_km)
    else:
        if uploaded_geojson:
            add_geojson_boundary(base_map, uploaded_geojson, name="Uploaded AOI", 
                               color="#ff7800", weight=3, fill_opacity=0.15)
        add_marker(base_map, city_coords["lat"], city_coords["lon"], 
                   popup="Custom Area Center", tooltip="Custom Area")
    
    if run_analysis:
        with st.spinner("Fetching Sentinel-5P data..."):
            try:
                if use_uploaded_aoi and uploaded_geometry:
                    geometry = uploaded_geometry
                    st.info("Using uploaded shapefile/GeoJSON geometry")
                else:
                    geometry = get_city_geometry(city_coords["lat"], city_coords["lon"], buffer_km)
                st.session_state.current_geometry = geometry
                
                start_str = start_date.strftime("%Y-%m-%d")
                end_str = end_date.strftime("%Y-%m-%d")
                
                st.session_state.pollutant_images = {}
                st.session_state.pollutant_stats = {}
                st.session_state.aqi_tile_urls = {}
                st.session_state.aqi_primary_pollutant = primary_pollutant
                
                for pollutant in selected_pollutants:
                    image = get_pollutant_image(geometry, pollutant, start_str, end_str)
                    if image:
                        st.session_state.pollutant_images[pollutant] = image
                        stats = calculate_pollutant_statistics(image, geometry, pollutant)
                        st.session_state.pollutant_stats[pollutant] = stats
                
                if primary_pollutant and primary_pollutant in st.session_state.pollutant_images:
                    primary_image = st.session_state.pollutant_images[primary_pollutant]
                    
                    if show_base_layer:
                        vis_params = get_pollutant_vis_params(primary_pollutant)
                        tile_url = get_tile_url(primary_image, vis_params)
                        st.session_state.aqi_tile_urls["base"] = {
                            "url": tile_url,
                            "name": f"{primary_pollutant} Concentration"
                        }
                    
                    if show_anomaly:
                        baseline = get_baseline_image(geometry, primary_pollutant)
                        if baseline:
                            anomaly = calculate_anomaly_map(primary_image, baseline)
                            if anomaly:
                                anomaly_params = get_anomaly_vis_params(primary_pollutant)
                                anomaly_url = get_tile_url(anomaly, anomaly_params)
                                st.session_state.aqi_tile_urls["anomaly"] = {
                                    "url": anomaly_url,
                                    "name": f"{primary_pollutant} Anomaly"
                                }
                    
                    if show_smoothed:
                        smoothed = create_smoothed_map(primary_image)
                        if smoothed:
                            vis_params = get_pollutant_vis_params(primary_pollutant)
                            smoothed_url = get_tile_url(smoothed, vis_params)
                            st.session_state.aqi_tile_urls["smoothed"] = {
                                "url": smoothed_url,
                                "name": f"{primary_pollutant} Smoothed"
                            }
                    
                    if show_hotspots:
                        hotspot = create_hotspot_mask(primary_image, geometry)
                        if hotspot:
                            hotspot_params = get_hotspot_vis_params()
                            hotspot_url = get_tile_url(hotspot, hotspot_params)
                            st.session_state.aqi_tile_urls["hotspots"] = {
                                "url": hotspot_url,
                                "name": f"{primary_pollutant} Hotspots"
                            }
                
                if show_time_series:
                    st.session_state.aqi_time_series = {}
                    for pollutant in selected_pollutants:
                        ts = get_pollutant_time_series(geometry, pollutant, start_str, end_str, interval_days=7)
                        if ts:
                            ts_with_rolling = calculate_rolling_average(ts, window=3)
                            st.session_state.aqi_time_series[pollutant] = ts_with_rolling
                
                if show_dashboard and len(selected_pollutants) > 1:
                    st.session_state.correlations = calculate_pollutant_correlations(
                        geometry, selected_pollutants, start_str, end_str
                    )
                
                st.session_state.aqi_analysis_complete = True
                st.session_state.aqi_pdf = None
                st.success("Analysis complete!")
            
            except Exception as e:
                st.error(f"Error: {str(e)}")
    
    if st.session_state.get("aqi_tile_urls"):
        for layer_type, layer_info in st.session_state.aqi_tile_urls.items():
            opacity = 0.8 if layer_type == "base" else 0.7
            add_tile_layer(base_map, layer_info["url"], layer_info["name"], opacity)
    
    add_layer_control(base_map)
    
    st.markdown(f"### 🗺️ {selected_city} - Air Quality Map")
    st.markdown('<div class="map-container">', unsafe_allow_html=True)
    st_folium(base_map, width=None, height=500)
    st.markdown('</div>', unsafe_allow_html=True)
    
    if st.session_state.get("aqi_analysis_complete"):
        st.markdown("---")
        st.markdown("## 📊 Analysis Results")
        
        if st.session_state.get("pollutant_stats"):
            num_pollutants = len(selected_pollutants)
            stat_cols = st.columns(min(num_pollutants, 4))
            
            for i, pollutant in enumerate(selected_pollutants):
                stats = st.session_state.pollutant_stats.get(pollutant)
                if stats:
                    info = POLLUTANT_INFO.get(pollutant, {})
                    with stat_cols[i % len(stat_cols)]:
                        mean_val = format_aqi_value(stats.get('mean', 0))
                        st.markdown(f"""
                        <div class="stat-card">
                            <div class="stat-value">{mean_val}</div>
                            <div class="stat-label">{info.get('name', pollutant)} Mean</div>
                            <div style="font-size: 0.75rem; color: #888;">{stats.get('unit', '')}</div>
                        </div>
                        """, unsafe_allow_html=True)
        
        res_col1, res_col2 = st.columns(2)
        
        with res_col1:
            st.markdown("### 📈 Detailed Statistics")
            for pollutant in selected_pollutants:
                stats = st.session_state.pollutant_stats.get(pollutant)
                if stats:
                    info = POLLUTANT_INFO.get(pollutant, {})
                    
                    with st.expander(f"📈 {info.get('name', pollutant)}", expanded=(pollutant == primary_pollutant)):
                        m_col1, m_col2, m_col3 = st.columns(3)
                        with m_col1:
                            st.metric("Mean", format_aqi_value(stats.get('mean', 0)))
                            st.metric("Median", format_aqi_value(stats.get('median', 0)))
                        with m_col2:
                            st.metric("Std Dev", format_aqi_value(stats.get('std_dev', 0)))
                            st.metric("P90", format_aqi_value(stats.get('p90', 0)))
                        with m_col3:
                            st.metric("Min", format_aqi_value(stats.get('min', 0)))
                            st.metric("Max", format_aqi_value(stats.get('max', 0)))
                        
                        st.caption(f"Unit: {stats.get('unit', '')}")
        
        with res_col2:
            st.markdown("### 🎨 Map Legends")
            
            if primary_pollutant:
                render_pollutant_legend_with_opacity(primary_pollutant, key_prefix="aqi_")
                
                if show_anomaly:
                    render_anomaly_legend(primary_pollutant)
                
                if show_hotspots:
                    render_hotspot_legend()
            
            st.markdown("### 📥 Export Options")
            
            exp_col1, exp_col2, exp_col3 = st.columns(3)
            
            with exp_col1:
                if st.button("📦 Generate GeoTIFF", use_container_width=True, key="aqi_export"):
                    if primary_pollutant and primary_pollutant in st.session_state.get("pollutant_images", {}):
                        with st.spinner("Generating..."):
                            url, error = get_safe_download_url(
                                st.session_state.pollutant_images[primary_pollutant],
                                st.session_state.current_geometry,
                                scale=1000
                            )
                            if url:
                                st.success("Ready!")
                                st.markdown(f"[📥 Download]({url})")
                            elif error:
                                st.warning(error)
            
            with exp_col2:
                if primary_pollutant and st.session_state.pollutant_stats.get(primary_pollutant):
                    csv_data = generate_aqi_csv(
                        st.session_state.pollutant_stats[primary_pollutant],
                        primary_pollutant, selected_city,
                        f"{start_date} to {end_date}"
                    )
                    if csv_data:
                        st.download_button(
                            "📄 Download CSV",
                            data=csv_data,
                            file_name=f"{primary_pollutant}_stats_{selected_city}.csv",
                            mime="text/csv",
                            key="dl_primary_csv",
                            use_container_width=True
                        )
            
            with exp_col3:
                if st.session_state.pollutant_stats:
                    if 'aqi_pdf' not in st.session_state or st.session_state.aqi_pdf is None:
                        compliance = calculate_aqi_compliance_score(st.session_state.pollutant_stats)
                        ts_data = st.session_state.get("aqi_time_series", {})
                        report_data = {
                            'city_name': selected_city,
                            'state': selected_state,
                            'date_range': f"{start_date} to {end_date}",
                            'pollutants': selected_pollutants,
                            'pollutant_stats': st.session_state.pollutant_stats,
                            'time_series': ts_data
                        }
                        
                        # Generate Insights
                        report_data['insights'] = generate_aqi_insights(st.session_state.pollutant_stats)
                        
                        st.session_state.aqi_pdf = generate_aqi_pdf_report(report_data)
                    
                    if st.session_state.get("aqi_pdf"):
                        st.download_button(
                            "📥 Download PDF Report",
                            data=st.session_state.aqi_pdf,
                            file_name=f"aqi_report_{selected_city}.pdf",
                            mime="application/pdf",
                            use_container_width=True,
                            key="dl_aqi_pdf"
                        )
                    else:
                        st.error("Failed to generate PDF")
        
        if show_time_series and st.session_state.get("aqi_time_series"):
            st.markdown("---")
            st.markdown("### 📈 Time Series Analysis")
            
            ts_cols = st.columns(min(len(st.session_state.aqi_time_series), 2))
            
            for i, (pollutant, ts_data) in enumerate(st.session_state.aqi_time_series.items()):
                with ts_cols[i % len(ts_cols)]:
                    info = POLLUTANT_INFO.get(pollutant, {})
                    st.markdown(f"#### {info.get('name', pollutant)}")
                    render_line_chart(
                        ts_data,
                        title=f"{pollutant} Over Time",
                        y_label=info.get('display_unit', ''),
                        show_rolling=True
                    )
                    
                    if ts_data:
                        csv_data = generate_time_series_csv(ts_data, pollutant, selected_city)
                        if csv_data:
                            st.download_button(
                                f"📥 Download {pollutant} Time Series",
                                data=csv_data,
                                file_name=f"{pollutant}_timeseries_{selected_city}.csv",
                                mime="text/csv",
                                key=f"dl_ts_{pollutant}"
                            )
        
        if show_dashboard and len(selected_pollutants) > 1:
            st.markdown("---")
            st.markdown("### 📊 Multi-Pollutant Dashboard")
            
            dash_col1, dash_col2 = st.columns(2)
            
            with dash_col1:
                st.markdown("#### Correlation Matrix")
                if st.session_state.get("correlations"):
                    render_correlation_heatmap(
                        st.session_state.correlations,
                        selected_pollutants,
                        "Pollutant Correlations"
                    )
            
            with dash_col2:
                st.markdown("#### Average Concentrations")
                if st.session_state.get("pollutant_stats"):
                    avg_data = {}
                    for p, stats in st.session_state.pollutant_stats.items():
                        if stats and "mean" in stats:
                            avg_data[p] = stats["mean"]
                    
                    if avg_data:
                        render_radar_chart(avg_data, "Pollutant Levels (Normalized)")
            
            if st.session_state.get("aqi_time_series"):
                st.markdown("#### Multi-Pollutant Comparison")
                render_multi_pollutant_chart(
                    st.session_state.aqi_time_series,
                    "Multi-Pollutant Time Series Comparison"
                )

elif not st.session_state.gee_initialized:
    render_info_box("Please check your GEE credentials in secrets.toml", "warning")
elif not selected_pollutants:
    render_info_box("Please select at least one pollutant to analyze", "info")
else:
    render_info_box("""
        <h4>Getting Started with AQI Analysis</h4>
        <ol>
            <li>Select a State and City</li>
            <li>Choose date range for analysis</li>
            <li>Select pollutants to analyze (NO₂, SO₂, CO, O₃, UVAI, CH₄)</li>
            <li>Enable map layers and analysis options</li>
            <li>Click Run Analysis</li>
        </ol>
        <h4>Available Features</h4>
        <ul>
            <li><b>Base Concentration:</b> Current pollutant levels</li>
            <li><b>Anomaly Map:</b> Difference from 2019 baseline</li>
            <li><b>Smoothed/Plume:</b> Gaussian smoothed visualization</li>
            <li><b>Hotspot Mask:</b> Areas above mean + 1.5σ</li>
            <li><b>Time Series:</b> Temporal analysis with rolling averages</li>
            <li><b>Dashboard:</b> Multi-pollutant correlations and comparisons</li>
        </ul>
    """, "info")

st.markdown("---")
st.markdown("### 📚 Pollutant Reference")

ref_cols = st.columns(3)
for i, (pollutant, info) in enumerate(POLLUTANT_INFO.items()):
    with ref_cols[i % 3]:
        st.markdown(f"""
        <div class="stat-card" style="margin-bottom: 0.5rem;">
            <div style="font-weight: 600;">{pollutant}</div>
            <div style="font-size: 0.85rem; color: #666;">{info['name']}</div>
            <div style="font-size: 0.75rem; margin-top: 0.5rem;">{info['description']}</div>
        </div>
        """, unsafe_allow_html=True)
