import streamlit as st
from services.gee_lulc import LULC_CLASSES
from services.gee_indices import INDEX_INFO
from services.gee_aqi import POLLUTANT_INFO

def render_lulc_legend():
    st.markdown("### Land Cover Classes")
    for class_id, info in LULC_CLASSES.items():
        col1, col2 = st.columns([1, 4])
        with col1:
            st.markdown(
                f'<div style="background-color: {info["color"]}; width: 30px; height: 30px; border-radius: 4px; border: 1px solid #ccc;"></div>',
                unsafe_allow_html=True,
            )
        with col2:
            st.write(info["name"])

def render_index_legend(index_name, show_description=True, show_range=True):
    info = INDEX_INFO.get(index_name, {})
    st.markdown(f"### {info.get('name', index_name)}")
    
    if show_description:
        st.markdown(f"*{info.get('description', '')}*")
    
    palette = info.get("palette", [])
    min_val = info.get("min", -1)
    max_val = info.get("max", 1)
    
    if palette:
        gradient = ", ".join(palette)
        st.markdown(
            f'<div style="background: linear-gradient(to right, {gradient}); height: 25px; border-radius: 4px; margin: 10px 0;"></div>',
            unsafe_allow_html=True,
        )
        if show_range:
            col1, col2, col3 = st.columns([1, 2, 1])
            with col1:
                st.caption(str(min_val))
            with col2:
                st.caption("Value Range", unsafe_allow_html=True)
            with col3:
                st.caption(str(max_val))

def render_index_legend_with_opacity(index_name, key_prefix=""):
    info = INDEX_INFO.get(index_name, {})
    
    with st.expander(f"{info.get('name', index_name)}", expanded=True):
        st.markdown(f"*{info.get('description', '')}*")
        
        palette = info.get("palette", [])
        min_val = info.get("min", -1)
        max_val = info.get("max", 1)
        
        if palette:
            gradient = ", ".join(palette)
            st.markdown(
                f'<div style="background: linear-gradient(to right, {gradient}); height: 20px; border-radius: 4px; margin: 5px 0;"></div>',
                unsafe_allow_html=True,
            )
            col1, col2 = st.columns(2)
            with col1:
                st.caption(f"Min: {min_val}")
            with col2:
                st.caption(f"Max: {max_val}")
        
        opacity = st.slider(
            "Opacity",
            min_value=0.0,
            max_value=1.0,
            value=0.8,
            step=0.1,
            key=f"{key_prefix}opacity_{index_name}"
        )
        
        return opacity

def render_pollutant_legend(pollutant):
    info = POLLUTANT_INFO.get(pollutant, {})
    
    st.markdown(f"### {info.get('name', pollutant)}")
    st.markdown(f"*{info.get('description', '')}*")
    
    palette = info.get("palette", [])
    min_val = info.get("min", 0)
    max_val = info.get("max", 100)
    unit = info.get("display_unit", "")
    
    if palette:
        gradient = ", ".join(palette)
        st.markdown(
            f'<div style="background: linear-gradient(to right, {gradient}); height: 25px; border-radius: 4px; margin: 10px 0;"></div>',
            unsafe_allow_html=True,
        )
        col1, col2, col3 = st.columns([1, 2, 1])
        with col1:
            st.caption(f"{min_val}")
        with col2:
            st.caption(f"({unit})")
        with col3:
            st.caption(f"{max_val}")

def render_pollutant_legend_with_opacity(pollutant, key_prefix=""):
    info = POLLUTANT_INFO.get(pollutant, {})
    
    with st.expander(f"{info.get('name', pollutant)}", expanded=True):
        st.markdown(f"*{info.get('description', '')}*")
        
        palette = info.get("palette", [])
        min_val = info.get("min", 0)
        max_val = info.get("max", 100)
        unit = info.get("display_unit", "")
        
        if palette:
            gradient = ", ".join(palette)
            st.markdown(
                f'<div style="background: linear-gradient(to right, {gradient}); height: 20px; border-radius: 4px; margin: 5px 0;"></div>',
                unsafe_allow_html=True,
            )
            st.caption(f"Range: {min_val} - {max_val} {unit}")
        
        opacity = st.slider(
            "Opacity",
            min_value=0.0,
            max_value=1.0,
            value=0.8,
            step=0.1,
            key=f"{key_prefix}opacity_{pollutant}"
        )
        
        return opacity

def render_anomaly_legend(pollutant):
    info = POLLUTANT_INFO.get(pollutant, {})
    max_val = info.get("max", 100) / 2
    
    st.markdown(f"### {pollutant} Anomaly")
    st.markdown("*Difference from baseline (2019)*")
    
    palette = ["#0000ff", "#00ffff", "#ffffff", "#ffff00", "#ff0000"]
    gradient = ", ".join(palette)
    
    st.markdown(
        f'<div style="background: linear-gradient(to right, {gradient}); height: 25px; border-radius: 4px; margin: 10px 0;"></div>',
        unsafe_allow_html=True,
    )
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        st.caption(f"-{max_val:.0f}")
    with col2:
        st.caption("Decrease | Increase")
    with col3:
        st.caption(f"+{max_val:.0f}")

def render_hotspot_legend():
    st.markdown("### Hotspot Areas")
    st.markdown("*Areas exceeding mean + 1.5σ*")
    
    col1, col2 = st.columns([1, 4])
    with col1:
        st.markdown(
            '<div style="background-color: #ff0000; width: 30px; height: 30px; border-radius: 4px; opacity: 0.7;"></div>',
            unsafe_allow_html=True,
        )
    with col2:
        st.write("High concentration hotspot")
