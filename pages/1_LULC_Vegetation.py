import streamlit as st
import folium
from streamlit_folium import st_folium
from folium.plugins import Draw
from datetime import datetime, date
import pandas as pd
import io

from india_cities import get_states, get_cities, get_city_coordinates
from services.gee_core import (
    auto_initialize_gee, get_city_geometry, get_tile_url, 
    geojson_to_ee_geometry, get_safe_download_url, sample_pixel_value, get_image_mean,
    process_shapefile_upload, geojson_file_to_ee_geometry
)
from services.gee_lulc import (
    get_sentinel2_image, get_landsat_image, get_dynamic_world_lulc,
    get_sentinel_rgb_params, get_landsat_rgb_params, get_lulc_vis_params,
    calculate_lulc_statistics_with_area, get_lulc_change_analysis,
    calculate_change_summary, LULC_CLASSES
)
from services.timelapse import get_ndvi_timelapse
from services.gee_indices import (
    get_index_functions, get_index_vis_params, INDEX_INFO
)
from components.ui import (
    apply_enhanced_css, render_page_header, render_stat_card,
    render_info_box, init_common_session_state
)
from components.maps import (
    create_base_map, add_tile_layer, add_marker, add_buffer_circle, add_layer_control,
    add_geojson_boundary
)
from components.legends import (
    render_lulc_legend, render_index_legend_with_opacity
)
from components.charts import (
    render_pie_chart, render_bar_chart, generate_csv_download, render_download_button
)
from services.exports import (
    generate_lulc_csv, generate_change_analysis_csv, generate_lulc_pdf_report,
    calculate_land_sustainability_score
)
from services.gee_trends import (
    get_historical_lulc_data, get_historical_index_data,
    analyze_lulc_trends, analyze_index_trends,
    generate_forecast_lulc, generate_forecast_indices,
    generate_forecast_lulc, generate_forecast_indices,
    get_trend_summary
)
from services.insights import generate_lulc_insights

st.set_page_config(
    page_title="LULC & Vegetation Analysis",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
)

auto_initialize_gee()
init_common_session_state()
apply_enhanced_css()

