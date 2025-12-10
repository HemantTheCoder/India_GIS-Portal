import ee
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from services.gee_lulc import get_sentinel2_image, calculate_lulc_statistics_with_area, LULC_CLASSES, BUILT_CLASSES
from services.gee_aqi import get_pollutant_image, calculate_pollutant_statistics, POLLUTANT_INFO
from services.gee_lst import get_mean_lst, get_lst_statistics
from services.gee_indices import calculate_ndvi_sentinel
from services.prediction import analyze_lulc_trends, get_historical_lulc_data

def calculate_vegetation_score(geometry, year):
    """
    Computes Vegetation Score (0-25) using:
    25 * ((NDVI_normalized + (1 - impervious_ratio)) / 2)
    NDVI_normalized = NDVI / 0.8 (capped 0-1)
    """
    try:
        start_date = f"{year}-01-01"
        end_date = f"{year}-12-31"
        
        # Get NDVI
        s2_image = get_sentinel2_image(geometry, start_date, end_date)
        if s2_image is None:
            return 0, 0, 0
            
        ndvi_image = calculate_ndvi_sentinel(s2_image)
        ndvi_stats = ndvi_image.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=geometry,
            scale=100, # Efficient scale
            maxPixels=1e9
        ).getInfo()
        mean_ndvi = ndvi_stats.get('NDVI', 0) if ndvi_stats else 0
        ndvi_normalized = min(max(mean_ndvi / 0.8, 0), 1)

        # Get Impervious Ratio (Built Area)
        # Using simple LULC stats if available or approximation
        # Ideally use gee_lulc functions.
        # Let's rely on Dynamic World or similar from gee_lulc if available, 
        # but for speed/simplicity in this aggregated report, we might need a direct call.
        # Re-using get_sentinel2_image is fine, but for LULC we need the classification.
        # Let's use the Dynamic World function from gee_lulc if importable, else implement basic check.
        # Assuming we can't easily get full LULC stats without heavy computation, 
        # we will use NDBI as a proxy or if we can, use the imported LULC function.
        # Let's use the actual numeric LULC stats from services if efficient.
        # actually get_lulc_statistics_with_area is available.
        
        # Note: get_lulc_statistics_with_area requires a lulc image.
        # We need to fetch it.
        from services.gee_lulc import get_dynamic_world_lulc
        lulc_img = get_dynamic_world_lulc(geometry, start_date, end_date)
        if lulc_img:
            stats = calculate_lulc_statistics_with_area(lulc_img, geometry)
            if stats and "classes" in stats:
                total_area = stats.get("total_area_sqkm", 1)
                built_area = 0
                for cls_name, data in stats["classes"].items():
                    if data["class_id"] in BUILT_CLASSES:
                        built_area += data["area_sqkm"]
                impervious_ratio = built_area / total_area if total_area > 0 else 0
            else:
                impervious_ratio = 0.5 # Default fallback
        else:
             impervious_ratio = 0.5

        score = 25 * ((ndvi_normalized + (1 - impervious_ratio)) / 2)
        return max(0, min(25, score)), mean_ndvi, impervious_ratio

    except Exception as e:
        print(f"Error in veg score: {e}")
        return 0, 0, 0

def calculate_aqi_score(geometry, year):
    """
    Computes Air Quality Score (0-25) using:
    25 * (1 - (AQI / 500))
    Approximate AQI from PM2.5 if direct AQI not available.
    """
    try:
        start_date = f"{year}-01-01"
        end_date = f"{year}-12-31"
        
        # Use PM2.5 as primary driver for AQI approximation in this context
        pm25_img = get_pollutant_image(geometry, "PM2.5", start_date, end_date)
        
        if pm25_img:
            stats = calculate_pollutant_statistics(pm25_img, geometry, "PM2.5")
            mean_pm25 = stats.get("mean", 0) if stats else 0
            
            # Simple conversion: US EPA breakpoints roughly
            # 12ug -> 50 AQI, 35ug -> 100 AQI, 55ug -> 150 AQI, 150ug -> 200 AQI, 250ug -> 300 AQI
            # Linear approximation for simplicity: AQI ~= PM2.5 * 2 (rough rule of thumb for average levels)
            # Improved approx:
            if mean_pm25 < 12: aqi = mean_pm25 * (50/12)
            elif mean_pm25 < 35.4: aqi = 50 + (mean_pm25-12) * (50/23.4)
            elif mean_pm25 < 55.4: aqi = 100 + (mean_pm25-35.4) * (50/20)
            elif mean_pm25 < 150.4: aqi = 150 + (mean_pm25-55.4) * (50/95)
            else: aqi = 200 + (mean_pm25-150.4) * (100/100)
            
            aqi = min(500, aqi)
        else:
            aqi = 100 # Default moderate
            mean_pm25 = 30

        score = 25 * (1 - (aqi / 500))
        return max(0, min(25, score)), aqi, mean_pm25
        
    except Exception as e:
        print(f"Error in AQI score: {e}")
        return 0, 0, 0


