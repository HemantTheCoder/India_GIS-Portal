import streamlit as st
import folium
from streamlit_folium import st_folium
from datetime import datetime, date, timedelta
import pandas as pd
import numpy as np

from india_cities import get_states, get_cities, get_city_coordinates
from services.gee_core import (
    auto_initialize_gee, get_city_geometry, get_tile_url, 
    geojson_to_ee_geometry, get_safe_download_url,
    process_shapefile_upload, geojson_file_to_ee_geometry
)
from services.gee_lst import (
    get_mean_lst, get_lst_statistics, get_seasonal_lst, get_monthly_lst,
    calculate_lst_anomaly, calculate_uhi_intensity, detect_heat_hotspots,
    identify_cooling_zones, get_lst_time_series, detect_heatwaves,
    calculate_warming_trend, get_lst_tile_url,
    LST_VIS_PARAMS, UHI_VIS_PARAMS, ANOMALY_VIS_PARAMS, HOTSPOT_VIS_PARAMS, COOLING_VIS_PARAMS
)
from components.ui import (
    apply_enhanced_css, render_page_header, render_stat_card,
    render_info_box, init_common_session_state
)
from components.maps import (
    create_base_map, add_tile_layer, add_marker, add_buffer_circle, add_layer_control,
    add_geojson_boundary
)
from components.charts import render_line_chart
from services.exports import (
    generate_time_series_csv, generate_urban_heat_pdf_report,
    calculate_heat_vulnerability_score
)

def format_temp(value, decimals=1):
    if value is None:
        return "N/A"
    return f"{value:.{decimals}f}°C"

