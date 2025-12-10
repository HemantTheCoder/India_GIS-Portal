import ee
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from services.gee_lulc import get_sentinel2_image, calculate_lulc_statistics_with_area, LULC_CLASSES, BUILT_CLASSES, get_dynamic_world_lulc
from services.gee_aqi import get_pollutant_image, calculate_pollutant_statistics, POLLUTANT_INFO
from services.gee_lst import get_mean_lst, get_lst_statistics
from services.gee_indices import calculate_ndvi_sentinel, calculate_ndwi_sentinel, calculate_ndbi_sentinel
from services.gee_core import get_tile_url

LULC_VIS_PARAMS = {
    'min': 0,
    'max': 8,
    'palette': ['419BDF', '397D49', '88B053', '7A87C6', 'E49635', 'DFC35A', 'C4281B', 'A59B8F', 'B39FE1']
}

NDVI_VIS_PARAMS = {
    'min': -0.2,
    'max': 0.8,
    'palette': ['#d73027', '#fc8d59', '#fee08b', '#d9ef8b', '#91cf60', '#1a9850']
}

LST_VIS_PARAMS = {
    'min': 20,
    'max': 45,
    'palette': ['040274', '040281', '0502a3', '0602ff', '235cb1', '307ef3', '30c8e2', 
                '3ae237', 'b5e22e', 'fff705', 'ffd611', 'ff8b13', 'ff500d', 'ff0000', 'c21301']
}

PM25_VIS_PARAMS = {
    'min': 0,
    'max': 100,
    'palette': ['00FF00', 'FFFF00', 'FF8C00', 'FF0000', '8B0000', '4B0082']
}


def calculate_vegetation_score(geometry, year):
    """
    Computes Vegetation Score (0-25) using:
    25 * ((NDVI_normalized + (1 - impervious_ratio)) / 2)
    Returns score, ndvi, impervious_ratio, ndvi_image, lulc_image
    """
    try:
        start_date = f"{year}-01-01"
        end_date = f"{year}-12-31"
        
        s2_image = get_sentinel2_image(geometry, start_date, end_date)
        ndvi_image = None
        lulc_image = None
        lulc_stats = None
        
        if s2_image is None:
            return 0, 0, 0, None, None, None
            
        ndvi_image = calculate_ndvi_sentinel(s2_image)
        ndvi_stats = ndvi_image.reduceRegion(
            reducer=ee.Reducer.mean().combine(ee.Reducer.stdDev(), sharedInputs=True),
            geometry=geometry,
            scale=100,
            maxPixels=1e9
        ).getInfo()
        mean_ndvi = ndvi_stats.get('NDVI_mean', 0) if ndvi_stats else 0
        if mean_ndvi is None:
            mean_ndvi = ndvi_stats.get('NDVI', 0) if ndvi_stats else 0
        ndvi_normalized = min(max(mean_ndvi / 0.8, 0), 1)

        lulc_image = get_dynamic_world_lulc(geometry, start_date, end_date)
        impervious_ratio = 0.5
        
        if lulc_image:
            lulc_stats = calculate_lulc_statistics_with_area(lulc_image, geometry)
            if lulc_stats and "classes" in lulc_stats:
                total_area = lulc_stats.get("total_area_sqkm", 1)
                built_area = 0
                for cls_name, data in lulc_stats["classes"].items():
                    if data["class_id"] in BUILT_CLASSES:
                        built_area += data["area_sqkm"]
                impervious_ratio = built_area / total_area if total_area > 0 else 0

        score = 25 * ((ndvi_normalized + (1 - impervious_ratio)) / 2)
        return max(0, min(25, score)), mean_ndvi, impervious_ratio, ndvi_image, lulc_image, lulc_stats

    except Exception as e:
        print(f"Error in veg score: {e}")
        return 0, 0, 0, None, None, None


