import streamlit as st
import ee
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, date, timedelta

# Reusing existing components
from india_cities import get_states, get_cities, get_city_coordinates
from services.gee_core import (auto_initialize_gee, get_city_geometry,
                               process_shapefile_upload,
                               geojson_file_to_ee_geometry)
from components.ui import apply_enhanced_css, render_page_header, custom_spinner

# Import prediction service
from services.prediction import prepare_time_series_data, train_forecast_model, generate_forecast, calculate_trend_slope
from services.insights import generate_predictive_insights
from services.timelapse import get_ndvi_timelapse, get_aqi_timelapse, get_lst_timelapse

# Import specific data extractors from other modules
# Note: We might need to slightly adapt these or use the logic directly if imports are tricky due to streamlit page structure
# For robustness, I'll reimplement lightweight versions of the time-series extractors here
# to avoid circular dependencies or complex import paths if those pages aren't designed as modules.

st.set_page_config(layout="wide", page_title="AI Predictive Analysis")

auto_initialize_gee()
apply_enhanced_css()

render_page_header("🔮 AI Predictive Analysis",
                   "Forecast environmental trends using Machine Learning")

# --- Helper Functions for Data Extraction ---


def get_ndvi_series(roi, start_date, end_date):
    """Fetches monthly NDVI time series."""

    def calculate_ndvi(image):
        ndvi = image.normalizedDifference(['B8', 'B4']).rename('NDVI')
        return image.addBands(ndvi).set('system:time_start',
                                        image.get('system:time_start'))

    collection = (ee.ImageCollection(
        'COPERNICUS/S2_SR_HARMONIZED').filterBounds(roi).filterDate(
            start_date, end_date).filter(
                ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE',
                             20)).map(calculate_ndvi).select('NDVI'))

    data = collection.mean().reduceRegion(reducer=ee.Reducer.mean(),
                                          geometry=roi,
                                          scale=1000)  # Quick check

    # Timeseries
    def reduce_region(image):
        mean = image.reduceRegion(reducer=ee.Reducer.mean(),
                                  geometry=roi,
                                  scale=100,
                                  maxPixels=1e9,
                                  bestEffort=True)
        return ee.Feature(None, {
            'date': image.date().format('YYYY-MM-dd'),
            'value': mean.get('NDVI')
        })

    data = collection.filter(ee.Filter.calendarRange(
        1, 12,
        'month')).map(reduce_region).filter(ee.Filter.notNull(['value'
                                                               ])).sort('date')
    info = data.getInfo()
    return pd.DataFrame([f['properties'] for f in features] if (
        features := info['features']) else [])


def get_aqi_series(roi, start_date, end_date, pollutant):
    """Fetches pollutant time series for various gases."""

    # Map pollutant to collection and band
    config = {
        'NO2': {
            'id': 'COPERNICUS/S5P/OFFL/L3_NO2',
            'band': 'tropospheric_NO2_column_number_density',
            'scale': 1e6
        },  # mol/m^2 to umol/m^2 approx
        'CO': {
            'id': 'COPERNICUS/S5P/OFFL/L3_CO',
            'band': 'CO_column_number_density',
            'scale': 1
        },
        'SO2': {
            'id': 'COPERNICUS/S5P/OFFL/L3_SO2',
            'band': 'SO2_column_number_density',
            'scale': 1e6
        },
        'O3': {
            'id': 'COPERNICUS/S5P/OFFL/L3_O3',
            'band': 'O3_column_number_density',
            'scale': 1
        },
        'Aerosol': {
            'id': 'COPERNICUS/S5P/OFFL/L3_AER_AI',
            'band': 'absorbing_aerosol_index',
            'scale': 1
        }
    }

    cfg = config.get(pollutant)

    collection = (ee.ImageCollection(cfg['id']).filterBounds(roi).filterDate(
        start_date, end_date).select(cfg['band']))

    def reduce_region(image):
        mean = image.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=roi,
            scale=3000,  # S5P is coarse
            maxPixels=1e9,
            bestEffort=True)
        # Safely handle nulls (clouds/masked pixels)
        val_raw = mean.get(cfg['band'])
        val = ee.Algorithms.If(val_raw,
                               ee.Number(val_raw).multiply(cfg['scale']), None)
        return ee.Feature(None, {
            'date': image.date().format('YYYY-MM-dd'),
            'value': val
        })

    # Limit to one image per week to avoid timeouts on large ranges
    data = collection.filter(ee.Filter.calendarRange(
        1, 31, 'day_of_month')).map(reduce_region).filter(
            ee.Filter.notNull(['value'])).sort('date')
    info = data.getInfo()
    return pd.DataFrame([f['properties'] for f in features] if (
        features := info['features']) else [])


