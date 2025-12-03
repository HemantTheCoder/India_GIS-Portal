# India GIS & Remote Sensing Portal

## Overview
A comprehensive web-based GIS and Remote Sensing application for analyzing Land Use/Land Cover (LULC), vegetation indices, and air quality for Indian cities using Google Earth Engine and Sentinel satellite data.

## Current State
- **Status**: Complete with Multi-Module Architecture
- **Last Updated**: December 3, 2025

## Features

### LULC & Vegetation Analysis Module
1. **Location Selection**: Dropdown menus for selecting any state and city in India (200+ cities covered)
2. **Date Range Selection**: Full year or custom date range from 2017 onwards
3. **Satellite Data Sources**:
   - Sentinel-2 (10m resolution)
   - Landsat 8/9 (30m resolution)
4. **LULC Analysis**: Using Google's Dynamic World dataset with 9 land cover classes
5. **Vegetation Indices**: NDVI, NDWI, NDBI, EVI, SAVI calculations with standardized ranges
6. **Interactive Map**: Folium-based map with layer controls and opacity sliders
7. **Pixel Inspector**: Click on map to view index values at any location
8. **Statistics**: Land cover percentage and area (km²) breakdown with pie/bar charts
9. **Time Series Analysis**: Compare LULC changes between years with change summaries
10. **Custom AOI Drawing**: Draw custom areas on map for specific region analysis
11. **Export/Download**: CSV statistics, GeoTIFF exports, PDF reports

### Air Quality (AQI) Analysis Module
1. **Pollutant Monitoring**: NO₂, SO₂, CO, O₃, UVAI, CH₄ from Sentinel-5P
2. **AOI Statistics**: Mean, median, std dev, percentiles, min/max
3. **Anomaly Maps**: Compare current levels to 2019 baseline
4. **Smoothed/Plume Maps**: Gaussian smoothed visualization
5. **Hotspot Detection**: Areas exceeding mean + 1.5σ threshold
6. **Time Series Analysis**: Track pollutant trends with rolling averages
7. **Multi-Pollutant Dashboard**: Correlation heatmaps, radar charts, comparison charts
8. **Export**: CSV statistics, GeoTIFF downloads

## Project Architecture

### File Structure
```
├── app.py                      # Main homepage/landing page
├── pages/
│   ├── 1_LULC_Vegetation.py   # LULC & vegetation analysis page
│   └── 2_AQI_Analysis.py      # Air quality analysis page
├── components/
│   ├── __init__.py
│   ├── ui.py                  # Shared UI components and CSS
│   ├── maps.py                # Map creation and layer helpers
│   ├── charts.py              # Chart rendering (pie, bar, line, radar)
│   └── legends.py             # Legend rendering for indices and pollutants
├── services/
│   ├── __init__.py
│   ├── gee_core.py            # Core GEE functions (init, geometry, downloads)
│   ├── gee_lulc.py            # LULC and satellite image functions
│   ├── gee_indices.py         # Vegetation index calculations
│   ├── gee_aqi.py             # Air quality/Sentinel-5P functions
│   └── exports.py             # CSV and PDF export functions
├── india_cities.py            # Indian cities database
├── gee_utils.py               # Legacy utilities (kept for compatibility)
├── pyproject.toml             # Python dependencies
└── .streamlit/
    ├── config.toml            # Streamlit configuration
    └── secrets.toml           # GEE service account credentials
```

### Key Components

#### Services Layer
- **gee_core.py**: GEE authentication, geometry helpers, download URL generation, pixel sampling
- **gee_lulc.py**: Sentinel-2/Landsat fetching, Dynamic World LULC, change analysis
- **gee_indices.py**: NDVI, NDWI, NDBI, EVI, SAVI with standardized ranges (-1 to 1, SAVI 0 to 1)
- **gee_aqi.py**: Sentinel-5P pollutant fetching, statistics, anomaly/hotspot detection, time series
- **exports.py**: CSV generation, PDF report generation with reportlab

#### Components Layer
- **ui.py**: Enhanced CSS, stat cards, info boxes, page headers, session state management
- **maps.py**: Folium map creation, layer management, drawing tools
- **charts.py**: Matplotlib-based pie, bar, line, radar, and correlation heatmap charts
- **legends.py**: Interactive legends with opacity sliders for indices and pollutants

## Index Reference

| Index | Range | Description |
|-------|-------|-------------|
| NDVI | -1 to 1 | Vegetation health and density |
| NDWI | -1 to 1 | Water body detection |
| NDBI | -1 to 1 | Built-up area identification |
| EVI | -1 to 1 | Enhanced vegetation index |
| SAVI | 0 to 1 | Soil-adjusted vegetation |

## Pollutant Reference

| Pollutant | Collection | Unit | Description |
|-----------|------------|------|-------------|
| NO₂ | S5P L3 NO2 | µmol/m² | Nitrogen dioxide from vehicles/industry |
| SO₂ | S5P L3 SO2 | µmol/m² | Sulfur dioxide from power plants |
| CO | S5P L3 CO | mmol/m² | Carbon monoxide from combustion |
| O₃ | S5P L3 O3 | mmol/m² | Tropospheric ozone |
| UVAI | S5P L3 AER_AI | index | UV Aerosol Index for smoke/dust |
| CH₄ | S5P L3 CH4 | ppb | Methane concentration |

## User Preferences
- Clean, intuitive interface with responsive cards
- Visual statistics with pie/bar charts and progress bars
- Layer toggle controls with opacity sliders
- Collapsible sections for legends and statistics
- CSV, GeoTIFF, and PDF export options

## Technical Notes
- Requires Google Earth Engine authentication (service account in secrets.toml)
- Uses Dynamic World for LULC classification (available from 2017)
- Uses Sentinel-5P for air quality (available from 2018)
- Cloud filtering applied to satellite imagery (< 20% cloud cover)
- Buffer radius configurable from 5-100 km around city center
- Custom AOI drawing enabled via Folium Draw plugin
- Multi-page Streamlit structure for modular navigation

## Dependencies
- streamlit
- earthengine-api
- geemap
- folium
- streamlit-folium
- pandas
- numpy
- matplotlib
- geopandas
- plotly
- reportlab
