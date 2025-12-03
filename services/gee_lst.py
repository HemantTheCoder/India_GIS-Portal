import ee
from datetime import datetime, timedelta

MODIS_LST_COLLECTION = "MODIS/061/MOD11A2"
MODIS_AQUA_LST_COLLECTION = "MODIS/061/MYD11A2"

LST_VIS_PARAMS = {
    'min': 20,
    'max': 45,
    'palette': ['blue', 'cyan', 'green', 'yellow', 'orange', 'red', 'darkred']
}

UHI_VIS_PARAMS = {
    'min': -5,
    'max': 10,
    'palette': ['#313695', '#4575b4', '#74add1', '#abd9e9', '#e0f3f8', '#ffffbf', '#fee090', '#fdae61', '#f46d43', '#d73027', '#a50026']
}

ANOMALY_VIS_PARAMS = {
    'min': -5,
    'max': 5,
    'palette': ['#2166ac', '#4393c3', '#92c5de', '#d1e5f0', '#f7f7f7', '#fddbc7', '#f4a582', '#d6604d', '#b2182b']
}

HOTSPOT_VIS_PARAMS = {
    'min': 0,
    'max': 1,
    'palette': ['yellow', 'orange', 'red', 'darkred']
}

COOLING_VIS_PARAMS = {
    'min': 0,
    'max': 1,
    'palette': ['#f7fcf5', '#c7e9c0', '#74c476', '#31a354', '#006d2c']
}

def get_modis_lst(geometry, start_date, end_date, satellite='Terra'):
    collection_id = MODIS_LST_COLLECTION if satellite == 'Terra' else MODIS_AQUA_LST_COLLECTION
    
    collection = ee.ImageCollection(collection_id) \
        .filterBounds(geometry) \
        .filterDate(start_date, end_date) \
        .select(['LST_Day_1km', 'LST_Night_1km', 'QC_Day', 'QC_Night'])
    
    count = collection.size().getInfo()
    if count == 0:
        return None, 0
    
    def kelvin_to_celsius(image):
        lst_day = image.select('LST_Day_1km').multiply(0.02).subtract(273.15).rename('LST_Day')
        lst_night = image.select('LST_Night_1km').multiply(0.02).subtract(273.15).rename('LST_Night')
        return image.addBands([lst_day, lst_night])
    
    collection = collection.map(kelvin_to_celsius)
    
    return collection, count

def get_mean_lst(geometry, start_date, end_date, time_of_day='Day', satellite='Terra'):
    collection, count = get_modis_lst(geometry, start_date, end_date, satellite)
    
    if collection is None:
        return None
    
    band_name = f'LST_{time_of_day}'
    mean_lst = collection.select(band_name).mean().clip(geometry)
    
    return mean_lst

def get_lst_statistics(lst_image, geometry):
    if lst_image is None:
        return None
    
    stats = lst_image.reduceRegion(
        reducer=ee.Reducer.mean()
            .combine(ee.Reducer.min(), sharedInputs=True)
            .combine(ee.Reducer.max(), sharedInputs=True)
            .combine(ee.Reducer.stdDev(), sharedInputs=True)
            .combine(ee.Reducer.percentile([10, 25, 50, 75, 90]), sharedInputs=True),
        geometry=geometry,
        scale=1000,
        maxPixels=1e9
    ).getInfo()
    
    return stats

def get_seasonal_lst(geometry, year, time_of_day='Day', satellite='Terra'):
    seasons = {
        'Winter': (f'{year}-01-01', f'{year}-02-28'),
        'Pre-Monsoon': (f'{year}-03-01', f'{year}-05-31'),
        'Monsoon': (f'{year}-06-01', f'{year}-09-30'),
        'Post-Monsoon': (f'{year}-10-01', f'{year}-12-31')
    }
    
    seasonal_data = {}
    for season, (start, end) in seasons.items():
        lst = get_mean_lst(geometry, start, end, time_of_day, satellite)
        if lst is not None:
            stats = get_lst_statistics(lst, geometry)
            seasonal_data[season] = {
                'image': lst,
                'stats': stats
            }
    
    return seasonal_data

