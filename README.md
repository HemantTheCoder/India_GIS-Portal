📌 India GIS & Remote Sensing Portal

A modern, web-based GIS and Remote Sensing application built using Streamlit + Google Earth Engine, designed to analyze Land Use / Land Cover (LULC) and vegetation indices for cities across India.

🌍 Overview

This portal enables users to perform geospatial analysis using satellite data, visualize results interactively, and export insights for reporting or research workflows.

It supports:

City-level spatial analysis across India

High-resolution satellite imagery

Dynamic World LULC classification

Vegetation & urban index computations

Time-series land use change analysis

Custom AOI drawing tools

Exportable maps and statistics

🚀 Current Status
Attribute	Status
Project State	✔️ Complete with enhanced LULC functionality
Last Updated	December 2, 2025
Tech Stack	Streamlit • Google Earth Engine • Python
⭐ Features
📍 Location Selection

Select any Indian state

Choose from 200+ major cities

Automatically loads geographic coordinates

Adjustable buffer radius (5–50 km)

🗓️ Date Range & Time Control

Analyze a single year or custom date range

Support for data starting from 2017

Compare two different years to study land cover change

🛰️ Satellite Data Sources

Sentinel-2 (10m resolution)

Landsat 8/9 (30m resolution)

Cloud filtering is automatically applied for optimal imagery quality.

🏞️ Land Use / Land Cover (LULC) Analysis

Based on the Google Dynamic World dataset, supporting 9 classes:

Water

Trees

Grass

Crops

Shrubland

Built-up

Bare ground

Flooded vegetation

Snow/Ice

Includes:

Interactive map visualization

Color-coded legend

Area (km²) and percentage breakdown

Custom AOI statistics

🌿 Vegetation & Urban Indices

Compute the following indices dynamically over your AOI:

Index	Purpose
NDVI	Vegetation health
NDWI	Water body detection
NDBI	Built-up area detection
EVI	Enhanced vegetation index
SAVI	Soil-adjusted vegetation

Each index is displayed with a full gradient legend for interpretation.

🗺️ Interactive Map (Folium)

Layer toggles (RGB, LULC, indices, etc.)

Zoom, pan, and inspect satellite layers

Circle AOI based on buffer radius

Custom AOI drawing (rectangle, circle, polygon)

📊 Analytics & Statistics

Per-class LULC area (km²)

Percentage distribution

Time-series LULC change analysis

Informative legends & progress indicators

💾 Export Options

Export outputs for further research & GIS workflows:

CSV files (LULC statistics, change detection tables)

GeoTIFF export links (Satellite imagery downloads)

🏗️ Project Architecture
📁 File Structure
├── Home.py             # Main Streamlit application
├── india_cities.py     # State-city database with coordinates
├── gee_utils.py        # Google Earth Engine helper functions
├── pyproject.toml      # Project dependencies
└── .streamlit/
    └── config.toml     # Streamlit theme & configuration

🔧 Key Components
india_cities.py

Contains:

The INDIA_DATA dictionary

Mapping of states → major cities → (lat, lon)

Covers 36 States/UTs and 200+ cities

gee_utils.py

Handles all Earth Engine operations:

GEE initialization & authentication

Sentinel-2 & Landsat image retrieval

Cloud masking logic

Dynamic World LULC extraction

Vegetation index computation

LULC statistics & area calculations

Year-to-year LULC change analysis

Generating exportable GeoTIFF URLs

Producing tile layers for Folium display

app.py

Implements:

UI & sidebar layout

State, city, and date selectors

Satellite source selection

AOI selection (buffer or custom geometry)

Map rendering (Folium + Streamlit)

LULC & index visualizations

Time-series comparison panel

Statistics display and download buttons

🎨 User Experience

Clean, intuitive layout

Clear color-coded legends

Progress bars for LULC distribution

Download buttons for quick export

Full-width map display for clarity

⚙️ Technical Notes

Requires a Google Earth Engine service account key
(stored in st.secrets["GEE_JSON"])

Dynamic World LULC available from 2017

Uses <20% cloud cover for imagery filtering

AOI radius: 5–50 km

Custom AOI supported via Folium Draw tools

📦 Dependencies
streamlit
earthengine-api
folium
streamlit-folium
pandas
numpy

💡 Future Enhancements (Optional)

Potential features to add next:

Sentinel-5P Air Quality (NO₂, SO₂, CO, O₃, CH₄, AAI)

AQI anomaly and plume detection

Multi-layer comparison visualizations

Time-series charts for AQI metrics

Multi-pollutant comparison dashboards

👨‍💻 Author

Hemant Kumar
LinkedIn: https://www.linkedin.com/in/hemantkumar2430
geemap
folium
streamlit-folium
pandas
numpy
matplotlib
geopandas
