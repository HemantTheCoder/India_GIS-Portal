"""
gee_water.py - Jala-AI Multi-Sensor Hydrological Intelligence Engine
====================================================================
GEE Datasets Used:
  - COPERNICUS/S1_GRD          : Sentinel-1 SAR (Radar Flood Watch, cloud-penetrating)
  - COPERNICUS/S2_SR_HARMONIZED: Sentinel-2 Optical (NDWI Surface Water Detection)
  - NASA/GPM_L3/IMERG_V06      : NASA GPM Rainfall (Real-time Precipitation Analysis)
  - JRC/GSW1_4/GlobalSurfaceWater: JRC Historical Water (Long-term Change Detection)
  - USGS/SRTMGL1_003           : SRTM Digital Elevation Model (Terrain Risk)
  - MODIS/061/MOD11A1           : MODIS LST (Heat Stress, illness risk in disaster areas)
  - MODIS/061/MOD13A2           : MODIS NDVI (Vegetation+Drought Index)
"""

import ee
from datetime import datetime, timedelta


# ─────────────────────────────────────────────────────────────
# 1. HYDROLOGY: Surface Water (NDWI via Sentinel-2 Optical)
# ─────────────────────────────────────────────────────────────
def get_ndwi_image(geometry, start_date, end_date):
    """
    NDWI = (Green - NIR) / (Green + NIR)  via Sentinel-2 S2_SR_HARMONIZED.
    Returns NDWI image or None.
    """
    try:
        s2 = (
            ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
            .filterBounds(geometry)
            .filterDate(start_date, end_date)
            .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 20))
            .median()
            .clip(geometry)
        )
        return s2.normalizedDifference(["B3", "B8"]).rename("NDWI")
    except Exception as e:
        print(f"[gee_water] NDWI error: {e}")
        return None


def calculate_water_statistics(ndwi_image, geometry):
    """
    Surface water area where NDWI > 0.
    Returns dict with area_sq_m, area_sq_km, area_hectares.
    """
    try:
        water_mask = ndwi_image.gt(0)
        area_image = water_mask.multiply(ee.Image.pixelArea())
        stats = area_image.reduceRegion(
            reducer=ee.Reducer.sum(),
            geometry=geometry,
            scale=30,
            maxPixels=1e9,
        ).getInfo()
        area_sq_m = stats.get("NDWI", 0) or 0
        return {
            "area_sq_m": area_sq_m,
            "area_sq_km": area_sq_m / 1e6,
            "area_hectares": area_sq_m / 1e4,
        }
    except Exception as e:
        print(f"[gee_water] water stats error: {e}")
        return None


