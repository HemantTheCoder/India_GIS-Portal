# India GIS & Remote Sensing Portal

## Overview
A comprehensive web-based GIS and Remote Sensing application for analyzing Land Use/Land Cover (LULC), vegetation indices, air quality, and urban heat for Indian cities using Google Earth Engine and satellite data from Sentinel, Landsat, and MODIS.

## Current State
- **Status**: Complete with Multi-Module Architecture + PDF Reports
- **Last Updated**: December 4, 2025

## Features

### LULC & Vegetation Analysis Module
1. **Location Selection**: Dropdown menus for selecting any state and city in India (200+ cities covered)
2. **Shapefile/GeoJSON Upload**: Custom AOI support for .shp, .zip, .geojson files
3. **Date Range Selection**: Full year or custom date range from 2017 onwards
4. **Satellite Data Sources**:
   - Sentinel-2 (10m resolution)
   - Landsat 8/9 (30m resolution)
5. **LULC Analysis**: Using Google's Dynamic World dataset with 9 land cover classes
6. **Vegetation Indices**: NDVI, NDWI, NDBI, EVI, SAVI calculations with standardized ranges
7. **Interactive Map**: Folium-based map with layer controls and opacity sliders
8. **Pixel Inspector**: Click on map to view index values at any location
9. **Statistics**: Land cover percentage and area (km²) breakdown with pie/bar charts
10. **Time Series Analysis**: Compare LULC changes between years with change summaries
11. **Export/Download**: CSV statistics, GeoTIFF exports, PDF reports

### Air Quality (AQI) Analysis Module
1. **Pollutant Monitoring**: NO₂, SO₂, CO, O₃, UVAI, CH₄ from Sentinel-5P
2. **Shapefile/GeoJSON Upload**: Custom AOI support
3. **AOI Statistics**: Mean, median, std dev, percentiles, min/max
4. **Anomaly Maps**: Compare current levels to 2019 baseline
5. **Smoothed/Plume Maps**: Gaussian smoothed visualization
6. **Hotspot Detection**: Areas exceeding mean + 1.5σ threshold
7. **Time Series Analysis**: Track pollutant trends with rolling averages
8. **Multi-Pollutant Dashboard**: Correlation heatmaps, radar charts, comparison charts
9. **Export**: CSV statistics, GeoTIFF downloads, PDF reports with Compliance Score

### Urban Heat & Climate Module
1. **Land Surface Temperature**: MODIS Terra/Aqua LST data (1km resolution)
2. **Location Selection**: City selection or shapefile/GeoJSON upload
3. **Time Selection**: Full year, seasonal, monthly, or custom date range
4. **Day/Night Analysis**: Separate daytime and nighttime LST analysis
5. **LST Mapping**: Mean temperature maps with statistics
6. **Urban Heat Island (UHI)**: Calculate UHI intensity (urban vs rural comparison)
7. **Heat Hotspots**: Identify areas exceeding 90th percentile temperature
8. **Cooling Zones**: Map parks and water bodies that reduce temperatures
9. **LST Anomaly**: Compare current period to baseline year
10. **Time Series**: Track temperature trends over multiple years
11. **Warming Trends**: Long-term warming analysis with regression
12. **Export**: CSV statistics, time series data, PDF reports with Vulnerability Score

## PDF Report Features

### Land Sustainability Score (LULC Module)
A comprehensive score (0-100) evaluating environmental sustainability based on:
- **Green Cover (35%)**: Percentage of vegetation (trees, grass, crops)
- **Impervious Surface (25%)**: Built-up and bare ground areas
- **Water Bodies (15%)**: Presence of water features
- **Land Diversity (15%)**: Number of distinct land cover classes
- **Vegetation Trend (10%)**: Change in tree cover over time

### Air Quality Compliance Score (AQI Module)
Compares measured pollutant concentrations against WHO Air Quality Guidelines:
- **Excellent**: ≤50% of WHO limit (Score: 100)
- **Good**: ≤100% of limit (Score: 80)
- **Moderate**: ≤150% of limit (Score: 60)
- **Poor**: ≤200% of limit (Score: 40)
- **Very Poor**: ≤300% of limit (Score: 20)
- **Severe**: >300% of limit (Score: 0)

