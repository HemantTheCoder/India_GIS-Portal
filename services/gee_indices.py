import ee

INDEX_INFO = {
    "NDVI": {
        "name": "Normalized Difference Vegetation Index",
        "description": "Measures vegetation health and density",
        "palette": ["#d73027", "#fc8d59", "#fee08b", "#d9ef8b", "#91cf60", "#1a9850"],
        "min": -1,
        "max": 1,
    },
    "NDWI": {
        "name": "Normalized Difference Water Index",
        "description": "Detects water bodies and moisture content",
        "palette": ["#ffffcc", "#a1dab4", "#41b6c4", "#2c7fb8", "#253494"],
        "min": -1,
        "max": 1,
    },
    "NDBI": {
        "name": "Normalized Difference Built-up Index",
        "description": "Identifies built-up/urban areas",
        "palette": ["#ffffb2", "#fecc5c", "#fd8d3c", "#f03b20", "#bd0026"],
        "min": -1,
        "max": 1,
    },
    "EVI": {
        "name": "Enhanced Vegetation Index",
        "description": "Enhanced vegetation index with atmospheric correction",
        "palette": ["#d73027", "#fc8d59", "#fee08b", "#d9ef8b", "#91cf60", "#1a9850"],
        "min": -1,
        "max": 1,
    },
    "SAVI": {
        "name": "Soil Adjusted Vegetation Index",
        "description": "Minimizes soil brightness influences",
        "palette": ["#d73027", "#fc8d59", "#fee08b", "#d9ef8b", "#91cf60", "#1a9850"],
        "min": 0,
        "max": 1,
    },
}

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

def calculate_savi_sentinel(image, L=0.5):
    savi = image.expression(
        "((NIR - RED) / (NIR + RED + L)) * (1 + L)",
        {
            "NIR": image.select("B8"),
            "RED": image.select("B4"),
            "L": L,
        }
    ).rename("SAVI")
    return savi

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

def calculate_savi_landsat(image, L=0.5):
    savi = image.expression(
        "((NIR - RED) / (NIR + RED + L)) * (1 + L)",
        {
            "NIR": image.select("SR_B5"),
            "RED": image.select("SR_B4"),
            "L": L,
        }
    ).rename("SAVI")
    return savi

def get_index_vis_params(index_name):
    info = INDEX_INFO.get(index_name, {})
    return {
        "min": info.get("min", -1),
        "max": info.get("max", 1),
        "palette": info.get("palette", [])
    }

def get_index_functions(satellite="Sentinel-2"):
    if satellite == "Sentinel-2":
        return {
            "NDVI": calculate_ndvi_sentinel,
            "NDWI": calculate_ndwi_sentinel,
            "NDBI": calculate_ndbi_sentinel,
            "EVI": calculate_evi_sentinel,
            "SAVI": calculate_savi_sentinel,
        }
    else:
        return {
            "NDVI": calculate_ndvi_landsat,
            "NDWI": calculate_ndwi_landsat,
            "NDBI": calculate_ndbi_landsat,
            "EVI": calculate_evi_landsat,
            "SAVI": calculate_savi_landsat,
        }
