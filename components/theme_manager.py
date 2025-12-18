import streamlit as st
import random

class ThemeManager:
    def __init__(self):
        if 'theme_mode' not in st.session_state:
            st.session_state['theme_mode'] = 'standard'
        
        if 'theme_effects' not in st.session_state:
            st.session_state['theme_effects'] = {
                'fog': True,
                'flicker': True,
                'glow': True,
                'grain': True,
                'audio': False # Default OFF
            }
        
        # Audio file URLs (using reliable public domain or placeholder sounds for demo)
        # In a real deployed app, these should be local assets encoded in base64
        self.audio_drone = "https://cdn.pixabay.com/download/audio/2022/03/15/audio_7306048d0e.mp3" # Low drone placeholder
        
    def render_theme_controls(self):
        """Renders the theme toggle and controls in the sidebar."""
        st.sidebar.divider()
        st.sidebar.markdown("### 🌗 Dimension Switch")
        
        mode = st.sidebar.radio(
            "Current Reality Layer",
            ["Standard Mode", "Upside Down Mode"],
            index=0 if st.session_state['theme_mode'] == 'standard' else 1,
            help="Switch between the Standard Academic view and the Alternate Dimension."
        )
        
        new_mode = 'standard' if mode == "Standard Mode" else 'upside_down'
        if new_mode != st.session_state['theme_mode']:
            st.session_state['theme_mode'] = new_mode
            st.rerun()
            
        if st.session_state['theme_mode'] == 'upside_down':
            with st.sidebar.expander("Control Panel", expanded=True):
                st.markdown("#### Immersive Effects")
                col1, col2 = st.columns(2)
                with col1:
                    st.session_state['theme_effects']['fog'] = st.checkbox("Fog", value=st.session_state['theme_effects']['fog'])
                    st.session_state['theme_effects']['flicker'] = st.checkbox("Flicker", value=st.session_state['theme_effects']['flicker'])
                with col2:
                    st.session_state['theme_effects']['glow'] = st.checkbox("Glow", value=st.session_state['theme_effects']['glow'])
                    st.session_state['theme_effects']['grain'] = st.checkbox("Grain", value=st.session_state['theme_effects']['grain'])
                
                st.markdown("#### Audio")
                st.session_state['theme_effects']['audio'] = st.checkbox("Enable Spatial Audio", value=st.session_state['theme_effects']['audio'], help="Experimental background audio.")
                
                # Cosmetic Stability Meter (V3 Feature)
                st.markdown("---")
                st.markdown(f"""
                <div style="font-family: 'Roboto Mono'; color: #b0b0b0; font-size: 0.8rem;">
                    Reality Stability: <span style="color: #ef4444; font-weight: bold;">███░░░ 63%</span>
                </div>
                """, unsafe_allow_html=True)

    def get_text(self, standard_text, alternate_text=None):
        """Returns standard or alternate text based on current theme."""
        if st.session_state['theme_mode'] == 'standard':
            return standard_text
        
        if alternate_text:
            return alternate_text
            
        # Default transformations if no alternate provided
        # V3: SCP / Stranger Things Terminology
        replacements = {
            "Urban Heat": "Thermal Rift Zones",
            "Vegetation": "Biological Overgrowth",
            "Air Quality": "Atmospheric Toxicity",
            "Earthquake": "Seismic Disturbances",
            "Risk": "Impending Doom",
            "Report": "Mission Log",
            "Analysis": "Investigation",
            "Dashboard": "Control Terminal",
            "Future Roadmap": "Expansion Protocol",
            "Search": "Scan Frequency",
            "Map": "Terrain Grid",
            "Data": "Raw Signal",
            "Comparison": "Dimensional Divergence"
        }
        
        text = standard_text
        for k, v in replacements.items():
            if k in text:
                text = text.replace(k, v)
                
        # V4: Apply glitch wrapper
        text = self.wrap_anomalies(text)
        return text

    def apply_theme(self):
        """Injects the necessary CSS and JS for the current theme."""
        if st.session_state['theme_mode'] == 'standard':
            return

        # Build Dynamic CSS
        css = """
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Creepster&family=Roboto+Mono:wght@300;700&display=swap');

            :root {
                --upside-bg: #0a0a0d;
                --upside-red: #ff0f0f;
                --upside-dim-red: #3d0000;
                --upside-text: #bfbfbf;
                --upside-glow: 0 0 10px rgba(255, 15, 15, 0.5);
            }

            /* Main App Background */
            .stApp {
                background-color: var(--upside-bg) !important;
                background-image: radial-gradient(circle at 50% 50%, #1a0505 0%, #000000 100%);
                color: var(--upside-text) !important;
                font-family: 'Roboto Mono', monospace;
            }
            
            /* Headers */
            h1, h2, h3, h4, h5, h6 {
                color: #e6e6e6 !important;
                font-family: 'Times New Roman', serif;
                text-transform: uppercase;
                letter-spacing: 2px;
                text-shadow: 0 0 5px var(--upside-red);
            }
            
            h1 {
                font-size: 3rem !important;
                border-bottom: 2px solid var(--upside-red);
                padding-bottom: 0.5rem;
            }

            /* Buttons */
            .stButton>button {
                background-color: transparent !important;
                border: 1px solid var(--upside-red) !important;
                color: var(--upside-red) !important;
                font-family: 'Roboto Mono', monospace;
                text-transform: uppercase;
                transition: all 0.3s ease;
                box-shadow: 0 0 5px var(--upside-dim-red);
            }
            
            .stButton>button:hover {
                background-color: var(--upside-dim-red) !important;
                box-shadow: 0 0 15px var(--upside-red);
                border-color: #ff4d4d !important;
                color: white !important;
            }

            /* Cards / Containers (approximate selectors for Streamlit containers) */
            div[data-testid="stExpander"], div.stDataFrame, div[data-testid="stMetricValue"] {
                border: 1px solid #330505 !important;
                background-color: rgba(10, 0, 0, 0.8) !important;
                box-shadow: 0 0 10px rgba(255, 0, 0, 0.1);
            }
            
            /* Inputs */
            .stTextInput>div>div>input, .stSelectbox>div>div>div {
                background-color: #000 !important;
                color: #ff9999 !important;
                border: 1px solid #500 !important;
            }
        """

        # Append Effects based on toggles
        if st.session_state['theme_effects']['glow']:
            css += """
            /* Pulsing Red Glow Animation */
            @keyframes redPulse {
                0% { box-shadow: 0 0 5px #300; }
                50% { box-shadow: 0 0 20px #800; }
                100% { box-shadow: 0 0 5px #300; }
            }
            .stApp div[data-testid="column"] {
                animation: redPulse 4s infinite ease-in-out;
            }
            """
            
        if st.session_state['theme_effects']['flicker']:
            css += """
            /* Screen Flicker */
            @keyframes flicker {
                0% { opacity: 0.97; }
                5% { opacity: 0.9; }
                10% { opacity: 0.97; }
                15% { opacity: 1; }
                50% { opacity: 0.98; }
                55% { opacity: 0.92; }
                60% { opacity: 0.98; }
                100% { opacity: 1; }
            }
            .stApp {
                animation: flicker 6s infinite;
            }
            """
            
        if st.session_state['theme_effects']['grain']:
            css += """
            /* Film Grain Overlay */
            .grain-overlay {
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                pointer-events: none;
                z-index: 9999;
                background-image: url("https://www.transparenttextures.com/patterns/stardust.png"); /* Simple noise pattern */
                opacity: 0.05;
            }
            """
            
        if st.session_state['theme_effects']['fog']:
            css += """
            /* --- V3: TOTAL IMMERSION OVERHAUL (REFINED) --- */
            
            /* 1. ATMOSPHERE LAYERS (SOFTENED) */
            .scanlines {
                position: fixed;
                top: 0;
                left: 0;
                width: 100vw;
                height: 100vh;
                background: linear-gradient(
                    to bottom,
                    rgba(255,255,255,0),
                    rgba(255,255,255,0) 50%,
                    rgba(0,0,0,0.05) 50%,
                    rgba(0,0,0,0.05)
                );
                background-size: 100% 4px;
                animation: scanlineMove 10s linear infinite;
                pointer-events: none;
                z-index: 9991;
                opacity: 0.15; /* Reduced from 0.3 */
            }
            @keyframes scanlineMove { from { background-position: 0 0; } to { background-position: 0 100%; } }

            .vignette-glow {
                position: fixed;
                top: 0;
                left: 0;
                width: 100vw;
                height: 100vh;
                background: radial-gradient(circle, transparent 60%, rgba(50,0,0,0.3) 90%, rgba(20,0,0,0.8) 100%);
                pointer-events: none;
                z-index: 9990;
                animation: vignettePulse 8s ease-in-out infinite;
            }
            @keyframes vignettePulse {
                0%, 100% { padding: 0; opacity: 0.7; }
                50% { padding: 20px; opacity: 0.9; }
            }

            /* 2. REACTIVE UI - HIERARCHY & FOCUS */
            /* Headers: Softened Red Line */
            h1 {
                font-size: 3rem !important;
                border-bottom: 2px solid rgba(255, 15, 15, 0.6) !important; /* Reduced opacity */
                box-shadow: 0 4px 6px -4px rgba(255, 0, 0, 0.4);
                padding-bottom: 0.5rem;
                text-shadow: 0 0 10px rgba(255,0,0,0.3);
            }

            /* Cards: Dimmed Defaults, Hero Hover */
            div[data-testid="column"] > div, div[data-testid="stExpander"], div.stDataFrame {
                transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
                border: 1px solid rgba(80, 0, 0, 0.1) !important; /* Very dim default */
                background-color: rgba(10, 0, 0, 0.6) !important;
            }
            /* Hover is where the action is */
            div[data-testid="column"] > div:hover, div[data-testid="stExpander"]:hover {
                transform: scale(1.01) translateY(-2px);
                box-shadow: 0 0 15px rgba(255, 30, 30, 0.3) !important;
                border-color: rgba(255, 15, 15, 0.6) !important;
                z-index: 10;
            }

            /* Warning Banner Pulse */
            div[data-testid="stAlert"] {
                animation: warningPulse 4s infinite ease-in-out;
                border: 1px solid rgba(249, 115, 22, 0.5);
            }
            @keyframes warningPulse {
                0% { border-color: rgba(249, 115, 22, 0.3); box-shadow: 0 0 0 rgba(0,0,0,0); }
                50% { border-color: rgba(249, 115, 22, 0.9); box-shadow: 0 0 15px rgba(249, 115, 22, 0.3); }
                100% { border-color: rgba(249, 115, 22, 0.3); box-shadow: 0 0 0 rgba(0,0,0,0); }
            }

            /* Buttons */
            .stButton>button {
                transition: all 0.1s ease;
                position: relative;
                overflow: hidden;
            }
            .stButton>button:active {
                transform: scale(0.96);
                box-shadow: inset 0 0 10px #000;
                border-color: #ff0000 !important;
            }

            /* 3. SIDEBAR "CONTROL ROOM" */
            section[data-testid="stSidebar"] {
                background-color: #050000 !important;
                background-image: 
                    linear-gradient(90deg, rgba(50,0,0,0.1) 1px, transparent 1px),
                    linear-gradient(rgba(50,0,0,0.1) 1px, transparent 1px),
                    url("https://www.transparenttextures.com/patterns/black-scales.png") !important;
                background-size: 20px 20px, 20px 20px, auto;
                border-right: 3px solid #3d0000 !important;
            }
            
            section[data-testid="stSidebar"] .stMarkdown h1, 
            section[data-testid="stSidebar"] .stMarkdown h2,
            section[data-testid="stSidebar"] .stMarkdown h3 {
                border-left: 3px solid #ff0f0f;
                padding-left: 10px;
                text-shadow: 0 0 8px #ff0f0f;
            }

            /* 4. LIVING MAPS - SINGLE BREATHING SOURCE */
            /* Only map containers breathe, nothing else loops continuously */
            iframe {
                animation: mapBreathe 8s ease-in-out infinite; /* Slower, more organic */
                filter: contrast(1.1) brightness(0.9);
            }
            @keyframes mapBreathe {
                0%, 100% { filter: contrast(1.1) brightness(0.9) saturate(0.8); }
                50% { filter: contrast(1.2) brightness(1.0) saturate(1.1); box-shadow: 0 0 20px rgba(50,0,0,0.15); }
            }

            /* 5. CINEMATIC ENTRY TRANSITION */
            @keyframes cinematicEntry {
                0% { opacity: 1; background: #000; filter: blur(0px); transform: scale(1); }
                20% { opacity: 1; background: #0a0000; filter: blur(2px); transform: scale(1.02); }
                50% { opacity: 1; background: #1a0000; filter: blur(4px) hue-rotate(90deg); transform: scale(1.05); }
                80% { opacity: 1; background: #000; filter: blur(0px); transform: scale(1.02); }
                100% { opacity: 0; pointer-events: none; transform: scale(1); }
            }
            
            .portal-transition {
                position: fixed;
                top: 0;
                left: 0;
                width: 100vw;
                height: 100vh;
                background-color: #000;
                z-index: 100000;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                animation: cinematicEntry 2.5s cubic-bezier(0.7, 0, 0.3, 1) forwards;
            }

            .portal-title {
                font-family: 'Times New Roman', serif;
                font-size: 3rem;
                color: #e2e8f0;
                text-transform: uppercase;
                letter-spacing: 0.5rem;
                opacity: 0;
                animation: textGlitch 2.5s ease-out forwards;
            }
            @keyframes textGlitch {
                 0% { opacity: 0; transform: scale(0.9); letter-spacing: 0; filter: blur(5px); }
                 30% { opacity: 1; transform: scale(1); letter-spacing: 0.5rem; filter: blur(0); text-shadow: 2px 0 red, -2px 0 blue; }
                 80% { opacity: 1; transform: scale(1.05); text-shadow: 5px 0 red; }
                 100% { opacity: 0; transform: scale(1.1); }
            }
            """
            
            css += """
            /* 6. V4.5 ADVANCED IMMERSION CSS */
            
            /* 'ALIVE' RED LINE (H1 Border) */
            h1 {
                border-bottom: none !important; /* Remove static border */
                position: relative;
                padding-bottom: 0.5rem;
            }
            h1::after {
                content: '';
                position: absolute;
                bottom: 0;
                left: 0;
                width: 100%;
                height: 2px;
                background: linear-gradient(90deg, transparent, #ff0f0f, transparent);
                background-size: 200% 100%;
                animation: energyFlow 4s infinite linear;
                box-shadow: 0 0 8px rgba(255, 15, 15, 0.6);
            }
            @keyframes energyFlow {
                0% { background-position: 100% 0; }
                100% { background-position: -100% 0; }
            }

            /* DIRECTIONAL FOG (Masked) */
            .fog-container {
                mask-image: linear-gradient(to bottom, transparent, black 40%);
                -webkit-mask-image: linear-gradient(to bottom, transparent, black 40%);
            }

            /* HERO CARD (First column/expander gets extra attention) */
            div[data-testid="column"]:first-child > div, div[data-testid="stExpander"]:first-child {
                border-color: rgba(255, 15, 15, 0.4) !important;
                box-shadow: 0 0 10px rgba(100, 0, 0, 0.3) !important;
            }

            /* KEYWORD GLITCH (SPARSE TIMING) */
            .glitch-text {
                position: relative;
                display: inline-block;
                color: #ff0f0f;
            }
            .glitch-text::before, .glitch-text::after {
                content: attr(data-text);
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                background: #0a0a0d;
                clip: rect(0, 0, 0, 0);
            }
            .glitch-text::before {
                left: -2px;
                text-shadow: 1px 0 #00f;
                animation: glitch-sparse-1 10s infinite linear alternate-reverse;
            }
            .glitch-text::after {
                left: 2px;
                text-shadow: -1px 0 #f00;
                animation: glitch-sparse-2 15s infinite linear alternate-reverse;
            }
            /* Glitch only happens briefly */
            @keyframes glitch-sparse-1 {
                0%, 92% { clip: rect(0,0,0,0); } 
                93% { clip: rect(20px, 9999px, 15px, 0); }
                95% { clip: rect(10px, 9999px, 85px, 0); }
                97% { clip: rect(80px, 9999px, 5px, 0); }
                100% { clip: rect(30px, 9999px, 60px, 0); }
            }
            @keyframes glitch-sparse-2 {
                0%, 94% { clip: rect(0,0,0,0); }
                95% { clip: rect(10px, 9999px, 80px, 0); }
                98% { clip: rect(40px, 9999px, 30px, 0); }
                100% { clip: rect(50px, 9999px, 20px, 0); }
            }

            /* Dynamic Lighting (Simulated) */
            .stApp::before {
                content: "";
                position: fixed;
                top: -50%;
                left: -50%;
                width: 200%;
                height: 200%;
                background: radial-gradient(circle, rgba(255, 100, 100, 0.05) 0%, transparent 60%);
                pointer-events: none;
                z-index: 9992;
                animation: lightShift 20s infinite ease-in-out;
            }
            @keyframes lightShift {
                0% { transform: translate(0, 0); }
                25% { transform: translate(10%, 10%); }
                50% { transform: translate(-5%, 20%); }
                75% { transform: translate(-10%, -5%); }
                100% { transform: translate(0, 0); }
            }

            /* STATUS LEDS (Global + Sidebar) */
            /* Main Content Headers */
            h1::before, h2::before, h3::before {
                content: '';
                display: inline-block;
                width: 6px;
                height: 6px;
                background-color: #22c55e;
                border-radius: 50%;
                margin-right: 12px;
                box-shadow: 0 0 6px #22c55e;
                vertical-align: middle;
                animation: statusBlink 4s infinite;
                opacity: 0.8;
            }
            /* Sidebar Headers */
            section[data-testid="stSidebar"] h1::before, 
            section[data-testid="stSidebar"] h2::before, 
            section[data-testid="stSidebar"] h3::before {
                content: '';
                display: inline-block;
                width: 5px;
                height: 5px;
                background-color: #f59e0b; /* Amber for sidebar */
                border-radius: 50%;
                margin-right: 8px;
                box-shadow: 0 0 5px #f59e0b;
                animation: statusBlink 3s infinite reverse;
            }
            
            /* Randomize Subheader Colors (CSS only assumption) */
            h3::before {
                background-color: #ef4444 !important;
                box-shadow: 0 0 8px #ef4444 !important;
                animation: statusBlinkFast 0.5s infinite alternate !important;
            }
            @keyframes statusBlink {
                0%, 100% { opacity: 0.9; transform: scale(1); }
                50% { opacity: 0.4; transform: scale(0.9); }
            }
            @keyframes statusBlinkFast {
                 0% { opacity: 1; }
                 100% { opacity: 0.3; }
            }

            /* Heat Bleed - Blur on specific zones (simulated via corner blur) */
            .stApp::after {
                content: "";
                position: fixed;
                bottom: -20px;
                right: -20px;
                width: 300px;
                height: 300px;
                background: radial-gradient(circle, rgba(255,50,0,0.15), transparent);
                filter: blur(40px);
                pointer-events: none;
                z-index: 9993;
            }
            """

        css += "</style>"
        
        # Inject Overlays
        overlays = ""
        
        # V3 Cinematic Transition
        overlays += """
        <div class="portal-transition">
            <div class="portal-title">Crossing Over...</div>
        </div>
        """

        # Atmosphere Layers (Persistent)
        if st.session_state['theme_effects']['grain']:
             overlays += '<div class="scanlines"></div>'
             
        # Vignette
        overlays += '<div class="vignette-glow"></div>'

        if st.session_state['theme_effects']['fog']:
            # Multi-layer parallax fog - Reduced Opacity
            overlays += """
            <div class="fog-container" style="position: fixed; top:0; left:0; width:100%; height:100%; pointer-events:none; z-index:9980; opacity:0.25;"> <!-- Reduced from 0.4 -->
                <div class="fog-layer-1" style="background:url('https://raw.githubusercontent.com/danielstuart14/CSS_FOG_ANIMATION/master/fog1.png'); width:200%; height:100%; animation: fogmove 20s linear infinite;"></div>
                <div class="fog-layer-2" style="background:url('https://raw.githubusercontent.com/danielstuart14/CSS_FOG_ANIMATION/master/fog2.png'); width:200%; height:100%; animation: fogmove 10s linear infinite; opacity:0.5;"></div>
            </div>
            <style>
                @keyframes fogmove { 0% { transform: translate3d(0, 0, 0); } 100% { transform: translate3d(-50%, 0, 0); } }
            </style>
            """
            
        st.markdown(css + overlays, unsafe_allow_html=True)

        # Audio Logic
        if st.session_state['theme_effects']['audio']:
            # Using HTML5 audio with loop and low volume
            audio_html = f"""
            <audio autoplay loop id="bg-audio">
                <source src="{self.audio_drone}" type="audio/mpeg">
            </audio>
            <script>
                var audio = document.getElementById("bg-audio");
                audio.volume = 0.2;
            </script>
            """
            st.markdown(audio_html, unsafe_allow_html=True)
            
        # V4: Silent Narrative & System Logs
        self._render_narrative_layer()

    def _render_narrative_layer(self):
        """Renders subtle narrative elements and system logs."""
        if st.session_state['theme_mode'] != 'upside_down':
            return

        # 1. Silent Narrative Text (Bottom Right)
        # Updates based on random session state interaction
        if 'narrative_step' not in st.session_state: st.session_state.narrative_step = 0
        
        narrative_lines = [
            "STATUS: DIMENSIONAL BREACH DETECTED",
            "WARNING: REALITY INTEGRITY < 85%",
            "ALERT: LOCALIZED TEMPORAL DISTORTION",
            "CRITICAL: CONTAINMENT PROTOCOL FAILING",
            "SYSTEM: RECALIBRATING SENSORS..."
        ]
        
        # Slowly cycle narrative
        import time
        current_idx = int(time.time() / 15) % len(narrative_lines) # Change every 15s
        current_msg = narrative_lines[current_idx]
        
        st.markdown(f"""
        <div style="position: fixed; bottom: 10px; right: 20px; color: rgba(255, 0, 0, 0.4); 
             font-family: 'Roboto Mono'; font-size: 0.7rem; pointer-events: none; z-index: 9995;">
             {current_msg}
        </div>
        """, unsafe_allow_html=True)

        # 2. System Logs (Sidebar) - Now with "Alive" feel
        with st.sidebar.expander("[ SYSTEM LOGS ]", expanded=False):
            # Fake rolling logs with visual glitches
            logs_pool = [
                f"[10:{random.randint(10,59)}] Connecting to Sat-Link {random.randint(1,9)}...",
                f"[10:{random.randint(10,59)}] Handshake successful.",
                f"[10:{random.randint(10,59)}] Specular reflection: {random.uniform(0.1, 0.9):.2f}",
                f"[10:{random.randint(10,59)}] BUFFER_OVERFLOW_EXCEPTION",
                f"[10:{random.randint(10,59)}] Retrying connection...",
                f"[10:{random.randint(10,59)}] <span style='color:red'>ANOMALY DETECTED IN SECTOR 7</span>",
                f"[10:{random.randint(10,59)}] Data packet size: {random.randint(1024, 9999)}kb",
                f"[10:{random.randint(10,59)}] Encryption: AES-256-GCM",
                f"<b>[!!!] ███ SIGNAL INTERRUPTED ███</b>",
                f"<span style='opacity:0.5'>[10:{random.randint(10,59)}] Background radiation: {random.randint(400,900)} mSv</span>"
            ]
            
            # Select random subset to make it feel like it's scrolling/changing
            display_logs = random.sample(logs_pool, k=7)
            
            log_html = "<div style='font-family: monospace; font-size: 0.7rem; color: #aaa; line-height: 1.2;'>"
            for log in display_logs:
                border_style = "border-left: 2px solid red; padding-left:5px;" if "ANOMALY" in log else ""
                log_html += f"<div style='margin-bottom:2px; {border_style}'> > {log}</div>"
            log_html += "</div>"
            st.markdown(log_html, unsafe_allow_html=True)
            
    def render_theme_controls(self):
        """Renders the theme toggle and controls in the sidebar."""
        st.sidebar.divider()
        st.sidebar.markdown("### 🌗 Dimension Switch")
        
        mode = st.sidebar.radio(
            "Current Reality Layer",
            ["Standard Mode", "Upside Down Mode"],
            index=0 if st.session_state['theme_mode'] == 'standard' else 1,
            help="Switch between the Standard Academic view and the Alternate Dimension."
        )
        
        new_mode = 'standard' if mode == "Standard Mode" else 'upside_down'
        if new_mode != st.session_state['theme_mode']:
            st.session_state['theme_mode'] = new_mode
            st.rerun()
            
        if st.session_state['theme_mode'] == 'upside_down':
            with st.sidebar.expander("Control Panel", expanded=True):
                st.markdown("#### Immersive Effects")
                col1, col2 = st.columns(2)
                with col1:
                    st.session_state['theme_effects']['fog'] = st.checkbox("Fog", value=st.session_state['theme_effects']['fog'])
                    st.session_state['theme_effects']['flicker'] = st.checkbox("Flicker", value=st.session_state['theme_effects']['flicker'])
                with col2:
                    st.session_state['theme_effects']['glow'] = st.checkbox("Glow", value=st.session_state['theme_effects']['glow'])
                    st.session_state['theme_effects']['grain'] = st.checkbox("Grain", value=st.session_state['theme_effects']['grain'])
                
                st.markdown("#### Audio")
                st.session_state['theme_effects']['audio'] = st.checkbox("Enable Spatial Audio", value=st.session_state['theme_effects']['audio'], help="Experimental background audio.")
                
                # Dynamic Stability Meter (V4.5 Feature)
                stability = random.randint(45, 85) # Fluctuate
                color = "#ef4444" if stability < 60 else "#f59e0b"
                bars = "█" * (stability // 10) + "░" * (10 - (stability // 10))
                
                st.markdown("---")
                st.markdown(f"""
                <div style="font-family: 'Roboto Mono'; color: #b0b0b0; font-size: 0.8rem;">
                    Reality Stability: <span style="color: {color}; font-weight: bold;">{bars} {stability}%</span>
                </div>
                """, unsafe_allow_html=True)

    def wrap_anomalies(self, text):
        """V4: Wraps specific keywords in glitch text span."""
        if st.session_state['theme_mode'] != 'upside_down':
            return text
            
        keywords = ["ANOMADLY", "ANOMALY", "BREACH", "RIFT", "ERROR", "WARNING", "CRITICAL", "FAILURE", "UNKNOWN"]
        
        for k in keywords:
            if k in text or k.title() in text:
                # Add glitch class
                replacement = f"<span class='glitch-text' data-text='{k}'>{k}</span>"
                text = text.replace(k, replacement).replace(k.title(), replacement)
        return text

    def render_hazard_overlay(self, hazard_type):
        """Renders specific atmospheric overlays based on the active module."""
        if st.session_state['theme_mode'] == 'standard':
            return
            
        overlay_html = ""
        
        if hazard_type == "heat":
            # Lava Lamp / Heat Haze effect
            overlay_html = """
            <div style="position:fixed; top:0; left:0; width:100%; height:100%; pointer-events:none; z-index:9000;
                background: radial-gradient(circle at 50% 100%, rgba(255, 50, 0, 0.2), transparent 70%);
                mix-blend-mode: overlay; animation: heatPulse 5s infinite ease-in-out;"></div>
            <style>@keyframes heatPulse { 0%, 100% { opacity: 0.3; } 50% { opacity: 0.6; } }</style>
            """
            
        elif hazard_type == "aqi":
            # Green/Yellow Toxic Smog
            overlay_html = """
            <div style="position:fixed; top:0; left:0; width:100%; height:100%; pointer-events:none; z-index:9000;
                background: linear-gradient(to bottom, rgba(50, 255, 0, 0.05), transparent);
                mix-blend-mode: color-dodge; animation: toxicDrift 10s infinite linear;"></div>
            <style>@keyframes toxicDrift { 0% { background-position: 0 0; } 100% { background-position: 100% 0; } }</style>
            """
            
        elif hazard_type == "earthquake":
            # Subtle Shake applied to main container globally is already handled, 
            # but maybe a crack overlay?
            overlay_html = """
            <div style="position:fixed; bottom:0; padding: 20px; width:100%; text-align:center; pointer-events:none; z-index:9000;
                color: rgba(255,0,0,0.5); font-family: 'Courier New'; font-size: 2rem; letter-spacing: 5px;
                animation: tremor 0.1s infinite;">
                SEISMIC INSTABILITY DETECTED
            </div>
            <style>@keyframes tremor { 0% { transform: translate(1px, 1px); } 100% { transform: translate(-1px, -1px); } }</style>
            """
        
        # V4: Cinematic Map Effects - Anomaly Ping (Generic for all hazards)
        overlay_html += """
        <div class="anomaly-ping" style="position:fixed; top:50%; left:50%; transform:translate(-50%, -50%); width:0px; height:0px; border-radius:50%; border: 2px solid rgba(255,0,0,0.5); z-index:9001; animation: pingRipple 4s infinite;"></div>
        <style>
        @keyframes pingRipple { 
            0% { width: 0; height: 0; opacity: 1; border-width: 5px; } 
            100% { width: 100vw; height: 100vw; opacity: 0; border-width: 0px; } 
        }
        </style>
        """

        if overlay_html:
            st.markdown(overlay_html, unsafe_allow_html=True)

    def play_sound_trigger(self, sound_type="click"):
        """Plays a one-shot sound effect."""
        if not st.session_state['theme_effects']['audio'] or st.session_state['theme_mode'] == 'standard':
            return
            
        # Placeholder sounds
        sounds = {
            "click": "https://cdn.pixabay.com/download/audio/2022/03/10/audio_c8c8a73467.mp3", # Glitch click
            "success": "https://cdn.pixabay.com/download/audio/2022/01/18/audio_d0a13f69d2.mp3", # Deep thud/whoosh
            "error": "https://cdn.pixabay.com/download/audio/2021/08/04/audio_0625c1539c.mp3" # Error buzz
        }
        
        url = sounds.get(sound_type, sounds["click"])
        
        # Auto-remove script to allow re-triggering? Streamlit handles script re-runs.
        # We use a unique ID based on time to force re-render if called multiple times?
        import time
        ts = int(time.time() * 1000)
        
        st.markdown(f"""
        <audio autoplay style="display:none;" id="sfx-{ts}">
            <source src="{url}" type="audio/mpeg">
        </audio>
        <script>
            var aud = document.getElementById("sfx-{ts}");
            aud.volume = 0.4;
            aud.play();
        </script>
        """, unsafe_allow_html=True)