st.set_page_config(
    page_title="Urban Heat & Climate",
    page_icon="🌡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

auto_initialize_gee()
init_common_session_state()
apply_enhanced_css()

render_page_header(
    "🌡️ Urban Heat & Climate Analysis",
    "Land Surface Temperature, Urban Heat Islands, and Climate Trends"
)

if "lst_analysis_complete" not in st.session_state:
    st.session_state.lst_analysis_complete = False
if "lst_tile_urls" not in st.session_state:
    st.session_state.lst_tile_urls = {}
if "lst_time_series" not in st.session_state:
    st.session_state.lst_time_series = []
if "lst_center_coords" not in st.session_state:
    st.session_state.lst_center_coords = None
if "lst_location_name" not in st.session_state:
    st.session_state.lst_location_name = None
if "lst_stats" not in st.session_state:
    st.session_state.lst_stats = None
if "uhi_stats" not in st.session_state:
    st.session_state.uhi_stats = None
if "hotspot_stats" not in st.session_state:
    st.session_state.hotspot_stats = None
if "cooling_stats" not in st.session_state:
    st.session_state.cooling_stats = None
if "anomaly_stats" not in st.session_state:
    st.session_state.anomaly_stats = None
if "warming_trend" not in st.session_state:
    st.session_state.warming_trend = None

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
        key="lst_location_mode",
        horizontal=True
    )
    
    selected_city = None
    city_coords = None
    uploaded_geometry = None
    uploaded_center = None
    uploaded_geojson = None
    
    if location_mode == "City Selection":
        states = get_states()
        selected_state = st.selectbox("State", ["Select..."] + states, key="lst_state")
        
        if selected_state != "Select...":
            cities = get_cities(selected_state)
            selected_city = st.selectbox("City", ["Select..."] + cities, key="lst_city")
            
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
            key="lst_shapefile_upload"
        )
        
        if uploaded_files:
            file_names = [f.name for f in uploaded_files]
            is_geojson = any(f.name.endswith('.geojson') or f.name.endswith('.json') for f in uploaded_files)
            is_zip = any(f.name.endswith('.zip') for f in uploaded_files)
            has_shp = any(f.name.endswith('.shp') for f in uploaded_files)
            
            if is_geojson:
                geojson_file = next((f for f in uploaded_files if f.name.endswith('.geojson') or f.name.endswith('.json')), None)
                if geojson_file:
                    geom, center, geojson_data, error = geojson_file_to_ee_geometry(geojson_file)
                    if error:
                        st.error(error)
                    else:
                        uploaded_geometry = geom
                        uploaded_center = center
                        uploaded_geojson = geojson_data
                        city_coords = center
                        st.success(f"✅ GeoJSON loaded! Center: {center['lat']:.4f}, {center['lon']:.4f}")
                        selected_city = "Custom AOI"
            elif is_zip or has_shp:
                geom, center, geojson_data, error = process_shapefile_upload(uploaded_files)
                if error:
                    st.error(error)
                else:
                    uploaded_geometry = geom
                    uploaded_center = center
                    uploaded_geojson = geojson_data
                    city_coords = center
                    st.success(f"✅ Shapefile loaded! Center: {center['lat']:.4f}, {center['lon']:.4f}")
                    selected_city = "Custom AOI"
    
    st.markdown("---")
    st.markdown("## 📅 Time Period")
    
    current_year = datetime.now().year
    
    analysis_period = st.radio(
        "Period",
        ["Full Year", "Seasonal", "Monthly", "Custom"],
        key="lst_period",
        horizontal=True
    )
    
    year = st.selectbox(
        "Year",
        list(range(current_year, 1999, -1)),
        key="lst_year"
    )
    
    if analysis_period == "Custom":
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input(
                "Start",
                value=date(year, 1, 1),
                min_value=date(2000, 1, 1),
                key="lst_start_date"
            )
        with col2:
            end_date = st.date_input(
                "End",
                value=date(year, 12, 31),
                min_value=start_date,
                key="lst_end_date"
            )
    elif analysis_period == "Seasonal":
        season = st.selectbox(
            "Season",
            ["Winter (Jan-Feb)", "Pre-Monsoon (Mar-May)", "Monsoon (Jun-Sep)", "Post-Monsoon (Oct-Dec)"],
            key="lst_season"
        )
        season_dates = {
            "Winter (Jan-Feb)": (f"{year}-01-01", f"{year}-02-28"),
            "Pre-Monsoon (Mar-May)": (f"{year}-03-01", f"{year}-05-31"),
            "Monsoon (Jun-Sep)": (f"{year}-06-01", f"{year}-09-30"),
            "Post-Monsoon (Oct-Dec)": (f"{year}-10-01", f"{year}-12-31")
        }
        start_date, end_date = season_dates[season]
        start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
    elif analysis_period == "Monthly":
        month = st.selectbox(
            "Month",
            ["January", "February", "March", "April", "May", "June",
             "July", "August", "September", "October", "November", "December"],
            key="lst_month"
        )
        month_num = ["January", "February", "March", "April", "May", "June",
                     "July", "August", "September", "October", "November", "December"].index(month) + 1
        start_date = date(year, month_num, 1)
        if month_num == 12:
            end_date = date(year, 12, 31)
        else:
            end_date = date(year, month_num + 1, 1) - timedelta(days=1)
    else:
        start_date = date(year, 1, 1)
        end_date = date(year, 12, 31)
    
    st.markdown("---")
    st.markdown("## ⚙️ Analysis Options")
    
    time_of_day = st.radio(
        "LST Time",
        ["Day", "Night"],
        key="lst_time_of_day",
        horizontal=True,
        help="Daytime LST shows surface heating, nighttime shows heat retention"
    )
    
    satellite = st.radio(
        "Satellite",
        ["Terra", "Aqua"],
        key="lst_satellite",
        horizontal=True,
        help="Terra (10:30 AM/PM), Aqua (1:30 PM/AM)"
    )
    
    buffer_radius = st.slider(
        "Buffer (km)",
        min_value=5,
        max_value=100,
        value=20,
        step=5,
        key="lst_buffer",
        help="Area around city center for analysis"
    )
    
    st.markdown("---")
    st.markdown("## 🔬 Analysis Type")
    
    analysis_types = st.multiselect(
        "Select Analyses",
        ["LST Map", "UHI Intensity", "Heat Hotspots", "Cooling Zones", "LST Anomaly"],
        default=["LST Map"],
        key="lst_analysis_types"
    )
    
    if "LST Anomaly" in analysis_types:
        st.markdown("##### Anomaly Settings")
        baseline_year = st.selectbox(
            "Baseline Year",
            list(range(2019, 1999, -1)),
            key="lst_baseline_year",
            help="Compare current period to this baseline"
        )
    
    st.markdown("---")
    st.markdown("## 📈 Time Series Options")
    
    show_time_series = st.checkbox("📈 Show Time Series", key="lst_show_ts")
    show_warming_trend = st.checkbox("🔥 Show Warming Trend", key="lst_show_warming")
    
    if show_time_series or show_warming_trend:
        st.markdown("##### Time Series Settings")
        ts_col1, ts_col2 = st.columns(2)
        with ts_col1:
            ts_start_year = st.selectbox(
                "From",
                list(range(2020, 1999, -1)),
                key="lst_ts_start"
            )
        with ts_col2:
            ts_end_year = st.selectbox(
                "To",
                list(range(current_year, ts_start_year - 1, -1)),
                key="lst_ts_end"
            )
        
        ts_aggregation = st.selectbox(
            "Aggregation",
            ["Yearly", "Seasonal", "Monthly"],
            key="lst_ts_agg"
        )
    
    run_analysis = st.button(
        "🔥 Run Analysis",
        type="primary",
        use_container_width=True,
        key="lst_run_analysis"
    )

