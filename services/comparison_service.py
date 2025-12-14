
import ee
import traceback
import concurrent.futures
from services.sustainability_report import (
    calculate_vegetation_score,
    calculate_aqi_score,
    calculate_heat_score,
    calculate_prediction_score,
    calculate_earthquake_score,
    get_uss_classification,
    get_score_grade,
    get_tile_url,
    NDVI_VIS_PARAMS,
    LULC_VIS_PARAMS,
    PM25_VIS_PARAMS,
    LST_VIS_PARAMS
)

def fetch_region_data(geometry, region_name, year, selected_modules, status_callback=None, prefix=""):
    """
    Fetches data for a single region for selected modules.
    Reuses logic from sustainability_report but filters by selected modules.
    """
    results = {}
    tile_urls = {}
    metrics = {}
    
    # Defaults
    score_sum = 0
    max_score_sum = 0
    
    # 1. Vegetation
    if "Vegetation" in selected_modules:
        if status_callback: status_callback(f"{prefix}Analyzing Vegetation...")
        try:
            score, ndvi_val, imp_ratio, ndvi_img, lulc_img, lulc_stats = calculate_vegetation_score(geometry, year)
            results["Vegetation"] = {
                "score": score,
                "value": ndvi_val,
                "metric": "NDVI",
                "impervious": imp_ratio,
                "stats": lulc_stats
            }
            if ndvi_img:
                try: tile_urls['ndvi'] = get_tile_url(ndvi_img.clip(geometry), NDVI_VIS_PARAMS)
                except: pass
            score_sum += score
            max_score_sum += 25
        except Exception as e:
            print(f"Error in Vegetation for {region_name}: {e}")
            results["Vegetation"] = {"score": 0, "value": 0, "metric": "NDVI", "error": str(e)}

    # 2. Air Quality
    if "Air Quality" in selected_modules:
        if status_callback: status_callback(f"{prefix}Analyzing Air Quality...")
        try:
            score, aqi_val, pm25_val, pm25_img, stats = calculate_aqi_score(geometry, year)
            results["Air Quality"] = {
                "score": score,
                "value": aqi_val,
                "metric": "AQI",
                "pm25": pm25_val,
                "stats": stats
            }
            if pm25_img:
                try: tile_urls['pm25'] = get_tile_url(pm25_img.clip(geometry), PM25_VIS_PARAMS)
                except: pass
            score_sum += score
            max_score_sum += 25
        except Exception as e:
            print(f"Error in AQI for {region_name}: {e}")
            results["Air Quality"] = {"score": 0, "value": 0, "metric": "AQI", "error": str(e)}

    # 3. Urban Heat
    if "Urban Heat" in selected_modules:
        if status_callback: status_callback(f"{prefix}Analyzing Urban Heat...")
        try:
            score, lst_val, lst_img, lst_stats = calculate_heat_score(geometry, year)
            results["Urban Heat"] = {
                "score": score,
                "value": lst_val,
                "metric": "LST (°C)",
                "stats": lst_stats
            }
            if lst_img:
                try: tile_urls['lst'] = get_tile_url(lst_img.clip(geometry), LST_VIS_PARAMS)
                except: pass
            score_sum += score
            max_score_sum += 25
        except Exception as e:
             print(f"Error in Heat for {region_name}: {e}")
             results["Urban Heat"] = {"score": 0, "value": 0, "metric": "LST (°C)", "error": str(e)}

    # 4. Future Risk
    if "Future Risk" in selected_modules:
        if status_callback: status_callback(f"{prefix}Projecting Future Risks...")
        try:
            score, risk_val, trends, trend_insights = calculate_prediction_score(geometry, year)
            results["Future Risk"] = {
                "score": score,
                "value": risk_val,
                "metric": "Risk Index",
                "trends": trends,
                "insights": trend_insights
            }
            score_sum += score
            max_score_sum += 25
        except Exception as e:
             print(f"Error in Risk for {region_name}: {e}")
             results["Future Risk"] = {"score": 0, "value": 0, "metric": "Risk Index", "error": str(e)}

    # 5. Earthquake
    if "Earthquake Safety" in selected_modules:
        if status_callback: status_callback(f"{prefix}Assessing Seismic Hazard...")
        try:
            # Need imp_ratio for full risk calculation, default 0.5 if not calc already
            imp_ratio = results.get("Vegetation", {}).get("impervious", 0.5)
            score, eq_risk_score, zone_info, hazard_stats, risk_data = calculate_earthquake_score(geometry, region_name, imp_ratio)
            results["Earthquake Safety"] = {
                "score": score,
                "value": eq_risk_score,
                "metric": "Comp. Risk",
                "zone": zone_info,
                "hazard": hazard_stats
            }
            if 'tile_url' in hazard_stats:
                tile_urls['earthquake'] = hazard_stats['tile_url']
            score_sum += score
            max_score_sum += 25
        except Exception as e:
             print(f"Error in Earthquake for {region_name}: {e}")
             results["Earthquake Safety"] = {"score": 0, "value": 0, "metric": "Risk Score", "error": str(e)}

    # Composite Score
    total_uss = 0
    if max_score_sum > 0:
        # Normalize to 100 based on selected modules
        total_uss = (score_sum / max_score_sum) * 100
    
    classification, color, desc = get_uss_classification(total_uss)
    
    return {
        "region_name": region_name,
        "results": results,
        "total_uss": total_uss,
        "classification": classification,
        "class_color": color,
        "tile_urls": tile_urls
    }