def get_monthly_lst(geometry, year, time_of_day='Day', satellite='Terra'):
    monthly_data = {}
    
    for month in range(1, 13):
        start_date = f'{year}-{month:02d}-01'
        if month == 12:
            end_date = f'{year}-12-31'
        else:
            end_date = f'{year}-{month+1:02d}-01'
        
        lst = get_mean_lst(geometry, start_date, end_date, time_of_day, satellite)
        if lst is not None:
            stats = get_lst_statistics(lst, geometry)
            month_name = datetime(year, month, 1).strftime('%B')
            monthly_data[month_name] = {
                'image': lst,
                'stats': stats,
                'month_num': month
            }
    
    return monthly_data

def calculate_lst_anomaly(geometry, target_start, target_end, baseline_start, baseline_end, time_of_day='Day', satellite='Terra'):
    target_lst = get_mean_lst(geometry, target_start, target_end, time_of_day, satellite)
    baseline_lst = get_mean_lst(geometry, baseline_start, baseline_end, time_of_day, satellite)
    
    if target_lst is None or baseline_lst is None:
        return None, None, None
    
    anomaly = target_lst.subtract(baseline_lst).rename('LST_Anomaly')
    
    target_stats = get_lst_statistics(target_lst, geometry)
    baseline_stats = get_lst_statistics(baseline_lst, geometry)
    anomaly_stats = get_lst_statistics(anomaly, geometry)
    
    return anomaly, {
        'target': target_stats,
        'baseline': baseline_stats,
        'anomaly': anomaly_stats
    }, target_lst

def calculate_uhi_intensity(geometry, start_date, end_date, buffer_km=20, time_of_day='Day', satellite='Terra'):
    urban_lst = get_mean_lst(geometry, start_date, end_date, time_of_day, satellite)
    
    if urban_lst is None:
        return None, None
    
    buffer_meters = buffer_km * 1000
    outer_buffer = geometry.buffer(buffer_meters, maxError=100)
    rural_zone = outer_buffer.difference(geometry, maxError=100)
    
    rural_lst = get_mean_lst(rural_zone, start_date, end_date, time_of_day, satellite)
    
    if rural_lst is None:
        return None, None
    
    urban_stats = get_lst_statistics(urban_lst, geometry)
    rural_stats = get_lst_statistics(rural_lst, rural_zone)
    
    uhi_intensity = None
    if urban_stats and rural_stats:
        band_key = 'LST_Day_mean' if time_of_day == 'Day' else 'LST_Night_mean'
        if band_key in urban_stats and band_key in rural_stats:
            urban_mean = urban_stats[band_key]
            rural_mean = rural_stats[band_key]
            if urban_mean is not None and rural_mean is not None:
                uhi_intensity = urban_mean - rural_mean
    
    rural_mean_value = rural_lst.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=rural_zone,
        scale=1000,
        maxPixels=1e9
    ).values().get(0)
    
    uhi_image = urban_lst.subtract(ee.Number(rural_mean_value)).rename('UHI_Intensity')
    
    return uhi_image, {
        'urban_stats': urban_stats,
        'rural_stats': rural_stats,
        'uhi_intensity': uhi_intensity
    }

def detect_heat_hotspots(lst_image, geometry, threshold_percentile=90):
    if lst_image is None:
        return None, None
    
    percentile = lst_image.reduceRegion(
        reducer=ee.Reducer.percentile([threshold_percentile]),
        geometry=geometry,
        scale=1000,
        maxPixels=1e9
    ).values().get(0)
    
    hotspots = lst_image.gt(ee.Number(percentile)).selfMask().rename('Heat_Hotspots')
    
    hotspot_area = hotspots.multiply(ee.Image.pixelArea()).reduceRegion(
        reducer=ee.Reducer.sum(),
        geometry=geometry,
        scale=1000,
        maxPixels=1e9
    ).getInfo()
    
    total_area = geometry.area(maxError=100).getInfo()
    
    return hotspots, {
        'threshold_temp': percentile.getInfo(),
        'hotspot_area_km2': hotspot_area.get('Heat_Hotspots', 0) / 1e6 if hotspot_area else 0,
        'total_area_km2': total_area / 1e6,
        'hotspot_percentage': (hotspot_area.get('Heat_Hotspots', 0) / total_area * 100) if hotspot_area and total_area else 0
    }

