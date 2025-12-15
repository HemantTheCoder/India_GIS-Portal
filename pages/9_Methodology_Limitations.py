import streamlit as st
from components.ui import apply_enhanced_css, render_page_header, render_info_box

st.set_page_config(layout="wide", page_title="Methodology & Limitations")

# Apply Theme
apply_enhanced_css()

# Header
render_page_header("📚 Methodology & Limitations", 
                   "Technical details, data sources, scoring logic, and platform disclaimers")
st.markdown("""
<style>
/* Remove Streamlit default padding */
.block-container {
    padding-top: 0rem !important;
    padding-bottom: 0rem !important;
    padding-left: 1rem !important;
    padding-right: 1rem !important;
}

/* Hide header & footer */
header {visibility: hidden;}
footer {visibility: hidden;}

/* Remove "Built with Streamlit" space */
.viewerBadge_container__1QSob {
    display: none !important;
}

/* Prevent double scrollbars */
html, body {
    overflow: hidden;
}
</style>
""", unsafe_allow_html=True)
# --- Section 1: Overview ---
with st.expander("ℹ️ Overview of the GIS Portal", expanded=True):
    st.markdown("""
    ### Purpose & Scope
    The **India GIS Portal** is a multi-hazard geospatial analytics and decision-support system designed to provide comprehensive environmental and risk assessments for Indian cities and regions. 
    It leverages satellite imagery, open-source data, and advanced processing algorithms to monitor urban sustainability indicators.

    **Key Capabilities:**
    - **Live Monitoring:** Real-time visualization of environmental parameters.
    - **Multi-Criteria Analysis:** Integrated assessment of vegetation, air quality, urban heat, and seismic risk.
    - **Data-Driven Scoring:** Standardized scoring mechanisms to compare regions objectively.
    - **Predictive Modeling:** AI-based forecasts for future environmental trends.
    """)

# --- Section 2: Data Sources ---
with st.expander("🛰️ Data Sources"):
    st.markdown("""
    The platform integrates data from multiple high-resolution satellite missions and reputable global datasets:

    | Parameter | Source | Resolution | Frequency | Description |
    |-----------|--------|------------|-----------|-------------|
    | **Vegetation (NDVI/EVI)** | Sentinel-2 (ESA) | 10m | 5 days | High-resolution optical imagery for assessing green cover health and density. |
    | **Land Use / Land Cover** | Sentinel-2 / ESRI Land Cover | 10m | Annual | Classification of built-up areas, water bodies, cropland, and forests. |
    | **Air Quality (NO₂, CO, O₃)** | Sentinel-5P TROPOMI | 3.5x5.5km | Daily | Atmospheric monitoring of trace gases and pollutants. |
    | **Aerosols (AOD)** | MODIS (NASA) / Sentinel-5P | 1km / 3.5km | Daily | Measurement of particulate matter distribution. |
    | **Land Surface Temperature** | Landsat 8/9 (TIRS) | 30m (resampled) | 16 days | Thermal band analysis for Urban Heat Island (UHI) detection. |
    | **Earthquake Hazard** | USGS / GEM / GSHAP | Regional | Static | Seismic zone maps, peak ground acceleration (PGA), and fault line proximity. |
    | **Future Climate Risk** | CMIP6 / Proxy Datasets | ~25km | Projected | Long-term climate scenario projections (SSP2-4.5/8.5). |
    
    > *Note: Data availability depends on satellite overpass schedules and cloud coverage conditions.*
    """)

# --- Section 3: Analysis Workflow ---
with st.expander("⚙️ Analysis Workflow"):
    st.markdown("""
    The system follows a standardized processing pipeline for all analytical modules:

    1. **Region Selection (AOI):**
       - User selects a City/State or uploads a Shapefile/GeoJSON.
       - The system extracts the geometry and defines the **Area of Interest (AOI)**.

    2. **Data Acquisition (GEE):**
       - The backend connects to **Google Earth Engine (GEE)** API.
       - Relevant image collections are filtered by date, bounds, and cloud cover (<20%).

    3. **Preprocessing & Masking:**
       - **Cloud Masking:** Removing cloudy pixels to ensure data quality.
       - **Clipping:** Trimming data to the exact AOI boundaries.
       - **Resampling:** Aligning grids if resolutions differ.

    4. **Index Calculation:**
       - Computing spectral indices (e.g., NDVI for vegetation, LST for heat).
       - $NDVI = (NIR - Red) / (NIR + Red)$
       - $LST = K_2 / \ln(\epsilon \cdot K_1 / L_\lambda + 1)$

    5. **Zonal Statistics:**
       - Aggregating pixel values to compute mean, median, min, and max for the region.
       - Generating histograms and area-class distributions.

    6. **Visualization:**
       - Rendering interactive folium maps.
       - Generating charts and downloadable reports.
    """)

