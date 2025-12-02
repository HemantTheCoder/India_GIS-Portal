# gee_utils.py
"""
Earth Engine helper utilities for the India LULC portal.

Functions provided (all used by app.py):
- initialize_gee
- get_city_geometry
- get_sentinel2_image
- get_landsat_image
- get_dynamic_world_lulc
- calculate_ndvi_sentinel, calculate_ndwi_sentinel, calculate_ndbi_sentinel, calculate_evi_sentinel, calculate_savi_sentinel
- calculate_ndvi_landsat, calculate_ndwi_landsat, calculate_ndbi_landsat, calculate_evi_landsat, calculate_savi_landsat
- get_sentinel_rgb_params, get_landsat_rgb_params
- get_lulc_vis_params, get_index_vis_params
- get_tile_url
- calculate_lulc_statistics, calculate_lulc_statistics_with_area
- get_lulc_change_analysis
- get_safe_download_url, get_download_url, export_to_drive
- calculate_geometry_area, geojson_to_ee_geometry
- LULC_CLASSES, INDEX_INFO
"""

import ee
import json
from datetime import datetime

# ---------------------------
# Class & palette dictionaries
# ---------------------------
LULC_CLASSES = {
    0: {"name": "Water", "color": "#419BDF"},
    1: {"name": "Trees", "color": "#397D49"},
    2: {"name": "Grass", "color": "#88B053"},
    3: {"name": "Flooded Vegetation", "color": "#7A87C6"},
    4: {"name": "Crops", "color": "#E49635"},
    5: {"name": "Shrub & Scrub", "color": "#DFC35A"},
    6: {"name": "Built Area", "color": "#C4281B"},
    7: {"name": "Bare Ground", "color": "#A59B8F"},
    8: {"name": "Snow & Ice", "color": "#B39FE1"},
}

INDEX_INFO = {
    "NDVI": {
        "name": "Normalized Difference Vegetation Index",
        "description": "Measures vegetation health and density.",
        "palette": ["#d73027", "#fc8d59", "#fee08b", "#d9ef8b", "#91cf60", "#1a9850"],
    },
    "NDWI": {
        "name": "Normalized Difference Water Index",
        "description": "Detects water bodies and moisture content.",
        "palette": ["#ffffb2", "#fed976", "#feb24c", "#fd8d3c", "#f03b20", "#bd0026"],
    },
    "NDBI": {
        "name": "Normalized Difference Built-up Index",
        "description": "Identifies built-up/urban areas.",
        "palette": ["#fff7bc", "#fee391", "#fec44f", "#fe9929", "#ec7014", "#cc4c02"],
    },
    "EVI": {
        "name": "Enhanced Vegetation Index",
        "description": "Corrects for atmosphere and soil background.",
        "palette": ["#d73027", "#fc8d59", "#fee08b", "#d9ef8b", "#91cf60", "#1a9850"],
    },
    "SAVI": {
        "name": "Soil Adjusted Vegetation Index",
        "description": "Useful where vegetation is sparse.",
        "palette": ["#d73027", "#fc8d59", "#fee08b", "#d9ef8b", "#91cf60", "#1a9850"],
    },
}

# ---------------------------
# Initialization
# ---------------------------
def initialize_gee(service_account_key=None):
    """
    Initialize Earth Engine.
    - If service_account_key is provided it should be a parsed JSON dict (service account).
    - If None, attempt to initialize with default credentials.
    Returns True on success, False on error.
    """
    try:
        if service_account_key:
            client_email = service_account_key.get("client_email")
            key_data = json.dumps(service_account_key)
            try:
                # Preferred method when ee.ServiceAccountCredentials is available
                creds = ee.ServiceAccountCredentials(client_email, key_data=key_data)
                ee.Initialize(creds)
            except Exception:
                # Fallback to default initialization if service-account flow fails
                ee.Initialize()
        else:
            ee.Initialize()
        return True
    except Exception as e:
        print("GEE initialization error:", e)
        return False

# ---------------------------
# Geometry helpers
# ---------------------------
def get_city_geometry(lat, lon, buffer_km=15):
    """
    Return an ee.Geometry (bounded rectangle) representing a buffer_km-radius around lat/lon.
    """
    point = ee.Geometry.Point([lon, lat])
    buffer_m = buffer_km * 1000
    return point.buffer(buffer_m).bounds()