geometry = None
center_coords = None

if location_mode == "City Selection" and selected_city and selected_city != "Select..." and city_coords:
    geometry = get_city_geometry(city_coords['lat'], city_coords['lon'], buffer_radius)
    center_coords = (city_coords['lat'], city_coords['lon'])
elif location_mode == "Upload Shapefile/GeoJSON" and uploaded_geometry and uploaded_center:
    geometry = uploaded_geometry
    center_coords = (uploaded_center['lat'], uploaded_center['lon'])

if center_coords:
    base_map = create_base_map(center_coords[0], center_coords[1], zoom=11)
    
    if location_mode == "City Selection" and selected_city and selected_city != "Select...":
        add_marker(base_map, center_coords[0], center_coords[1], selected_city)
        add_buffer_circle(base_map, center_coords[0], center_coords[1], buffer_radius)
    elif location_mode == "Upload Shapefile/GeoJSON" and uploaded_geojson:
        add_geojson_boundary(base_map, uploaded_geojson, name="Uploaded AOI", 
                           color="#ff7800", weight=3, fill_opacity=0.15)
        add_marker(base_map, center_coords[0], center_coords[1], 
                   popup="Custom Area Center", tooltip="Custom Area")
else:
    base_map = create_base_map(20.5937, 78.9629, zoom=5)

