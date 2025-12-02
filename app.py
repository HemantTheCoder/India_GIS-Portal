import streamlit as st
import folium
from streamlit_folium import st_folium
from folium.plugins import Draw
import ee
import json
from datetime import datetime, date
import pandas as pd
import io

from india_cities import get_states, get_cities, get_city_coordinates, INDIA_DATA
from gee_utils import (
    initialize_gee,
    get_city_geometry,
    get_sentinel2_image,
    get_landsat_image,
    get_dynamic_world_lulc,
    calculate_ndvi_sentinel,
    calculate_ndwi_sentinel,
    calculate_ndbi_sentinel,
    calculate_evi_sentinel,
    calculate_savi_sentinel,
    calculate_ndvi_landsat,
    calculate_ndwi_landsat,
    calculate_ndbi_landsat,
    calculate_evi_landsat,
    calculate_savi_landsat,
    get_sentinel_rgb_params,
    get_landsat_rgb_params,
    get_lulc_vis_params,
    get_index_vis_params,
    get_tile_url,
    calculate_lulc_statistics,
    calculate_lulc_statistics_with_area,
    get_lulc_change_analysis,
    get_safe_download_url,
    calculate_geometry_area,
    geojson_to_ee_geometry,
    LULC_CLASSES,
    INDEX_INFO,
)