def geojson_to_ee_geometry(geojson_feature):
    """
    Convert a folium-draw GeoJSON feature (as returned by streamlit_folium) to an ee.Geometry.
    """
    try:
        if not isinstance(geojson_feature, dict):
            return None
        geom = geojson_feature.get("geometry") or {}
        gtype = geom.get("type")
        coords = geom.get("coordinates")
        props = geojson_feature.get("properties", {}) or {}
        if gtype == "Point":
            # coords = [lon, lat]
            pt = ee.Geometry.Point(coords)
            # radius (in meters) might be provided by draw plugin properties
            radius = props.get("radius") or props.get("radius_m")
            if radius:
                return pt.buffer(float(radius))
            return pt.buffer(1000)
        if gtype == "Polygon":
            return ee.Geometry.Polygon(coords)
        if gtype == "MultiPolygon":
            return ee.Geometry.MultiPolygon(coords)
        if gtype == "LineString":
            return ee.Geometry.LineString(coords).buffer(50)
        return None
    except Exception as e:
        print("geojson_to_ee_geometry error:", e)
        return None

def calculate_geometry_area(geometry):
    """
    Calculate area of ee.Geometry in km^2 (returns float)
    """
    try:
        area_sqm = geometry.area().getInfo()
        return round(area_sqm / 1e6, 2)
    except Exception as e:
        print("calculate_geometry_area error:", e)
        return None

# ---------------------------
# Cloud masking & compositing
# ---------------------------
def sentinel_cloud_mask_s2_sr(image):
    """
    Basic cloud/cirrus mask for S2 SR using QA60 band (bits 10 and 11).
    """
    try:
        qa = image.select("QA60")
        cloud_bit = 1 << 10
        cirrus_bit = 1 << 11
        mask = qa.bitwiseAnd(cloud_bit).eq(0).And(qa.bitwiseAnd(cirrus_bit).eq(0))
        return image.updateMask(mask).copyProperties(image, image.propertyNames())
    except Exception:
        return image

def get_sentinel2_image(geometry, start_date, end_date, max_cloud_percentage=20):
    """
    Retrieve Sentinel-2 SR composite clipped to geometry.
    Tries HARMONIZED collection then standard SR.
    """
    try:
        col = ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED").filterBounds(geometry).filterDate(start_date, end_date)
        # apply QA mask where available
        col = col.map(lambda im: sentinel_cloud_mask_s2_sr(im) if im.bandNames().contains("QA60") else im)
        col = col.filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", max_cloud_percentage))
        if col.size().getInfo() == 0:
            col = ee.ImageCollection("COPERNICUS/S2_SR").filterBounds(geometry).filterDate(start_date, end_date)
            col = col.map(sentinel_cloud_mask_s2_sr)
            col = col.filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", max_cloud_percentage))
        if col.size().getInfo() == 0:
            return None
        return col.median().clip(geometry)
    except Exception as e:
        print("get_sentinel2_image error:", e)
        return None

def landsat_cloud_mask_l2(image):
    """
    Attempt to mask clouds in Landsat Collection-2 Level-2 products using 'QA_PIXEL' or 'pixel_qa' flags.
    This is conservative; if flags unavailable, returns the image unchanged.
    """
    try:
        # If QA_PIXEL exists, the flag scheme is complicated; here we try a conservative approach.
        if image.bandNames().contains("QA_PIXEL"):
            # Many LC02 products include QA_PIXEL; leaving unmasked after initial cloud cover filter to avoid unexpected masking.
            return image
        if image.bandNames().contains("pixel_qa"):
            qa = image.select("pixel_qa")
            cloud_shadow = qa.bitwiseAnd(1 << 3).eq(0)
            cloud = qa.bitwiseAnd(1 << 5).eq(0)
            return image.updateMask(cloud_shadow.And(cloud))
        return image
    except Exception:
        return image

def get_landsat_image(geometry, start_date, end_date, max_cloud_cover=20):
    """
    Get median composite from Landsat Collection-2 L2: try LC09 then LC08.
    Output image uses SR_B* band names.
    """
    try:
        col = ee.ImageCollection("LANDSAT/LC09/C02/T1_L2").filterBounds(geometry).filterDate(start_date, end_date)
        col = col.filter(ee.Filter.lt("CLOUD_COVER", max_cloud_cover)).map(landsat_cloud_mask_l2)
        if col.size().getInfo() == 0:
            col = ee.ImageCollection("LANDSAT/LC08/C02/T1_L2").filterBounds(geometry).filterDate(start_date, end_date)
            col = col.filter(ee.Filter.lt("CLOUD_COVER", max_cloud_cover)).map(landsat_cloud_mask_l2)
        if col.size().getInfo() == 0:
            return None
        return col.median().clip(geometry)
    except Exception as e:
        print("get_landsat_image error:", e)
        return None

