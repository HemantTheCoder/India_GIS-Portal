import requests
import io
import tempfile
import os
from PIL import Image, ImageDraw, ImageFont

def annotate_gif(gif_url, start_date, end_date, frequency):
    """
    Downloads GIF, adds date overlay, and returns local file path.
    """
    try:
        response = requests.get(gif_url)
        if response.status_code != 200:
            return None, "Failed to download GIF"
        
        img = Image.open(io.BytesIO(response.content))
        
        frames = []
        try:
            while True:
                frames.append(img.copy())
                img.seek(img.tell() + 1)
        except EOFError:
            pass
            
        # Calculate dates
        start = datetime.strptime(str(start_date), "%Y-%m-%d")
        end = datetime.strptime(str(end_date), "%Y-%m-%d")
        
        # Draw text on frames
        annotated_frames = []
        for i, frame in enumerate(frames):
            # Convert to RGBA to draw
            frame = frame.convert("RGBA")
            draw = ImageDraw.Draw(frame)
            
            # Estimate date for this frame
            # This assumes linear spacing match, which GEE might approximate
            # Ideally we match exact counts.
            if frequency == 'Yearly':
                current_date = start.replace(year=start.year + i)
                date_str = current_date.strftime("%Y")
            elif frequency == 'Monthly':
                 # Add month delta
                 year = start.year + (start.month + i - 1) // 12
                 month = (start.month + i - 1) % 12 + 1
                 current_date = datetime(year, month, 1)
                 date_str = current_date.strftime("%b %Y")
            else:
                 date_str = ""

            # Position text (Top Left)
            text = f"{date_str}"
            
            # Simple outline effect for visibility
            from PIL import ImageFont
            try:
                # Try to load a default font, size depends on image
                font_size = 40
                font = ImageFont.truetype("arial.ttf", font_size)
            except:
                font = ImageFont.load_default()

            x, y = 20, 20
            
            # Shadow/Outline
            draw.text((x+2, y+2), text, font=font, fill="black")
            draw.text((x, y), text, font=font, fill="white")
            
            annotated_frames.append(frame)
            
        # Save result
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.gif')
        annotated_frames[0].save(
            temp_file.name,
            save_all=True,
            append_images=annotated_frames[1:],
            loop=0,
            duration=img.info.get('duration', 500)
        )
        return temp_file.name, None

    except Exception as e:
        return None, str(e)


def get_lulc_timelapse(region, start_date, end_date, frequency='Yearly'):
    """
    Dynamic World LULC timelapse.
    """
    # Dynamic World V1: GOOGLE/DYNAMICWORLD/V1
    collection_id = "GOOGLE/DYNAMICWORLD/V1"
    band = "label"
    
    start = ee.Date(start_date)
    end = ee.Date(end_date)
    
    vis_params = {
        'min': 0,
        'max': 8,
        'palette': [
            '#419BDF', # Water
            '#397D49', # Trees
            '#88B053', # Grass
            '#7A87C6', # Flooded Veg
            '#E49635', # Crops
            '#DFC35A', # Shrub
            '#C4281B', # Built
            '#A59B8F', # Bare
            '#B39FE1'  # Snow
        ]
    }

    col = ee.ImageCollection(collection_id).filterBounds(region).select(band)
    
    unit = 'year'
    if frequency == 'Monthly': unit = 'month' # LULC monthly might be noisy/incomplete
    
    def get_step_img(n):
        date = start.advance(n, unit)
        filtered = col.filterDate(date, date.advance(1, unit))
        
        def process_image():
            return filtered.mode() \
                   .clip(region) \
                   .visualize(**vis_params) \
                   .set('system:time_start', date.millis())
        
        def empty_image():
             return ee.Image(0).byte().rename('vis-red') \
                   .addBands(ee.Image(0).byte().rename('vis-green')) \
                   .addBands(ee.Image(0).byte().rename('vis-blue')) \
                   .selfMask() \
                   .set('system:time_start', date.millis())

        return ee.Algorithms.If(filtered.size().gt(0), process_image(), empty_image())

    cnt = end.difference(start, unit).floor()
    indices = ee.List.sequence(0, cnt.subtract(1))
    
    # Limit max frames to avoid GEE timeouts or huge GIFs
    # 5 years * 12 months = 60 frames (Okay)
    
    compiled = ee.ImageCollection(indices.map(get_step_img))
    
    video_args = {
        'dimensions': 600, # Smaller for UI safety
        'region': region,
        'framesPerSecond': 2,
        'crs': 'EPSG:3857'
    }
    
    url = compiled.getVideoThumbURL(video_args)
    if url:
        return annotate_gif(url, start_date, end_date, frequency)
    return None, "Failed to get GEE URL"


