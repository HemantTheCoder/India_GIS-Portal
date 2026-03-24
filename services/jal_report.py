"""
services/jal_report.py
Jal-AI Community Action & Disaster Preparedness Report – PDF Generator
Uses reportlab (already a project dependency).
"""

import io
from datetime import datetime

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


# ─────────────────────────────────────────────────────────────
# Helpers – Charts
# ─────────────────────────────────────────────────────────────

def _risk_gauge_image(score: float) -> io.BytesIO:
    """True semi-circular gauge chart using Wedge patches to prevent corruption."""
    from matplotlib.patches import Wedge
    fig, ax = plt.subplots(figsize=(4, 2.5), facecolor="#0f172a")
    ax.set_facecolor("#0f172a")

    # Define accurate color wedges (Green -> Lime -> Amber -> Orange -> Red)
    sections = [
        (0,  20,  "#22c55e"), # Green
        (20, 40,  "#84cc16"), # Lime
        (40, 65,  "#f59e0b"), # Amber
        (65, 80,  "#f97316"), # Orange
        (80, 100, "#ef4444"), # Red
    ]

    for lo, hi, col in sections:
        # angles in degrees: 180 (left) to 0 (right)
        start_angle = 180 - (lo / 100 * 180)
        end_angle   = 180 - (hi / 100 * 180)
        wedge = Wedge((0, 0), 1.0, end_angle, start_angle, width=0.35, color=col, alpha=0.9, ec="none")
        ax.add_patch(wedge)

    # Needle/Arrow
    # angle_rad: 0 (right) to pi (left). We want 100 score -> 0 rad, 0 score -> pi rad.
    angle_rad = np.pi - (score / 100 * np.pi)
    
    # Draw arrow from center to outer ring
    ax.annotate("", 
                xy=(0.9 * np.cos(angle_rad), 0.9 * np.sin(angle_rad)),
                xytext=(0, 0),
                arrowprops=dict(arrowstyle="-|>", color="white", lw=2.5, mutation_scale=20, shrinkA=0, shrinkB=0))
    
    # Center cap circle
    ax.add_patch(plt.Circle((0, 0), 0.08, color="white", zorder=15))

    # Text positioning - move score slightly lower to avoid needle overlap
    if score >= 65:
        label_col = "#ef4444"
    elif score >= 40:
        label_col = "#f59e0b"
    elif score >= 20:
        label_col = "#facc15" # Yellow/Lime
    else:
        label_col = "#22c55e"

    # Big score text (Positioned to ensure no collision)
    ax.text(0, -0.25, f"{score:.0f}/100", fontsize=24, ha="center", va="center",
            color=label_col, fontweight="900")
    ax.text(0, -0.42, "AI DISASTER RISK SCORE", fontsize=8, ha="center",
            color="#94a3b8", fontweight="bold")
    
    ax.set_xlim(-1.1, 1.1)
    ax.set_ylim(-0.6, 1.1) 
    ax.axis("off")
    plt.tight_layout(pad=0.2)

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=140, bbox_inches="tight", facecolor="#0f172a")
    plt.close(fig)
    buf.seek(0)
    return buf


def _sensor_bar_image(data: dict) -> io.BytesIO:
    """Horizontal bar chart for sensor contribution weights."""
    labels = list(data.keys())
    values = list(data.values())

    cmap = ["#22c55e" if v < 33 else "#f59e0b" if v < 66 else "#ef4444" for v in values]

    fig, ax = plt.subplots(figsize=(5, 3), facecolor="#0f172a")
    ax.set_facecolor("#1e293b")
    bars = ax.barh(labels, values, color=cmap, height=0.6, edgecolor="none")
    for bar, val in zip(bars, values):
        ax.text(bar.get_width() + 1, bar.get_y() + bar.get_height() / 2,
                f"{val:.1f}", va="center", color="white", fontsize=8)
    ax.set_xlim(0, max(values) * 1.2 + 5)
    ax.set_xlabel("Contribution Weight (%)", color="#94a3b8", fontsize=8)
    ax.tick_params(colors="white", labelsize=8)
    ax.spines[:].set_visible(False)
    plt.tight_layout(pad=0.5)

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=120, bbox_inches="tight", facecolor="#0f172a")
    plt.close(fig)
    buf.seek(0)
    return buf


# ─────────────────────────────────────────────────────────────
# Main PDF Generator
# ─────────────────────────────────────────────────────────────