def identify_cooling_zones(geometry, start_date, end_date, lst_image=None, time_of_day='Day', satellite='Terra'):
    if lst_image is None:
        lst_image = get_mean_lst(geometry, start_date, end_date, time_of_day, satellite)
    
    if lst_image is None:
        return None, None
    
    percentile_25 = lst_image.reduceRegion(
        reducer=ee.Reducer.percentile([25]),
        geometry=geometry,
        scale=1000,
        maxPixels=1e9
    ).values().get(0)
    
    cooling_zones = lst_image.lt(ee.Number(percentile_25)).selfMask().rename('Cooling_Zones')
    
    cooling_area = cooling_zones.multiply(ee.Image.pixelArea()).reduceRegion(
        reducer=ee.Reducer.sum(),
        geometry=geometry,
        scale=1000,
        maxPixels=1e9
    ).getInfo()
    
    total_area = geometry.area(maxError=100).getInfo()
    
    return cooling_zones, {
        'threshold_temp': percentile_25.getInfo(),
        'cooling_area_km2': cooling_area.get('Cooling_Zones', 0) / 1e6 if cooling_area else 0,
        'total_area_km2': total_area / 1e6,
        'cooling_percentage': (cooling_area.get('Cooling_Zones', 0) / total_area * 100) if cooling_area and total_area else 0
    }

def analyze_lst_ndvi_relationship(geometry, start_date, end_date, time_of_day='Day'):
    from services.gee_indices import calculate_vegetation_indices
    from services.gee_lulc import get_sentinel2_image
    
    lst_image = get_mean_lst(geometry, start_date, end_date, time_of_day)
    
    s2_image = get_sentinel2_image(geometry, start_date, end_date)
    if s2_image is None or lst_image is None:
        return None
    
    indices = calculate_vegetation_indices(s2_image)
    ndvi = indices['NDVI']
    ndbi = indices['NDBI']
    
    sample_points = ee.FeatureCollection.randomPoints(geometry, 500, 42)
    
    combined = lst_image.addBands(ndvi).addBands(ndbi)
    
    samples = combined.sampleRegions(
        collection=sample_points,
        scale=1000,
        geometries=False
    ).getInfo()
    
    return samples

def get_lst_time_series(geometry, start_year, end_year, time_of_day='Day', satellite='Terra', aggregation='monthly'):
    time_series = []
    
    for year in range(start_year, end_year + 1):
        if aggregation == 'monthly':
            for month in range(1, 13):
                start_date = f'{year}-{month:02d}-01'
                if month == 12:
                    end_date = f'{year}-12-31'
                else:
                    end_date = f'{year}-{month+1:02d}-01'
                
                lst = get_mean_lst(geometry, start_date, end_date, time_of_day, satellite)
                if lst is not None:
                    stats = get_lst_statistics(lst, geometry)
                    band_key = f'LST_{time_of_day}_mean'
                    if stats and band_key in stats and stats[band_key] is not None:
                        time_series.append({
                            'date': f'{year}-{month:02d}',
                            'year': year,
                            'month': month,
                            'mean_lst': stats[band_key],
                            'min_lst': stats.get(f'LST_{time_of_day}_min'),
                            'max_lst': stats.get(f'LST_{time_of_day}_max'),
                            'std_lst': stats.get(f'LST_{time_of_day}_stdDev')
                        })
        
        elif aggregation == 'seasonal':
            seasons = {
                'Winter': (f'{year}-01-01', f'{year}-02-28'),
                'Pre-Monsoon': (f'{year}-03-01', f'{year}-05-31'),
                'Monsoon': (f'{year}-06-01', f'{year}-09-30'),
                'Post-Monsoon': (f'{year}-10-01', f'{year}-12-31')
            }
            
            for season, (start, end) in seasons.items():
                lst = get_mean_lst(geometry, start, end, time_of_day, satellite)
                if lst is not None:
                    stats = get_lst_statistics(lst, geometry)
                    band_key = f'LST_{time_of_day}_mean'
                    if stats and band_key in stats and stats[band_key] is not None:
                        time_series.append({
                            'date': f'{year} {season}',
                            'year': year,
                            'season': season,
                            'mean_lst': stats[band_key],
                            'min_lst': stats.get(f'LST_{time_of_day}_min'),
                            'max_lst': stats.get(f'LST_{time_of_day}_max'),
                            'std_lst': stats.get(f'LST_{time_of_day}_stdDev')
                        })
        
        elif aggregation == 'yearly':
            start_date = f'{year}-01-01'
            end_date = f'{year}-12-31'
            
            lst = get_mean_lst(geometry, start_date, end_date, time_of_day, satellite)
            if lst is not None:
                stats = get_lst_statistics(lst, geometry)
                band_key = f'LST_{time_of_day}_mean'
                if stats and band_key in stats and stats[band_key] is not None:
                    time_series.append({
                        'date': str(year),
                        'year': year,
                        'mean_lst': stats[band_key],
                        'min_lst': stats.get(f'LST_{time_of_day}_min'),
                        'max_lst': stats.get(f'LST_{time_of_day}_max'),
                        'std_lst': stats.get(f'LST_{time_of_day}_stdDev')
                    })
    
    return time_series

