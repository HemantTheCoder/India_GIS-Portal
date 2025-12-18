import streamlit as st
import folium
from streamlit_folium import st_folium
from folium.plugins import Draw

def create_base_map(lat, lon, zoom=11, enable_drawing=False):
    # Check for Upside Down Mode
    theme_mode = st.session_state.get('theme_mode', 'standard')
    
    if theme_mode == 'upside_down':
        tiles = "CartoDB dark_matter"
        attr = "CartoDB Dark Matter"
    else:
        tiles = "OpenStreetMap"
        attr = "OpenStreetMap"

    m = folium.Map(
        location=[lat, lon],
        zoom_start=zoom,
        tiles=tiles,
        attr=attr if tiles != "OpenStreetMap" else None
    )
    
    if enable_drawing:
        draw = Draw(
            draw_options={
                'polyline': False,
                'rectangle': True,
                'polygon': True,
                'circle': True,
                'marker': False,
                'circlemarker': False,
            },
            edit_options={'edit': False}
        )
        draw.add_to(m)
    
    return m

def add_tile_layer(map_obj, tile_url, layer_name, opacity=1.0):
    folium.TileLayer(
        tiles=tile_url,
        attr="Google Earth Engine",
        name=layer_name,
        overlay=True,
        control=True,
        opacity=opacity,
    ).add_to(map_obj)
    return map_obj

def add_marker(map_obj, lat, lon, popup="", tooltip="", color="red"):
    folium.Marker(
        [lat, lon],
        popup=popup,
        tooltip=tooltip,
        icon=folium.Icon(color=color, icon="info-sign"),
    ).add_to(map_obj)
    return map_obj

def add_buffer_circle(map_obj, lat, lon, radius_km, color="#3388ff", fill_opacity=0.1):
    folium.Circle(
        [lat, lon],
        radius=radius_km * 1000,
        color=color,
        fill=True,
        fillOpacity=fill_opacity,
        weight=2,
    ).add_to(map_obj)
    return map_obj

def add_layer_control(map_obj, collapsed=False):
    folium.LayerControl(collapsed=collapsed).add_to(map_obj)
    return map_obj

def render_map_with_drawing(map_obj, height=600, key=None):
    map_data = st_folium(
        map_obj, 
        width=None, 
        height=height, 
        returned_objects=["all_drawings", "last_clicked"],
        key=key
    )
    return map_data

def render_map(map_obj, height=600, key=None):
    return st_folium(map_obj, width=None, height=height, key=key)

def create_full_width_map_container():
    st.markdown('<div class="map-container">', unsafe_allow_html=True)
    
def close_map_container():
    st.markdown('</div>', unsafe_allow_html=True)

def get_click_coordinates(map_data):
    if map_data and map_data.get("last_clicked"):
        return {
            "lat": map_data["last_clicked"]["lat"],
            "lon": map_data["last_clicked"]["lng"]
        }
    return None

def add_geojson_boundary(map_obj, geojson_data, name="Uploaded Boundary", 
                          color="#ff7800", weight=3, fill=True, fill_opacity=0.1):
    """Add a GeoJSON boundary to the map for visualization."""
    if geojson_data is None:
        return map_obj
    
    style_function = lambda x: {
        'fillColor': color,
        'color': color,
        'weight': weight,
        'fillOpacity': fill_opacity,
    }
    
    folium.GeoJson(
        geojson_data,
        name=name,
        style_function=style_function,
        tooltip=name
    ).add_to(map_obj)
    
    return map_obj