if run_analysis and geometry:
    st.session_state.lst_tile_urls = {}
    st.session_state.lst_time_series = []
    st.session_state.lst_center_coords = center_coords
    st.session_state.lst_location_name = selected_city if selected_city else "Custom AOI"
    st.session_state.lst_stats = None
    st.session_state.uhi_stats = None
    st.session_state.hotspot_stats = None
    st.session_state.cooling_stats = None
    st.session_state.anomaly_stats = None
    st.session_state.warming_trend = None
    
    try:
        with st.spinner("Analyzing Land Surface Temperature..."):
            start_str = start_date.strftime("%Y-%m-%d")
            end_str = end_date.strftime("%Y-%m-%d")
            
            if "LST Map" in analysis_types:
                with st.spinner("Generating LST map..."):
                    lst_image = get_mean_lst(geometry, start_str, end_str, time_of_day, satellite)
                    if lst_image:
                        lst_stats = get_lst_statistics(lst_image, geometry)
                        st.session_state.lst_stats = lst_stats
                        tile_url = get_lst_tile_url(lst_image, LST_VIS_PARAMS)
                        if tile_url:
                            st.session_state.lst_tile_urls['LST'] = {
                                "url": tile_url,
                                "name": "Land Surface Temperature"
                            }
            
            if "UHI Intensity" in analysis_types:
                with st.spinner("Calculating Urban Heat Island intensity..."):
                    uhi_image, uhi_stats = calculate_uhi_intensity(
                        geometry, start_str, end_str, buffer_radius, time_of_day, satellite
                    )
                    if uhi_image:
                        st.session_state.uhi_stats = uhi_stats
                        tile_url = get_lst_tile_url(uhi_image, UHI_VIS_PARAMS)
                        if tile_url:
                            st.session_state.lst_tile_urls['UHI'] = {
                                "url": tile_url,
                                "name": "UHI Intensity"
                            }
            
            if "Heat Hotspots" in analysis_types:
                with st.spinner("Detecting heat hotspots..."):
                    lst_image = get_mean_lst(geometry, start_str, end_str, time_of_day, satellite)
                    if lst_image:
                        hotspots, hotspot_stats = detect_heat_hotspots(lst_image, geometry)
                        if hotspots:
                            st.session_state.hotspot_stats = hotspot_stats
                            tile_url = get_lst_tile_url(hotspots, HOTSPOT_VIS_PARAMS)
                            if tile_url:
                                st.session_state.lst_tile_urls['Hotspots'] = {
                                    "url": tile_url,
                                    "name": "Heat Hotspots"
                                }
            
            if "Cooling Zones" in analysis_types:
                with st.spinner("Identifying cooling zones..."):
                    cooling, cooling_stats = identify_cooling_zones(
                        geometry, start_str, end_str, None, time_of_day, satellite
                    )
                    if cooling:
                        st.session_state.cooling_stats = cooling_stats
                        tile_url = get_lst_tile_url(cooling, COOLING_VIS_PARAMS)
                        if tile_url:
                            st.session_state.lst_tile_urls['Cooling'] = {
                                "url": tile_url,
                                "name": "Cooling Zones"
                            }
            
            if "LST Anomaly" in analysis_types:
                with st.spinner("Calculating LST anomaly..."):
                    baseline_start = f"{baseline_year}-{start_date.month:02d}-{start_date.day:02d}"
                    baseline_end = f"{baseline_year}-{end_date.month:02d}-{end_date.day:02d}"
                    
                    anomaly, anomaly_stats, _ = calculate_lst_anomaly(
                        geometry, start_str, end_str, baseline_start, baseline_end, time_of_day, satellite
                    )
                    if anomaly:
                        st.session_state.anomaly_stats = anomaly_stats
                        tile_url = get_lst_tile_url(anomaly, ANOMALY_VIS_PARAMS)
                        if tile_url:
                            st.session_state.lst_tile_urls['Anomaly'] = {
                                "url": tile_url,
                                "name": "LST Anomaly"
                            }
            
            if show_time_series or show_warming_trend:
                with st.spinner("Generating time series data..."):
                    time_series = get_lst_time_series(
                        geometry, ts_start_year, ts_end_year, 
                        time_of_day, satellite, ts_aggregation.lower()
                    )
                    st.session_state.lst_time_series = time_series
                    
                    if show_warming_trend and time_series:
                        trend = calculate_warming_trend(time_series)
                        st.session_state.warming_trend = trend
            
            st.session_state.lst_analysis_complete = True
            st.session_state.heat_pdf = None
            st.success("Analysis complete!")
        
    except Exception as e:
        st.error(f"Error: {str(e)}")

if st.session_state.get("lst_tile_urls"):
    for layer_type, layer_info in st.session_state.lst_tile_urls.items():
        opacity = 0.8 if layer_type == "LST" else 0.7
        add_tile_layer(base_map, layer_info["url"], layer_info["name"], opacity)

add_layer_control(base_map)

display_name = st.session_state.lst_location_name or selected_city or "India"
st.markdown(f"### 🗺️ {display_name} - Land Surface Temperature Map")
st.markdown('<div class="map-container">', unsafe_allow_html=True)
st_folium(base_map, width=None, height=500, use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)

