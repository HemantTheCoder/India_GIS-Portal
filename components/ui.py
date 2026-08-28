import streamlit as st
import contextlib


def get_enhanced_css():
    from components.map_asset import INDIA_MAP_BASE64
    css = """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&display=swap');

        /* ============================================================
           DESIGN TOKENS
           ============================================================ */
        :root {
            color-scheme: dark !important;

            --bg-base: #060a12;
            --bg-surface: rgba(15, 23, 42, 0.6);
            --bg-surface-solid: #0f172a;
            --bg-surface-hover: rgba(30, 41, 59, 0.75);
            --bg-surface-dim: rgba(15, 23, 42, 0.4);

            --border-subtle: rgba(148, 163, 184, 0.12);
            --border-strong: rgba(148, 163, 184, 0.32);

            --text-primary: #f1f5f9;
            --text-secondary: #cbd5e1;
            --text-muted: #94a3b8;

            --accent: #38bdf8;
            --accent-strong: #0ea5e9;
            --accent-soft: rgba(56, 189, 248, 0.14);

            --success: #22c55e;
            --warning: #f97316;
            --danger: #ef4444;
            --info: #3b82f6;

            --radius-sm: 8px;
            --radius-md: 12px;
            --radius-lg: 16px;
            --radius-pill: 9999px;

            --shadow-card: 0 4px 16px -4px rgba(0, 0, 0, 0.4);
            --shadow-card-hover: 0 16px 32px -12px rgba(0, 0, 0, 0.55);
        }

        /* ============================================================
           BASE / SHELL
           ============================================================ */
        html, body, [class*="css"] {
            font-family: 'Outfit', sans-serif;
            scroll-behavior: smooth;
            background-color: var(--bg-base) !important;
            color: var(--text-primary) !important;
        }

        .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"],
        .main, section[data-testid="stSidebar"], [data-testid="stToolbar"] {
            background-color: var(--bg-base) !important;
            color: var(--text-primary) !important;
        }

        .stApp {
            background-image:
                radial-gradient(circle at 50% 0%, #101c2e 0%, transparent 55%),
                radial-gradient(circle at 0% 60%, rgba(56, 189, 248, 0.05) 0%, transparent 40%) !important;
        }

        header[data-testid="stHeader"] {
            background-color: var(--bg-base) !important;
        }

        section[data-testid="stSidebar"] > div {
            background-color: var(--bg-surface-solid) !important;
        }

        /* Remove default Streamlit chrome */
        .block-container {
            padding-top: 0rem !important;
            padding-bottom: 1.5rem !important;
            padding-left: 1rem !important;
            padding-right: 1rem !important;
        }
        footer, footer:after,
        .viewerBadge_container__1QSob,
        div[data-testid="stStatusWidget"],
        #MainMenu,
        .stDeployButton {
            display: none !important;
            visibility: hidden !important;
            height: 0px !important;
        }
        html, body { overflow-x: hidden !important; }

        /* ============================================================
           HERO / HEADER
           ============================================================ */
        .main-header {
            font-size: 3.25rem;
            font-weight: 800;
            color: var(--text-primary) !important;
            text-align: center;
            padding: 3.5rem 0 1.25rem 0;
            letter-spacing: -0.03em;
            position: relative;
            z-index: 1;
        }

        .hero-container {
            position: relative;
            padding: 1.5rem 0 0 0;
            margin-bottom: 1rem;
        }

        .hero-background {
            position: absolute;
            top: 0;
            left: 50%;
            transform: translateX(-50%);
            width: 100%;
            height: 100%;
            max-width: 780px;
            background-image: url('data:image/png;base64,INDIA_MAP_PLACEHOLDER');
            background-size: contain;
            background-repeat: no-repeat;
            background-position: center center;
            opacity: 0.10;
            z-index: 0;
            pointer-events: none;
        }

        .sub-header {
            font-size: 1.05rem;
            color: var(--text-secondary) !important;
            text-align: center;
            margin-bottom: 3rem;
            font-weight: 400;
            max-width: 680px;
            margin-left: auto;
            margin-right: auto;
            border: 1px solid var(--border-subtle);
            background: var(--bg-surface);
            backdrop-filter: blur(10px);
            padding: 0.75rem 1.5rem;
            border-radius: var(--radius-pill);
        }

        .attribution-line {
            text-align: center;
            font-size: 0.85rem;
            color: var(--text-muted);
            padding: 0.5rem 0;
            margin-bottom: 1rem;
        }
        .attribution-line a { color: var(--accent); text-decoration: none; }
        .attribution-line a:hover { text-decoration: underline; }

        .map-container {
            border-radius: var(--radius-sm);
            overflow: hidden;
            box-shadow: 0 0 0 1px var(--border-subtle), var(--shadow-card);
            padding: 4px;
            background: var(--bg-surface-solid);
            margin: 1.5rem 0;
        }

        /* ============================================================
           FEATURE CARDS (homepage grid)
           ============================================================ */
        .feature-card {
            background: var(--bg-surface);
            backdrop-filter: blur(12px);
            border-radius: var(--radius-md);
            padding: 1.75rem;
            margin: 0.5rem 0;
            border: 1px solid var(--border-subtle);
            box-shadow: var(--shadow-card);
            transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            overflow: hidden;
            color: var(--text-primary);
            height: 320px;
            display: flex;
            flex-direction: column;
        }

        .feature-card::before {
            content: '';
            position: absolute;
            top: 0; left: 0; right: 0;
            height: 2px;
            background: linear-gradient(90deg, transparent, var(--badge-color, var(--accent)), transparent);
            opacity: 0;
            transition: opacity 0.25s ease;
        }

        .feature-card:hover {
            transform: translateY(-4px);
            border-color: var(--border-strong);
            box-shadow: var(--shadow-card-hover);
            background: var(--bg-surface-hover);
        }
        .feature-card:hover::before { opacity: 1; }

        .feature-icon-badge {
            width: 44px;
            height: 44px;
            border-radius: var(--radius-sm);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.35rem;
            background: color-mix(in srgb, var(--badge-color, var(--accent)) 16%, transparent);
            border: 1px solid color-mix(in srgb, var(--badge-color, var(--accent)) 35%, transparent);
            margin-bottom: 1rem;
        }

        .card-header {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            margin-bottom: 0.6rem;
            font-weight: 700;
            font-size: 1.15rem;
            color: var(--text-primary);
            letter-spacing: 0.01em;
            line-height: 1.25;
        }

        .feature-desc {
            color: var(--text-secondary);
            font-size: 0.9rem;
            margin-bottom: 1rem;
            line-height: 1.5;
            flex-grow: 1;
        }

        .feature-list {
            color: var(--text-secondary);
            font-size: 0.85rem;
            margin-bottom: 1.25rem;
            padding-left: 1.1rem;
            line-height: 1.6;
        }

        /* Coming Soon Card */
        .coming-soon-card {
            background: var(--bg-surface-dim);
            backdrop-filter: blur(8px);
            border-radius: var(--radius-md);
            padding: 1.75rem;
            margin: 1rem 0;
            border: 1px solid var(--border-subtle);
            box-shadow: none;
            position: relative;
            overflow: hidden;
            color: var(--text-muted);
            opacity: 0.85;
            transition: all 0.25s ease;
        }
        .coming-soon-card:hover {
            opacity: 1;
            border-color: var(--border-strong);
            background: rgba(15, 23, 42, 0.55);
        }
        .coming-soon-badge {
            display: inline-block;
            padding: 0.25rem 0.75rem;
            border-radius: var(--radius-pill);
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            background: rgba(51, 65, 85, 0.5);
            color: var(--text-secondary);
            margin-bottom: 1rem;
            border: 1px solid var(--border-subtle);
        }

        /* Generic content card (render_card) */
        .card {
            background: var(--bg-surface);
            backdrop-filter: blur(12px);
            border-radius: var(--radius-md);
            padding: 1.75rem;
            margin: 1rem 0;
            border: 1px solid var(--border-subtle);
            box-shadow: var(--shadow-card);
            color: var(--text-primary);
        }

        /* ============================================================
           STAT CARDS
           ============================================================ */
        .stat-card {
            background: rgba(15, 23, 42, 0.85);
            border: 1px solid var(--border-subtle);
            border-radius: var(--radius-md);
            padding: 1.25rem 1rem;
            text-align: center;
            margin: 0.5rem 0;
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            min-height: 160px;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            box-shadow: var(--shadow-card);
        }
        .stat-card:hover {
            transform: translateY(-3px);
            background: var(--bg-surface-hover);
            border-color: var(--border-strong);
            box-shadow: var(--shadow-card-hover);
        }
        .stat-card-blue { color: var(--accent); }
        .stat-card-green { color: #4ade80; }
        .stat-card-orange { color: #fb923c; }

        .stat-value {
            font-size: 2.25rem;
            font-weight: 800;
            letter-spacing: -0.02em;
            color: #fff;
            margin-bottom: 0.25rem;
        }
        .stat-label {
            font-size: 0.85rem;
            opacity: 0.9;
            color: var(--text-secondary);
            font-weight: 600;
            letter-spacing: 0.05em;
            text-transform: uppercase;
        }

        /* ============================================================
           POLLUTANT CARDS + GRADIENT LEGEND
           ============================================================ */
        .pollutant-card {
            background: var(--bg-surface);
            border: 1px solid var(--border-subtle);
            border-radius: var(--radius-md);
            padding: 1.1rem 1rem;
            text-align: center;
            color: var(--text-primary);
        }
        .pollutant-value {
            font-size: 1.75rem;
            font-weight: 800;
            color: var(--accent);
        }
        .pollutant-unit {
            font-size: 0.75rem;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        .gradient-legend {
            height: 14px;
            border-radius: var(--radius-pill);
            border: 1px solid var(--border-subtle);
        }
        .legend-labels {
            display: flex;
            justify-content: space-between;
            font-size: 0.75rem;
            color: var(--text-muted);
            margin-top: 0.35rem;
        }

        /* ============================================================
           UTILITY BOXES
           ============================================================ */
        .info-box, .success-box, .warning-box, .error-box {
            border-radius: var(--radius-sm);
            padding: 1rem;
            margin: 1.5rem 0;
            border-left: 3px solid;
            background: rgba(15, 23, 42, 0.8);
            display: flex;
            gap: 1rem;
        }
        .info-box { border-color: var(--info); color: #bfdbfe; }
        .success-box { border-color: var(--success); color: #bbf7d0; }
        .warning-box { border-color: var(--warning); color: #fed7aa; }
        .error-box { border-color: var(--danger); color: #fecaca; }

        /* ============================================================
           ANIMATIONS
           ============================================================ */
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .animate-fade-in { animation: fadeIn 0.5s ease-out forwards; }

        .custom-loader-container {
            position: fixed;
            top: 0; left: 0;
            width: 100vw;
            height: 100dvh;
            background: rgba(6, 10, 18, 0.88);
            backdrop-filter: blur(8px);
            z-index: 999999;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
        }
        .radar-spinner {
            width: 50px;
            height: 50px;
            border-radius: 50%;
            border: 2px solid var(--accent-soft);
            border-top-color: var(--accent);
            box-shadow: 0 0 15px rgba(56, 189, 248, 0.4);
            animation: radar-spin 1.5s linear infinite;
            margin-bottom: 1rem;
            position: relative;
        }
        .radar-spinner::before {
            content: '';
            position: absolute;
            top: 50%; left: 50%;
            transform: translate(-50%, -50%);
            width: 6px; height: 6px;
            background: var(--accent);
            border-radius: 50%;
            box-shadow: 0 0 10px var(--accent);
        }
        @keyframes radar-spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }

        .loader-text {
            color: var(--text-secondary);
            font-size: 0.9rem;
            font-weight: 500;
            letter-spacing: 0.05em;
            text-transform: uppercase;
            animation: pulse 1.5s ease-in-out infinite;
        }
        @keyframes pulse { 0%, 100% { opacity: 0.6; } 50% { opacity: 1; } }

        /* ============================================================
           FORM ELEMENTS
           ============================================================ */
        [data-testid="stSelectbox"] label, [data-testid="stSlider"] label, [data-testid="stDateInput"] label,
        [data-testid="stMultiSelect"] label, [data-testid="stTextInput"] label, [data-testid="stNumberInput"] label {
            color: var(--text-primary) !important;
            font-size: 0.85rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        .stButton button {
            background-color: var(--bg-surface-solid) !important;
            border: 1px solid #475569 !important;
            color: var(--text-primary) !important;
            transition: all 0.2s;
        }
        .stButton button[kind="primary"] {
            background: linear-gradient(90deg, var(--accent-strong), var(--accent)) !important;
            border: none !important;
            color: #fff !important;
            font-weight: 600;
        }
        .stButton button[kind="secondary"] {
            background-color: var(--bg-surface-solid) !important;
            border: 1px solid #475569 !important;
            color: var(--text-primary) !important;
        }
        .stButton button:hover {
            box-shadow: 0 0 15px rgba(56, 189, 248, 0.35);
            transform: scale(1.02);
            border-color: var(--accent) !important;
            background-color: #1e293b !important;
            color: #fff !important;
        }

        .stDownloadButton button {
            background-color: var(--bg-surface-solid) !important;
            border: 1px solid #475569 !important;
            color: var(--text-primary) !important;
        }
        .stDownloadButton button:hover {
            border-color: var(--accent) !important;
            background-color: #1e293b !important;
            color: #fff !important;
        }

        div[data-testid="stExpander"] details > summary {
            background-color: rgba(15, 23, 42, 0.8) !important;
            color: var(--text-primary) !important;
            border: 1px solid var(--border-subtle) !important;
            border-radius: var(--radius-sm) !important;
        }
        div[data-testid="stExpander"] details > summary:hover {
            color: var(--accent) !important;
            border-color: var(--accent) !important;
        }
        div[data-testid="stExpander"] details[open] > summary {
            border-bottom-left-radius: 0 !important;
            border-bottom-right-radius: 0 !important;
        }
        div[data-testid="stExpander"] { border: none !important; box-shadow: none !important; }

        [data-testid="stCheckbox"] label, [data-testid="stRadio"] label { color: var(--text-secondary) !important; }

        [data-testid="stSlider"] div[data-testid="stMarkdownContainer"] p,
        [data-testid="stSlider"] div[data-testid="stSliderTickBar"] + div,
        [data-testid="stSlider"] div[data-testid="stSliderValueLabel"] {
            color: var(--text-secondary) !important;
        }

        [data-testid="stRadio"] div[role="radiogroup"] label { color: var(--text-primary) !important; }
        [data-testid="stRadio"] div[role="radiogroup"] label[data-baseweb="radio"] { background-color: transparent; }
        [data-testid="stRadio"] div[role="radiogroup"] {
            background-color: var(--bg-surface-dim);
            padding: 4px;
            border-radius: var(--radius-sm);
        }

        div[data-testid="stSlider"], div[data-testid="stSlider"] label,
        div[data-testid="stSlider"] p, div[data-testid="stSlider"] div {
            color: var(--text-primary) !important;
        }
        div[data-testid="stSliderTickBar"] > div { color: var(--text-secondary) !important; }
        div[data-testid="stRadio"] label p { color: var(--text-primary) !important; }

        div[data-baseweb="select"] > div, div[data-baseweb="input"] > div {
            background-color: rgba(15, 23, 42, 0.8) !important;
            border-color: #475569 !important;
            color: var(--text-primary) !important;
        }
        ul[data-testid="stSelectboxVirtualDropdown"] { background-color: var(--bg-surface-solid) !important; }
        li[role="option"] { color: var(--text-secondary) !important; }
        span[data-baseweb="tag"] { background-color: #1e293b !important; color: var(--text-primary) !important; }

        /* ============================================================
           SIDEBAR
           ============================================================ */
        section[data-testid="stSidebar"] {
            background-color: var(--bg-surface-solid) !important;
            color: var(--text-primary) !important;
        }
        section[data-testid="stSidebar"] > div { background-color: var(--bg-surface-solid) !important; }
        section[data-testid="stSidebar"] .stMarkdown p,
        section[data-testid="stSidebar"] .stCaption,
        section[data-testid="stSidebar"] label,
        section[data-testid="stSidebar"] div[data-testid="stMarkdownContainer"] p,
        section[data-testid="stSidebar"] .stMultiSelect,
        section[data-testid="stSidebar"] .stSelectbox,
        section[data-testid="stSidebar"] h1, section[data-testid="stSidebar"] h2, section[data-testid="stSidebar"] h3 {
            color: var(--text-primary) !important;
        }
        section[data-testid="stSidebar"] [data-testid="stCaptionContainer"],
        section[data-testid="stSidebar"] small {
            color: var(--text-secondary) !important;
            opacity: 1 !important;
        }
        [data-testid="stSidebarNav"] a, [data-testid="stSidebarNav"] span { color: var(--text-primary) !important; }
        [data-testid="stSidebarNav"] a:hover { color: var(--accent) !important; }

        /* ============================================================
           TEXT / TABLES / MISC CONTRAST
           ============================================================ */
        .stMarkdown p, .stMarkdown li, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3,
        .stMarkdown h4, .stMarkdown h5, .stMarkdown h6, .stMarkdown span {
            color: var(--text-secondary) !important;
        }

        div[data-baseweb="input"] > div, div[data-baseweb="base-input"] > div,
        div[data-baseweb="select"] > div, div[data-baseweb="number-input"] > div {
            background-color: #1e293b !important;
            color: var(--text-primary) !important;
            border-color: #475569 !important;
        }
        input[data-baseweb="input"], div[data-baseweb="select"] span {
            color: var(--text-primary) !important;
            -webkit-text-fill-color: var(--text-primary) !important;
        }

        [data-testid="stDataFrame"] div, [data-testid="stTable"] div { color: var(--text-secondary) !important; }
        [data-testid="stDataFrame"] { background-color: var(--bg-surface-dim); }

        /* Date picker */
        section[data-testid="stSidebar"] [data-testid="stDateInput"] { position: relative; }
        div[data-baseweb="popover"] { z-index: 9999 !important; }
        div[data-baseweb="calendar"] {
            background-color: #1e293b !important;
            color: var(--text-primary) !important;
            border: 1px solid #475569 !important;
            border-radius: var(--radius-sm) !important;
            box-shadow: 0 10px 25px rgba(0,0,0,0.5) !important;
        }
        div[data-baseweb="calendar"] div[role="presentation"] {
            background-color: var(--bg-surface-solid) !important;
            color: var(--text-primary) !important;
        }
        div[data-baseweb="calendar"] button { color: var(--text-primary) !important; background-color: transparent !important; }
        div[data-baseweb="calendar"] button:hover { background-color: var(--accent) !important; color: #000 !important; }
        div[data-baseweb="calendar"] button[aria-selected="true"] { background-color: var(--accent-strong) !important; color: #fff !important; }
        div[data-baseweb="calendar"] div[role="row"] > div { color: var(--text-muted) !important; }
        div[data-baseweb="calendar"], div[data-baseweb="calendar"] > div { background-color: #1e293b !important; }
        section[data-testid="stSidebar"] div[data-baseweb="popover"] > div { max-width: 340px !important; min-width: 300px !important; }

        /* ============================================================
           MOBILE RESPONSIVENESS
           ============================================================ */
        @media (max-width: 768px) {
            html, body { width: 100% !important; }
            .main-header { font-size: 2.1rem !important; padding-top: 1.5rem; }
            .sub-header { font-size: 0.95rem !important; padding: 1rem; margin-bottom: 2rem; }
            .stat-value { font-size: 1.75rem !important; }
            .stat-label { font-size: 0.75rem; }
            .card-header { font-size: 1.05rem; }
            .feature-card, .card, .stat-card {
                padding: 1.25rem !important;
                margin: 0.75rem 0;
                height: auto !important;
                min-height: 240px;
            }
            .stApp { background-image: none !important; background-color: var(--bg-base) !important; }
        }
    </style>
    """
    return css.replace("INDIA_MAP_PLACEHOLDER", INDIA_MAP_BASE64)


