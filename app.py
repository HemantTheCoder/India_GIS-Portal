import streamlit as st
import folium
from streamlit_folium import st_folium
from folium.plugins import Draw
import ee
import json

service_account_json = os.environ.get("GEE_SERVICE_ACCOUNT_JSON")
if service_account_json:
    from gee_utils import initialize_gee
    initialize_gee(json.loads(service_account_json))
else:
    ee.Initialize()  # fallback
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

# Streamlit page configuration
st.set_page_config(
    page_title="India GIS & Remote Sensing Portal",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ------------------------------------
# CSS Styling
# ------------------------------------
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


# ------------------------------------
# Session State Initialization
# ------------------------------------
def init_session_state():
    defaults = {
        "gee_initialized": False,
        "current_map": None,
        "analysis_complete": False,
        "lulc_stats": None,
        "current_image": None,
        "current_geometry": None,
        "time_series_stats": None,
        "drawn_geometry": None,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


# ------------------------------------
# Map Helpers
# ------------------------------------
def create_base_map(lat, lon, zoom=11, enable_drawing=False):
    m = folium.Map(location=[lat, lon], zoom_start=zoom, tiles="OpenStreetMap")
    if enable_drawing:
        Draw(
            draw_options={
                'polyline': False,
                'rectangle': True,
                'polygon': True,
                'circle': True,
                'marker': False,
                'circlemarker': False,
            },
            edit_options={'edit': False}
        ).add_to(m)
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


# ------------------------------------
# Legend Rendering
# ------------------------------------
def render_lulc_legend():
    st.markdown("### Land Cover Classes")
    for class_id, info in LULC_CLASSES.items():
        col1, col2 = st.columns([1, 4])
        with col1:
            st.markdown(
                f'<div style="background-color: {info["color"]}; '
                f'width: 30px; height: 30px; border-radius: 4px; '
                f'border: 1px solid #ccc;"></div>',
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
            f'<div style="background: linear-gradient(to right, {gradient}); '
            f'height: 30px; border-radius: 4px; margin: 10px 0;"></div>',
            unsafe_allow_html=True,
        )
        col1, col2 = st.columns(2)
        with col1:
            st.write("Low")
        with col2:
            st.write("High")


# ------------------------------------
# LULC Statistics Rendering
# ------------------------------------
def render_statistics_with_area(stats, city_name=""):
    if not stats or "classes" not in stats:
        st.warning("Unable to calculate statistics for this area.")
        return

    st.markdown("### Land Cover Statistics")
    st.markdown(f"**Total Area: {stats.get('total_area_sqkm', 'N/A')} km²**")

    df_data = []
    for name, data in sorted(stats["classes"].items(), key=lambda x: x[1]["percentage"], reverse=True):
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
                f'<div style="background-color: {row["Color"]}; '
                f'width: 24px; height: 24px; border-radius: 4px; '
                f'border: 1px solid #ccc;"></div>',
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

    st.download_button(
        label="📥 Download Statistics (CSV)",
        data=csv_buffer.getvalue(),
        file_name=f"lulc_statistics_{city_name}_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv",
        use_container_width=True,
    )


# ------------------------------------
# Time Series Comparison Rendering
# ------------------------------------
def render_time_series_comparison(stats1, stats2, year1, year2):
    if not stats1 or not stats2:
        st.warning("Unable to compare time series data.")
        return

    st.markdown(f"### LULC Change Analysis: {year1} vs {year2}")

    classes1 = stats1.get("classes", {})
    classes2 = stats2.get("classes", {})
    all_classes = set(classes1.keys()) | set(classes2.keys())

    comparison = []
    for cls in all_classes:
        d1 = classes1.get(cls, {"percentage": 0, "area_sqkm": 0})
        d2 = classes2.get(cls, {"percentage": 0, "area_sqkm": 0})
        pct_diff = d2["percentage"] - d1["percentage"]
        area_diff = d2["area_sqkm"] - d1["area_sqkm"]
        comparison.append({
            "Class": cls,
            f"{year1} (%)": d1["percentage"],
            f"{year2} (%)": d2["percentage"],
            "Change (%)": pct_diff,
            f"{year1} (km²)": d1["area_sqkm"],
            f"{year2} (km²)": d2["area_sqkm"],
            "Change (km²)": area_diff,
        })

    df = pd.DataFrame(comparison).sort_values("Change (%)", key=abs, ascending=False)
    st.dataframe(df, use_container_width=True, hide_index=True)

    st.markdown("#### Key Changes")
    for _, row in df.iterrows():
        if abs(row["Change (%)"]) > 0.5:
            change = row["Change (%)"]
            if change > 0:
                st.markdown(
                    f"- **{row['Class']}**: <span class='change-positive'>+{change:.2f}%</span> "
                    f"(+{row['Change (km²)']:.2f} km²)",
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f"- **{row['Class']}**: <span class='change-negative'>{change:.2f}%</span> "
                    f"({row['Change (km²)']:.2f} km²)",
                    unsafe_allow_html=True,
                )

    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)

    st.download_button(
        label="📥 Download Change Analysis (CSV)",
        data=csv_buffer.getvalue(),
        file_name=f"lulc_change_{year1}_vs_{year2}.csv",
        mime="text/csv",
        use_container_width=True,
    )


# ============================================
# ================ MAIN APP ===================
# ============================================
def main():
    init_session_state()

    st.markdown('<div class="main-header">🛰️ India GIS & Remote Sensing Portal</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Analyze Land Use, Land Cover, and Vegetation Indices for Indian Cities</div>',
                unsafe_allow_html=True)

    # ---------------- SIDEBAR ----------------
    with st.sidebar:

        # GEE Authentication
        st.markdown("## 🔐 GEE Authentication")
        st.markdown("""
        <div class="info-box">
        <strong>Google Earth Engine Setup:</strong><br>
        1. Go to earthengine.google.com<br>
        2. Sign in<br>
        3. Create a Service Account<br>
        4. Paste your JSON key below
        </div>
        """, unsafe_allow_html=True)

        auth_method = st.radio(
            "Authentication Method",
            ["Service Account (JSON Key)", "Default Credentials"]
        )

        if auth_method == "Service Account (JSON Key)":
            service_json = st.text_area(
                "Paste your Service Account JSON Key",
                height=150,
                placeholder='{"type": "service_account", ... }'
            )
            if st.button("🔓 Initialize GEE", use_container_width=True):
                if service_json:
                    try:
                        data = json.loads(service_json)
                        if initialize_gee(data):
                            st.session_state.gee_initialized = True
                            st.success("GEE initialized!")
                            st.rerun()
                    except:
                        st.error("Invalid JSON key format.")
                else:
                    st.warning("Paste your key first.")
        else:
            if st.button("🔓 Initialize with Default Credentials", use_container_width=True):
                if initialize_gee():
                    st.session_state.gee_initialized = True
                    st.success("GEE initialized!")
                    st.rerun()

        if st.session_state.gee_initialized:
            st.markdown('<div class="success-box">✅ Connected to GEE</div>', unsafe_allow_html=True)

        st.markdown("---")

        # Location selection
        st.markdown("## 📍 Location Selection")
        states = get_states()
        selected_state = st.selectbox("Select State", ["Select..."] + states)

        selected_city = None
        city_coords = None

        if selected_state and selected_state != "Select...":
            cities = get_cities(selected_state)
            selected_city = st.selectbox("Select City", ["Select..."] + cities)

            if selected_city and selected_city != "Select...":
                city_coords = get_city_coordinates(selected_state, selected_city)
                if city_coords:
                    st.success(f"{selected_city}, {selected_state}")
                    st.caption(f"Lat: {city_coords['lat']}, Lon: {city_coords['lon']}")

        st.markdown("---")

        # Time selection
        st.markdown("## 📅 Time Period")
        now_year = datetime.now().year
        years = list(range(2017, now_year + 1))

        analysis_mode = st.radio("Mode", ["Single Period", "Time Series Comparison"])

        if analysis_mode == "Single Period":
            selected_year = st.selectbox("Select Year", years[::-1])
            range_type = st.radio("Date Range", ["Full Year", "Custom"])

            if range_type == "Full Year":
                start_date = f"{selected_year}-01-01"
                end_date = f"{selected_year}-12-31"
            else:
                col1, col2 = st.columns(2)
                with col1:
                    s = st.date_input("Start", value=date(selected_year, 1, 1))
                with col2:
                    e = st.date_input("End", value=date(selected_year, 12, 31))
                start_date = s.strftime("%Y-%m-%d")
                end_date = e.strftime("%Y-%m-%d")

            compare_year1 = compare_year2 = None

        else:
            col1, col2 = st.columns(2)
            with col1:
                compare_year1 = st.selectbox("Earlier Year", years[::-1])
            with col2:
                compare_year2 = st.selectbox("Later Year", years[::-1])

            start_date = f"{compare_year2}-01-01"
            end_date = f"{compare_year2}-12-31"
            selected_year = compare_year2

        st.caption(f"Period: {start_date} → {end_date}")

        st.markdown("---")

        # Satellite selection
        st.markdown("## 🛰️ Satellite Source")
        satellite = st.radio("Satellite", ["Sentinel-2", "Landsat 8/9"])

        buffer_km = st.slider("Analysis Radius (km)", 5, 50, 15)

        st.markdown("---")

        # Analysis options
        st.markdown("## 📊 Analysis Options")
        show_lulc = st.checkbox("LULC", value=True)
        show_indices = st.multiselect(
            "Vegetation & Urban Indices",
            ["NDVI", "NDWI", "NDBI", "EVI", "SAVI"],
            default=["NDVI"]
        )
        show_rgb = st.checkbox("True Color RGB", value=True)
        enable_draw = st.checkbox("Enable Custom AOI Drawing")

    # --------------- MAIN MAP AREA ---------------
    if city_coords:
        base_map = create_base_map(city_coords["lat"], city_coords["lon"], enable_drawing=enable_draw)

        # Marker + radius
        folium.Marker(
            [city_coords["lat"], city_coords["lon"]],
            popup=selected_city,
            icon=folium.Icon(color="red")
        ).add_to(base_map)

        folium.Circle(
            [city_coords["lat"], city_coords["lon"]],
            radius=buffer_km * 1000,
            color="#3388ff",
            fill=True,
            fillOpacity=0.1
        ).add_to(base_map)

        # If GEE initialized
        if st.session_state.gee_initialized:

            use_custom_aoi = st.sidebar.checkbox(
                "Use Custom AOI",
                value=False,
                disabled=not st.session_state.drawn_geometry
            )

            if st.sidebar.button("🚀 Run Analysis", use_container_width=True):
                with st.spinner("Running analysis..."):

                    # AOI selection
                    if use_custom_aoi and st.session_state.drawn_geometry:
                        drawn = st.session_state.drawn_geometry[0]
                        geometry = geojson_to_ee_geometry(drawn)
                        if geometry is None:
                            st.warning("Invalid AOI → using city radius.")
                            geometry = get_city_geometry(city_coords["lat"], city_coords["lon"], buffer_km)
                    else:
                        geometry = get_city_geometry(city_coords["lat"], city_coords["lon"], buffer_km)

                    st.session_state.current_geometry = geometry

                    # Image selection
                    if satellite == "Sentinel-2":
                        image = get_sentinel2_image(geometry, start_date, end_date)
                        rgb_func = get_sentinel_rgb_params
                        ndvi = calculate_ndvi_sentinel
                        ndwi = calculate_ndwi_sentinel
                        ndbi = calculate_ndbi_sentinel
                        evi = calculate_evi_sentinel
                        savi = calculate_savi_sentinel
                    else:
                        image = get_landsat_image(geometry, start_date, end_date)
                        rgb_func = get_landsat_rgb_params
                        ndvi = calculate_ndvi_landsat
                        ndwi = calculate_ndwi_landsat
                        ndbi = calculate_ndbi_landsat
                        evi = calculate_evi_landsat
                        savi = calculate_savi_landsat

                    if image is None:
                        st.error(f"No cloud-free {satellite} images found for this period.")
                    else:
                        st.session_state.current_image = image

                        # RGB
                        if show_rgb:
                            rgb_params = rgb_func(image)
                            rgb_url = get_tile_url(image, rgb_params)
                            base_map = add_tile_layer(base_map, rgb_url, f"{satellite} RGB", 0.9)

                        # LULC
                        if show_lulc:
                            lulc_img = get_dynamic_world_lulc(geometry, start_date, end_date)
                            if lulc_img:
                                params = get_lulc_vis_params()
                                lulc_url = get_tile_url(lulc_img, params)
                                base_map = add_tile_layer(base_map, lulc_url, "LULC", 0.8)
                                st.session_state.lulc_stats = calculate_lulc_statistics_with_area(lulc_img, geometry)

                                if analysis_mode == "Time Series Comparison":
                                    stats1, stats2, _ = get_lulc_change_analysis(geometry, compare_year1, compare_year2)
                                    st.session_state.time_series_stats = (stats1, stats2, compare_year1, compare_year2)

                        # Indices
                        index_funcs = {
                            "NDVI": ndvi,
                            "NDWI": ndwi,
                            "NDBI": ndbi,
                            "EVI": evi,
                            "SAVI": savi,
                        }

                        for idx in show_indices:
                            idx_img = index_funcs[idx](image)
                            idx_params = get_index_vis_params(idx)
                            idx_url = get_tile_url(idx_img, idx_params)
                            base_map = add_tile_layer(base_map, idx_url, idx, 0.8)

                        st.session_state.analysis_complete = True
                        st.success("Analysis complete!")

        else:
            st.sidebar.warning("⚠️ Initialize GEE first")

        folium.LayerControl(collapsed=False).add_to(base_map)

        # -------- Map & Right Panel layout --------
        col1, col2 = st.columns([3, 1])

        with col1:
            st.markdown(f"### 🗺️ {selected_city}, {selected_state}")
            map_result = st_folium(base_map, height=600, returned_objects=["all_drawings"])

            if enable_draw and map_result and map_result.get("all_drawings"):
                st.info(f"📐 Custom shapes drawn: {len(map_result['all_drawings'])}")
                st.session_state.drawn_geometry = map_result["all_drawings"]

        with col2:
            if st.session_state.analysis_complete:

                if analysis_mode == "Time Series Comparison" and st.session_state.time_series_stats:
                    stats1, stats2, y1, y2 = st.session_state.time_series_stats
                    render_time_series_comparison(stats1, stats2, y1, y2)

                elif show_lulc and st.session_state.lulc_stats:
                    render_lulc_legend()
                    st.markdown("---")
                    render_statistics_with_area(st.session_state.lulc_stats, selected_city)

                # Index legends
                for idx in show_indices:
                    st.markdown("---")
                    render_index_legend(idx)

                # Export
                st.markdown("---")
                st.markdown("### 📥 Export Options")

                scale = 10 if satellite == "Sentinel-2" else 30

                if st.button("Generate GeoTIFF Download Link", use_container_width=True):
                    if st.session_state.current_geometry:
                        with st.spinner("Generating…"):
                            url, err = get_safe_download_url(
                                st.session_state.current_image,
                                st.session_state.current_geometry,
                                scale=scale,
                            )
                            if url:
                                st.success("Download Ready")
                                st.markdown(f"[📥 Download GeoTIFF]({url})")
                                st.caption(f"Resolution: {scale} m")
                            else:
                                st.warning(err)

    # ------- If no city selected --------
    else:
        st.markdown("""
        <div class="info-box">
        <h3>🚀 Getting Started</h3>
        <ol>
            <li>Initialize Earth Engine</li>
            <li>Select a State and City</li>
            <li>Choose the Year / Date Range</li>
            <li>Select Satellite and Indices</li>
            <li>Run Analysis</li>
        </ol>
        </div>
        """, unsafe_allow_html=True)

        # Descriptive sidebar content omitted for brevity


if __name__ == "__main__":
    main()

