import ee
import numpy as np
from datetime import datetime
from scipy import stats

LULC_CLASSES = {
    0: {
        "name": "Water",
        "color": "#419bdf"
    },
    1: {
        "name": "Trees",
        "color": "#397d49"
    },
    2: {
        "name": "Grass",
        "color": "#88b053"
    },
    3: {
        "name": "Flooded Vegetation",
        "color": "#7a87c6"
    },
    4: {
        "name": "Crops",
        "color": "#e49635"
    },
    5: {
        "name": "Shrub & Scrub",
        "color": "#dfc35a"
    },
    6: {
        "name": "Built Area",
        "color": "#c4281b"
    },
    7: {
        "name": "Bare Ground",
        "color": "#a59b8f"
    },
    8: {
        "name": "Snow & Ice",
        "color": "#b39fe1"
    },
}


def get_historical_lulc_data(geometry, start_year, end_year, resolution=30):
    yearly_data = {}

    for year in range(start_year, end_year + 1):
        try:
            start_date = f"{year}-01-01"
            end_date = f"{year}-12-31"

            collection = (ee.ImageCollection(
                "GOOGLE/DYNAMICWORLD/V1").filterBounds(geometry).filterDate(
                    start_date, end_date))

            if collection.size().getInfo() == 0:
                continue

            classification = collection.select("label")
            mode_lulc = classification.mode().clip(geometry)

            stats_result = mode_lulc.reduceRegion(
                reducer=ee.Reducer.frequencyHistogram(),
                geometry=geometry,
                scale=resolution,
                maxPixels=1e9)

            histogram = stats_result.get("label").getInfo()
            if histogram is None:
                continue

            total_pixels = sum(histogram.values())
            year_stats = {}

            for class_id, count in histogram.items():
                class_id = int(float(class_id))
                if class_id in LULC_CLASSES:
                    percentage = (count / total_pixels) * 100
                    year_stats[LULC_CLASSES[class_id]["name"]] = round(
                        percentage, 2)

            yearly_data[year] = year_stats

        except Exception as e:
            print(f"Error processing year {year}: {e}")
            continue

    return yearly_data