def apply_enhanced_css():
    st.markdown(get_enhanced_css(), unsafe_allow_html=True)


@contextlib.contextmanager
def custom_spinner(text="Processing Earth Data..."):
    """
    context manager compatible with st.spinner but uses our custom styled loader.
    """
    placeholder = st.empty()
    placeholder.markdown(f"""
        <div class="custom-loader-container">
            <div class="radar-spinner"></div>
            <div class="loader-text">{text}</div>
        </div>
    """, unsafe_allow_html=True)
    try:
        yield
    finally:
        placeholder.empty()


def render_stat_card(value, label, icon="", color_class=""):
    """
    Renders a stat card. `color_class` is unused visually (kept for call-site
    compatibility) - value color is driven by the shared token system.
    """
    st.markdown(f"""
        <div class="stat-card">
            <div style="font-size: 2rem; margin-bottom: 0.5rem;">{icon}</div>
            <div class="stat-value">{value}</div>
            <div class="stat-label">{label}</div>
        </div>
    """, unsafe_allow_html=True)


def render_stepper(current_step):
    """
    Renders a horizontal progress stepper for multi-phase analysis.
    """
    steps = ["📍 AOI SELECTION", "🌊 WATERSHED", "🧠 RISK ENGINE"]
    cols = st.columns(len(steps))
    for i, s in enumerate(steps):
        with cols[i]:
            is_done = current_step > i
            is_active = current_step == i
            color = "#22c55e" if is_done else "#38bdf8" if is_active else "#475569"
            icon = "✅" if is_done else "🔵" if is_active else "⚪"
            st.markdown(f"""
            <div style="text-align:center; border-bottom: 3px solid {color}; padding-bottom:8px; margin-bottom: 25px;">
                <span style="color:{color}; font-weight:700; font-size:0.75rem; letter-spacing:0.05em;">{icon} {s}</span>
            </div>
            """, unsafe_allow_html=True)


