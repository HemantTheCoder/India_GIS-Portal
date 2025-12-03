import ee
from datetime import datetime, timedelta

POLLUTANT_INFO = {
    "NO2": {
        "name": "Nitrogen Dioxide",
        "collection": "COPERNICUS/S5P/NRTI/L3_NO2",
        "band": "NO2_column_number_density",
        "unit": "mol/m²",
        "scale_factor": 1e6,
        "display_unit": "µmol/m²",
        "min": 0,
        "max": 200,
        "palette": ["#00ff00", "#ffff00", "#ff9900", "#ff0000", "#990066", "#660033"],
        "description": "Nitrogen dioxide from vehicles and industry",
    },
    "SO2": {
        "name": "Sulfur Dioxide",
        "collection": "COPERNICUS/S5P/NRTI/L3_SO2",
        "band": "SO2_column_number_density",
        "unit": "mol/m²",
        "scale_factor": 1e6,
        "display_unit": "µmol/m²",
        "min": 0,
        "max": 500,
        "palette": ["#00ff00", "#ffff00", "#ff9900", "#ff0000", "#990066"],
        "description": "Sulfur dioxide from power plants and volcanoes",
    },
    "CO": {
        "name": "Carbon Monoxide",
        "collection": "COPERNICUS/S5P/NRTI/L3_CO",
        "band": "CO_column_number_density",
        "unit": "mol/m²",
        "scale_factor": 1e3,
        "display_unit": "mmol/m²",
        "min": 0,
        "max": 50,
        "palette": ["#00ff00", "#ffff00", "#ff9900", "#ff0000", "#990066"],
        "description": "Carbon monoxide from combustion",
    },
    "O3": {
        "name": "Ozone",
        "collection": "COPERNICUS/S5P/NRTI/L3_O3",
        "band": "O3_column_number_density",
        "unit": "mol/m²",
        "scale_factor": 1e3,
        "display_unit": "mmol/m²",
        "min": 0,
        "max": 200,
        "palette": ["#00ff00", "#ffff00", "#ff9900", "#ff0000", "#990066"],
        "description": "Tropospheric ozone",
    },
    "UVAI": {
        "name": "UV Aerosol Index",
        "collection": "COPERNICUS/S5P/NRTI/L3_AER_AI",
        "band": "absorbing_aerosol_index",
        "unit": "index",
        "scale_factor": 1,
        "display_unit": "index",
        "min": -2,
        "max": 5,
        "palette": ["#0000ff", "#00ffff", "#00ff00", "#ffff00", "#ff9900", "#ff0000"],
        "description": "UV Aerosol Index for smoke and dust detection",
    },
    "CH4": {
        "name": "Methane",
        "collection": "COPERNICUS/S5P/OFFL/L3_CH4",
        "band": "CH4_column_volume_mixing_ratio_dry_air",
        "unit": "ppb",
        "scale_factor": 1,
        "display_unit": "ppb",
        "min": 1750,
        "max": 2000,
        "palette": ["#00ff00", "#ffff00", "#ff9900", "#ff0000", "#990066"],
        "description": "Methane concentration",
    },
}

def get_pollutant_image(geometry, pollutant, start_date, end_date):
    if pollutant not in POLLUTANT_INFO:
        return None
    
    info = POLLUTANT_INFO[pollutant]
    
    try:
        collection = (
            ee.ImageCollection(info["collection"])
            .filterBounds(geometry)
            .filterDate(start_date, end_date)
            .select(info["band"])
        )
        
        if collection.size().getInfo() == 0:
            return None
        
        image = collection.mean().clip(geometry)
        
        if info["scale_factor"] != 1:
            image = image.multiply(info["scale_factor"])
        
        return image
    except Exception as e:
        print(f"Error fetching {pollutant} data: {e}")
        return None

def get_pollutant_vis_params(pollutant):
    if pollutant not in POLLUTANT_INFO:
        return {"min": 0, "max": 100, "palette": ["green", "yellow", "red"]}
    
    info = POLLUTANT_INFO[pollutant]
    return {
        "min": info["min"],
        "max": info["max"],
        "palette": info["palette"],
    }

def calculate_pollutant_statistics(image, geometry, pollutant):
    if pollutant not in POLLUTANT_INFO:
        return None
    
    info = POLLUTANT_INFO[pollutant]
    
    try:
        stats = image.reduceRegion(
            reducer=ee.Reducer.mean()
                .combine(ee.Reducer.median(), '', True)
                .combine(ee.Reducer.stdDev(), '', True)
                .combine(ee.Reducer.min(), '', True)
                .combine(ee.Reducer.max(), '', True)
                .combine(ee.Reducer.percentile([10, 90]), '', True),
            geometry=geometry,
            scale=1000,
            maxPixels=1e9
        ).getInfo()
        
        band_name = image.bandNames().get(0).getInfo()
        
        return {
            "mean": stats.get(f"{band_name}_mean", 0) or 0,
            "median": stats.get(f"{band_name}_median", 0) or 0,
            "std_dev": stats.get(f"{band_name}_stdDev", 0) or 0,
            "min": stats.get(f"{band_name}_min", 0) or 0,
            "max": stats.get(f"{band_name}_max", 0) or 0,
            "p10": stats.get(f"{band_name}_p10", 0) or 0,
            "p90": stats.get(f"{band_name}_p90", 0) or 0,
            "unit": info["display_unit"],
        }
    except Exception as e:
        print(f"Error calculating {pollutant} statistics: {e}")
        return None

