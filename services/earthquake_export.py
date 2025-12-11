
import io
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY

def _create_chart_image(chart_type, data, title, width=400, height=250):
    """
    Helper to create charts for the PDF (Pie, Bar, Line).
    Adjusted to handle Earthquake specific data types.
    """
    fig, ax = plt.subplots(figsize=(width/100, height/100), dpi=100)
    
    if chart_type == 'magnitude_hist':
        # Data is list of magnitudes
        ax.hist(data, bins=range(2, 10), color='#f97316', alpha=0.7, edgecolor='black')
        ax.set_xlabel('Magnitude')
        ax.set_ylabel('Frequency')
        ax.set_title(title, fontsize=10, fontweight='bold')
        ax.grid(True, alpha=0.3)
        
    elif chart_type == 'depth_scatter':
        # Data is list of dicts {mag, depth}
        mags = [d['mag'] for d in data]
        depths = [d['depth'] for d in data]
        scatter = ax.scatter(mags, depths, c=depths, cmap='viridis', alpha=0.6)
        ax.set_xlabel('Magnitude')
        ax.set_ylabel('Depth (km)')
        ax.invert_yaxis() # Depth increases downwards
        plt.colorbar(scatter, label='Depth')
        ax.set_title(title, fontsize=10, fontweight='bold')
    
    plt.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight', dpi=100)
    plt.close(fig)
    buf.seek(0)
    return buf

def generate_earthquake_pdf_report(data):
    """
    Generate a comprehensive Earthquake Hazard PDF Report.
    data format:
    {
        'region_name': str,
        'generated_at': str,
        'zone_info': dict,
        'risk_score': dict,
        'hazard_stats': dict,
        'recent_quakes': list,
        'stats': dict
    }
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=1*cm, bottomMargin=1*cm)
    styles = getSampleStyleSheet()
    elements = []
    
    # Styles
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=24, 
                                  spaceAfter=20, alignment=TA_CENTER, textColor=colors.HexColor('#1e293b'))
    subtitle_style = ParagraphStyle('Subtitle', parent=styles['Heading2'], fontSize=14, 
                                     spaceAfter=10, alignment=TA_CENTER, textColor=colors.grey)
    heading_style = ParagraphStyle('Heading', parent=styles['Heading2'], fontSize=16, 
                                    spaceBefore=20, spaceAfter=10, textColor=colors.HexColor('#0ea5e9'))
    body_style = ParagraphStyle('Body', parent=styles['Normal'], fontSize=10, 
                                 spaceAfter=8, alignment=TA_JUSTIFY, leading=14)
    stat_label_style = ParagraphStyle('StatLabel', parent=styles['Normal'], fontSize=8, textColor=colors.grey)
    stat_val_style = ParagraphStyle('StatVal', parent=styles['Normal'], fontSize=12, fontName='Helvetica-Bold')

    # 1. Header
    elements.append(Paragraph("Seismic Hazard & Risk Assessment Report", title_style))
    elements.append(Paragraph(f"Region: {data['region_name']}", subtitle_style))
    elements.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", subtitle_style))
    elements.append(Spacer(1, 20))
    
    # 2. Executive Summary (Risk Score)
    elements.append(Paragraph("Executive Summary", heading_style))
    risk_score = data['risk_score']
    
    summary_text = f"""
    The probabilistic seismic hazard analysis for <b>{data['region_name']}</b> indicates a 
    <b>{data['zone_info'].get('risk', 'Unknown')} Risk</b> level. The region falls under 
    <b>Seismic Zone {data['zone_info'].get('zone', 'Unknown')}</b> according to IS 1893:2025 classification.
    The calculated Seismic Risk Score is <b>{risk_score['total_score']}/100</b>.
    """
    elements.append(Paragraph(summary_text, body_style))
    elements.append(Spacer(1, 10))
    
    # Score Table
    score_data = [
        ['Metric', 'Value', 'Contribution'],
        ['Seismic Zone Factor', f"Zone {data['zone_info'].get('zone')}", f"{risk_score['components']['zone']}"],
        ['Avg PGA (g)', f"{data['hazard_stats'].get('mean_pga', 0):.2f}g", f"{risk_score['components']['hazard']}"],
        ['Exposure Index', "Derived", f"{risk_score['components']['exposure']}"],
        ['Total Risk Score', '', f"{risk_score['total_score']}"]
    ]
    
    t = Table(score_data, colWidths=[6*cm, 5*cm, 4*cm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f1f5f9')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#0f172a')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0')),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#f0f9ff')),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
    ]))
    elements.append(t)
    
    # 3. Seismic Activity
    elements.append(Paragraph("Historical Seismicity Analysis", heading_style))
    
    stats = data['stats']
    elements.append(Paragraph(f"Based on USGS data from {data['time_range']}, the following activity was observed:", body_style))
    
    stat_grid = [
        ['Total Events', 'Max Magnitude', 'Avg Depth'],
        [str(stats['total_events']), str(stats['max_mag']), f"{stats['avg_depth']:.1f} km"]
    ]
    t_stats = Table(stat_grid, colWidths=[5*cm, 5*cm, 5*cm])
    t_stats.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#cbd5e1')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, colors.HexColor('#f8fafc')])
    ]))
    elements.append(t_stats)
    elements.append(Spacer(1, 15))
    
    # Charts
    if data['recent_quakes']:
        mags = [q['magnitude'] for q in data['recent_quakes']]
        mag_img = _create_chart_image('magnitude_hist', mags, "Magnitude Frequency Distribution")
        elements.append(Image(mag_img, width=6*inch, height=3.5*inch))
        
        # Depth scatter
        depth_data = [{'mag': q['magnitude'], 'depth': q['depth']} for q in data['recent_quakes']]
        depth_img = _create_chart_image('depth_scatter', depth_data, "Depth vs Magnitude")
        elements.append(Image(depth_img, width=6*inch, height=3.5*inch))
    else:
        elements.append(Paragraph("No seismic events recorded in the selected period/region.", body_style))

    # 4. Recommendations
    elements.append(PageBreak())
    elements.append(Paragraph("Recommendations & Mitigation", heading_style))
    
    mitigations = [
        "Ensure all new construction complies with IS 1893:2016/2025 standards.",
        "Retrofit critical infrastructure (hospitals, schools) in high-exposure zones.",
        "Implement early warning systems for regions in Zone IV and V.",
        "Conduct regular evacuation drills in high-density urban areas."
    ]
    
    for m in mitigations:
        elements.append(Paragraph(f"• {m}", body_style))
        
    # Metadata
    elements.append(Spacer(1, 40))
    elements.append(Paragraph("Methodology Notes:", ParagraphStyle('SubHeading', parent=body_style, fontName='Helvetica-Bold')))
    notes = """
    - Hazard data derived from GSHAP/Global Models via Google Earth Engine.
    - Historical earthquake catalog sourced from USGS Earthquake Hazards Program.
    - Zonation based on closest major city approximation to IS 1893 map.
    - Risk Score is a composite index of Hazard, Vulnerability, and Exposure.
    """
    elements.append(Paragraph(notes, ParagraphStyle('Small', parent=body_style, fontSize=8, textColor=colors.grey)))
    
    doc.build(elements)
    return buffer.getvalue()
