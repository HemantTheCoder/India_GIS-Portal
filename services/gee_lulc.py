import ee

LULC_CLASSES = {
    0: {"name": "Water", "color": "#419BDF"},
    1: {"name": "Trees", "color": "#397D49"},
    2: {"name": "Grass", "color": "#88B053"},
    3: {"name": "Flooded Vegetation", "color": "#7A87C6"},
    4: {"name": "Crops", "color": "#E49635"},
    5: {"name": "Shrub & Scrub", "color": "#DFC35A"},
    6: {"name": "Built Area", "color": "#C4281B"},
    7: {"name": "Bare Ground", "color": "#A59B8F"},
    8: {"name": "Snow & Ice", "color": "#B39FE1"},
}

VEGETATION_CLASSES = [1, 2, 3, 4, 5]  # Trees, Grass, Flooded Veg, Crops, Shrub
BUILT_CLASSES = [6]  # Built Area

def get_sentinel2_image(geometry, start_date, end_date):
    collection = (
        ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
        .filterBounds(geometry)
        .filterDate(start_date, end_date)
        .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 20))
        .sort("CLOUDY_PIXEL_PERCENTAGE")
    )
    
    if collection.size().getInfo() == 0:
        return None
    
    image = collection.median().clip(geometry)
    return image

def get_landsat_image(geometry, start_date, end_date):
    collection = (
        ee.ImageCollection("LANDSAT/LC09/C02/T1_L2")
        .filterBounds(geometry)
        .filterDate(start_date, end_date)
        .filter(ee.Filter.lt("CLOUD_COVER", 20))
        .sort("CLOUD_COVER")
    )
    
    if collection.size().getInfo() == 0:
        collection = (
            ee.ImageCollection("LANDSAT/LC08/C02/T1_L2")
            .filterBounds(geometry)
            .filterDate(start_date, end_date)
            .filter(ee.Filter.lt("CLOUD_COVER", 20))
            .sort("CLOUD_COVER")
        )
    
    if collection.size().getInfo() == 0:
        return None
    
    image = collection.median().clip(geometry)
    return image

def get_dynamic_world_lulc(geometry, start_date, end_date):
    collection = (
        ee.ImageCollection("GOOGLE/DYNAMICWORLD/V1")
        .filterBounds(geometry)
        .filterDate(start_date, end_date)
    )
    
    if collection.size().getInfo() == 0:
        return None
    
    classification = collection.select("label")
    mode_lulc = classification.mode().clip(geometry)
    
    return mode_lulc

def get_sentinel_rgb_params(image):
    return {
        "bands": ["B4", "B3", "B2"],
        "min": 0,
        "max": 3000,
    }

def get_landsat_rgb_params(image):
    return {
        "bands": ["SR_B4", "SR_B3", "SR_B2"],
        "min": 5000,
        "max": 15000,
    }

def get_lulc_vis_params():
    return {
        "min": 0,
        "max": 8,
        "palette": [LULC_CLASSES[i]["color"] for i in range(9)],
    }

def calculate_area_from_pixels(pixel_count, resolution=10):
    pixel_area_sqm = resolution * resolution
    area_sqm = pixel_count * pixel_area_sqm
    area_sqkm = area_sqm / 1_000_000
    return round(area_sqkm, 2)

def calculate_lulc_statistics_with_area(lulc_image, geometry, resolution=10):
    try:
        stats = lulc_image.reduceRegion(
            reducer=ee.Reducer.frequencyHistogram(),
            geometry=geometry,
            scale=resolution,
            maxPixels=1e9
        )
        
        histogram = stats.get("label").getInfo()
        if histogram is None:
            return None
        
        total_pixels = sum(histogram.values())
        total_area_sqkm = calculate_area_from_pixels(total_pixels, resolution)
        result = {}
        
        for class_id, count in histogram.items():
            class_id = int(float(class_id))
            if class_id in LULC_CLASSES:
                percentage = (count / total_pixels) * 100
                area_sqkm = calculate_area_from_pixels(count, resolution)
                result[LULC_CLASSES[class_id]["name"]] = {
                    "pixels": count,
                    "percentage": round(percentage, 2),
                    "area_sqkm": area_sqkm,
                    "color": LULC_CLASSES[class_id]["color"],
                    "class_id": class_id,
                }
        
        return {"classes": result, "total_area_sqkm": total_area_sqkm}
    except Exception as e:
        print(f"Error calculating statistics: {e}")
        return None

def get_lulc_change_analysis(geometry, year1, year2):
    start1 = f"{year1}-01-01"
    end1 = f"{year1}-12-31"
    start2 = f"{year2}-01-01"
    end2 = f"{year2}-12-31"
    
    lulc1 = get_dynamic_world_lulc(geometry, start1, end1)
    lulc2 = get_dynamic_world_lulc(geometry, start2, end2)
    
    if lulc1 is None or lulc2 is None:
        return None, None, None
    
    stats1 = calculate_lulc_statistics_with_area(lulc1, geometry)
    stats2 = calculate_lulc_statistics_with_area(lulc2, geometry)
    
    change_image = lulc2.subtract(lulc1)
    
    return stats1, stats2, change_image

def calculate_change_summary(stats1, stats2):
    if not stats1 or not stats2:
        return None
    
    classes1 = stats1.get("classes", {})
    classes2 = stats2.get("classes", {})
    
    changes = []
    for class_name in set(classes1.keys()) | set(classes2.keys()):
        data1 = classes1.get(class_name, {"percentage": 0, "area_sqkm": 0, "class_id": -1})
        data2 = classes2.get(class_name, {"percentage": 0, "area_sqkm": 0, "class_id": -1})
        
        pct_change = data2.get("percentage", 0) - data1.get("percentage", 0)
        area_change = data2.get("area_sqkm", 0) - data1.get("area_sqkm", 0)
        
        class_id = data1.get("class_id", data2.get("class_id", -1))
        
        changes.append({
            "class": class_name,
            "class_id": class_id,
            "year1_pct": data1.get("percentage", 0),
            "year2_pct": data2.get("percentage", 0),
            "pct_change": pct_change,
            "year1_area": data1.get("area_sqkm", 0),
            "year2_area": data2.get("area_sqkm", 0),
            "area_change": area_change,
        })
    
    changes_sorted = sorted(changes, key=lambda x: abs(x["pct_change"]), reverse=True)
    
    biggest_increase = max(changes, key=lambda x: x["pct_change"])
    biggest_decrease = min(changes, key=lambda x: x["pct_change"])
    
    vegetation_change = sum(
        c["area_change"] for c in changes 
        if c["class_id"] in VEGETATION_CLASSES
    )
    
    built_change = sum(
        c["area_change"] for c in changes 
        if c["class_id"] in BUILT_CLASSES
    )
    
    return {
        "all_changes": changes_sorted,
        "biggest_increase": biggest_increase,
        "biggest_decrease": biggest_decrease,
        "net_vegetation_change": vegetation_change,
        "net_built_change": built_change,
    }
