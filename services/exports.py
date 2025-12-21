import io
import pandas as pd
from datetime import datetime
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

def generate_lulc_csv(stats, city_name="", year=""):
    if not stats or "classes" not in stats:
        return None
    
    df_data = []
    for name, data in sorted(stats["classes"].items(), key=lambda x: x[1]["percentage"], reverse=True):
        df_data.append({
            "Class": name,
            "Area (km²)": data["area_sqkm"],
            "Percentage (%)": data["percentage"],
        })
    
    df = pd.DataFrame(df_data)
    
    csv_buffer = io.StringIO()
    csv_buffer.write(f"# LULC Statistics Report\n")
    csv_buffer.write(f"# Location: {city_name}\n")
    csv_buffer.write(f"# Year: {year}\n")
    csv_buffer.write(f"# Total Area: {stats.get('total_area_sqkm', 'N/A')} km²\n")
    csv_buffer.write(f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    csv_buffer.write("#\n")
    df.to_csv(csv_buffer, index=False)
    
    return csv_buffer.getvalue()

def generate_change_analysis_csv(stats1, stats2, year1, year2, city_name=""):
    if not stats1 or not stats2:
        return None
    
    classes1 = stats1.get("classes", {})
    classes2 = stats2.get("classes", {})
    all_classes = set(classes1.keys()) | set(classes2.keys())
    
    df_data = []
    for class_name in all_classes:
        data1 = classes1.get(class_name, {"percentage": 0, "area_sqkm": 0})
        data2 = classes2.get(class_name, {"percentage": 0, "area_sqkm": 0})
        
        df_data.append({
            "Class": class_name,
            f"{year1} Area (km²)": data1.get("area_sqkm", 0),
            f"{year2} Area (km²)": data2.get("area_sqkm", 0),
            "Change (km²)": data2.get("area_sqkm", 0) - data1.get("area_sqkm", 0),
            f"{year1} (%)": data1.get("percentage", 0),
            f"{year2} (%)": data2.get("percentage", 0),
            "Change (%)": data2.get("percentage", 0) - data1.get("percentage", 0),
        })
    
    df = pd.DataFrame(df_data)
    df = df.sort_values("Change (%)", key=abs, ascending=False)
    
    csv_buffer = io.StringIO()
    csv_buffer.write(f"# LULC Change Analysis Report\n")
    csv_buffer.write(f"# Location: {city_name}\n")
    csv_buffer.write(f"# Period: {year1} to {year2}\n")
    csv_buffer.write(f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    csv_buffer.write("#\n")
    df.to_csv(csv_buffer, index=False)
    
    return csv_buffer.getvalue()

def generate_aqi_csv(stats, pollutant, city_name="", date_range=""):
    if not stats:
        return None
    
    df_data = [{
        "Statistic": key.replace("_", " ").title(),
        "Value": f"{value:.4f}" if isinstance(value, float) else value,
        "Unit": stats.get("unit", "")
    } for key, value in stats.items() if key != "unit"]
    
    df = pd.DataFrame(df_data)
    
    csv_buffer = io.StringIO()
    csv_buffer.write(f"# AQI Statistics Report - {pollutant}\n")
    csv_buffer.write(f"# Location: {city_name}\n")
    csv_buffer.write(f"# Date Range: {date_range}\n")
    csv_buffer.write(f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    csv_buffer.write("#\n")
    df.to_csv(csv_buffer, index=False)
    
    return csv_buffer.getvalue()

def generate_time_series_csv(time_series, pollutant, city_name=""):
    if not time_series:
        return None
    
    df = pd.DataFrame(time_series)
    
    csv_buffer = io.StringIO()
    csv_buffer.write(f"# Time Series Data - {pollutant}\n")
    csv_buffer.write(f"# Location: {city_name}\n")
    csv_buffer.write(f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    csv_buffer.write("#\n")
    df.to_csv(csv_buffer, index=False)
    
    return csv_buffer.getvalue()


WHO_STANDARDS_2021 = {
    'PM2.5': {
        'name': 'Fine Particulate Matter',
        'daily': 15,
        'annual': 5,
        'unit': 'µg/m³',
        'comparable': True,
        'aqi_breakpoints': [(0, 12, 0, 50), (12.1, 35.4, 51, 100), (35.5, 55.4, 101, 150), 
                           (55.5, 150.4, 151, 200), (150.5, 250.4, 201, 300), (250.5, 500.4, 301, 500)]
    },
    'PM10': {
        'name': 'Coarse Particulate Matter',
        'daily': 45,
        'annual': 15,
        'unit': 'µg/m³',
        'comparable': True,
        'aqi_breakpoints': [(0, 54, 0, 50), (55, 154, 51, 100), (155, 254, 101, 150),
                           (255, 354, 151, 200), (355, 424, 201, 300), (425, 604, 301, 500)]
    },
    'NO2': {
        'name': 'Nitrogen Dioxide',
        'daily': 25,
        'annual': 10,
        'unit': 'µg/m³',
        'comparable': False,
        'note': 'Sentinel-5P provides column density (µmol/m²), not ground concentration'
    },
    'SO2': {
        'name': 'Sulfur Dioxide',
        'daily': 40,
        'unit': 'µg/m³',
        'comparable': False,
        'note': 'Sentinel-5P provides column density (µmol/m²), not ground concentration'
    },
    'CO': {
        'name': 'Carbon Monoxide',
        'daily': 4,
        'unit': 'mg/m³',
        'comparable': False,
        'note': 'Sentinel-5P provides column density (mmol/m²), not ground concentration'
    },
    'O3': {
        'name': 'Ozone',
        'daily': 100,
        'unit': 'µg/m³',
        'comparable': False,
        'note': 'Sentinel-5P provides column density (mmol/m²), not ground concentration'
    },
}

WHO_STANDARDS = WHO_STANDARDS_2021

NAAQS_INDIA = {
    'PM2.5': {'annual': 40, 'daily': 60, 'unit': 'µg/m³'},
    'PM10': {'annual': 60, 'daily': 100, 'unit': 'µg/m³'},
    'NO2': {'annual': 40, 'daily': 80, 'unit': 'µg/m³'},
    'SO2': {'annual': 50, 'daily': 80, 'unit': 'µg/m³'},
    'CO': {'8hr': 2, 'daily': 4, 'unit': 'mg/m³'},
    'O3': {'8hr': 100, 'daily': 180, 'unit': 'µg/m³'},
}

def calculate_sub_aqi(concentration, breakpoints):
    for bp_lo, bp_hi, aqi_lo, aqi_hi in breakpoints:
        if bp_lo <= concentration <= bp_hi:
            aqi = ((aqi_hi - aqi_lo) / (bp_hi - bp_lo)) * (concentration - bp_lo) + aqi_lo
            return round(aqi)
    return 500 if concentration > breakpoints[-1][1] else 0

def get_aqi_category(aqi):
    if aqi <= 50:
        return "Good", "#00e400"
    elif aqi <= 100:
        return "Satisfactory", "#ffff00"
    elif aqi <= 150:
        return "Moderate", "#ff7e00"
    elif aqi <= 200:
        return "Poor", "#ff0000"
    elif aqi <= 300:
        return "Very Poor", "#8f3f97"
    else:
        return "Severe", "#7e0023"

def calculate_aqi_compliance_score(pollutant_stats):
    if not pollutant_stats:
        return {'score': 0, 'rating': 'Unknown', 'details': [], 'aqi_index': 0, 'satellite_details': []}
    
    total_score = 0
    max_score = 0
    details = []
    satellite_details = []
    sub_aqis = []
    
    for pollutant, stats in pollutant_stats.items():
        mean_val = stats.get('mean', 0)
        if mean_val is None or mean_val == 0:
            continue
        
        if pollutant in WHO_STANDARDS_2021:
            std = WHO_STANDARDS_2021[pollutant]
            is_comparable = std.get('comparable', False)
            
            if is_comparable:
                who_limit = std.get('daily', std.get('annual', 0))
                
                if who_limit == 0:
                    continue
                
                ratio = mean_val / who_limit if who_limit else 1
                
                if ratio <= 0.5:
                    score = 100
                    status = "Excellent"
                elif ratio <= 1.0:
                    score = 80
                    status = "Good"
                elif ratio <= 1.5:
                    score = 60
                    status = "Moderate"
                elif ratio <= 2.0:
                    score = 40
                    status = "Poor"
                elif ratio <= 3.0:
                    score = 20
                    status = "Very Poor"
                else:
                    score = 0
                    status = "Severe"
                
                sub_aqi = 0
                if 'aqi_breakpoints' in std:
                    sub_aqi = calculate_sub_aqi(mean_val, std['aqi_breakpoints'])
                    sub_aqis.append(sub_aqi)
                
                total_score += score
                max_score += 100
                details.append({
                    'pollutant': pollutant,
                    'name': std['name'],
                    'measured': mean_val,
                    'who_limit': who_limit,
                    'ratio': ratio,
                    'score': score,
                    'sub_aqi': sub_aqi,
                    'status': status,
                    'unit': std.get('unit', '')
                })
            else:
                satellite_details.append({
                    'pollutant': pollutant,
                    'name': std.get('name', pollutant),
                    'measured': mean_val,
                    'unit': stats.get('unit', ''),
                    'note': std.get('note', 'Column density measurement')
                })
        else:
            satellite_details.append({
                'pollutant': pollutant,
                'name': pollutant,
                'measured': mean_val,
                'unit': stats.get('unit', ''),
                'note': 'Relative measurement (not comparable to WHO limits)'
            })
    
    overall_score = (total_score / max_score * 100) if max_score > 0 else 0
    overall_aqi = max(sub_aqis) if sub_aqis else 0
    aqi_category, aqi_color = get_aqi_category(overall_aqi)
    
    if max_score == 0:
        rating = "N/A - No comparable pollutants"
    elif overall_score >= 80:
        rating = "Good - Meets WHO Guidelines"
    elif overall_score >= 60:
        rating = "Moderate - Minor Exceedances"
    elif overall_score >= 40:
        rating = "Poor - Significant Exceedances"
    elif overall_score >= 20:
        rating = "Very Poor - Major Exceedances"
    else:
        rating = "Severe - Critical Pollution Levels"
    
    return {
        'score': round(overall_score, 1),
        'rating': rating,
        'details': details,
        'satellite_details': satellite_details,
        'aqi_index': overall_aqi,
        'aqi_category': aqi_category,
        'aqi_color': aqi_color
    }


def calculate_heat_vulnerability_score(lst_stats, uhi_stats=None, time_series=None, warming_trend=None):
    if not lst_stats:
        return {'score': 0, 'rating': 'Unknown', 'components': {}}
    
    components = {}
    total_weight = 0
    weighted_score = 0
    
    mean_temp = lst_stats.get('mean_celsius') or lst_stats.get('mean', 0)
    if mean_temp:
        if mean_temp >= 45:
            temp_score = 100
        elif mean_temp >= 40:
            temp_score = 80
        elif mean_temp >= 35:
            temp_score = 60
        elif mean_temp >= 30:
            temp_score = 40
        elif mean_temp >= 25:
            temp_score = 20
        else:
            temp_score = 0
        
        components['temperature'] = {
            'value': mean_temp,
            'score': temp_score,
            'weight': 30,
            'description': f"Mean LST: {mean_temp:.1f}°C"
        }
        weighted_score += temp_score * 30
        total_weight += 30
    
    if uhi_stats:
        uhi_intensity = uhi_stats.get('mean', 0) or 0
        if uhi_intensity >= 8:
            uhi_score = 100
        elif uhi_intensity >= 6:
            uhi_score = 80
        elif uhi_intensity >= 4:
            uhi_score = 60
        elif uhi_intensity >= 2:
            uhi_score = 40
        elif uhi_intensity >= 1:
            uhi_score = 20
        else:
            uhi_score = 0
        
        components['uhi'] = {
            'value': uhi_intensity,
            'score': uhi_score,
            'weight': 25,
            'description': f"UHI Intensity: {uhi_intensity:.1f}°C"
        }
        weighted_score += uhi_score * 25
        total_weight += 25
    
    max_temp = lst_stats.get('max_celsius') or lst_stats.get('max', 0)
    if max_temp and mean_temp:
        temp_range = max_temp - mean_temp
        if temp_range >= 15:
            range_score = 80
        elif temp_range >= 10:
            range_score = 60
        elif temp_range >= 5:
            range_score = 40
        else:
            range_score = 20
        
        components['variability'] = {
            'value': temp_range,
            'score': range_score,
            'weight': 15,
            'description': f"Temp Variability: {temp_range:.1f}°C"
        }
        weighted_score += range_score * 15
        total_weight += 15
    
    if warming_trend:
        slope = warming_trend.get('slope_per_year', 0) or warming_trend.get('slope', 0)
        if slope >= 0.5:
            trend_score = 100
        elif slope >= 0.3:
            trend_score = 80
        elif slope >= 0.1:
            trend_score = 60
        elif slope >= 0:
            trend_score = 40
        else:
            trend_score = 20
        
        components['warming_trend'] = {
            'value': slope,
            'score': trend_score,
            'weight': 20,
            'description': f"Warming: {slope:.3f}°C/year"
        }
        weighted_score += trend_score * 20
        total_weight += 20
    
    if time_series and len(time_series) > 5:
        temps = [d.get('mean_lst', 0) for d in time_series if d.get('mean_lst')]
        if temps:
            extreme_days = sum(1 for t in temps if t and t >= 40)
            extreme_pct = (extreme_days / len(temps)) * 100
            if extreme_pct >= 30:
                extreme_score = 100
            elif extreme_pct >= 20:
                extreme_score = 80
            elif extreme_pct >= 10:
                extreme_score = 60
            elif extreme_pct >= 5:
                extreme_score = 40
            else:
                extreme_score = 20
            
            components['extreme_heat'] = {
                'value': extreme_pct,
                'score': extreme_score,
                'weight': 10,
                'description': f"Extreme Heat Days: {extreme_pct:.1f}%"
            }
            weighted_score += extreme_score * 10
            total_weight += 10
    
    final_score = (weighted_score / total_weight) if total_weight > 0 else 0
    
    if final_score >= 80:
        rating = "Very High Vulnerability"
        color = "#d32f2f"
    elif final_score >= 60:
        rating = "High Vulnerability"
        color = "#f57c00"
    elif final_score >= 40:
        rating = "Moderate Vulnerability"
        color = "#fbc02d"
    elif final_score >= 20:
        rating = "Low Vulnerability"
        color = "#388e3c"
    else:
        rating = "Very Low Vulnerability"
        color = "#1976d2"
    
    return {
        'score': round(final_score, 1),
        'rating': rating,
        'color': color,
        'components': components
    }


def calculate_land_sustainability_score(lulc_stats, change_stats=None):
    if not lulc_stats or 'classes' not in lulc_stats:
        return {'score': 0, 'rating': 'Unknown', 'components': {}}
    
    classes = lulc_stats.get('classes', {})
    components = {}
    total_weight = 0
    weighted_score = 0
    
    green_classes = ['Trees', 'Grass', 'Crops', 'Flooded Vegetation', 'Shrub & Scrub']
    green_pct = sum(classes.get(c, {}).get('percentage', 0) for c in green_classes)
    
    if green_pct >= 50:
        green_score = 100
    elif green_pct >= 40:
        green_score = 80
    elif green_pct >= 30:
        green_score = 60
    elif green_pct >= 20:
        green_score = 40
    elif green_pct >= 10:
        green_score = 20
    else:
        green_score = 0
    
    components['green_cover'] = {
        'value': green_pct,
        'score': green_score,
        'weight': 35,
        'description': f"Green Cover: {green_pct:.1f}%"
    }
    weighted_score += green_score * 35
    total_weight += 35
    
    built_pct = classes.get('Built Area', {}).get('percentage', 0)
    bare_pct = classes.get('Bare Ground', {}).get('percentage', 0)
    impervious_pct = built_pct + bare_pct
    
    if impervious_pct <= 20:
        impervious_score = 100
    elif impervious_pct <= 30:
        impervious_score = 80
    elif impervious_pct <= 40:
        impervious_score = 60
    elif impervious_pct <= 50:
        impervious_score = 40
    elif impervious_pct <= 60:
        impervious_score = 20
    else:
        impervious_score = 0
    
    components['impervious'] = {
        'value': impervious_pct,
        'score': impervious_score,
        'weight': 25,
        'description': f"Impervious Surface: {impervious_pct:.1f}%"
    }
    weighted_score += impervious_score * 25
    total_weight += 25
    
    water_pct = classes.get('Water', {}).get('percentage', 0)
    if water_pct >= 10:
        water_score = 100
    elif water_pct >= 5:
        water_score = 80
    elif water_pct >= 2:
        water_score = 60
    elif water_pct >= 1:
        water_score = 40
    else:
        water_score = 20
    
    components['water'] = {
        'value': water_pct,
        'score': water_score,
        'weight': 15,
        'description': f"Water Bodies: {water_pct:.1f}%"
    }
    weighted_score += water_score * 15
    total_weight += 15
    
    num_classes = sum(1 for c, d in classes.items() if d.get('percentage', 0) > 1)
    if num_classes >= 7:
        diversity_score = 100
    elif num_classes >= 5:
        diversity_score = 80
    elif num_classes >= 4:
        diversity_score = 60
    elif num_classes >= 3:
        diversity_score = 40
    else:
        diversity_score = 20
    
    components['diversity'] = {
        'value': num_classes,
        'score': diversity_score,
        'weight': 15,
        'description': f"Land Diversity: {num_classes} classes"
    }
    weighted_score += diversity_score * 15
    total_weight += 15
    
    if change_stats:
        tree_change = change_stats.get('Trees', {}).get('change', 0)
        if tree_change >= 5:
            change_score = 100
        elif tree_change >= 0:
            change_score = 70
        elif tree_change >= -5:
            change_score = 40
        else:
            change_score = 10
        
        components['vegetation_trend'] = {
            'value': tree_change,
            'score': change_score,
            'weight': 10,
            'description': f"Tree Cover Change: {tree_change:+.1f}%"
        }
        weighted_score += change_score * 10
        total_weight += 10
    
    final_score = (weighted_score / total_weight) if total_weight > 0 else 0
    
    if final_score >= 80:
        rating = "Excellent Sustainability"
        color = "#1976d2"
    elif final_score >= 60:
        rating = "Good Sustainability"
        color = "#388e3c"
    elif final_score >= 40:
        rating = "Moderate Sustainability"
        color = "#fbc02d"
    elif final_score >= 20:
        rating = "Poor Sustainability"
        color = "#f57c00"
    else:
        rating = "Critical - Needs Intervention"
        color = "#d32f2f"
    
    return {
        'score': round(final_score, 1),
        'rating': rating,
        'color': color,
        'components': components
    }


def _create_chart_image(chart_type, data, title, width=400, height=250):
    if chart_type == 'bar' and isinstance(data, dict) and len(data) > 5:
        height = max(250, len(data) * 30)
    
    fig, ax = plt.subplots(figsize=(width/100, height/100), dpi=100)
    
    if chart_type == 'pie':
        labels = list(data.keys())
        values = [d.get('percentage', 0) for d in data.values()]
        pie_colors = plt.cm.Set3(np.linspace(0, 1, len(labels)))
        
        wedges, texts, autotexts = ax.pie(values, autopct='%1.1f%%', colors=pie_colors, startangle=90, pctdistance=0.75)
        
        for autotext in autotexts:
            autotext.set_fontsize(7)
        
        ax.legend(wedges, labels, loc='center left', bbox_to_anchor=(1, 0.5), fontsize=7)
        ax.set_title(title, fontsize=10, fontweight='bold')
    
    elif chart_type == 'bar':
        labels = list(data.keys())
        values = [d.get('percentage', 0) if isinstance(d, dict) else d for d in data.values()]
        bar_colors = plt.cm.viridis(np.linspace(0.2, 0.8, len(labels)))
        
        if len(labels) > 5:
            ax.barh(range(len(labels)), values, color=bar_colors)
            ax.set_yticks(range(len(labels)))
            ax.set_yticklabels(labels, fontsize=8)
            ax.set_xlabel('Percentage (%)')
            ax.invert_yaxis()
        else:
            ax.bar(range(len(labels)), values, color=bar_colors)
            ax.set_xticks(range(len(labels)))
            ax.set_xticklabels(labels, rotation=30, ha='right', fontsize=8)
            ax.set_ylabel('Percentage (%)')
        ax.set_title(title, fontsize=10, fontweight='bold')
    
    elif chart_type == 'line':
        if isinstance(data, list):
            dates = [d.get('date', d.get('year', '')) for d in data]
            values = [d.get('value', d.get('mean_lst', d.get('mean', 0))) for d in data]
            ax.plot(range(len(dates)), values, marker='o', linewidth=2, markersize=4)
            ax.set_xticks(range(0, len(dates), max(1, len(dates)//6)))
            ax.set_xticklabels([dates[i] for i in range(0, len(dates), max(1, len(dates)//6))], 
                              rotation=45, ha='right', fontsize=8)
            ax.set_ylabel('Value')
            ax.set_title(title, fontsize=10, fontweight='bold')
            ax.grid(True, alpha=0.3)
    
    elif chart_type == 'gauge':
        score = data.get('score', 0)
        colors_gauge = ['#d32f2f', '#f57c00', '#fbc02d', '#388e3c', '#1976d2']
        sections = [20, 40, 60, 80, 100]
        
        theta = np.linspace(np.pi, 0, 100)
        for i, (end, color) in enumerate(zip(sections, colors_gauge)):
            start = sections[i-1] if i > 0 else 0
            mask = (np.linspace(0, 100, 100) >= start) & (np.linspace(0, 100, 100) < end)
            ax.fill_between(theta[mask], 0.6, 1, color=color, alpha=0.7)
        
        needle_angle = np.pi - (score / 100) * np.pi
        ax.arrow(0, 0, 0.5 * np.cos(needle_angle), 0.5 * np.sin(needle_angle),
                head_width=0.05, head_length=0.05, fc='black', ec='black')
        ax.add_patch(plt.Circle((0, 0), 0.08, color='black'))
        ax.set_xlim(-1.2, 1.2)
        ax.set_ylim(-0.2, 1.2)
        ax.set_aspect('equal')
        ax.axis('off')
        ax.text(0, -0.1, f"{score:.0f}", fontsize=20, ha='center', fontweight='bold')
        ax.set_title(title, fontsize=10, fontweight='bold', y=0.95)
    
    plt.tight_layout()
    
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight', dpi=100)
    plt.close(fig)
    buf.seek(0)
    
    return buf



def _add_insights_section(elements, styles_dict, insights):
    """
    Helper function to add the insights section to the PDF report.
    """
    if not insights:
        return

    from reportlab.lib import colors
    from reportlab.platypus import Paragraph, Spacer
    from reportlab.lib.styles import ParagraphStyle
    
    heading_style = styles_dict.get('Heading')
    body_style = styles_dict.get('Body')
    
    # Create specific styles for insights
    subheading_style = ParagraphStyle(
        'SubHeading', 
        parent=heading_style, 
        fontSize=12, 
        spaceBefore=10, 
        spaceAfter=5,
        textColor=colors.HexColor('#455a64')
    )
    
    bullet_style = ParagraphStyle(
        'Bullet',
        parent=body_style,
        leftIndent=15,
        spaceAfter=3,
        bulletIndent=5
    )
    
    elements.append(Spacer(1, 20))
    elements.append(Paragraph("Actionable Insights & Recommendations", heading_style))
    elements.append(Spacer(1, 10))
    
    # (a) Key Findings
    if insights.get("key_findings"):
        elements.append(Paragraph("Key Environmental Findings", subheading_style))
        for item in insights["key_findings"]:
             elements.append(Paragraph(f"• {item}", bullet_style))
    
    # (b) Root Causes
    if insights.get("root_causes"):
        elements.append(Paragraph("Root Cause Analysis", subheading_style))
        for item in insights["root_causes"]:
             elements.append(Paragraph(f"• {item}", bullet_style))
    
    # (c) Mitigation Actions
    if insights.get("mitigation_actions"):
        elements.append(Paragraph("Recommended Mitigation Actions", subheading_style))
        for item in insights["mitigation_actions"]:
             elements.append(Paragraph(f"• {item}", bullet_style))
    
    # (d) Future Risks
    if insights.get("future_risks"):
        elements.append(Paragraph("Future Risk Assessment", subheading_style))
        elements.append(Paragraph(insights["future_risks"], body_style))
    
    # (e) Rules Used
    if insights.get("rules_used"):
        elements.append(Spacer(1, 10))
        elements.append(Paragraph("Analysis Basis (Rules & Thresholds)", subheading_style))
        for item in insights["rules_used"]:
             elements.append(Paragraph(f"• {item}", bullet_style))
    
    elements.append(Spacer(1, 20))


def generate_lulc_pdf_report(report_data):
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch, cm
        from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
        
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=1*cm, bottomMargin=1*cm)
        styles = getSampleStyleSheet()
        elements = []
        
        title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=22, 
                                      spaceAfter=20, alignment=TA_CENTER, textColor=colors.HexColor('#1565c0'))
        subtitle_style = ParagraphStyle('Subtitle', parent=styles['Heading2'], fontSize=14, 
                                         spaceAfter=10, alignment=TA_CENTER, textColor=colors.grey)
        heading_style = ParagraphStyle('Heading', parent=styles['Heading2'], fontSize=14, 
                                        spaceBefore=15, spaceAfter=10, textColor=colors.HexColor('#2e7d32'))
        body_style = ParagraphStyle('Body', parent=styles['Normal'], fontSize=10, 
                                     spaceAfter=8, alignment=TA_JUSTIFY)
        note_style = ParagraphStyle('Note', parent=styles['Normal'], fontSize=8, 
                                     textColor=colors.grey, alignment=TA_LEFT, leftIndent=20)
        
        elements.append(Paragraph("Land Use Land Cover Analysis Report", title_style))
        elements.append(Paragraph("India GIS & Remote Sensing Portal", subtitle_style))
        elements.append(Spacer(1, 20))
        
        city = report_data.get('city_name', 'Unknown')
        state = report_data.get('state', '')
        year = report_data.get('year', '')
        satellite = report_data.get('satellite', '')
        total_area = report_data.get('total_area', 0)
        date_range = report_data.get('date_range', '')
        
        info_data = [
            ['Location', f"{city}, {state}" if state else city],
            ['Analysis Period', date_range or str(year)],
            ['Satellite Source', satellite],
            ['Total Area', f"{total_area:.2f} km²" if total_area else 'N/A'],
            ['Report Generated', datetime.now().strftime('%Y-%m-%d %H:%M:%S')]
        ]
        info_table = Table(info_data, colWidths=[5*cm, 12*cm])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e3f2fd')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('PADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elements.append(info_table)
        elements.append(Spacer(1, 25))
        
        sustainability = report_data.get('sustainability_score', {})
        if sustainability:
            elements.append(Paragraph("Land Sustainability Score", heading_style))
            elements.append(Spacer(1, 10))
            
            score = sustainability.get('score', 0)
            rating = sustainability.get('rating', 'Unknown')
            score_color = sustainability.get('color', '#666666')
            
            score_table_data = [[
                Paragraph(f'<font size="24" color="{score_color}"><b>{score:.0f}</b></font><font size="12">/100</font>', 
                         ParagraphStyle('ScoreStyle', alignment=TA_CENTER)),
                Paragraph(f'<font size="11" color="{score_color}"><b>{rating}</b></font>',
                         ParagraphStyle('RatingStyle', alignment=TA_CENTER))
            ]]
            score_display = Table(score_table_data, colWidths=[4*cm, 10*cm])
            score_display.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('PADDING', (0, 0), (-1, -1), 10),
            ]))
            elements.append(score_display)
            elements.append(Spacer(1, 15))
            
            components = sustainability.get('components', {})
            if components:
                comp_data = [['Component', 'Value', 'Score', 'Weight']]
                for name, comp in components.items():
                    comp_data.append([
                        name.replace('_', ' ').title(),
                        comp.get('description', ''),
                        f"{comp.get('score', 0):.0f}/100",
                        f"{comp.get('weight', 0)}%"
                    ])
                
                comp_table = Table(comp_data, colWidths=[4*cm, 5*cm, 2.5*cm, 2*cm])
                comp_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4caf50')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('PADDING', (0, 0), (-1, -1), 6),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('ALIGN', (2, 0), (-1, -1), 'CENTER'),
                ]))
                elements.append(comp_table)
            
            elements.append(Spacer(1, 15))
            method_note = """<b>Methodology:</b> The Land Sustainability Score is calculated using weighted components:
            Green Cover (35%) - Percentage of vegetation including trees, grass, and crops;
            Impervious Surface (25%) - Built-up and bare ground areas;
            Water Bodies (15%) - Presence of water features;
            Land Diversity (15%) - Number of distinct land cover classes;
            Vegetation Trend (10%) - Change in tree cover if time-series available.
            Scores range from 0-100, with higher scores indicating better environmental sustainability."""
            elements.append(Paragraph(method_note, note_style))
            elements.append(Spacer(1, 30))
        
        stats = report_data.get('stats', {})
        if stats:
            elements.append(Paragraph("Land Cover Statistics", heading_style))
            
            table_data = [['Land Cover Class', 'Area (km²)', 'Percentage (%)']]
            for name, data in sorted(stats.items(), key=lambda x: x[1].get('percentage', 0), reverse=True):
                if isinstance(data, dict):
                    table_data.append([
                        name,
                        f"{data.get('area_sqkm', 0):.2f}",
                        f"{data.get('percentage', 0):.1f}%"
                    ])
            
            lulc_table = Table(table_data, colWidths=[6*cm, 3.5*cm, 3.5*cm])
            lulc_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1565c0')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('PADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
            ]))
            elements.append(lulc_table)
            elements.append(Spacer(1, 15))
            
            if len(stats) > 0:
                try:
                    chart_buf = _create_chart_image('pie', stats, 'Land Cover Distribution', 400, 280)
                    elements.append(Image(chart_buf, width=5*inch, height=2.8*inch))
                except Exception:
                    pass
            elements.append(Spacer(1, 20))
        
        indices = report_data.get('indices', {})
        if indices:
            elements.append(Paragraph("Vegetation Indices Summary", heading_style))
            
            idx_data = [['Index', 'Mean Value', 'Description']]
            idx_descriptions = {
                'NDVI': 'Vegetation health and density',
                'NDWI': 'Water content in vegetation',
                'NDBI': 'Built-up area intensity',
                'EVI': 'Enhanced vegetation monitoring',
                'SAVI': 'Soil-adjusted vegetation'
            }
            for idx_name, idx_val in indices.items():
                if idx_val is not None:
                    idx_data.append([
                        idx_name,
                        f"{idx_val:.4f}",
                        idx_descriptions.get(idx_name, '')
                    ])
            
            if len(idx_data) > 1:
                idx_table = Table(idx_data, colWidths=[3*cm, 3*cm, 11*cm])
                idx_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#8bc34a')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('PADDING', (0, 0), (-1, -1), 8),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('ALIGN', (1, 0), (1, -1), 'CENTER'),
                ]))
                elements.append(idx_table)
                elements.append(Spacer(1, 20))
        
        change_data = report_data.get('change_analysis', {})
        if change_data:
            elements.append(PageBreak())
            elements.append(Paragraph("Land Cover Change Analysis", heading_style))
            
            year1 = change_data.get('year1', '')
            year2 = change_data.get('year2', '')
            changes = change_data.get('changes', {})
            
            elements.append(Paragraph(f"Comparison: {year1} to {year2}", body_style))
            
            change_table_data = [['Class', f'{year1} (%)', f'{year2} (%)', 'Change (%)']]
            for class_name, data in sorted(changes.items(), key=lambda x: abs(x[1].get('change', 0)), reverse=True):
                change_val = data.get('change', 0)
                change_str = f"+{change_val:.1f}" if change_val > 0 else f"{change_val:.1f}"
                change_table_data.append([
                    class_name,
                    f"{data.get('year1_pct', 0):.1f}",
                    f"{data.get('year2_pct', 0):.1f}",
                    change_str
                ])
            
            change_table = Table(change_table_data, colWidths=[5*cm, 3*cm, 3*cm, 3*cm])
            change_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#ff9800')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('PADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
            ]))
            change_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#ff9800')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('PADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
            ]))
            elements.append(change_table)
        
        # Add Insights Section
        insights = report_data.get('insights')
        if insights:
            elements.append(PageBreak())
            styles_dict = {'Heading': heading_style, 'Body': body_style}
            _add_insights_section(elements, styles_dict, insights)
            
        elements.append(Spacer(1, 30))
        elements.append(Paragraph("—" * 40, styles['Normal']))
        elements.append(Paragraph("Generated by India GIS & Remote Sensing Portal", note_style))
        elements.append(Paragraph("Data Source: Google Earth Engine - Dynamic World, Sentinel-2, Landsat", note_style))
        
        doc.build(elements)
        pdf_data = buffer.getvalue()
        buffer.close()
        return pdf_data
        
    except Exception as e:
        print(f"Error generating LULC PDF: {e}")
        return None


