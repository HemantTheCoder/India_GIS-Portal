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


WHO_STANDARDS = {
    'NO2': {'annual': 10, 'unit': 'µg/m³', 'name': 'Nitrogen Dioxide'},
    'SO2': {'daily': 40, 'unit': 'µg/m³', 'name': 'Sulfur Dioxide'},
    'CO': {'daily': 4, 'unit': 'mg/m³', 'name': 'Carbon Monoxide'},
    'O3': {'8hr': 100, 'unit': 'µg/m³', 'name': 'Ozone'},
    'PM2.5': {'daily': 15, 'unit': 'µg/m³', 'name': 'Particulate Matter < 2.5µm'},
    'PM10': {'daily': 45, 'unit': 'µg/m³', 'name': 'Particulate Matter < 10µm'},
}

from services.aqi_logic import calculate_cpcb_aqi

def generate_aqi_pdf_report(report_data):
    """Generates a Premium PDF Report for AQI Analysis (Updated Phase 7)."""
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch, cm
        from reportlab.lib.enums import TA_CENTER, TA_LEFT

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=1*cm, bottomMargin=1*cm)
        styles = getSampleStyleSheet()
        elements = []

        # Custom Styles
        title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=24, 
                                      spaceAfter=20, alignment=TA_CENTER, textColor=colors.HexColor('#d32f2f'))
        heading_style = ParagraphStyle('Heading', parent=styles['Heading2'], fontSize=16, 
                                        spaceBefore=15, spaceAfter=10, textColor=colors.HexColor('#1976d2'))
        subheading_style = ParagraphStyle('SubHeading', parent=styles['Heading3'], fontSize=12, 
                                        textColor=colors.grey)

        # Header
        elements.append(Paragraph("Air Quality Detailed Assessment", title_style))
        elements.append(Paragraph(f"Analysis Report | {report_data.get('city_name', 'Region')}", subheading_style))
        elements.append(Spacer(1, 20))

        # Info Table
        info_data = [
            ['Location', report_data.get('city_name', 'N/A')],
            ['Analysis Date', datetime.now().strftime('%Y-%m-%d')],
            ['Data Source', "Sentinel-5P (Gases) & ECMWF CAMS (PM)"]
        ]
        info_table = Table(info_data, colWidths=[5*cm, 12*cm])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#ffebee')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('PADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(info_table)
        elements.append(Spacer(1, 20))

        # --- Section 1: Surface AQI (PM2.5 / PM10) ---
        elements.append(Paragraph("1. Surface Pollution & AQI", heading_style))
        elements.append(Paragraph("Based on Particulate Matter (PM2.5 / PM10) - CPCB Standards", styles['Italic']))
        elements.append(Spacer(1, 10))

        compliance = report_data.get('compliance', {})
        aqi_val = compliance.get('aqi_val', None)
        aqi_cat = compliance.get('aqi_cat', 'Insufficient Data')
        aqi_color = compliance.get('aqi_color', '#808080')
        dominant = compliance.get('dominant', 'N/A')
        
        # New Style for Big Stats
        aqi_style = ParagraphStyle('AQI_Big', parent=styles['Normal'], fontSize=24, leading=28,
                                   alignment=TA_CENTER, textColor=colors.HexColor(aqi_color if aqi_color else '#000000'))
        
        cat_style = ParagraphStyle('AQI_Cat', parent=styles['Normal'], fontSize=16, leading=20, 
                                   alignment=TA_CENTER, textColor=colors.black)

        # Draw Gauge if data exists
        if aqi_val is not None:
             # 1. ADD TEXT FIRST (Safe)
             try:
                 elements.append(Paragraph(f"<b>AQI INDEX: {aqi_val}</b>", 
                     ParagraphStyle('AQI_Val', parent=styles['Heading1'], fontSize=24, alignment=TA_CENTER, textColor=colors.HexColor(aqi_color if aqi_color else '#000000'))))
                     
                 elements.append(Paragraph(f"<b>{aqi_cat.upper()}</b>", 
                     ParagraphStyle('AQI_Cat', parent=styles['Normal'], fontSize=18, alignment=TA_CENTER, textColor=colors.black)))
             except Exception as e:
                 elements.append(Paragraph(f"Error rendering AQI Text: {e}", styles['Normal']))
             
             elements.append(Spacer(1, 10))
             
             # 2. ADD GAUGE SECOND (Risky - Wrap in try/catch)
             try:
                 gauge_buf = _create_chart_image('gauge', {'score': aqi_val}, "", width=400, height=200)
                 elements.append(Image(gauge_buf, width=4*inch, height=2*inch))
             except Exception as e:
                 print(f"Gauge Gen Error: {e}")
                 elements.append(Paragraph("(Gauge visualization unavailable)", styles['Italic']))
             
             elements.append(Paragraph(f"Dominant Pollutant: {dominant}", styles['Normal']))
             
        else:
             # Fallback if no PM data
             elements.append(Paragraph("<b>AQI: N/A</b>", aqi_style))
             elements.append(Paragraph("(Requires PM2.5 or PM10 data)", cat_style))
        
        elements.append(Spacer(1, 15))

        # PM Detail Table
        pm_data = [['Pollutant', 'Concentration', 'Unit', 'WHO Limit', 'Status']]
        
        details = compliance.get('details', [])
        pm_details = [d for d in details if d['type'] == 'particles']
        
        if pm_details:
            for d in pm_details:
                status_color = colors.green if d['status'] in ['Excellent', 'Good'] else (colors.orange if d['status'] in ['Moderate', 'Satisfactory'] else colors.red)
                pm_data.append([
                    d['pollutant'],
                    f"{d['measured']:.2f}",
                    d['unit'],
                    f"{d['limit']}",
                    Paragraph(f"<font color='{status_color.hexval()}'><b>{d['status']}</b></font>", styles['Normal'])
                ])
            
            t_pm = Table(pm_data, colWidths=[3*cm, 4*cm, 2*cm, 3*cm, 4*cm])
            t_pm.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#5c6bc0')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#e8eaf6')])
            ]))
            elements.append(t_pm)
        else:
             elements.append(Paragraph("No PM2.5/PM10 data available for AQI calculation.", styles['Normal']))

        elements.append(Spacer(1, 20))

        # --- Section 2: Trace Gases (Satellite Column Density) ---
        elements.append(Paragraph("2. Trace Gas Analysis (Satellite)", heading_style))
        elements.append(Paragraph(
            "Values represent <b>Total Column Density</b> (vertical sum of gas molecules from ground to space). "
            "<i>Note: High column density usually correlates with ground pollution, but these are NOT direct breathing-level concentrations.</i>",
            styles['Normal']))
        elements.append(Spacer(1, 10))

        gas_data = [['Gas', 'Column Density', 'Unit', 'Interpretation']]
        gas_details = [d for d in details if d['type'] == 'gas']

        if gas_details:
            for d in gas_details:
                gas_data.append([
                    d['pollutant'],
                    f"{d['measured']:.2f}", 
                    d['unit'],
                    "Satellite Observation"
                ])
            
            t_gas = Table(gas_data, colWidths=[3*cm, 5*cm, 3*cm, 5*cm])
            t_gas.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#455a64')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#eceff1')])
            ]))
            elements.append(t_gas)
        else:
             elements.append(Paragraph("No Trace Gas data available.", styles['Normal']))
             
        elements.append(Spacer(1, 20))

        # Visualizations
        if 'charts' in report_data:
            elements.append(PageBreak())
            elements.append(Paragraph("Visual Analysis", heading_style))
            for title, chart_buf in report_data['charts'].items():
                elements.append(Paragraph(title, subheading_style))
                elements.append(Image(chart_buf, width=6*inch, height=3.5*inch))
                elements.append(Spacer(1, 15))
        
        # Auto-generate Charts from Time Series
        if report_data.get('time_series'):
            ts_data = report_data['time_series']
            for pollutant, data in ts_data.items():
                if data:
                    try:
                        chart_type = "Surface Concentration" if pollutant in ['PM2.5', 'PM10'] else "Column Density"
                        chart_buf = _create_chart_image('line', data, f"{pollutant} Trends ({chart_type})", width=600, height=300)
                        elements.append(Paragraph(f"Trend: {pollutant}", subheading_style))
                        elements.append(Image(chart_buf, width=6*inch, height=3*inch))
                        elements.append(Spacer(1, 15))
                    except Exception as e:
                        print(f"Chart Gen Error: {e}")

        doc.build(elements)
        return buffer.getvalue()
    except Exception as e:
        print(f"PDF Gen Error: {e}")
        return None