# --- Section 4: Scoring & Normalization ---
with st.expander("📊 Scoring & Normalization Methodology"):
    st.markdown("""
    To enable cross-regional comparison, raw values are normalized into a **0–100 scale**, where higher scores indicate better sustainability or lower risk.

    #### 1. Module-Level Normalization
    Each module (Vegetation, Air Quality, Heat, Risk, Seismic) computes a raw score which is then normalized based on established thresholds:

    - **Vegetation Score:** Based on the percentage of healthy vegetation ($NDVI > 0.4$) vs. barren/built-up land.
    - **Air Quality Score (100 - AQI):** Inverse of the Air Quality Index; cleaner air yields a higher score.
    - **Heat Resilience Score:** Based on the inverse variation of Land Surface Temperature (LST) from the regional mean.
    - **Seismic Safety:** Inverse of the Peak Ground Acceleration (PGA) and Fault Proximity risk.

    #### 2. Composite Sustainability Score (USS)
    The **Urban Sustainability Score (USS)** is a weighted average of individual module scores.

    $$ 
    USS = \sum (W_i \times S_i) 
    $$
    
    Where:
    - $S_{veg}$ (Vegetation) Weight: **20%**
    - $S_{aqi}$ (Air Quality) Weight: **20%**
    - $S_{heat}$ (Thermal Comfort) Weight: **20%**
    - $S_{risk}$ (Future Resilience) Weight: **20%**
    - $S_{quake}$ (Seismic Safety) Weight: **20%**

    *Currently, an equal weighting scheme (20% each) is applied to ensure balanced holistic assessment, totaling 100.*

    #### 3. Risk Classification
    | Score Range | Classification | Indicator Color |
    |-------------|----------------|-----------------|
    | **80 – 100** | Excellent | 🟢 Green |
    | **60 – 79** | Good | 🔵 Blue |
    | **40 – 59** | Moderate | 🟡 Yellow |
    | **20 – 39** | Poor | 🟠 Orange |
    | **0 – 19** | Critical | 🔴 Red |
    """)

# --- Section 5: Comparison Module Logic ---
with st.expander("⚖️ Comparison Module Logic"):
    st.markdown("""
    The **Comparison Module** allows for side-by-side evaluation of two distinct regions (Region A vs. Region B) or two time periods.

    **Mechanism:**
    - The backend explicitly triggers the analysis pipeline twice, once for each geometry.
    - Results are stored in independent session states.
    - A "Difference Metric" ($\Delta$) is computed: 
      $$ \Delta = Val_A - Val_B $$
    - **Radar Charts** are used to visualize the multivariate balance between the two regions across all 5 dimensions.
    """)

# --- Section 6: Limitations & Disclaimer ---
st.markdown("### ⚠️ Limitations & Disclaimer")

render_info_box("""<div style="display: flex; gap: 2rem; align-items: flex-start; flex-wrap: wrap;">
<div style="flex: 1; min-width: 300px;">
<strong style="color: #fca5a5; font-size: 1.05rem;">Academic & Research Use Only:</strong>
<p style="margin-top: 0.5rem; line-height: 1.6;">
This platform is intended for <strong>academic, research, and exploratory purposes only</strong>. 
It should <strong>NOT</strong> be used for:
</p>
<ul style="margin-top: 0.5rem; padding-left: 1.2rem; color: #fecaca;">
<li>Operational disaster response or emergency management.</li>
<li>Legal or regulatory compliance certification.</li>
<li>Real-estate valuation or insurance underwriting.</li>
</ul>
</div>
<div style="width: 1px; background: rgba(255,255,255,0.1); align-self: stretch;"></div>
<div style="flex: 1; min-width: 300px;">
<strong style="color: #fca5a5; font-size: 1.05rem;">Key Limitations:</strong>
<ul style="margin-top: 0.5rem; padding-left: 1.2rem; line-height: 1.6;">
<li style="margin-bottom: 0.5rem;">
<strong>Resolution:</strong> Analysis is limited by the spatial resolution of satellite sensors (e.g., 10m for Sentinel-2, ~3.5km for Sentinel-5P). Small-scale features may be missed.
</li>
<li style="margin-bottom: 0.5rem;">
<strong>Cloud Cover:</strong> Optical satellite data (Sentinel-2, Landsat) cannot penetrate clouds. During monsoon seasons, data accumulation may be sparse or interpolated.
</li>
<li style="margin-bottom: 0.5rem;">
<strong>Temporal Latency:</strong> Data is not strictly "real-time" but "near real-time," subject to processing delays (typically 24-48 hours).
</li>
<li>
<strong>Model Assumptions:</strong> Predictive models and risk scores are based on simplified assumptions and proxy datasets, which may not capture local micro-phenomena.
</li>
</ul>
</div>
</div>""", box_type="warning")

st.markdown("""
<div style="text-align: center; color: #64748b; font-size: 0.8rem; margin-top: 2rem;">
    <em>Methodology last updated: December 2025 | Version 1.0</em>
</div>
""", unsafe_allow_html=True)
