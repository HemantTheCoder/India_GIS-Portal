def calculate_sub_index(conc, breakpoints):
    """
  Calculates the sub-index for a single pollutant based on CPCB formula.
  Ip = [{(IHI - ILO) / (BHI - BLO)} * (Cp - BLO)] + ILO
  """
    if conc is None:
        return None

    for i, (blo, bhi, ilo, ihi) in enumerate(breakpoints):
        if blo <= conc <= bhi:
            return ((ihi - ilo) / (bhi - blo)) * (conc - blo) + ilo

    # If concentration is beyond the highest defined range, extrapolate or cap
    # For simplicity, we cap at the max index (usually 500)
    return breakpoints[-1][3] if conc > breakpoints[-1][1] else 0


def get_aqi_category(aqi):
    if aqi is None: return "Unknown", "#808080"
    if aqi <= 50: return "Good", "#00b050"
    if aqi <= 100: return "Satisfactory", "#92d050"
    if aqi <= 200: return "Moderate", "#ffff00"
    if aqi <= 300: return "Poor", "#ff9900"
    if aqi <= 400: return "Very Poor", "#ff0000"
    return "Severe", "#c00000"


def calculate_cpcb_aqi(pm25=None, pm10=None):
    """
  Calculates AQI based on Indian CPCB Standards.
  Only considers PM2.5 and PM10 for now as those are our valid surface params.

  Breakpoints (Conc_LO, Conc_HI, Index_LO, Index_HI):
  """

    # PM2.5 Breakpoints (24-hr avg)
    pm25_breakpoints = [
        (0, 30, 0, 50),
        (31, 60, 51, 100),
        (61, 90, 101, 200),
        (91, 120, 201, 300),
        (121, 250, 301, 400),
        (251, 5000, 401, 500)  # Extended cap
    ]

    # PM10 Breakpoints (24-hr avg)
    pm10_breakpoints = [(0, 50, 0, 50), (51, 100, 51, 100),
                        (101, 250, 101, 200), (251, 350, 201, 300),
                        (351, 430, 301, 400), (431, 5000, 401, 500)]

    indices = {}
    if pm25 is not None:
        indices['PM2.5'] = calculate_sub_index(pm25, pm25_breakpoints)
    if pm10 is not None:
        indices['PM10'] = calculate_sub_index(pm10, pm10_breakpoints)

    valid_indices = {k: v for k, v in indices.items() if v is not None}

    if not valid_indices:
        return None, "Insufficient Data", None, None

    # AQI is the maximum of the sub-indices
    max_pollutant = max(valid_indices, key=valid_indices.get)
    aqi_value = valid_indices[max_pollutant]

    category, color = get_aqi_category(aqi_value)

    return round(aqi_value), category, color, max_pollutant