### Heat Vulnerability Score (Urban Heat Module)
Assesses heat risk based on multiple factors:
- **Temperature (30%)**: Mean Land Surface Temperature severity
- **UHI Intensity (25%)**: Urban Heat Island effect magnitude
- **Variability (15%)**: Temperature range and extremes
- **Warming Trend (20%)**: Rate of temperature increase per year
- **Extreme Heat Days (10%)**: Percentage of days exceeding 40°C

## Project Architecture

### File Structure
```
├── app.py                      # Main homepage/landing page
├── pages/
│   ├── 1_LULC_Vegetation.py   # LULC & vegetation analysis page
│   ├── 2_AQI_Analysis.py      # Air quality analysis page
│   └── 3_Urban_Heat_Climate.py # Urban heat & climate analysis page
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
│   ├── gee_lst.py             # Land Surface Temperature/MODIS functions
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
- **gee_lst.py**: MODIS LST fetching, UHI calculation, hotspot/cooling detection, warming trends
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

### Ground-Level Pollutants (WHO Comparable)
| Pollutant | Collection | Unit | WHO Daily Limit | Description |
|-----------|------------|------|-----------------|-------------|
| PM2.5 | ECMWF CAMS NRT | µg/m³ | 15 µg/m³ | Fine particulate matter (<2.5µm) |
| PM10 | ECMWF CAMS NRT | µg/m³ | 45 µg/m³ | Coarse particulate matter (<10µm) |
| NO₂ | ECMWF CAMS NRT | µg/m³ | 25 µg/m³ | Nitrogen dioxide at surface level |
| SO₂ | ECMWF CAMS NRT | µg/m³ | 40 µg/m³ | Sulfur dioxide at surface level |
| CO | ECMWF CAMS NRT | mg/m³ | 4 mg/m³ | Carbon monoxide at surface level |
| O₃ | ECMWF CAMS NRT | µg/m³ | 100 µg/m³ | Ozone at surface level |

### Satellite Column Density (Not directly comparable to WHO limits)
| Pollutant | Collection | Unit | Description |
|-----------|------------|------|-------------|
| NO₂_Column | S5P L3 NO2 | µmol/m² | Nitrogen dioxide column density from vehicles/industry |
| SO₂_Column | S5P L3 SO2 | µmol/m² | Sulfur dioxide column density from power plants |
| CO_Column | S5P L3 CO | mmol/m² | Carbon monoxide column density from combustion |
| O₃_Column | S5P L3 O3 | mmol/m² | Tropospheric ozone column density |
| UVAI | S5P L3 AER_AI | index | UV Aerosol Index for smoke/dust detection |
| CH₄ | S5P L3 CH4 | ppb | Methane concentration |

**Note:** CAMS reanalysis data provides validated surface-level concentrations (µg/m³ or mg/m³) which ARE directly comparable to WHO air quality guidelines. Sentinel-5P satellite provides atmospheric column density measurements (total gas in a vertical column), which are useful for spatial patterns but cannot be directly compared to WHO ground-level limits. AQI and WHO compliance scores are calculated for all CAMS surface pollutants (PM2.5, PM10, NO₂, SO₂, CO, O₃).

## WHO 2021 Air Quality Guidelines (Ground-Level)

| Pollutant | Annual Average | 24-hour Average | Notes |
|-----------|---------------|-----------------|-------|
| PM2.5 | 5 µg/m³ | 15 µg/m³ | Most health-relevant pollutant |
| PM10 | 15 µg/m³ | 45 µg/m³ | Coarse particles |
| NO₂ | 10 µg/m³ | 25 µg/m³ | Traffic-related pollutant |
| SO₂ | N/A | 40 µg/m³ | Industrial emissions |
| CO | N/A | 4 mg/m³ | Combustion byproduct |
| O₃ | N/A | 100 µg/m³ | 8-hour peak season mean |

## LST Reference

| Dataset | Resolution | Coverage | Description |
|---------|------------|----------|-------------|
| MODIS Terra | 1 km | 2000-present | MOD11A2 8-day composite LST |
| MODIS Aqua | 1 km | 2002-present | MYD11A2 8-day composite LST |

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
- Uses MODIS for Land Surface Temperature (available from 2000)
- Cloud filtering applied to satellite imagery (< 20% cloud cover)
- Buffer radius configurable from 5-100 km around city center
- Custom AOI via shapefile/GeoJSON upload
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