def calculate_heat_score(geometry, year):
    """
    Computes Urban Heat Score (0-25) using:
    25 * (1 - ((LST - 22) / (50 - 22)))
    LST clamped between 22 and 50.
    """
    try:
        start_date = f"{year}-01-01"
        end_date = f"{year}-12-31"
        
        lst_limit_low = 22
        lst_limit_high = 50
        
        mean_lst_img = get_mean_lst(geometry, start_date, end_date)
        if mean_lst_img:
            stats = get_lst_statistics(mean_lst_img, geometry)
            # Use LST_Day_mean
            lst_val = stats.get("LST_Day_mean", 30) if stats else 30
        else:
            lst_val = 30
            
        lst_clamped = max(lst_limit_low, min(lst_limit_high, lst_val))
        
        score = 25 * (1 - ((lst_clamped - lst_limit_low) / (lst_limit_high - lst_limit_low)))
        return max(0, min(25, score)), lst_val
        
    except Exception as e:
        print(f"Error in Heat score: {e}")
        return 0, 0

def calculate_prediction_score(geometry, year):
    """
    Computes Prediction Score (0-25) using:
    25 * (1 - future_risk)
    risk derived from predicted % increase in heat/pollution/veg-loss.
    """
    try:
        # Simplified risk calculation based on trends
        # Look back 5 years to project risk
        start_hist = year - 5
        end_hist = year - 1
        
        # check veg trend
        hist_data = get_historical_lulc_data(geometry, start_hist, end_hist)
        trends = analyze_lulc_trends(hist_data)
        
        risk = 0.2 # Base risk
        
        if trends:
            # Check built area trend (Class 6)
            built_trend = trends.get("Built Area")
            if built_trend and built_trend.get("slope", 0) > 0:
                risk += 0.2 # Increasing urbanization risk
            
            # Check tree loss (Class 1)
            tree_trend = trends.get("Trees")
            if tree_trend and tree_trend.get("slope", 0) < 0:
                risk += 0.2 # Deforestation risk
                
        # Cap risk at 1.0
        risk = min(1.0, risk)
        
        score = 25 * (1 - risk)
        return max(0, min(25, score)), risk
        
    except Exception as e:
        print(f"Error in Prediction score: {e}")
        return 0, 0

