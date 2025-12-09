import streamlit as st

def get_enhanced_css():
    return """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');

        html, body, [class*="css"] {
            font-family: 'Outfit', sans-serif;
            scroll-behavior: smooth;
        }

        /* --- ORBITAL COMMAND THEME --- */
        
        .stApp {
            background-color: #050911;
            color: #f1f5f9;
            background-image: 
                radial-gradient(circle at 50% 0%, #1e293b 0%, transparent 50%),
                radial-gradient(circle at 0% 50%, rgba(0, 243, 255, 0.03) 0%, transparent 40%);
        }

        .main-header {
            font-size: 3.5rem;
            font-weight: 800;
            color: #ffffff;
            text-align: center;
            padding: 2.5rem 0 1rem 0;
            letter-spacing: -0.03em;
            text-shadow: 0 0 40px rgba(0, 243, 255, 0.2);
            text-transform: uppercase;
        }
        
        .sub-header {
            font-size: 1.1rem;
            color: #f8fafc;
            text-align: center;
            margin-bottom: 3.5rem;
            font-weight: 400;
            max-width: 650px;
            margin-left: auto;
            margin-right: auto;
            border: 1px solid rgba(255,255,255,0.1);
            background: rgba(15, 23, 42, 0.6);
            padding: 0.75rem 1.5rem;
            border-radius: 100px;
            backdrop-filter: blur(10px);
        }

        .map-container {
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 0 0 1px #1e293b, 0 20px 40px -10px rgba(0,0,0,0.5);
            padding: 4px;
            background: #0f172a;
            margin: 1.5rem 0;
        }

        /* HUD Cards */
        .card, .feature-card {
            background: rgba(15, 23, 42, 0.6);
            backdrop-filter: blur(12px);
            border-radius: 12px;
            padding: 1.75rem;
            margin: 1rem 0;
            border: 1px solid rgba(56, 189, 248, 0.1); /* Subtle cyan border */
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            overflow: hidden;
            color: #f1f5f9;
        }
        
        .feature-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 2px;
            background: linear-gradient(90deg, transparent, #00f3ff, transparent);
            opacity: 0;
            transition: opacity 0.3s ease;
        }

        .feature-card:hover {
            transform: translateY(-4px);
            border-color: rgba(56, 189, 248, 0.4);
            box-shadow: 0 0 20px rgba(0, 243, 255, 0.1);
            background: rgba(15, 23, 42, 0.8);
        }
        
        .feature-card:hover::before {
            opacity: 1;
        }

        .card-header {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            margin-bottom: 1.25rem;
            font-weight: 700;
            font-size: 1.2rem;
            color: #f1f5f9;
            letter-spacing: 0.02em;
        }

        /* Stat Cards */
        .stat-card {
            background: rgba(15, 23, 42, 0.8);
            border: 1px solid rgba(255,255,255,0.05);
            border-radius: 12px;
            padding: 1.5rem;
            text-align: center;
            margin: 0.5rem 0;
            transition: transform 0.2s;
            position: relative;
        }
        
        .stat-card::after {
            content: '';
            position: absolute;
            bottom: 0px;
            left: 20%;
            width: 60%;
            height: 2px;
            background: currentColor;
            opacity: 0.5;
            box-shadow: 0 -2px 10px currentColor;
        }
        
        .stat-card:hover {
            transform: scale(1.02);
            background: rgba(30, 41, 59, 0.5);
        }

        .stat-card-blue { color: #38bdf8; }
        .stat-card-green { color: #4ade80; }
        .stat-card-orange { color: #fb923c; }

        .stat-value {
            font-size: 2.25rem;
            font-weight: 800;
            letter-spacing: -0.02em;
            color: #fff;
            margin-bottom: 0.25rem;
            text-shadow: 0 0 20px rgba(0,0,0,0.5);
        }

        .stat-label {
            font-size: 0.85rem;
            opacity: 0.9;
            color: #e2e8f0;
            font-weight: 600;
            letter-spacing: 0.05em;
            text-transform: uppercase;
        }

        /* Utility Boxes */
        .info-box, .success-box, .warning-box, .error-box {
            border-radius: 8px;
            padding: 1rem;
            margin: 1.5rem 0;
            border-left: 3px solid;
            background: rgba(15, 23, 42, 0.8);
            display: flex;
            gap: 1rem;
        }

        .info-box { border-color: #3b82f6; color: #bfdbfe; }
        .success-box { border-color: #22c55e; color: #bbf7d0; }
        .warning-box { border-color: #f97316; color: #fed7aa; }
        .error-box { border-color: #ef4444; color: #fecaca; }

        /* Animation */
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .animate-fade-in { animation: fadeIn 0.6s ease-out forwards; }
        
        /* Form Elements Override */
        [data-testid="stSelectbox"] label, [data-testid="stSlider"] label {
            color: #f1f5f9 !important;
            font-size: 0.85rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        
        .stButton button {
            background: linear-gradient(90deg, #0ea5e9, #2563eb);
            border: none;
            color: white;
            font-weight: 600;
            transition: all 0.2s;
        }
        
        .stButton button:hover {
            box-shadow: 0 0 15px rgba(14, 165, 233, 0.4);
            transform: scale(1.02);
        }

        /* --- MOBILE RESPONSIVENESS --- */
        @media (max-width: 768px) {
            .main-header {
                font-size: 2.2rem !important;
                padding-top: 1.5rem;
            }
            .sub-header {
                font-size: 0.95rem !important;
                padding: 1rem;
                margin-bottom: 2rem;
            }
            .stat-value {
                font-size: 1.75rem !important;
            }
            .stat-label {
                font-size: 0.75rem;
            }
            .card-header {
                font-size: 1.1rem;
            }
            .feature-card, .card, .stat-card {
                padding: 1.25rem !important;
                margin: 0.75rem 0;
            }
            .stApp {
                background-image: none !important; /* Performance on mobile */
                background-color: #050911 !important;
            }
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
            <div class="author-info" style="text-align: center; font-size: 15px; padding: 0rem 0; margin-top: -50px;">
                <hr class="header-divider" style="border: none; border-top: 1px solid currentColor; opacity: 0.3; margin-bottom: 0px;">
                Made with ❤️ by <strong>Hemant Kumar</strong> • 
                <a href="https://www.linkedin.com/in/hemantkumar2430" target="_blank" style="color: #60a5fa;">LinkedIn</a>
            </div>
            <style>
                .author-info { color: #94a3b8; }
                .author-info a { color: #60a5fa; }
                @media (prefers-color-scheme: dark) {
                    .author-info { color: #e2e8f0; }
                    .author-info a { color: #93c5fd; }
                }
            </style>
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
