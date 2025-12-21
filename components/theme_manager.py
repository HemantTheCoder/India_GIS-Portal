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
                'transition': True  # Cinematic Transition
            }
        
        # Transition State
        if 'last_mode_switch' not in st.session_state:
            st.session_state['last_mode_switch'] = 0.0
        if 'mode_switch_direction' not in st.session_state:
            st.session_state['mode_switch_direction'] = None
            
            
        # Audio Assets Library REMOVED
        self.assets = {}
        
    def render_theme_controls(self):
        """Renders the theme toggle and controls in the sidebar."""
        st.sidebar.divider()
        st.sidebar.markdown("### 🌗 Dimension Switch")
        
        mode = st.sidebar.radio(
            "Current Reality Layer",
            ["Standard Mode", "Upside Down Mode"],
            index=0 if st.session_state['theme_mode'] == 'standard' else 1,
            label_visibility="collapsed"
        )
        
        new_mode = 'standard' if mode == "Standard Mode" else 'upside_down'
        if new_mode != st.session_state['theme_mode']:
            # Record Switch Event for Cinematic Transition
            import time
            st.session_state['last_mode_switch'] = time.time()
            st.session_state['mode_switch_direction'] = 'enter' if new_mode == 'upside_down' else 'exit'
            
            st.session_state['theme_mode'] = new_mode
            st.rerun()
            
        if st.session_state['theme_mode'] == 'upside_down':
            with st.sidebar.expander("Control Panel", expanded=False):
                # ---------------------------------------------------------
                # 1. CINEMATIC TRANSITION TOGGLE (CONTROLS & SAFETY)
                # ---------------------------------------------------------
                st.markdown("#### Transition")
                st.session_state['theme_effects']['transition'] = st.checkbox(
                    "Cinematic Transition", 
                    value=st.session_state['theme_effects']['transition'],
                    help="Cinematic visual transition representing entry into an alternate analytical mode."
                )

                st.markdown("#### Immersive Effects")
                col1, col2 = st.columns(2)
                with col1:
                    st.session_state['theme_effects']['fog'] = st.checkbox("Fog", value=st.session_state['theme_effects']['fog'])
                    st.session_state['theme_effects']['flicker'] = st.checkbox("Flicker", value=st.session_state['theme_effects']['flicker'])
                with col2:
                    st.session_state['theme_effects']['glow'] = st.checkbox("Glow", value=st.session_state['theme_effects']['glow'])
                    st.session_state['theme_effects']['grain'] = st.checkbox("Grain", value=st.session_state['theme_effects']['grain'])
                
                # Dynamic Stability Meter
                stability = random.randint(45, 85) # Fluctuate
                color = "#ef4444" if stability < 60 else "#f59e0b"
                bars = "█" * (stability // 10) + "░" * (10 - (stability // 10))
                
                st.markdown("---")
                st.markdown(f"""
                <div style="font-family: 'Roboto Mono'; color: #b0b0b0; font-size: 0.8rem;">
                    Reality Stability: <span style="color: {color}; font-weight: bold;">{bars} {stability}%</span>
                </div>
                """, unsafe_allow_html=True)

    def _queue_sound(self, sound_key):
        """Queue a sound to play on next render."""
        pass

    def apply_theme(self):
        """Injects the necessary CSS and JS for the current theme."""
        # 1. Handle Cinematic Transitions (Runs regardless of mode if recent switch)
        is_transitioning = self._handle_cinematic_transition()

        if st.session_state['theme_mode'] == 'standard':
            return
            
        # If transitioning, skip standard ambient loops to prevent CSS conflict
        if is_transitioning:
            # We still render the basics, but skip .stApp animation overrides
            pass
        
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

            /* Cards / Containers */
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

            /* --- MOBILE RESPONSIVENESS (Upside Down) --- */
            @media (max-width: 768px) {
                h1 {
                    font-size: 1.8rem !important; 
                    letter-spacing: 1px;
                }
                h2 { font-size: 1.5rem !important; }
                h3 { font-size: 1.2rem !important; }
                
                .stApp {
                    background-image: radial-gradient(circle at 50% 50%, #1a0505 0%, #000000 120%);
                }
                
                div[data-testid="column"] > div, div[data-testid="stExpander"] {
                    margin-bottom: 1rem;
                }
            }
        """

        # Append Effects based on toggles
        if st.session_state['theme_effects']['glow']:
            css += """
            @keyframes redPulse {
                0% { box-shadow: 0 0 5px #300; }
                50% { box-shadow: 0 0 20px #800; }
                100% { box-shadow: 0 0 5px #300; }
            }
            .stApp div[data-testid="column"] {
                animation: redPulse 4s infinite ease-in-out;
            }
            """
            
        if st.session_state['theme_effects']['flicker'] and not is_transitioning:
            css += """
            @keyframes flicker {
                0% { opacity: 0.97; } 5% { opacity: 0.9; } 10% { opacity: 0.97; } 15% { opacity: 1; }
                50% { opacity: 0.98; } 55% { opacity: 0.92; } 60% { opacity: 0.98; } 100% { opacity: 1; }
            }
            .stApp { animation: flicker 6s infinite; }
            """
            
        if st.session_state['theme_effects']['grain']:
            css += """
            .grain-overlay {
                position: fixed; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none; z-index: 9999;
                background-image: url("https://www.transparenttextures.com/patterns/stardust.png");
                opacity: 0.05;
            }
            """
            
        if st.session_state['theme_effects']['fog']:
            css += """
            .scanlines {
                position: fixed; top: 0; left: 0; width: 100vw; height: 100dvh;
                background: linear-gradient(to bottom, rgba(255,255,255,0), rgba(255,255,255,0) 50%, rgba(0,0,0,0.05) 50%, rgba(0,0,0,0.05));
                background-size: 100% 4px; animation: scanlineMove 10s linear infinite; pointer-events: none; z-index: 9991; opacity: 0.15;
            }
            @keyframes scanlineMove { from { background-position: 0 0; } to { background-position: 0 100%; } }

            .vignette-glow {
                position: fixed; top: 0; left: 0; width: 100vw; height: 100dvh;
                background: radial-gradient(circle, transparent 60%, rgba(50,0,0,0.3) 90%, rgba(20,0,0,0.8) 100%);
                pointer-events: none; z-index: 9990; animation: vignettePulse 8s ease-in-out infinite;
            }
            @keyframes vignettePulse { 0%, 100% { padding: 0; opacity: 0.7; } 50% { padding: 20px; opacity: 0.9; } }
            
            /* UI Refinements */
            h1 { font-size: 3rem !important; border-bottom: 2px solid rgba(255, 15, 15, 0.6) !important; box-shadow: 0 4px 6px -4px rgba(255, 0, 0, 0.4); padding-bottom: 0.5rem; text-shadow: 0 0 10px rgba(255,0,0,0.3); }
            div[data-testid="column"] > div, div[data-testid="stExpander"], div.stDataFrame {
                transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275); border: 1px solid rgba(80, 0, 0, 0.1) !important; background-color: rgba(10, 0, 0, 0.6) !important;
            }
            div[data-testid="column"] > div:hover, div[data-testid="stExpander"]:hover {
                transform: scale(1.01) translateY(-2px); box-shadow: 0 0 15px rgba(255, 30, 30, 0.3) !important; border-color: rgba(255, 15, 15, 0.6) !important; z-index: 10;
            }
            div[data-testid="stAlert"] { animation: warningPulse 4s infinite ease-in-out; border: 1px solid rgba(249, 115, 22, 0.5); }
            @keyframes warningPulse { 0% { border-color: rgba(249, 115, 22, 0.3); } 50% { border-color: rgba(249, 115, 22, 0.9); box-shadow: 0 0 15px rgba(249, 115, 22, 0.3); } 100% { border-color: rgba(249, 115, 22, 0.3); } }
            
            section[data-testid="stSidebar"] {
                background-color: #050000 !important;
                background-image: linear-gradient(90deg, rgba(50,0,0,0.1) 1px, transparent 1px), linear-gradient(rgba(50,0,0,0.1) 1px, transparent 1px), url("https://www.transparenttextures.com/patterns/black-scales.png") !important;
                background-size: 20px 20px, 20px 20px, auto; border-right: 3px solid #3d0000 !important;
            }
            
            iframe { animation: mapBreathe 8s ease-in-out infinite; filter: contrast(1.1) brightness(0.9); }
            @keyframes mapBreathe { 0%, 100% { filter: contrast(1.1) brightness(0.9) saturate(0.8); } 50% { filter: contrast(1.2) brightness(1.0) saturate(1.1); box-shadow: 0 0 20px rgba(50,0,0,0.15); } }
            """
            
            css += """
            /* ALIVE RED LINE */
            h1 { border-bottom: none !important; position: relative; padding-bottom: 0.5rem; }
            h1::after {
                content: ''; position: absolute; bottom: 0; left: 0; width: 100%; height: 2px;
                background: linear-gradient(90deg, transparent, #ff0f0f, transparent); background-size: 200% 100%;
                animation: energyFlow 4s infinite linear; box-shadow: 0 0 8px rgba(255, 15, 15, 0.6);
            }
            @keyframes energyFlow { 0% { background-position: 100% 0; } 100% { background-position: -100% 0; } }

            .fog-container { mask-image: linear-gradient(to bottom, transparent, black 40%); -webkit-mask-image: linear-gradient(to bottom, transparent, black 40%); }
            
            .glitch-text { position: relative; display: inline-block; color: #ff0f0f; }
            .glitch-text::before, .glitch-text::after { content: attr(data-text); position: absolute; top: 0; left: 0; width: 100%; background: #0a0a0d; clip: rect(0, 0, 0, 0); }
            .glitch-text::before { left: -2px; text-shadow: 1px 0 #00f; animation: glitch-sparse-1 10s infinite linear alternate-reverse; }
            .glitch-text::after { left: 2px; text-shadow: -1px 0 #f00; animation: glitch-sparse-2 15s infinite linear alternate-reverse; }
            @keyframes glitch-sparse-1 { 0%, 92% { clip: rect(0,0,0,0); } 93% { clip: rect(20px, 9999px, 15px, 0); } 95% { clip: rect(10px, 9999px, 85px, 0); } 97% { clip: rect(80px, 9999px, 5px, 0); } 100% { clip: rect(30px, 9999px, 60px, 0); } }
            @keyframes glitch-sparse-2 { 0%, 94% { clip: rect(0,0,0,0); } 95% { clip: rect(10px, 9999px, 80px, 0); } 98% { clip: rect(40px, 9999px, 30px, 0); } 100% { clip: rect(50px, 9999px, 20px, 0); } }

            /* HEADER GLITCH (Applied via JS) */
            .glitch-header { position: relative; display: inline-block; color: #ff0f0f !important; }
            .glitch-header::before, .glitch-header::after { 
                content: attr(data-text); position: absolute; top: 0; left: 0; width: 100%; height: 100%; background: #0a0a0d; 
            }
            .glitch-header::before { 
                left: -2px; text-shadow: 2px 0 #00f; clip: rect(24px, 550px, 90px, 0); animation: glitch-sparse-1 8s infinite linear alternate-reverse; z-index: -1;
            }
            .glitch-header::after { 
                left: 2px; text-shadow: -2px 0 #f00; clip: rect(85px, 550px, 140px, 0); animation: glitch-sparse-2 10s infinite linear alternate-reverse; z-index: -2;
            }

            .stApp::before {
                content: ""; position: fixed; top: -50%; left: -50%; width: 200%; height: 200%;
                background: radial-gradient(circle, rgba(255, 100, 100, 0.05) 0%, transparent 60%); pointer-events: none; z-index: 9992;
                animation: lightShift 20s infinite ease-in-out;
            }
            @keyframes lightShift { 0% { transform: translate(0, 0); } 25% { transform: translate(10%, 10%); } 50% { transform: translate(-5%, 20%); } 75% { transform: translate(-10%, -5%); } 100% { transform: translate(0, 0); } }

            /* LEDS */
            h1::before, h2::before, h3::before {
                content: ''; display: inline-block; width: 6px; height: 6px; background-color: #22c55e; border-radius: 50%; margin-right: 12px; box-shadow: 0 0 6px #22c55e; vertical-align: middle; animation: statusBlink 4s infinite; opacity: 0.8;
            }
            section[data-testid="stSidebar"] h1::before, section[data-testid="stSidebar"] h2::before, section[data-testid="stSidebar"] h3::before {
                content: ''; display: inline-block; width: 5px; height: 5px; background-color: #f59e0b; border-radius: 50%; margin-right: 8px; box-shadow: 0 0 5px #f59e0b; animation: statusBlink 3s infinite reverse;
            }
            @keyframes statusBlink { 0%, 100% { opacity: 0.9; transform: scale(1); } 50% { opacity: 0.4; transform: scale(0.9); } }

            .stApp::after {
                content: ""; position: fixed; bottom: -20px; right: -20px; width: 300px; height: 300px;
                background: radial-gradient(circle, rgba(255,50,0,0.15), transparent); filter: blur(40px); pointer-events: none; z-index: 9993;
            }
            """

        css += "</style>"
        
        # Inject Overlays (Visuals)
        overlays = ""
        # ... [Visual Overlays Logic Preserved] ...
        if st.session_state['theme_effects']['grain']: overlays += '<div class="scanlines"></div>'
        overlays += '<div class="vignette-glow"></div>'
        if st.session_state['theme_effects']['fog']:
            overlays += """
<div class="fog-container" style="position: fixed; top:0; left:0; width:100%; height:100%; pointer-events:none; z-index:9980; opacity:0.25;">
    <div class="fog-layer-1" style="background:url('https://raw.githubusercontent.com/danielstuart14/CSS_FOG_ANIMATION/master/fog1.png'); width:200%; height:100%; animation: fogmove 20s linear infinite;"></div>
    <div class="fog-layer-2" style="background:url('https://raw.githubusercontent.com/danielstuart14/CSS_FOG_ANIMATION/master/fog2.png'); width:200%; height:100%; animation: fogmove 10s linear infinite; opacity:0.5;"></div>
</div>
<style>@keyframes fogmove { 0% { transform: translate3d(0, 0, 0); } 100% { transform: translate3d(-50%, 0, 0); } }</style>
"""
        st.markdown(css + overlays, unsafe_allow_html=True)

        # JS Injection for Header Glitch
        js_glitch = """
        <script>
        (function() {
            function applyGlitchToHeaders() {
                const headers = window.parent.document.querySelectorAll('h1, h2, h3');
                headers.forEach(h => {
                    if (!h.classList.contains('glitch-header')) {
                        h.setAttribute('data-text', h.innerText);
                        h.classList.add('glitch-header');
                    }
                });
            }
            // Run initially and then on interval to catch re-renders
            setTimeout(applyGlitchToHeaders, 500);
            setInterval(applyGlitchToHeaders, 2000);
        })();
        </script>
        """
        st.components.v1.html(js_glitch, height=0, width=0)

        
        # Audio Engine Injection - REMOVED
            
        # V4: Silent Narrative & System Logs
        self._render_narrative_layer()

    def _render_narrative_layer(self):
        """Renders subtle narrative elements and system logs."""
        if st.session_state['theme_mode'] != 'upside_down':
            return

        # 1. Silent Narrative Text (Bottom Right)
        if 'narrative_step' not in st.session_state: st.session_state.narrative_step = 0
        
        narrative_lines = [
            "STATUS: DIMENSIONAL BREACH DETECTED",
            "WARNING: REALITY INTEGRITY < 85%",
            "ALERT: LOCALIZED TEMPORAL DISTORTION",
            "CRITICAL: CONTAINMENT PROTOCOL FAILING",
            "SYSTEM: RECALIBRATING SENSORS..."
        ]
        
        import time
        current_idx = int(time.time() / 15) % len(narrative_lines)
        current_msg = narrative_lines[current_idx]
        
        st.markdown(f"""
        <div style="position: fixed; bottom: 10px; right: 20px; color: rgba(255, 0, 0, 0.4); 
             font-family: 'Roboto Mono'; font-size: 0.7rem; pointer-events: none; z-index: 9995;">
             {current_msg}
        </div>
        """, unsafe_allow_html=True)

        # 2. System Logs (Sidebar)
        with st.sidebar.expander("[ SYSTEM LOGS ]", expanded=False):
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
            
            display_logs = random.sample(logs_pool, k=7)
            
            log_html = "<div style='font-family: monospace; font-size: 0.7rem; color: #aaa; line-height: 1.2;'>"
            for log in display_logs:
                border_style = "border-left: 2px solid red; padding-left:5px;" if "ANOMALY" in log else ""
                log_html += f"<div style='margin-bottom:2px; {border_style}'> > {log}</div>"
            log_html += "</div>"
            st.markdown(log_html, unsafe_allow_html=True)

    def get_text(self, standard_text, upside_down_text=None):
        """Returns the text, applying glitch effects or switching content if in immersive mode."""
        if st.session_state['theme_mode'] == 'upside_down':
            if upside_down_text:
                return self.wrap_anomalies(upside_down_text)
            return self.wrap_anomalies(standard_text)
        return standard_text

    def wrap_anomalies(self, text):
        """V4: Wraps specific keywords in glitch text span."""
        if st.session_state['theme_mode'] != 'upside_down':
            return text
            
        keywords = ["ANOMALY", "BREACH", "RIFT", "ERROR", "WARNING", "CRITICAL", "FAILURE", "UNKNOWN"]
        
        for k in keywords:
            if k in text or k.title() in text:
                replacement = f"<span class='glitch-text' data-text='{k}'>{k}</span>"
                text = text.replace(k, replacement).replace(k.title(), replacement)
        return text

    def render_hazard_overlay(self, hazard_type):
        """Renders specific atmospheric overlays based on hazardous state."""
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
            # Crack overlay
            overlay_html = """
            <div style="position:fixed; bottom:0; padding: 20px; width:100%; text-align:center; pointer-events:none; z-index:9000;
                color: rgba(255,0,0,0.5); font-family: 'Courier New'; font-size: 2rem; letter-spacing: 5px;
                animation: tremor 0.1s infinite;">
                SEISMIC INSTABILITY DETECTED
            </div>
            <style>@keyframes tremor { 0% { transform: translate(1px, 1px); } 100% { transform: translate(-1px, -1px); } }</style>
            """
        
        # Anomaly Ping (Generic for all hazards)
        overlay_html += """
        <div class="anomaly-ping" style="position:fixed; top:50%; left:50%; transform:translate(-50%, -50%); width:0px; height:0px; border-radius:50%; border: 2px solid rgba(255,0,0,0.5); z-index:9001; pointer-events: none; animation: pingRipple 12s infinite;"></div>
        <style>
        @keyframes pingRipple { 
            0% { width: 0; height: 0; opacity: 0.4; border-width: 5px; } 
            100% { width: 100vw; height: 100vw; opacity: 0; border-width: 0px; } 
        }
        </style>
        """

        if overlay_html:
            st.markdown(overlay_html, unsafe_allow_html=True)

    def play_sound_trigger(self, sound_type="click"):
        """Plays a one-shot sound effect respecting user settings."""
        pass

    def _handle_cinematic_transition(self):
        """Injects cinematic transition CSS. Returns True if transition is active."""
        if not st.session_state['theme_effects'].get('transition', True):
            return False

        import time
        now = time.time()
        start = st.session_state.get('last_mode_switch', 0)
        direction = st.session_state.get('mode_switch_direction')
        
        # Phase 1/2 window: 2.0s for Enter, 1.0s for Exit
        # We extend the window slightly to ensure lock
        duration = 2.5 if direction == 'enter' else 1.5
        
        if now - start > duration:
            return False

        # Generate CSS
        css = ""
        if direction == 'enter':
            css = """
            <style>
            /* ENTER SEQUENCE: Standard -> Upside Down */
            @keyframes dimensionalRotate {
                0% { transform: scale(1) rotate(0deg); filter: brightness(1) blur(0px); }
                20% { transform: scale(0.95) rotate(5deg); filter: brightness(0.8) blur(1px) sepia(0.2); }
                50% { transform: scale(0.9) rotate(180deg); filter: brightness(0.5) blur(3px) contrast(1.2); }
                80% { transform: scale(1.02) rotate(355deg); filter: brightness(0.7) blur(1px) hue-rotate(-20deg); }
                100% { transform: scale(1) rotate(360deg); filter: brightness(1) blur(0px); }
            }
            
            /* Overlay for Init Phase */
            @keyframes overlayFade {
                0% { opacity: 0; } 30% { opacity: 1; } 90% { opacity: 1; } 100% { opacity: 0; pointer-events: none; }
            }

            .stApp {
                animation: dimensionalRotate 2s cubic-bezier(0.45, 0, 0.55, 1) forwards !important;
                transform-origin: center center;
                overflow: hidden !important; 
            }

            .cinematic-overlay {
                position: fixed; top: 0; left: 0; width: 100vw; height: 100dvh;
                background: radial-gradient(circle, transparent 40%, rgba(50,0,0,0.8) 100%);
                z-index: 10000; pointer-events: none;
                animation: overlayFade 2s ease-in-out forwards !important;
                display: flex; align-items: center; justify-content: center;
                color: rgba(255, 50, 50, 0.7); font-family: 'Courier New'; font-size: 1.2rem; letter-spacing: 4px;
            }
            </style>
            <div class="cinematic-overlay">CROSSING DIMENSIONAL BOUNDARY...</div>
            """
        elif direction == 'exit':
            css = """
            <style>
            /* EXIT SEQUENCE: Upside Down -> Standard */
            @keyframes snapBack {
                0% { transform: scale(1) rotate(0deg); filter: contrast(1.1) brightness(0.9); }
                40% { transform: scale(0.98) rotate(-5deg); filter: blur(2px); }
                100% { transform: scale(1) rotate(0deg); filter: none; }
            }
            
            .stApp {
                animation: snapBack 1s cubic-bezier(0.25, 1, 0.5, 1) forwards !important;
            }
            </style>
            """
            
        if css:
            st.markdown(css, unsafe_allow_html=True)
            return True
            
        return False
