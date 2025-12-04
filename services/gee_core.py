import ee
import json
import streamlit as st
import geopandas as gpd
import tempfile
import os
import zipfile

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
            return None, "Too many pixels. Try increasing the scale (resolution) value."
        if "must be less than or equal to" in error_msg:
            return None, "File too large (>50MB). Please increase the scale value to reduce file size."
        return None, f"Export error: {error_msg}"

def process_shapefile_upload(uploaded_files):
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            for uploaded_file in uploaded_files:
                file_path = os.path.join(tmpdir, uploaded_file.name)
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                if uploaded_file.name.endswith('.zip'):
                    with zipfile.ZipFile(file_path, 'r') as zip_ref:
                        zip_ref.extractall(tmpdir)
            
            shp_files = [f for f in os.listdir(tmpdir) if f.endswith('.shp')]
            
            if not shp_files:
                return None, None, "No .shp file found. Please upload a valid shapefile."
            
            shp_path = os.path.join(tmpdir, shp_files[0])
            gdf = gpd.read_file(shp_path)
            
            if gdf.crs and gdf.crs.to_epsg() != 4326:
                gdf = gdf.to_crs(epsg=4326)
            
            geometry = gdf.geometry.union_all()
            centroid = geometry.centroid
            
            coords = list(geometry.exterior.coords) if hasattr(geometry, 'exterior') else None
            if coords is None and hasattr(geometry, 'geoms'):
                all_coords = []
                for geom in geometry.geoms:
                    if hasattr(geom, 'exterior'):
                        all_coords.extend(list(geom.exterior.coords))
                coords = all_coords
            
            if coords:
                ee_geometry = ee.Geometry.Polygon([[[c[0], c[1]] for c in coords]])
            else:
                bounds = geometry.bounds
                ee_geometry = ee.Geometry.Rectangle([bounds[0], bounds[1], bounds[2], bounds[3]])
            
            center = {"lat": centroid.y, "lon": centroid.x}
            
            return ee_geometry, center, None
            
    except Exception as e:
        return None, None, f"Error processing shapefile: {str(e)}"

def geojson_file_to_ee_geometry(uploaded_file):
    try:
        content = uploaded_file.read().decode('utf-8')
        geojson = json.loads(content)
        
        if geojson.get("type") == "FeatureCollection":
            features = geojson.get("features", [])
            if features:
                geom = features[0].get("geometry", {})
            else:
                return None, None, "No features found in GeoJSON"
        elif geojson.get("type") == "Feature":
            geom = geojson.get("geometry", {})
        else:
            geom = geojson
        
        geom_type = geom.get("type", "")
        coords = geom.get("coordinates", [])
        
        if geom_type == "Polygon":
            ee_geometry = ee.Geometry.Polygon(coords)
        elif geom_type == "MultiPolygon":
            ee_geometry = ee.Geometry.MultiPolygon(coords)
        else:
            return None, None, f"Unsupported geometry type: {geom_type}"
        
        centroid = ee_geometry.centroid().getInfo()["coordinates"]
        center = {"lat": centroid[1], "lon": centroid[0]}
        
        return ee_geometry, center, None
        
    except Exception as e:
        return None, None, f"Error processing GeoJSON: {str(e)}"

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

def get_image_mean(image, geometry, scale=30):
    try:
        result = image.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=geometry,
            scale=scale,
            maxPixels=1e9
        ).getInfo()
        return result
    except Exception as e:
        print(f"Error calculating mean: {e}")
        return None