render_page_header(
    "🌍 LULC & Vegetation Analysis",
    "Analyze Land Use, Land Cover, and Vegetation Indices for Indian Cities"
)

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
        key="lulc_location_mode",
        horizontal=True
    )
    
    selected_city = None
    city_coords = None
    uploaded_geometry = None
    uploaded_center = None
    uploaded_geojson = None
    
    if location_mode == "City Selection":
        states = get_states()
        selected_state = st.selectbox("State", ["Select..."] + states, key="lulc_state")
        
        if selected_state != "Select...":
            cities = get_cities(selected_state)
            selected_city = st.selectbox("City", ["Select..."] + cities, key="lulc_city")
            
            if selected_city != "Select...":
                city_coords = get_city_coordinates(selected_state, selected_city)
                if city_coords:
                    st.success(f"📍 {selected_city}, {selected_state}")
                    st.caption(f"Lat: {city_coords['lat']:.4f}, Lon: {city_coords['lon']:.4f}")
    else:
        selected_state = "Custom AOI"
        st.markdown("##### Upload Files")
        st.caption("Upload a Shapefile (.shp + .shx + .dbf + .prj) or a single .zip file containing the shapefile, or a GeoJSON file.")
        
        uploaded_files = st.file_uploader(
            "Choose files",
            type=["shp", "shx", "dbf", "prj", "cpg", "zip", "geojson", "json"],
            accept_multiple_files=True,
            key="lulc_shapefile_upload"
        )
        
        if uploaded_files:
            file_names = [f.name for f in uploaded_files]
            
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
                st.warning("Please upload all required shapefile components (.shp, .shx, .dbf, .prj) or a .zip file")
    
    st.markdown("---")
    st.markdown("## 📅 Time Period")
    
    current_year = datetime.now().year
    years = list(range(2017, current_year + 1))
    
    analysis_mode = st.radio(
        "Analysis Mode",
        ["Single Period", "Time Series Comparison", "Timelapse Animation"],
        key="lulc_analysis_mode"
    )
    
    if analysis_mode == "Single Period":
        selected_year = st.selectbox("Year", years[::-1], key="lulc_year")
        
        date_range_option = st.radio("Date Range", ["Full Year", "Custom"], key="lulc_date_range")
        
        if date_range_option == "Full Year":
            start_date = f"{selected_year}-01-01"
            end_date = f"{selected_year}-12-31"
        else:
            col1, col2 = st.columns(2)
            with col1:
                start = st.date_input("Start", value=date(selected_year, 1, 1), key="lulc_start")
            with col2:
                end = st.date_input("End", value=date(selected_year, 12, 31), key="lulc_end")
            start_date = start.strftime("%Y-%m-%d")
            end_date = end.strftime("%Y-%m-%d")
        
        compare_year1, compare_year2 = None, None
    elif analysis_mode == "Timelapse Animation":
        col1, col2 = st.columns(2)
        with col1:
            start_year = st.selectbox("Start Year", years[::-1], index=len(years)-1, key="tl_start_year")
        with col2:
            end_year = st.selectbox("End Year", years[::-1], index=0, key="tl_end_year")
        
        frequency = st.selectbox("Frequency", ["Monthly", "Yearly"], key="tl_freq")
        
        start_date = f"{start_year}-01-01"
        end_date = f"{end_year}-12-31"
        selected_year = end_year # Context for other things
    else:
        col1, col2 = st.columns(2)
        with col1:
            compare_year1 = st.selectbox("Year 1", years[::-1], index=len(years)-1, key="lulc_year1")
        with col2:
            compare_year2 = st.selectbox("Year 2", years[::-1], index=0, key="lulc_year2")
        
        start_date = f"{compare_year2}-01-01"
        end_date = f"{compare_year2}-12-31"
        selected_year = compare_year2
    
    st.markdown("---")
    st.markdown("## 🛰️ Data Source")
    
    satellite = st.radio("Satellite", ["Sentinel-2", "Landsat 8/9"], key="lulc_satellite")
    buffer_km = st.slider("Radius (km)", 5, 50, 15, key="lulc_buffer")
    
    st.markdown("---")
    st.markdown("## 📊 Analysis Options")
    
    show_lulc = st.checkbox("LULC Analysis", value=True, key="lulc_show_lulc")
    show_indices = st.multiselect(
        "Vegetation Indices",
        ["NDVI", "NDWI", "NDBI", "EVI", "SAVI"],
        default=["NDVI"],
        key="lulc_indices"
    )
    show_rgb = st.checkbox("RGB Image", value=True, key="lulc_show_rgb")
    enable_drawing = st.checkbox("Custom AOI", value=False, key="lulc_enable_drawing")
    enable_pixel_inspector = st.checkbox("Pixel Inspector", value=False, key="lulc_pixel_inspector")

