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
    create_base_map, add_tile_layer, add_marker, add_buffer_circle, add_layer_control
)
from components.charts import render_line_chart
from services.exports import generate_time_series_csv

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
                    result = geojson_file_to_ee_geometry(geojson_file)
                    if result:
                        uploaded_geometry, uploaded_center = result
                        st.success(f"GeoJSON loaded successfully")
                        selected_city = "Custom AOI"
                    else:
                        st.error("Failed to parse GeoJSON file")
            elif is_zip or has_shp:
                result = process_shapefile_upload(uploaded_files)
                if result:
                    uploaded_geometry, uploaded_center = result
                    st.success(f"Shapefile loaded successfully")
                    selected_city = "Custom AOI"
                else:
                    st.error("Failed to process shapefile")
    
    st.markdown("---")
    st.markdown("## 📅 Date Range")
    
    current_year = datetime.now().year
    year = st.selectbox(
        "Year",
        list(range(current_year, 1999, -1)),
        key="lst_year"
    )
    
    analysis_period = st.radio(
        "Period",
        ["Full Year", "Seasonal", "Monthly", "Custom Range"],
        key="lst_period",
        horizontal=True
    )
    
    if analysis_period == "Custom Range":
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input(
                "Start",
                value=date(year, 1, 1),
                min_value=date(2000, 1, 1),
                max_value=date.today(),
                key="lst_start_date"
            )
        with col2:
            end_date = st.date_input(
                "End",
                value=date(year, 12, 31),
                min_value=date(2000, 1, 1),
                max_value=date.today(),
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
        ["LST Map", "UHI Intensity", "Heat Hotspots", "Cooling Zones", 
         "LST Anomaly", "Time Series", "Warming Trend"],
        default=["LST Map", "UHI Intensity", "Heat Hotspots"],
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
    
    if "Time Series" in analysis_types or "Warming Trend" in analysis_types:
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
elif location_mode == "Upload Shapefile/GeoJSON" and uploaded_geometry:
    geometry = uploaded_geometry
    center_coords = uploaded_center

if run_analysis and geometry:
    st.session_state.lst_tile_urls = {}
    st.session_state.lst_time_series = []
    st.session_state.lst_center_coords = center_coords
    st.session_state.lst_location_name = selected_city if selected_city else "Custom AOI"
    
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
                        st.session_state.lst_tile_urls['LST'] = tile_url
        
        if "UHI Intensity" in analysis_types:
            with st.spinner("Calculating Urban Heat Island intensity..."):
                uhi_image, uhi_stats = calculate_uhi_intensity(
                    geometry, start_str, end_str, buffer_radius, time_of_day, satellite
                )
                if uhi_image:
                    st.session_state.uhi_stats = uhi_stats
                    tile_url = get_lst_tile_url(uhi_image, UHI_VIS_PARAMS)
                    if tile_url:
                        st.session_state.lst_tile_urls['UHI'] = tile_url
        
        if "Heat Hotspots" in analysis_types:
            with st.spinner("Detecting heat hotspots..."):
                lst_image = get_mean_lst(geometry, start_str, end_str, time_of_day, satellite)
                if lst_image:
                    hotspots, hotspot_stats = detect_heat_hotspots(lst_image, geometry)
                    if hotspots:
                        st.session_state.hotspot_stats = hotspot_stats
                        tile_url = get_lst_tile_url(hotspots, HOTSPOT_VIS_PARAMS)
                        if tile_url:
                            st.session_state.lst_tile_urls['Hotspots'] = tile_url
        
        if "Cooling Zones" in analysis_types:
            with st.spinner("Identifying cooling zones..."):
                cooling, cooling_stats = identify_cooling_zones(
                    geometry, start_str, end_str, None, time_of_day, satellite
                )
                if cooling:
                    st.session_state.cooling_stats = cooling_stats
                    tile_url = get_lst_tile_url(cooling, COOLING_VIS_PARAMS)
                    if tile_url:
                        st.session_state.lst_tile_urls['Cooling'] = tile_url
        
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
                        st.session_state.lst_tile_urls['Anomaly'] = tile_url
        
        if "Time Series" in analysis_types or "Warming Trend" in analysis_types:
            with st.spinner("Generating time series data..."):
                time_series = get_lst_time_series(
                    geometry, ts_start_year, ts_end_year, 
                    time_of_day, satellite, ts_aggregation.lower()
                )
                st.session_state.lst_time_series = time_series
                
                if "Warming Trend" in analysis_types and time_series:
                    trend = calculate_warming_trend(time_series)
                    st.session_state.warming_trend = trend
        
        st.session_state.lst_analysis_complete = True
        st.success("Analysis complete!")

if st.session_state.lst_tile_urls or st.session_state.lst_analysis_complete:
    display_coords = st.session_state.lst_center_coords or center_coords
    display_name = st.session_state.lst_location_name or selected_city
    
    tab1, tab2, tab3, tab4 = st.tabs(["🗺️ Maps", "📊 Statistics", "📈 Time Series", "📥 Export"])
    
    with tab1:
        if display_coords:
            m = create_base_map(display_coords[0], display_coords[1], zoom=11)
            
            if 'LST' in st.session_state.lst_tile_urls:
                add_tile_layer(m, st.session_state.lst_tile_urls['LST'], "Land Surface Temperature")
            
            if 'UHI' in st.session_state.lst_tile_urls:
                add_tile_layer(m, st.session_state.lst_tile_urls['UHI'], "UHI Intensity")
            
            if 'Hotspots' in st.session_state.lst_tile_urls:
                add_tile_layer(m, st.session_state.lst_tile_urls['Hotspots'], "Heat Hotspots")
            
            if 'Cooling' in st.session_state.lst_tile_urls:
                add_tile_layer(m, st.session_state.lst_tile_urls['Cooling'], "Cooling Zones")
            
            if 'Anomaly' in st.session_state.lst_tile_urls:
                add_tile_layer(m, st.session_state.lst_tile_urls['Anomaly'], "LST Anomaly")
            
            if display_name and display_name != "Select..." and display_name != "Custom AOI":
                add_marker(m, display_coords[0], display_coords[1], display_name)
                add_buffer_circle(m, display_coords[0], display_coords[1], buffer_radius)
            
            add_layer_control(m)
            
            st_folium(m, width=None, height=600, use_container_width=True)
            
            st.markdown("### 🎨 Map Legends")
            
            legend_cols = st.columns(3)
            
            with legend_cols[0]:
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
            
            with legend_cols[1]:
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
            
            with legend_cols[2]:
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
        else:
            render_info_box("No location data available. Please run the analysis first.", "warning")
    
    with tab2:
        st.markdown("### 📊 Analysis Statistics")
        
        if hasattr(st.session_state, 'lst_stats') and st.session_state.lst_stats:
            st.markdown("#### 🌡️ Land Surface Temperature")
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
            
            st.markdown("##### Percentiles")
            p_cols = st.columns(5)
            percentiles = [10, 25, 50, 75, 90]
            for i, p in enumerate(percentiles):
                with p_cols[i]:
                    val = stats.get(f'{band_prefix}_p{p}')
                    st.metric(f"P{p}", format_temp(val))
        
        if hasattr(st.session_state, 'uhi_stats') and st.session_state.uhi_stats:
            st.markdown("---")
            st.markdown("#### 🏙️ Urban Heat Island Analysis")
            uhi = st.session_state.uhi_stats
            
            cols = st.columns(3)
            band_prefix = f"LST_{time_of_day}"
            
            with cols[0]:
                urban_mean = uhi['urban_stats'].get(f'{band_prefix}_mean') if uhi['urban_stats'] else None
                render_stat_card(
                    format_temp(urban_mean),
                    "Urban Mean LST",
                    "🏙️",
                    "stat-card-orange"
                )
            with cols[1]:
                rural_mean = uhi['rural_stats'].get(f'{band_prefix}_mean') if uhi['rural_stats'] else None
                render_stat_card(
                    format_temp(rural_mean),
                    "Rural Mean LST",
                    "🌳",
                    "stat-card-green"
                )
            with cols[2]:
                uhi_intensity = uhi.get('uhi_intensity')
                color = "stat-card-orange" if uhi_intensity and uhi_intensity > 0 else "stat-card-blue"
                render_stat_card(
                    f"+{format_temp(uhi_intensity)}" if uhi_intensity and uhi_intensity > 0 else format_temp(uhi_intensity),
                    "UHI Intensity",
                    "🌡️",
                    color
                )
            
            if uhi_intensity:
                if uhi_intensity > 3:
                    render_info_box("⚠️ High UHI intensity detected! Urban areas are significantly warmer than surrounding rural areas.", "warning")
                elif uhi_intensity > 1:
                    render_info_box("Moderate UHI effect observed. Urban development is contributing to local warming.", "info")
                else:
                    render_info_box("Low UHI intensity. Good urban-rural temperature balance.", "success")
        
        if hasattr(st.session_state, 'hotspot_stats') and st.session_state.hotspot_stats:
            st.markdown("---")
            st.markdown("#### 🔥 Heat Hotspots")
            hs = st.session_state.hotspot_stats
            
            cols = st.columns(4)
            with cols[0]:
                st.metric("Threshold", format_temp(hs.get('threshold_temp')))
            with cols[1]:
                st.metric("Hotspot Area", f"{hs.get('hotspot_area_km2', 0):.1f} km²")
            with cols[2]:
                st.metric("Total Area", f"{hs.get('total_area_km2', 0):.1f} km²")
            with cols[3]:
                st.metric("Hotspot %", f"{hs.get('hotspot_percentage', 0):.1f}%")
        
        if hasattr(st.session_state, 'cooling_stats') and st.session_state.cooling_stats:
            st.markdown("---")
            st.markdown("#### 🌳 Cooling Zones")
            cs = st.session_state.cooling_stats
            
            cols = st.columns(4)
            with cols[0]:
                st.metric("Threshold", format_temp(cs.get('threshold_temp')))
            with cols[1]:
                st.metric("Cooling Area", f"{cs.get('cooling_area_km2', 0):.1f} km²")
            with cols[2]:
                st.metric("Total Area", f"{cs.get('total_area_km2', 0):.1f} km²")
            with cols[3]:
                st.metric("Cooling %", f"{cs.get('cooling_percentage', 0):.1f}%")
            
            render_info_box("Cooling zones typically correspond to parks, water bodies, and dense vegetation that help reduce urban temperatures.", "info")
        
        if hasattr(st.session_state, 'anomaly_stats') and st.session_state.anomaly_stats:
            st.markdown("---")
            st.markdown("#### 📉 LST Anomaly")
            anom = st.session_state.anomaly_stats
            
            cols = st.columns(3)
            with cols[0]:
                target_mean = anom['target'].get(f'LST_{time_of_day}_mean') if anom.get('target') else None
                st.metric("Current Period", format_temp(target_mean))
            with cols[1]:
                baseline_mean = anom['baseline'].get(f'LST_{time_of_day}_mean') if anom.get('baseline') else None
                st.metric("Baseline Period", format_temp(baseline_mean))
            with cols[2]:
                anomaly_mean = anom['anomaly'].get('LST_Anomaly_mean') if anom.get('anomaly') else None
                delta_color = "inverse" if anomaly_mean and anomaly_mean < 0 else "normal"
                st.metric(
                    "Anomaly",
                    format_temp(anomaly_mean),
                    delta=f"{anomaly_mean:+.1f}°C" if anomaly_mean else None,
                    delta_color=delta_color
                )
    
    with tab3:
        st.markdown("### 📈 Temperature Trends")
        
        if st.session_state.lst_time_series:
            ts_data = st.session_state.lst_time_series
            df = pd.DataFrame(ts_data)
            
            st.markdown("#### Temperature Time Series")
            
            if 'mean_lst' in df.columns:
                fig_data = {
                    'dates': df['date'].tolist(),
                    'values': df['mean_lst'].tolist(),
                    'label': f'Mean {time_of_day} LST (°C)'
                }
                render_line_chart(
                    fig_data['dates'],
                    fig_data['values'],
                    f"Mean {time_of_day}time LST",
                    "Date",
                    "Temperature (°C)",
                    color='#e74c3c'
                )
            
            if hasattr(st.session_state, 'warming_trend') and st.session_state.warming_trend:
                st.markdown("---")
                st.markdown("#### 🔥 Warming Trend Analysis")
                trend = st.session_state.warming_trend
                
                cols = st.columns(4)
                with cols[0]:
                    rate = trend.get('warming_rate_per_decade')
                    color = "stat-card-orange" if rate and rate > 0 else "stat-card-blue"
                    render_stat_card(
                        f"{rate:+.2f}°C" if rate else "N/A",
                        "Warming Rate/Decade",
                        "📈",
                        color
                    )
                with cols[1]:
                    total = trend.get('total_warming')
                    render_stat_card(
                        f"{total:+.2f}°C" if total else "N/A",
                        "Total Change",
                        "🌡️"
                    )
                with cols[2]:
                    r2 = trend.get('r_squared')
                    render_stat_card(
                        f"{r2:.3f}" if r2 else "N/A",
                        "R² (Fit)",
                        "📊"
                    )
                with cols[3]:
                    years = f"{trend.get('start_year')}-{trend.get('end_year')}"
                    render_stat_card(
                        years,
                        "Period",
                        "📅"
                    )
                
                if rate:
                    if rate > 0.3:
                        render_info_box(f"⚠️ Significant warming trend detected: {rate:.2f}°C per decade. This indicates accelerated urban heating.", "warning")
                    elif rate > 0:
                        render_info_box(f"Moderate warming trend: {rate:.2f}°C per decade.", "info")
                    else:
                        render_info_box(f"Cooling trend detected: {rate:.2f}°C per decade.", "success")
            
            st.markdown("---")
            st.markdown("#### 📋 Time Series Data")
            st.dataframe(df, use_container_width=True)
        else:
            render_info_box("Run analysis with 'Time Series' or 'Warming Trend' selected to view temporal data.", "info")
    
    with tab4:
        st.markdown("### 📥 Export Data")
        
        export_cols = st.columns(2)
        
        with export_cols[0]:
            if hasattr(st.session_state, 'lst_stats') and st.session_state.lst_stats:
                stats_df = pd.DataFrame([st.session_state.lst_stats])
                csv = stats_df.to_csv(index=False)
                st.download_button(
                    "📊 Download LST Statistics (CSV)",
                    csv,
                    f"lst_statistics_{start_date}_{end_date}.csv",
                    "text/csv",
                    use_container_width=True
                )
        
        with export_cols[1]:
            if st.session_state.lst_time_series:
                ts_df = pd.DataFrame(st.session_state.lst_time_series)
                csv = ts_df.to_csv(index=False)
                st.download_button(
                    "📈 Download Time Series (CSV)",
                    csv,
                    f"lst_time_series.csv",
                    "text/csv",
                    use_container_width=True
                )
        
        if hasattr(st.session_state, 'uhi_stats') and st.session_state.uhi_stats:
            st.markdown("---")
            uhi = st.session_state.uhi_stats
            uhi_data = {
                'metric': ['Urban Mean LST', 'Rural Mean LST', 'UHI Intensity'],
                'value': [
                    uhi['urban_stats'].get(f'LST_{time_of_day}_mean') if uhi['urban_stats'] else None,
                    uhi['rural_stats'].get(f'LST_{time_of_day}_mean') if uhi['rural_stats'] else None,
                    uhi.get('uhi_intensity')
                ]
            }
            uhi_df = pd.DataFrame(uhi_data)
            csv = uhi_df.to_csv(index=False)
            st.download_button(
                "🏙️ Download UHI Analysis (CSV)",
                csv,
                f"uhi_analysis_{start_date}_{end_date}.csv",
                "text/csv",
                use_container_width=True
            )

else:
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="card">
            <div class="card-header">🌡️ Land Surface Temperature</div>
            <p>Analyze surface temperature patterns using MODIS satellite data:</p>
            <ul>
                <li><b>Resolution:</b> 1km (MODIS Terra/Aqua)</li>
                <li><b>Coverage:</b> 2000 - Present</li>
                <li><b>Day/Night:</b> Separate analyses for daytime and nighttime LST</li>
                <li><b>Seasonal:</b> Pre-monsoon, monsoon, post-monsoon patterns</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="card">
            <div class="card-header">🏙️ Urban Heat Island</div>
            <p>Quantify urban-rural temperature differences:</p>
            <ul>
                <li><b>UHI Intensity:</b> Temperature difference between urban and rural areas</li>
                <li><b>Heat Hotspots:</b> Areas exceeding 90th percentile temperature</li>
                <li><b>Cooling Zones:</b> Parks and water bodies that reduce temperatures</li>
                <li><b>Trends:</b> Long-term warming analysis</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    render_info_box("👈 Select a location and configure analysis options in the sidebar, then click 'Run Analysis' to begin.", "info")

st.markdown("---")
st.markdown(
    """
    <div style="text-align: center; color: #666; padding: 1rem;">
        Made with ❤️ by <strong>Hemant Kumar</strong> • 
        <a href="https://www.linkedin.com/in/hemantkumar2430" target="_blank">LinkedIn</a>
        <br>
        Powered by Streamlit & Google Earth Engine | Data: MODIS LST
    </div>
    """,
    unsafe_allow_html=True,
)