def get_historical_index_data(geometry,
                              start_year,
                              end_year,
                              satellite="Sentinel-2",
                              indices=None):
    if indices is None:
        indices = ["NDVI", "NDWI", "NDBI", "EVI", "SAVI"]

    yearly_data = {idx: {} for idx in indices}

    for year in range(start_year, end_year + 1):
        try:
            start_date = f"{year}-01-01"
            end_date = f"{year}-12-31"

            if satellite == "Sentinel-2":
                collection = (ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
                              .filterBounds(geometry).filterDate(
                                  start_date, end_date).filter(
                                      ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE",
                                                   20)))

                if collection.size().getInfo() == 0:
                    continue

                image = collection.median().clip(geometry)

                for idx in indices:
                    try:
                        if idx == "NDVI":
                            index_img = image.normalizedDifference(
                                ["B8", "B4"]).rename(idx)
                        elif idx == "NDWI":
                            index_img = image.normalizedDifference(
                                ["B3", "B8"]).rename(idx)
                        elif idx == "NDBI":
                            index_img = image.normalizedDifference(
                                ["B11", "B8"]).rename(idx)
                        elif idx == "EVI":
                            index_img = image.expression(
                                "2.5 * ((NIR - RED) / (NIR + 6 * RED - 7.5 * BLUE + 1))",
                                {
                                    "NIR": image.select("B8"),
                                    "RED": image.select("B4"),
                                    "BLUE": image.select("B2")
                                }).rename(idx)
                        elif idx == "SAVI":
                            index_img = image.expression(
                                "((NIR - RED) / (NIR + RED + 0.5)) * 1.5", {
                                    "NIR": image.select("B8"),
                                    "RED": image.select("B4")
                                }).rename(idx)
                        else:
                            continue

                        mean_val = index_img.reduceRegion(
                            reducer=ee.Reducer.mean(),
                            geometry=geometry,
                            scale=30,
                            maxPixels=1e9).get(idx).getInfo()

                        if mean_val is not None:
                            yearly_data[idx][year] = round(mean_val, 4)
                    except Exception as e:
                        print(f"Error calculating {idx} for {year}: {e}")
                        continue
            else:
                collection = (ee.ImageCollection("LANDSAT/LC08/C02/T1_L2").
                              filterBounds(geometry).filterDate(
                                  start_date, end_date).filter(
                                      ee.Filter.lt("CLOUD_COVER", 20)))

                if collection.size().getInfo() == 0:
                    collection = (ee.ImageCollection("LANDSAT/LC09/C02/T1_L2").
                                  filterBounds(geometry).filterDate(
                                      start_date, end_date).filter(
                                          ee.Filter.lt("CLOUD_COVER", 20)))

                if collection.size().getInfo() == 0:
                    continue

                image = collection.median().clip(geometry)

                for idx in indices:
                    try:
                        if idx == "NDVI":
                            index_img = image.normalizedDifference(
                                ["SR_B5", "SR_B4"]).rename(idx)
                        elif idx == "NDWI":
                            index_img = image.normalizedDifference(
                                ["SR_B3", "SR_B5"]).rename(idx)
                        elif idx == "NDBI":
                            index_img = image.normalizedDifference(
                                ["SR_B6", "SR_B5"]).rename(idx)
                        elif idx == "EVI":
                            index_img = image.expression(
                                "2.5 * ((NIR - RED) / (NIR + 6 * RED - 7.5 * BLUE + 1))",
                                {
                                    "NIR": image.select("SR_B5"),
                                    "RED": image.select("SR_B4"),
                                    "BLUE": image.select("SR_B2")
                                }).rename(idx)
                        elif idx == "SAVI":
                            index_img = image.expression(
                                "((NIR - RED) / (NIR + RED + 0.5)) * 1.5", {
                                    "NIR": image.select("SR_B5"),
                                    "RED": image.select("SR_B4")
                                }).rename(idx)
                        else:
                            continue

                        mean_val = index_img.reduceRegion(
                            reducer=ee.Reducer.mean(),
                            geometry=geometry,
                            scale=30,
                            maxPixels=1e9).get(idx).getInfo()

                        if mean_val is not None:
                            yearly_data[idx][year] = round(mean_val, 4)
                    except Exception as e:
                        print(f"Error calculating {idx} for {year}: {e}")
                        continue

        except Exception as e:
            print(f"Error processing year {year}: {e}")
            continue

    return yearly_data


def calculate_trend(data_dict):
    if len(data_dict) < 2:
        return None

    years = sorted(data_dict.keys())
    values = [data_dict[y] for y in years]

    slope, intercept, r_value, p_value, std_err = stats.linregress(
        years, values)

    n = len(years)
    predicted = [intercept + slope * y for y in years]
    residuals = [values[i] - predicted[i] for i in range(n)]

    if n > 2:
        residual_std_err = np.sqrt(sum(r**2 for r in residuals) / (n - 2))
    else:
        residual_std_err = std_err

    return {
        "slope":
        round(slope, 6),
        "intercept":
        round(intercept, 4),
        "r_squared":
        round(r_value**2, 4),
        "p_value":
        round(p_value, 4),
        "std_err":
        round(std_err, 6),
        "residual_std_err":
        round(residual_std_err, 6),
        "trend_direction":
        "increasing" if slope > 0 else "decreasing" if slope < 0 else "stable",
        "significant":
        p_value < 0.05,
        "years":
        years,
        "values":
        values,
        "n":
        n
    }