if st.session_state.get("lst_analysis_complete"):
    st.markdown("---")
    st.markdown("## 📊 Analysis Results")
    
    res_col1, res_col2 = st.columns([2, 1])
    
    with res_col1:
        if st.session_state.lst_stats:
            st.markdown("### 🌡️ Land Surface Temperature")
            stats = st.session_state.lst_stats
            band_prefix = f"LST_{time_of_day}"
            
            cols = st.columns(4)
            with cols[0]:
                render_stat_card(
                    format_temp(stats.get(f'{band_prefix}_mean')),
                    "Mean LST",
                    "🌡️",
                    "stat-card-orange"
                )
            with cols[1]:
                render_stat_card(
                    format_temp(stats.get(f'{band_prefix}_min')),
                    "Min LST",
                    "❄️",
                    "stat-card-blue"
                )
            with cols[2]:
                render_stat_card(
                    format_temp(stats.get(f'{band_prefix}_max')),
                    "Max LST",
                    "🔥",
                    "stat-card-orange"
                )
            with cols[3]:
                render_stat_card(
                    format_temp(stats.get(f'{band_prefix}_stdDev')),
                    "Std Dev",
                    "📊"
                )
        
        if st.session_state.uhi_stats:
            st.markdown("### 🏙️ Urban Heat Island")
            uhi = st.session_state.uhi_stats
            
            cols = st.columns(3)
            with cols[0]:
                uhi_intensity = uhi.get('uhi_intensity')
                color = "stat-card-orange" if uhi_intensity and uhi_intensity > 0 else "stat-card-blue"
                render_stat_card(
                    format_temp(uhi_intensity),
                    "UHI Intensity",
                    "🔥" if uhi_intensity and uhi_intensity > 0 else "❄️",
                    color
                )
            with cols[1]:
                urban_stats = uhi.get('urban_stats', {})
                render_stat_card(
                    format_temp(urban_stats.get(f'LST_{time_of_day}_mean')),
                    "Urban Mean",
                    "🏙️"
                )
            with cols[2]:
                rural_stats = uhi.get('rural_stats', {})
                render_stat_card(
                    format_temp(rural_stats.get(f'LST_{time_of_day}_mean')),
                    "Rural Mean",
                    "🌳"
                )
        
        if st.session_state.hotspot_stats:
            st.markdown("### 🔥 Heat Hotspots")
            hs = st.session_state.hotspot_stats
            
            cols = st.columns(3)
            with cols[0]:
                render_stat_card(
                    format_temp(hs.get('threshold_temp')),
                    "Threshold (P90)",
                    "🌡️"
                )
            with cols[1]:
                render_stat_card(
                    f"{hs.get('hotspot_area_km2', 0):.1f} km²",
                    "Hotspot Area",
                    "📐",
                    "stat-card-orange"
                )
            with cols[2]:
                render_stat_card(
                    f"{hs.get('hotspot_percentage', 0):.1f}%",
                    "% of AOI",
                    "📊"
                )
        
        if st.session_state.cooling_stats:
            st.markdown("### 🌳 Cooling Zones")
            cz = st.session_state.cooling_stats
            
            cols = st.columns(3)
            with cols[0]:
                render_stat_card(
                    format_temp(cz.get('threshold_temp')),
                    "Threshold (P25)",
                    "🌡️"
                )
            with cols[1]:
                render_stat_card(
                    f"{cz.get('cooling_area_km2', 0):.1f} km²",
                    "Cooling Area",
                    "🌲",
                    "stat-card-blue"
                )
            with cols[2]:
                render_stat_card(
                    f"{cz.get('cooling_percentage', 0):.1f}%",
                    "% of AOI",
                    "📊"
                )
        
        if st.session_state.anomaly_stats:
            st.markdown("### 📈 LST Anomaly")
            anom = st.session_state.anomaly_stats
            anomaly_val = anom.get('anomaly', {}).get('LST_Anomaly_mean')
            
            cols = st.columns(3)
            with cols[0]:
                color = "stat-card-orange" if anomaly_val and anomaly_val > 0 else "stat-card-blue"
                sign = "+" if anomaly_val and anomaly_val > 0 else ""
                render_stat_card(
                    f"{sign}{format_temp(anomaly_val)}",
                    "Mean Anomaly",
                    "📈" if anomaly_val and anomaly_val > 0 else "📉",
                    color
                )
            with cols[1]:
                render_stat_card(
                    format_temp(anom.get('target', {}).get(f'LST_{time_of_day}_mean')),
                    f"Current ({year})",
                    "🌡️"
                )
            with cols[2]:
                render_stat_card(
                    format_temp(anom.get('baseline', {}).get(f'LST_{time_of_day}_mean')),
                    f"Baseline ({baseline_year})",
                    "📅"
                )
    
    with res_col2:
        st.markdown("### 🎨 Map Legends")
        
        if 'LST' in st.session_state.lst_tile_urls:
            st.markdown("**Land Surface Temperature**")
            st.markdown("""
            <div style="display: flex; align-items: center; gap: 10px;">
                <div style="width: 150px; height: 20px; background: linear-gradient(to right, blue, cyan, green, yellow, orange, red, darkred); border-radius: 4px;"></div>
            </div>
            <div style="display: flex; justify-content: space-between; width: 150px; font-size: 0.8rem;">
                <span>20°C</span><span>45°C</span>
            </div>
            """, unsafe_allow_html=True)
        
        if 'UHI' in st.session_state.lst_tile_urls:
            st.markdown("**UHI Intensity**")
            st.markdown("""
            <div style="display: flex; align-items: center; gap: 10px;">
                <div style="width: 150px; height: 20px; background: linear-gradient(to right, #313695, #74add1, #ffffbf, #f46d43, #a50026); border-radius: 4px;"></div>
            </div>
            <div style="display: flex; justify-content: space-between; width: 150px; font-size: 0.8rem;">
                <span>-5°C</span><span>+10°C</span>
            </div>
            """, unsafe_allow_html=True)
        
        if 'Hotspots' in st.session_state.lst_tile_urls:
            st.markdown("**Heat Hotspots**")
            st.markdown("""
            <div style="display: flex; align-items: center; gap: 5px;">
                <div style="width: 20px; height: 20px; background: #FF4500; border-radius: 4px;"></div>
                <span style="font-size: 0.8rem;">Above 90th percentile</span>
            </div>
            """, unsafe_allow_html=True)
        
        if 'Cooling' in st.session_state.lst_tile_urls:
            st.markdown("**Cooling Zones**")
            st.markdown("""
            <div style="display: flex; align-items: center; gap: 5px;">
                <div style="width: 20px; height: 20px; background: #228B22; border-radius: 4px;"></div>
                <span style="font-size: 0.8rem;">Below 25th percentile</span>
            </div>
            """, unsafe_allow_html=True)
        
        if 'Anomaly' in st.session_state.lst_tile_urls:
            st.markdown("**LST Anomaly**")
            st.markdown("""
            <div style="display: flex; align-items: center; gap: 10px;">
                <div style="width: 150px; height: 20px; background: linear-gradient(to right, #2166ac, #92c5de, #f7f7f7, #f4a582, #b2182b); border-radius: 4px;"></div>
            </div>
            <div style="display: flex; justify-content: space-between; width: 150px; font-size: 0.8rem;">
                <span>-5°C</span><span>+5°C</span>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("### 📥 Export Options")
        
        exp_cols = st.columns(2)
        
        with exp_cols[0]:
            if st.session_state.lst_stats:
                stats = st.session_state.lst_stats
                csv_data = f"Metric,Value\n"
                for key, val in stats.items():
                    csv_data += f"{key},{val}\n"
                
                st.download_button(
                    "📄 Download CSV",
                    data=csv_data,
                    file_name=f"lst_stats_{display_name}.csv",
                    mime="text/csv",
                    use_container_width=True,
                    key="dl_lst_stats"
                )
        
        with exp_cols[1]:
            if st.session_state.lst_stats:
                if 'heat_pdf' not in st.session_state or st.session_state.heat_pdf is None:
                    vulnerability = calculate_heat_vulnerability_score(
                        st.session_state.lst_stats,
                        st.session_state.uhi_stats,
                        st.session_state.lst_time_series,
                        st.session_state.warming_trend
                    )
                    report_data = {
                        'city_name': display_name,
                        'state': selected_state if selected_state != "Custom AOI" else "",
                        'date_range': f"{start_date} to {end_date}",
                        'time_of_day': time_of_day,
                        'data_source': f"MODIS {satellite}",
                        'lst_stats': st.session_state.lst_stats,
                        'uhi_stats': st.session_state.uhi_stats,
                        'vulnerability_score': vulnerability,
                        'time_series': st.session_state.lst_time_series,
                        'warming_trend': st.session_state.warming_trend
                    }
                    st.session_state.heat_pdf = generate_urban_heat_pdf_report(report_data)
                
                if st.session_state.get("heat_pdf"):
                    st.download_button(
                        "📥 Download PDF Report",
                        data=st.session_state.heat_pdf,
                        file_name=f"urban_heat_report_{display_name}.pdf",
                        mime="application/pdf",
                        use_container_width=True,
                        key="dl_heat_pdf"
                    )
                else:
                    st.error("Failed to generate PDF")
    
    if st.session_state.lst_time_series:
        st.markdown("---")
        st.markdown("### 📈 Temperature Time Series")
        
        ts_data = st.session_state.lst_time_series
        
        chart_data = [{'date': d['date'], 'value': d['mean_lst']} for d in ts_data if d.get('mean_lst')]
        
        ts_cols = st.columns([3, 1])
        
        with ts_cols[0]:
            render_line_chart(
                chart_data,
                title=f"Land Surface Temperature ({time_of_day}time)",
                y_label="Temperature (°C)",
                show_rolling=False
            )
        
        with ts_cols[1]:
            if ts_data:
                temps = [d['mean_lst'] for d in ts_data if d.get('mean_lst')]
                if temps:
                    st.markdown("#### Summary")
                    st.metric("Average", f"{np.mean(temps):.1f}°C")
                    st.metric("Maximum", f"{np.max(temps):.1f}°C")
                    st.metric("Minimum", f"{np.min(temps):.1f}°C")
                    st.metric("Range", f"{np.max(temps) - np.min(temps):.1f}°C")
        
        if ts_data:
            csv_data = generate_time_series_csv(ts_data, 'LST', display_name)
            if csv_data:
                st.download_button(
                    "📥 Download Time Series CSV",
                    data=csv_data,
                    file_name=f"lst_timeseries_{display_name}.csv",
                    mime="text/csv",
                    key="dl_ts_csv"
                )
    
    if st.session_state.warming_trend:
        st.markdown("---")
        st.markdown("### 🔥 Warming Trend Analysis")
        
        trend = st.session_state.warming_trend
        
        trend_cols = st.columns(4)
        with trend_cols[0]:
            slope = trend.get('slope_per_year', 0)
            color = "stat-card-orange" if slope > 0 else "stat-card-blue"
            sign = "+" if slope > 0 else ""
            render_stat_card(
                f"{sign}{slope:.3f}°C/year",
                "Warming Rate",
                "📈" if slope > 0 else "📉",
                color
            )
        with trend_cols[1]:
            total_change = trend.get('total_change', 0)
            sign = "+" if total_change > 0 else ""
            render_stat_card(
                f"{sign}{total_change:.2f}°C",
                "Total Change",
                "🌡️"
            )
        with trend_cols[2]:
            render_stat_card(
                f"{trend.get('r_squared', 0):.3f}",
                "R² Score",
                "📊"
            )
        with trend_cols[3]:
            significance = "Significant" if trend.get('p_value', 1) < 0.05 else "Not Significant"
            render_stat_card(
                significance,
                "Statistical Significance",
                "✓" if trend.get('p_value', 1) < 0.05 else "✗"
            )
        
        if trend.get('slope_per_year', 0) > 0:
            st.warning(f"⚠️ This area shows a warming trend of approximately {trend.get('slope_per_year', 0):.3f}°C per year.")
        else:
            st.info(f"ℹ️ This area shows a cooling trend of approximately {abs(trend.get('slope_per_year', 0)):.3f}°C per year.")

if not center_coords:
    render_info_box("Select a city or upload a shapefile to view the map and run analysis.", "info")
elif not st.session_state.get("lst_analysis_complete"):
    render_info_box("Click 'Run Analysis' to generate temperature maps and statistics.", "info")