# ─────────────────────────────────────────────────────────────
# 2. FLOOD DETECTION: Sentinel-1 SAR (Radar, Cloud-independent)
# ─────────────────────────────────────────────────────────────
def get_flood_active_mask(geometry, target_date):
    """
    SAR-based CHANGE DETECTION using Sentinel-1 IW VV polarisation.

    Algorithm (UNOSAT / JRC standard):
      1. Median composite of baseline period (90–180 days before event)
      2. Median composite of event period (last 20 days)
      3. Speckle filter: 100m circular focal median on both epochs
      4. Flood = pixels where:
           - backscatter DROPPED by >= 4 dB  (specular reflection of inundation)
           - event backscatter < -16 dB       (characteristic open-water threshold)
      5. Mask out JRC permanent water (occurrence > 80%) so existing
         rivers/lakes are NOT counted as new flooding.

    Returns selfMasked binary Flood_Mask image, or None if no SAR data found.
    """
    try:
        tgt_dt  = datetime.strptime(target_date, "%Y-%m-%d")
        base_start  = (tgt_dt - timedelta(days=180)).strftime("%Y-%m-%d")
        base_end    = (tgt_dt - timedelta(days=90)).strftime("%Y-%m-%d")
        flood_start = (tgt_dt - timedelta(days=20)).strftime("%Y-%m-%d")
        flood_end   = target_date

        def sar_collection(s, e):
            col = (
                ee.ImageCollection("COPERNICUS/S1_GRD")
                .filterBounds(geometry)
                .filterDate(s, e)
                .filter(ee.Filter.eq("instrumentMode", "IW"))
                .filter(ee.Filter.listContains("transmitterReceiverPolarisation", "VV"))
                .filter(ee.Filter.eq("orbitProperties_pass", "DESCENDING"))  # consistent pass
                .select("VV")
            )
            # Fall back to both orbits if DESCENDING yields < 2 images
            if col.size().getInfo() < 2:
                col = (
                    ee.ImageCollection("COPERNICUS/S1_GRD")
                    .filterBounds(geometry)
                    .filterDate(s, e)
                    .filter(ee.Filter.eq("instrumentMode", "IW"))
                    .filter(ee.Filter.listContains("transmitterReceiverPolarisation", "VV"))
                    .select("VV")
                )
            return col

        SMOOTH_M = 100  # metres — better speckle suppression
        before_col = sar_collection(base_start, base_end)
        after_col  = sar_collection(flood_start, flood_end)

        # Need at least 1 image in each epoch
        if before_col.size().getInfo() < 1 or after_col.size().getInfo() < 1:
            print("[gee_water] SAR: insufficient images for change detection")
            return None

        before = before_col.median().focal_median(SMOOTH_M, "circle", "meters").clip(geometry)
        after  = after_col.median().focal_median(SMOOTH_M, "circle", "meters").clip(geometry)

        # dB change detection  (negative = backscatter drop = inundation signal)
        diff = after.subtract(before)

        # PRIMARY FLOOD MASK
        # >= 4 dB drop  AND  absolute VV < -16 dB (open water signature)
        flood_raw = diff.lt(-4).And(after.lt(-16))

        # ── SUBTRACT PERMANENT WATER (JRC) ──────────────────────────────────
        # Occurrence > 80% = perennial water body — exclude from flood count
        jrc_occurrence = (
            ee.Image("JRC/GSW1_4/GlobalSurfaceWater")
            .select("occurrence")
            .clip(geometry)
        )
        perm_water = jrc_occurrence.gt(80)   # permanent water mask (1 = permanent)
        flood_new  = flood_raw.And(perm_water.Not())  # only non-permanent cells

        return flood_new.selfMask().rename("Flood_Mask")

    except Exception as e:
        print(f"[gee_water] SAR flood error: {e}")
        return None


def get_flood_statistics(flood_mask, geometry):
    """
    Returns flooded area in sq_km.
    """
    try:
        area = flood_mask.unmask(0).multiply(ee.Image.pixelArea())
        stats = area.reduceRegion(
            reducer=ee.Reducer.sum(),
            geometry=geometry,
            scale=30,
            maxPixels=1e9,
        ).getInfo()
        sq_m = stats.get("Flood_Mask", 0) or 0
        return {"flooded_sq_km": sq_m / 1e6}
    except Exception as e:
        print(f"[gee_water] flood stats error: {e}")
        return {"flooded_sq_km": 0}


# ─────────────────────────────────────────────────────────────
# 3. RAINFALL: NASA GPM IMERG Real-time Precipitation
# ─────────────────────────────────────────────────────────────
def get_precipitation_map(geometry, start_date, end_date):
    """
    Cumulative precipitation from NASA GPM IMERG (mm).
    Returns summed rainfall image or None.
    """
    try:
        gpm = (
            ee.ImageCollection("NASA/GPM_L3/IMERG_V07")
            .filterBounds(geometry)
            .filterDate(start_date, end_date)
            .select("precipitationCal")
            .sum()
            .clip(geometry)
        )
        return gpm.rename("Rainfall")
    except Exception as e:
        print(f"[gee_water] GPM error: {e}")
        return None


def get_rainfall_statistics(rain_img, geometry):
    """
    Returns mean, max rainfall in mm.
    """
    try:
        stats = rain_img.reduceRegion(
            reducer=ee.Reducer.mean().combine(ee.Reducer.max(), sharedInputs=True),
            geometry=geometry,
            scale=5000,
            maxPixels=1e9,
        ).getInfo()
        return {
            "mean_mm": stats.get("Rainfall_mean", 0) or 0,
            "max_mm":  stats.get("Rainfall_max", 0) or 0,
        }
    except Exception as e:
        print(f"[gee_water] rainfall stats error: {e}")
        return {"mean_mm": 0, "max_mm": 0}