def detect_heatwaves(geometry, year, threshold_percentile=95, min_duration_days=3, time_of_day='Day', satellite='Terra'):
    collection_id = MODIS_LST_COLLECTION if satellite == 'Terra' else MODIS_AQUA_LST_COLLECTION
    
    collection = ee.ImageCollection(collection_id) \
        .filterBounds(geometry) \
        .filterDate(f'{year}-01-01', f'{year}-12-31') \
        .select(['LST_Day_1km'] if time_of_day == 'Day' else ['LST_Night_1km'])
    
    count = collection.size().getInfo()
    if count == 0:
        return None
    
    def kelvin_to_celsius(image):
        band = 'LST_Day_1km' if time_of_day == 'Day' else 'LST_Night_1km'
        return image.select(band).multiply(0.02).subtract(273.15).rename('LST') \
            .copyProperties(image, ['system:time_start'])
    
    collection = collection.map(kelvin_to_celsius)
    
    threshold = collection.reduce(ee.Reducer.percentile([threshold_percentile]))
    
    heatwave_events = []
    image_list = collection.toList(collection.size())
    
    for i in range(count):
        img = ee.Image(image_list.get(i))
        date = ee.Date(img.get('system:time_start')).format('YYYY-MM-dd').getInfo()
        
        mean_temp = img.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=geometry,
            scale=1000,
            maxPixels=1e9
        ).get('LST').getInfo()
        
        threshold_val = threshold.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=geometry,
            scale=1000,
            maxPixels=1e9
        ).values().get(0).getInfo()
        
        if mean_temp and threshold_val and mean_temp > threshold_val:
            heatwave_events.append({
                'date': date,
                'temperature': mean_temp,
                'threshold': threshold_val,
                'excess': mean_temp - threshold_val
            })
    
    return heatwave_events

def calculate_warming_trend(time_series_data):
    if not time_series_data or len(time_series_data) < 2:
        return None
    
    years = [d['year'] for d in time_series_data if 'year' in d]
    temps = [d['mean_lst'] for d in time_series_data if d.get('mean_lst') is not None]
    
    if len(years) < 2 or len(temps) < 2:
        return None
    
    n = len(years)
    sum_x = sum(years)
    sum_y = sum(temps)
    sum_xy = sum(x * y for x, y in zip(years, temps))
    sum_x2 = sum(x ** 2 for x in years)
    
    slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2)
    intercept = (sum_y - slope * sum_x) / n
    
    mean_y = sum_y / n
    ss_tot = sum((y - mean_y) ** 2 for y in temps)
    ss_res = sum((y - (slope * x + intercept)) ** 2 for x, y in zip(years, temps))
    r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
    
    return {
        'slope': slope,
        'intercept': intercept,
        'r_squared': r_squared,
        'warming_rate_per_decade': slope * 10,
        'start_year': min(years),
        'end_year': max(years),
        'total_warming': slope * (max(years) - min(years))
    }

def get_lst_tile_url(lst_image, vis_params=None):
    if lst_image is None:
        return None
    
    if vis_params is None:
        vis_params = LST_VIS_PARAMS
    
    map_id = lst_image.getMapId(vis_params)
    return map_id['tile_fetcher'].url_format
