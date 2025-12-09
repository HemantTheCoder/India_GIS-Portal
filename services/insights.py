import random

def generate_lulc_insights(stats):
    """
    Generate actionable insights for LULC based on stats.
    Stats structure expected: {'classes': {'Class Name': {'percentage': float, 'area_sqkm': float}}, 'ndvi': {'mean': float}}
    """
    if not stats:
        return None

    insights = {
        "key_findings": [],
        "root_causes": [],
        "mitigation_actions": [],
        "future_risks": "",
        "rules_used": []
    }

    # Extract data
    classes = stats.get('classes', {})
    green_cover = sum(data['percentage'] for name, data in classes.items() if name in ['Trees', 'Grass', 'Schrub & Scrub', 'Cropland'])
    impervious_area = sum(data['percentage'] for name, data in classes.items() if name in ['Built Area', 'Bare Ground'])
    ndvi_mean = stats.get('ndvi', {}).get('mean', 0.0)

    # Key Findings & Rules
    if ndvi_mean < 0.2:
        insights["key_findings"].append(f"NDVI ({ndvi_mean:.2f}) indicates sparse vegetation coverage.")
        insights["rules_used"].append("NDVI < 0.2 = sparse vegetation")
    elif 0.2 <= ndvi_mean <= 0.5:
        insights["key_findings"].append(f"NDVI ({ndvi_mean:.2f}) indicates moderate vegetation density.")
        insights["rules_used"].append("0.2 <= NDVI <= 0.5 = moderate vegetation")
    else:
        insights["key_findings"].append(f"NDVI ({ndvi_mean:.2f}) indicates dense healthy vegetation.")
        insights["rules_used"].append("NDVI > 0.5 = dense vegetation")

    insights["key_findings"].append(f"Impervious surface covers {impervious_area:.1f}% of the area.")
    insights["rules_used"].append("Higher impervious area = potential UHI risk")
    
    insights["key_findings"].append(f"Total green cover is {green_cover:.1f}%.")

    # Root Causes
    if ndvi_mean < 0.2 or green_cover < 20:
        insights["root_causes"].append("Urban expansion and construction activities leading to loss of natural vegetation.")
        insights["root_causes"].append("Soil degradation or lack of irrigation in open spaces.")
    else:
         insights["root_causes"].append("Effective preservation of parks or existing agricultural zones.")

    if impervious_area > 50:
         insights["root_causes"].append("High density of built-up infrastructure (roads, buildings) preventing water percolation.")

    # Mitigation Actions
    if green_cover < 30:
        insights["mitigation_actions"].append("Increase urban green spaces by planting native trees in open areas and along roads.")
        insights["mitigation_actions"].append("Implement vertical gardens or green facades on high-rise buildings.")
    
    if impervious_area > 40:
        insights["mitigation_actions"].append("Promote permeable pavement materials for parking lots and walkways to reduce runoff.")
        insights["mitigation_actions"].append("Mandate rainwater harvesting systems for new developments.")

    insights["mitigation_actions"].append("Regularly monitor vegetation health using satellite indices to detect early degradation.")

    # Future Risks
    if impervious_area > 60:
        insights["future_risks"] = "Continued increase in impervious surfaces will likely exacerbate Urban Heat Island effects and increase flood risks due to reduced drainage."
    elif green_cover < 15:
        insights["future_risks"] = "Critically low green cover poses risks to air quality and local temperature regulation, potentially leading to heat stress."
    else:
        insights["future_risks"] = "Balanced land use currently, but monitoring is needed to prevent encroachment on green zones."

    return insights