def get_lst_series(roi, start_date, end_date):
    """Fetches LST time series."""
    collection = (
        ee.ImageCollection('MODIS/006/MOD11A1').filterBounds(roi).filterDate(
            start_date, end_date).select('LST_Day_1km'))

    def scale_lst(image):
        val = image.multiply(0.02).subtract(273.15)
        return image.addBands(val, overwrite=True).set(
            'system:time_start', image.get('system:time_start'))

    collection = collection.map(scale_lst)

    def reduce_region(image):
        mean = image.reduceRegion(reducer=ee.Reducer.mean(),
                                  geometry=roi,
                                  scale=1000,
                                  maxPixels=1e9,
                                  bestEffort=True)
        return ee.Feature(
            None, {
                'date': image.date().format('YYYY-MM-dd'),
                'value': mean.get('LST_Day_1km')
            })

    data = collection.map(reduce_region).filter(ee.Filter.notNull(
        ['value'])).sort('date')
    info = data.getInfo()
    return pd.DataFrame([f['properties'] for f in features] if (
        features := info['features']) else [])


def get_lulc_area_series(roi, start_year, end_year):
    """Fetches annual area of ALL LULC classes using group reducer."""

    # Dynamic World Class mapping
    idx_to_class = {
        0: 'Water',
        1: 'Trees',
        2: 'Grass',
        3: 'Flooded Veg',
        4: 'Crops',
        5: 'Shrub',
        6: 'Built Area',
        7: 'Bare Ground',
        8: 'Snow/Ice'
    }

    # Dynamic World is available from mid-2015.
    years = range(max(2016, start_year), end_year + 1)
    results = []

    for year in years:
        start = f"{year}-01-01"
        end = f"{year}-12-31"

        # Get mode image for the year (most common class)
        dw = ee.ImageCollection("GOOGLE/DYNAMICWORLD/V1") \
            .filterBounds(roi) \
            .filterDate(start, end) \
            .select('label') \
            .mode()

        area_image = ee.Image.pixelArea().addBands(dw)

        # Grouped reduction: Sum area grouped by class label
        stats = area_image.reduceRegion(
            reducer=ee.Reducer.sum().group(
                groupField=1,
                groupName='class_idx',
            ),
            geometry=roi,
            scale=100,  # 100m scale for performance
            maxPixels=1e9,
            bestEffort=True)

        # Client side processing of the group list
        groups = stats.get('groups').getInfo()

        # Use mid-year date for plotting
        date_str = f"{year}-06-01"

        # Organize into a row
        row = {'date': date_str}

        if groups:
            for grp in groups:
                c_idx = int(grp['class_idx'])
                area_sqkm = grp['sum'] / 1e6  # m2 to km2
                c_name = idx_to_class.get(c_idx, f"Class_{c_idx}")
                row[c_name] = area_sqkm

        results.append(row)

    return pd.DataFrame(results).fillna(0)