# ---------------------------
# Dynamic World LULC retrieval
# ---------------------------
def get_dynamic_world_lulc(geometry, start_date, end_date):
    """
    Return the mode (most-frequent) DynamicWorld 'label' image (values 0..8) for the period.
    """
    try:
        col = ee.ImageCollection("GOOGLE/DYNAMICWORLD/V1").filterBounds(geometry).filterDate(start_date, end_date).select("label")
        if col.size().getInfo() == 0:
            return None
        mode = col.mode().clip(geometry)
        return mode
    except Exception as e:
        print("get_dynamic_world_lulc error:", e)
        return None

# ---------------------------
# Index calculations (Sentinel & Landsat)
# ---------------------------
def calculate_ndvi_sentinel(image):
    return image.normalizedDifference(["B8", "B4"]).rename("NDVI")

def calculate_ndwi_sentinel(image):
    return image.normalizedDifference(["B3", "B8"]).rename("NDWI")

def calculate_ndbi_sentinel(image):
    return image.normalizedDifference(["B11", "B8"]).rename("NDBI")

def calculate_evi_sentinel(image):
    return image.expression(
        "2.5 * ((NIR - RED) / (NIR + 6 * RED - 7.5 * BLUE + 1))",
        {"NIR": image.select("B8"), "RED": image.select("B4"), "BLUE": image.select("B2")}
    ).rename("EVI")

def calculate_savi_sentinel(image, L=0.5):
    return image.expression(
        "((NIR - RED) / (NIR + RED + L)) * (1 + L)",
        {"NIR": image.select("B8"), "RED": image.select("B4"), "L": L}
    ).rename("SAVI")

def calculate_ndvi_landsat(image):
    return image.normalizedDifference(["SR_B5", "SR_B4"]).rename("NDVI")

def calculate_ndwi_landsat(image):
    return image.normalizedDifference(["SR_B3", "SR_B5"]).rename("NDWI")

def calculate_ndbi_landsat(image):
    return image.normalizedDifference(["SR_B6", "SR_B5"]).rename("NDBI")

def calculate_evi_landsat(image):
    return image.expression(
        "2.5 * ((NIR - RED) / (NIR + 6 * RED - 7.5 * BLUE + 1))",
        {"NIR": image.select("SR_B5"), "RED": image.select("SR_B4"), "BLUE": image.select("SR_B2")}
    ).rename("EVI")

def calculate_savi_landsat(image, L=0.5):
    return image.expression(
        "((NIR - RED) / (NIR + RED + L)) * (1 + L)",
        {"NIR": image.select("SR_B5"), "RED": image.select("SR_B4"), "L": L}
    ).rename("SAVI")

# ---------------------------
# Visualization parameter helpers
# ---------------------------
def get_sentinel_rgb_params(image):
    return {"bands": ["B4", "B3", "B2"], "min": 0, "max": 3000}

def get_landsat_rgb_params(image):
    return {"bands": ["SR_B4", "SR_B3", "SR_B2"], "min": 100, "max": 3000}

def get_lulc_vis_params():
    palette = [LULC_CLASSES[i]["color"] for i in range(len(LULC_CLASSES))]
    return {"min": 0, "max": len(LULC_CLASSES) - 1, "palette": palette}

def get_index_vis_params(index_name):
    info = INDEX_INFO.get(index_name, {})
    if index_name in ["NDVI", "EVI", "SAVI"]:
        return {"min": -0.2, "max": 0.8, "palette": info.get("palette", [])}
    if index_name in ["NDWI", "NDBI"]:
        return {"min": -0.5, "max": 0.5, "palette": info.get("palette", [])}
    return {"min": -1, "max": 1, "palette": info.get("palette", [])}

# ---------------------------
# Statistics & area calculations
# ---------------------------
def calculate_area_from_pixels(pixel_count, resolution=10):
    pixel_area_sqm = resolution * resolution
    area_sqm = pixel_count * pixel_area_sqm
    area_sqkm = area_sqm / 1_000_000
    return round(area_sqkm, 2)

def calculate_lulc_statistics(lulc_image, geometry, scale=10):
    """
    Returns dict: {class_name: {pixels, percentage, color}}
    """
    try:
        stats = lulc_image.reduceRegion(
            reducer=ee.Reducer.frequencyHistogram(),
            geometry=geometry,
            scale=scale,
            maxPixels=1e10
        )
        histogram = stats.get("label").getInfo() if stats else None
        if not histogram:
            return None
        total_pixels = sum(histogram.values())
        out = {}
        for cid, cnt in histogram.items():
            cid_int = int(float(cid))
            if cid_int in LULC_CLASSES:
                name = LULC_CLASSES[cid_int]["name"]
                color = LULC_CLASSES[cid_int]["color"]
                pct = (cnt / total_pixels) * 100
                out[name] = {"pixels": cnt, "percentage": round(pct, 2), "color": color}
        return out
    except Exception as e:
        print("calculate_lulc_statistics error:", e)
        return None