def forecast_values(trend_data, forecast_years):
    if trend_data is None:
        return None

    slope = trend_data["slope"]
    intercept = trend_data["intercept"]
    residual_std_err = trend_data.get("residual_std_err",
                                      trend_data.get("std_err", 0))
    historical_years = trend_data["years"]
    n = trend_data.get("n", len(historical_years))

    if n <= 2:
        return None

    forecasts = {}

    x_mean = np.mean(historical_years)
    ss_x = sum((y - x_mean)**2 for y in historical_years)

    if ss_x == 0:
        return None

    t_value = stats.t.ppf(0.975, n - 2)

    for year in forecast_years:
        predicted = intercept + slope * year

        se_forecast = residual_std_err * np.sqrt(1 + 1 / n +
                                                 (year - x_mean)**2 / ss_x)

        lower_bound = predicted - t_value * se_forecast
        upper_bound = predicted + t_value * se_forecast

        forecasts[year] = {
            "predicted": round(predicted, 4),
            "lower_bound": round(lower_bound, 4),
            "upper_bound": round(upper_bound, 4),
            "confidence": "95%"
        }

    return forecasts


def analyze_lulc_trends(yearly_lulc_data):
    if not yearly_lulc_data:
        return None

    all_classes = set()
    for year_data in yearly_lulc_data.values():
        all_classes.update(year_data.keys())

    trends = {}
    for lulc_class in all_classes:
        class_data = {}
        for year, year_data in yearly_lulc_data.items():
            if lulc_class in year_data:
                class_data[year] = year_data[lulc_class]

        if len(class_data) >= 2:
            trends[lulc_class] = calculate_trend(class_data)

    return trends


def analyze_index_trends(yearly_index_data):
    if not yearly_index_data:
        return None

    trends = {}
    for index_name, year_data in yearly_index_data.items():
        if len(year_data) >= 2:
            trends[index_name] = calculate_trend(year_data)

    return trends


def generate_forecast_lulc(lulc_trends, forecast_years):
    if not lulc_trends:
        return None

    forecasts = {}
    for lulc_class, trend in lulc_trends.items():
        if trend is not None:
            class_forecast = forecast_values(trend, forecast_years)
            if class_forecast:
                for year, forecast in class_forecast.items():
                    forecast["predicted"] = max(
                        0, min(100, forecast["predicted"]))
                    forecast["lower_bound"] = max(0, forecast["lower_bound"])
                    forecast["upper_bound"] = min(100, forecast["upper_bound"])
                forecasts[lulc_class] = class_forecast

    return forecasts


def generate_forecast_indices(index_trends, forecast_years):
    if not index_trends:
        return None

    forecasts = {}
    for index_name, trend in index_trends.items():
        if trend is not None:
            index_forecast = forecast_values(trend, forecast_years)
            if index_forecast:
                for year, forecast in index_forecast.items():
                    if index_name == "SAVI":
                        forecast["predicted"] = max(
                            0, min(1, forecast["predicted"]))
                        forecast["lower_bound"] = max(0,
                                                      forecast["lower_bound"])
                        forecast["upper_bound"] = min(1,
                                                      forecast["upper_bound"])
                    else:
                        forecast["predicted"] = max(
                            -1, min(1, forecast["predicted"]))
                        forecast["lower_bound"] = max(-1,
                                                      forecast["lower_bound"])
                        forecast["upper_bound"] = min(1,
                                                      forecast["upper_bound"])
                forecasts[index_name] = index_forecast

    return forecasts


def get_trend_summary(trends, data_type="LULC"):
    if not trends:
        return None

    summary = {
        "significant_increases": [],
        "significant_decreases": [],
        "stable": [],
        "data_type": data_type
    }

    for name, trend in trends.items():
        if trend is None:
            continue

        if trend["significant"]:
            if trend["trend_direction"] == "increasing":
                summary["significant_increases"].append({
                    "name":
                    name,
                    "change_per_year":
                    trend["slope"],
                    "r_squared":
                    trend["r_squared"]
                })
            elif trend["trend_direction"] == "decreasing":
                summary["significant_decreases"].append({
                    "name":
                    name,
                    "change_per_year":
                    trend["slope"],
                    "r_squared":
                    trend["r_squared"]
                })
        else:
            summary["stable"].append(name)

    return summary