def generate_prediction_pdf_report(report_data):
    """Generates a PDF for Predictive Analysis (Phase 3 Upgrade)."""
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch, cm
        from reportlab.lib.enums import TA_CENTER

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=1*cm, bottomMargin=1*cm)
        styles = getSampleStyleSheet()
        elements = []

        title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=24, 
                                      alignment=TA_CENTER, textColor=colors.HexColor('#7b1fa2'))
                                      
        elements.append(Paragraph("Predictive Impact Assessment", title_style))
        elements.append(Paragraph(f"Horizon: {report_data.get('current_year')} ⮕ {report_data.get('target_year')}", 
                                  ParagraphStyle('Sub', parent=styles['Heading2'], alignment=TA_CENTER)))
        elements.append(Spacer(1, 20))

        # Key Metrics
        metrics = report_data.get('metrics', {})
        if metrics:
            data = [['Metric', 'Current', 'Predicted', 'Change']]
            for k, v in metrics.items():
                change_color = colors.red if v.get('delta', 0) < 0 and 'Trees' in k else colors.black
                if 'Built' in k and v.get('delta', 0) > 0: change_color = colors.red # Bad sign usually
                
                data.append([
                    k,
                    f"{v.get('current',0):.1f}",
                    f"{v.get('future',0):.1f}",
                    Paragraph(f"<font color='{change_color.hexval()}'>{v.get('delta',0):+.1f} ({v.get('pct',0):+.1f}%)</font>", styles['Normal'])
                ])
            
            t = Table(data, colWidths=[5*cm, 3*cm, 3*cm, 4*cm])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#ab47bc')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
                ('PADDING', (0, 0), (-1, -1), 10),
            ]))
            elements.append(t)
            elements.append(Spacer(1, 20))

        # Charts
        if 'charts' in report_data:
            for title, chart_buf in report_data['charts'].items():
                elements.append(Paragraph(title, styles['Heading2']))
                elements.append(Image(chart_buf, width=7*inch, height=4*inch))
                elements.append(Spacer(1, 20))
        
        # Auto-Plot Forecasts
        if report_data.get('forecast_data'):
            import matplotlib.pyplot as plt
            import pandas as pd
            
            f_data = pd.DataFrame(report_data['forecast_data'])
            # We expect columns: date, value, type (historical/predicted)
            
            if not f_data.empty:
                # Plot for the primary metric
                # Determine value col (first non-date/type col)
                val_cols = [c for c in f_data.columns if c not in ['date', 'type']]
                
                for col in val_cols[:2]: # Plot max 2 metrics to save space
                    try:
                        fig, ax = plt.subplots(figsize=(8, 4))
                        
                        # Plot Historical
                        hist = f_data[f_data['type'] == 'historical']
                        ax.plot(pd.to_datetime(hist['date']), hist[col], label='Historical', color='#3b82f6', linewidth=2)
                        
                        # Plot Forecast
                        pred = f_data[f_data['type'] == 'predicted']
                        ax.plot(pd.to_datetime(pred['date']), pred[col], label='Forecast', color='#10b981', linestyle='--', linewidth=2)
                        
                        ax.set_title(f"{col} Projection", fontweight='bold')
                        ax.legend()
                        ax.grid(True, alpha=0.3)
                        
                        buf = io.BytesIO()
                        fig.savefig(buf, format='png', bbox_inches='tight', dpi=100)
                        plt.close(fig)
                        buf.seek(0)
                        
                        elements.append(Paragraph(f"Trend Analysis: {col}", styles['Heading2']))
                        elements.append(Image(buf, width=6.5*inch, height=3.5*inch))
                        elements.append(Spacer(1, 15))
                    except Exception as e:
                        print(f"Pred Chart Error: {e}")
                
        elements.append(Paragraph(f"Model Confidence: {report_data.get('confidence', 'N/A')}", styles['Italic']))

        doc.build(elements)
        return buffer.getvalue()

    except Exception as e:
        print(f"PDF Gen Error: {e}")
        return None