# --- Sidebar ---
with st.sidebar:
    st.header("⚙️ Data Config")

    # Location
    st.subheader("📍 Location")

    location_mode = st.radio("Input Method",
                             ["City Selection", "Upload Shapefile/GeoJSON"],
                             key="pred_loc_mode")

    selected_city = None
    selected_state = None
    city_coords = None
    uploaded_geometry = None
    uploaded_center = None

    if location_mode == "City Selection":
        states = get_states()
        selected_state = st.selectbox("Select State", states, key="pred_state")
        cities = get_cities(selected_state)
        selected_city = st.selectbox("Select City", cities, key="pred_city")
        if selected_city:
            city_coords = get_city_coordinates(selected_state, selected_city)

    else:
        st.markdown("##### Upload Area")
        st.caption("Supported: .shp (zip), .geojson")
        uploaded_files = st.file_uploader("Choose files",
                                          accept_multiple_files=True,
                                          key="pred_upload")

        if uploaded_files:
            geojson_files = [
                f for f in uploaded_files
                if f.name.endswith(('.geojson', '.json'))
            ]
            zip_files = [f for f in uploaded_files if f.name.endswith('.zip')]
            shp_files = [f for f in uploaded_files if f.name.endswith('.shp')]

            if geojson_files:
                geom, center, _, error = geojson_file_to_ee_geometry(
                    geojson_files[0])
                if error: st.error(error)
                else:
                    uploaded_geometry = geom
                    uploaded_center = center
                    st.success("✅ GeoJSON Loaded")
                    selected_city = "Custom Area"

            elif zip_files or shp_files:
                geom, center, _, error = process_shapefile_upload(uploaded_files)
                if error: st.error(error)
                else:
                    uploaded_geometry = geom
                    uploaded_center = center
                    st.success("✅ Shapefile Loaded")
                    selected_city = "Custom Area"

    st.divider()

    # Prediction Target
    st.subheader("🎯 Prediction Target")
    target_category = st.selectbox("Category", [
        "Air Quality (AQI)", "Land Cover (LULC)", "Urban Heat (LST)",
        "Vegetation (NDVI)"
    ])

    target_param = ""
    target_unit = ""

    if target_category == "Air Quality (AQI)":
        target_param = st.selectbox("Pollutant",
                                    ["NO2", "CO", "SO2", "O3", "Aerosol"])
        if target_param == "NO2" or target_param == "SO2":
            target_unit = "µmol/m²"
        elif target_param == "CO":
            target_unit = "mol/m² - Raw"
        elif target_param == "O3":
            target_unit = "mol/m²"
        else:
            target_unit = "Index"

    elif target_category == "Land Cover (LULC)":
        st.markdown("Analyzing **ALL** land cover classes.")
        target_unit = "sq km"

    elif target_category == "Urban Heat (LST)":
        target_unit = "°C"

    elif target_category == "Vegetation (NDVI)":
        target_unit = "Index"

    st.divider()

    # Timeline
    st.subheader("⏳ Time Machine")

    col_t1, col_t2 = st.columns(2)
    with col_t1:
        train_start_year = st.number_input("Train From", 2017, 2023, 2018)
    with col_t2:
        predict_until_year = st.number_input("Predict Until", 2025, 2030, 2026)

    model_choice = st.selectbox("Algorithm",
                                ["Random Forest", "Linear Regression"])

    run_btn = st.button("🚀 Train & Predict",
                        type="primary",
                        use_container_width=True)

# --- Main Content ---

