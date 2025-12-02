# India GIS & Remote Sensing Portal

## Overview
A web-based GIS and Remote Sensing application for analyzing Land Use/Land Cover (LULC) and vegetation indices for Indian cities using Google Earth Engine.

## Current State
- **Status**: Complete MVP
- **Last Updated**: December 2, 2025

## Features
1. **Location Selection**: Dropdown menus for selecting any state and city in India (200+ cities covered)
2. **Date Range Selection**: Full year or custom date range from 2017 onwards
3. **Satellite Data Sources**:
   - Sentinel-2 (10m resolution)
   - Landsat 8/9 (30m resolution)
4. **LULC Analysis**: Using Google's Dynamic World dataset with 9 land cover classes
5. **Vegetation Indices**: NDVI, NDWI, NDBI, EVI calculations
6. **Interactive Map**: Folium-based map with layer controls
7. **Statistics**: Land cover percentage breakdown for analyzed areas

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
  - Vegetation index calculations (NDVI, NDWI, NDBI, EVI)
  - Tile URL generation for map display
- **app.py**: Streamlit UI with sidebar controls and interactive map display

## User Preferences
- Clean, intuitive interface with clear legends
- Visual statistics with progress bars
- Layer toggle controls on map

## Technical Notes
- Requires Google Earth Engine authentication (service account JSON key or default credentials)
- Uses Dynamic World for LULC classification (available from 2017)
- Cloud filtering applied to satellite imagery (< 20% cloud cover)
- Buffer radius configurable from 5-50 km around city center

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
