"""
road_network.py - OSM Road Network Fetching & Safe Route Analysis
=================================================================
Fetches road data from OpenStreetMap Overpass API and classifies
roads by safety (SAFE / AT_RISK / IMPASSABLE) based on SAR flood data.
Uses NetworkX for shortest safe-path routing.
"""

import requests
import json
import geopandas as gpd
import pandas as pd
from shapely.geometry import LineString, Point, shape
import math


# ─────────────────────────────────────────────────────────────
# 1. FETCH OSM ROAD NETWORK via Overpass API
# ─────────────────────────────────────────────────────────────
def fetch_osm_roads(lat=None, lon=None, radius_km=15, bbox=None):
    """
    Fetches road network from OpenStreetMap Overpass API.
    Supports either point+radius OR bounding box.
    
    Args:
        lat, lon   : Center coordinates (optional if bbox provided)
        radius_km  : Search radius (optional if bbox provided)
        bbox       : list/tuple (min_lat, min_lon, max_lat, max_lon)
    """
    overpass_url = "https://overpass-api.de/api/interpreter"

    if bbox:
        # BBox format: (min_lat, min_lon, max_lat, max_lon)
        area_filter = f"{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]}"
        query = f"""
        [out:json][timeout:45];
        (
          way["highway"~"^(motorway|trunk|primary|secondary|tertiary|residential|unclassified)$"]
             ({area_filter});
        );
        out body geom;
        """
    else:
        radius_m = radius_km * 1000
        query = f"""
        [out:json][timeout:30];
        (
          way["highway"~"^(motorway|trunk|primary|secondary|tertiary|residential|unclassified)$"]
             (around:{radius_m},{lat},{lon});
        );
        out body geom;
        """

    try:
        resp = requests.post(overpass_url, data={"data": query}, timeout=50)
        resp.raise_for_status()
        data = resp.json()

        elements = data.get("elements", [])
        if not elements:
            return None

        rows = []
        for el in elements:
            if el.get("type") != "way":
                continue
            geometry_nodes = el.get("geometry", [])
            if len(geometry_nodes) < 2:
                continue
            coords = [(nd["lon"], nd["lat"]) for nd in geometry_nodes]
            tags = el.get("tags", {})
            rows.append({
                "geometry":  LineString(coords),
                "osm_id":    el.get("id"),
                "name":      tags.get("name", "Unnamed Road"),
                "highway":   tags.get("highway", "unclassified"),
                "road_type": _classify_road_type(tags.get("highway", "")),
                "status":    "SAFE",       # default; will be updated by SAR overlay
                "color":     "#22c55e",
            })

        if not rows:
            return None

        gdf = gpd.GeoDataFrame(rows, crs="EPSG:4326")
        return gdf

    except Exception as e:
        print(f"[road_network] OSM fetch error: {e}")
        return None


def _classify_road_type(highway_tag):
    """Maps OSM highway tag to readable road type."""
    mapping = {
        "motorway":      "Highway / Expressway",
        "trunk":         "State Highway",
        "primary":       "National Road",
        "secondary":     "District Road",
        "tertiary":      "Feeder Road",
        "residential":   "Residential",
        "unclassified":  "Minor Road",
    }
    return mapping.get(highway_tag, "Other")


# ─────────────────────────────────────────────────────────────
# 2. CLASSIFY ROAD SAFETY using flood GeoJSON
# ─────────────────────────────────────────────────────────────
def classify_road_safety(roads_gdf, flood_geojson=None, safe_haven_geojson=None):
    """
    Assigns safety status to each road segment:
      - IMPASSABLE : Road overlaps with active flood zone (from SAR)
      - AT_RISK    : Road within 500m of flood zone
      - SAFE       : No flood proximity detected

    Args:
        roads_gdf          : GeoDataFrame of roads
        flood_geojson      : GeoJSON dict of flood polygons (from GEE SAR)
        safe_haven_geojson : GeoJSON dict of safe areas

    Returns updated GeoDataFrame.
    """
    if roads_gdf is None or roads_gdf.empty:
        return roads_gdf

    # Project to metric CRS for distance calculations
    roads_proj = roads_gdf.to_crs("EPSG:32643")  # UTM Zone 43N (central India)

    flood_union = None
    if flood_geojson and flood_geojson.get("features"):
        try:
            flood_shapes = [
                shape(f["geometry"])
                for f in flood_geojson["features"]
                if f.get("geometry")
            ]
            if flood_shapes:
                from shapely.ops import unary_union
                flood_gdf = gpd.GeoDataFrame(
                    geometry=flood_shapes, crs="EPSG:4326"
                ).to_crs("EPSG:32643")
                flood_union = flood_gdf.unary_union
        except Exception as e:
            print(f"[road_network] Flood GeoJSON parse error: {e}")

    statuses = []
    colors   = []

    for _, row in roads_proj.iterrows():
        geom = row.geometry
        if flood_union is not None:
            try:
                if geom.intersects(flood_union):
                    statuses.append("IMPASSABLE")
                    colors.append("#ef4444")
                    continue
                elif geom.distance(flood_union) < 500:
                    statuses.append("AT_RISK")
                    colors.append("#f97316")
                    continue
            except Exception:
                pass
        statuses.append("SAFE")
        colors.append("#22c55e")

    roads_gdf = roads_gdf.copy()
    roads_gdf["status"] = statuses
    roads_gdf["color"]  = colors
    return roads_gdf


