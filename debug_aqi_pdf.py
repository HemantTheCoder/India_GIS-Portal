import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from services.exports import generate_aqi_pdf_report

dummy_compliance = {
    'aqi_val': 125,
    'aqi_cat': 'Moderate',
    'aqi_color': '#ffff00',
    'dominant': 'PM2.5',
    'details': [
        {'type': 'particles', 'pollutant': 'PM2.5', 'measured': 45.5, 'unit': 'µg/m³', 'limit': 15, 'status': 'Poor'},
        {'type': 'particles', 'pollutant': 'PM10', 'measured': 85.2, 'unit': 'µg/m³', 'limit': 45, 'status': 'Moderate'},
        {'type': 'gas', 'pollutant': 'NO2', 'measured': 0.00012, 'unit': 'mol/m²', 'status': 'N/A'},
    ]
}

dummy_report_data = {
    'city_name': 'Test City',
    'state': 'Test State',
    'date_range': '2024-01-01 to 2024-01-30',
    'pollutants': ['NO2', 'PM2.5'],
    'pollutant_stats': {},
    'compliance': dummy_compliance,
    'time_series': {}
}

print("Generating PDF...")
try:
    pdf_bytes = generate_aqi_pdf_report(dummy_report_data)
    if pdf_bytes:
        print(f"Success! PDF generated. Size: {len(pdf_bytes)} bytes")
        with open("debug_aqi_report.pdf", "wb") as f:
            f.write(pdf_bytes)
        print("Saved to debug_aqi_report.pdf")
    else:
        print("Failed: Generator returned None")
except Exception as e:
    print(f"CRASH: {e}")