def calculate_aqi_score(geometry, year):
    """
    Computes Air Quality Score (0-25) using PM2.5.
    Returns score, aqi, pm25, pm25_image, pollutant_stats
    """
    try:
        start_date = f"{year}-01-01"
        end_date = f"{year}-12-31"
        
        pm25_img = get_pollutant_image(geometry, "PM2.5", start_date, end_date)
        no2_img = get_pollutant_image(geometry, "NO2", start_date, end_date)
        
        pm25_stats = None
        no2_stats = None
        
        if pm25_img:
            pm25_stats = calculate_pollutant_statistics(pm25_img, geometry, "PM2.5")
            mean_pm25 = pm25_stats.get("mean", 0) if pm25_stats else 0
            
            if mean_pm25 < 12: aqi = mean_pm25 * (50/12)
            elif mean_pm25 < 35.4: aqi = 50 + (mean_pm25-12) * (50/23.4)
            elif mean_pm25 < 55.4: aqi = 100 + (mean_pm25-35.4) * (50/20)
            elif mean_pm25 < 150.4: aqi = 150 + (mean_pm25-55.4) * (50/95)
            else: aqi = 200 + (mean_pm25-150.4) * (100/100)
            
            aqi = min(500, aqi)
        else:
            aqi = 100
            mean_pm25 = 30
            
        if no2_img:
            no2_stats = calculate_pollutant_statistics(no2_img, geometry, "NO2")

        score = 25 * (1 - (aqi / 500))
        
        return max(0, min(25, score)), aqi, mean_pm25, pm25_img, {
            "pm25": pm25_stats,
            "no2": no2_stats
        }
        
    except Exception as e:
        print(f"Error in AQI score: {e}")
        return 0, 0, 0, None, None


def calculate_heat_score(geometry, year):
    """
    Computes Urban Heat Score (0-25).
    Returns score, lst_value, lst_image, lst_stats
    """
    try:
        start_date = f"{year}-01-01"
        end_date = f"{year}-12-31"
        
        lst_limit_low = 22
        lst_limit_high = 50
        
        mean_lst_img = get_mean_lst(geometry, start_date, end_date)
        lst_stats = None
        
        if mean_lst_img:
            lst_stats = get_lst_statistics(mean_lst_img, geometry)
            lst_val = lst_stats.get("LST_Day_mean", 30) if lst_stats else 30
            if lst_val is None:
                lst_val = 30
        else:
            lst_val = 30
            
        lst_clamped = max(lst_limit_low, min(lst_limit_high, lst_val))
        
        score = 25 * (1 - ((lst_clamped - lst_limit_low) / (lst_limit_high - lst_limit_low)))
        return max(0, min(25, score)), lst_val, mean_lst_img, lst_stats
        
    except Exception as e:
        print(f"Error in Heat score: {e}")
        return 0, 0, None, None


def calculate_prediction_score(geometry, year):
    """
    Computes Prediction Score (0-25) based on historical trends.
    """
    try:
        from services.prediction import analyze_lulc_trends, get_historical_lulc_data
        
        start_hist = year - 5
        end_hist = year - 1
        
        hist_data = get_historical_lulc_data(geometry, start_hist, end_hist)
        trends = analyze_lulc_trends(hist_data)
        
        risk = 0.2
        trend_insights = []
        
        if trends:
            built_trend = trends.get("Built Area")
            if built_trend and built_trend.get("slope", 0) > 0:
                risk += 0.2
                trend_insights.append(f"Built area increasing at {built_trend.get('slope', 0)*100:.2f}% per year")
            
            tree_trend = trends.get("Trees")
            if tree_trend and tree_trend.get("slope", 0) < 0:
                risk += 0.2
                trend_insights.append(f"Tree cover declining at {abs(tree_trend.get('slope', 0))*100:.2f}% per year")
                
            grass_trend = trends.get("Grass")
            if grass_trend and grass_trend.get("slope", 0) < 0:
                risk += 0.1
                trend_insights.append(f"Grassland declining")
                
        risk = min(1.0, risk)
        
        score = 25 * (1 - risk)
        return max(0, min(25, score)), risk, trends, trend_insights
        
    except Exception as e:
        print(f"Error in Prediction score: {e}")
        return 12.5, 0.5, None, []


def get_uss_classification(uss):
    """Returns classification and color based on USS score."""
    if uss >= 80:
        return "Excellent", "#22c55e", "The region demonstrates outstanding environmental sustainability."
    elif uss >= 60:
        return "Good", "#84cc16", "The region shows good sustainability with room for improvement."
    elif uss >= 40:
        return "Moderate", "#eab308", "The region has moderate sustainability requiring attention."
    elif uss >= 20:
        return "Poor", "#f97316", "The region has poor sustainability needing urgent intervention."
    else:
        return "Critical", "#ef4444", "The region is in critical condition requiring immediate action."