if city_coords and st.session_state.gee_initialized:
    use_custom_aoi = False
    use_uploaded_aoi = uploaded_geometry is not None
    
    if enable_drawing and st.session_state.get("drawn_geometry"):
        use_custom_aoi = st.sidebar.checkbox("Use Drawn AOI", value=False, key="lulc_use_custom")
    
    run_analysis = st.sidebar.button("🚀 Run Analysis", use_container_width=True, type="primary")
    
    base_map = create_base_map(city_coords["lat"], city_coords["lon"], enable_drawing=enable_drawing)
    
    if not use_uploaded_aoi:
        add_marker(base_map, city_coords["lat"], city_coords["lon"], 
                   popup=f"{selected_city}, {selected_state}", tooltip=selected_city)
        add_buffer_circle(base_map, city_coords["lat"], city_coords["lon"], buffer_km)
    else:
        if uploaded_geojson:
            add_geojson_boundary(base_map, uploaded_geojson, name="Uploaded AOI", 
                               color="#ff7800", weight=3, fill_opacity=0.15)
        add_marker(base_map, city_coords["lat"], city_coords["lon"], 
                   popup="Custom Area Center", tooltip="Custom Area")
    
    if run_analysis:
        with st.spinner("Fetching satellite data and running analysis..."):
            try:
                if use_uploaded_aoi and uploaded_geometry:
                    geometry = uploaded_geometry
                    st.info("Using uploaded shapefile/GeoJSON geometry")
                elif use_custom_aoi and st.session_state.get("drawn_geometry"):
                    first_drawing = st.session_state.drawn_geometry[0]
                    geometry = geojson_to_ee_geometry(first_drawing)
                    if geometry is None:
                        st.warning("Could not parse custom AOI. Using city buffer.")
                        geometry = get_city_geometry(city_coords["lat"], city_coords["lon"], buffer_km)
                else:
                    geometry = get_city_geometry(city_coords["lat"], city_coords["lon"], buffer_km)
                
                st.session_state.current_geometry = geometry
                
                if satellite == "Sentinel-2":
                    image = get_sentinel2_image(geometry, start_date, end_date)
                    rgb_params_func = get_sentinel_rgb_params
                else:
                    image = get_landsat_image(geometry, start_date, end_date)
                    rgb_params_func = get_landsat_rgb_params
                
                if image is None:
                    st.error(f"No cloud-free {satellite} images found. Try a different date range.")
                else:
                    st.session_state.current_image = image
                    
                    if show_rgb and image is not None:
                        try:
                            rgb_params = rgb_params_func(image)
                            rgb_url = get_tile_url(image, rgb_params)
                            add_tile_layer(base_map, rgb_url, f"{satellite} RGB", 0.9)
                        except Exception as e:
                            st.warning(f"Could not load RGB layer: {str(e)}")
                    
                    if show_lulc:
                        lulc = get_dynamic_world_lulc(geometry, start_date, end_date)
                        if lulc:
                            lulc_params = get_lulc_vis_params()
                            lulc_url = get_tile_url(lulc, lulc_params)
                            add_tile_layer(base_map, lulc_url, "LULC", 0.8)
                            st.session_state.lulc_stats = calculate_lulc_statistics_with_area(lulc, geometry)
                            
                            if analysis_mode == "Time Series Comparison" and compare_year1 and compare_year2:
                                stats1, stats2, _ = get_lulc_change_analysis(geometry, compare_year1, compare_year2)
                                st.session_state.time_series_stats = (stats1, stats2, compare_year1, compare_year2)
                    
                    index_funcs = get_index_functions(satellite)
                    st.session_state.index_images = {}
                    st.session_state.index_means = {}
                    
                    for idx in show_indices:
                        if idx in index_funcs:
                            try:
                                index_image = index_funcs[idx](image)
                                if index_image is not None:
                                    st.session_state.index_images[idx] = index_image
                                    index_params = get_index_vis_params(idx)
                                    index_url = get_tile_url(index_image, index_params)
                                    add_tile_layer(base_map, index_url, idx, 0.8)
                                    
                                    mean_result = get_image_mean(index_image, geometry)
                                    if mean_result:
                                        st.session_state.index_means[idx] = mean_result.get(idx, None)
                            except Exception as e:
                                st.warning(f"Could not calculate {idx}: {str(e)}")
                    
                    st.session_state.analysis_complete = True
                    st.session_state.lulc_pdf = None
                    st.success("Analysis complete!")
            
            except Exception as e:
                st.error(f"Error: {str(e)}")
            
            if analysis_mode == "Timelapse Animation" and st.session_state.get("current_geometry"):
                geometry = st.session_state.current_geometry
                gif_url, error = None, None
                
                if tl_type == "LULC Map (Land Cover)":
                    with st.spinner("Generating LULC Timelapse..."):
                        from services.timelapse import get_lulc_timelapse
                        gif_url, error = get_lulc_timelapse(
                            geometry, 
                            f"{start_year}-01-01", 
                            f"{end_year}-12-31",
                            frequency=frequency
                        )
                else: # NDVI (Vegetation Index)
                    with st.spinner("Generating NDVI Timelapse..."):
                        from services.timelapse import get_ndvi_timelapse
                        gif_url, error = get_ndvi_timelapse(
                             geometry, 
                             f"{start_year}-01-01", 
                             f"{end_year}-12-31", 
                             frequency=frequency
                        )
                
                if gif_url:
                    st.session_state.timelapse_url = gif_url
                    st.success("Timelapse Generated!")
                elif error:
                    st.error(f"Timelapse error: {error}")
    
    add_layer_control(base_map)
    
    st.markdown(f"### 🗺️ {selected_city}, {selected_state}")
    st.markdown('<div class="map-container">', unsafe_allow_html=True)
    map_data = st_folium(base_map, width=None, height=550, returned_objects=["all_drawings", "last_clicked"])
    st.markdown('</div>', unsafe_allow_html=True)
    
    map_info_col1, map_info_col2 = st.columns(2)
    
    with map_info_col1:
        if enable_drawing and map_data and map_data.get("all_drawings"):
            st.info(f"📐 {len(map_data['all_drawings'])} shape(s) drawn")
            st.session_state.drawn_geometry = map_data["all_drawings"]
    
    with map_info_col2:
        if enable_pixel_inspector and map_data and map_data.get("last_clicked"):
            click_lat = map_data["last_clicked"]["lat"]
            click_lng = map_data["last_clicked"]["lng"]
            st.info(f"📍 Clicked: {click_lat:.4f}, {click_lng:.4f}")
            
            if st.session_state.get("index_images"):
                try:
                    pixel_vals = {}
                    for idx_name, idx_image in st.session_state.index_images.items():
                        if idx_image is not None:
                            val = sample_pixel_value(idx_image, click_lat, click_lng)
                            if val:
                                pixel_vals[idx_name] = val.get(idx_name, "N/A")
                    
                    if pixel_vals:
                        cols = st.columns(min(len(pixel_vals), 5))
                        for i, (name, val) in enumerate(pixel_vals.items()):
                            with cols[i % len(cols)]:
                                if isinstance(val, (int, float)):
                                    st.metric(name, f"{val:.3f}")
                                else:
                                    st.metric(name, str(val))
                except Exception as e:
                    st.warning(f"Could not sample pixel values: {str(e)}")
    
    if st.session_state.get("analysis_complete"):
        st.markdown("---")
        
        if analysis_mode == "Timelapse Animation" and st.session_state.get("timelapse_url"):
            st.markdown(f"## 🎞️ {tl_type}")
            st.markdown(f"**Period:** {start_year} - {end_year} | **Frequency:** {frequency}")
            
            st.image(st.session_state.timelapse_url, caption=f"{tl_type} Variation over time", use_container_width=True)
            
            st.markdown(f"[📥 Download GIF]({st.session_state.timelapse_url})")
            
            st.info("💡 Green areas indicate healthy vegetation. Brown/White areas indicate urban usage, clouds, or barren land.")
            st.markdown("---")

        st.markdown("## 📊 Analysis Results")
        
        if analysis_mode == "Time Series Comparison" and st.session_state.get("time_series_stats"):
            stats1, stats2, year1, year2 = st.session_state.time_series_stats
            
            if stats1 and stats2:
                change_summary = calculate_change_summary(stats1, stats2)
                
                if change_summary:
                    col1, col2, col3, col4 = st.columns(4)
                    
                    biggest_inc = change_summary["biggest_increase"]
                    biggest_dec = change_summary["biggest_decrease"]
                    veg_change = change_summary["net_vegetation_change"]
                    built_change = change_summary["net_built_change"]
                    
                    with col1:
                        st.markdown(f"""
                        <div class="stat-card">
                            <div class="stat-value" style="color: #2ecc71;">📈 +{biggest_inc['pct_change']:.1f}%</div>
                            <div class="stat-label">Largest Increase: {biggest_inc['class']}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col2:
                        st.markdown(f"""
                        <div class="stat-card">
                            <div class="stat-value" style="color: #e74c3c;">📉 {biggest_dec['pct_change']:.1f}%</div>
                            <div class="stat-label">Largest Decrease: {biggest_dec['class']}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col3:
                        color = "#2ecc71" if veg_change >= 0 else "#e74c3c"
                        st.markdown(f"""
                        <div class="stat-card">
                            <div class="stat-value" style="color: {color};">🌿 {'+' if veg_change >= 0 else ''}{veg_change:.2f} km²</div>
                            <div class="stat-label">Net Vegetation Change</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col4:
                        color = "#e74c3c" if built_change >= 0 else "#2ecc71"
                        st.markdown(f"""
                        <div class="stat-card">
                            <div class="stat-value" style="color: {color};">🏘️ {'+' if built_change >= 0 else ''}{built_change:.2f} km²</div>
                            <div class="stat-label">Net Built-up Change</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    res_col1, res_col2 = st.columns(2)
                    
                    with res_col1:
                        st.markdown(f"#### {year1} Land Cover")
                        render_pie_chart(stats1.get("classes", {}), f"Distribution {year1}")
                    
                    with res_col2:
                        st.markdown(f"#### {year2} Land Cover")
                        render_pie_chart(stats2.get("classes", {}), f"Distribution {year2}")
                    
                    with st.expander("📋 Detailed Change Analysis", expanded=False):
                        change_data = []
                        for change in change_summary["all_changes"]:
                            if abs(change["pct_change"]) > 0.1:
                                change_data.append({
                                    "Class": change["class"],
                                    "Change (%)": f"{change['pct_change']:+.1f}%",
                                    "Trend": "📈" if change["pct_change"] > 0 else "📉"
                                })
                        if change_data:
                            st.dataframe(pd.DataFrame(change_data), use_container_width=True, hide_index=True)
                    
                    csv_data = generate_change_analysis_csv(stats1, stats2, year1, year2, selected_city)
                    if csv_data:
                        st.download_button(
                            "📥 Download Change Analysis CSV",
                            data=csv_data,
                            file_name=f"lulc_change_{year1}_{year2}.csv",
                            mime="text/csv"
                        )
        
        elif show_lulc and st.session_state.get("lulc_stats"):
            stats = st.session_state.lulc_stats
            
            summary_col1, summary_col2, summary_col3 = st.columns(3)
            
            total_area = stats.get('total_area_sqkm', 0)
            classes_data = stats.get("classes", {})
            
            veg_pct = classes_data.get("Trees", {}).get("percentage", 0) + classes_data.get("Grass", {}).get("percentage", 0) + classes_data.get("Crops", {}).get("percentage", 0)
            built_pct = classes_data.get("Built Area", {}).get("percentage", 0)
            water_pct = classes_data.get("Water", {}).get("percentage", 0)
            
            with summary_col1:
                st.markdown(f"""
                <div class="stat-card">
                    <div class="stat-value">🌿 {veg_pct:.1f}%</div>
                    <div class="stat-label">Vegetation Cover</div>
                </div>
                """, unsafe_allow_html=True)
            
            with summary_col2:
                st.markdown(f"""
                <div class="stat-card">
                    <div class="stat-value">🏘️ {built_pct:.1f}%</div>
                    <div class="stat-label">Built-up Area</div>
                </div>
                """, unsafe_allow_html=True)
            
            with summary_col3:
                st.markdown(f"""
                <div class="stat-card">
                    <div class="stat-value">📏 {total_area:.1f} km²</div>
                    <div class="stat-label">Total Area Analyzed</div>
                </div>
                """, unsafe_allow_html=True)
            
            res_col1, res_col2 = st.columns(2)
            
            with res_col1:
                st.markdown("#### 📊 Land Cover Distribution")
                chart_type = st.radio("Chart Type", ["Pie", "Bar"], horizontal=True, key="chart_type")
                if chart_type == "Pie":
                    render_pie_chart(classes_data, "Land Cover Distribution")
                else:
                    render_bar_chart(classes_data, "Land Cover by Area")
            
            with res_col2:
                st.markdown("#### 🎨 Legend & Details")
                render_lulc_legend()
                
                st.markdown("##### Area Breakdown")
                for name, data in sorted(classes_data.items(), key=lambda x: x[1]["percentage"], reverse=True):
                    if data["percentage"] > 0.5:
                        st.progress(data["percentage"] / 100)
                        st.caption(f"{name}: {data['percentage']:.1f}% ({data['area_sqkm']:.2f} km²)")
            
            csv_data = generate_lulc_csv(stats, selected_city, selected_year)
            if csv_data:
                st.download_button(
                    "📥 Download LULC Statistics CSV",
                    data=csv_data,
                    file_name=f"lulc_{selected_city}_{selected_year}.csv",
                    mime="text/csv"
                )
        
        if show_indices and st.session_state.get("index_images"):
            st.markdown("---")
            st.markdown("### 🌱 Vegetation Indices")
            
            index_means = st.session_state.get("index_means", {})
            if index_means:
                st.markdown("#### 📊 Mean Index Values")
                mean_cols = st.columns(min(len(index_means), 5))
                
                index_colors = {
                    "NDVI": "#2ecc71",
                    "NDWI": "#3498db",
                    "NDBI": "#e74c3c",
                    "EVI": "#27ae60",
                    "SAVI": "#f39c12"
                }
                
                for i, (idx_name, mean_val) in enumerate(index_means.items()):
                    with mean_cols[i % len(mean_cols)]:
                        color = index_colors.get(idx_name, "#666")
                        if mean_val is not None:
                            st.markdown(f"""
                            <div class="stat-card">
                                <div class="stat-value" style="color: {color};">{mean_val:.4f}</div>
                                <div class="stat-label">{idx_name} Mean</div>
                            </div>
                            """, unsafe_allow_html=True)
                
                st.markdown("---")
            
            num_indices = len(show_indices)
            if num_indices <= 3:
                idx_cols = st.columns(num_indices)
            else:
                idx_cols = st.columns(3)
            
            for i, idx in enumerate(show_indices):
                with idx_cols[i % len(idx_cols)]:
                    render_index_legend_with_opacity(idx, key_prefix="lulc_")
        
        if st.session_state.get("current_geometry"):
            st.markdown("---")
            st.markdown("### 📈 Trend Analysis & Forecast")
            st.caption("Analyze historical trends and forecast future values based on linear regression of satellite data (2017-present)")
            
            trend_col1, trend_col2 = st.columns(2)
            
            current_year = datetime.now().year
            
            with trend_col1:
                history_start = st.selectbox(
                    "Historical Start Year",
                    options=list(range(2017, current_year)),
                    index=0,
                    key="trend_start_year"
                )
            
            with trend_col2:
                history_end = st.selectbox(
                    "Historical End Year",
                    options=list(range(history_start + 1, current_year + 1)),
                    index=min(current_year - history_start - 1, len(list(range(history_start + 1, current_year + 1))) - 1),
                    key="trend_end_year"
                )
            
            forecast_col1, forecast_col2 = st.columns(2)
            
            with forecast_col1:
                trend_type = st.multiselect(
                    "Analyze",
                    ["LULC Classes", "Vegetation Indices"],
                    default=["LULC Classes", "Vegetation Indices"],
                    key="trend_type"
                )
            
            with forecast_col2:
                forecast_years = st.multiselect(
                    "Forecast Years",
                    options=list(range(current_year + 1, current_year + 11)),
                    default=[current_year + 1, current_year + 3, current_year + 5],
                    key="forecast_years"
                )
            
            if st.button("🔍 Run Trend Analysis", use_container_width=True, key="run_trends"):
                geometry = st.session_state.current_geometry
                
                with st.spinner("Fetching historical data and calculating trends..."):
                    try:
                        if "LULC Classes" in trend_type:
                            lulc_data = get_historical_lulc_data(geometry, history_start, history_end)
                            if lulc_data and len(lulc_data) >= 2:
                                st.session_state.lulc_historical = lulc_data
                                st.session_state.lulc_trends = analyze_lulc_trends(lulc_data)
                                if forecast_years:
                                    st.session_state.lulc_forecast = generate_forecast_lulc(
                                        st.session_state.lulc_trends, forecast_years
                                    )
                            else:
                                st.warning("Insufficient LULC data for trend analysis (need at least 2 years)")
                        
                        if "Vegetation Indices" in trend_type:
                            index_data = get_historical_index_data(
                                geometry, history_start, history_end, 
                                satellite=satellite if 'satellite' in dir() else "Sentinel-2"
                            )
                            if index_data:
                                valid_indices = {k: v for k, v in index_data.items() if len(v) >= 2}
                                if valid_indices:
                                    st.session_state.index_historical = valid_indices
                                    st.session_state.index_trends = analyze_index_trends(valid_indices)
                                    if forecast_years:
                                        st.session_state.index_forecast = generate_forecast_indices(
                                            st.session_state.index_trends, forecast_years
                                        )
                                else:
                                    st.warning("Insufficient index data for trend analysis")
                        
                        st.success("Trend analysis complete!")
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"Error during trend analysis: {str(e)}")
            
            if st.session_state.get("lulc_trends"):
                st.markdown("#### 🏞️ LULC Trend Results")
                
                lulc_summary = get_trend_summary(st.session_state.lulc_trends, "LULC")
                if lulc_summary:
                    trend_status_cols = st.columns(3)
                    
                    with trend_status_cols[0]:
                        increases = lulc_summary.get("significant_increases", [])
                        if increases:
                            st.markdown("**📈 Significant Increases:**")
                            for item in increases:
                                st.markdown(f"- {item['name']}: +{item['change_per_year']:.2f}%/yr (R²={item['r_squared']:.2f})")
                        else:
                            st.caption("No significant increases detected")
                    
                    with trend_status_cols[1]:
                        decreases = lulc_summary.get("significant_decreases", [])
                        if decreases:
                            st.markdown("**📉 Significant Decreases:**")
                            for item in decreases:
                                st.markdown(f"- {item['name']}: {item['change_per_year']:.2f}%/yr (R²={item['r_squared']:.2f})")
                        else:
                            st.caption("No significant decreases detected")
                    
                    with trend_status_cols[2]:
                        stable = lulc_summary.get("stable", [])
                        if stable:
                            st.markdown("**➡️ Stable Classes:**")
                            st.markdown(", ".join(stable[:5]))
                
                lulc_forecast = st.session_state.get("lulc_forecast")
                if lulc_forecast and forecast_years:
                    st.markdown("##### 🔮 LULC Forecast")
                    st.caption("Based on linear regression with 95% confidence intervals")
                    
                    forecast_data = []
                    for lulc_class, years_data in lulc_forecast.items():
                        if years_data:
                            for year, values in years_data.items():
                                forecast_data.append({
                                    "Class": lulc_class,
                                    "Year": year,
                                    "Predicted (%)": f"{values['predicted']:.1f}",
                                    "Range": f"{values['lower_bound']:.1f} - {values['upper_bound']:.1f}%"
                                })
                    
                    if forecast_data:
                        df = pd.DataFrame(forecast_data)
                        st.dataframe(df, use_container_width=True, hide_index=True)
            
            if st.session_state.get("index_trends"):
                st.markdown("#### 🌿 Vegetation Index Trend Results")
                
                index_summary = get_trend_summary(st.session_state.index_trends, "Indices")
                if index_summary:
                    idx_trend_cols = st.columns(2)
                    
                    with idx_trend_cols[0]:
                        increases = index_summary.get("significant_increases", [])
                        if increases:
                            st.markdown("**📈 Improving Indices:**")
                            for item in increases:
                                st.markdown(f"- {item['name']}: +{item['change_per_year']:.4f}/yr (R²={item['r_squared']:.2f})")
                        else:
                            st.caption("No significant improvements")
                    
                    with idx_trend_cols[1]:
                        decreases = index_summary.get("significant_decreases", [])
                        if decreases:
                            st.markdown("**📉 Declining Indices:**")
                            for item in decreases:
                                st.markdown(f"- {item['name']}: {item['change_per_year']:.4f}/yr (R²={item['r_squared']:.2f})")
                        else:
                            st.caption("No significant declines")
                
                index_forecast = st.session_state.get("index_forecast")
                if index_forecast and forecast_years:
                    st.markdown("##### 🔮 Vegetation Index Forecast")
                    
                    idx_forecast_data = []
                    for idx_name, years_data in index_forecast.items():
                        if years_data:
                            for year, values in years_data.items():
                                idx_forecast_data.append({
                                    "Index": idx_name,
                                    "Year": year,
                                    "Predicted": f"{values['predicted']:.4f}",
                                    "Range": f"{values['lower_bound']:.4f} - {values['upper_bound']:.4f}"
                                })
                    
                    if idx_forecast_data:
                        df = pd.DataFrame(idx_forecast_data)
                        st.dataframe(df, use_container_width=True, hide_index=True)
            
            st.caption("**Note:** Forecasts are based on linear regression extrapolation of historical trends. Actual future values may differ due to policy changes, climate variations, and other factors. Use forecasts for indicative purposes only.")
        
        if st.session_state.get("current_image") and st.session_state.get("current_geometry"):
            st.markdown("---")
            st.markdown("### 📥 Export Options")
            
            export_col1, export_col2, export_col3 = st.columns(3)
            
            default_scale = 30 if satellite == "Landsat 8/9" else 10
            
            with export_col1:
                st.markdown("**GeoTIFF Export**")
                export_scale = st.select_slider(
                    "Resolution (meters)",
                    options=[10, 20, 30, 50, 100, 250, 500, 1000],
                    value=default_scale,
                    key="export_scale",
                    help="Higher values = smaller file size. Use larger values for big areas."
                )
                
                if st.button("📦 Generate GeoTIFF", use_container_width=True):
                    with st.spinner("Generating..."):
                        url, error = get_safe_download_url(
                            st.session_state.current_image,
                            st.session_state.current_geometry,
                            scale=export_scale
                        )
                        if url:
                            st.success("Ready!")
                            st.markdown(f"[📥 Download GeoTIFF]({url})")
                        elif error:
                            st.error(error)
                            st.info("💡 Try increasing the resolution value above to reduce file size.")
            
            with export_col2:
                st.markdown("**CSV Report**")
                if st.session_state.get("lulc_stats"):
                    csv_data = generate_lulc_csv(st.session_state.lulc_stats, selected_city, selected_year)
                    if csv_data:
                        st.download_button(
                            "📄 Download CSV Report",
                            data=csv_data,
                            file_name=f"lulc_{selected_city}_{selected_year}.csv",
                            mime="text/csv",
                            use_container_width=True
                        )
                else:
                    st.caption("Run LULC analysis to enable CSV export")
            
            with export_col3:
                st.markdown("**PDF Report**")
                if st.session_state.get("lulc_stats"):
                    if 'lulc_pdf' not in st.session_state or st.session_state.lulc_pdf is None:
                        sustainability = calculate_land_sustainability_score(st.session_state.lulc_stats)
                        report_data = {
                            'city_name': selected_city,
                            'state': selected_state,
                            'year': selected_year,
                            'date_range': f"{start_date} to {end_date}",
                            'satellite': satellite,
                            'total_area': st.session_state.lulc_stats.get('total_area_sqkm', 0),
                            'stats': st.session_state.lulc_stats.get('classes', {}),
                            'sustainability_score': sustainability,
                            'indices': st.session_state.get('index_means', {})
                        }
                        
                        # Generate Insights
                        insight_stats = {
                            'classes': st.session_state.lulc_stats.get('classes', {}),
                            'ndvi': {'mean': st.session_state.index_means.get('NDVI', 0)}
                        }
                        report_data['insights'] = generate_lulc_insights(insight_stats)
                        
                        st.session_state.lulc_pdf = generate_lulc_pdf_report(report_data)
                    
                    if st.session_state.get("lulc_pdf"):
                        st.download_button(
                            "📥 Download PDF Report",
                            data=st.session_state.lulc_pdf,
                            file_name=f"lulc_report_{selected_city}_{selected_year}.pdf",
                            mime="application/pdf",
                            use_container_width=True,
                            key="dl_lulc_pdf"
                        )
                    else:
                        st.error("Failed to generate PDF")
                else:
                    st.caption("Run analysis to enable PDF export")

elif not st.session_state.gee_initialized:
    render_info_box("Please check your GEE credentials in secrets.toml", "warning")
else:
    render_info_box("""
        <h4>Getting Started</h4>
        <ol>
            <li>Select a State and City</li>
            <li>Choose your analysis period</li>
            <li>Select satellite and options</li>
            <li>Click Run Analysis</li>
        </ol>
    """, "info")