st.set_page_config(
    page_title="India GIS & Remote Sensing Portal",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1E3A5F;
        text-align: center;
        padding: 1rem 0;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .legend-box {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .legend-item {
        display: flex;
        align-items: center;
        margin: 0.5rem 0;
    }
    .legend-color {
        width: 24px;
        height: 24px;
        border-radius: 4px;
        margin-right: 10px;
        border: 1px solid #ddd;
    }
    .stat-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
        padding: 1.5rem;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
    }
    .info-box {
        background-color: #e7f3ff;
        border-left: 4px solid #2196F3;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 0 8px 8px 0;
    }
    .success-box {
        background-color: #e8f5e9;
        border-left: 4px solid #4CAF50;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 0 8px 8px 0;
    }
    .warning-box {
        background-color: #fff3e0;
        border-left: 4px solid #FF9800;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 0 8px 8px 0;
    }
    .change-positive {
        color: #4CAF50;
        font-weight: bold;
    }
    .change-negative {
        color: #f44336;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

def init_session_state():
    if "gee_initialized" not in st.session_state:
        st.session_state.gee_initialized = False
    if "current_map" not in st.session_state:
        st.session_state.current_map = None
    if "analysis_complete" not in st.session_state:
        st.session_state.analysis_complete = False
    if "lulc_stats" not in st.session_state:
        st.session_state.lulc_stats = None
    if "current_image" not in st.session_state:
        st.session_state.current_image = None
    if "current_geometry" not in st.session_state:
        st.session_state.current_geometry = None
    if "time_series_stats" not in st.session_state:
        st.session_state.time_series_stats = None
    if "drawn_geometry" not in st.session_state:
        st.session_state.drawn_geometry = None

def create_base_map(lat, lon, zoom=11, enable_drawing=False):
    m = folium.Map(
        location=[lat, lon],
        zoom_start=zoom,
        tiles="OpenStreetMap",
    )
    
    if enable_drawing:
        draw = Draw(
            draw_options={
                'polyline': False,
                'rectangle': True,
                'polygon': True,
                'circle': True,
                'marker': False,
                'circlemarker': False,
            },
            edit_options={'edit': False}
        )
        draw.add_to(m)
    
    return m

def add_tile_layer(map_obj, tile_url, layer_name, opacity=1.0):
    folium.TileLayer(
        tiles=tile_url,
        attr="Google Earth Engine",
        name=layer_name,
        overlay=True,
        control=True,
        opacity=opacity,
    ).add_to(map_obj)
    return map_obj

def render_lulc_legend():
    st.markdown("### Land Cover Classes")
    for class_id, info in LULC_CLASSES.items():
        col1, col2 = st.columns([1, 4])
        with col1:
            st.markdown(
                f'<div style="background-color: {info["color"]}; width: 30px; height: 30px; border-radius: 4px; border: 1px solid #ccc;"></div>',
                unsafe_allow_html=True,
            )
        with col2:
            st.write(info["name"])

def render_index_legend(index_name):
    info = INDEX_INFO.get(index_name, {})
    st.markdown(f"### {info.get('name', index_name)}")
    st.markdown(f"*{info.get('description', '')}*")
    
    palette = info.get("palette", [])
    if palette:
        gradient = ", ".join(palette)
        st.markdown(
            f'<div style="background: linear-gradient(to right, {gradient}); height: 30px; border-radius: 4px; margin: 10px 0;"></div>',
            unsafe_allow_html=True,
        )
        col1, col2 = st.columns(2)
        with col1:
            st.write("Low")
        with col2:
            st.write("High", unsafe_allow_html=True)

def render_statistics_with_area(stats, city_name=""):
    if not stats or "classes" not in stats:
        st.warning("Unable to calculate statistics for this area.")
        return
    
    st.markdown("### Land Cover Statistics")
    st.markdown(f"**Total Area: {stats.get('total_area_sqkm', 'N/A')} km²**")
    
    classes_data = stats["classes"]
    df_data = []
    
    for name, data in sorted(classes_data.items(), key=lambda x: x[1]["percentage"], reverse=True):
        df_data.append({
            "Class": name,
            "Area (km²)": data["area_sqkm"],
            "Percentage": data["percentage"],
            "Color": data["color"]
        })
    
    df = pd.DataFrame(df_data)
    
    for _, row in df.iterrows():
        col1, col2, col3, col4 = st.columns([1, 2, 1, 1])
        with col1:
            st.markdown(
                f'<div style="background-color: {row["Color"]}; width: 24px; height: 24px; border-radius: 4px; border: 1px solid #ccc;"></div>',
                unsafe_allow_html=True,
            )
        with col2:
            st.progress(row["Percentage"] / 100)
        with col3:
            st.write(f"{row['Percentage']:.1f}%")
        with col4:
            st.write(f"{row['Area (km²)']:.2f} km²")
        st.caption(row["Class"])
    
    csv_df = df.drop(columns=["Color"])
    csv_buffer = io.StringIO()
    csv_df.to_csv(csv_buffer, index=False)
    csv_data = csv_buffer.getvalue()
    
    st.download_button(
        label="📥 Download Statistics (CSV)",
        data=csv_data,
        file_name=f"lulc_statistics_{city_name}_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv",
        use_container_width=True,
    )

def render_time_series_comparison(stats1, stats2, year1, year2):
    if not stats1 or not stats2:
        st.warning("Unable to compare time series data.")
        return
    
    st.markdown(f"### LULC Change Analysis: {year1} vs {year2}")
    
    classes1 = stats1.get("classes", {})
    classes2 = stats2.get("classes", {})
    
    all_classes = set(classes1.keys()) | set(classes2.keys())
    
    comparison_data = []
    for class_name in all_classes:
        data1 = classes1.get(class_name, {"percentage": 0, "area_sqkm": 0})
        data2 = classes2.get(class_name, {"percentage": 0, "area_sqkm": 0})
        
        pct_change = data2.get("percentage", 0) - data1.get("percentage", 0)
        area_change = data2.get("area_sqkm", 0) - data1.get("area_sqkm", 0)
        
        comparison_data.append({
            "Class": class_name,
            f"{year1} (%)": data1.get("percentage", 0),
            f"{year2} (%)": data2.get("percentage", 0),
            "Change (%)": pct_change,
            f"{year1} (km²)": data1.get("area_sqkm", 0),
            f"{year2} (km²)": data2.get("area_sqkm", 0),
            "Change (km²)": area_change,
        })
    
    df = pd.DataFrame(comparison_data)
    df = df.sort_values("Change (%)", key=abs, ascending=False)
    
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    st.markdown("#### Key Changes")
    for _, row in df.iterrows():
        change = row["Change (%)"]
        if abs(change) > 0.5:
            if change > 0:
                st.markdown(f"- **{row['Class']}**: <span class='change-positive'>+{change:.2f}%</span> (+{row['Change (km²)']:.2f} km²)", unsafe_allow_html=True)
            else:
                st.markdown(f"- **{row['Class']}**: <span class='change-negative'>{change:.2f}%</span> ({row['Change (km²)']:.2f} km²)", unsafe_allow_html=True)
    
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    csv_data = csv_buffer.getvalue()
    
    st.download_button(
        label="📥 Download Change Analysis (CSV)",
        data=csv_data,
        file_name=f"lulc_change_{year1}_vs_{year2}.csv",
        mime="text/csv",
        use_container_width=True,
    )

def main():
    init_session_state()
    
    st.markdown('<div class="main-header">🛰️ India GIS & Remote Sensing Portal</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Analyze Land Use, Land Cover, and Vegetation Indices for Indian Cities</div>', unsafe_allow_html=True)
    
    with st.sidebar:
        st.markdown("## 🔐 GEE Authentication")
        
        st.markdown("""
        <div class="info-box">
        <strong>Google Earth Engine Setup:</strong><br>
        1. Go to <a href="https://earthengine.google.com/" target="_blank">Google Earth Engine</a><br>
        2. Sign up for a free account<br>
        3. Create a service account and download the JSON key<br>
        4. Paste the JSON key below
        </div>
        """, unsafe_allow_html=True)
        
        auth_method = st.radio(
            "Authentication Method",
            ["Service Account (JSON Key)", "Default Credentials"],
            help="Use service account for production, or default credentials if already authenticated"
        )
        
        if auth_method == "Service Account (JSON Key)":
            service_account_json = st.text_area(
                "Paste Service Account JSON Key",
                height=150,
                placeholder='{"type": "service_account", "project_id": "...", ...}',
            )
            
            if st.button("🔓 Initialize GEE", use_container_width=True):
                if service_account_json:
                    try:
                        key_data = json.loads(service_account_json)
                        if initialize_gee(key_data):
                            st.session_state.gee_initialized = True
                            st.success("GEE initialized successfully!")
                            st.rerun()
                        else:
                            st.error("Failed to initialize GEE. Check your credentials.")
                    except json.JSONDecodeError:
                        st.error("Invalid JSON format. Please check your key.")
                else:
                    st.warning("Please paste your service account JSON key.")
        else:
            if st.button("🔓 Initialize with Default Credentials", use_container_width=True):
                if initialize_gee():
                    st.session_state.gee_initialized = True
                    st.success("GEE initialized successfully!")
                    st.rerun()
                else:
                    st.error("Failed to initialize GEE. Please authenticate first.")
        
        if st.session_state.gee_initialized:
            st.markdown('<div class="success-box">✅ GEE Connected</div>', unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown("## 📍 Location Selection")
        
        states = get_states()
        selected_state = st.selectbox("Select State", ["Select a state..."] + states)
        
        selected_city = None
        city_coords = None
        
        if selected_state and selected_state != "Select a state...":
            cities = get_cities(selected_state)
            selected_city = st.selectbox("Select City", ["Select a city..."] + cities)
            
            if selected_city and selected_city != "Select a city...":
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
            help="Compare LULC changes between two different years"
        )
        
        if analysis_mode == "Single Period":
            selected_year = st.selectbox("Select Year", years[::-1])
            
            date_range = st.radio(
                "Date Range",
                ["Full Year", "Custom Range"],
            )
            
            if date_range == "Full Year":
                start_date = f"{selected_year}-01-01"
                end_date = f"{selected_year}-12-31"
            else:
                col1, col2 = st.columns(2)
                with col1:
                    start = st.date_input(
                        "Start Date",
                        value=date(selected_year, 1, 1),
                        min_value=date(2017, 1, 1),
                        max_value=date(current_year, 12, 31),
                    )
                with col2:
                    end = st.date_input(
                        "End Date",
                        value=date(selected_year, 12, 31),
                        min_value=date(2017, 1, 1),
                        max_value=date(current_year, 12, 31),
                    )
                start_date = start.strftime("%Y-%m-%d")
                end_date = end.strftime("%Y-%m-%d")
            
            st.caption(f"Period: {start_date} to {end_date}")
            compare_year1, compare_year2 = None, None
        else:
            col1, col2 = st.columns(2)
            with col1:
                compare_year1 = st.selectbox("Year 1 (Earlier)", years[::-1], index=len(years)-1)
            with col2:
                compare_year2 = st.selectbox("Year 2 (Later)", years[::-1], index=0)
            
            start_date = f"{compare_year2}-01-01"
            end_date = f"{compare_year2}-12-31"
            selected_year = compare_year2
        
        st.markdown("---")
        st.markdown("## 🛰️ Data Source")
        
        satellite = st.radio(
            "Satellite",
            ["Sentinel-2", "Landsat 8/9"],
            help="Sentinel-2 has 10m resolution, Landsat has 30m resolution"
        )
        
        buffer_km = st.slider(
            "Analysis Radius (km)",
            min_value=5,
            max_value=50,
            value=15,
            help="Area around city center to analyze"
        )
        
        st.markdown("---")
        st.markdown("## 📊 Analysis Options")
        
        show_lulc = st.checkbox("Land Use / Land Cover (LULC)", value=True)
        show_indices = st.multiselect(
            "Vegetation/Urban Indices",
            ["NDVI", "NDWI", "NDBI", "EVI", "SAVI"],
            default=["NDVI"],
        )
        show_rgb = st.checkbox("True Color (RGB) Image", value=True)
        enable_drawing = st.checkbox("Enable Custom AOI Drawing", value=False, 
                                     help="Draw custom areas on the map to analyze specific regions")
    
    if city_coords:
        base_map = create_base_map(city_coords["lat"], city_coords["lon"], enable_drawing=enable_drawing)
        
        folium.Marker(
            [city_coords["lat"], city_coords["lon"]],
            popup=f"{selected_city}, {selected_state}",
            tooltip=selected_city,
            icon=folium.Icon(color="red", icon="info-sign"),
        ).add_to(base_map)
        
        folium.Circle(
            [city_coords["lat"], city_coords["lon"]],
            radius=buffer_km * 1000,
            color="#3388ff",
            fill=True,
            fillOpacity=0.1,
            weight=2,
        ).add_to(base_map)
        
        if st.session_state.gee_initialized:
            use_custom_aoi = st.sidebar.checkbox(
                "Use Custom AOI (if drawn)",
                value=False,
                help="Check this to use a custom drawn area instead of the city buffer",
                disabled=not st.session_state.drawn_geometry
            )
            
            if st.sidebar.button("🚀 Run Analysis", use_container_width=True, type="primary"):
                with st.spinner("Fetching satellite data and running analysis..."):
                    try:
                        if use_custom_aoi and st.session_state.drawn_geometry:
                            first_drawing = st.session_state.drawn_geometry[0]
                            geometry = geojson_to_ee_geometry(first_drawing)
                            if geometry is None:
                                st.warning("Could not parse custom AOI. Using city buffer instead.")
                                geometry = get_city_geometry(city_coords["lat"], city_coords["lon"], buffer_km)
                        else:
                            geometry = get_city_geometry(city_coords["lat"], city_coords["lon"], buffer_km)
                        
                        st.session_state.current_geometry = geometry
                        
                        if satellite == "Sentinel-2":
                            image = get_sentinel2_image(geometry, start_date, end_date)
                            rgb_params_func = get_sentinel_rgb_params
                            ndvi_func = calculate_ndvi_sentinel
                            ndwi_func = calculate_ndwi_sentinel
                            ndbi_func = calculate_ndbi_sentinel
                            evi_func = calculate_evi_sentinel
                            savi_func = calculate_savi_sentinel
                        else:
                            image = get_landsat_image(geometry, start_date, end_date)
                            rgb_params_func = get_landsat_rgb_params
                            ndvi_func = calculate_ndvi_landsat
                            ndwi_func = calculate_ndwi_landsat
                            ndbi_func = calculate_ndbi_landsat
                            evi_func = calculate_evi_landsat
                            savi_func = calculate_savi_landsat
                        
                        if image is None:
                            st.error(f"No cloud-free {satellite} images found for the selected period. Try a different date range.")
                        else:
                            st.session_state.current_image = image
                            
                            if show_rgb:
                                rgb_params = rgb_params_func(image)
                                rgb_url = get_tile_url(image, rgb_params)
                                base_map = add_tile_layer(base_map, rgb_url, f"{satellite} RGB", 0.9)
                            
                            if show_lulc:
                                lulc = get_dynamic_world_lulc(geometry, start_date, end_date)
                                if lulc:
                                    lulc_params = get_lulc_vis_params()
                                    lulc_url = get_tile_url(lulc, lulc_params)
                                    base_map = add_tile_layer(base_map, lulc_url, "LULC (Dynamic World)", 0.8)
                                    
                                    st.session_state.lulc_stats = calculate_lulc_statistics_with_area(lulc, geometry)
                                    
                                    if analysis_mode == "Time Series Comparison" and compare_year1 and compare_year2:
                                        stats1, stats2, _ = get_lulc_change_analysis(geometry, compare_year1, compare_year2)
                                        st.session_state.time_series_stats = (stats1, stats2, compare_year1, compare_year2)
                                else:
                                    st.warning("LULC data not available for the selected period.")
                            
                            index_funcs = {
                                "NDVI": ndvi_func,
                                "NDWI": ndwi_func,
                                "NDBI": ndbi_func,
                                "EVI": evi_func,
                                "SAVI": savi_func,
                            }
                            
                            for idx in show_indices:
                                if idx in index_funcs:
                                    index_image = index_funcs[idx](image)
                                    index_params = get_index_vis_params(idx)
                                    index_url = get_tile_url(index_image, index_params)
                                    base_map = add_tile_layer(base_map, index_url, idx, 0.8)
                            
                            st.session_state.analysis_complete = True
                            st.success("Analysis complete! Toggle layers using the control panel on the map.")
                    
                    except Exception as e:
                        st.error(f"Error during analysis: {str(e)}")
                        st.info("Please check your GEE credentials and try again.")
        else:
            st.sidebar.warning("⚠️ Please initialize GEE first")
        
        folium.LayerControl(collapsed=False).add_to(base_map)
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.markdown(f"### 🗺️ {selected_city}, {selected_state}")
            map_data = st_folium(base_map, width=None, height=600, returned_objects=["all_drawings"])
            
            if enable_drawing and map_data and map_data.get("all_drawings"):
                st.info(f"📐 Custom area(s) drawn: {len(map_data['all_drawings'])} shape(s)")
                st.session_state.drawn_geometry = map_data["all_drawings"]
        
        with col2:
            if st.session_state.analysis_complete:
                if analysis_mode == "Time Series Comparison" and st.session_state.time_series_stats:
                    stats1, stats2, year1, year2 = st.session_state.time_series_stats
                    render_time_series_comparison(stats1, stats2, year1, year2)
                elif show_lulc and st.session_state.lulc_stats:
                    render_lulc_legend()
                    st.markdown("---")
                    render_statistics_with_area(st.session_state.lulc_stats, selected_city or "city")
            
            for idx in show_indices:
                if st.session_state.analysis_complete:
                    st.markdown("---")
                    render_index_legend(idx)
            
            if st.session_state.analysis_complete and st.session_state.current_image:
                st.markdown("---")
                st.markdown("### 📥 Export Options")
                
                export_scale = 30 if satellite == "Landsat 8/9" else 10
                
                if st.button("Generate GeoTIFF Download Link", use_container_width=True):
                    try:
                        if st.session_state.current_geometry:
                            with st.spinner("Generating download link..."):
                                download_url, error = get_safe_download_url(
                                    st.session_state.current_image,
                                    st.session_state.current_geometry,
                                    scale=export_scale,
                                )
                                if download_url:
                                    st.success("Download link ready!")
                                    st.markdown(f"[📥 Download GeoTIFF]({download_url})")
                                    st.caption(f"Resolution: {export_scale}m per pixel")
                                elif error:
                                    st.warning(error)
                    except Exception as e:
                        st.warning(f"Export not available: {str(e)}")
    
    else:
        st.markdown("""
        <div class="info-box">
        <h3>🚀 Getting Started</h3>
        <ol>
            <li><strong>Initialize GEE:</strong> Set up your Google Earth Engine credentials in the sidebar</li>
            <li><strong>Select Location:</strong> Choose a state and city from the dropdown menus</li>
            <li><strong>Set Time Period:</strong> Select the year or date range for analysis</li>
            <li><strong>Choose Data:</strong> Select satellite source and analysis options</li>
            <li><strong>Run Analysis:</strong> Click the "Run Analysis" button to generate maps</li>
        </ol>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("### 📊 Available Analyses")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            #### 🏞️ Land Use / Land Cover (LULC)
            Using Google's Dynamic World dataset:
            - Water bodies
            - Trees and forests
            - Grasslands
            - Crops and agriculture
            - Built-up areas
            - Bare ground
            - Snow and ice
            """)
        
        with col2:
            st.markdown("""
            #### 🌿 Vegetation & Urban Indices
            - **NDVI**: Vegetation health and density
            - **NDWI**: Water body detection
            - **NDBI**: Built-up area identification
            - **EVI**: Enhanced vegetation assessment
            - **SAVI**: Soil-adjusted vegetation index
            """)
        
        st.markdown("---")
        st.markdown("### 🆕 New Features")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            #### 📈 Time Series Analysis
            Compare LULC changes between two different years:
            - Track urban expansion
            - Monitor deforestation
            - Analyze agricultural changes
            """)
        
        with col2:
            st.markdown("""
            #### 📥 Export & Download
            - Download statistics as CSV
            - Export maps as GeoTIFF
            - Area calculations in km²
            """)
        
        st.markdown("---")
        st.markdown("### 🛰️ Data Sources")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            #### Sentinel-2
            - Resolution: 10m (RGB, NIR)
            - Revisit time: ~5 days
            - Available from: 2017
            - Best for: Detailed analysis
            """)
        
        with col2:
            st.markdown("""
            #### Landsat 8/9
            - Resolution: 30m
            - Revisit time: ~16 days
            - Available from: 2013
            - Best for: Long-term studies
            """)
    st.markdown("---")
    st.markdown(
        '<div style="text-align: center; color: #666; padding: 1rem;">Made with Streamlit & Google Earth Engine</div>',
        unsafe_allow_html=True,
    )
     st.markdown("""
<div style="text-align: center; font-size: 15px; color: #777; margin-top: -15px;">
    Developed by <strong>Hemant Kumar</strong> • 
    <a href="https://www.linkedin.com/in/hemantkumar2430" target="_blank">LinkedIn</a>
</div>
""", unsafe_allow_html=True)
if __name__ == "__main__":
    main()