NAAQS_STANDARDS = {
    'NO2': {'annual': 40, 'unit': 'µg/m³'},
    'SO2': {'annual': 50, 'unit': 'µg/m³'},
    'CO': {'8hr': 2, 'unit': 'mg/m³'},
    'O3': {'8hr': 100, 'unit': 'µg/m³'},
}

def calculate_aqi_compliance_score(pollutant_stats):
    """
    Refined Function (Phase 7.1):
    - Focuses strictly on CPCB AQI for Surface PM2.5/PM10.
    - Removes the misleading 'Overall Score' that mixed Satellite Gases.
    """
    if not pollutant_stats:
        return {'aqi_val': None, 'details': []}
    
    details = []
    
    # 1. Surface Pollutants (PM2.5, PM10)
    # We strictly use these for the AQI Gauge
    pm25_val = None
    pm10_val = None
    
    if 'PM2.5' in pollutant_stats:
        stats = pollutant_stats['PM2.5']
        val = stats.get('mean', 0)
        pm25_val = val
        
        # WHO Limit Check (Daily Mean: 15 µg/m³)
        limit = 15
        ratio = val / limit if limit else 0
        status = "Good" if ratio <= 1 else ("Moderate" if ratio <= 2 else "Poor")
        
        details.append({
            'type': 'particles', 'pollutant': 'PM2.5', 'measured': val, 'unit': 'µg/m³',
            'limit': limit, 'status': status
        })
        
    if 'PM10' in pollutant_stats:
        stats = pollutant_stats['PM10']
        val = stats.get('mean', 0)
        pm10_val = val
        
        # WHO Limit Check (Daily Mean: 45 µg/m³)
        limit = 45
        ratio = val / limit if limit else 0
        status = "Good" if ratio <= 1 else ("Moderate" if ratio <= 2 else "Poor")
        
        details.append({
            'type': 'particles', 'pollutant': 'PM10', 'measured': val, 'unit': 'µg/m³',
            'limit': limit, 'status': status
        })
        
    # Calculate real AQI using CPCB logic
    aqi_val, aqi_cat, aqi_color, dominant = calculate_cpcb_aqi(pm25_val, pm10_val)
    
    # 2. Trace Gases (NO2, SO2, CO, O3)
    # Purely informational - no "status" or "score" assigned to avoid confusion
    for p in ['NO2', 'SO2', 'CO', 'O3']:
        if p in pollutant_stats:
            stats = pollutant_stats[p]
            val = stats.get('mean', 0)
            unit = stats.get('unit', '')
            details.append({
                'type': 'gas', 'pollutant': p, 'measured': val, 'unit': unit
            })
            
    return {
        'aqi_val': aqi_val,
        'aqi_cat': aqi_cat,
        'aqi_color': aqi_color,
        'dominant': dominant,
        'details': details
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
            elements.append(change_table)
        
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
            elements.append(Paragraph("Air Quality Compliance Score", heading_style))
            
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
            
            score_text = f"""
            <para align="center">
            <font size="28" color="{score_color}"><b>{score:.0f}</b></font><font size="14">/100</font><br/>
            <font size="12" color="{score_color}"><b>{rating}</b></font>
            </para>
            """
            elements.append(Paragraph(score_text, styles['Normal']))
            elements.append(Spacer(1, 15))
            
            details = compliance.get('details', [])
            if details:
                elements.append(Paragraph("Pollutant-wise Compliance vs WHO Standards", body_style))
                
                comp_data = [['Pollutant', 'Measured', 'WHO Limit', 'Ratio', 'Status']]
                for d in details:
                    ratio = d.get('ratio', 0)
                    status = d.get('status', 'Unknown')
                    comp_data.append([
                        d.get('pollutant', ''),
                        f"{d.get('measured', 0):.4f}",
                        f"{d.get('who_limit', 0)}",
                        f"{ratio:.2f}x",
                        status
                    ])
                
                comp_table = Table(comp_data, colWidths=[2.5*cm, 3*cm, 2.5*cm, 2*cm, 3*cm])
                comp_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0288d1')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('PADDING', (0, 0), (-1, -1), 6),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
                ]))
                elements.append(comp_table)
            
            elements.append(Spacer(1, 10))
            method_note = """<b>Methodology:</b> The Air Quality Compliance Score compares measured pollutant concentrations 
            against WHO Air Quality Guidelines. Each pollutant is scored (0-100) based on how far below or above the WHO limit 
            it is: Excellent (≤50% of limit), Good (≤100%), Moderate (≤150%), Poor (≤200%), Very Poor (≤300%), Severe (>300%).
            The overall score is the weighted average across all measured pollutants. A score of 100 indicates full compliance."""
            elements.append(Paragraph(method_note, note_style))
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
        elements.append(Paragraph("Recommendations", heading_style))
        
        recommendations = []
        if vulnerability and vulnerability.get('score', 0) >= 60:
            recommendations.append("• Increase urban green cover through tree planting and parks")
            recommendations.append("• Implement cool roof and cool pavement programs")
            recommendations.append("• Develop heat action plans for vulnerable populations")
        if uhi_stats and uhi_stats.get('mean', 0) >= 3:
            recommendations.append("• Create urban cooling corridors with vegetation")
            recommendations.append("• Promote green building standards")
        if warming_trend and warming_trend.get('slope_per_year', 0) > 0.1:
            recommendations.append("• Monitor long-term temperature trends")
            recommendations.append("• Plan for climate adaptation in urban development")
        
        if not recommendations:
            recommendations.append("• Continue monitoring temperature patterns")
            recommendations.append("• Maintain existing green infrastructure")
        
        for rec in recommendations:
            elements.append(Paragraph(rec, body_style))
        
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
    else:
        return None