def render_info_box(content, box_type="info"):
    st.markdown(f'<div class="{box_type}-box">{content}</div>',
                unsafe_allow_html=True)


def render_card(title, content, icon=""):
    header = f"{icon} {title}" if icon else title
    st.markdown(f"""
        <div class="card">
            <div class="card-header">{header}</div>
            <div>{content}</div>
        </div>
    """,
                unsafe_allow_html=True)


def render_feature_card(icon, title, description, bullets, accent, button_label, page_path, delay=0.0):
    """
    Renders one homepage feature card and its navigation button as a single unit.
    `accent` is a CSS color used for the icon badge tint and hover accent line.
    Returns True the render cycle the button is clicked, so callers do:
        if render_feature_card(...): st.switch_page(page_path)
    """
    bullets_html = "".join(f"<li>{b}</li>" for b in bullets)
    st.markdown(f"""
        <div class="feature-card animate-fade-in" style="animation-delay: {delay}s; --badge-color: {accent};">
            <div class="feature-icon-badge" style="--badge-color: {accent};">{icon}</div>
            <div class="card-header">{title}</div>
            <p class="feature-desc">{description}</p>
            <ul class="feature-list">{bullets_html}</ul>
        </div>
    """, unsafe_allow_html=True)

    return st.button(button_label, use_container_width=True, type="primary", key=f"nav_{page_path}")


