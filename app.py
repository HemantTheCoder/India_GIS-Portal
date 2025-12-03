import streamlit as st
import folium
from streamlit_folium import st_folium
from folium.plugins import Draw
import ee
import json
from datetime import datetime, date, timedelta
import pandas as pd
import numpy as np
import io
import matplotlib.pyplot as plt

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

# -------------------------
# page config + styles
# -------------------------
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
        margin-bottom: 0rem;
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
    .map-container {
        border-radius: 8px;
        overflow: hidden;
        border: 1px solid #e6eef8;
        box-shadow: 0 4px 14px rgba(20,30,60,0.06);
    }
</style>
""", unsafe_allow_html=True)

# -------------------------
# init GEE from secrets (unchanged logic, safe)
# -------------------------
if "gee_initialized" not in st.session_state:
    st.session_state.gee_initialized = False

try:
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

# -------------------------
# Navigation state
# -------------------------
if "page" not in st.session_state:
    st.session_state.page = "LULC & Vegetation Analysis"

# -------------------------
# session state keys for analysis
# -------------------------
def init_session_state():
    keys_defaults = {
        "gee_initialized": st.session_state.get("gee_initialized", False),
        "current_map": st.session_state.get("current_map", None),
        "analysis_complete": st.session_state.get("analysis_complete", False),
        "lulc_stats": st.session_state.get("lulc_stats", None),
        "current_image": st.session_state.get("current_image", None),
        "current_geometry": st.session_state.get("current_geometry", None),
        "time_series_stats": st.session_state.get("time_series_stats", None),
        "drawn_geometry": st.session_state.get("drawn_geometry", None),
    }
    for k, v in keys_defaults.items():
        st.session_state[k] = v

# -------------------------
# Basic helpers (existing ones)
# -------------------------
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

# -------------------------
# Sentinel-5P AQI helpers
# -------------------------
# Map pollutant names to Earth Engine collection + band names (OFFL L3)
S5P_DATASETS = {
    "NO2": {"collection": "COPERNICUS/S5P/OFFL/L3_NO2", "band": "tropospheric_NO2_column_number_density"},
    "SO2": {"collection": "COPERNICUS/S5P/OFFL/L3_SO2", "band": "SO2_column_number_density"},
    "CO": {"collection": "COPERNICUS/S5P/OFFL/L3_CO", "band": "CO_column_number_density"},
    "O3": {"collection": "COPERNICUS/S5P/OFFL/L3_O3", "band": "O3_column_number_density"},
    "UVAI": {"collection": "COPERNICUS/S5P/OFFL/L3_AER_AI", "band": "absorbing_aerosol_index"},
    "CH4": {"collection": "COPERNICUS/S5P/OFFL/L3_CH4", "band": "CH4_column_volume_mixing_ratio_dry_air"},
}

def load_sentinel5p_image(pollutant, date_value):
    """Return a single S5P image for a date (or None)."""
    if pollutant not in S5P_DATASETS:
        return None
    ds = S5P_DATASETS[pollutant]
    date_str = date_value.strftime("%Y-%m-%d")
    # filter date to 24h window: start inclusive, end exclusive
    start = ee.Date(date_str)
    end = start.advance(1, 'day')
    try:
        coll = ee.ImageCollection(ds["collection"]).filterDate(start, end).select(ds["band"])
        img = coll.mean()  # using mean across the day to reduce missing pixels
        return img
    except Exception:
        return None

def get_s5p_vis(pollutant):
    # default vis; we will adapt min/max per pollutant later
    palettes = {
        "NO2": {"min": 0, "max": 0.0002, "palette": ["black","blue","purple","cyan","green","yellow","red"]},
        "SO2": {"min": 0, "max": 0.0003, "palette": ["black","navy","purple","orange","red"]},
        "CO": {"min": 0, "max": 0.05, "palette": ["black","blue","green","yellow","red"]},
        "O3": {"min": 0, "max": 0.0003, "palette": ["black","blue","green","yellow","red"]},
        "UVAI": {"min": -2, "max": 4, "palette": ["white","blue","green","yellow","red"]},
        "CH4": {"min": 1800, "max": 1900, "palette": ["black","blue","green","yellow","red"]},
    }
    return palettes.get(pollutant, {"min": 0, "max": 1, "palette": ["black","blue","green","yellow","red"]})

def compute_region_stats(image, geometry, scale=7000):
    """Compute basic stats (mean, median, std, max) for image within geometry.
       scale large (meters) because S5P is coarse (approx 7x7 km typical)."""
    try:
        reducer = ee.Reducer.mean().combine(ee.Reducer.median(), "", True)\
                                  .combine(ee.Reducer.stdDev(), "", True).combine(ee.Reducer.max(), "", True)
        stats = image.reduceRegion(reducer=reducer, geometry=geometry, scale=scale, maxPixels=1e13)
        # convert to python dict (may contain ee.Number)
        stats_py = {}
        for k, v in stats.getInfo().items():
            stats_py[k] = v
        return stats_py
    except Exception as e:
        return {}

def detect_hotspots(image, geometry, k=1.5, scale=7000):
    """Detect hotspots: pixels > mean + k*std. Return hotspot fraction and an image mask."""
    try:
        stats = compute_region_stats(image, geometry, scale=scale)
        # band name extraction (first key)
        if not stats:
            return {"hotspot_fraction": None, "threshold": None, "hotspot_mask": None}
        band = list(stats.keys())[0]
        mean = stats[band + "_mean"] if (band + "_mean") in stats else stats[band]
        std = stats[band + "_stdDev"] if (band + "_stdDev") in stats else 0
        threshold = mean + k * std
        # create hotspot mask
        hotspot_mask = image.gt(threshold)
        # fraction of pixels in AOI that are hotspots
        # Compute pixel counts: sum(mask) / count(non-null)
        hotspot_count = hotspot_mask.reduceRegion(reducer=ee.Reducer.sum(), geometry=geometry, scale=scale, maxPixels=1e13)
        valid_count = image.reduceRegion(reducer=ee.Reducer.count(), geometry=geometry, scale=scale, maxPixels=1e13)
        try:
            hc = list(hotspot_count.getInfo().values())[0]
            vc = list(valid_count.getInfo().values())[0]
            fraction = (hc / vc) if vc and vc != 0 else None
        except Exception:
            fraction = None
        return {"hotspot_fraction": fraction, "threshold": threshold, "hotspot_mask": hotspot_mask}
    except Exception:
        return {"hotspot_fraction": None, "threshold": None, "hotspot_mask": None}

def compute_baseline_mean(pollutant, geometry, years=1, reference_window_days=30, scale=7000):
    """Compute baseline mean for a pollutant using the same day-of-year averaged over `years` back.
       For simplicity use the mean of the previous `reference_window_days` ending at today minus offset."""
    try:
        ds = S5P_DATASETS[pollutant]
        coll = ee.ImageCollection(ds["collection"]).select(ds["band"])
        # baseline: last `reference_window_days` before today-year_offset (e.g., last 30 days)
        end = ee.Date(datetime.utcnow().strftime("%Y-%m-%d"))
        start = end.advance(-reference_window_days, 'day')
        baseline = coll.filterDate(start, end).mean()
        # reduce over geometry
        stats = compute_region_stats(baseline, geometry, scale=scale)
        return baseline, stats
    except Exception:
        return None, {}

def anomaly_image(image, baseline):
    """Return anomaly image: image - baseline (bandwise)."""
    try:
        return image.subtract(baseline)
    except Exception:
        return None

def s5p_timeseries(pollutant, geometry, start_date, end_date, scale=7000):
    """Return pandas DataFrame with date vs mean pollutant in geometry."""
    try:
        ds = S5P_DATASETS[pollutant]
        coll = ee.ImageCollection(ds["collection"]).select(ds["band"]).filterDate(start_date, end_date)
        # map over collection: compute mean over geometry for each image
        def reducer_per_image(img):
            date = img.date().format('YYYY-MM-dd')
            stat = img.reduceRegion(ee.Reducer.mean(), geometry, scale=scale, maxPixels=1e13)
            val = ee.Number(stat.get(ds["band"]))
            return ee.Feature(None, {'date': date, 'value': val})
        feats = coll.map(lambda i: ee.Feature(None, {'date': i.date().format('YYYY-MM-dd'), 'value': i.reduceRegion(ee.Reducer.mean(), geometry, scale=scale).get(ds["band"])}))
        # convert to list
        fc = feats.filter(ee.Filter.notNull(['value']))
        data = []
        try:
            features = fc.getInfo().get('features', [])
            for f in features:
                props = f.get('properties', {})
                d = props.get('date')
                v = props.get('value')
                if v is not None:
                    data.append({'date': d, 'value': v})
            if not data:
                return pd.DataFrame(columns=['date','value'])
            df = pd.DataFrame(data)
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date')
            return df
        except Exception:
            return pd.DataFrame(columns=['date','value'])
    except Exception:
        return pd.DataFrame(columns=['date','value'])

# -------------------------
# LULC page: wrap your existing logic inside a function
# -------------------------
def render_lulc_page():
    init_session_state()
    st.markdown('<div class="main-header">🛰️ India GIS & Remote Sensing Portal</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Analyze Land Use, Land Cover, and Vegetation Indices for Indian Cities</div>', unsafe_allow_html=True)
    st.markdown(
        """
        <div style="text-align: center; font-size: 15px; color: #555; padding: 0rem 0; margin-top: -50px;">
            <hr style="border: none; border-top: 1px solid #ddd; margin-bottom: 0px;">
            Made with ❤️ by <strong>Hemant Kumar</strong> • 
            <a href="https://www.linkedin.com/in/hemantkumar2430" target="_blank">LinkedIn</a>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Sidebar UI for LULC (we'll expose the nav selection outside; assume the shared sidebar set the page)
    # We'll render most controls in the main area to avoid duplication in both pages.
    with st.sidebar:
        st.markdown("## 🔐 Google Earth Engine")
        if st.session_state.gee_initialized:
            st.markdown('<div class="success-box">🟢 GEE Connected</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="warning-box">🔴 GEE Not Connected<br>Check secrets.toml</div>', unsafe_allow_html=True)

    # Main control panel (not sidebar) to avoid duplicating nav across pages
    st.markdown("### ⚙️ LULC Analysis Controls")
    colA, colB = st.columns(2)
    with colA:
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
    with colB:
        current_year = datetime.now().year
        years = list(range(2017, current_year + 1))
        analysis_mode = st.radio("Analysis Mode", ["Single Period", "Time Series Comparison"])
        if analysis_mode == "Single Period":
            selected_year = st.selectbox("Select Year", years[::-1])
            date_range = st.radio("Date Range", ["Full Year", "Custom Range"])
            if date_range == "Full Year":
                start_date = f"{selected_year}-01-01"
                end_date = f"{selected_year}-12-31"
            else:
                start = st.date_input("Start Date", value=date(selected_year, 1, 1), min_value=date(2017, 1, 1), max_value=date(current_year, 12, 31))
                end = st.date_input("End Date", value=date(selected_year, 12, 31), min_value=date(2017, 1, 1), max_value=date(current_year, 12, 31))
                start_date = start.strftime("%Y-%m-%d")
                end_date = end.strftime("%Y-%m-%d")
            compare_year1, compare_year2 = None, None
        else:
            compare_year1 = st.selectbox("Year 1 (Earlier)", years[::-1], index=len(years)-1)
            compare_year2 = st.selectbox("Year 2 (Later)", years[::-1], index=0)
            start_date = f"{compare_year2}-01-01"
            end_date = f"{compare_year2}-12-31"
            selected_year = compare_year2

    st.markdown("---")
    st.markdown("### 🛰️ Data Source & Options")
    sat_col1, sat_col2 = st.columns(2)
    with sat_col1:
        satellite = st.radio("Satellite", ["Sentinel-2", "Landsat 8/9"], help="Sentinel-2 has 10m resolution, Landsat has 30m resolution")
        buffer_km = st.slider("Analysis Radius (km)", min_value=5, max_value=50, value=15)
    with sat_col2:
        show_lulc = st.checkbox("Land Use / Land Cover (LULC)", value=True)
        show_indices = st.multiselect("Vegetation/Urban Indices", ["NDVI", "NDWI", "NDBI", "EVI", "SAVI"], default=["NDVI"])
        show_rgb = st.checkbox("True Color (RGB) Image", value=True)
        enable_drawing = st.checkbox("Enable Custom AOI Drawing", value=False)

    run_lulc = st.button("🚀 Run LULC Analysis")
    # Map and result area
    if city_coords:
        base_map = create_base_map(city_coords["lat"], city_coords["lon"], enable_drawing=enable_drawing)
        folium.Marker([city_coords["lat"], city_coords["lon"]], popup=f"{selected_city}, {selected_state}", tooltip=selected_city, icon=folium.Icon(color="red", icon="info-sign")).add_to(base_map)
        folium.Circle([city_coords["lat"], city_coords["lon"]], radius=buffer_km*1000, color="#3388ff", fill=True, fillOpacity=0.1, weight=2).add_to(base_map)

        if run_lulc:
            if not st.session_state.gee_initialized:
                st.warning("⚠️ Initialize GEE first")
            else:
                with st.spinner("Running LULC analysis..."):
                    try:
                        geometry = get_city_geometry(city_coords["lat"], city_coords["lon"], buffer_km) if not (enable_drawing and st.session_state.drawn_geometry) else geojson_to_ee_geometry(st.session_state.drawn_geometry[0])
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
                            st.error("No cloud-free images found for the selected period.")
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
                                    st.warning("LULC not available for the period.")
                            # Indices
                            index_funcs = {"NDVI": ndvi_func, "NDWI": ndwi_func, "NDBI": ndbi_func, "EVI": evi_func, "SAVI": savi_func}
                            for idx in show_indices:
                                if idx in index_funcs:
                                    index_image = index_funcs[idx](image)
                                    index_params = get_index_vis_params(idx)
                                    index_url = get_tile_url(index_image, index_params)
                                    base_map = add_tile_layer(base_map, index_url, idx, 0.8)
                            st.session_state.analysis_complete = True
                            st.success("LULC analysis complete!")
                    except Exception as e:
                        st.error(f"Analysis error: {str(e)}")
        folium.LayerControl(collapsed=False).add_to(base_map)
        st_folium(base_map, width="100%", height=650, returned_objects=["all_drawings"])
    else:
        st.info("Select a city to run LULC analysis.")

    # show results on right column style within page
    if st.session_state.analysis_complete and st.session_state.lulc_stats:
        st.markdown("---")
        render_lulc_legend()
        render_statistics_with_area(st.session_state.lulc_stats, selected_city or "city")
    if st.session_state.analysis_complete:
        for idx in show_indices:
            render_index_legend(idx)

# -------------------------
# AQI page: full features
# -------------------------
def render_aqi_page():
    init_session_state()
    st.markdown('<div class="main-header">🌫️ Air Quality (Sentinel-5P) Analysis</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Explore trace gases (NO₂, SO₂, CO, O₃), UV Aerosol Index and CH₄ using TROPOMI / Sentinel-5P</div>', unsafe_allow_html=True)
    st.markdown(
        """
        <div style="text-align:center; font-size:13px; color:#555; margin-bottom:8px;">
            Tools: single-day analysis, timeseries, hotspot detection, plume/anomaly mapping, multi-pollutant comparison.
        </div>
        """, unsafe_allow_html=True
    )

    # Controls
    st.markdown("### 🔎 Controls")
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        pollutant = st.selectbox("Pollutant", ["NO2", "SO2", "CO", "O3", "UVAI", "CH4"])
    with col2:
        mode = st.radio("Mode", ["Single Date", "Time Series", "Multi-Pollutant Comparison"])
    with col3:
        buffer_km = st.number_input("AOI radius (km)", min_value=5, max_value=200, value=25)

    # shared location selectors (so user doesn't reselect across pages)
    st.markdown("### 📍 Location")
    s1, s2 = st.columns([2, 3])
    with s1:
        states = get_states()
        selected_state = st.selectbox("State", ["Select a state..."] + states, key="aqi_state")
    with s2:
        selected_city = None
        city_coords = None
        if selected_state and selected_state != "Select a state...":
            cities = get_cities(selected_state)
            selected_city = st.selectbox("City", ["Select a city..."] + cities, key="aqi_city")
            if selected_city and selected_city != "Select a city...":
                city_coords = get_city_coordinates(selected_state, selected_city)
                if city_coords:
                    st.success(f"Selected: {selected_city}, {selected_state}")
                    st.caption(f"Lat: {city_coords['lat']:.4f}, Lon: {city_coords['lon']:.4f}")

    if not city_coords:
        st.info("Choose a city to run AQI analysis.")
        return

    # Build AOI geometry using get_city_geometry (same as LULC)
    geometry = get_city_geometry(city_coords["lat"], city_coords["lon"], buffer_km)
    st.session_state.current_geometry = geometry

    # Map top
    m = create_base_map(city_coords["lat"], city_coords["lon"], zoom=9, enable_drawing=False)
    folium.Marker([city_coords["lat"], city_coords["lon"]], popup=f"{selected_city}, {selected_state}").add_to(m)
    folium.Circle([city_coords["lat"], city_coords["lon"]], radius=buffer_km*1000, color="#ff7800", fill=True, fillOpacity=0.08).add_to(m)

    if mode == "Single Date":
        date_sel = st.date_input("Select Date", value=date.today() - timedelta(days=1))
        run = st.button("Run AQI Analysis")
        if run:
            if not st.session_state.gee_initialized:
                st.warning("Initialize GEE first.")
            else:
                with st.spinner("Loading Sentinel-5P data..."):
                    img = load_sentinel5p_image(pollutant, date_sel)
                    if img is None:
                        st.warning("No S5P data for this date or pollutant.")
                    else:
                        # visualization and layer
                        vis = get_s5p_vis(pollutant)
                        url = get_tile_url(img, vis)
                        add_tile_layer(m, url, f"{pollutant} ({date_sel})", 0.85)
                        folium.LayerControl(collapsed=False).add_to(m)
                        st_folium(m, width="100%", height=600)

                        # compute stats
                        stats = compute_region_stats(img, geometry, scale=7000)
                        st.markdown("### 📈 AQI Statistics (AOI)")
                        if stats:
                            # adapt key extraction for band name
                            band_key = list(stats.keys())[0]
                            mean = stats.get(band_key + "_mean", stats.get(band_key, None))
                            median = stats.get(band_key + "_median", None)
                            std = stats.get(band_key + "_stdDev", None)
                            maximum = stats.get(band_key + "_max", None)
                            st.write(f"- **Mean:** {mean}")
                            st.write(f"- **Median:** {median}")
                            st.write(f"- **Std dev:** {std}")
                            st.write(f"- **Max:** {maximum}")
                        else:
                            st.write("No stats available.")

                        # hotspot detection
                        hotspots = detect_hotspots(img, geometry, k=1.5, scale=7000)
                        if hotspots and hotspots["hotspot_fraction"] is not None:
                            st.write(f"🔴 **Hotspot fraction:** {hotspots['hotspot_fraction']*100:.2f}% (pixels > mean + 1.5σ)")
                            # add hotspot mask to map
                            try:
                                mask_url = get_tile_url(hotspots["hotspot_mask"].selfMask(), {"min":0,"max":1,"palette":["white","red"]})
                                add_tile_layer(m, mask_url, f"{pollutant} hotspots", 0.6)
                                st_folium(m, width="100%", height=400)
                            except Exception:
                                pass

                        # anomaly (difference from recent baseline)
                        baseline_img, baseline_stats = compute_baseline_mean(pollutant, geometry, reference_window_days=30, scale=7000)
                        if baseline_img:
                            anomaly = anomaly_image(img, baseline_img)
                            if anomaly:
                                # visualize anomalies (positive = increase)
                                anom_vis = {"min": -0.0001, "max": 0.0001, "palette": ["blue","white","red"]}
                                try:
                                    anom_url = get_tile_url(anomaly, anom_vis)
                                    add_tile_layer(m, anom_url, f"{pollutant} anomaly", 0.8)
                                    st.markdown("### 🔍 Anomaly (current - baseline)")
                                    st_folium(m, width="100%", height=300)
                                except Exception:
                                    pass

    elif mode == "Time Series":
        st.markdown("### 📅 Time Series Settings")
        colA, colB = st.columns(2)
        with colA:
            start = st.date_input("Start date", value=date.today() - timedelta(days=30))
        with colB:
            end = st.date_input("End date", value=date.today() - timedelta(days=1))
        run_ts = st.button("Run Time Series")
        if run_ts:
            if not st.session_state.gee_initialized:
                st.warning("Initialize GEE first.")
            else:
                with st.spinner("Computing time series..."):
                    df = s5p_timeseries(pollutant, geometry, start.isoformat(), (end + timedelta(days=1)).isoformat(), scale=7000)
                    if df.empty:
                        st.warning("No time series values found for this AOI/date range.")
                    else:
                        st.markdown("### 📈 Timeseries (Mean over AOI)")
                        st.line_chart(df.set_index('date')['value'])
                        # basic stats
                        st.markdown("### Summary")
                        st.write(df['value'].describe())
                        # export CSV
                        csv_buf = io.StringIO()
                        df.to_csv(csv_buf, index=False)
                        st.download_button("📥 Download time series CSV", csv_buf.getvalue(), file_name=f"{pollutant}_timeseries_{start}_{end}.csv", mime="text/csv")
                        # show last map
                        # add last available image as layer
                        last_date = df['date'].max()
                        last_img = load_sentinel5p_image(pollutant, last_date.to_pydatetime().date())
                        if last_img:
                            vis = get_s5p_vis(pollutant)
                            url = get_tile_url(last_img, vis)
                            add_tile_layer(m, url, f"{pollutant} latest", 0.85)
                            folium.LayerControl(collapsed=False).add_to(m)
                            st_folium(m, width="100%", height=500)

    elif mode == "Multi-Pollutant Comparison":
        st.markdown("### 🔁 Multi-Pollutant Comparison")
        poll_list = st.multiselect("Select pollutants to compare", ["NO2", "SO2", "CO", "O3", "UVAI", "CH4"], default=["NO2", "CO"])
        colA, colB = st.columns(2)
        with colA:
            start = st.date_input("Start date", value=date.today() - timedelta(days=14), key="mp_start")
        with colB:
            end = st.date_input("End date", value=date.today() - timedelta(days=1), key="mp_end")
        run_cmp = st.button("Run Multi-Pollutant Comparison")
        if run_cmp:
            if not st.session_state.gee_initialized:
                st.warning("Initialize GEE first.")
            else:
                with st.spinner("Computing comparison..."):
                    # compute timeseries for each pollutant
                    series = {}
                    for p in poll_list:
                        df = s5p_timeseries(p, geometry, start.isoformat(), (end + timedelta(days=1)).isoformat(), scale=7000)
                        if not df.empty:
                            series[p] = df.set_index('date')['value']
                    if not series:
                        st.warning("No data found for selected pollutants in this AOI/date range.")
                    else:
                        # merge into one DataFrame
                        merged = pd.concat(series, axis=1)
                        st.markdown("### Comparison Chart")
                        st.line_chart(merged.fillna(method='ffill'))
                        st.markdown("### Data")
                        st.dataframe(merged.tail(20))
                        # download
                        csv_buf = io.StringIO()
                        merged.reset_index().to_csv(csv_buf, index=False)
                        st.download_button("📥 Download comparison CSV", csv_buf.getvalue(), file_name=f"aqi_multi_{start}_{end}.csv", mime="text/csv")

    # final: show small legend and data source info
    st.markdown("---")
    st.markdown("### Data & Notes")
    st.markdown("""
    - Sentinel-5P (TROPOMI) L3 offline products used (COPERNICUS/S5P/OFFL/*).  
    - S5P pixel scale is coarse (~7x7 km at nadir) — AOI stats use scale=7000 m.  
    - Hotspots are computed as pixels > mean + 1.5 * std (configurable in code).  
    - Plume/anomaly is computed as deviation from a recent baseline (past 30 days mean).
    """)

# -------------------------
# Main app wrapper with navigation
# -------------------------
def main():
    init_session_state()

    # Sidebar navigation at top
    with st.sidebar:
        st.markdown("## 🧭 Navigation")
        nav = st.radio("Go to:", ["LULC & Vegetation Analysis", "AQI Analysis (Sentinel-5P)"], index=0)
        st.session_state.page = nav
        st.markdown("---")
        # Show GEE status as well
        if st.session_state.gee_initialized:
            st.markdown('<div class="success-box">🟢 GEE Connected</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="warning-box">🔴 GEE Not Connected — set secrets.toml</div>', unsafe_allow_html=True)
        st.markdown("---")
        st.markdown("Made with ❤️ by Hemant Kumar")

    # Render selected page
    if st.session_state.page == "LULC & Vegetation Analysis":
        render_lulc_page()
    elif st.session_state.page == "AQI Analysis (Sentinel-5P)":
        render_aqi_page()
    else:
        st.info("Choose a page from the sidebar")

if __name__ == "__main__":
    main()