# ─────────────────────────────────────────────────────────────
# 4. HISTORICAL WATER CHANGE: JRC Global Surface Water
# ─────────────────────────────────────────────────────────────
def get_jrc_water_change(geometry):
    """
    JRC Global Surface Water v1.4 – 'change_abs' band.
    Negative = water loss (drought signal), Positive = water gain (flood risk).
    Returns image classified as: gain, stable, loss.
    """
    try:
        jrc = ee.Image("JRC/GSW1_4/GlobalSurfaceWater").select("change_abs").clip(geometry)
        # gain = > +10% | stable = -10 to +10 | loss = < -10%
        gain   = jrc.gt(10).rename("Water_Gain")
        loss   = jrc.lt(-10).rename("Water_Loss")
        stable = jrc.gte(-10).And(jrc.lte(10)).rename("Water_Stable")
        return jrc, gain, loss, stable
    except Exception as e:
        print(f"[gee_water] JRC error: {e}")
        return None, None, None, None


def get_jrc_water_stats(jrc_raw, geometry):
    """
    Returns the mean surface water occurrence change percentage.
    """
    try:
        stats = jrc_raw.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=geometry,
            scale=30,
            maxPixels=1e9,
        ).getInfo()
        return {"change_abs_mean": stats.get("change_abs", 0) or 0}
    except Exception as e:
        print(f"[gee_water] JRC stats error: {e}")
        return {"change_abs_mean": 0}


# ─────────────────────────────────────────────────────────────
# 5. TERRAIN: SRTM Elevation & Slope
# ─────────────────────────────────────────────────────────────
def get_terrain_slope(geometry):
    """
    Returns SRTM Elevation and slope images.
    """
    try:
        srtm  = ee.Image("USGS/SRTMGL1_003").clip(geometry)
        slope = ee.Terrain.slope(srtm)
        return srtm.rename("Elevation"), slope.rename("Slope")
    except Exception as e:
        print(f"[gee_water] terrain error: {e}")
        return None, None


def get_terrain_statistics(elev_img, slope_img, geometry):
    """
    Returns mean/min elevation and mean slope.
    """
    try:
        stats = elev_img.addBands(slope_img).reduceRegion(
            reducer=ee.Reducer.mean().combine(ee.Reducer.min(), sharedInputs=True),
            geometry=geometry,
            scale=90,
            maxPixels=1e9,
        ).getInfo()
        return {
            "mean_elev":  stats.get("Elevation_mean", 0) or 0,
            "min_elev":   stats.get("Elevation_min", 0) or 0,
            "mean_slope": stats.get("Slope_mean", 0) or 0,
        }
    except Exception as e:
        print(f"[gee_water] terrain stats error: {e}")
        return {"mean_elev": 0, "min_elev": 0, "mean_slope": 0}


# ─────────────────────────────────────────────────────────────
# 6. HEAT STRESS: MODIS Land Surface Temperature
# ─────────────────────────────────────────────────────────────
def get_heat_stress_map(geometry, start_date, end_date):
    """
    MODIS MOD11A1 LST – critical for disaster health risk.
    Converts K→°C.  Returns daily-mean LST image.
    """
    try:
        lst = (
            ee.ImageCollection("MODIS/061/MOD11A1")
            .filterBounds(geometry)
            .filterDate(start_date, end_date)
            .select("LST_Day_1km")
            .mean()
            .multiply(0.02)
            .subtract(273.15)
            .clip(geometry)
            .rename("LST_C")
        )
        return lst
    except Exception as e:
        print(f"[gee_water] LST error: {e}")
        return None


def get_lst_statistics(lst_img, geometry):
    """Returns mean/max LST in Celsius."""
    try:
        stats = lst_img.reduceRegion(
            reducer=ee.Reducer.mean().combine(ee.Reducer.max(), sharedInputs=True),
            geometry=geometry,
            scale=1000,
            maxPixels=1e9,
        ).getInfo()
        return {
            "mean_c": round(stats.get("LST_C_mean", 0) or 0, 2),
            "max_c":  round(stats.get("LST_C_max", 0) or 0, 2),
        }
    except Exception as e:
        print(f"[gee_water] LST stats error: {e}")
        return {"mean_c": 0, "max_c": 0}