def render_gradient_legend(palette, min_val, max_val, label=""):
    gradient = ", ".join(palette)
    st.markdown(f"""
        <div style="margin: 1rem 0;">
            {f'<div style="font-weight: 500; margin-bottom: 0.5rem; color: var(--text-primary);">{label}</div>' if label else ''}
            <div class="gradient-legend" style="background: linear-gradient(to right, {gradient});"></div>
            <div class="legend-labels">
                <span>{min_val}</span>
                <span>{max_val}</span>
            </div>
        </div>
    """,
                unsafe_allow_html=True)


def render_collapsible(title, content_func, icon="", default_open=False):
    with st.expander(f"{icon} {title}" if icon else title,
                     expanded=default_open):
        content_func()


def render_pollutant_stat_card(name, value, unit, description=""):
    st.markdown(f"""
        <div class="pollutant-card">
            <div style="font-weight: 500; margin-bottom: 0.5rem; color: var(--text-primary);">{name}</div>
            <div class="pollutant-value">{value:.2f}</div>
            <div class="pollutant-unit">{unit}</div>
            {f'<div style="font-size: 0.75rem; color: var(--text-muted); margin-top: 0.5rem;">{description}</div>' if description else ''}
        </div>
    """,
                unsafe_allow_html=True)


def render_page_header(title, subtitle="", hero=False, show_author=True):
    """
    Render consistent page headers across the application.

    Args:
        title: Main page title (can include emoji)
        subtitle: Optional description text
        hero: If True, renders larger centered hero-style header (for landing page)
        show_author: If True, shows author attribution line
    """
    if hero:
        st.markdown(f"""
        <div class="hero-container">
            <div class="hero-background"></div>
            <div style="text-align: center; padding: 1rem 0 0.5rem 0; position: relative; z-index: 2;">
                <h1 class="main-header">{title}</h1>
            </div>
        </div>
        """, unsafe_allow_html=True)
        if subtitle:
            st.markdown(f'<div class="sub-header">{subtitle}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="main-header" style="font-size: 2.1rem; padding: 1rem 0;">{title}</div>', unsafe_allow_html=True)
        if subtitle:
            st.markdown(f'<div class="sub-header" style="font-size: 1rem; margin-bottom: 1.5rem;">{subtitle}</div>', unsafe_allow_html=True)

    if show_author:
        st.markdown("""
        <div class="attribution-line">
            Made with ❤️ by <strong style="color: var(--text-primary);">Hemant Kumar</strong> •
            <a href="https://www.linkedin.com/in/hemantkumar2430" target="_blank">LinkedIn</a>
        </div>
        """, unsafe_allow_html=True)


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

def ensure_python_dict(d):
    """
    Ensures a value is a Python dictionary. If it's a GEE object (ee.Dictionary/ee.Image),
    it calls .getInfo() to convert it. Useful for robust multi-sensor data access.
    """
    if d is None: return {}
    if hasattr(d, "getInfo"):
        try:
            return d.getInfo() or {}
        except:
            return {}
    return d if isinstance(d, dict) else {}