def get_ndvi_timelapse(region, start_date, end_date, frequency='Monthly'):
    """
    Generates NDVI timelapse URL.
    """
    s2 = ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED") \
        .filterBounds(region) \
        .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 30))

    def add_ndvi(image):
        ndvi = image.normalizedDifference(['B8', 'B4']).rename('NDVI')
        return image.addBands(ndvi)

    with_ndvi = s2.map(add_ndvi).select('NDVI')
    
    # Aggregate based on frequency
    # Note: For efficient timelapse, we need to handle gaps.
    # We will use a simplified approach: map over time periods.
    
    # Custom aggregation logic might be needed for consistency
    # But for now, let's try to filter to the collection logic
    
    # Re-using the helper logic inline for robustness with GEE syntax
    start = ee.Date(start_date)
    end = ee.Date(end_date)
    
    interval = 1
    unit = 'month'
    if frequency == 'Yearly':
        unit = 'year'
    elif frequency == 'Weekly':
        unit = 'week'
    
    # Setup sequence
    t_start = start.millis()
    t_end = end.millis()
    
    # Easier way: iterate over known ranges in python if collection is small,
    # but for GEE server-side gen, we prefer ee.List.sequence
    # However, to burn text, we mostly need geemap or a specific styling.
    
    # Let's produce the raw RGB visuals first
    
    vis_params = {
        'min': 0.0,
        'max': 0.8,
        'palette': ['#FFFFFF', '#CE7E45', '#DF923D', '#F1B555', '#FCD163', '#99B718', '#74A901', '#66A000', '#529400', '#3E8601', '#207401', '#056201', '#004C00', '#023B01', '#012E01', '#011D01', '#011301']
    }
    
    # We will create a collection of visualized images
    
    # Using geemap's create_timelapse is easiest if available, but it often requires local execution for some parts or specific constraints.
    # Let's try constructing the collection manually and then getThumbURL (video).
    
    # To handle "text overlay" in a purely server-side GEE way is tricky without treating it as geometry.
    # We will proceed with generating the video URL of just the data, and handle "Date" by trusting the frame sequence or using a simplified approach if text is critical.
    # The user asked for captions showing date.
    # geemap.cartoee can potentially help but that's static plots.
    # Actually, GEE doesn't easily support text burn-in on server-side videos without complex feature collections.
    # RECOMMENDATION: We will return the video URL. Text overlay in frontend via JS slider is better, 
    # BUT user asked for "downloadable GIF".
    
    # Let's try to use the `visualize` method and rely on the UI for the date slider feedback, 
    # but for the "download" file, we might not have text.
    # Wait, the user specifically asked for "captions showing the date ...". 
    # We can use `geemap.add_text_to_gif` if we download it, but that's heavy for a web app server (replit).
    # Alternative: We can create a FeatureCollection of text (very hard) or just accept we show the map.
    
    # Let's stick to generating the visuals.
    
    # 1. Create list of dates
    # 2. Mosaic images
    # 3. Apply vis
    
    # Using a simpler "monthly" composite approach
    
    col = ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED") \
        .filterBounds(region) \
        .select(['B8', 'B4'])
        
    def get_monthly_ndvi(n):
        date = start.advance(n, unit)
        filtered = col.filterDate(date, date.advance(1, unit)) \
                  .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 30))
        
        def process_image():
            return filtered.median() \
                   .normalizedDifference(['B8', 'B4']) \
                   .rename('NDVI') \
                   .clip(region) \
                   .visualize(**vis_params) \
                   .set('system:time_start', date.millis())
        
        def empty_image():
            # Return a transparent image compatible with visualization (RGB)
            return ee.Image(0).byte().rename('vis-red') \
                   .addBands(ee.Image(0).byte().rename('vis-green')) \
                   .addBands(ee.Image(0).byte().rename('vis-blue')) \
                   .selfMask() \
                   .set('system:time_start', date.millis()) # Masked everywhere

        return ee.Algorithms.If(filtered.size().gt(0), process_image(), empty_image())

    if frequency == 'Yearly':
         cnt = end.difference(start, 'year').round()
    else:
         cnt = end.difference(start, 'month').round()

    # ee.List.sequence is exclusive on end? 0 to cnt-1
    check_cnt = cnt.getInfo() # This might be blocking, but okay for setup
    if check_cnt <= 0:
        return None, "Invalid date range or frequency."
        
    indices = ee.List.sequence(0, cnt.subtract(1))
    
    compiled = ee.ImageCollection(indices.map(get_monthly_ndvi))
    
    # Define video args
    video_args = {
        'dimensions': 600,
        'region': region,
        'framesPerSecond': 2,
        'crs': 'EPSG:3857'
    }
    
    url = compiled.getVideoThumbURL(video_args)
    if url:
        return annotate_gif(url, start_date, end_date, frequency)
    return None, "Failed to get GEE URL"