def get_score_grade(score, max_score=25):
    """Returns grade for individual module score."""
    pct = (score / max_score) * 100
    if pct >= 80: return "A", "#22c55e"
    elif pct >= 60: return "B", "#84cc16"
    elif pct >= 40: return "C", "#eab308"
    elif pct >= 20: return "D", "#f97316"
    else: return "F", "#ef4444"


def generate_comprehensive_report(geometry, region_name="Selected Region", year=2023, buffer_km=10):
    """
    Generates comprehensive sustainability report with all data, images, and analysis.
    """
    
    veg_score, ndvi_val, imp_ratio, ndvi_img, lulc_img, lulc_stats = calculate_vegetation_score(geometry, year)
    aqi_score, aqi_val, pm25_val, pm25_img, pollutant_stats = calculate_aqi_score(geometry, year)
    heat_score, lst_val, lst_img, lst_stats = calculate_heat_score(geometry, year)
    pred_score, risk_val, trends, trend_insights = calculate_prediction_score(geometry, year)
    
    total_uss = veg_score + aqi_score + heat_score + pred_score
    classification, class_color, class_desc = get_uss_classification(total_uss)
    
    scores_dict = {
        "Vegetation": veg_score,
        "Air Quality": aqi_score,
        "Urban Heat": heat_score,
        "Future Risk": pred_score
    }
    weakest_sector = min(scores_dict.keys(), key=lambda k: scores_dict[k])
    strongest_sector = max(scores_dict.keys(), key=lambda k: scores_dict[k])
    
    tile_urls = {}
    
    if ndvi_img:
        try:
            tile_urls['ndvi'] = get_tile_url(ndvi_img.clip(geometry), NDVI_VIS_PARAMS)
        except:
            pass
            
    if lulc_img:
        try:
            tile_urls['lulc'] = get_tile_url(lulc_img.clip(geometry), LULC_VIS_PARAMS)
        except:
            pass
            
    if pm25_img:
        try:
            tile_urls['pm25'] = get_tile_url(pm25_img.clip(geometry), PM25_VIS_PARAMS)
        except:
            pass
            
    if lst_img:
        try:
            tile_urls['lst'] = get_tile_url(lst_img.clip(geometry), LST_VIS_PARAMS)
        except:
            pass

    veg_grade, veg_color = get_score_grade(veg_score)
    aqi_grade, aqi_color = get_score_grade(aqi_score)
    heat_grade, heat_color = get_score_grade(heat_score)
    pred_grade, pred_color = get_score_grade(pred_score)

    overview_text = f"""
The **Urban Sustainability Score (USS)** for **{region_name}** is **{total_uss:.1f}/100**, classified as **{classification}**. 
{class_desc}

This comprehensive assessment integrates satellite-derived data across four critical environmental dimensions:
vegetation health and land use, air quality, thermal comfort, and predictive climate risks.

**Key Findings:**
- The region's strongest performance is in **{strongest_sector}** (Score: {scores_dict[strongest_sector]:.1f}/25)
- The primary area of concern is **{weakest_sector}** (Score: {scores_dict[weakest_sector]:.1f}/25)
- Average NDVI: **{ndvi_val:.3f}** | Impervious Surface: **{imp_ratio*100:.1f}%**
- Air Quality Index: **{aqi_val:.0f}** | PM2.5: **{pm25_val:.1f} µg/m³**
- Land Surface Temperature: **{lst_val:.1f}°C**
- Future Risk Index: **{risk_val:.2f}**
"""

    veg_status = "healthy and dense" if ndvi_val > 0.5 else "moderate" if ndvi_val > 0.3 else "sparse and concerning"
    aqi_status = "excellent" if aqi_val < 50 else "good" if aqi_val < 100 else "moderate" if aqi_val < 150 else "unhealthy" if aqi_val < 200 else "hazardous"
    heat_status = "comfortable" if lst_val < 30 else "warm" if lst_val < 35 else "hot" if lst_val < 40 else "extreme"
    
    analysis_sections = {
        "vegetation": f"""
**Vegetation & Land Use Analysis (Score: {veg_score:.1f}/25 - Grade {veg_grade})**

The vegetation assessment reveals an NDVI of **{ndvi_val:.3f}**, indicating {veg_status} vegetation cover. 
The impervious surface ratio stands at **{imp_ratio*100:.1f}%**, {"suggesting significant urbanization pressure" if imp_ratio > 0.4 else "indicating balanced land use" if imp_ratio > 0.2 else "showing predominantly natural land cover"}.

{"⚠️ **Warning:** High impervious surface coverage reduces natural water infiltration and increases urban runoff." if imp_ratio > 0.5 else ""}
{"✅ Vegetation density is above healthy thresholds." if ndvi_val > 0.4 else "⚠️ Vegetation density is below optimal levels - consider green infrastructure investments."}
""",
        "aqi": f"""
**Air Quality Analysis (Score: {aqi_score:.1f}/25 - Grade {aqi_grade})**

Air quality conditions are **{aqi_status}** with an estimated AQI of **{aqi_val:.0f}**.
PM2.5 concentration averages **{pm25_val:.1f} µg/m³** {"(exceeds WHO guideline of 15 µg/m³)" if pm25_val > 15 else "(within WHO guidelines)"}.

{"⚠️ **Health Advisory:** Current pollution levels may affect sensitive groups." if aqi_val > 100 else ""}
{"✅ Air quality meets acceptable standards for outdoor activities." if aqi_val < 100 else ""}
""",
        "heat": f"""
**Urban Heat Analysis (Score: {heat_score:.1f}/25 - Grade {heat_grade})**

Land Surface Temperature averages **{lst_val:.1f}°C**, indicating **{heat_status}** thermal conditions.
{"The region shows signs of Urban Heat Island effect with elevated temperatures in built-up areas." if lst_val > 35 else "Thermal conditions are within comfortable ranges for most of the year."}

{"⚠️ **Heat Stress Warning:** High LST indicates potential heat stress zones requiring cooling interventions." if lst_val > 40 else ""}
{"✅ Temperature levels are conducive to outdoor activities and urban comfort." if lst_val < 32 else ""}
""",
        "prediction": f"""
**Predictive Risk Analysis (Score: {pred_score:.1f}/25 - Grade {pred_grade})**

Based on 5-year historical trend analysis, the future environmental risk index is **{risk_val:.2f}** (scale 0-1).
{"⚠️ **High Risk:** Current development patterns suggest accelerating environmental degradation." if risk_val > 0.6 else "The region shows stable or improving environmental trends." if risk_val < 0.3 else "Moderate risk levels require continued monitoring and proactive planning."}

**Observed Trends:**
{chr(10).join([f"- {insight}" for insight in trend_insights]) if trend_insights else "- Trend data insufficient for detailed analysis"}
"""
    }

    mitigations = {
        "Vegetation": [
            "Implement Miyawaki method rapid afforestation in urban pockets",
            "Establish green corridors connecting fragmented natural areas",
            "Mandate permeable paving in new developments",
            "Create rooftop and vertical gardens in commercial zones",
            "Protect existing green spaces through zoning regulations"
        ],
        "Air Quality": [
            "Establish Low Emission Zones in high-traffic areas",
            "Enforce strict construction dust control measures",
            "Plant dense vegetation buffers along major roadways",
            "Promote electric vehicle adoption through incentives",
            "Monitor industrial emissions with real-time sensors"
        ],
        "Urban Heat": [
            "Implement cool roof programs for residential and commercial buildings",
            "Restore and maintain urban water bodies as cooling zones",
            "Increase tree canopy coverage along pedestrian areas",
            "Use heat-reflective materials in new infrastructure",
            "Create shaded public spaces and cooling centers"
        ],
        "Future Risk": [
            "Develop comprehensive climate resilience master plan",
            "Protect wetlands and natural flood mitigation zones",
            "Invest in sustainable public transportation infrastructure",
            "Implement early warning systems for environmental hazards",
            "Establish community-based environmental monitoring networks"
        ]
    }
    
    mitigation_text = "\n".join([f"- {m}" for m in mitigations.get(weakest_sector, [])])
    
    who_comparison = {
        "pm25": {"value": pm25_val, "limit": 15, "name": "PM2.5 (24-hr)"},
        "lst": {"value": lst_val, "limit": 32, "name": "Thermal Comfort"}
    }

    roadmap = [
        {
            "phase": "Immediate (0-6 months)",
            "actions": [
                f"Conduct detailed assessment of {weakest_sector} hotspots",
                "Establish baseline monitoring stations",
                "Launch public awareness campaign"
            ],
            "expected_gain": 2
        },
        {
            "phase": "Short-term (6-18 months)",
            "actions": [
                f"Pilot {mitigations.get(weakest_sector, ['improvement'])[0].lower()}",
                "Develop policy framework for sustainability",
                "Secure funding for infrastructure improvements"
            ],
            "expected_gain": 5
        },
        {
            "phase": "Medium-term (18-36 months)",
            "actions": [
                "Scale successful pilot programs region-wide",
                "Implement regulatory enforcement mechanisms",
                "Establish public-private partnerships"
            ],
            "expected_gain": 8
        },
        {
            "phase": "Long-term (3-10 years)",
            "actions": [
                "Achieve structural transformation in land use",
                "Integrate sustainability into all urban planning",
                "Reach target USS of 70+"
            ],
            "expected_gain": 15
        }
    ]

    return {
        "region_name": region_name,
        "year": year,
        "buffer_km": buffer_km,
        "scores": {
            "vegetation": {"score": veg_score, "grade": veg_grade, "color": veg_color, "value": ndvi_val, "metric": "NDVI"},
            "aqi": {"score": aqi_score, "grade": aqi_grade, "color": aqi_color, "value": aqi_val, "metric": "AQI"},
            "heat": {"score": heat_score, "grade": heat_grade, "color": heat_color, "value": lst_val, "metric": "LST (°C)"},
            "prediction": {"score": pred_score, "grade": pred_grade, "color": pred_color, "value": risk_val, "metric": "Risk Index"},
            "total_uss": total_uss,
            "classification": classification,
            "class_color": class_color,
            "class_desc": class_desc
        },
        "weakest_sector": weakest_sector,
        "strongest_sector": strongest_sector,
        "tile_urls": tile_urls,
        "raw_metrics": {
            "ndvi": ndvi_val,
            "impervious": imp_ratio,
            "aqi": aqi_val,
            "pm25": pm25_val,
            "lst": lst_val,
            "risk": risk_val
        },
        "lulc_stats": lulc_stats,
        "lst_stats": lst_stats,
        "pollutant_stats": pollutant_stats,
        "trends": trends,
        "trend_insights": trend_insights,
        "text_sections": {
            "overview": overview_text,
            "analysis": analysis_sections,
            "mitigation": mitigation_text,
            "mitigations_full": mitigations,
            "roadmap": roadmap
        },
        "who_comparison": who_comparison
    }