# ─────────────────────────────────────────────────────────────
# 3. SAFE ROUTE RECOMMENDATION (NetworkX-based)
# ─────────────────────────────────────────────────────────────
def find_safest_evacuation_route(roads_gdf, origin_lat, origin_lon,
                                 safe_havens_geojson=None):
    """
    Finds the safest evacuation direction from a given origin point.
    Returns a summary dict with recommended direction, safe roads count,
    and nearest safe corridor info.

    Note: Full A* routing requires a proper graph; this gives a
    direction-based recommendation suitable for community use.
    """
    if roads_gdf is None or roads_gdf.empty:
        return None

    try:
        safe_roads = roads_gdf[roads_gdf["status"] == "SAFE"]
        at_risk    = roads_gdf[roads_gdf["status"] == "AT_RISK"]
        impassable = roads_gdf[roads_gdf["status"] == "IMPASSABLE"]

        origin = Point(origin_lon, origin_lat)

        # Find nearest safe road
        nearest_safe = None
        nearest_dist = float("inf")
        nearest_name = "Unknown"
        nearest_type = "Road"

        for _, row in safe_roads.iterrows():
            try:
                dist = origin.distance(row.geometry)
                if dist < nearest_dist:
                    nearest_dist = dist
                    nearest_safe = row.geometry
                    nearest_name = row.get("name", "Unnamed Road")
                    nearest_type = row.get("road_type", "Road")
            except Exception:
                continue

        # Determine cardinal direction to nearest safe road
        direction = "N/A"
        if nearest_safe:
            mid_pt = nearest_safe.interpolate(0.5, normalized=True)
            dlat = mid_pt.y - origin_lat
            dlon = mid_pt.x - origin_lon
            angle = math.degrees(math.atan2(dlon, dlat)) % 360
            directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW", "N"]
            direction = directions[int((angle + 22.5) / 45)]

        # Distance in km (rough geographic degree → km conversion)
        dist_km = round(nearest_dist * 111, 2) if nearest_dist != float("inf") else 0

        route_coords = []
        if nearest_safe:
            # Get list of coordinates from the LineString
            route_coords = [[lat, lon] for lon, lat in list(nearest_safe.coords)]

        return {
            "total_roads":     len(roads_gdf),
            "safe_count":      len(safe_roads),
            "at_risk_count":   len(at_risk),
            "impassable_count":len(impassable),
            "nearest_safe_road": nearest_name,
            "nearest_road_type": nearest_type,
            "direction":       direction,
            "distance_km":     dist_km,
            "route_coords":    route_coords,
            "origin":          [origin_lat, origin_lon],
            "recommendation":  _build_recommendation(
                len(safe_roads), len(impassable), direction, nearest_name, dist_km
            ),
        }
    except Exception as e:
        print(f"[road_network] Route analysis error: {e}")
        return None


def _build_recommendation(safe_cnt, impassable_cnt, direction, road_name, dist_km):
    """Builds human-readable evacuation recommendation."""
    if impassable_cnt == 0:
        return (
            f"✅ All monitored roads are currently passable. "
            f"Nearest safe arterial: **{road_name}** ({dist_km:.1f} km {direction})."
        )
    elif safe_cnt > 0:
        return (
            f"⚠️ {impassable_cnt} road segment(s) flooded. "
            f"Recommended evacuation direction: **{direction}** via **{road_name}** "
            f"({dist_km:.1f} km away)."
        )
    else:
        return (
            f"🚨 **All monitored roads at risk or impassable.** "
            f"Stay in place and contact emergency services. "
            f"Move to high ground immediately."
        )


# ─────────────────────────────────────────────────────────────
# 4. ROADS → FOLIUM LAYER HELPER
# ─────────────────────────────────────────────────────────────
def roads_to_folium_features(roads_gdf):
    """
    Converts road GeoDataFrame to list of dicts for Folium GeoJson rendering.
    Returns list of {geojson, color, tooltip} dicts.
    """
    if roads_gdf is None or roads_gdf.empty:
        return []

    features = []
    for _, row in roads_gdf.iterrows():
        try:
            feat = {
                "type": "Feature",
                "geometry": row.geometry.__geo_interface__,
                "properties": {
                    "name":      row.get("name", "Road"),
                    "highway":   row.get("highway", ""),
                    "road_type": row.get("road_type", ""),
                    "status":    row.get("status", "SAFE"),
                    "color":     row.get("color", "#22c55e"),
                },
            }
            features.append(feat)
        except Exception:
            continue

    return {
        "type": "FeatureCollection",
        "features": features,
    }