def get_baseline_image(geometry, pollutant, baseline_year=2019):
    start_date = f"{baseline_year}-01-01"
    end_date = f"{baseline_year}-12-31"
    return get_pollutant_image(geometry, pollutant, start_date, end_date)

def calculate_anomaly_map(current_image, baseline_image):
    if current_image is None or baseline_image is None:
        return None
    return current_image.subtract(baseline_image)

def get_anomaly_vis_params(pollutant):
    info = POLLUTANT_INFO.get(pollutant, {})
    max_val = info.get("max", 100) / 2
    return {
        "min": -max_val,
        "max": max_val,
        "palette": ["#0000ff", "#00ffff", "#ffffff", "#ffff00", "#ff0000"],
    }

def create_smoothed_map(image, radius_meters=5000):
    if image is None:
        return None
    kernel = ee.Kernel.gaussian(radius=radius_meters, units='meters')
    return image.convolve(kernel)

def create_hotspot_mask(image, geometry, threshold_sigma=1.5):
    if image is None:
        return None
    
    try:
        stats = image.reduceRegion(
            reducer=ee.Reducer.mean().combine(ee.Reducer.stdDev(), '', True),
            geometry=geometry,
            scale=1000,
            maxPixels=1e9
        )
        
        band_name = image.bandNames().get(0).getInfo()
        mean = ee.Number(stats.get(f"{band_name}_mean"))
        std = ee.Number(stats.get(f"{band_name}_stdDev"))
        
        threshold = mean.add(std.multiply(threshold_sigma))
        hotspot_mask = image.gt(threshold)
        
        return hotspot_mask
    except Exception as e:
        print(f"Error creating hotspot mask: {e}")
        return None

def get_hotspot_vis_params():
    return {
        "min": 0,
        "max": 1,
        "palette": ["transparent", "#ff0000"],
    }

def get_pollutant_time_series(geometry, pollutant, start_date, end_date, interval_days=7):
    if pollutant not in POLLUTANT_INFO:
        return None
    
    info = POLLUTANT_INFO[pollutant]
    
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        
        time_series = []
        current = start
        
        while current < end:
            next_date = current + timedelta(days=interval_days)
            if next_date > end:
                next_date = end
            
            image = get_pollutant_image(
                geometry, 
                pollutant, 
                current.strftime("%Y-%m-%d"), 
                next_date.strftime("%Y-%m-%d")
            )
            
            if image is not None:
                band_name = image.bandNames().get(0).getInfo()
                stats = image.reduceRegion(
                    reducer=ee.Reducer.mean(),
                    geometry=geometry,
                    scale=1000,
                    maxPixels=1e9
                ).getInfo()
                
                value = stats.get(band_name, None)
                
                time_series.append({
                    "date": current.strftime("%Y-%m-%d"),
                    "value": value,
                    "pollutant": pollutant,
                })
            
            current = next_date
        
        return time_series
    except Exception as e:
        print(f"Error getting time series for {pollutant}: {e}")
        return None

def calculate_rolling_average(time_series, window=7):
    if not time_series or len(time_series) < window:
        return time_series
    
    result = []
    values = [d["value"] for d in time_series if d["value"] is not None]
    
    for i, data in enumerate(time_series):
        if data["value"] is None:
            result.append({**data, "rolling_avg": None})
            continue
        
        start_idx = max(0, i - window + 1)
        window_values = values[start_idx:i+1]
        
        if window_values:
            avg = sum(window_values) / len(window_values)
            result.append({**data, "rolling_avg": avg})
        else:
            result.append({**data, "rolling_avg": None})
    
    return result

def calculate_pollutant_correlations(geometry, pollutants, start_date, end_date):
    correlations = {}
    
    for p1 in pollutants:
        for p2 in pollutants:
            if p1 == p2:
                correlations[(p1, p2)] = 1.0
            elif (p2, p1) in correlations:
                correlations[(p1, p2)] = correlations[(p2, p1)]
            else:
                img1 = get_pollutant_image(geometry, p1, start_date, end_date)
                img2 = get_pollutant_image(geometry, p2, start_date, end_date)
                
                if img1 is None or img2 is None:
                    correlations[(p1, p2)] = None
                    continue
                
                try:
                    combined = img1.addBands(img2)
                    corr = combined.reduceRegion(
                        reducer=ee.Reducer.pearsonsCorrelation(),
                        geometry=geometry,
                        scale=1000,
                        maxPixels=1e8
                    ).getInfo()
                    
                    correlations[(p1, p2)] = corr.get("correlation", None)
                except:
                    correlations[(p1, p2)] = None
    
    return correlations
