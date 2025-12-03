import io
import pandas as pd
from datetime import datetime

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

def generate_pdf_report(report_data, report_type="lulc"):
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        styles = getSampleStyleSheet()
        elements = []
        
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=1
        )
        
        if report_type == "lulc":
            elements.append(Paragraph("Land Use Land Cover Analysis Report", title_style))
            elements.append(Spacer(1, 12))
            
            if "city_name" in report_data:
                elements.append(Paragraph(f"<b>Location:</b> {report_data['city_name']}", styles["Normal"]))
            if "year" in report_data:
                elements.append(Paragraph(f"<b>Year:</b> {report_data['year']}", styles["Normal"]))
            if "total_area" in report_data:
                elements.append(Paragraph(f"<b>Total Area:</b> {report_data['total_area']} km²", styles["Normal"]))
            
            elements.append(Spacer(1, 20))
            
            if "stats" in report_data and report_data["stats"]:
                table_data = [["Land Cover Class", "Area (km²)", "Percentage (%)"]]
                for name, data in sorted(report_data["stats"].items(), key=lambda x: x[1]["percentage"], reverse=True):
                    table_data.append([name, f"{data['area_sqkm']:.2f}", f"{data['percentage']:.1f}"])
                
                table = Table(table_data, colWidths=[3*inch, 1.5*inch, 1.5*inch])
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 1), (-1, -1), 10),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ]))
                elements.append(table)
        
        elif report_type == "aqi":
            elements.append(Paragraph("Air Quality Analysis Report", title_style))
            elements.append(Spacer(1, 12))
            
            if "city_name" in report_data:
                elements.append(Paragraph(f"<b>Location:</b> {report_data['city_name']}", styles["Normal"]))
            if "pollutant" in report_data:
                elements.append(Paragraph(f"<b>Pollutant:</b> {report_data['pollutant']}", styles["Normal"]))
            if "date_range" in report_data:
                elements.append(Paragraph(f"<b>Date Range:</b> {report_data['date_range']}", styles["Normal"]))
            
            elements.append(Spacer(1, 20))
            
            if "stats" in report_data and report_data["stats"]:
                table_data = [["Statistic", "Value", "Unit"]]
                stats = report_data["stats"]
                unit = stats.get("unit", "")
                for key, value in stats.items():
                    if key != "unit" and value is not None:
                        table_data.append([key.replace("_", " ").title(), f"{value:.4f}", unit])
                
                table = Table(table_data, colWidths=[2*inch, 2*inch, 1.5*inch])
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2196F3')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ]))
                elements.append(table)
        
        elements.append(Spacer(1, 30))
        elements.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles["Normal"]))
        elements.append(Paragraph("India GIS & Remote Sensing Portal", styles["Normal"]))
        
        doc.build(elements)
        pdf_data = buffer.getvalue()
        buffer.close()
        
        return pdf_data
    
    except ImportError:
        return None
    except Exception as e:
        print(f"Error generating PDF: {e}")
        return None
