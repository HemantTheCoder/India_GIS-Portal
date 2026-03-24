📌 India GIS & Remote Sensing Portal
====================================

A state-of-the-art, web-based GIS and Remote Sensing application built using **Streamlit + Google Earth Engine**. Designed to provide holistic urban analytics, environmental monitoring, and disaster resilience insights for cities across India.

🚀 **Special Edition: WATER INNOVATION HACKATHON 2026**
This portal now features **Jala-AI**, an advanced hydrological monitoring module developed for the "AI for Disaster Preparedness" track.

🌍 Overview
----------

The portal transforms raw satellite data into actionable intelligence across six critical dimensions of urban sustainability. It enables researchers, urban planners, and disaster management authorities to visualize high-resolution geospatial data and generate comprehensive sustainability reports.

⭐ Core Modules
--------------

1. **🌿 Vegetation & LULC**: Dynamic World land use classification and NDVI health monitoring.
2. **💨 Air Quality (AQI)**: Sentinel-5P based monitoring of PM2.5, NO2, and other pollutants.
3. **🔥 Urban Heat & Climate**: Land Surface Temperature (LST) mapping and heat island detection.
4. **🧠 Predictive Analysis**: AI-driven trend forecasting for urban expansion.
5. **🌋 Earthquake Hazard**: Seismic zone mapping and comprehensive risk scoring (IS 1893:2025).
6. **💧 Jala-AI (Water Resilience)**: Radar-based flood watch and surface water dynamics.

🛰️ Tech Stack & Data Sources
----------------------------

- **Framework**: Streamlit (Python)
- **Engine**: Google Earth Engine (GEE)
- **Imagery**: Sentinel-1 (Radar), Sentinel-2 (Optical), Landsat 8/9, Sentinel-5P (AQI)
- **Climate Data**: NASA GPM (Rainfall IMERG V07), MODIS (Temperature)
- **Mapping**: Folium, Geemap, Leaflet

💧 Jala-AI: Water Innovation Feature
------------------------------------

Developed for the **Water Innovation Hackathon 2026**, this module focuses on:

- **Active Flood Watch**: Using Sentinel-1 SAR (Radar) to detect flood inundation through cloud cover during extreme weather.
- **Surface Water Dynamics**: NDWI-based monitoring of reservoirs, lakes, and wetlands to detect drought patterns.
- **Rainfall Risk HUD**: Visualizing cumulative precipitation using NASA GPM IMERG V07 data.
- **Scientific Transparency**: Built-in methodology and data limitation disclosures to account for satellite revisit times and cloud interference.
- **Gender-Socio Resilience**: Strategic mapping for Women's Self-Help Groups (SHGs) to manage local water accessibility during disasters.

📊 Urban Sustainability Score (USS)
-----------------------------------

The portal features a unique **USS Engine** that aggregates data from all modules to provide a holistic 0-100 score for any Indian city.

- **Grade A (80-100)**: Excellent resilience and environmental health.
- **Grade F (< 20)**: Critical intervention required.

🏗️ Project Structure
--------------------

```text
├── app.py                      # Main Landing Page & Feature Grid
├── services/
│   ├── gee_core.py             # GEE Initialization & Geometry Helpers
│   ├── gee_water.py            # [NEW] Jala-AI Water Analytics
│   ├── gee_aqi.py              # Sentinel-5P Pollutant Logic
│   ├── earthquake_core.py      # Seismic Risk Engine
│   └── sustainability_report.py # USS Scoring & Report Generation
├── pages/
│   ├── 1_LULC_Vegetation.py
│   ├── 2_AQI_Analysis.py
│   ├── 10_Jala_AI_Water_Resilience.py # Jala-AI Dashboard
│   └── ...
└── components/                 # Reusable UI & Map Components
```

⚙️ Setup & Authentication
-------------------------

1. **GEE Credentials**: Ensure you have a service account and the `service_account.json` is configured.
2. **Environment**:

    ```bash
    pip install -r requirements.txt
    streamlit run app.py
    ```

👨‍💻 Author
----------

**Hemant Kumar**  
*GIS Developer | AI for Sustainability*  
[LinkedIn](https://www.linkedin.com/in/hemantkumar2430)