if run_btn:
    if not st.session_state.get("gee_initialized", False):
        st.error(
            "Google Earth Engine not initialized. Please check your secrets.")
        st.stop()

    roi = None

    if location_mode == "City Selection":
        if not selected_city:
            st.error("Please select a city")
            st.stop()
        lat_lon = get_city_coordinates(selected_state, selected_city)
        if not lat_lon:
            st.error("Could not find coordinates")
            st.stop()
        roi = get_city_geometry(lat_lon["lat"], lat_lon["lon"])

    else:
        if not uploaded_geometry:
            st.error("Please upload a valid geometry file")
            st.stop()
        roi = uploaded_geometry

    # Dates
    start_date = f"{train_start_year}-01-01"
    end_date = datetime.now().strftime('%Y-%m-%d')

    # Calc forecast days
    target_date = date(predict_until_year, 12, 31)
    current_date = date.today()
    forecast_days = (target_date - current_date).days

    if forecast_days <= 0:
        st.error("Target year must be in the future!")
        st.stop()

    with st.status("Training Predictive Models...", expanded=True) as status:
        st.write(f"fetching data for {selected_city}...")
        try:
            df = pd.DataFrame()
            title = ""
            is_multi_class = False

            # --- DATA FETCHING ---
            if target_category == "Urban Heat (LST)":
                df = get_lst_series(roi, start_date, end_date)
                title = "Land Surface Temperature"

            elif target_category == "Vegetation (NDVI)":
                df = get_ndvi_series(roi, start_date, end_date)
                title = "Vegetation Health (NDVI)"

            elif target_category == "Air Quality (AQI)":
                df = get_aqi_series(roi, start_date, end_date, target_param)
                title = f"Air Quality: {target_param}"

            elif target_category == "Land Cover (LULC)":
                st.write("Calculating annual class areas (multi-class)...")
                df = get_lulc_area_series(roi, train_start_year,
                                          datetime.now().year)
                title = "Land Cover Composition"
                is_multi_class = True

            if df.empty:
                status.update(label="Analysis Failed: No Data", state="error")
                st.error("No data found. Try a different parameter or location.")
                st.stop()

            # --- PREDICTION LOOP ---
            st.write(f"🧠 Training {model_choice} models...")

            final_forecast_df = pd.DataFrame()
            model_metrics = {}

            # Identify columns to predict
            if is_multi_class:
                value_cols = [c for c in df.columns if c != 'date']
            else:
                value_cols = ['value']

            for col in value_cols:
                # Prepare data for this specific column
                sub_df = df[['date', col]].rename(columns={col: 'value'})

                # Simple prep
                X, y, last_date, features_list = prepare_time_series_data(
                    sub_df, 'date', 'value')

                # Train
                model_type_code = 'random_forest' if model_choice == "Random Forest" else 'linear'
                model, metrics = train_forecast_model(X,
                                                      y,
                                                      model_type=model_type_code)

                # Store Metrics
                if 'type' in metrics:
                    model_metrics[col] = f"{metrics['r2']:.2f} ({metrics['type']})"
                else:
                    model_metrics[col] = f"{metrics['r2']:.2f}"

                # Forecast
                f_df = generate_forecast(model,
                                         last_date,
                                         features_list,
                                         periods=forecast_days)
                f_df = f_df.rename(columns={'predicted_value': col})

                if final_forecast_df.empty:
                    final_forecast_df = f_df[['date']]

                final_forecast_df[col] = f_df[col]

            # --- VISUALIZATION ---

            # Parse metrics for display
            avg_r2_val = 0
            try:
                # Extract just the float part for average
                r2_floats = [
                    float(v.split(' ')[0]) for v in model_metrics.values()
                ]
                avg_r2_val = sum(r2_floats) / len(r2_floats)
            except:
                pass
            
            status.update(label=f"Prediction Complete! (Confidence: {avg_r2_val:.2f})", state="complete", expanded=False)
            st.success(f"Analysis Complete! Average Confidence: {avg_r2_val:.2f}")

        except Exception as e:
            status.update(label="Analysis Failed", state="error", expanded=True)
            st.error(f"Error: {str(e)}")

        # --- TREND TIMELAPSE ---
        st.markdown("### 🎞️ Historical Trend Timelapse")
        with custom_spinner("Generating Trend Timelapse..."):
            tl_url, tl_error = None, None
            tl_start = start_date
            tl_end = end_date
            
            if target_category == "Vegetation (NDVI)" or target_category == "Land Cover (LULC)":
                tl_url, tl_error = get_ndvi_timelapse(roi, tl_start, tl_end, frequency='Yearly')
            elif target_category == "Urban Heat (LST)":
                tl_url, tl_error = get_lst_timelapse(roi, tl_start, tl_end, frequency='Yearly')
            elif target_category == "Air Quality (AQI)":
                # Use simple mapping for AQI param if available
                tl_param = target_param if target_param in ['NO2', 'SO2', 'O3', 'CO', 'Aerosol'] else 'NO2'
                tl_url, tl_error = get_aqi_timelapse(roi, tl_start, tl_end, parameter=tl_param, frequency='Monthly')
            
            if tl_url:
                st.video(tl_url, autoplay=True, loop=True)
                st.caption(f"Historical Trend ({tl_start} - {tl_end})")
                with open(tl_url, 'rb') as v:
                    st.download_button("📥 Download Video", data=v, file_name="trend_timelapse.mp4", mime="video/mp4", key="dl_pred_tl_video")
            elif tl_error:
                st.warning(f"Could not generate timelapse: {tl_error}")
            else:
                st.info("Timelapse not available for this parameter.")
        
        st.markdown("---")

        if is_multi_class:
            # --- LULC VISUALIZATION (Comparison Bar Chart) ---

            last_hist_row = df.iloc[-1]
            last_pred_row = final_forecast_df.iloc[-1]

            # Prepare data for Bar Chart
            bar_data = []

            # Define key classes to show
            classes = [c for c in df.columns if c != 'date']

            current_year = pd.to_datetime(last_hist_row['date']).year
            target_year = pd.to_datetime(last_pred_row['date']).year

            for cls in classes:
                # Current
                bar_data.append({
                    'Class': cls,
                    'Area (sq km)': last_hist_row[cls],
                    'Year': str(current_year)
                })
                # Future
                bar_data.append({
                    'Class': cls,
                    'Area (sq km)': last_pred_row[cls],
                    'Year': str(target_year)
                })

            bar_df = pd.DataFrame(bar_data)

            # Create Clustered Bar Chart
            fig = px.bar(
                bar_df,
                x="Class",
                y="Area (sq km)",
                color="Year",
                barmode="group",
                title=f"Land Cover Change: {current_year} vs {target_year}",
                text_auto='.1f',
                color_discrete_map={
                    str(current_year): '#3b82f6',
                    str(target_year): '#10b981'
                },
                template="plotly_dark",
                height=500)

            fig.update_layout(yaxis_title="Area (sq km)", xaxis_title=None)

            st.plotly_chart(fig, use_container_width=True)

            # Metric Cards
            st.markdown("### 📈 Key Changes")
            cols = st.columns(4)
            key_classes = ['Built Area', 'Water', 'Trees', 'Crops']
            idx = 0
            for cls in key_classes:
                if cls in df.columns:
                    curr = last_hist_row[cls]
                    fut = last_pred_row[cls]
                    delta = fut - curr
                    delta_pct = (delta / curr) * 100 if curr > 0 else 0

                    with cols[idx % 4]:
                        st.metric(cls, f"{fut:.1f} km²",
                                  f"{delta:+.1f} km² ({delta_pct:+.1f}%)")
                    idx += 1

            # Show detailed fit info
            fit_details = []
            for k, v in model_metrics.items():
                if 'poly' in str(v):
                    fit_details.append(f"{k}: {v}")

            fit_str = " | ".join(fit_details[:3])  # Show top 3
            if len(fit_details) > 3: fit_str += "..."

            st.caption(
                f"📈 Trend Fit Confidence: {avg_r2_val:.2f} (Auto-Degree Selection). Details: {fit_str}"
            )

            # Auto-generate PDF (LULC)
            st.toast("Generating PDF Report...", icon="📄")
            try:
                # Prepare data for PDF
                pdf_metrics = {}
                for cls in classes:
                    curr_v = last_hist_row[cls]
                    fut_v = last_pred_row[cls]
                    pdf_metrics[cls] = {
                        'current': curr_v,
                        'future': fut_v,
                        'delta': fut_v - curr_v,
                        'pct':
                        ((fut_v - curr_v) / curr_v) * 100 if curr_v else 0
                    }

                # Prepare time series for plotting
                f_data = []
                # Add future
                for _, row in final_forecast_df.iterrows():
                    f_data.append({
                        'date': row['date'],
                        'Built Area': row.get('Built Area', 0),
                        'type': 'predicted'
                    })
                # Add history
                for _, row in df.iterrows():
                    f_data.append({
                        'date': row['date'],
                        'Built Area': row.get('Built Area', 0),
                        'type': 'historical'
                    })

                # Generate Insights for the most changed class
                max_change_cls = None
                max_change_val = 0
                for cls, m in pdf_metrics.items():
                    if abs(m['delta']) > abs(max_change_val):
                        max_change_val = m['delta']
                        max_change_cls = cls
                
                insight_stats = {
                    'target_name': max_change_cls if max_change_cls else 'Land Cover',
                    'current_value': pdf_metrics[max_change_cls]['current'] if max_change_cls else 0,
                    'future_value': pdf_metrics[max_change_cls]['future'] if max_change_cls else 0,
                    'trend_percentage': pdf_metrics[max_change_cls]['pct'] if max_change_cls else 0
                }
                insights = generate_predictive_insights(insight_stats)

                from services.exports import generate_predictive_pdf_report
                pdf_bytes = generate_predictive_pdf_report({
                    'current_year':
                    current_year,
                    'target_year':
                    target_year,
                    'metrics':
                    pdf_metrics,
                    'confidence':
                    f"{avg_r2_val:.2f}",
                    'forecast_data':
                    f_data,
                    'insights': insights
                })

                if pdf_bytes:
                    st.session_state.pred_pdf = pdf_bytes
            except Exception as e:
                print(f"PDF Auto-gen failed: {e}")

            # Download
            csv_p = final_forecast_df.to_csv(index=False).encode('utf-8')
            col_d1, col_d2 = st.columns(2)
            col_d1.download_button("📥 CSV Data",
                                   csv_p,
                                   "forecast.csv",
                                   "text/csv",
                                   use_container_width=True)

            with col_d2:
                if st.session_state.get('pred_pdf'):
                    st.download_button(
                        "📥 Download PDF",
                        st.session_state.pred_pdf,
                        "prediction_report.pdf",
                        "application/pdf",
                        use_container_width=True,
                        key=
                        f"dl_pred_pdf_{datetime.now().strftime('%Y%m%d%H%M%S')}"
                    )
                else:
                    st.caption("PDF generating...")

        else:
            # Single Variable Plot (Existing Logic)
            hist_df = df.copy()
            pred_df = final_forecast_df.copy()
            pred_df = pred_df.rename(columns={'value': 'predicted_value'})

            # Metrics
            current_val = hist_df['value'].iloc[-1]
            future_val = pred_df['predicted_value'].iloc[-1]
            change_pct = ((future_val - current_val) /
                          current_val) * 100 if current_val != 0 else 0

            # Use the already parsed average R2
            avg_r2 = avg_r2_val

            # Display
            col_m1, col_m2, col_m3 = st.columns(3)
            col_m1.metric("Current Value", f"{current_val:.2f} {target_unit}")
            col_m2.metric(f"Projection ({predict_until_year})",
                          f"{future_val:.2f} {target_unit}",
                          f"{change_pct:.1f}%")
            col_m3.metric("Model Confidence", f"{avg_r2:.2f}")

            fig = go.Figure()

            # Historical
            fig.add_trace(
                go.Scatter(x=hist_df['date'],
                           y=hist_df['value'],
                           mode='lines',
                           name='Historical',
                           line=dict(color='#00f3ff', width=3)))

            # Forecast (Dashed)
            fig.add_trace(
                go.Scatter(x=pred_df['date'],
                           y=pred_df['predicted_value'],
                           mode='lines',
                           name='Forecast',
                           line=dict(color='#fb923c', width=3, dash='dash')))

            fig.update_layout(title=f"AI Forecast: {title}",
                              xaxis_title="Timeline",
                              yaxis_title=f"{target_unit}",
                              template="plotly_dark",
                              paper_bgcolor='rgba(0,0,0,0)',
                              plot_bgcolor='rgba(0,0,0,0)',
                              hovermode="x unified",
                              height=500)

            st.plotly_chart(fig, use_container_width=True)

            st.markdown(f"""
            <div class="info-box">
                <b>AI Insight:</b> {title} is projected to <b>{'increase' if change_pct > 0 else 'decrease'}</b> 
                by {abs(change_pct):.1f}% over the next {forecast_days//365} years based on current trends.
            </div>
            """,
                        unsafe_allow_html=True)

            # Auto-generate PDF (Single Variable)
            st.toast("Generating PDF Report...", icon="📄")
            try:
                f_data = []
                for _, row in hist_df.iterrows():
                    f_data.append({
                        'date': row['date'],
                        title: row['value'],
                        'type': 'historical'
                    })
                for _, row in pred_df.iterrows():
                    f_data.append({
                        'date': row['date'],
                        title: row['predicted_value'],
                        'type': 'predicted'
                    })

                insight_stats = {
                    'target_name': title,
                    'current_value': current_val,
                    'future_value': future_val,
                    'trend_percentage': change_pct
                }
                insights = generate_predictive_insights(insight_stats)

                from services.exports import generate_predictive_pdf_report
                pdf_bytes_s = generate_predictive_pdf_report({
                    'current_year':
                    pd.to_datetime(hist_df['date'].max()).year,
                    'target_year':
                    predict_until_year,
                    'metrics': {
                        title: {
                            'current': current_val,
                            'future': future_val,
                            'delta': future_val - current_val,
                            'pct': change_pct
                        }
                    },
                    'confidence':
                    f"{avg_r2:.2f}",
                    'forecast_data':
                    f_data,
                    'insights': insights
                })
                if pdf_bytes_s:
                    st.session_state.pred_pdf_s = pdf_bytes_s
            except Exception as e:
                print(f"PDF Auto-gen failed: {e}")

            # Download
            csv_p = pred_df.to_csv(index=False).encode('utf-8')
            col_d1, col_d2 = st.columns(2)
            col_d1.download_button("📥 CSV Data",
                                   csv_p,
                                   "forecast.csv",
                                   "text/csv",
                                   use_container_width=True)

            with col_d2:
                if st.session_state.get('pred_pdf_s'):
                    st.download_button(
                        "📥 Download PDF",
                        st.session_state.pred_pdf_s,
                        "prediction_report.pdf",
                        "application/pdf",
                        use_container_width=True,
                        key=
                        f"dl_pred_pdf_s_{datetime.now().strftime('%Y%m%d%H%M%S')}"
                    )
                else:
                    st.caption("PDF generating...")



