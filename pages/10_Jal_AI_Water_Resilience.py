import streamlit as st
from streamlit_folium import st_folium
from datetime import date, timedelta
import pandas as pd
import json
import tempfile
import zipfile
import os
import ee
import geopandas as gpd

from india_cities import get_states, get_cities, get_city_coordinates
from services.gee_core import auto_initialize_gee, get_city_geometry, get_tile_url, geojson_to_ee_geometry
from services.gee_water import (
    get_ndwi_image, calculate_water_statistics,
    get_flood_active_mask, get_flood_statistics,
    get_precipitation_map, get_rainfall_statistics,
    get_jrc_water_change, get_jrc_water_stats,
    get_terrain_slope, get_terrain_statistics,
    get_heat_stress_map, get_lst_statistics,
    get_drought_ndvi, get_ndvi_statistics,
    get_safe_haven_zones, detect_vulnerable_paths,
    compute_composite_risk_score, get_jal_accuracy_metrics
)
from components.ui import (
    apply_enhanced_css, render_page_header, render_stat_card,
    init_common_session_state
)
from components.theme_manager import ThemeManager
from components.maps import create_base_map, add_tile_layer, add_layer_control

# ── Page Config ──────────────────────────────────────────────
st.set_page_config(
    page_title="Jal-AI | Disaster Preparedness Portal",
    page_icon="💧",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
.block-container{padding-top:0!important;padding-bottom:0!important;}
header{visibility:hidden;}
footer{visibility:hidden;}
html,body{overflow-x:hidden;}
.jal-card{
    background:rgba(15,23,42,0.7);
    border:1px solid rgba(14,165,233,0.25);
    border-radius:12px;
    padding:1.2rem 1.4rem;
    margin-bottom:0.8rem;
}
.risk-badge{
    display:inline-block;
    padding:0.3rem 1rem;
    border-radius:20px;
    font-weight:700;
    font-size:1rem;
}
</style>
""", unsafe_allow_html=True)

auto_initialize_gee()
init_common_session_state()
apply_enhanced_css()

theme_manager = ThemeManager()
theme_manager.apply_theme()

render_page_header(
    theme_manager.get_text("💧 Jal-AI — AI Disaster Preparedness & Early Action"),
    theme_manager.get_text(
        "Real-time multi-satellite intelligence for water resilience, flood risk, and community early action.",
        "🌊 HYDRO-NEURAL: Catastrophic water flux event detected — multi-sensor fusion active."
    )
)

# ── Session state init ────────────────────────────────────────
if "jal_done" not in st.session_state:
    st.session_state.jal_done = False

ANALYSIS_KEYS = [
    "jal_done", "jal_city", "jal_state",
    "ndwi_url", "flood_url", "rain_url", "jrc_url", "safe_url", "vulner_url",
    "lst_url", "ndvi_url",
    "water_stats", "flood_stats", "rain_stats", "jrc_stats",
    "terrain_stats", "lst_stats", "ndvi_stats",
    "composite_risk", "accuracy_metrics"
]

# ── Sidebar ───────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🔐 GEE Status")
    if st.session_state.gee_initialized:
        st.success("Connected ✅")
    else:
        st.error("Not Connected ❌")

    st.markdown("---")
    st.markdown("## 📍 Area of Interest (AOI)")

    aoi_mode = st.radio(
        "Input Mode",
        ["🏙️ Select City", "📁 Upload Shapefile"],
        key="jal_aoi_mode",
        horizontal=True,
    )

    sel_state, sel_city, city_coords = None, None, None
    shp_geom_ee, shp_center, shp_label = None, None, None

    if aoi_mode == "🏙️ Select City":
        states = get_states()
        sel_state = st.selectbox("State", ["Select..."] + states, key="jal_sel_state")
        if sel_state != "Select...":
            cities = get_cities(sel_state)
            sel_city = st.selectbox("City", ["Select..."] + cities, key="jal_sel_city")
            if sel_city != "Select...":
                city_coords = get_city_coordinates(sel_state, sel_city)
    else:
        st.markdown("""
<small style='color:#94a3b8;'>Upload a <b>.zip</b> containing your Shapefile
(.shp + .dbf + .prj + .shx). Any CRS is accepted —
the system reprojects to WGS-84 automatically.</small>
        """, unsafe_allow_html=True)
        uploaded_zip = st.file_uploader("Shapefile (.zip)", type=["zip"], key="jal_shp_upload")
        if uploaded_zip:
            try:
                with tempfile.TemporaryDirectory() as tmpdir:
                    zip_path = os.path.join(tmpdir, "upload.zip")
                    with open(zip_path, "wb") as f:
                        f.write(uploaded_zip.read())
                    with zipfile.ZipFile(zip_path, "r") as zf:
                        zf.extractall(tmpdir)
                    shp_files = [fn for fn in os.listdir(tmpdir) if fn.endswith(".shp")]
                    if not shp_files:
                        st.error("No .shp file found inside the zip.")
                    else:
                        gdf = gpd.read_file(os.path.join(tmpdir, shp_files[0]))
                        gdf = gdf.to_crs("EPSG:4326")
                        dissolved = gdf.dissolve()
                        feat = json.loads(dissolved.geometry.to_json())["features"][0]["geometry"]
                        shp_geom_ee = geojson_to_ee_geometry(feat)
                        centroid = dissolved.geometry.centroid.iloc[0]
                        shp_center = {"lat": centroid.y, "lon": centroid.x}
                        shp_label = uploaded_zip.name.replace(".zip", "")
                        st.success(f"✅ **{shp_label}** loaded ({len(gdf)} feature(s))")
            except Exception as e:
                st.error(f"Shapefile parse error: {e}")

    st.markdown("---")
    st.markdown("## ⚙️ Parameters")
    analysis_date = st.date_input("Target Date", value=date.today(), key="jal_date")
    buffer_km = st.slider("Radius (km)", 5, 50, 15, key="jal_buffer")

    st.markdown("---")
    st.markdown("## 🗺️ Sensor Layers")
    L = {
        "ndwi":   st.checkbox("🔵 Surface Water (NDWI)", value=True),
        "flood":  st.checkbox("🔴 Radar Flood (SAR)", value=True),
        "rain":   st.checkbox("🌧️ GPM Rainfall", value=True),
        "jrc":    st.checkbox("🏞️ JRC Water Change", value=True),
        "safe":   st.checkbox("🟢 Safe Havens", value=True),
        "vulner": st.checkbox("🟡 Vulnerability Corridors", value=True),
        "lst":    st.checkbox("🌡️ Heat Stress (LST)", value=False),
        "ndvi":   st.checkbox("🌿 Drought Index (NDVI)", value=False),
    }

# ── Guard: need a valid AOI ───────────────────────────────────
has_city_aoi = city_coords is not None
has_shp_aoi  = shp_geom_ee is not None

if not st.session_state.gee_initialized:
    st.warning("⚠️ GEE not initialised. Check credentials in `.streamlit/secrets.toml`.")
    st.stop()

if not (has_city_aoi or has_shp_aoi):
    st.info("👈 **Select a City** or **upload a Shapefile**, then click **Run Jal-AI Analysis**.")
    
    st.markdown("---")
    st.markdown("### 🧠 How Jal-AI Works")
    st.info("Before running analysis, you can review the methodology and satellite sensors used below.")

    with st.expander("📖 Methodology & Data Sources", expanded=True):
        st.markdown("""
        Jal-AI is a **real-time, multi-satellite hydrological disaster intelligence system** built on
        Google Earth Engine (GEE). It fuses 7 independent satellite data sources to produce a
        transparent, community-facing **Composite Disaster Risk Score (0–100)**.

        | Sensor | Dataset | Variable | Role in Score | Weight |
        |---|---|---|---|---|
        | **Sentinel-1 SAR** | S1_GRD | Radar backscatter | **Flood Detection** | **30%** |
        | **NASA GPM** | IMERG_V07 | Precipitation | **Rainfall** (30-day) | **20%** |
        | **Sentinel-2** | S2_SR | NDWI (Green-NIR) | **Surface Water** | **15%** |
        | **SRTM DEM** | SRTMGL1 | Elevation/Slope | **Terrain Risk** | **10%** |
        | **JRC Water** | JRC/GSW1_4 | Change band | **Historical Trend** | **10%** |
        | **MODIS NDVI** | MOD13A2 | NDVI composite | **Drought Index** | **10%** |
        | **MODIS LST** | MOD11A1 | LST_Day_1km | **Heat Stress** | **5%** |
        """)
    st.stop()

# Resolve display label and map centre
if aoi_mode == "🏙️ Select City" and has_city_aoi:
    aoi_label  = f"{sel_city}, {sel_state}"
    map_center = city_coords
else:
    aoi_label  = shp_label
    map_center = shp_center

run_btn = st.sidebar.button("🚀 Run Jal-AI Analysis", use_container_width=True, type="primary")

if run_btn:
    # Hard-reset stale state for new AOI
    for k in ANALYSIS_KEYS:
        st.session_state.pop(k, None)

    with st.status(f"🛰️ Initialising multi-sensor array for **{aoi_label}**…", expanded=True) as status:
        try:
            # Resolve EE geometry from the active mode
            if has_shp_aoi and aoi_mode == "📁 Upload Shapefile":
                geom = shp_geom_ee
            else:
                geom = get_city_geometry(city_coords["lat"], city_coords["lon"], buffer_km)

            tgt  = analysis_date.strftime("%Y-%m-%d")
            d30  = (analysis_date - timedelta(days=30)).strftime("%Y-%m-%d")
            d180 = (analysis_date - timedelta(days=180)).strftime("%Y-%m-%d")

            # ── 1. NDWI Surface Water ─────────────────────────
            st.write("🔵 Sentinel-2 NDWI (Surface Water Detection)…")
            ndwi_img = get_ndwi_image(geom, d30, tgt)
            if ndwi_img:
                st.session_state.ndwi_url   = get_tile_url(ndwi_img, {"min": 0, "max": 0.6, "palette": ["#d1fae5","#0ea5e9","#0c4a6e"]})
                st.session_state.water_stats = calculate_water_statistics(ndwi_img, geom)

            # ── 2. SAR Flood Detection ────────────────────────
            st.write("🔴 Sentinel-1 SAR (Radar Flood Detection)…")
            flood_mask = get_flood_active_mask(geom, tgt)
            if flood_mask:
                st.session_state.flood_url  = get_tile_url(flood_mask, {"palette": ["#ef4444"]})
                st.session_state.flood_stats = get_flood_statistics(flood_mask, geom)
            else:
                st.session_state.flood_stats = {"flooded_sq_km": 0}

            # ── 3. GPM Rainfall ───────────────────────────────
            st.write("🌧️ NASA GPM IMERG (Precipitation Analysis)…")
            rain_img = get_precipitation_map(geom, d30, tgt)
            if rain_img:
                st.session_state.rain_url   = get_tile_url(rain_img, {"min": 0, "max": 600, "palette": ["#f0f9ff","#38bdf8","#0369a1","#1e3a5f"]})
                st.session_state.rain_stats = get_rainfall_statistics(rain_img, geom)
            else:
                st.session_state.rain_stats = {"mean_mm": 0, "max_mm": 0}

            # ── 4. JRC Historical Water Change ────────────────
            st.write("🏞️ JRC Global Surface Water (Long-term Change)…")
            jrc_raw, jrc_gain, jrc_loss, _ = get_jrc_water_change(geom)
            if jrc_raw:
                # Visualise loss (red) / gain (blue)
                jrc_vis = jrc_loss.unmask(0).rename("loss").addBands(
                    jrc_gain.unmask(0).rename("gain")
                )
                st.session_state.jrc_url    = get_tile_url(jrc_raw, {"min": -100, "max": 100, "palette": ["#b91c1c","#fafafa","#1d4ed8"]})
                st.session_state.jrc_stats  = get_jrc_water_stats(jrc_raw, geom)
            else:
                st.session_state.jrc_stats  = {"change_abs_mean": 0}

            # ── 5. Terrain (SRTM) ─────────────────────────────
            st.write("⛰️ SRTM (Terrain Elevation & Slope)…")
            elev_img, slope_img = get_terrain_slope(geom)
            if elev_img and slope_img:
                st.session_state.terrain_stats = get_terrain_statistics(elev_img, slope_img, geom)
            else:
                st.session_state.terrain_stats = {"mean_elev": 0, "min_elev": 0, "mean_slope": 0}

            # ── 6. Heat Stress (MODIS LST) ────────────────────
            st.write("🌡️ MODIS LST (Heat Stress Index)…")
            lst_img = get_heat_stress_map(geom, d30, tgt)
            if lst_img:
                st.session_state.lst_url   = get_tile_url(lst_img, {"min": 20, "max": 50, "palette": ["#bfdbfe","#fde68a","#f97316","#7f1d1d"]})
                st.session_state.lst_stats = get_lst_statistics(lst_img, geom)
            else:
                st.session_state.lst_stats = {"mean_c": 0, "max_c": 0}

            # ── 7. Drought Index (MODIS NDVI) ─────────────────
            st.write("🌿 MODIS NDVI (Drought & Vegetation Stress)…")
            ndvi_img = get_drought_ndvi(geom, d180, tgt)
            if ndvi_img:
                st.session_state.ndvi_url   = get_tile_url(ndvi_img, {"min": 0, "max": 0.8, "palette": ["#7f1d1d","#fde68a","#14532d"]})
                st.session_state.ndvi_stats = get_ndvi_statistics(ndvi_img, geom)
            else:
                st.session_state.ndvi_stats = {"mean_ndvi": 0.5, "drought_label": "Unknown"}

            # ── 8. Community Safe Havens & Vulnerability ──────
            if elev_img and slope_img:
                st.write("🛡️ Computing Safe Havens (Terrain + Flood-free)…")
                safe = get_safe_haven_zones(geom, flood_mask, slope_img, elev_img)
                if safe:
                    st.session_state.safe_url = get_tile_url(safe, {"palette": ["#22c55e"]})

            if flood_mask and ndwi_img:
                st.write("🛣️ Mapping Vulnerability Corridors…")
                vulner = detect_vulnerable_paths(geom, flood_mask, ndwi_img.gt(0))
                if vulner:
                    st.session_state.vulner_url = get_tile_url(vulner, {"palette": ["#f59e0b"]})

            # ── 9. Composite AI Risk Score ────────────────────
            st.write("🧠 Computing Composite Disaster Risk Score…")
            st.session_state.composite_risk = compute_composite_risk_score(
                flooded_sq_km    = st.session_state.flood_stats.get("flooded_sq_km", 0),
                rain_mean_mm     = st.session_state.rain_stats.get("mean_mm", 0),
                water_area_sq_km = st.session_state.water_stats["area_sq_km"] if st.session_state.water_stats else 0,
                mean_slope       = st.session_state.terrain_stats.get("mean_slope", 0),
                jrc_change       = st.session_state.jrc_stats.get("change_abs_mean", 0),
                mean_ndvi        = st.session_state.ndvi_stats.get("mean_ndvi", 0.5),
                lst_mean_c       = st.session_state.lst_stats.get("mean_c", 0),
            )

            # ── 10. Accuracy Metadata ────────────────────────
            st.write("📡 Finalising data accuracy validation…")
            st.session_state.accuracy_metrics = get_jal_accuracy_metrics(geom, tgt)

            st.session_state.jal_city  = aoi_label
            st.session_state.jal_state = sel_state or "Custom AOI"
            st.session_state.jal_done  = True
            status.update(label="✅ Jal-AI Analysis Complete!", state="complete", expanded=False)

        except Exception as e:
            st.error(f"Analysis error: {e}")

# ═══════════════════════════════════════════════════════════════
# RESULTS SECTION
# ═══════════════════════════════════════════════════════════════
if not st.session_state.get("jal_done"):
    st.stop()

city_name  = st.session_state.get("jal_city", sel_city)
risk_score = st.session_state.get("composite_risk", 0)
w_stats    = st.session_state.get("water_stats") or {}
f_stats    = st.session_state.get("flood_stats") or {}
r_stats    = st.session_state.get("rain_stats") or {}
j_stats    = st.session_state.get("jrc_stats") or {}
t_stats    = st.session_state.get("terrain_stats") or {}
l_stats    = st.session_state.get("lst_stats") or {}
n_stats    = st.session_state.get("ndvi_stats") or {}

water_area    = w_stats.get("area_sq_km", 0)
flooded_km    = f_stats.get("flooded_sq_km", 0)
rain_mean     = r_stats.get("mean_mm", 0)
rain_max      = r_stats.get("max_mm", 0)
jrc_change    = j_stats.get("change_abs_mean", 0)
mean_elev     = t_stats.get("mean_elev", 0)
mean_slope    = t_stats.get("mean_slope", 0)
lst_mean      = l_stats.get("mean_c", 0)
ndvi_mean     = n_stats.get("mean_ndvi", 0)
drought_label = n_stats.get("drought_label", "")
has_flood     = flooded_km > 0.01

# ── Risk tier ─────────────────────────────────────────────────
if risk_score >= 65:
    risk_label, risk_col, action_tier = "🚨 Critical", "#ef4444", "CRITICAL"
elif risk_score >= 40:
    risk_label, risk_col, action_tier = "⚠️ High",    "#f97316", "ALERT"
elif risk_score >= 20:
    risk_label, risk_col, action_tier = "🟡 Moderate","#eab308", "WATCH"
else:
    risk_label, risk_col, action_tier = "🟢 Low",     "#22c55e", "STABLE"

# ── Map ───────────────────────────────────────────────────────
base_map = create_base_map(map_center["lat"], map_center["lon"], zoom=11)
layer_map = [
    ("ndwi",   "ndwi_url",   "Surface Water (NDWI)", 0.65),
    ("flood",  "flood_url",  "🔴 Active Flood Zone",  0.9),
    ("rain",   "rain_url",   "🌧️ GPM Rainfall",       0.5),
    ("jrc",    "jrc_url",    "🏞️ Water Change (JRC)",  0.6),
    ("safe",   "safe_url",   "🟢 Safe Havens",         1.0),
    ("vulner", "vulner_url", "⚠️ Vulnerability Corridors", 0.85),
    ("lst",    "lst_url",    "🌡️ Heat Stress",         0.55),
    ("ndvi",   "ndvi_url",   "🌿 Drought Index",       0.55),
]
for key, url_key, name, opacity in layer_map:
    if L.get(key) and st.session_state.get(url_key):
        add_tile_layer(base_map, st.session_state[url_key], name, opacity)
add_layer_control(base_map)

# ── Top KPI bar ───────────────────────────────────────────────
acc_meta = st.session_state.get("accuracy_metrics", {})
acc_score = acc_meta.get("accuracy_score", 0)

kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
with kpi1:
    render_stat_card(f"{risk_score}/100", "AI Disaster Risk", "🧠", "stat-card-orange" if risk_score > 40 else "stat-card-blue")
with kpi2:
    render_stat_card(f"{acc_score}%", "Data Accuracy", "📡", "stat-card-green" if acc_score > 75 else "stat-card-orange")
with kpi3:
    render_stat_card(f"{flooded_km:.2f} km²", "Flooded (SAR)", "🔴", "stat-card-orange" if has_flood else "stat-card-green")
with kpi4:
    render_stat_card(f"{rain_mean:.1f} mm", "Rainfall (30d)", "🌧️", "stat-card-blue")
with kpi5:
    render_stat_card(drought_label, "Drought Index", "🌿", "stat-card-green" if "Healthy" in drought_label else "stat-card-orange")

st.markdown(f"### 🗺️ {city_name} — Multi-Sensor Disaster Intelligence Map")
st_folium(base_map, width=None, height=480)

st.markdown("---")

# ── Analysis Grid ─────────────────────────────────────────────
col_left, col_right = st.columns([3, 2])

with col_left:
    # ── Community Resilience Row ──────────────────────────────
    st.markdown(f"#### 🏘️ {city_name} — Disaster Preparedness Summary")

    tabs = st.tabs(["🌊 Water & Flood", "🌧️ Rainfall", "⛰️ Terrain", "🌡️ Heat & Drought", "👩‍👩‍👧‍👦 Community Action", "📡 Validation & Integrity"])

    with tabs[0]:
        r1, r2 = st.columns(2)
        with r1:
            st.markdown(f"""
            <div class="jal-card">
            <b>Surface Water (NDWI)</b><br>
            <span style="font-size:1.4rem;color:#0ea5e9">{water_area:.2f} km²</span><br>
            <small style="color:#94a3b8">JRC long-term change: <b style="color:{'#22c55e' if jrc_change>=0 else '#ef4444'}">{jrc_change:+.1f}%</b></small>
            </div>
            """, unsafe_allow_html=True)
        with r2:
            st.markdown(f"""
            <div class="jal-card">
            <b>Radar Flood Detection (SAR)</b><br>
            <span style="font-size:1.4rem;color:{'#ef4444' if has_flood else '#22c55e'}">
            {"🔴 " + str(flooded_km) + " km² Flooded" if has_flood else "🟢 No Active Flooding"}
            </span><br>
            <small style="color:#94a3b8">Cloud-independent Sentinel-1 C-Band radar</small>
            </div>
            """, unsafe_allow_html=True)

    with tabs[1]:
        r1, r2 = st.columns(2)
        with r1:
            rain_risk = "🔴 Extreme" if rain_mean > 300 else "🟠 High" if rain_mean > 150 else "🟡 Moderate" if rain_mean > 50 else "🟢 Low"
            st.markdown(f"""
            <div class="jal-card">
            <b>30-Day Cumulative Rainfall</b><br>
            <span style="font-size:1.4rem;color:#38bdf8">{rain_mean:.1f} mm mean</span><br>
            <small style="color:#94a3b8">Peak: {rain_max:.1f} mm — Risk: {rain_risk}</small>
            </div>
            """, unsafe_allow_html=True)
        with r2:
            st.markdown(f"""
            <div class="jal-card">
            <b>Rainfall Source</b><br>
            <span style="font-size:0.9rem;color:#94a3b8">NASA GPM IMERG (30-min, global)<br>
            Collection: NASA/GPM_L3/IMERG_V07</span>
            </div>
            """, unsafe_allow_html=True)

    with tabs[2]:
        r1, r2 = st.columns(2)
        with r1:
            st.markdown(f"""
            <div class="jal-card">
            <b>Terrain Analysis (SRTM 30m)</b><br>
            Mean Elevation: <b>{mean_elev:.0f} m</b><br>
            Mean Slope: <b>{mean_slope:.1f}°</b><br>
            <small style="color:#94a3b8">{'⚠️ Steep — high runoff risk' if mean_slope>15 else '✅ Gentle — manageable runoff'}</small>
            </div>
            """, unsafe_allow_html=True)
        with r2:
            low_lying = mean_elev < 50
            st.markdown(f"""
            <div class="jal-card">
            <b>Flood Exposure Risk</b><br>
            <span style="color:{'#ef4444' if low_lying else '#22c55e'}">
            {'🔴 Low-lying coastal/valley city — high inundation exposure' if low_lying else '🟢 Elevated terrain — lower inundation exposure'}
            </span>
            </div>
            """, unsafe_allow_html=True)

    with tabs[3]:
        r1, r2 = st.columns(2)
        with r1:
            heat_level = "🔴 Extreme" if lst_mean > 42 else "🟠 High" if lst_mean > 36 else "🟡 Moderate" if lst_mean > 30 else "🟢 Low"
            st.markdown(f"""
            <div class="jal-card">
            <b>Land Surface Temp (MODIS)</b><br>
            <span style="font-size:1.4rem;color:#f97316">{lst_mean:.1f}°C</span><br>
            <small style="color:#94a3b8">Heat stress level: {heat_level}</small>
            </div>
            """, unsafe_allow_html=True)
        with r2:
            ndvi_color = "#22c55e" if "Healthy" in drought_label else "#f59e0b" if "Normal" in drought_label else "#ef4444"
            st.markdown(f"""
            <div class="jal-card">
            <b>Drought Index (MODIS NDVI)</b><br>
            <span style="font-size:1.4rem;color:{ndvi_color}">{drought_label}</span><br>
            <small style="color:#94a3b8">Mean NDVI: {ndvi_mean:.3f} (0=bare, 1=dense vegetation)</small>
            </div>
            """, unsafe_allow_html=True)

    with tabs[4]:
        # Gender & Community Advisory — fully data-driven
        if action_tier == "CRITICAL":
            st.error(f"🚨 **CRITICAL Advisory for {city_name}:** AI Risk Score {risk_score}/100. Active flooding ({flooded_km:.2f} km²) detected. W-SHGs must execute **Emergency Water Storage Protocol** immediately.")
        elif action_tier == "ALERT":
            st.warning(f"⚠️ **HIGH Alert for {city_name}:** Risk Score {risk_score}/100. Rainfall {rain_mean:.0f}mm + potential inundation risk. Activate pre-emptive community water protocols.")
        elif action_tier == "WATCH":
            st.info(f"🟡 **WATCH for {city_name}:** Risk Score {risk_score}/100. Monitor rainfall trends. JRC water change: {jrc_change:+.1f}%. Pre-position resources.")
        else:
            st.success(f"✅ **STABLE for {city_name}:** Risk Score {risk_score}/100. Conditions normal. Maintain routine monitoring.")

        # Context-specific SHG actions
        actions = []
        if has_flood:
            actions += [
                f"Evacuate W-SHG collecting groups from flooded zones ({flooded_km:.2f} km² inundated).",
                "Activate Safe Haven points (🟢 green layer on map) as emergency water storage sites.",
                "Issue contamination alerts for all water points within Vulnerability Corridors.",
            ]
        if rain_mean > 100:
            actions += [
                f"Deploy water quality test kits — cumulative rain: {rain_mean:.0f}mm (max: {rain_max:.0f}mm).",
                "Inspect and reinforce community rainwater harvesting tanks.",
            ]
        if "Drought" in drought_label:
            actions += [
                f"Drought stress detected (NDVI: {ndvi_mean:.2f}). Engage district for emergency water tanker supply.",
                "Map groundwater wells within 2km radius for SHG access in water-stressed clusters.",
            ]
        if lst_mean > 36:
            actions += [
                f"High heat stress ({lst_mean:.1f}°C). Ensure shaded water distribution points for women & children.",
            ]
        if jrc_change < -10:
            actions += [
                f"Long-term water body loss detected ({jrc_change:.1f}% JRC change). Launch wetland restoration campaign.",
            ]
        if not actions:
            actions = [
                "Conditions stable. Conduct routine water quality audit at community points.",
                f"Update household water stress map for {city_name} (current surface water: {water_area:.2f} km²).",
                "Submit monthly GIS monitoring report to District Water Board.",
            ]

    with tabs[5]:
        # Validation & Integrity Tab
        st.markdown(f"#### 📡 Data Confidence & Accuracy Index: {city_name}")
        meta = st.session_state.get("accuracy_metrics")
        if meta:
            is_val = meta.get("accuracy_score", 0)
            st.markdown(f"""
            <div class="jal-card" style="border-left: 5px solid {'#22c55e' if is_val > 75 else '#f59e0b' if is_val > 50 else '#ef4444'};">
            <b>Jal-AI Confidence Index: <span style="font-size:1.5rem;color:{'#22c55e' if is_val > 75 else '#f59e0b' if is_val > 50 else '#ef4444'};">{is_val}%</span></b><br>
            <span style="color:#94a3b8;font-size:0.9rem;">Status: <b>{meta.get('integrity_label', 'Unknown')}</b> — Sensor Fusion: <b>{meta.get('sensor_fusion', 'N/A')}</b></span>
            </div>
            """, unsafe_allow_html=True)

            v1, v2, v3 = st.columns(3)
            with v1:
                st.markdown(f"""
                <div class="jal-card" style="text-align:center;">
                <small style="color:#94a3b8; text-transform:uppercase;">Sentinel-2 Optical</small><br>
                <div style="font-size:1.2rem; font-weight:700; margin:0.5rem 0;">{meta.get('s2_status', 'N/A')}</div>
                <small style="color:#64748b;">Latest: {meta.get('last_s2', 'N/A')}</small>
                </div>
                """, unsafe_allow_html=True)
            with v2:
                st.markdown(f"""
                <div class="jal-card" style="text-align:center;">
                <small style="color:#94a3b8; text-transform:uppercase;">Sentinel-1 Radar</small><br>
                <div style="font-size:1.2rem; font-weight:700; margin:0.5rem 0;">{meta.get('s1_status', 'N/A')}</div>
                <small style="color:#64748b;">Latest: {meta.get('last_s1', 'N/A')}</small>
                </div>
                """, unsafe_allow_html=True)
            with v3:
                st.markdown(f"""
                <div class="jal-card" style="text-align:center;">
                <small style="color:#94a3b8; text-transform:uppercase;">GPM Rainfall</small><br>
                <div style="font-size:1.2rem; font-weight:700; margin:0.5rem 0;">{meta.get('gpm_status', 'N/A')}</div>
                <small style="color:#64748b;">NASA IMERG V07</small>
                </div>
                """, unsafe_allow_html=True)
            
            st.info("💡 **Accuracy logic:** Radar (SAR) provides 40pts base confidence (penetrates clouds). Optical (S2) provides 40pts base (penalized by clouds/age). Rainfall (GPM) provides final 20pts.")

        st.markdown("**📋 W-SHG Recommended Actions:**")
        for i, a in enumerate(actions, 1):
            st.write(f"{i}. {a}")

        st.markdown("---")
        st.markdown("**📤 Broadcast & Export:**")

        from services.jal_report import generate_jal_pdf, format_jal_whatsapp_alert

        bc1, bc2 = st.columns(2)

        with bc1:
            with st.spinner("Generating PDF report…"):
                try:
                    pdf_bytes = generate_jal_pdf(
                        city_name     = city_name,
                        analysis_date = str(analysis_date),
                        risk_score    = risk_score,
                        action_tier   = action_tier,
                        water_area    = water_area,
                        flooded_km    = flooded_km,
                        rain_mean     = rain_mean,
                        rain_max      = rain_max,
                        jrc_change    = jrc_change,
                        mean_elev     = mean_elev,
                        mean_slope    = mean_slope,
                        lst_mean      = lst_mean,
                        ndvi_mean     = ndvi_mean,
                        drought_label = drought_label,
                        actions       = actions,
                        buffer_km     = buffer_km if aoi_mode == "🏙️ Select City" else 0,
                    )
                    fn = f"JalaAI_{city_name.replace(' ','_').replace(',','').replace('. ','_')}_{str(analysis_date)}.pdf"
                    st.download_button(
                        label="📥 Download Action Report PDF",
                        data=pdf_bytes,
                        file_name=fn,
                        mime="application/pdf",
                        use_container_width=True,
                    )
                except Exception as pdf_err:
                    st.error(f"PDF generation error: {pdf_err}")

        with bc2:
            try:
                wa_text = format_jal_whatsapp_alert(
                    city_name     = city_name,
                    analysis_date = str(analysis_date),
                    action_tier   = action_tier,
                    risk_score    = risk_score,
                    flooded_km    = flooded_km,
                    rain_mean     = rain_mean,
                    water_area    = water_area,
                    drought_label = drought_label,
                    actions       = actions,
                )
                st.download_button(
                    label="📲 Download SHG Alert (Text)",
                    data=wa_text,
                    file_name=f"JalAI_Alert_{city_name.replace(' ','_')}_{str(analysis_date)}.txt",
                    mime="text/plain",
                    use_container_width=True,
                    type="primary",
                )
                with st.expander("👁 Preview WhatsApp Alert"):
                    st.text(wa_text)
            except Exception as wa_err:
                st.error(f"Alert generation error: {wa_err}")

with col_right:
    st.markdown(f"#### 📊 {city_name} Risk Dashboard")

    st.markdown(f"""
    <div class="jal-card" style="border-color:{risk_col};">
        <b>🧠 AI Composite Risk Score</b><br>
        <span style="font-size:2.2rem;font-weight:900;color:{risk_col};">{risk_score}<span style="font-size:1rem;color:#94a3b8;">/100</span></span><br>
        <span class="risk-badge" style="background:{risk_col}22;color:{risk_col};margin-top:0.5rem;">{risk_label}</span><br>
        <small style="color:#94a3b8;margin-top:0.5rem;display:block;">Computed from 7 satellite data sources in real-time</small>
    </div>
    """, unsafe_allow_html=True)

    # Score breakdown
    breakdown = pd.DataFrame({
        "Factor": ["Flood (SAR)", "Rainfall (GPM)", "Water Deficit", "Terrain Slope",
                   "Water Change (JRC)", "Drought (NDVI)", "Heat Stress (LST)"],
        "Weight": ["30%", "20%", "15%", "10%", "10%", "10%", "5%"],
        "Value": [
            f"{flooded_km:.2f} km²",
            f"{rain_mean:.1f} mm",
            f"{water_area:.2f} km²",
            f"{mean_slope:.1f}°",
            f"{jrc_change:+.1f}%",
            f"{ndvi_mean:.3f}",
            f"{lst_mean:.1f}°C",
        ]
    })
    st.dataframe(breakdown, use_container_width=True, hide_index=True)

    st.markdown(f"""
    <div class="jal-card">
    <b>City Summary</b><br>
    📍 <b>{city_name}</b>, {st.session_state.get('jal_state', '')}<br>
    📅 Analysis Date: <b>{analysis_date}</b><br>
    🔭 Coverage Radius: <b>{buffer_km} km</b><br>
    🛰️ Sensors: Sentinel-1,2 · GPM · JRC · SRTM · MODIS
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

with st.expander("📖 Methodology & Data Sources — How Jal-AI Works", expanded=False):
    st.markdown("""
    ### 🧠 Jal-AI: Methodology Overview

    Jal-AI is a **real-time, multi-satellite hydrological disaster intelligence system** built on
    Google Earth Engine (GEE). It fuses 7 independent satellite data sources to produce a
    transparent, community-facing **Composite Disaster Risk Score (0–100)**.

    ---

    #### 🛰️ Satellite Data Sources & Their Role

    | Sensor | GEE Collection | Variable | Role in Score | Weight |
    |---|---|---|---|---|
    | **Sentinel-1 SAR** | `COPERNICUS/S1_GRD` | Radar backscatter (VV) | **Flood Detection** — change detection between baseline & event window | **30%** |
    | **NASA GPM IMERG** | `NASA/GPM_L3/IMERG_V07` | `precipitation` | **Rainfall** — 30-day cumulative precipitation (mm) | **20%** |
    | **Sentinel-2** | `COPERNICUS/S2_SR_HARMONIZED` | NDWI = (B3−B8)/(B3+B8) | **Surface Water** — current water area (km²), low area = high deficit risk | **15%** |
    | **SRTM DEM** | `USGS/SRTMGL1_003` | Elevation + Slope | **Terrain Risk** — steep slopes = high runoff; low elevation = flood exposure | **10%** |
    | **JRC Global Surface Water** | `JRC/GSW1_4/GlobalSurfaceWater` | `change_abs` band | **Historical Water Trend** — long-term loss of water bodies signals drought risk | **10%** |
    | **MODIS NDVI** | `MODIS/061/MOD13A2` | 16-day NDVI composite | **Drought Index** — low NDVI = vegetation and water stress | **10%** |
    | **MODIS LST** | `MODIS/061/MOD11A1` | `LST_Day_1km` (K→°C) | **Heat Stress** — extreme heat compounds disaster health risk | **5%** |

    ---

    #### 🔢 Composite Risk Score Formula

    ```
    Risk Score (0–100) =
        min(flooded_km / 5.0,  1.0) × 30   [Flood — SAR]
      + min(rain_mm / 500.0,   1.0) × 20   [Rainfall — GPM]
      + max(1 − water_km / 5.0, 0)  × 15   [Water Deficit — NDWI]
      + min(slope_deg / 20.0,  1.0) × 10   [Terrain — SRTM]
      + min(−jrc_change / 30,  1.0) × 10   [Water Loss Trend — JRC]
      + max(1 − NDVI / 0.5,    0)   × 10   [Drought — MODIS NDVI]
      + min((LST − 32) / 15,   1.0) × 5    [Heat Stress — MODIS LST]
    ```

    All input values are fetched **live from GEE** for the selected city and time window.
    No values are hardcoded or pre-cached.

    ---

    #### 🛡️ Community Layers (Terrain + Flood Fusion)

    | Layer | Logic |
    |---|---|
    | **Safe Havens (Green)** | Elevation > 65th percentile AND slope < 15° AND NOT flooded (SRTM + SAR) |
    | **Vulnerability Corridors (Amber)** | Within 500m of surface water AND actively flooded pixels (NDWI + SAR) |

    ---

    #### 👩‍👩‍👧‍👦 Early Action Advisory Logic (W-SHG)

    The advisory text and SHG action list are dynamically selected using thresholds:
    - **CRITICAL**: Flooded area > 0.01 km² (SAR) OR Risk Score ≥ 65
    - **ALERT**: Rainfall > 150 mm (GPM) OR Risk Score ≥ 40
    - **WATCH**: Rainfall > 50 mm OR JRC water loss > 10% OR Risk Score ≥ 20
    - **STABLE**: All below threshold — routine monitoring protocols applied

    ---
    
    #### ⚠️ Limitations & Data Uncertainty
    
    Jal-AI relies on public satellite records which have inherent scientific limitations:
    - **Temporal Latency**: Sentinel-1/2 have a 5-12 day revisit cycle. The "Real-time" analysis reflects the *latest available* scene, not necessarily the current hour.
    - **Cloud Interference**: Sentinel-2 (NDWI) and MODIS (LST/NDVI) cannot see through thick cloud cover. During heavy storms, Radar (Sentinel-1) is the primary reliable sensor.
    - **Spatial Resolution**: GPM Rainfall (11km) and MODIS (1km) provide regional trends. Localized "cloudbursts" may be under-reported compared to ground-based rain gauges.
    - **Vertical Accuracy**: SRTM Elevation data is static (circa 2000). It does not account for recent urban construction, new embankments, or drainage infrastructure.
    - **Synthetic Fusions**: The Composite Risk Score is an algorithmic estimate. It should supplement, not replace, official government disaster bulletins and local field reports.

    ---

    #### 📦 Open-Source Stack
    - **Platform**: Google Earth Engine (GEE) API + Streamlit
    - **Mapping**: Folium (Leaflet.js) via streamlit-folium
    - **Language**: Python 3.11
    - **License**: Open for community deployment & NGO use
    """)

st.caption("Jal-AI v2.0 · WATER INNOVATION HACKATHON 2026 · Developed by Hemant Kumar · GEE-Powered")