def get_aqi_timelapse(region, start_date, end_date, parameter='PM2.5', frequency='Monthly'):
    """
    Generates AQI timelapse.
    Supported parameters: 'NO2', 'SO2', 'CO', 'O3', 'Aerosol', 'UVAI'.
    Defaults to NO2 if PM2.5 (unavailable directly) or unknown is passed.
    """
    
    # Configuration for different pollutants
    aqi_config = {
        'NO2': {
            'id': "COPERNICUS/S5P/NRTI/L3_NO2",
            'band': "NO2_column_number_density",
            'vis': {'min': 0, 'max': 0.0002, 'palette': ['black', 'blue', 'purple', 'cyan', 'green', 'yellow', 'red']}
        },
        'SO2': {
            'id': "COPERNICUS/S5P/NRTI/L3_SO2",
            'band': "SO2_column_number_density",
            'vis': {'min': 0, 'max': 0.0005, 'palette': ['black', 'blue', 'purple', 'cyan', 'green', 'yellow', 'red']}
        },
        'CO': {
            'id': "COPERNICUS/S5P/NRTI/L3_CO",
            'band': "CO_column_number_density",
            'vis': {'min': 0, 'max': 0.05, 'palette': ['black', 'blue', 'purple', 'cyan', 'green', 'yellow', 'red']}
        },
        'O3': {
            'id': "COPERNICUS/S5P/NRTI/L3_O3",
            'band': "O3_column_number_density",
            'vis': {'min': 0.12, 'max': 0.15, 'palette': ['black', 'blue', 'purple', 'cyan', 'green', 'yellow', 'red']}
        },
        'Aerosol': {
            'id': "COPERNICUS/S5P/NRTI/L3_AER_AI",
            'band': "absorbing_aerosol_index",
            'vis': {'min': -1, 'max': 2.0, 'palette': ['black', 'blue', 'purple', 'cyan', 'green', 'yellow', 'red']}
        }
    }
    
    # Default to NO2 if parameter not found (sane default for "AQI")
    # Handle aliases
    if parameter == 'UVAI': parameter = 'Aerosol'
    
    cfg = aqi_config.get(parameter, aqi_config['NO2'])
    
    start = ee.Date(start_date)
    end = ee.Date(end_date)
    
    unit = 'month'
    if frequency == 'Yearly': unit = 'year'
    if frequency == 'Weekly': unit = 'week'
    
    col = ee.ImageCollection(cfg['id']).filterBounds(region).select(cfg['band'])

    def get_step_img(n):
        date = start.advance(n, unit)
        filtered = col.filterDate(date, date.advance(1, unit))

        def process_image():
            return filtered.mean() \
                   .clip(region) \
                   .visualize(**cfg['vis']) \
                   .set('system:time_start', date.millis())

        def empty_image():
            return ee.Image(0).byte().rename('vis-red') \
                   .addBands(ee.Image(0).byte().rename('vis-green')) \
                   .addBands(ee.Image(0).byte().rename('vis-blue')) \
                   .selfMask() \
                   .set('system:time_start', date.millis())

        return ee.Algorithms.If(filtered.size().gt(0), process_image(), empty_image())

    cnt = end.difference(start, unit).floor()
    indices = ee.List.sequence(0, cnt.subtract(1))
    compiled = ee.ImageCollection(indices.map(get_step_img))
    
    video_args = {
        'dimensions': 600,
        'region': region,
        'framesPerSecond': 2,
        'crs': 'EPSG:3857'
    }
    
    url = compiled.getVideoThumbURL(video_args)
    if url:
        return annotate_gif(url, start_date, end_date, frequency)
    return None, "Failed to get GEE URL"


