import ee
import json
import os
import math
from datetime import datetime

LULC_CLASSES = {
    0: {
        "name": "Water",
        "color": "#419BDF"
    },
    1: {
        "name": "Trees",
        "color": "#397D49"
    },
    2: {
        "name": "Grass",
        "color": "#88B053"
    },
    3: {
        "name": "Flooded Vegetation",
        "color": "#7A87C6"
    },
    4: {
        "name": "Crops",
        "color": "#E49635"
    },
    5: {
        "name": "Shrub & Scrub",
        "color": "#DFC35A"
    },
    6: {
        "name": "Built Area",
        "color": "#C4281B"
    },
    7: {
        "name": "Bare Ground",
        "color": "#A59B8F"
    },
    8: {
        "name": "Snow & Ice",
        "color": "#B39FE1"
    },
}

INDEX_INFO = {
    "NDVI": {
        "name":
        "Normalized Difference Vegetation Index",
        "description":
        "Measures vegetation health and density. Values range from -1 to 1, where higher values indicate denser vegetation.",
        "palette":
        ["#d73027", "#fc8d59", "#fee08b", "#d9ef8b", "#91cf60", "#1a9850"],
    },
    "NDWI": {
        "name":
        "Normalized Difference Water Index",
        "description":
        "Detects water bodies and moisture content. Higher values indicate more water presence.",
        "palette":
        ["#ffffb2", "#fed976", "#feb24c", "#fd8d3c", "#f03b20", "#bd0026"],
    },
    "NDBI": {
        "name":
        "Normalized Difference Built-up Index",
        "description":
        "Identifies built-up/urban areas. Higher values indicate more built-up surfaces.",
        "palette":
        ["#fff7bc", "#fee391", "#fec44f", "#fe9929", "#ec7014", "#cc4c02"],
    },
    "EVI": {
        "name":
        "Enhanced Vegetation Index",
        "description":
        "Enhanced vegetation index that corrects for atmospheric conditions and soil background.",
        "palette":
        ["#d73027", "#fc8d59", "#fee08b", "#d9ef8b", "#91cf60", "#1a9850"],
    },
    "SAVI": {
        "name":
        "Soil Adjusted Vegetation Index",
        "description":
        "Minimizes soil brightness influences from spectral vegetation indices. Useful for areas with sparse vegetation.",
        "palette":
        ["#d73027", "#fc8d59", "#fee08b", "#d9ef8b", "#91cf60", "#1a9850"],
    },
}


def initialize_gee(service_account_key=None):
    try:
        if service_account_key:
            credentials = ee.ServiceAccountCredentials(
                service_account_key.get("client_email", ""),
                key_data=json.dumps(service_account_key))
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
    collection = (ee.ImageCollection(
        "COPERNICUS/S2_SR_HARMONIZED").filterBounds(geometry).filterDate(
            start_date,
            end_date).filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE",
                                          20)).sort("CLOUDY_PIXEL_PERCENTAGE"))

    if collection.size().getInfo() == 0:
        return None

    image = collection.median().clip(geometry)
    return image


def get_landsat_image(geometry, start_date, end_date):
    collection = (ee.ImageCollection("LANDSAT/LC09/C02/T1_L2").filterBounds(
        geometry).filterDate(start_date, end_date).filter(
            ee.Filter.lt("CLOUD_COVER", 20)).sort("CLOUD_COVER"))

    if collection.size().getInfo() == 0:
        collection = (ee.ImageCollection(
            "LANDSAT/LC08/C02/T1_L2").filterBounds(geometry).filterDate(
                start_date,
                end_date).filter(ee.Filter.lt("CLOUD_COVER",
                                              20)).sort("CLOUD_COVER"))

    if collection.size().getInfo() == 0:
        return None

    image = collection.median().clip(geometry)
    return image


def get_dynamic_world_lulc(geometry, start_date, end_date):
    collection = (ee.ImageCollection("GOOGLE/DYNAMICWORLD/V1").filterBounds(
        geometry).filterDate(start_date, end_date))

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
        "2.5 * ((NIR - RED) / (NIR + 6 * RED - 7.5 * BLUE + 1))", {
            "NIR": image.select("B8"),
            "RED": image.select("B4"),
            "BLUE": image.select("B2"),
        }).rename("EVI")
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
        "2.5 * ((NIR - RED) / (NIR + 6 * RED - 7.5 * BLUE + 1))", {
            "NIR": image.select("SR_B5"),
            "RED": image.select("SR_B4"),
            "BLUE": image.select("SR_B2"),
        }).rename("EVI")
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
    if index_name in ["NDVI", "EVI", "SAVI"]:
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
            maxPixels=1e9)

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


def calculate_savi_sentinel(image, L=0.5):
    savi = image.expression("((NIR - RED) / (NIR + RED + L)) * (1 + L)", {
        "NIR": image.select("B8"),
        "RED": image.select("B4"),
        "L": L,
    }).rename("SAVI")
    return savi