def perform_comparison(region_a, region_b, modules, year=2023, status_callback=None):
    """
    Main driver for comparison.
    region_a/b: { 'geometry': ee.Geometry, 'name': str }
    """
    
    # We can run these sequentially to avoid thread/context issues with GEE client side objects in some environments,
    # or use ThreadPoolExecutor if we are sure about thread safety of the session. 
    # For Streamlit + GEE Python API, sequential is often safer to avoid "ComputedObject" mix-ups or race conditions,
    # though parallel is faster. Let's try sequential first for stability.
    
    data_a = fetch_region_data(
        region_a['geometry'], 
        region_a['name'], 
        year, 
        modules, 
        status_callback, 
        prefix="[Region A] "
    )
    
    data_b = fetch_region_data(
        region_b['geometry'], 
        region_b['name'], 
        year, 
        modules, 
        status_callback, 
        prefix="[Region B] "
    )
    
    summary = generate_comparative_summary(data_a, data_b, modules)
    
    return {
        "region_a": data_a,
        "region_b": data_b,
        "summary": summary,
        "modules": modules,
        "year": year
    }

def generate_comparative_summary(data_a, data_b, modules):
    """
    Generates natural language comparison validation.
    """
    summary = []
    
    # Overall USS Comparison
    uss_diff = data_a['total_uss'] - data_b['total_uss']
    leader = data_a['region_name'] if uss_diff > 0 else data_b['region_name']
    
    if abs(uss_diff) < 2:
        summary.append("Both regions show **similar overall sustainability performance**.")
    else:
        summary.append(f"**{leader}** outperforms overall with a Sustainability Score of **{max(data_a['total_uss'], data_b['total_uss']):.1f}** compared to **{min(data_a['total_uss'], data_b['total_uss']):.1f}**.")

    # Module-wise highlights
    if "Vegetation" in modules:
        val_a = data_a['results']['Vegetation'].get('value', 0)
        val_b = data_b['results']['Vegetation'].get('value', 0)
        diff_pct = ((val_a - val_b) / (val_b + 0.001)) * 100
        
        if abs(diff_pct) > 10:
            better_veg = data_a['region_name'] if val_a > val_b else data_b['region_name']
            summary.append(f"**{better_veg}** has significantly **greener cover** (NDVI {max(val_a, val_b):.2f} vs {min(val_a, val_b):.2f}).")
            
    if "Air Quality" in modules:
        # Lower AQI is better
        val_a = data_a['results']['Air Quality'].get('value', 0)
        val_b = data_b['results']['Air Quality'].get('value', 0)
        
        if abs(val_a - val_b) > 20:
            cleaner = data_a['region_name'] if val_a < val_b else data_b['region_name']
            summary.append(f"**{cleaner}** enjoys specificially **cleaner air** (AQI {min(val_a, val_b):.0f}).")

    if "Urban Heat" in modules:
        # Lower LST is better
        val_a = data_a['results']['Urban Heat'].get('value', 0)
        val_b = data_b['results']['Urban Heat'].get('value', 0)
        
        if abs(val_a - val_b) > 3:
            cooler = data_a['region_name'] if val_a < val_b else data_b['region_name']
            summary.append(f"**{cooler}** is noticeably **cooler** ({min(val_a, val_b):.1f}°C vs {max(val_a, val_b):.1f}°C).")
            
    if "Earthquake Safety" in modules:
        zone_a = data_a['results']['Earthquake Safety'].get('zone', {}).get('zone', 'Unknown')
        zone_b = data_b['results']['Earthquake Safety'].get('zone', {}).get('zone', 'Unknown')
        
        if zone_a != zone_b:
            summary.append(f"Seismic risk varies: **{data_a['region_name']}** is in **Zone {zone_a}** while **{data_b['region_name']}** is in **Zone {zone_b}**.")
            
    return " ".join(summary)