def get_lst_timelapse(region, start_date, end_date, frequency='Monthly'):
    """
    Landsat LST or MODIS. MODIS is better for timelapse (daily/8-day).
    Using MODIS Terra Land Surface Temperature (MOD11A2) 8-day global 1km.
    """
    collection_id = "MODIS/006/MOD11A2"
    band = "LST_Day_1km"
    
    start = ee.Date(start_date)
    end = ee.Date(end_date)
    
    # Scale factor for LST is usually 0.02, converts to Kelvin. -273.15 for Celsius.
    
    vis_params = {
        'min': 15.0, # Celsius
        'max': 45.0,
        'palette': ['040274', '040281', '0502a3', '0502b8', '0502ce', '0502e6',
                    '0602ff', '235cb1', '307ef3', '269db1', '30c8e2', '32d3ef',
                    '3be285', '3ff38f', '86e26f', '3ae237', 'b5e22e', 'd6e21f',
                    'fff705', 'ffd611', 'ffb613', 'ff8b13', 'ff6e08', 'ff500d',
                    'ff0000', 'de0101', 'c21301', 'a71001', '911003']
    }
    
    col = ee.ImageCollection(collection_id).filterBounds(region).select(band)

    unit = 'month'
    if frequency == 'Yearly': unit = 'year'
    
    def get_step_img(n):
        date = start.advance(n, unit)
        filtered = col.filterDate(date, date.advance(1, unit))
        
        def process_image():
            return filtered.mean() \
                   .multiply(0.02).subtract(273.15) \
                   .clip(region) \
                   .visualize(**vis_params) \
                   .set('system:time_start', date.millis())
        
        def empty_image():
             return ee.Image(0).byte().rename('vis-red') \
                   .addBands(ee.Image(0).byte().rename('vis-green')) \
                   .addBands(ee.Image(0).byte().rename('vis-blue')) \
                   .selfMask() \
                   .set('system:time_start', date.millis())

        return ee.Algorithms.If(filtered.size().gt(0), process_image(), empty_image())

    cnt = end.difference(start, unit).floor()
    indices = ee.List.sequence(0, cnt.subtract(1))
    compiled = ee.ImageCollection(indices.map(get_step_img))
    
    video_args = {
        'dimensions': 600,
        'region': region,
        'framesPerSecond': 2,
        'crs': 'EPSG:3857'
    }
    
    url = compiled.getVideoThumbURL(video_args)
    if url:
        return annotate_gif(url, start_date, end_date, frequency)
    return None, "Failed to get GEE URL"

