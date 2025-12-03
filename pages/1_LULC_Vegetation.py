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
    geojson_to_ee_geometry, get_safe_download_url, sample_pixel_value
)
from services.gee_lulc import (
    get_sentinel2_image, get_landsat_image, get_dynamic_world_lulc,
    get_sentinel_rgb_params, get_landsat_rgb_params, get_lulc_vis_params,
    calculate_lulc_statistics_with_area, get_lulc_change_analysis,
    calculate_change_summary, LULC_CLASSES
)
from services.gee_indices import (
    get_index_functions, get_index_vis_params, INDEX_INFO
)
from components.ui import (
    apply_enhanced_css, render_page_header, render_stat_card,
    render_info_box, init_common_session_state
)
from components.maps import (
    create_base_map, add_tile_layer, add_marker, add_buffer_circle, add_layer_control
)
from components.legends import (
    render_lulc_legend, render_index_legend_with_opacity
)
from components.charts import (
    render_pie_chart, render_bar_chart, generate_csv_download, render_download_button
)
from services.exports import (
    generate_lulc_csv, generate_change_analysis_csv, generate_pdf_report
)

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
    
    states = get_states()
    selected_state = st.selectbox("State", ["Select..."] + states, key="lulc_state")
    
    selected_city = None
    city_coords = None
    
    if selected_state != "Select...":
        cities = get_cities(selected_state)
        selected_city = st.selectbox("City", ["Select..."] + cities, key="lulc_city")
        
        if selected_city != "Select...":
            city_coords = get_city_coordinates(selected_state, selected_city)
            if city_coords:
                st.success(f"📍 {selected_city}, {selected_state}")
                st.caption(f"Lat: {city_coords['lat']:.4f}, Lon: {city_coords['lon']:.4f}")
    
    st.markdown("---")
    st.markdown("## 📅 Time Period")
    
    current_year = datetime.now().year
    years = list(range(2017, current_year + 1))
    
    analysis_mode = st.radio(
        "Analysis Mode",
        ["Single Period", "Time Series Comparison"],
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
    if enable_drawing and st.session_state.get("drawn_geometry"):
        use_custom_aoi = st.sidebar.checkbox("Use Custom AOI", value=False, key="lulc_use_custom")
    
    run_analysis = st.sidebar.button("🚀 Run Analysis", use_container_width=True, type="primary")
    
    base_map = create_base_map(city_coords["lat"], city_coords["lon"], enable_drawing=enable_drawing)
    add_marker(base_map, city_coords["lat"], city_coords["lon"], 
               popup=f"{selected_city}, {selected_state}", tooltip=selected_city)
    add_buffer_circle(base_map, city_coords["lat"], city_coords["lon"], buffer_km)
    
    if run_analysis:
        with st.spinner("Fetching satellite data and running analysis..."):
            try:
                if use_custom_aoi and st.session_state.get("drawn_geometry"):
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
                    
                    for idx in show_indices:
                        if idx in index_funcs:
                            try:
                                index_image = index_funcs[idx](image)
                                if index_image is not None:
                                    st.session_state.index_images[idx] = index_image
                                    index_params = get_index_vis_params(idx)
                                    index_url = get_tile_url(index_image, index_params)
                                    add_tile_layer(base_map, index_url, idx, 0.8)
                            except Exception as e:
                                st.warning(f"Could not calculate {idx}: {str(e)}")
                    
                    st.session_state.analysis_complete = True
                    st.success("Analysis complete!")
            
            except Exception as e:
                st.error(f"Error: {str(e)}")
    
    add_layer_control(base_map)
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown(f"### 🗺️ {selected_city}, {selected_state}")
        st.markdown('<div class="map-container">', unsafe_allow_html=True)
        map_data = st_folium(base_map, width=None, height=600, returned_objects=["all_drawings", "last_clicked"])
        st.markdown('</div>', unsafe_allow_html=True)
        
        if enable_drawing and map_data and map_data.get("all_drawings"):
            st.info(f"📐 {len(map_data['all_drawings'])} shape(s) drawn")
            st.session_state.drawn_geometry = map_data["all_drawings"]
        
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
                        st.markdown("**Index Values:**")
                        cols = st.columns(min(len(pixel_vals), 5))
                        for i, (name, val) in enumerate(pixel_vals.items()):
                            with cols[i % len(cols)]:
                                if isinstance(val, (int, float)):
                                    st.metric(name, f"{val:.3f}")
                                else:
                                    st.metric(name, str(val))
                except Exception as e:
                    st.warning(f"Could not sample pixel values: {str(e)}")
    
    with col2:
        if st.session_state.get("analysis_complete"):
            if analysis_mode == "Time Series Comparison" and st.session_state.get("time_series_stats"):
                stats1, stats2, year1, year2 = st.session_state.time_series_stats
                
                st.markdown(f"### 📈 Change: {year1} → {year2}")
                
                if stats1 and stats2:
                    change_summary = calculate_change_summary(stats1, stats2)
                    
                    if change_summary:
                        st.markdown("#### Key Insights")
                        
                        biggest_inc = change_summary["biggest_increase"]
                        biggest_dec = change_summary["biggest_decrease"]
                        
                        st.markdown(f"📈 **Largest Increase:** {biggest_inc['class']} (+{biggest_inc['pct_change']:.1f}%)")
                        st.markdown(f"📉 **Largest Decrease:** {biggest_dec['class']} ({biggest_dec['pct_change']:.1f}%)")
                        
                        veg_change = change_summary["net_vegetation_change"]
                        built_change = change_summary["net_built_change"]
                        
                        st.markdown("---")
                        st.markdown(f"🌿 **Net Vegetation:** {'+' if veg_change >= 0 else ''}{veg_change:.2f} km²")
                        st.markdown(f"🏘️ **Net Built-up:** {'+' if built_change >= 0 else ''}{built_change:.2f} km²")
                        
                        st.markdown("---")
                        with st.expander("View All Changes", expanded=False):
                            for change in change_summary["all_changes"]:
                                if abs(change["pct_change"]) > 0.1:
                                    arrow = "📈" if change["pct_change"] > 0 else "📉"
                                    st.caption(f"{arrow} {change['class']}: {change['pct_change']:+.1f}%")
                        
                        csv_data = generate_change_analysis_csv(stats1, stats2, year1, year2, selected_city)
                        if csv_data:
                            st.download_button(
                                "📥 Download CSV",
                                data=csv_data,
                                file_name=f"lulc_change_{year1}_{year2}.csv",
                                mime="text/csv",
                                use_container_width=True
                            )
            
            elif show_lulc and st.session_state.get("lulc_stats"):
                stats = st.session_state.lulc_stats
                
                st.markdown("### 📊 LULC Statistics")
                st.markdown(f"**Total Area: {stats.get('total_area_sqkm', 'N/A')} km²**")
                
                with st.expander("🎨 Legend", expanded=True):
                    render_lulc_legend()
                
                with st.expander("📊 Charts", expanded=True):
                    chart_type = st.radio("Chart Type", ["Bar", "Pie"], horizontal=True, key="chart_type")
                    if chart_type == "Pie":
                        render_pie_chart(stats.get("classes", {}), "Land Cover Distribution")
                    else:
                        render_bar_chart(stats.get("classes", {}), "Land Cover by Area")
                
                with st.expander("📋 Details", expanded=False):
                    classes_data = stats.get("classes", {})
                    for name, data in sorted(classes_data.items(), key=lambda x: x[1]["percentage"], reverse=True):
                        col_a, col_b = st.columns([3, 1])
                        with col_a:
                            st.progress(data["percentage"] / 100)
                            st.caption(f"{name}: {data['percentage']:.1f}%")
                        with col_b:
                            st.caption(f"{data['area_sqkm']:.1f} km²")
                
                csv_data = generate_lulc_csv(stats, selected_city, selected_year)
                if csv_data:
                    st.download_button(
                        "📥 Download CSV",
                        data=csv_data,
                        file_name=f"lulc_{selected_city}_{selected_year}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
            
            st.markdown("---")
            for idx in show_indices:
                opacity = render_index_legend_with_opacity(idx, key_prefix="lulc_")
            
            if st.session_state.get("current_image") and st.session_state.get("current_geometry"):
                st.markdown("---")
                st.markdown("### 📥 Export")
                
                export_scale = 30 if satellite == "Landsat 8/9" else 10
                
                if st.button("Generate GeoTIFF", use_container_width=True):
                    with st.spinner("Generating..."):
                        url, error = get_safe_download_url(
                            st.session_state.current_image,
                            st.session_state.current_geometry,
                            scale=export_scale
                        )
                        if url:
                            st.success("Ready!")
                            st.markdown(f"[📥 Download]({url})")
                        elif error:
                            st.warning(error)

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
