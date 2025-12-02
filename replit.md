# India GIS & Remote Sensing Portal

## Overview
A web-based GIS and Remote Sensing application for analyzing Land Use/Land Cover (LULC) and vegetation indices for Indian cities using Google Earth Engine.

## Current State
- **Status**: Complete with Enhanced Features
- **Last Updated**: December 2, 2025

## Features
1. **Location Selection**: Dropdown menus for selecting any state and city in India (200+ cities covered)
2. **Date Range Selection**: Full year or custom date range from 2017 onwards
3. **Satellite Data Sources**:
   - Sentinel-2 (10m resolution)
   - Landsat 8/9 (30m resolution)
4. **LULC Analysis**: Using Google's Dynamic World dataset with 9 land cover classes
5. **Vegetation Indices**: NDVI, NDWI, NDBI, EVI, SAVI calculations
6. **Interactive Map**: Folium-based map with layer controls
7. **Statistics**: Land cover percentage and area (km²) breakdown
8. **Time Series Analysis**: Compare LULC changes between two different years
9. **Custom AOI Drawing**: Draw custom areas on map for specific region analysis
10. **Export/Download**: CSV statistics and GeoTIFF exports

## Project Architecture

### File Structure
```
├── app.py              # Main Streamlit application
├── india_cities.py     # Indian cities database with coordinates
├── gee_utils.py        # Google Earth Engine utility functions
├── pyproject.toml      # Python dependencies
└── .streamlit/
    └── config.toml     # Streamlit configuration
```

### Key Components
- **india_cities.py**: Contains INDIA_DATA dictionary with state-city-coordinates mapping for 36 states/UTs and 200+ cities
- **gee_utils.py**: GEE functions for:
  - Authentication (service account or default)
  - Satellite image fetching (Sentinel-2, Landsat)
  - Dynamic World LULC retrieval
  - Vegetation index calculations (NDVI, NDWI, NDBI, EVI, SAVI)
  - LULC statistics with area calculations
  - Time series change analysis
  - GeoTIFF export/download URL generation
  - Tile URL generation for map display
- **app.py**: Streamlit UI with sidebar controls, interactive map, time series comparison, statistics with downloads

## User Preferences
- Clean, intuitive interface with clear legends
- Visual statistics with progress bars and area calculations
- Layer toggle controls on map
- CSV and GeoTIFF export options

## Technical Notes
- Requires Google Earth Engine authentication (service account JSON key or default credentials)
- Uses Dynamic World for LULC classification (available from 2017)
- Cloud filtering applied to satellite imagery (< 20% cloud cover)
- Buffer radius configurable from 5-50 km around city center
- Custom AOI drawing enabled via Folium Draw plugin

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