def generate_sustainability_report(geometry, region_name="Selected Region", year=2023):
    """
    Generates the full report data structure.
    """
    
    # 1. Compute Scores
    veg_score, ndvi_val, imp_ratio = calculate_vegetation_score(geometry, year)
    aqi_score, aqi_val, pm25_val = calculate_aqi_score(geometry, year)
    heat_score, lst_val = calculate_heat_score(geometry, year)
    pred_score, risk_val = calculate_prediction_score(geometry, year)
    
    total_uss = veg_score + aqi_score + heat_score + pred_score
    
    # Classify USS
    if total_uss >= 80: classification = "Excellent"
    elif total_uss >= 60: classification = "Moderate"
    elif total_uss >= 40: classification = "Poor"
    else: classification = "Critical"
    
    # 2. Identify Weakest Sector
    scores = {
        "Vegetation": veg_score,
        "Air Quality": aqi_score,
        "Urban Heat": heat_score,
        "Future Risk": pred_score
    }
    weakest_sector = min(scores, key=scores.get)
    
    # 3. Generate Sections
    
    # (A) Interpretive Overview
    overview_text = f"""
    The **Urban Sustainability Score (USS)** for **{region_name}** is **{total_uss:.1f}/100**, classified as **{classification}**. 
    This composite metric integrates satellite-derived data on vegetation health, air quality, thermal comfort, and predictive climate risks.
    
    The region's environmental state is currently driven by its **{weakest_sector}** performance. 
    With an NDVI of **{ndvi_val:.2f}** and an impervious surface ratio of **{imp_ratio*100:.1f}%**, the biological infrastructure plays a key role.
    Simultaneously, the air quality index averages around **{aqi_val:.0f}**, while land surface temperatures average **{lst_val:.1f}°C**.
    """
    
    # (B) Module-wise Analysis (Summarized)
    # Ideally this would be dynamic based on more in-depth trend analysis
    analysis_text = f"""
    ### 1. Vegetation & Land Use
    - **Current State**: NDVI is {ndvi_val:.2f}, indicating {"healthy" if ndvi_val > 0.4 else "sparse"} vegetation.
    - **Trend**: Urbanization pressure is evident with {imp_ratio*100:.1f}% impervious coverage.
    
    ### 2. Air Quality
    - **Status**: Average AQI is {aqi_val:.0f} (PM2.5: {pm25_val:.1f} µg/m³).
    - **Implication**: {"Air quality is a major concern requiring immediate intervention." if aqi_val > 100 else "Air quality is within manageable limits but requires monitoring."}
    
    ### 3. Urban Heat
    - **Thermal Comfort**: Mean LST is {lst_val:.1f}°C.
    - **UHI Effect**: High impervious surfaces contribution to heat island formation is {"significant" if lst_val > 35 else "moderate"}.
    
    ### 4. Predictive Risk
    - **Risk Factor**: Calculated at {risk_val:.2f} (0-1 scale).
    - **Outlook**: Future development trends suggest a {"high" if risk_val > 0.5 else "stable"} probability of environmental degradation if unchecked.
    """
    
    # (E) Mitigation Strategies - Customized
    mitigations = []
    if weakest_sector == "Vegetation":
        mitigations = [
            "**Strategic Afforestation**: Implement Miyawaki forests in available pocket spaces.",
            "**Green Corridors**: Connect fragmented green spaces to improve biodiversity and cooling.",
            "**Permeable Paving**: Mandate permeable materials for new parking lots to reduce runoff."
        ]
        score_gain_est = 10
    elif weakest_sector == "Air Quality":
        mitigations = [
            "**Traffic Management**: Implement low-emission zones (LEZ) in city centers.",
            "**Construction Dust Control**: En strict regulations for construction sites (sprinklers/barriers).",
            "**Green Buffers**: Plant dense foliage along major highways to trap particulate matter."
        ]
        score_gain_est = 8
    elif weakest_sector == "Urban Heat":
        mitigations = [
            "**Cool Roofs**: Subsidize white reflective paint for industrial and residential roofs.",
            "**Urban Water Bodies**: Revive and maintain lakes/ponds to act as heat sinks.",
            "**Shading Policy**: Increase tree canopy coverage along pedestrian walkways."
        ]
        score_gain_est = 12
    else: # Future Risk
        mitigations = [
            "**Policy Framework**: Enforce stricter zoning laws preventing encroachments on wetlands.",
            "**Sustainable Transport**: Invest heavily in EV infrastructure and public transit.",
            "**Climate Resilience Plan**: Develop a 10-year master plan for climate adaptation."
        ]
        score_gain_est = 5
        
    mitigation_text = "\n".join([f"- {m}" for m in mitigations])
    
    # (F) Improvement Projection
    improvement_text = f"""
    Improving the **{weakest_sector}** sector through the targeted strategies above is estimated to increase the overall USS by approximately **+{score_gain_est} points**.
    This would potentially raise the region's classification from **{classification}** to **{"Excellent" if total_uss + score_gain_est >= 80 else "Moderate" if total_uss + score_gain_est >= 60 else "Poor"}**.
    """
    
    # (G) Action Roadmap
    roadmap_text = f"""
    | Timeline | Action Item | Expected Outcome |
    |----------|-------------|------------------|
    | **Short-term (0-1 yr)** | Pilot {mitigations[0].split(':')[0].replace('*','')} projects in hotspots. | Immediate relief in critical zones. |
    | **Mid-term (1-3 yrs)** | Scale up {mitigations[1].split(':')[0].replace('*','')} across the region. | Structural improvement in {weakest_sector}. |
    | **Long-term (3-10 yrs)** | Full implementation of {mitigations[2].split(':')[0].replace('*','')} and policy shifts. | Sustainable dominance of the {weakest_sector} sector. |
    """

    return {
        "scores": {
            "Vegetation": {"score": veg_score, "value": ndvi_val, "metric": "NDVI"},
            "Air Quality": {"score": aqi_score, "value": aqi_val, "metric": "AQI"},
            "Urban Heat": {"score": heat_score, "value": lst_val, "metric": "LST (°C)"},
            "Prediction": {"score": pred_score, "value": risk_val, "metric": "Risk Index"},
            "Total USS": total_uss,
            "Classification": classification
        },
        "weakest_sector": weakest_sector,
        "text_sections": {
            "overview": overview_text,
            "analysis": analysis_text,
            "mitigation": mitigation_text,
            "improvement": improvement_text,
            "roadmap": roadmap_text
        },
        "raw_metrics": {
            "ndvi": ndvi_val,
            "impervious": imp_ratio,
            "aqi": aqi_val,
            "pm25": pm25_val,
            "lst": lst_val,
            "risk": risk_val
        }
    }