# ─────────────────────────────────────────────────────────────
# 7. DROUGHT INDEX: MODIS NDVI (16-day composite)
# ─────────────────────────────────────────────────────────────
def get_drought_ndvi(geometry, start_date, end_date):
    """
    MODIS MOD13A2 16-day NDVI – negative anomalies = drought + water stress.
    Returns scaled NDVI image.
    """
    try:
        ndvi = (
            ee.ImageCollection("MODIS/061/MOD13A2")
            .filterBounds(geometry)
            .filterDate(start_date, end_date)
            .select("NDVI")
            .mean()
            .multiply(0.0001)
            .clip(geometry)
            .rename("NDVI")
        )
        return ndvi
    except Exception as e:
        print(f"[gee_water] NDVI drought error: {e}")
        return None


def get_ndvi_statistics(ndvi_img, geometry):
    """Returns mean NDVI and drought classification."""
    try:
        stats = ndvi_img.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=geometry,
            scale=500,
            maxPixels=1e9,
        ).getInfo()
        mean = stats.get("NDVI", 0.5) or 0.5
        if mean < 0.2:
            label = "Extreme Drought"
        elif mean < 0.35:
            label = "Moderate Drought"
        elif mean < 0.5:
            label = "Normal Vegetated"
        else:
            label = "Healthy Vegetation"
        return {"mean_ndvi": round(mean, 3), "drought_label": label}
    except Exception as e:
        print(f"[gee_water] NDVI stats error: {e}")
        return {"mean_ndvi": 0, "drought_label": "Unknown"}


# ─────────────────────────────────────────────────────────────
# 8. COMMUNITY LAYERS: Safe Havens & Vulnerability Corridors
# ─────────────────────────────────────────────────────────────
def get_safe_haven_zones(geometry, flood_mask, slope_img, elevation_img):
    """
    Safe Havens = High Elevation + Low Slope (<15°) + No Flooding.
    """
    try:
        stats = elevation_img.reduceRegion(
            reducer=ee.Reducer.minMax(),
            geometry=geometry,
            scale=90,
        ).getInfo()
        min_e = stats.get("Elevation_min", 0) or 0
        max_e = stats.get("Elevation_max", 100) or 100
        threshold = min_e + (max_e - min_e) * 0.65

        is_high = elevation_img.gt(threshold)
        is_flat = slope_img.lt(15)
        is_dry  = flood_mask.unmask(0).Not() if flood_mask else ee.Image(1)
        return is_high.And(is_flat).And(is_dry).selfMask().rename("Safe_Havens")
    except Exception as e:
        print(f"[gee_water] safe haven error: {e}")
        return None


def detect_vulnerable_paths(geometry, flood_mask, water_mask):
    """
    Vulnerability Corridors = Areas within 500m of water AND actively flooded.
    """
    try:
        dist_to_water = water_mask.fastDistanceTransform().sqrt().multiply(
            ee.Image.pixelArea().sqrt()
        )
        is_near_water   = dist_to_water.lt(500)
        vulnerable = is_near_water.And(flood_mask.unmask(0).gt(0))
        return vulnerable.selfMask().rename("Vulnerable_Paths")
    except Exception as e:
        print(f"[gee_water] vulnerable path error: {e}")
        return None


# ─────────────────────────────────────────────────────────────
# 9. COMPOSITE RISK SCORE (0–100)
# ─────────────────────────────────────────────────────────────
def compute_composite_risk_score(
    flooded_sq_km,
    rain_mean_mm,
    water_area_sq_km,
    mean_slope,
    jrc_change,
    mean_ndvi,
    lst_mean_c
):
    """
    Weighted composite disaster risk score (0–100) computed entirely from GEE data.

    Weights:
      Flood presence        : 30%
      Rainfall intensity    : 20%
      Water area deficit    : 15%
      Terrain slope risk    : 10%
      JRC water loss trend  : 10%
      Drought (NDVI)        : 10%
      Heat stress (LST)     : 5%
    """
    flood_score    = min(1.0, flooded_sq_km / 5.0)             * 30
    rain_score     = min(1.0, rain_mean_mm / 500.0)            * 20
    water_deficit  = max(0.0, 1 - water_area_sq_km / 5.0)     * 15  # low water = high vulnerability
    slope_risk     = min(1.0, mean_slope / 20.0)               * 10
    jrc_loss       = min(1.0, max(0, -jrc_change / 30.0))      * 10
    drought_risk   = max(0.0, 1 - mean_ndvi / 0.5)            * 10
    heat_risk      = min(1.0, max(0, lst_mean_c - 32) / 15.0) * 5

    total = flood_score + rain_score + water_deficit + slope_risk + jrc_loss + drought_risk + heat_risk
    return round(min(100, max(0, total)), 1)