def generate_aqi_pdf_report(report_data):
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch, cm
        from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
        
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=1*cm, bottomMargin=1*cm)
        styles = getSampleStyleSheet()
        elements = []
        
        title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=22, 
                                      spaceAfter=20, alignment=TA_CENTER, textColor=colors.HexColor('#1565c0'))
        subtitle_style = ParagraphStyle('Subtitle', parent=styles['Heading2'], fontSize=14, 
                                         spaceAfter=10, alignment=TA_CENTER, textColor=colors.grey)
        heading_style = ParagraphStyle('Heading', parent=styles['Heading2'], fontSize=14, 
                                        spaceBefore=15, spaceAfter=10, textColor=colors.HexColor('#0277bd'))
        body_style = ParagraphStyle('Body', parent=styles['Normal'], fontSize=10, 
                                     spaceAfter=8, alignment=TA_JUSTIFY)
        note_style = ParagraphStyle('Note', parent=styles['Normal'], fontSize=8, 
                                     textColor=colors.grey, alignment=TA_LEFT, leftIndent=20)
        
        elements.append(Paragraph("Air Quality Analysis Report", title_style))
        elements.append(Paragraph("India GIS & Remote Sensing Portal", subtitle_style))
        elements.append(Spacer(1, 20))
        
        city = report_data.get('city_name', 'Unknown')
        state = report_data.get('state', '')
        date_range = report_data.get('date_range', '')
        pollutants = report_data.get('pollutants', [])
        
        info_data = [
            ['Location', f"{city}, {state}" if state else city],
            ['Analysis Period', date_range],
            ['Pollutants Analyzed', ', '.join(pollutants) if pollutants else 'N/A'],
            ['Report Generated', datetime.now().strftime('%Y-%m-%d %H:%M:%S')]
        ]
        info_table = Table(info_data, colWidths=[4*cm, 9*cm])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e1f5fe')),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('PADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        elements.append(info_table)
        elements.append(Spacer(1, 20))
        
        compliance = report_data.get('compliance_score', {})
        if compliance:
            elements.append(Paragraph("Air Quality Index & Compliance", heading_style))
            
            aqi_index = compliance.get('aqi_index', 0)
            aqi_category = compliance.get('aqi_category', 'Unknown')
            aqi_color = compliance.get('aqi_color', '#888888')
            score = compliance.get('score', 0)
            rating = compliance.get('rating', 'Unknown')
            
            if score >= 80:
                score_color = '#388e3c'
            elif score >= 60:
                score_color = '#fbc02d'
            elif score >= 40:
                score_color = '#f57c00'
            else:
                score_color = '#d32f2f'
            
            aqi_score_data = [
                ['AQI Index', 'AQI Category', 'WHO Compliance', 'Rating'],
                [str(aqi_index), aqi_category, f"{score:.0f}/100", rating]
            ]
            aqi_score_table = Table(aqi_score_data, colWidths=[2.5*cm, 3.5*cm, 3.5*cm, 6.5*cm])
            aqi_score_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1565c0')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('FONTSIZE', (0, 1), (0, 1), 14),
                ('FONTSIZE', (1, 1), (-1, 1), 9),
                ('TEXTCOLOR', (0, 1), (0, 1), colors.HexColor(aqi_color)),
                ('TEXTCOLOR', (2, 1), (2, 1), colors.HexColor(score_color)),
                ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
                ('PADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            elements.append(aqi_score_table)
            elements.append(Spacer(1, 15))
            
            aqi_legend = """<b>AQI Categories:</b> Good (0-50), Satisfactory (51-100), Moderate (101-150), 
            Poor (151-200), Very Poor (201-300), Severe (301-500)"""
            elements.append(Paragraph(aqi_legend, note_style))
            elements.append(Spacer(1, 15))
            
            details = compliance.get('details', [])
            if details:
                elements.append(Paragraph("Pollutant-wise WHO Comparison (2021 Guidelines)", body_style))
                
                comp_data = [['Pollutant', 'Name', 'Measured', 'WHO Limit', 'Sub-AQI', 'Status']]
                for d in details:
                    ratio = d.get('ratio', 0)
                    status = d.get('status', 'Unknown')
                    sub_aqi = d.get('sub_aqi', 0)
                    unit = d.get('unit', '')
                    comp_data.append([
                        d.get('pollutant', ''),
                        d.get('name', ''),
                        f"{d.get('measured', 0):.2f} {unit}",
                        f"{d.get('who_limit', 0)} {unit}",
                        str(sub_aqi),
                        status
                    ])
                
                comp_table = Table(comp_data, colWidths=[1.8*cm, 4*cm, 3.2*cm, 2.8*cm, 1.8*cm, 2.5*cm])
                comp_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0288d1')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 8),
                    ('PADDING', (0, 0), (-1, -1), 5),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('ALIGN', (2, 0), (-1, -1), 'CENTER'),
                ]))
                elements.append(comp_table)
            
            elements.append(Spacer(1, 10))
            method_note = """<b>Methodology:</b> AQI is calculated using standard breakpoints for PM2.5 and PM10. 
            The overall AQI is the highest sub-index. WHO Compliance Score (0-100) compares ground-level concentrations 
            against WHO 2021 Guidelines: Excellent (≤50% of limit), Good (≤100%), Moderate (≤150%), 
            Poor (≤200%), Very Poor (≤300%), Severe (>300%)."""
            elements.append(Paragraph(method_note, note_style))
            elements.append(Spacer(1, 15))
            
            satellite_details = compliance.get('satellite_details', [])
            if satellite_details:
                elements.append(Paragraph("Satellite-based Pollutant Measurements", body_style))
                sat_note = """<i>Note: The following pollutants are measured as atmospheric column density by Sentinel-5P 
                satellite and cannot be directly compared to WHO ground-level concentration limits.</i>"""
                elements.append(Paragraph(sat_note, note_style))
                elements.append(Spacer(1, 5))
                
                sat_data = [['Pollutant', 'Name', 'Measured Value', 'Unit']]
                for d in satellite_details:
                    sat_data.append([
                        d.get('pollutant', ''),
                        d.get('name', ''),
                        f"{d.get('measured', 0):.4f}",
                        d.get('unit', '')
                    ])
                
                sat_table = Table(sat_data, colWidths=[2.5*cm, 5*cm, 4*cm, 4*cm])
                sat_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#78909c')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('PADDING', (0, 0), (-1, -1), 5),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('ALIGN', (2, 0), (-1, -1), 'CENTER'),
                ]))
                elements.append(sat_table)
                elements.append(Spacer(1, 15))
        
        pollutant_stats = report_data.get('pollutant_stats', {})
        if pollutant_stats:
            elements.append(Paragraph("Pollutant Statistics", heading_style))
            
            for pollutant, stats in pollutant_stats.items():
                elements.append(Paragraph(f"<b>{pollutant}</b>", body_style))
                
                stat_data = [['Metric', 'Value', 'Unit']]
                unit = stats.get('unit', '')
                for key, val in stats.items():
                    if key != 'unit' and val is not None:
                        stat_data.append([
                            key.replace('_', ' ').title(),
                            f"{val:.6f}" if isinstance(val, float) else str(val),
                            unit
                        ])
                
                stat_table = Table(stat_data, colWidths=[4*cm, 4*cm, 3*cm])
                stat_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4fc3f7')),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('PADDING', (0, 0), (-1, -1), 5),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
                ]))
                elements.append(stat_table)
                elements.append(Spacer(1, 10))
        
        time_series = report_data.get('time_series', {})
        if time_series:
            elements.append(PageBreak())
            elements.append(Paragraph("Time Series Analysis", heading_style))
            
            for pollutant, ts_data in time_series.items():
                if ts_data and len(ts_data) > 0:
                    elements.append(Paragraph(f"<b>{pollutant} Temporal Trend</b>", body_style))
                    
                    try:
                        chart_buf = _create_chart_image('line', ts_data, f'{pollutant} Time Series', 450, 200)
                        elements.append(Image(chart_buf, width=4.5*inch, height=2*inch))
                    except Exception:
                        pass
                    
                    values = [d.get('value', d.get('mean', 0)) for d in ts_data if d.get('value') or d.get('mean')]
                    if values:
                        summary_text = f"Period Average: {np.mean(values):.4f} | Max: {np.max(values):.4f} | Min: {np.min(values):.4f}"
                        elements.append(Paragraph(summary_text, note_style))
                    elements.append(Spacer(1, 15))
        
        hotspots = report_data.get('hotspots', {})
        if hotspots:
            elements.append(Paragraph("Hotspot Analysis", heading_style))
            elements.append(Paragraph(
                "Areas where pollutant concentrations exceed the mean + 1.5 standard deviations are identified as hotspots, "
                "indicating localized high pollution zones that may require targeted interventions.",
                body_style
            ))
        

        
        # Add Insights Section
        insights = report_data.get('insights')
        if insights:
            elements.append(PageBreak())
            styles_dict = {'Heading': heading_style, 'Body': body_style}
            _add_insights_section(elements, styles_dict, insights)

        elements.append(Spacer(1, 30))
        elements.append(Paragraph("—" * 40, styles['Normal']))
        elements.append(Paragraph("Generated by India GIS & Remote Sensing Portal", note_style))
        elements.append(Paragraph("Data Source: Sentinel-5P TROPOMI via Google Earth Engine", note_style))
        elements.append(Paragraph("Reference Standards: WHO Air Quality Guidelines 2021", note_style))
        
        doc.build(elements)
        pdf_data = buffer.getvalue()
        buffer.close()
        return pdf_data
        
    except Exception as e:
        print(f"Error generating AQI PDF: {e}")
        return None


