import ee
import json
import streamlit as st
import geopandas as gpd
import tempfile
import os
import zipfile


def format_gee_error(e):
    """Returns a user-friendly error message for common GEE exceptions."""
    error_msg = str(e)
    if "Quota exceeded" in error_msg:
        return "GEE Quota Exceeded. Please wait a moment and try again."
    if "Too many pixels" in error_msg:
        return "Region too large. Please reduce the area or increase scale."
    if "Computation timed out" in error_msg:
        return "Computation timed out. The analysis is too complex for this region."
    if "User memory limit exceeded" in error_msg:
        return "Memory limit exceeded. Try a smaller area."
    if "Invalid JSON" in error_msg:
        return "Invalid Service Account Credentials."
    return f"GEE Error: {error_msg}"


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
        st.session_state.gee_error = format_gee_error(e)
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
        return None, format_gee_error(e)


def optimize_geometry(geometry, max_vertices=5000):
    """
    Simplifies geometry if it exceeds the vertex threshold.
    Preserves topology while reducing payload size for GEE.
    """
    try:
        # Calculate total vertices
        if hasattr(geometry, "geoms"):  # MultiPolygon/GeometryCollection
            total_coords = sum(len(g.exterior.coords) + sum(len(i.coords) for i in g.interiors) for g in geometry.geoms)
        else:  # Polygon/Point/LineString
            total_coords = len(geometry.exterior.coords) + sum(len(i.coords) for i in geometry.interiors)

        if total_coords > max_vertices:
            print(f"Geometry has {total_coords} vertices. Simplifying...")
            # Tolerance in degrees. 0.0001 is approx 11 meters at equator.
            # Start subtle.
            simplified = geometry.simplify(tolerance=0.001, preserve_topology=True)
            return simplified
        return geometry
    except Exception as e:
        print(f"Error optimizing geometry: {e}")
        return geometry


def _geometry_to_ee(geometry):
    """
    Helper to reliably convert shapely geometry to ee.Geometry
    """
    try:
        # Optimize geometry first to avoid payload errors
        geometry = optimize_geometry(geometry)

        # Convert to GeoJSON dict/feature
        if hasattr(geometry, "__geo_interface__"):
            geojson = geometry.__geo_interface__
        else:
            return None, "Invalid geometry object"

        type_ = geojson.get("type")
        coords = geojson.get("coordinates")

        if type_ == "Polygon":
            return ee.Geometry.Polygon(coords), None
        elif type_ == "MultiPolygon":
            return ee.Geometry.MultiPolygon(coords), None
        elif type_ == "Point":
            return ee.Geometry.Point(coords).buffer(
                1000), None  # Default buffer for points
        else:
            # Fallback for others
            return ee.Geometry(geojson), None

    except Exception as e:
        return None, str(e)


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
                return None, None, None, "No .shp file found. Please upload a valid shapefile."

            shp_path = os.path.join(tmpdir, shp_files[0])
            gdf = gpd.read_file(shp_path)

            if gdf.crs and gdf.crs.to_epsg() != 4326:
                gdf = gdf.to_crs(epsg=4326)

            # Combine all features into one geometry (Union)
            # Use unary_union which is standard for merging all geometries in a GDF
            geometry = gdf.unary_union

            # Get centroid for map centering
            centroid = geometry.centroid
            center = {"lat": centroid.y, "lon": centroid.x}

            # Get plain GeoJSON for frontend display if needed
            geojson_data = json.loads(gpd.GeoSeries([geometry]).to_json())

            # Convert to Earth Engine Geometry
            ee_geometry, error = _geometry_to_ee(geometry)

            if error:
                # Fallback: Try bounds if complex conversion fails (though unlikely with unicary_union)
                bounds = geometry.bounds
                ee_geometry = ee.Geometry.Rectangle(
                    [bounds[0], bounds[1], bounds[2], bounds[3]])

            return ee_geometry, center, geojson_data, None

    except Exception as e:
        return None, None, None, f"Error processing shapefile: {str(e)}"


def geojson_file_to_ee_geometry(uploaded_file):
    try:
        content = uploaded_file.read().decode('utf-8')
        geojson = json.loads(content)

        # Handle FeatureCollection: Merge all geometries
        if geojson.get("type") == "FeatureCollection":
            features = geojson.get("features", [])
            if not features:
                return None, None, None, "No features found in GeoJSON"

            # Simple approach: Load into GeoDataFrame to handle merging easily
            # This is robust because GPD handles CRS and topology
            gdf = gpd.GeoDataFrame.from_features(features)
            if not gdf.crs:
                gdf.set_crs(epsg=4326, inplace=True)  # Assume 4326 if missing
            elif gdf.crs.to_epsg() != 4326:
                gdf = gdf.to_crs(epsg=4326)

            geometry = gdf.unary_union

        elif geojson.get("type") == "Feature":
            # load as single feature gdf
            gdf = gpd.GeoDataFrame.from_features([geojson])
            if not gdf.crs: gdf.set_crs(epsg=4326, inplace=True)
            geometry = gdf.unary_union

        else:
            # Just geometry
            # Create a dummy feature to load into GPD or handle directly
            # Handling directly is riskier if it's complex, let's wrap in feature
            feature = {
                "type": "Feature",
                "geometry": geojson,
                "properties": {}
            }
            gdf = gpd.GeoDataFrame.from_features([feature])
            if not gdf.crs: gdf.set_crs(epsg=4326, inplace=True)
            geometry = gdf.unary_union

        # Extract centroid
        centroid = geometry.centroid
        center = {"lat": centroid.y, "lon": centroid.x}

        # Convert to EE
        ee_geometry, error = _geometry_to_ee(geometry)

        if error:
            return None, None, None, f"Geometry Conversion Error: {error}"

        return ee_geometry, center, geojson, None

    except Exception as e:
        return None, None, None, f"Error processing GeoJSON: {str(e)}"


def sample_pixel_value(image, lat, lon, scale=10):
    try:
        point = ee.Geometry.Point([lon, lat])
        result = image.reduceRegion(reducer=ee.Reducer.first(),
                                    geometry=point,
                                    scale=scale).getInfo()
        return result
    except Exception as e:
        print(f"Error sampling pixel: {e}")
        return None


def get_image_mean(image, geometry, scale=30):
    try:
        result = image.reduceRegion(reducer=ee.Reducer.mean(),
                                    geometry=geometry,
                                    scale=scale,
                                    maxPixels=1e9).getInfo()
        return result
    except Exception as e:
        print(f"Error calculating mean: {e}")
        return None