def prepare_time_series_data(df, date_col, value_col):
    """Prepare time series data for ML forecasting.
    
    Args:
        df: DataFrame with date and value columns
        date_col: Name of date column
        value_col: Name of value column
        
    Returns:
        X: Feature matrix (numpy array)
        y: Target values (numpy array)
        last_date: Last date in the dataset
        features_list: List of feature names
    """
    import pandas as pd
    
    df = df.copy()
    df[date_col] = pd.to_datetime(df[date_col])
    df = df.dropna(subset=[value_col])
    
    if len(df) < 3:
        raise ValueError("Not enough data points for forecasting")
    
    df = df.sort_values(date_col).reset_index(drop=True)
    
    df['day_of_year'] = df[date_col].dt.dayofyear
    df['month'] = df[date_col].dt.month
    df['year'] = df[date_col].dt.year
    df['days_since_start'] = (df[date_col] - df[date_col].min()).dt.days
    
    features_list = ['days_since_start', 'day_of_year', 'month', 'year']
    
    X = df[features_list].values
    y = df[value_col].values
    last_date = df[date_col].max()
    
    return X, y, last_date, features_list


def train_forecast_model(X, y, model_type='random_forest'):
    """Train a forecasting model.
    
    Args:
        X: Feature matrix
        y: Target values
        model_type: 'random_forest' or 'linear'
        
    Returns:
        model: Trained model
        metrics: Dictionary with model performance metrics
    """
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import r2_score, mean_absolute_error
    
    if len(X) < 5:
        from sklearn.linear_model import LinearRegression
        model = LinearRegression()
        model.fit(X, y)
        y_pred = model.predict(X)
        r2 = r2_score(y, y_pred) if len(y) > 1 else 0
        mae = mean_absolute_error(y, y_pred)
        return model, {'r2': max(0, r2), 'mae': mae, 'type': 'linear (small dataset)'}
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    if model_type == 'random_forest':
        from sklearn.ensemble import RandomForestRegressor
        model = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
    else:
        from sklearn.linear_model import LinearRegression
        model = LinearRegression()
    
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    
    r2 = r2_score(y_test, y_pred)
    mae = mean_absolute_error(y_test, y_pred)
    
    model.fit(X, y)
    
    return model, {'r2': max(0, r2), 'mae': mae, 'type': model_type}


def generate_forecast(model, last_date, features_list, periods=30):
    """Generate future predictions.
    
    Args:
        model: Trained model
        last_date: Last date in training data
        features_list: List of feature names used in training
        periods: Number of periods (days) to forecast
        
    Returns:
        DataFrame with date and predicted_value columns
    """
    import pandas as pd
    
    future_dates = pd.date_range(start=last_date + pd.Timedelta(days=1), periods=periods, freq='D')
    
    future_df = pd.DataFrame({'date': future_dates})
    future_df['day_of_year'] = future_df['date'].dt.dayofyear
    future_df['month'] = future_df['date'].dt.month
    future_df['year'] = future_df['date'].dt.year
    
    start_date = last_date - pd.Timedelta(days=int((last_date - pd.Timestamp('2017-01-01')).days))
    future_df['days_since_start'] = (future_df['date'] - pd.Timestamp('2017-01-01')).dt.days
    
    X_future = future_df[features_list].values
    predictions = model.predict(X_future)
    
    result_df = pd.DataFrame({
        'date': future_dates,
        'predicted_value': predictions
    })
    
    return result_df


def calculate_trend_slope(values, dates=None):
    """Calculate trend slope from a series of values.
    
    Args:
        values: List or array of values
        dates: Optional list of dates (uses indices if not provided)
        
    Returns:
        slope: Rate of change per unit time
    """
    if len(values) < 2:
        return 0
    
    if dates is not None:
        import pandas as pd
        dates = pd.to_datetime(dates)
        x = np.array([(d - dates.min()).days for d in dates])
    else:
        x = np.arange(len(values))
    
    y = np.array(values)
    
    mask = ~np.isnan(y)
    if mask.sum() < 2:
        return 0
    
    slope, _, _, _, _ = stats.linregress(x[mask], y[mask])
    return slope