def generate_sustainability_report(geometry, region_name="Selected Region", year=2023):
    """Legacy wrapper for backward compatibility."""
    report = generate_comprehensive_report(geometry, region_name, year)
    
    return {
        "scores": {
            "Vegetation": {"score": report["scores"]["vegetation"]["score"], "value": report["raw_metrics"]["ndvi"], "metric": "NDVI"},
            "Air Quality": {"score": report["scores"]["aqi"]["score"], "value": report["raw_metrics"]["aqi"], "metric": "AQI"},
            "Urban Heat": {"score": report["scores"]["heat"]["score"], "value": report["raw_metrics"]["lst"], "metric": "LST (°C)"},
            "Prediction": {"score": report["scores"]["prediction"]["score"], "value": report["raw_metrics"]["risk"], "metric": "Risk Index"},
            "Total USS": report["scores"]["total_uss"],
            "Classification": report["scores"]["classification"]
        },
        "weakest_sector": report["weakest_sector"],
        "text_sections": {
            "overview": report["text_sections"]["overview"],
            "analysis": "\n\n".join(report["text_sections"]["analysis"].values()),
            "mitigation": report["text_sections"]["mitigation"],
            "improvement": f"Improving {report['weakest_sector']} can increase USS by ~10 points.",
            "roadmap": "\n".join([f"**{r['phase']}**: {', '.join(r['actions'][:2])}" for r in report["text_sections"]["roadmap"]])
        },
        "raw_metrics": report["raw_metrics"]
    }
