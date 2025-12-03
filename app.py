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

# ================================================================
#  🛰️ Page config + Modern UI Styling (single injection)
# ================================================================
st.set_page_config(
    page_title="India GIS & Remote Sensing Portal",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>

:root {
    --primary: #4C6EF5;
    --primary-dark: #364FC7;
    --bg-light: #F7F9FC;
    --card-bg: #FFFFFFCC;
    --border-light: #E4E7EC;
    --radius: 14px;
    --shadow-soft: 0 6px 22px rgba(20,20,40,0.06);
}

/* Header */
.topbar {
    width: 100%;
    background: linear-gradient(90deg, #4C6EF5 0%, #764ba2 100%);
    padding: 10px 24px;
    border-radius: 12px;
    color: white;
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 18px;
}
.topbar .title {
    font-size: 22px;
    font-weight: 800;
}
.topbar .subtitle {
    font-size: 13px;
    opacity: 0.95;
}

/* Main headers */
.main-header {
    font-size: 2.25rem;
    font-weight: 800;
    color: var(--primary-dark);
    margin: 0;
}
.sub-header {
    font-size: 1rem;
    color: #556;
    margin-top: 6px;
}

/* Cards and layout */
.card {
    background: var(--card-bg);
    border: 1px solid var(--border-light);
    border-radius: var(--radius);
    padding: 18px;
    box-shadow: var(--shadow-soft);
    backdrop-filter: blur(6px);
    margin-bottom: 16px;
}

/* Map container */
.map-container {
    border-radius: 12px;
    overflow: hidden;
    box-shadow: var(--shadow-soft);
    border: 1px solid #dfe6f3;
}

/* Legends */
.legend-card {
    background: white;
    padding: 10px;
    border-radius: 12px;
    border: 1px solid #eee;
    margin-bottom: 12px;
}
.legend-color-box {
    width: 28px;
    height: 28px;
    border-radius: 6px;
    border: 1px solid #ddd;
    display: inline-block;
    margin-right: 10px;
    vertical-align: middle;
}

/* Info boxes */
.info-box {
    background: #eef6ff;
    border-left: 4px solid var(--primary);
    padding: 10px;
    border-radius: 6px;
}

/* Small helpers */
.small-muted {
    color: #718096;
    font-size: 0.9rem;
}

/* Responsive spacing */
@media (max-width: 900px) {
    .main-header { font-size: 1.6rem; }
    .topbar { flex-direction: column; gap: 8px; align-items: flex-start; }
}

</style>
""",
    unsafe_allow_html=True,
)

# ================================================================
#  ⭐⭐⭐ AUTO-INITIALIZE GEE FROM STREAMLIT SECRETS (unchanged) ⭐⭐⭐
# ================================================================
try:
    if "gee_initialized" not in st.session_state:
        st.session_state.gee_initialized = False

    if not st.session_state.gee_initialized:
        if "GEE_JSON" in st.secrets:
            key_data = dict(st.secrets["GEE_JSON"])
            try:
                ok = initialize_gee(key_data)
                st.session_state.gee_initialized = bool(ok)
            except Exception:
                st.session_state.gee_initialized = False
        else:
            st.session_state.gee_initialized = False
except Exception:
    st.session_state.gee_initialized = False

# ================================================================
# Helper / UI utility functions (kept but slightly restyled)
# ================================================================
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
    st.markdown('<div class="legend-card">', unsafe_allow_html=True)
    st.markdown("#### Land Cover Classes")
    for class_id, info in LULC_CLASSES.items():
        st.markdown(
            f'<div style="margin:6px 0;"><span class="legend-color-box" style="background:{info["color"]};"></span> <strong>{info["name"]}</strong></div>',
            unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)

def render_index_legend(index_name):
    info = INDEX_INFO.get(index_name, {})
    st.markdown('<div class="legend-card">', unsafe_allow_html=True)
    st.markdown(f"#### {info.get('name', index_name)}")
    st.markdown(f"*{info.get('description', '')}*")
    palette = info.get("palette", [])
    if palette:
        gradient = ", ".join(palette)
        st.markdown(
            f'<div class="index-gradient" style="background: linear-gradient(to right, {gradient}); margin-top:8px;"></div>',
            unsafe_allow_html=True,
        )
        st.markdown('<div style="display:flex; justify-content:space-between; margin-top:6px;"><small>Low</small><small>High</small></div>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

def render_statistics_with_area(stats, city_name=""):
    if not stats or "classes" not in stats:
        st.warning("Unable to calculate statistics for this area.")
        return

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### Land Cover Statistics")
    st.markdown(f"**Total Area:** <span class='small-muted'>{stats.get('total_area_sqkm', 'N/A')} km²</span>", unsafe_allow_html=True)

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

    # horizontal card rows for each class
    for _, row in df.iterrows():
        st.markdown(
            f"""
            <div style="display:flex; align-items:center; justify-content:space-between; padding:8px 6px; border-bottom:1px solid #f1f3f6">
                <div style="display:flex; align-items:center;">
                    <div style="width:36px; height:36px; border-radius:8px; background:{row['Color']}; margin-right:12px; border:1px solid #e6e6e6;"></div>
                    <div><strong>{row['Class']}</strong><div class="small-muted" style="font-size:0.85rem;">{row['Percentage']:.2f}%</div></div>
                </div>
                <div style="text-align:right;">
                    <div style="font-weight:700;">{row['Area (km²)']:.2f} km²</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)

    # Download CSV
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

    st.markdown('<div class="card">', unsafe_allow_html=True)
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
                st.markdown(f"- **{row['Class']}**: <span style='color:#16a34a; font-weight:700;'>+{change:.2f}%</span> (+{row['Change (km²)']:.2f} km²)", unsafe_allow_html=True)
            else:
                st.markdown(f"- **{row['Class']}**: <span style='color:#ef4444; font-weight:700;'>{change:.2f}%</span> ({row['Change (km²)']:.2f} km²)", unsafe_allow_html=True)

    # CSV export
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
    st.markdown("</div>", unsafe_allow_html=True)

# ================================================================
#  Main application
# ================================================================
def main():
    init_session_state()

    # Topbar
    st.markdown(
        f"""
        <div class="topbar">
            <div>
                <div class="title">🛰️ India GIS & Remote Sensing Portal</div>
                <div class="small-muted">Analyze Land Use, Land Cover, and Vegetation Indices for Indian Cities</div>
            </div>
            <div style="text-align:right;">
                <div class="subtitle">Made with ❤️ by <strong>Hemant Kumar</strong> &nbsp; • &nbsp; <a href="https://www.linkedin.com/in/hemantkumar2430" target="_blank" style="color:white; text-decoration:underline;">LinkedIn</a></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Sidebar (kept but re-ordered visually)
    with st.sidebar:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("## 🔐 Google Earth Engine")
        if st.session_state.gee_initialized:
            st.markdown('<div class="info-box">🟢 <strong>GEE Connected</strong></div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="info-box" style="background:#fff6ea; border-left:4px solid #ff9800;">🔴 <strong>GEE Not Connected</strong><div class="small-muted">Set your GEE service account in secrets.toml</div></div>', unsafe_allow_html=True)

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

        analysis_mode = st.radio("Analysis Mode", ["Single Period", "Time Series Comparison"], help="Compare LULC changes between two different years")

        if analysis_mode == "Single Period":
            selected_year = st.selectbox("Select Year", years[::-1])
            date_range = st.radio("Date Range", ["Full Year", "Custom Range"])
            if date_range == "Full Year":
                start_date = f"{selected_year}-01-01"
                end_date = f"{selected_year}-12-31"
            else:
                col1, col2 = st.columns(2)
                with col1:
                    start = st.date_input("Start Date", value=date(selected_year, 1, 1), min_value=date(2017, 1, 1), max_value=date(current_year, 12, 31))
                with col2:
                    end = st.date_input("End Date", value=date(selected_year, 12, 31), min_value=date(2017, 1, 1), max_value=date(current_year, 12, 31))
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
        satellite = st.radio("Satellite", ["Sentinel-2", "Landsat 8/9"], help="Sentinel-2 has 10m resolution, Landsat has 30m resolution")
        buffer_km = st.slider("Analysis Radius (km)", min_value=5, max_value=50, value=15, help="Area around city center to analyze")

        st.markdown("---")
        st.markdown("## 📊 Analysis Options")
        show_lulc = st.checkbox("Land Use / Land Cover (LULC)", value=True)
        show_indices = st.multiselect("Vegetation/Urban Indices", ["NDVI", "NDWI", "NDBI", "EVI", "SAVI"], default=["NDVI"])
        show_rgb = st.checkbox("True Color (RGB) Image", value=True)
        enable_drawing = st.checkbox("Enable Custom AOI Drawing", value=False, help="Draw custom areas on the map to analyze specific regions")

        st.markdown("---")
        st.markdown('<div style="display:flex; gap:8px;">', unsafe_allow_html=True)
        run_btn = st.button("🚀 Run Analysis", use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

    # MAIN content area
    col_map, col_side = st.columns([3, 1], gap="large")

    with col_map:
        st.markdown('<div class="card map-container">', unsafe_allow_html=True)
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
                fillOpacity=0.08,
                weight=2,
            ).add_to(base_map)

            # Run analysis when user clicks run and GEE initialized
            if run_btn:
                if not st.session_state.gee_initialized:
                    st.warning("⚠️ Initialize GEE first (see sidebar).")
                else:
                    with st.spinner("Fetching satellite data and running analysis..."):
                        try:
                            if enable_drawing and st.session_state.drawn_geometry:
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
                                st.session_state.analysis_complete = False
                            else:
                                st.session_state.current_image = image

                                # RGB
                                if show_rgb:
                                    rgb_params = rgb_params_func(image)
                                    rgb_url = get_tile_url(image, rgb_params)
                                    base_map = add_tile_layer(base_map, rgb_url, f"{satellite} RGB", 0.9)

                                # LULC
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

                                # Indices
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
                                st.success("Analysis complete! Use the layer control on the map to toggle layers.")
                        except Exception as e:
                            st.error(f"Error during analysis: {str(e)}")
                            st.info("Please check your GEE credentials and try again.")
            else:
                # If previously completed analysis, re-add layers from session state if possible
                if st.session_state.analysis_complete and st.session_state.current_image:
                    try:
                        image = st.session_state.current_image
                        if show_rgb:
                            try:
                                rgb_params = get_sentinel_rgb_params(image) if satellite == "Sentinel-2" else get_landsat_rgb_params(image)
                                rgb_url = get_tile_url(image, rgb_params)
                                base_map = add_tile_layer(base_map, rgb_url, f"{satellite} RGB", 0.9)
                            except Exception:
                                pass
                    except Exception:
                        pass

            folium.LayerControl(collapsed=False).add_to(base_map)

            # Render map
            map_data = st_folium(base_map, width="100%", height=700, returned_objects=["all_drawings"])
            if enable_drawing and map_data and map_data.get("all_drawings"):
                st.session_state.drawn_geometry = map_data["all_drawings"]

        else:
            st.markdown(
                """
                <div class="card">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <div>
                            <h3 style="margin:0;">Welcome 👋</h3>
                            <div class="small-muted">Start by selecting a state and city from the sidebar.</div>
                        </div>
                        <div style="text-align:right;">
                            <div class="small-muted">Tip: enable drawing to analyze a custom AOI</div>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown("### 📊 Available Analyses")
            st.markdown("""
            - **LULC (Dynamic World)**: Water, Trees, Grass, Crops, Built-up, Bare, Snow
            - **Indices**: NDVI, NDWI, NDBI, EVI, SAVI
            - **Time Series**: Compare LULC between years
            - **Export**: CSV stats & GeoTIFF download links
            """)
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

    # Right column: results, legends, exports
    with col_side:
        # Stats / Legend card
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("### Results & Exports")
        if st.session_state.analysis_complete:
            if analysis_mode == "Time Series Comparison" and st.session_state.time_series_stats:
                stats1, stats2, year1, year2 = st.session_state.time_series_stats
                st.markdown("<div class='small-muted'>Time series comparison available</div>", unsafe_allow_html=True)
                render_time_series_comparison(stats1, stats2, year1, year2)
            elif show_lulc and st.session_state.lulc_stats:
                render_lulc_legend()
                st.markdown("---")
                render_statistics_with_area(st.session_state.lulc_stats, selected_city or "city")
        else:
            st.markdown('<div class="info-box">Run analysis to see results here</div>', unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        # Index legends
        if st.session_state.analysis_complete:
            for idx in show_indices:
                render_index_legend(idx)

        # Export options
        if st.session_state.analysis_complete and st.session_state.current_image:
            st.markdown('<div class="card">', unsafe_allow_html=True)
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
            st.markdown("</div>", unsafe_allow_html=True)

        # Additional info / data sources
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("### About Data")
        st.markdown("""
        - **Sentinel-2:** 10 m (RGB/NIR), available since 2017 — best for detailed urban/vegetation mapping  
        - **Landsat 8/9:** 30 m, longer time-series — useful for historical trends
        """)
        st.markdown("</div>", unsafe_allow_html=True)

    # Footer
    st.markdown("---")
    st.markdown(
        '<div style="text-align:center; color:#7b8794; padding:8px 0;">Made with Streamlit & Google Earth Engine • © Hemant Kumar</div>',
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