# ─────────────────────────────────────────────────────────────
# 9. VALIDATION & INTEGRITY: Real-time Data Accuracy Metrics
# ─────────────────────────────────────────────────────────────
def get_jal_accuracy_metrics(geometry, target_date):
    """
    Computes a Data Confidence Index (Accuracy) based on sensor availability,
    temporal proximity, and cloud interference.
    """
    try:
        tgt_dt = datetime.strptime(target_date, "%Y-%m-%d")
        d30 = (tgt_dt - timedelta(days=30)).strftime("%Y-%m-%d")

        # 1. Sentinel-2 (Optical) Accuracy
        s2_col = (
            ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
            .filterBounds(geometry)
            .filterDate(d30, target_date)
            .sort("system:time_start", False)
        )
        s2_count = s2_col.size().getInfo()
        s2_cloud = s2_col.aggregate_mean("CLOUDY_PIXEL_PERCENTAGE").getInfo() if s2_count > 0 else 100
        
        # S2 temporal gap (days from target)
        s2_gap = 15
        if s2_count > 0:
            s2_latest = ee.Date(s2_col.first().get("system:time_start")).format("yyyy-MM-dd").getInfo()
            s2_gap = (tgt_dt - datetime.strptime(s2_latest, "%Y-%m-%d")).days

        # 2. Sentinel-1 (Radar) Accuracy
        s1_col = (
            ee.ImageCollection("COPERNICUS/S1_GRD")
            .filterBounds(geometry)
            .filterDate(d30, target_date)
            .sort("system:time_start", False)
        )
        s1_count = s1_col.size().getInfo()
        s1_gap = 15
        if s1_count > 0:
            s1_latest = ee.Date(s1_col.first().get("system:time_start")).format("yyyy-MM-dd").getInfo()
            s1_gap = (tgt_dt - datetime.strptime(s1_latest, "%Y-%m-%d")).days

        # 3. GPM Rainfall (Granule Density)
        gpm_count = (
            ee.ImageCollection("NASA/GPM_L3/IMERG_V07")
            .filterBounds(geometry)
            .filterDate(d30, target_date)
            .size().getInfo()
        )

        # ── Jal-AI Accuracy Formula (0-100) ──
        # We value consistency and clear skies.
        
        # Optic base: starts at 40, loses 1 point per 1% cloud, 2 points per day of age
        optic_conf = max(0, 40 - (s2_cloud * 0.4) - (s2_gap * 2)) if s2_count > 0 else 0
        
        # Radar base: starts at 40 (cloud independent!), loses 2 points per day of age
        radar_conf = max(0, 40 - (s1_gap * 2)) if s1_count > 0 else 0
        
        # Rainfall / Ancillary: 20 points
        ancillary_conf = min(20, (gpm_count / 1400) * 20) # IMERG has ~1400 granules in 30 days globally

        accuracy_score = optic_conf + radar_conf + ancillary_conf
        
        # Bonus for Multi-sensor fusion
        if s1_count > 0 and s2_count > 0:
            accuracy_score += 5

        return {
            "accuracy_score": min(100, round(accuracy_score, 1)),
            "s2_status": f"{s2_count} scenes | {s2_cloud:.1f}% cloud",
            "s1_status": f"{s1_count} passes | {s1_gap}d latency",
            "gpm_status": f"{gpm_count} granules",
            "sensor_fusion": "QUAD-SENSOR ACTIVE" if s1_count > 0 and s2_count > 0 and gpm_count > 100 else "DEGRADED",
            "integrity_label": "High Confidence" if accuracy_score > 80 else "Moderate" if accuracy_score > 50 else "Low / Field Verify",
            "last_s2": s2_latest if s2_count > 0 else "N/A",
            "last_s1": s1_latest if s1_count > 0 else "N/A",
        }
    except Exception as e:
        print(f"[gee_water] Accuracy metrics error: {e}")
        return {"accuracy_score": 0, "error": str(e)}