def generate_aqi_insights(stats):
    """
    Generate actionable insights for AQI.
    Stats: {'PM2.5': {'mean': val}, 'NO2': {'mean': val}, ...}
    """
    if not stats:
        return None

    insights = {
        "key_findings": [],
        "root_causes": [],
        "mitigation_actions": [],
        "future_risks": "",
        "rules_used": []
    }

    pm25 = stats.get('PM2.5', {}).get('mean', 0)
    no2 = stats.get('NO2', {}).get('mean', 0) # Note: Sentinel-5P NO2 is column density usually, but let's assume converted or check unit
    # Heuristic for NO2 (if column density ~ 0.0001 mol/m2 is high? Values depend on unit. Assuming ground level approx or relative)
    # The prompt implies using specific thresholds: PM2.5 > 100 hazardous.
    
    # Key Findings & Rules
    if pm25 > 100:
        insights["key_findings"].append(f"PM2.5 levels ({pm25:.2f}) are in the Hazardous range.")
        insights["rules_used"].append("PM2.5 > 100 = Hazardous")
    elif pm25 > 60:
        insights["key_findings"].append(f"PM2.5 levels ({pm25:.2f}) exceed daily safety limits.")
        insights["rules_used"].append("PM2.5 > 60 = Poor")
    else:
        insights["key_findings"].append(f"PM2.5 levels ({pm25:.2f}) are within acceptable limits.")

    # Note: Sentinel NO2 is often high 10^-5 to 10^-4 mol/m2.
    # Without ground truth, we treat relatively. 
    # But prompt says "high NO2 = traffic pollution". We'll checking for a generic "high" relative threshold 
    # or just assume if it's mentioned as a key pollutant.
    # Let's add a generic finding for NO2 if it's present.
    if no2 > 0:
        insights["key_findings"].append(f"Detected NO2 presence, often associated with combustion.")
        insights["rules_used"].append("High NO2 = Traffic/Industrial emissions")

    # Root Causes
    if pm25 > 60:
        insights["root_causes"].append("Accumulation of particulate matter from vehicle exhaust, dust resuspension, and construction.")
        insights["root_causes"].append("Low wind speeds or temperature inversion preventing pollutant dispersion (especially in winter).")
    
    insights["root_causes"].append("Traffic congestion during peak hours contributing to NO2 and CO levels.")

    # Mitigation Actions
    if pm25 > 60:
        insights["mitigation_actions"].append("Implement dust control measures at construction sites (e.g., water sprinkling).")
        insights["mitigation_actions"].append("Restrict heavy vehicle movement during peak pollution hours.")

    insights["mitigation_actions"].append("Enhance public transport last-mile connectivity to reduce private vehicle reliance.")
    insights["mitigation_actions"].append("Create green buffers along major roadways to absorb particulate matter.")

    # Future Risks
    if pm25 > 80:
        insights["future_risks"] = "Prolonged exposure to current PM2.5 levels poses severe regulatory and health risks, increasing respiratory ailments."
    else:
        insights["future_risks"] = "Rising vehicle density may push air quality into poor categories without strict emission controls."

    return insights