else:
    # Landing State
    st.markdown("""
    <div class="animate-fade-in" style="text-align: center; padding: 4rem 2rem;">
        <h2>🤖 Environmental Time Machine</h2>
        <p style="color: #cbd5e1; font-size: 1.1rem; max-width: 600px; margin: 0 auto;">
            Select any pollutant or land cover class, define your timeline, and let the AI predict the future of your city.
        </p>
    </div>

    <div class="row" style="display: flex; gap: 1rem; justify-content: center; flex-wrap: wrap;">
        <div class="feature-card" style="width: 280px; text-align: center;">
            <div style="font-size: 2rem;">🌫️</div>
            <h4>Multi-Gas AQI</h4>
            <p>NO₂, SO₂, CO, Ozone & Aerosols</p>
        </div>
        <div class="feature-card" style="width: 280px; text-align: center;">
            <div style="font-size: 2rem;">🏗️</div>
            <h4>LULC Quantification</h4>
            <p>Predict growth of Built Area or Water Bodies in sq km.</p>
        </div>
        <div class="feature-card" style="width: 280px; text-align: center;">
            <div style="font-size: 2rem;">⏳</div>
            <h4>Custom Horizon</h4>
            <p>Train from 2017... Predict until 2030.</p>
        </div>
    </div>
    """,
                unsafe_allow_html=True)
