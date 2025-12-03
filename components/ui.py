import streamlit as st

def get_enhanced_css():
    return """
    <style>
        .main-header {
            font-size: 2.5rem;
            font-weight: 700;
            color: #1E3A5F;
            text-align: center;
            padding: 1rem 0;
            margin-bottom: 0rem;
        }
        .sub-header {
            font-size: 1.1rem;
            color: #666;
            text-align: center;
            margin-bottom: 2rem;
        }
        .map-container {
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            padding: 0;
            margin: 1rem 0;
        }
        .card {
            background: white;
            border-radius: 12px;
            padding: 1.5rem;
            margin: 1rem 0;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.08);
            border: 1px solid #eee;
        }
        .card-header {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            margin-bottom: 1rem;
            font-weight: 600;
            font-size: 1.1rem;
            color: #333;
        }
        .stat-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 12px;
            padding: 1.5rem;
            color: white;
            text-align: center;
            margin: 0.5rem 0;
        }
        .stat-card-green {
            background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        }
        .stat-card-orange {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        }
        .stat-card-blue {
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        }
        .stat-value {
            font-size: 1.8rem;
            font-weight: 700;
        }
        .stat-label {
            font-size: 0.85rem;
            opacity: 0.9;
        }
        .legend-box {
            background-color: #f8f9fa;
            border-radius: 10px;
            padding: 1rem;
            margin: 1rem 0;
        }
        .legend-item {
            display: flex;
            align-items: center;
            margin: 0.5rem 0;
        }
        .legend-color {
            width: 24px;
            height: 24px;
            border-radius: 4px;
            margin-right: 10px;
            border: 1px solid #ddd;
        }
        .info-box {
            background-color: #e7f3ff;
            border-left: 4px solid #2196F3;
            padding: 1rem;
            margin: 1rem 0;
            border-radius: 0 8px 8px 0;
        }
        .success-box {
            background-color: #e8f5e9;
            border-left: 4px solid #4CAF50;
            padding: 1rem;
            margin: 1rem 0;
            border-radius: 0 8px 8px 0;
        }
        .warning-box {
            background-color: #fff3e0;
            border-left: 4px solid #FF9800;
            padding: 1rem;
            margin: 1rem 0;
            border-radius: 0 8px 8px 0;
        }
        .error-box {
            background-color: #ffebee;
            border-left: 4px solid #f44336;
            padding: 1rem;
            margin: 1rem 0;
            border-radius: 0 8px 8px 0;
        }
        .change-positive {
            color: #4CAF50;
            font-weight: bold;
        }
        .change-negative {
            color: #f44336;
            font-weight: bold;
        }
        .gradient-legend {
            height: 20px;
            border-radius: 4px;
            margin: 10px 0;
        }
        .legend-labels {
            display: flex;
            justify-content: space-between;
            font-size: 0.8rem;
            color: #666;
        }
        .pollutant-card {
            background: white;
            border-radius: 10px;
            padding: 1rem;
            margin: 0.5rem 0;
            border: 1px solid #e0e0e0;
        }
        .pollutant-value {
            font-size: 1.5rem;
            font-weight: 600;
            color: #333;
        }
        .pollutant-unit {
            font-size: 0.85rem;
            color: #666;
        }
        .opacity-slider {
            margin: 0.5rem 0;
        }
        .pixel-inspector {
            background: rgba(0, 0, 0, 0.8);
            color: white;
            padding: 0.5rem 1rem;
            border-radius: 6px;
            font-size: 0.85rem;
        }
    </style>
    """

def apply_enhanced_css():
    st.markdown(get_enhanced_css(), unsafe_allow_html=True)

def render_stat_card(value, label, icon="", color_class=""):
    extra_class = f" {color_class}" if color_class else ""
    st.markdown(f"""
        <div class="stat-card{extra_class}">
            <div class="stat-value">{icon} {value}</div>
            <div class="stat-label">{label}</div>
        </div>
    """, unsafe_allow_html=True)

def render_info_box(content, box_type="info"):
    st.markdown(f'<div class="{box_type}-box">{content}</div>', unsafe_allow_html=True)

def render_card(title, content, icon=""):
    header = f"{icon} {title}" if icon else title
    st.markdown(f"""
        <div class="card">
            <div class="card-header">{header}</div>
            <div>{content}</div>
        </div>
    """, unsafe_allow_html=True)

def render_gradient_legend(palette, min_val, max_val, label=""):
    gradient = ", ".join(palette)
    st.markdown(f"""
        <div style="margin: 1rem 0;">
            {f'<div style="font-weight: 500; margin-bottom: 0.5rem;">{label}</div>' if label else ''}
            <div class="gradient-legend" style="background: linear-gradient(to right, {gradient});"></div>
            <div class="legend-labels">
                <span>{min_val}</span>
                <span>{max_val}</span>
            </div>
        </div>
    """, unsafe_allow_html=True)

def render_collapsible(title, content_func, icon="", default_open=False):
    with st.expander(f"{icon} {title}" if icon else title, expanded=default_open):
        content_func()

def render_pollutant_stat_card(name, value, unit, description=""):
    st.markdown(f"""
        <div class="pollutant-card">
            <div style="font-weight: 500; margin-bottom: 0.5rem;">{name}</div>
            <div class="pollutant-value">{value:.2f}</div>
            <div class="pollutant-unit">{unit}</div>
            {f'<div style="font-size: 0.75rem; color: #888; margin-top: 0.5rem;">{description}</div>' if description else ''}
        </div>
    """, unsafe_allow_html=True)

def render_page_header(title, subtitle="", author_info=True):
    st.markdown(f'<div class="main-header">{title}</div>', unsafe_allow_html=True)
    if subtitle:
        st.markdown(f'<div class="sub-header">{subtitle}</div>', unsafe_allow_html=True)
    if author_info:
        st.markdown(
            """
            <div style="text-align: center; font-size: 15px; color: #555; padding: 0rem 0; margin-top: -50px;">
                <hr style="border: none; border-top: 1px solid #ddd; margin-bottom: 0px;">
                Made with love by <strong>Hemant Kumar</strong> • 
                <a href="https://www.linkedin.com/in/hemantkumar2430" target="_blank">LinkedIn</a>
            </div>
            """,
            unsafe_allow_html=True,
        )

def init_common_session_state():
    defaults = {
        "gee_initialized": False,
        "current_map": None,
        "analysis_complete": False,
        "lulc_stats": None,
        "current_image": None,
        "current_geometry": None,
        "time_series_stats": None,
        "drawn_geometry": None,
        "selected_state": None,
        "selected_city": None,
        "city_coords": None,
        "index_opacities": {},
        "pixel_values": None,
        "aqi_stats": None,
        "aqi_time_series": None,
    }
    
    for key, default_value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default_value