def calculate_savi_landsat(image, L=0.5):
    savi = image.expression("((NIR - RED) / (NIR + RED + L)) * (1 + L)", {
        "NIR": image.select("SR_B5"),
        "RED": image.select("SR_B4"),
        "L": L,
    }).rename("SAVI")
    return savi


def calculate_area_from_pixels(pixel_count, resolution=10):
    pixel_area_sqm = resolution * resolution
    area_sqm = pixel_count * pixel_area_sqm
    area_sqkm = area_sqm / 1_000_000
    return round(area_sqkm, 2)


def calculate_lulc_statistics_with_area(lulc_image, geometry, resolution=10):
    try:
        stats = lulc_image.reduceRegion(
            reducer=ee.Reducer.frequencyHistogram(),
            geometry=geometry,
            scale=resolution,
            maxPixels=1e9)

        histogram = stats.get("label").getInfo()
        if histogram is None:
            return None

        total_pixels = sum(histogram.values())
        total_area_sqkm = calculate_area_from_pixels(total_pixels, resolution)
        result = {}

        for class_id, count in histogram.items():
            class_id = int(float(class_id))
            if class_id in LULC_CLASSES:
                percentage = (count / total_pixels) * 100
                area_sqkm = calculate_area_from_pixels(count, resolution)
                result[LULC_CLASSES[class_id]["name"]] = {
                    "pixels": count,
                    "percentage": round(percentage, 2),
                    "area_sqkm": area_sqkm,
                    "color": LULC_CLASSES[class_id]["color"],
                }

        return {"classes": result, "total_area_sqkm": total_area_sqkm}
    except Exception as e:
        print(f"Error calculating statistics: {e}")
        return None


def get_lulc_change_analysis(geometry, year1, year2):
    start1 = f"{year1}-01-01"
    end1 = f"{year1}-12-31"
    start2 = f"{year2}-01-01"
    end2 = f"{year2}-12-31"

    lulc1 = get_dynamic_world_lulc(geometry, start1, end1)
    lulc2 = get_dynamic_world_lulc(geometry, start2, end2)

    if lulc1 is None or lulc2 is None:
        return None, None, None

    stats1 = calculate_lulc_statistics_with_area(lulc1, geometry)
    stats2 = calculate_lulc_statistics_with_area(lulc2, geometry)

    change_image = lulc2.subtract(lulc1)

    return stats1, stats2, change_image


def get_download_url(image, geometry, scale=30, format_type="GEO_TIFF"):
    try:
        url = image.getDownloadURL({
            "name": "export",
            "scale": scale,
            "region": geometry,
            "format": format_type,
            "maxPixels": 1e9,
        })
        return url
    except Exception as e:
        print(f"Error generating download URL: {e}")
        return None


def export_to_drive(image, description, folder, geometry, scale=30):
    try:
        task = ee.batch.Export.image.toDrive(image=image,
                                             description=description,
                                             folder=folder,
                                             region=geometry,
                                             scale=scale,
                                             maxPixels=1e9)
        task.start()
        return task.id
    except Exception as e:
        print(f"Error starting export: {e}")
        return None


def calculate_geometry_area(geometry):
    try:
        area_sqm = geometry.area().getInfo()
        area_sqkm = area_sqm / 1_000_000
        return round(area_sqkm, 2)
    except Exception as e:
        print(f"Error calculating geometry area: {e}")
        return None


def geojson_to_ee_geometry(geojson_feature):
    try:
        if isinstance(geojson_feature, dict):
            geom_type = geojson_feature.get("geometry", {}).get("type", "")
            coords = geojson_feature.get("geometry", {}).get("coordinates", [])
            properties = geojson_feature.get("properties", {})

            radius = properties.get("radius")
            if radius and geom_type == "Point":
                return ee.Geometry.Point(coords).buffer(radius)

            if geom_type == "Polygon":
                return ee.Geometry.Polygon(coords)
            elif geom_type == "Rectangle":
                return ee.Geometry.Rectangle(coords)
            elif geom_type == "Point":
                return ee.Geometry.Point(coords).buffer(1000)
            else:
                if coords:
                    return ee.Geometry.Polygon(coords)
                return None
        return None
    except Exception as e:
        print(f"Error converting GeoJSON to EE geometry: {e}")
        return None


def get_safe_download_url(image, geometry, scale=30, max_pixels=1e8):
    try:
        area = geometry.area().getInfo()
        area_sqkm = area / 1_000_000

        if scale == 10:
            max_area_for_direct = 500
        else:
            max_area_for_direct = 2000

        if area_sqkm > max_area_for_direct:
            return None, f"Area too large ({area_sqkm:.0f} km²). Max allowed: {max_area_for_direct} km². Try a smaller region."

        url = image.getDownloadURL({
            "name": "export",
            "scale": scale,
            "region": geometry,
            "format": "GEO_TIFF",
            "maxPixels": max_pixels,
        })
        return url, None
    except Exception as e:
        return None, f"Export error: {str(e)}"
