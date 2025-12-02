import ee
import json
import os
from datetime import datetime

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
        "description": "Measures vegetation health and density. Values range from -1 to 1, where higher values indicate denser vegetation.",
        "palette": ["#d73027", "#fc8d59", "#fee08b", "#d9ef8b", "#91cf60", "#1a9850"],
    },
    "NDWI": {
        "name": "Normalized Difference Water Index",
        "description": "Detects water bodies and moisture content. Higher values indicate more water presence.",
        "palette": ["#ffffb2", "#fed976", "#feb24c", "#fd8d3c", "#f03b20", "#bd0026"],
    },
    "NDBI": {
        "name": "Normalized Difference Built-up Index",
        "description": "Identifies built-up/urban areas. Higher values indicate more built-up surfaces.",
        "palette": ["#fff7bc", "#fee391", "#fec44f", "#fe9929", "#ec7014", "#cc4c02"],
    },
    "EVI": {
        "name": "Enhanced Vegetation Index",
        "description": "Enhanced vegetation index that corrects for atmospheric conditions and soil background.",
        "palette": ["#d73027", "#fc8d59", "#fee08b", "#d9ef8b", "#91cf60", "#1a9850"],
    },
}

def initialize_gee(service_account_key=None):
    try:
        if service_account_key:
            credentials = ee.ServiceAccountCredentials(
                service_account_key.get("client_email", ""),
                key_data=json.dumps(service_account_key)
            )
            ee.Initialize(credentials)
        else:
            ee.Initialize()
        return True
    except Exception as e:
        print(f"GEE initialization error: {e}")
        return False

def get_city_geometry(lat, lon, buffer_km=15):
    point = ee.Geometry.Point([lon, lat])
    buffer_meters = buffer_km * 1000
    return point.buffer(buffer_meters).bounds()

def get_sentinel2_image(geometry, start_date, end_date):
    collection = (
        ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
        .filterBounds(geometry)
        .filterDate(start_date, end_date)
        .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 20))
        .sort("CLOUDY_PIXEL_PERCENTAGE")
    )
    
    if collection.size().getInfo() == 0:
        return None
    
    image = collection.median().clip(geometry)
    return image

def get_landsat_image(geometry, start_date, end_date):
    collection = (
        ee.ImageCollection("LANDSAT/LC09/C02/T1_L2")
        .filterBounds(geometry)
        .filterDate(start_date, end_date)
        .filter(ee.Filter.lt("CLOUD_COVER", 20))
        .sort("CLOUD_COVER")
    )
    
    if collection.size().getInfo() == 0:
        collection = (
            ee.ImageCollection("LANDSAT/LC08/C02/T1_L2")
            .filterBounds(geometry)
            .filterDate(start_date, end_date)
            .filter(ee.Filter.lt("CLOUD_COVER", 20))
            .sort("CLOUD_COVER")
        )
    
    if collection.size().getInfo() == 0:
        return None
    
    image = collection.median().clip(geometry)
    return image

def get_dynamic_world_lulc(geometry, start_date, end_date):
    collection = (
        ee.ImageCollection("GOOGLE/DYNAMICWORLD/V1")
        .filterBounds(geometry)
        .filterDate(start_date, end_date)
    )
    
    if collection.size().getInfo() == 0:
        return None
    
    classification = collection.select("label")
    mode_lulc = classification.mode().clip(geometry)
    
    return mode_lulc

def calculate_ndvi_sentinel(image):
    ndvi = image.normalizedDifference(["B8", "B4"]).rename("NDVI")
    return ndvi

def calculate_ndwi_sentinel(image):
    ndwi = image.normalizedDifference(["B3", "B8"]).rename("NDWI")
    return ndwi

def calculate_ndbi_sentinel(image):
    ndbi = image.normalizedDifference(["B11", "B8"]).rename("NDBI")
    return ndbi

def calculate_evi_sentinel(image):
    evi = image.expression(
        "2.5 * ((NIR - RED) / (NIR + 6 * RED - 7.5 * BLUE + 1))",
        {
            "NIR": image.select("B8"),
            "RED": image.select("B4"),
            "BLUE": image.select("B2"),
        }
    ).rename("EVI")
    return evi

def calculate_ndvi_landsat(image):
    ndvi = image.normalizedDifference(["SR_B5", "SR_B4"]).rename("NDVI")
    return ndvi

def calculate_ndwi_landsat(image):
    ndwi = image.normalizedDifference(["SR_B3", "SR_B5"]).rename("NDWI")
    return ndwi

def calculate_ndbi_landsat(image):
    ndbi = image.normalizedDifference(["SR_B6", "SR_B5"]).rename("NDBI")
    return ndbi

def calculate_evi_landsat(image):
    evi = image.expression(
        "2.5 * ((NIR - RED) / (NIR + 6 * RED - 7.5 * BLUE + 1))",
        {
            "NIR": image.select("SR_B5"),
            "RED": image.select("SR_B4"),
            "BLUE": image.select("SR_B2"),
        }
    ).rename("EVI")
    return evi

def get_sentinel_rgb_params(image):
    return {
        "bands": ["B4", "B3", "B2"],
        "min": 0,
        "max": 3000,
    }

def get_landsat_rgb_params(image):
    return {
        "bands": ["SR_B4", "SR_B3", "SR_B2"],
        "min": 5000,
        "max": 15000,
    }

def get_lulc_vis_params():
    return {
        "min": 0,
        "max": 8,
        "palette": [LULC_CLASSES[i]["color"] for i in range(9)],
    }

def get_index_vis_params(index_name):
    info = INDEX_INFO.get(index_name, {})
    if index_name in ["NDVI", "EVI"]:
        return {"min": -0.2, "max": 0.8, "palette": info.get("palette", [])}
    elif index_name == "NDWI":
        return {"min": -0.5, "max": 0.5, "palette": info.get("palette", [])}
    elif index_name == "NDBI":
        return {"min": -0.5, "max": 0.5, "palette": info.get("palette", [])}
    return {"min": -1, "max": 1, "palette": info.get("palette", [])}

def calculate_lulc_statistics(lulc_image, geometry):
    try:
        stats = lulc_image.reduceRegion(
            reducer=ee.Reducer.frequencyHistogram(),
            geometry=geometry,
            scale=10,
            maxPixels=1e9
        )
        
        histogram = stats.get("label").getInfo()
        if histogram is None:
            return None
        
        total_pixels = sum(histogram.values())
        result = {}
        
        for class_id, count in histogram.items():
            class_id = int(float(class_id))
            if class_id in LULC_CLASSES:
                percentage = (count / total_pixels) * 100
                result[LULC_CLASSES[class_id]["name"]] = {
                    "pixels": count,
                    "percentage": round(percentage, 2),
                    "color": LULC_CLASSES[class_id]["color"],
                }
        
        return result
    except Exception as e:
        print(f"Error calculating statistics: {e}")
        return None

def get_tile_url(image, vis_params):
    map_id = image.getMapId(vis_params)
    return map_id["tile_fetcher"].url_format