def generate_urban_heat_pdf_report(report_data):
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch, cm
        from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
        
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=1*cm, bottomMargin=1*cm)
        styles = getSampleStyleSheet()
        elements = []
        
        title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=22, 
                                      spaceAfter=20, alignment=TA_CENTER, textColor=colors.HexColor('#d32f2f'))
        subtitle_style = ParagraphStyle('Subtitle', parent=styles['Heading2'], fontSize=14, 
                                         spaceAfter=10, alignment=TA_CENTER, textColor=colors.grey)
        heading_style = ParagraphStyle('Heading', parent=styles['Heading2'], fontSize=14, 
                                        spaceBefore=15, spaceAfter=10, textColor=colors.HexColor('#e65100'))
        body_style = ParagraphStyle('Body', parent=styles['Normal'], fontSize=10, 
                                     spaceAfter=8, alignment=TA_JUSTIFY)
        note_style = ParagraphStyle('Note', parent=styles['Normal'], fontSize=8, 
                                     textColor=colors.grey, alignment=TA_LEFT, leftIndent=20)
        
        elements.append(Paragraph("Urban Heat & Climate Analysis Report", title_style))
        elements.append(Paragraph("India GIS & Remote Sensing Portal", subtitle_style))
        elements.append(Spacer(1, 20))
        
        city = report_data.get('city_name', 'Unknown')
        state = report_data.get('state', '')
        date_range = report_data.get('date_range', '')
        time_of_day = report_data.get('time_of_day', 'Day')
        data_source = report_data.get('data_source', 'MODIS')
        
        info_data = [
            ['Location', f"{city}, {state}" if state else city],
            ['Analysis Period', date_range],
            ['Time of Day', f"{time_of_day}time"],
            ['Data Source', data_source],
            ['Report Generated', datetime.now().strftime('%Y-%m-%d %H:%M:%S')]
        ]
        info_table = Table(info_data, colWidths=[4*cm, 9*cm])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#ffebee')),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('PADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        elements.append(info_table)
        elements.append(Spacer(1, 20))
        
        vulnerability = report_data.get('vulnerability_score', {})
        if vulnerability:
            elements.append(Paragraph("Heat Vulnerability Score", heading_style))
            
            score = vulnerability.get('score', 0)
            rating = vulnerability.get('rating', 'Unknown')
            score_color = vulnerability.get('color', '#666666')
            
            score_text = f"""
            <para align="center">
            <font size="28" color="{score_color}"><b>{score:.0f}</b></font><font size="14">/100</font><br/>
            <font size="12" color="{score_color}"><b>{rating}</b></font>
            </para>
            """
            elements.append(Paragraph(score_text, styles['Normal']))
            elements.append(Spacer(1, 15))
            
            components = vulnerability.get('components', {})
            if components:
                elements.append(Paragraph("Vulnerability Components", body_style))
                
                comp_data = [['Component', 'Value', 'Score', 'Weight']]
                for name, comp in components.items():
                    comp_data.append([
                        name.replace('_', ' ').title(),
                        comp.get('description', ''),
                        f"{comp.get('score', 0):.0f}/100",
                        f"{comp.get('weight', 0)}%"
                    ])
                
                comp_table = Table(comp_data, colWidths=[3.5*cm, 5*cm, 2.5*cm, 2*cm])
                comp_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#ff5722')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('PADDING', (0, 0), (-1, -1), 6),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('ALIGN', (2, 0), (-1, -1), 'CENTER'),
                ]))
                elements.append(comp_table)
            
            elements.append(Spacer(1, 10))
            method_note = """<b>Methodology:</b> The Heat Vulnerability Score is calculated using weighted components:
            Temperature (30%) - Mean Land Surface Temperature where >45°C = highest risk;
            UHI Intensity (25%) - Urban Heat Island effect where >8°C difference = highest risk;
            Temperature Variability (15%) - Range between mean and max temperature;
            Warming Trend (20%) - Rate of temperature increase per year;
            Extreme Heat Days (10%) - Percentage of days exceeding 40°C.
            Scores range from 0-100, with higher scores indicating greater heat vulnerability and risk."""
            elements.append(Paragraph(method_note, note_style))
            elements.append(Spacer(1, 15))
        
        lst_stats = report_data.get('lst_stats', {})
        if lst_stats:
            elements.append(Paragraph("Land Surface Temperature Statistics", heading_style))
            
            time_of_day = report_data.get('time_of_day', 'Day')
            band_prefix = f"LST_{time_of_day}"
            
            stat_data = [['Metric', 'Value']]
            stat_mappings = [
                (f'{band_prefix}_mean', 'Mean Temperature'),
                (f'{band_prefix}_min', 'Minimum Temperature'),
                (f'{band_prefix}_max', 'Maximum Temperature'),
                (f'{band_prefix}_stdDev', 'Standard Deviation'),
                (f'{band_prefix}_p50', 'Median Temperature'),
                (f'{band_prefix}_p10', '10th Percentile'),
                (f'{band_prefix}_p90', '90th Percentile'),
            ]
            
            for key, label in stat_mappings:
                if key in lst_stats and lst_stats[key] is not None:
                    val = lst_stats[key]
                    stat_data.append([label, f"{val:.1f}°C"])
            
            if len(stat_data) > 1:
                stat_table = Table(stat_data, colWidths=[6*cm, 4*cm])
                stat_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#ff7043')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('PADDING', (0, 0), (-1, -1), 8),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
                ]))
                elements.append(stat_table)
                elements.append(Spacer(1, 15))
        
        uhi_stats = report_data.get('uhi_stats', {})
        if uhi_stats:
            elements.append(Paragraph("Urban Heat Island Analysis", heading_style))
            
            uhi_intensity = uhi_stats.get('uhi_intensity', 0) or 0
            
            urban_stats = uhi_stats.get('urban_stats', {})
            rural_stats = uhi_stats.get('rural_stats', {})
            urban_mean_key = f"LST_{time_of_day}_mean"
            urban_mean = urban_stats.get(urban_mean_key, 0) if urban_stats else 0
            rural_mean = rural_stats.get(urban_mean_key, 0) if rural_stats else 0
            
            if uhi_intensity >= 5:
                uhi_severity = "Severe UHI effect - Significant urban warming"
            elif uhi_intensity >= 3:
                uhi_severity = "Moderate UHI effect - Noticeable urban warming"
            elif uhi_intensity >= 1:
                uhi_severity = "Mild UHI effect - Slight urban warming"
            else:
                uhi_severity = "Minimal UHI effect"
            
            uhi_data = [
                ['UHI Intensity', f"{uhi_intensity:.1f}°C" if uhi_intensity else "N/A"],
                ['Urban Mean Temp', f"{urban_mean:.1f}°C" if urban_mean else "N/A"],
                ['Rural Mean Temp', f"{rural_mean:.1f}°C" if rural_mean else "N/A"],
                ['Assessment', uhi_severity]
            ]
            uhi_table = Table(uhi_data, colWidths=[5*cm, 8*cm])
            uhi_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('PADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ]))
            elements.append(uhi_table)
            elements.append(Spacer(1, 10))
            elements.append(Paragraph(
                "UHI intensity represents the temperature difference between urban areas and surrounding rural/vegetated areas. "
                "Higher values indicate stronger urban heating effects.",
                note_style
            ))
            elements.append(Spacer(1, 15))
        
        time_series = report_data.get('time_series', [])
        if time_series:
            elements.append(PageBreak())
            elements.append(Paragraph("Temperature Time Series", heading_style))
            
            try:
                chart_buf = _create_chart_image('line', time_series, 'Land Surface Temperature Trend', 450, 200)
                elements.append(Image(chart_buf, width=4.5*inch, height=2*inch))
            except Exception:
                pass
            
            temps = [d.get('mean_lst', 0) for d in time_series if d.get('mean_lst')]
            if temps:
                summary_text = f"Average: {np.mean(temps):.1f}°C | Maximum: {np.max(temps):.1f}°C | Minimum: {np.min(temps):.1f}°C | Range: {np.max(temps) - np.min(temps):.1f}°C"
                elements.append(Paragraph(summary_text, body_style))
            elements.append(Spacer(1, 15))
        
        warming_trend = report_data.get('warming_trend', {})
        if warming_trend:
            elements.append(Paragraph("Warming Trend Analysis", heading_style))
            
            slope = warming_trend.get('slope_per_year', warming_trend.get('slope', 0))
            total_change = warming_trend.get('total_change', warming_trend.get('total_warming', 0))
            r_squared = warming_trend.get('r_squared', 0)
            p_value = warming_trend.get('p_value', 1)
            start_year = warming_trend.get('start_year', '')
            end_year = warming_trend.get('end_year', '')
            
            trend_data = [
                ['Warming Rate', f"{slope:+.3f}°C per year"],
                ['Total Temperature Change', f"{total_change:+.2f}°C"],
                ['Analysis Period', f"{start_year} to {end_year}"],
                ['R² (Model Fit)', f"{r_squared:.3f}"],
                ['Statistical Significance', 'Significant (p<0.05)' if p_value < 0.05 else 'Not Significant']
            ]
            
            trend_table = Table(trend_data, colWidths=[5*cm, 6*cm])
            trend_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('PADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ]))
            elements.append(trend_table)
            
            if slope > 0:
                trend_interpretation = f"The area shows a warming trend of {slope:.3f}°C per year. Over the analysis period, this represents a total temperature increase of {total_change:.2f}°C."
            else:
                trend_interpretation = f"The area shows a cooling trend of {abs(slope):.3f}°C per year."
            
            elements.append(Spacer(1, 10))
            elements.append(Paragraph(trend_interpretation, body_style))
        
        elements.append(Spacer(1, 30))
        # Replaced hardcoded recommendations with dynamic insights
        
        # Add Insights Section
        insights = report_data.get('insights')
        if insights:
            # Replaces the recommendations section or appends to it? 
            # The prompt implies getting insights from the logic. 
            # We'll prioritize the insights passed in.
            elements.append(PageBreak())
            styles_dict = {'Heading': heading_style, 'Body': body_style}
            _add_insights_section(elements, styles_dict, insights)
        
        elements.append(Spacer(1, 30))
        elements.append(Paragraph("—" * 40, styles['Normal']))
        elements.append(Paragraph("Generated by India GIS & Remote Sensing Portal", note_style))
        elements.append(Paragraph("Data Source: MODIS Land Surface Temperature via Google Earth Engine", note_style))
        
        doc.build(elements)
        pdf_data = buffer.getvalue()
        buffer.close()
        return pdf_data
        
    except Exception as e:
        print(f"Error generating Urban Heat PDF: {e}")
        return None


def generate_pdf_report(report_data, report_type="lulc"):
    if report_type == "lulc":
        return generate_lulc_pdf_report(report_data)
    elif report_type == "aqi":
        return generate_aqi_pdf_report(report_data)
    elif report_type == "urban_heat":
        return generate_urban_heat_pdf_report(report_data)
def generate_predictive_pdf_report(report_data):
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch, cm
        from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
        
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=1*cm, bottomMargin=1*cm)
        styles = getSampleStyleSheet()
        elements = []
        
        title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=22, 
                                      spaceAfter=20, alignment=TA_CENTER, textColor=colors.HexColor('#5e35b1'))
        subtitle_style = ParagraphStyle('Subtitle', parent=styles['Heading2'], fontSize=14, 
                                         spaceAfter=10, alignment=TA_CENTER, textColor=colors.grey)
        heading_style = ParagraphStyle('Heading', parent=styles['Heading2'], fontSize=14, 
                                        spaceBefore=15, spaceAfter=10, textColor=colors.HexColor('#673ab7'))
        body_style = ParagraphStyle('Body', parent=styles['Normal'], fontSize=10, 
                                     spaceAfter=8, alignment=TA_JUSTIFY)
        note_style = ParagraphStyle('Note', parent=styles['Normal'], fontSize=8, 
                                     textColor=colors.grey, alignment=TA_LEFT, leftIndent=20)
        
        elements.append(Paragraph("Predictive Analysis Report", title_style))
        elements.append(Paragraph("India GIS & Remote Sensing Portal", subtitle_style))
        elements.append(Spacer(1, 20))
        
        curr_year = report_data.get('current_year', 'N/A')
        target_year = report_data.get('target_year', 'N/A')
        confidence = report_data.get('confidence', 'N/A')
        
        info_data = [
            ['Analysis Period', f"{curr_year} to {target_year}"],
            ['Model Confidence', f"R² = {confidence}"],
            ['Report Generated', datetime.now().strftime('%Y-%m-%d %H:%M:%S')]
        ]
        info_table = Table(info_data, colWidths=[4*cm, 9*cm])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#ede7f6')),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('PADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        elements.append(info_table)
        elements.append(Spacer(1, 25))
        
        # Metrics Table
        metrics = report_data.get('metrics', {})
        if metrics:
            elements.append(Paragraph("Forecast Summary & Key Metrics", heading_style))
            
            table_data = [['Variable', 'Current', f'Forecast ({target_year})', 'Change', '% Change']]
            
            for var_name, m in metrics.items():
                curr = m.get('current', 0)
                fut = m.get('future', 0)
                delta = m.get('delta', 0)
                pct = m.get('pct', 0)
                
                # Format
                def fmt(v): return f"{v:.2f}" if isinstance(v, (int, float)) else str(v)
                
                table_data.append([
                    var_name,
                    fmt(curr),
                    fmt(fut),
                    f"{delta:+.2f}",
                    f"{pct:+.1f}%"
                ])
                
            metric_table = Table(table_data, colWidths=[4*cm, 3*cm, 3*cm, 3*cm, 3*cm])
            metric_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#b39ddb')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
                ('PADDING', (0, 0), (-1, -1), 6),
            ]))
            elements.append(metric_table)
            elements.append(Spacer(1, 20))

        # Insights Section
        insights = report_data.get('insights')
        if insights:
            styles_dict = {'Heading': heading_style, 'Body': body_style}
            _add_insights_section(elements, styles_dict, insights)
            
        elements.append(Spacer(1, 30))
        elements.append(Paragraph("—" * 40, styles['Normal']))
        elements.append(Paragraph("Generated by India GIS & Remote Sensing Portal", note_style))
        elements.append(Paragraph("Disclaimer: Forecasts are based on historical trends and machine learning models. Actual values may vary.", note_style))
        
        doc.build(elements)
        pdf_data = buffer.getvalue()
        buffer.close()
        return pdf_data
        
    except Exception as e:
        print(f"Error generating Predictive PDF: {e}")
        return None