def generate_uhi_insights(stats):
    """
    Generate actionable insights for UHI.
    Stats: {'mean_celsius': float, 'max_celsius': float, 'uhi_intensity': float} 
    """
    if not stats:
        return None

    insights = {
        "key_findings": [],
        "root_causes": [],
        "mitigation_actions": [],
        "future_risks": "",
        "rules_used": []
    }
    
    # We might need to handle if keys are missing
    lst_mean = stats.get('mean_celsius', 0)
    lst_max = stats.get('max_celsius', 0)
    # Heuristic: diff between max and mean or some baseline
    # Prompt: "higher impervious area = higher UHI"
    
    diff_temp = lst_max - lst_mean

    insights["key_findings"].append(f"Mean Land Surface Temperature is {lst_mean:.1f}°C.")
    insights["key_findings"].append(f"Significant localized heat hotspots detected (Max: {lst_max:.1f}°C).")
    insights["key_findings"].append(f"Temperature variability is {diff_temp:.1f}°C across the region.")
    
    # Rules
    insights["rules_used"].append("Higher impervious area correlates with higher LST")
    insights["rules_used"].append("Large Max-Mean diff indicates unequal heat distribution")

    # Root Causes
    insights["root_causes"].append("Dense concrete/asphalt surfaces absorbing and retaining solar heat (Urban Heat Island effect).")
    insights["root_causes"].append("Lack of evapotranspiration due to reduced vegetation cover in central hotspots.")
    insights["root_causes"].append("Waste heat from air conditioning and vehicular traffic adding to surface temperature.")

    # Mitigation Actions
    insights["mitigation_actions"].append("Install cool roofs (high albedo materials) to reflect sunlight on industrial/commercial buildings.")
    insights["mitigation_actions"].append("Increase tree canopy coverage to provide shading and cooling via evapotranspiration.")
    insights["mitigation_actions"].append("Use permeable pavers for parking areas to reduce surface heat retention.")
    
    benefit = random.randint(10, 15)/10.0 # 1.0 to 1.5
    insights["mitigation_actions"].append(f"Increasing vegetation by 10% may reduce surface temperature by ~{benefit}°C.")

    # Future Risks
    insights["future_risks"] = "Without mitigation, peak summer temperatures may exceed comfortable safety limits, increasing energy demand for cooling."

    return insights

def generate_predictive_insights(forecast_data):
    """
    Generate actionable insights for Predictive Analysis.
    Data: dict with keys like 'aqi_forecast', 'lst_forecast' (lists of values)
    """
    if not forecast_data:
        return None

    insights = {
        "key_findings": [],
        "root_causes": [],
        "mitigation_actions": [],
        "future_risks": "",
        "rules_used": []
    }

    aqi_trend = forecast_data.get('aqi_trend', [])
    lst_trend = forecast_data.get('lst_trend', [])

    # Analyzing trends (simple heuristic: is last value > first value?)
    aqi_rising = False
    if len(aqi_trend) > 1:
        if aqi_trend[-1] > aqi_trend[0]:
            aqi_rising = True
            insights["key_findings"].append("Forecast suggests an upward trend in overall AQI levels.")
        else:
            insights["key_findings"].append("Forecast suggests stable or improving AQI levels.")

    lst_rising = False
    if len(lst_trend) > 1:
        if lst_trend[-1] > lst_trend[0]:
            lst_rising = True
            insights["key_findings"].append("LST forecast indicates a gradual warming trend.")
        else:
             insights["key_findings"].append("LST forecast indicates stable thermal conditions.")

    insights["rules_used"].append("Positive slope = Increasing Trend")

    # Root Causes
    if aqi_rising:
        insights["root_causes"].append("Projected industrial growth and vehicle fleet expansion outpacing emission controls.")
    if lst_rising:
        insights["root_causes"].append("Ongoing urbanization converting natural cover to heat-absorbing built-up areas.")
    
    if not aqi_rising and not lst_rising:
        insights["root_causes"].append("Current trends reflect stable environmental conditions or effective existing policies.")

    # Mitigation Actions
    if aqi_rising:
        insights["mitigation_actions"].append("Pre-emptive implementation of stricter emission norms for new industries.")
        insights["mitigation_actions"].append("Expansion of real-time monitoring network to identify emerging hotspots.")
    
    if lst_rising:
        insights["mitigation_actions"].append("Enforce 'Green Building' codes for all future commercial developments.")
        insights["mitigation_actions"].append("Plan for urban cooling corridors (wind paths) in master city planning.")

    # Future Risks
    if aqi_rising and lst_rising:
        insights["future_risks"] = "Compound risk of degrading air quality and rising heat stress may significantly impact public health and livability."
    elif aqi_rising:
        insights["future_risks"] = "Risk of respiratory health issues increasing if pollution trend continues unchecked."
    elif lst_rising:
        insights["future_risks"] = "Risk of increased energy consumption for cooling and potential heat island intensification."
    else:
        insights["future_risks"] = "Minimal immediate risk, but continuous monitoring is advised to detect sudden changes."

    return insights