def generate_jal_pdf(
    city_name: str,
    analysis_date: str,
    risk_score: float,
    action_tier: str,
    water_area: float,
    flooded_km: float,
    rain_mean: float,
    rain_max: float,
    jrc_change: float,
    mean_elev: float,
    mean_slope: float,
    lst_mean: float,
    ndvi_mean: float,
    drought_label: str,
    actions: list,
    buffer_km: int = 15,
) -> bytes:
    """
    Generates a professional Jal-AI Disaster Preparedness PDF report.
    Returns raw PDF bytes.
    """
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image,
        HRFlowable
    )

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        topMargin=1.2 * cm, bottomMargin=1.2 * cm,
        leftMargin=1.5 * cm, rightMargin=1.5 * cm,
    )

    styles = getSampleStyleSheet()

    def S(name, parent="Normal", **kw):
        return ParagraphStyle(name, parent=styles[parent], **kw)

    BLUE  = colors.HexColor("#0ea5e9")
    SLATE = colors.HexColor("#1e293b")
    MUTED = colors.HexColor("#64748b")
    GREEN = colors.HexColor("#22c55e")
    RED   = colors.HexColor("#ef4444")
    AMBER = colors.HexColor("#f59e0b")

    if risk_score >= 65:
        tier_col = RED
    elif risk_score >= 40:
        tier_col = AMBER
    elif risk_score >= 20:
        tier_col = colors.HexColor("#84cc16") # Lime/WATCH
    else:
        tier_col = GREEN

    title_style    = S("T1", "Heading1", fontSize=22, alignment=TA_CENTER, textColor=BLUE, spaceAfter=2)
    subtitle_style = S("T2", "Normal",  fontSize=10, alignment=TA_CENTER, textColor=MUTED, spaceAfter=12)
    h2_style       = S("H2", "Heading2", fontSize=14, textColor=BLUE, spaceBefore=12, spaceAfter=6, fontName="Helvetica-Bold")
    h3_style       = S("H3", "Heading3", fontSize=11, textColor=SLATE, spaceBefore=8, spaceAfter=4)
    body_style     = S("BD", "Normal",  fontSize=9.5, leading=14, alignment=TA_JUSTIFY, spaceAfter=6)
    bullet_style   = S("BL", "Normal",  fontSize=9.5, leftIndent=15, spaceAfter=4, leading=14)
    small_style    = S("SM", "Normal",  fontSize=8, textColor=MUTED)
    badge_style    = S("BG", "Normal",  fontSize=16, alignment=TA_CENTER, textColor=tier_col, fontName="Helvetica-Bold")

    def hr():
        return HRFlowable(width="100%", thickness=0.8, color=colors.HexColor("#cbd5e1"), spaceBefore=10, spaceAfter=10)

    def metric_table(rows):
        tbl = Table(rows, colWidths=[6.5 * cm, 10.5 * cm])
        tbl.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f0f9ff")),
            ("FONTNAME",   (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTSIZE",   (0, 0), (-1, -1), 9.5),
            ("GRID",       (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ("PADDING",    (0, 0), (-1, -1), 8),
            ("VALIGN",     (0, 0), (-1, -1), "MIDDLE"),
        ]))
        return tbl

    elems = []

    # ── Cover Header ──────────────────────────────────────────
    elems.append(Paragraph("💧 Jal-AI", title_style))
    elems.append(Paragraph("AI Disaster Preparedness & Community Water Resilience Intelligence", subtitle_style))
    elems.append(hr())

    elems.append(metric_table([
        ["Location / AOI",   city_name],
        ["Analysis Date",    analysis_date],
        ["Coverage Radius",  f"{buffer_km} km"],
        ["Platform",         "India GIS Portal | Jal-AI v2.0 Final (Hackathon 2026)"],
        ["Data Integrity",   "Multi-Sensor Satellite Verification Active"],
    ]))

    elems.append(Spacer(1, 15))

    # ── Risk Gauge ────────────────────────────────────────────
    elems.append(Paragraph(f"Early Action Tier: {action_tier}", badge_style))
    elems.append(Spacer(1, 8))
    
    gauge_buf = _risk_gauge_image(risk_score)
    gauge_img = Image(gauge_buf, width=10 * cm, height=6 * cm)
    gauge_img.hAlign = "CENTER"
    elems.append(gauge_img)
    elems.append(Spacer(1, 5))
    elems.append(hr())

    # ── Section 1: Dashboard Sensors ───────────────────────────
    elems.append(Paragraph("1. Real-time Multi-Satellite Observations", h2_style))
    
    sensor_rows = [
        ["Satellite Sensor", "Metric Value", "Disaster Context"],
        ["Sentinel-1 SAR",   f"{flooded_km:.2f} km² Flooded", "🟢 Stable" if flooded_km < 0.01 else "🔴 Inundation Detected"],
        ["NASA GPM RAIN",    f"{rain_mean:.1f} mm (30d mean)", "🟠 Elevated" if rain_mean > 150 else "✅ Normal"],
        ["Sentinel-2 NDWI",  f"{water_area:.2f} km² Surface", "⚠ Stressed" if water_area < 2 else "✅ Sufficient"],
        ["MODIS LST",        f"{lst_mean:.1f}°C Day Mean",    "🔴 Extreme Heat" if lst_mean > 42 else "✅ Normal"],
        ["MODIS NDVI",       f"{ndvi_mean:.3f} (Drought)",    drought_label],
    ]
    stbl = Table(sensor_rows, colWidths=[5 * cm, 6 * cm, 6 * cm])
    stbl.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, 0),  BLUE),
        ("TEXTCOLOR",    (0, 0), (-1, 0),  colors.white),
        ("FONTNAME",     (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("GRID",         (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("PADDING",      (0, 0), (-1, -1), 6),
        ("FONTSIZE",     (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
    ]))
    elems.append(stbl)
    
    # ── Section 2: Contribution ───────────────────────────────
    elems.append(Spacer(1, 10))
    sensor_weights = {
        "Flood (SAR)": min(100, flooded_km / 5 * 100),
        "Rain (GPM)": min(100, rain_mean / 400 * 100),
        "Deficit (NDWI)": max(0, (1 - water_area / 5) * 100),
        "Heat (LST)": min(100, max(0, (lst_mean - 32) / 15 * 100)),
        "Drought (NDVI)": max(0, (1 - ndvi_mean / 0.5) * 100),
    }
    bar_img = Image(_sensor_bar_image(sensor_weights), width=12 * cm, height=6 * cm)
    bar_img.hAlign = "CENTER"
    elems.append(bar_img)
    elems.append(hr())

    # ── Section 3: Advisory ──────────────────────────────────
    elems.append(Paragraph("2. Community Early Action Advisory (W-SHG)", h2_style))
    
    # Simple summary sentence
    summary_text = f"Current AI Risk Score for {city_name} is {risk_score:.0f}/100. "
    if risk_score >= 65:
        summary_text += "<b>CRITICAL:</b> Execute primary disaster response protocols immediately. Evacuate low-lying vulnerability corridors."
    elif risk_score >= 40:
        summary_text += "<b>WARNING:</b> High runoff and contamination risk. Pre-position water storage kits for SHG network."
    else:
        summary_text += "<b>STABLE:</b> No immediate threat detected. Continue standard resilience training."
    
    elems.append(Paragraph(summary_text, body_style))
    elems.append(Spacer(1, 5))
    
    elems.append(Paragraph("Strategic Actions for Local Women SHGs:", h3_style))
    for i, a in enumerate(actions, 1):
        elems.append(Paragraph(f"{i}. {a}", bullet_style))

    # ── Footer ────────────────────────────────────────────────
    elems.append(Spacer(1, 20))
    elems.append(HRFlowable(width="100%", thickness=0.5, color=MUTED))
    
    # Use center style for footer text
    footer_style = S("FT", "Normal", fontSize=8, textColor=MUTED, alignment=TA_CENTER)
    elems.append(Paragraph(
        "Jal-AI: Water Resilience Intelligence · Powered by Google Earth Engine · v2.0 Final Build",
        footer_style
    ))

    doc.build(elems)
    buf.seek(0)
    return buf.read()


def format_jal_whatsapp_alert(
    city_name: str,
    analysis_date: str,
    action_tier: str,
    risk_score: float,
    flooded_km: float,
    rain_mean: float,
    water_area: float,
    drought_label: str,
    actions: list,
) -> str:
    """Formats a concise, WhatsApp-ready disaster alert message."""
    lines = [
        f"💧 *JAL-AI DISASTER ALERT*",
        f"📍 Location: *{city_name}*",
        f"🚦 Status: *{action_tier}*",
        f"🧠 AI Risk Score: *{risk_score:.0f}/100*",
        f"",
        f"📊 *Key Indicators:*",
        f"  🌊 Surface Water: {water_area:.2f} km²",
        f"  📡 Flooded Area (SAR): {flooded_km:.2f} km²",
        f"  🌧️ 30d Rainfall: {rain_mean:.1f} mm",
        f"  🌿 Drought Index: {drought_label}",
        f"",
        f"📋 *Recommended SHG Actions:*",
    ]
    for i, action in enumerate(actions[:3], 1):
        lines.append(f"  {i}. {action}")

    lines += [
        f"",
        f"⚡ *Powered by Jal-AI | Hackathon 2026*",
    ]
    return "\n".join(lines)