def calculate_lulc_statistics_with_area(lulc_image, geometry, resolution=10):
    """
    Returns {"classes": {name: {pixels, percentage, area_sqkm, color}}, "total_area_sqkm": float}
    """
    try:
        hist_res = lulc_image.reduceRegion(
            reducer=ee.Reducer.frequencyHistogram(),
            geometry=geometry,
            scale=resolution,
            maxPixels=1e10
        )
        histogram = hist_res.get("label").getInfo() if hist_res else None
        if not histogram:
            return None
        total_pixels = sum(histogram.values())
        total_area = calculate_area_from_pixels(total_pixels, resolution)
        classes = {}
        for cid, cnt in histogram.items():
            cid_int = int(float(cid))
            if cid_int in LULC_CLASSES:
                name = LULC_CLASSES[cid_int]["name"]
                color = LULC_CLASSES[cid_int]["color"]
                pct = (cnt / total_pixels) * 100
                area_km2 = calculate_area_from_pixels(cnt, resolution)
                classes[name] = {"pixels": cnt, "percentage": round(pct, 2), "area_sqkm": area_km2, "color": color}
        return {"classes": classes, "total_area_sqkm": total_area}
    except Exception as e:
        print("calculate_lulc_statistics_with_area error:", e)
        return None

def get_lulc_change_analysis(geometry, year1, year2):
    """
    Returns stats1, stats2, change_image
    """
    try:
        s1, e1 = f"{year1}-01-01", f"{year1}-12-31"
        s2, e2 = f"{year2}-01-01", f"{year2}-12-31"
        lulc1 = get_dynamic_world_lulc(geometry, s1, e1)
        lulc2 = get_dynamic_world_lulc(geometry, s2, e2)
        if lulc1 is None or lulc2 is None:
            return None, None, None
        stats1 = calculate_lulc_statistics_with_area(lulc1, geometry)
        stats2 = calculate_lulc_statistics_with_area(lulc2, geometry)
        change_image = lulc2.subtract(lulc1).rename("LULC_change")
        return stats1, stats2, change_image
    except Exception as e:
        print("get_lulc_change_analysis error:", e)
        return None, None, None

# ---------------------------
# Tiles & downloads
# ---------------------------
def get_tile_url(image, vis_params):
    """
    Return Earth Engine tile URL template for Leaflet:
    https://earthengine.googleapis.com/v1alpha/{mapid}/tiles/{z}/{x}/{y}?token={token}
    """
    try:
        mapid = ee.Image(image).getMapId(vis_params)
        # mapid may be dict-like or object with keys
        mid = mapid.get("mapid") if isinstance(mapid, dict) and "mapid" in mapid else mapid["mapid"]
        token = mapid.get("token") if isinstance(mapid, dict) and "token" in mapid else mapid["token"]
        url = f"https://earthengine.googleapis.com/v1alpha/{mid}/tiles/{{z}}/{{x}}/{{y}}?token={token}"
        return url
    except Exception as e:
        print("get_tile_url error:", e)
        try:
            mf = ee.Image(image).getMapId(vis_params)
            return mf["tile_fetcher"].url_format
        except Exception as e2:
            print("fallback tile URL error:", e2)
            return None

def get_download_url(image, geometry, scale=30, format_type="GEO_TIFF"):
    """
    Direct download URL (may be limited for large areas).
    """
    try:
        url = image.getDownloadURL({
            "name": "export",
            "scale": scale,
            "region": geometry,
            "format": format_type,
            "maxPixels": 1e10
        })
        return url
    except Exception as e:
        print("get_download_url error:", e)
        return None

def get_safe_download_url(image, geometry, scale=30, max_pixels=1e9):
    """
    Conservative guard before returning a direct download URL. Returns (url, None) or (None, error_message).
    """
    try:
        area_sqm = geometry.area().getInfo()
        area_km2 = area_sqm / 1e6
        # heuristics
        limit_km2 = 500 if scale <= 10 else 2000
        if area_km2 > limit_km2:
            return None, f"Selected area ({area_km2:.0f} km²) exceeds safe direct download limit ({limit_km2} km²). Reduce AOI or use Export to Drive."
        url = get_download_url(image, geometry, scale=scale, format_type="GEO_TIFF")
        if url:
            return url, None
        return None, "Could not generate download URL."
    except Exception as e:
        return None, f"get_safe_download_url error: {e}"

def export_to_drive(image, description, folder, geometry, scale=30):
    """
    Start a batch export to Google Drive. Returns task id or None.
    """
    try:
        task = ee.batch.Export.image.toDrive(
            image=image,
            description=description,
            folder=folder,
            region=geometry,
            scale=scale,
            maxPixels=1e10
        )
        task.start()
        return task.id
    except Exception as e:
        print("export_to_drive error:", e)
        return None