def generate_pdf_report(report_data, report_type="lulc"):
    if report_type == "lulc":
        return generate_lulc_pdf_report(report_data)
    elif report_type == "aqi":
        return generate_aqi_pdf_report(report_data)
    elif report_type == "urban_heat":
        return generate_urban_heat_pdf_report(report_data)
    elif report_type == "predictive":
        return generate_predictive_pdf_report(report_data)
    elif report_type == "sustainability":
        return generate_sustainability_pdf_report(report_data)
    else:
        return None


def generate_sustainability_pdf_report(report_data):
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch, cm
        from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
        
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=1*cm, bottomMargin=1*cm, 
                                leftMargin=1.5*cm, rightMargin=1.5*cm)
        styles = getSampleStyleSheet()
        elements = []
        
        title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=24, 
                                      spaceAfter=10, alignment=TA_CENTER, textColor=colors.HexColor('#1e3a5f'))
        subtitle_style = ParagraphStyle('Subtitle', parent=styles['Heading2'], fontSize=12, 
                                         spaceAfter=20, alignment=TA_CENTER, textColor=colors.grey)
        heading_style = ParagraphStyle('Heading', parent=styles['Heading2'], fontSize=14, 
                                        spaceBefore=20, spaceAfter=10, textColor=colors.HexColor('#1565c0'))
        subheading_style = ParagraphStyle('SubHeading', parent=styles['Heading3'], fontSize=12, 
                                           spaceBefore=10, spaceAfter=8, textColor=colors.HexColor('#2e7d32'))
        body_style = ParagraphStyle('Body', parent=styles['Normal'], fontSize=10, 
                                     spaceAfter=8, alignment=TA_JUSTIFY)
        note_style = ParagraphStyle('Note', parent=styles['Normal'], fontSize=8, 
                                     textColor=colors.grey, alignment=TA_LEFT)
        
        region_name = report_data.get('region_name', 'Unknown Region')
        year = report_data.get('year', 2024)
        scores = report_data.get('scores', {})
        metrics = report_data.get('metrics', {})
        text_sections = report_data.get('text_sections', {})
        
        # Use raw_metrics as fall back if metrics is empty, or just use raw_metrics as primary
        metrics = report_data.get('raw_metrics', report_data.get('metrics', {}))
        
        elements.append(Paragraph("URBAN SUSTAINABILITY REPORT", title_style))
        elements.append(Paragraph("Comprehensive Environmental Assessment", subtitle_style))
        elements.append(Spacer(1, 10))
        
        info_data = [
            ['Region', region_name],
            ['Analysis Year', str(year)],
            ['Report Generated', datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
            ['Data Sources', 'Sentinel-2, Dynamic World, ECMWF CAMS, MODIS']
        ]
        info_table = Table(info_data, colWidths=[5*cm, 12*cm])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e3f2fd')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('PADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elements.append(info_table)
        elements.append(Spacer(1, 25))
        
        elements.append(Paragraph("URBAN SUSTAINABILITY SCORE (USS)", heading_style))
        
        total_uss = scores.get('total_uss', 0)
        classification = scores.get('classification', 'Unknown')
        class_color = scores.get('class_color', '#666666')
        class_desc = scores.get('class_desc', '')
        
        uss_data = [[
            Paragraph(f'<font size="36" color="{class_color}"><b>{total_uss:.0f}</b></font><font size="14">/100</font>', 
                     ParagraphStyle('USSScore', alignment=TA_CENTER)),
            Paragraph(f'<font size="16" color="{class_color}"><b>{classification}</b></font><br/><br/>'
                     f'<font size="10">{class_desc}</font>',
                     ParagraphStyle('USSClass', alignment=TA_CENTER))
        ]]
        uss_table = Table(uss_data, colWidths=[5*cm, 12*cm])
        uss_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 20),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 20),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ('BOX', (0, 0), (-1, -1), 2, colors.HexColor(class_color)),
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
        ]))
        elements.append(uss_table)
        elements.append(Spacer(1, 25))
        
        elements.append(Paragraph("MODULE SCORES BREAKDOWN", heading_style))
        
        module_header = ['Module', 'Score', 'Grade', 'Key Metric', 'Value']
        module_rows = [module_header]
        
        modules_data = [
            ('Vegetation', 'vegetation', 'NDVI', metrics.get('ndvi', 0)),
            ('Air Quality', 'aqi', 'AQI', metrics.get('aqi', 0)),
            ('Urban Heat', 'heat', 'LST (°C)', metrics.get('lst', 0)),
            ('Future Risk', 'prediction', 'Risk Index', metrics.get('risk', 0)),
            ('Earthquake Safety', 'earthquake', 'Risk Score', metrics.get('eq_risk', 0))
        ]
        
        for name, key, metric_name, metric_val in modules_data:
            module_score = scores.get(key, {})
            score_val = module_score.get('score', 0)
            grade = module_score.get('grade', 'N/A')
            module_rows.append([
                name,
                f"{score_val:.1f}/25",
                f"Grade {grade}",
                metric_name,
                f"{metric_val:.2f}" if isinstance(metric_val, float) else str(metric_val)
            ])
        
        module_table = Table(module_rows, colWidths=[4*cm, 2.5*cm, 2.5*cm, 3.5*cm, 3*cm])
        module_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1565c0')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('PADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
        ]))
        elements.append(module_table)
        elements.append(Spacer(1, 25))
        
        elements.append(Paragraph("DETAILED METRICS", heading_style))
        
        metrics_detail = [
            ['Metric', 'Value', 'Unit', 'Status'],
            ['NDVI (Vegetation Health)', f"{metrics.get('ndvi', 0):.3f}", 'index', 
             'Good' if metrics.get('ndvi', 0) > 0.3 else 'Moderate' if metrics.get('ndvi', 0) > 0.2 else 'Poor'],
            ['Impervious Surface', f"{metrics.get('impervious', 0)*100:.1f}", '%',
             'Low' if metrics.get('impervious', 0) < 0.3 else 'Moderate' if metrics.get('impervious', 0) < 0.5 else 'High'],
            ['Air Quality Index', f"{metrics.get('aqi', 0):.0f}", 'AQI',
             'Good' if metrics.get('aqi', 0) < 50 else 'Moderate' if metrics.get('aqi', 0) < 100 else 'Unhealthy'],
            ['PM2.5 Concentration', f"{metrics.get('pm25', 0):.1f}", 'µg/m³',
             'Good' if metrics.get('pm25', 0) < 12 else 'Moderate' if metrics.get('pm25', 0) < 35 else 'Unhealthy'],
            ['Land Surface Temperature', f"{metrics.get('lst', 0):.1f}", '°C',
             'Comfortable' if metrics.get('lst', 0) < 30 else 'Warm' if metrics.get('lst', 0) < 35 else 'Hot'],
            ['Environmental Risk Index', f"{metrics.get('risk', 0):.2f}", 'index',
             'Low' if metrics.get('risk', 0) < 0.3 else 'Moderate' if metrics.get('risk', 0) < 0.6 else 'High'],
            ['Seismic Risk Score', f"{metrics.get('eq_risk', 0):.1f}", 'Index',
             'Low' if metrics.get('eq_risk', 0) < 40 else 'Moderate' if metrics.get('eq_risk', 0) < 70 else 'High'],
        ]
        
        metrics_table = Table(metrics_detail, colWidths=[6*cm, 3*cm, 3*cm, 3.5*cm])
        metrics_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4caf50')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('PADDING', (0, 0), (-1, -1), 7),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
        ]))
        elements.append(metrics_table)
        elements.append(Spacer(1, 15))
        
        elements.append(PageBreak())
        
        # --- Seismic Breakdown Section ---
        eq_risk_data = report_data.get('eq_risk_data', {})
        if eq_risk_data and 'breakdown' in eq_risk_data:
            elements.append(Paragraph("SEISMIC SAFETY ANALYSIS", heading_style))
            
            bd = eq_risk_data.get('breakdown', {})
            total_risk = eq_risk_data.get('total_score', 0)
            risk_class = eq_risk_data.get('risk_class', 'Unknown')
            
            # Intro text
            zone = report_data.get('zone_info', {}).get('zone', 'Unknown')
            pga = report_data.get('hazard_stats', {}).get('mean_pga', 0)
            
            eq_intro = f"""
            <b>Seismic Zone:</b> {zone} &nbsp;&nbsp;|&nbsp;&nbsp; <b>Est. PGA:</b> {pga:.2f}g &nbsp;&nbsp;|&nbsp;&nbsp; <b>Risk Class:</b> {risk_class}<br/><br/>
            The Earthquake Safety Score is derived from a detailed risk assessment model considering multiple weighted factors. 
            A lower Risk Score indicates higher Safety.
            """
            elements.append(Paragraph(eq_intro, body_style))
            elements.append(Spacer(1, 10))
            
            # Breakdown Table
            eq_header = ['Risk Component', 'Weight', 'Component Score', 'Weighted Score']
            eq_rows = [eq_header]
            
            # Map keys to display names
            key_map = {
                'pga': 'PGA Hazard (Ground Shaking)',
                'zone': 'Seismic Zone Factor (IS 1893)',
                'history': 'Historical Seismicity (Frequency)',
                'fault': 'Fault Proximity',
                'exposure': 'Urban Exposure (Built-up Density)'
            }
            
            for k, v in bd.items():
                name = key_map.get(k, k.title())
                weight = f"{v['weight']*100:.0f}%"
                c_score = f"{v['score']:.0f}"
                w_score = f"{v['weighted_score']:.1f}"
                eq_rows.append([name, weight, c_score, w_score])
                
            # Total Row
            eq_rows.append(['Total Seismic Risk Score', '', '', f"<b>{total_risk:.1f} / 100</b>"])
            
            eq_table = Table(eq_rows, colWidths=[8*cm, 3*cm, 3.5*cm, 3.5*cm])
            eq_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#607d8b')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('PADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
                ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#eceff1')),
            ]))
            elements.append(eq_table)
            
            # Explanation of conversion
            elements.append(Spacer(1, 10))
            conv_text = f"<b>Safety Score Contribution:</b> The Risk Score ({total_risk:.1f}) is inverted to calculate the Safety Score for the USS: <br/>" \
                        f"Safety Score = 25 * (1 - ({total_risk:.1f} / 100)) = <b>{report_data['scores']['earthquake']['score']:.1f} / 25</b>"
            elements.append(Paragraph(conv_text, body_style))
            elements.append(Spacer(1, 25))
        
        elements.append(Paragraph("KEY FINDINGS", heading_style))
        
        strongest = report_data.get('strongest_sector', 'N/A')
        weakest = report_data.get('weakest_sector', 'N/A')
        
        findings_text = f"""
        <b>Strongest Sector:</b> {strongest}<br/>
        This sector demonstrates the best performance in the sustainability assessment and can serve as a model for other areas.<br/><br/>
        <b>Weakest Sector:</b> {weakest}<br/>
        This sector requires immediate attention and targeted interventions to improve the overall sustainability score.
        """
        elements.append(Paragraph(findings_text, body_style))
        elements.append(Spacer(1, 15))
        
        elements.append(Paragraph("PRIORITY RECOMMENDATIONS", heading_style))
        
        mitigations_full = text_sections.get('mitigations_full', {})
        priority_mitigations = mitigations_full.get(weakest, [])
        
        if priority_mitigations:
            for i, mitigation in enumerate(priority_mitigations[:5], 1):
                elements.append(Paragraph(f"<b>{i}.</b> {mitigation}", body_style))
        else:
            elements.append(Paragraph("No specific recommendations available.", body_style))
        
        elements.append(Spacer(1, 20))
        
        elements.append(Paragraph("IMPLEMENTATION ROADMAP", heading_style))
        
        roadmap = text_sections.get('roadmap', [])
        for phase in roadmap:
            phase_text = f"<b>{phase.get('phase', 'Phase')}</b> (Expected Gain: +{phase.get('expected_gain', 0)} USS points)"
            elements.append(Paragraph(phase_text, subheading_style))
            for action in phase.get('actions', []):
                elements.append(Paragraph(f"• {action}", body_style))
            elements.append(Spacer(1, 10))
        
        elements.append(Spacer(1, 20))
        
        elements.append(Paragraph("METHODOLOGY", heading_style))
        
        methodology_text = """
        This Urban Sustainability Score (USS) integrates satellite-derived environmental data from multiple sources:
        <br/><br/>
        <b>Data Sources:</b><br/>
        • Sentinel-2 (10m resolution) - Vegetation indices and land cover<br/>
        • Dynamic World - Land use/land cover classification (9 classes)<br/>
        • ECMWF CAMS - Air quality data (PM2.5, PM10)<br/>
        • MODIS Terra/Aqua - Land Surface Temperature (1km resolution)<br/>
        <br/>
        <b>Scoring Components:</b><br/>
        • Vegetation Score (25 pts): Based on NDVI and impervious surface ratio<br/>
        • Air Quality Score (25 pts): Derived from PM2.5 concentration using EPA AQI methodology<br/>
        • Urban Heat Score (25 pts): Based on LST deviation from comfort threshold (25°C)<br/>
        • Future Risk Score (25 pts): 5-year trend analysis for environmental risk prediction<br/>
        • Seismic Safety Score (25 pts): Based on Zone Factor, PGA, and Exposure indices<br/>
        <br/>
        <b>Classification:</b><br/>
        • 80-100: Excellent (Highly sustainable environment)<br/>
        • 60-79: Good (Well-managed with minor improvements needed)<br/>
        • 40-59: Moderate (Requires attention in multiple areas)<br/>
        • 20-39: Poor (Significant environmental challenges)<br/>
        • 0-19: Critical (Urgent intervention required)<br/><br/>
        <b>Note:</b> The total raw score (max 125) is normalized to a standard 0-100 scale for final classification.
        """
        elements.append(Paragraph(methodology_text, body_style))
        
        elements.append(Spacer(1, 30))
        elements.append(Paragraph("—" * 50, styles['Normal']))
        elements.append(Paragraph("Generated by India GIS & Remote Sensing Portal", note_style))
        elements.append(Paragraph(f"Report Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", note_style))
        elements.append(Spacer(1, 10))
        elements.append(Paragraph(
            "<b>Disclaimer:</b> This report is generated using satellite remote sensing data and automated analysis. "
            "Results should be verified with ground-truth data for policy decisions. Data sources include "
            "Google Earth Engine, Copernicus Climate Data Store, and NASA.", note_style))
        
        doc.build(elements)
        pdf_data = buffer.getvalue()
        buffer.close()
        return pdf_data
        
    except Exception as e:
        print(f"Error generating Sustainability PDF: {e}")
        import traceback
        traceback.print_exc()
        return None


