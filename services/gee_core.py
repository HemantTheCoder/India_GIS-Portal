import ee
import json
import streamlit as st

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

def auto_initialize_gee():
    if not st.session_state.get("gee_initialized", False):
        try:
            if "GEE_JSON" in st.secrets:
                key_data = dict(st.secrets["GEE_JSON"])
                if initialize_gee(key_data):
                    st.session_state.gee_initialized = True
                else:
                    st.session_state.gee_initialized = False
            else:
                st.session_state.gee_initialized = False
        except Exception as e:
            st.session_state.gee_initialized = False

def get_city_geometry(lat, lon, buffer_km=15):
    point = ee.Geometry.Point([lon, lat])
    buffer_meters = buffer_km * 1000
    return point.buffer(buffer_meters).bounds()

def get_tile_url(image, vis_params):
    map_id = image.getMapId(vis_params)
    return map_id["tile_fetcher"].url_format

def calculate_geometry_area(geometry):
    try:
        area_sqm = geometry.area(maxError=1).getInfo()
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

def get_safe_download_url(image, geometry, scale=30, max_pixels=5e8):
    try:
        url = image.getDownloadURL({
            "name": "export",
            "scale": scale,
            "region": geometry,
            "format": "GEO_TIFF",
            "maxPixels": max_pixels,
        })
        return url, None
    except Exception as e:
        error_msg = str(e)
        if "Too many pixels" in error_msg:
            return None, "Area too large for direct download. Try reducing the buffer radius or use a coarser scale."
        return None, f"Export error: {error_msg}"

def sample_pixel_value(image, lat, lon, scale=10):
    try:
        point = ee.Geometry.Point([lon, lat])
        result = image.reduceRegion(
            reducer=ee.Reducer.first(),
            geometry=point,
            scale=scale
        ).getInfo()
        return result
    except Exception as e:
        print(f"Error sampling pixel: {e}")
        return None
