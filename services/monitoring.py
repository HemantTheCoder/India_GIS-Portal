import time
import toml
import ee
import json
import streamlit as st
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler

from services.storage import get_all_regions, get_thresholds, log_alert, get_preference
from services.notifications import push_notification
from services.gee_core import initialize_gee

# Import Analysis Services
# Note: We import these inside the job to avoid circular dependency issues at startup
# provided they are designed to be callable without active streamlit context 
# (our previous refactors helped ensure this separators of concerns)

def load_secrets_from_file():
    """Load secrets.toml manually if running outside Streamlit."""
    try:
        return toml.load(".streamlit/secrets.toml")
    except Exception as e:
        print(f"Could not load secrets.toml: {e}")
        return {}

def init_gee_backend():
    """Initialize GEE for backend usage."""
    try:
        # Try active streamlit session first
        if ee.data._credentials:
            return True
        
        # Fallback to loading from file
        secrets = load_secrets_from_file()
        if "GEE_JSON" in secrets:
            key_data = secrets["GEE_JSON"]
            credentials = ee.ServiceAccountCredentials(
                key_data.get("client_email", ""),
                key_data=json.dumps(key_data)
            )
            ee.Initialize(credentials)
            return True
        
        # Try default
        ee.Initialize()
        return True
    except Exception as e:
        print(f"Backend GEE Init Failed: {e}")
        return False

def check_region_status(region):
    """Run analysis for a single region."""
    try:
        region_id = region['id']
        name = region['name']
        geometry =  ee.Geometry(json.loads(region['geometry']))
        
        print(f"Checking region: {name}")
        
        # Get Thresholds
        thresholds = get_thresholds(region_id)
        if not thresholds:
            print(f"No thresholds for {name}, skipping.")
            return

        # 1. AQI Analysis (Latest avail date)
        # We check last 3 days
        end_date = datetime.now()
        start_date = end_date - timedelta(days=3)
        
        from services.gee_aqi import get_pollutant_image, calculate_pollutant_statistics
        
        # 2. LST Analysis (Latest avail)
        # We check last 7 days usually for MODIS
        lst_start = end_date - timedelta(days=7)
        from services.gee_lst import get_mean_lst, get_lst_statistics
        
        alerts_triggered = []

        for thresh in thresholds:
            if not thresh['enabled']: continue
            
            metric = thresh['metric'] # e.g., 'NO2', 'LST_Day', 'NDVI'
            operator = thresh['operator'] # '>', '<'
            limit = thresh['value']
            
            val = None
            
            # --- FETCH VALUE ---
            if metric in ['NO2', 'CO', 'SO2', 'O3', 'PM25']:
                img = get_pollutant_image(geometry, metric, start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))
                if img:
                    stats = calculate_pollutant_statistics(img, geometry, metric)
                    val = stats.get('mean')
            
            elif metric.startswith('LST'):
                time_of_day = 'Day' if 'Day' in metric else 'Night'
                img = get_mean_lst(geometry, lst_start.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"), time_of_day)
                if img:
                    stats = get_lst_statistics(img, geometry)
                    val = stats.get(f"LST_{time_of_day}_mean")

            # --- CHECK THRESHOLD ---
            if val is not None:
                triggered = False
                if operator == '>' and val > limit:
                    triggered = True
                elif operator == '<' and val < limit:
                    triggered = True
                
                if triggered:
                    msg = f"Alert! {metric} in {name} is {val:.2f} (Threshold: {operator} {limit})"
                    log_alert(name, metric, val, msg)
                    alerts_triggered.append(msg)
                    print(f"  [TRIGGERED] {msg}")
        
        # Send Notifications
        if alerts_triggered:
            summary = "\n".join(alerts_triggered)
            subject = f"Environmental Alert: {name}"
            push_notification(subject, summary)
            
    except Exception as e:
        print(f"Error checking region {region['name']}: {e}")

def run_monitoring_job():
    """Main job to run periodic monitoring."""
    print("--- Starting Monitoring Job ---")
    if not init_gee_backend():
        print("GEE Init failed, aborting job.")
        return

    regions = get_all_regions()
    if not regions:
        print("No regions to monitor.")
        return

    for region in regions:
        check_region_status(region)
    
    print("--- Monitoring Job Complete ---")

# Scheduler Setup
scheduler = BackgroundScheduler()
# Run every 24 hours by default, but for demo we might want it more frequent or configurable
# We'll set it to run daily at 8 AM
# scheduler.add_job(run_monitoring_job, 'cron', hour=8, minute=0)

# For demonstration/testing, we can add a simpler interval
# Check every 6 hours
scheduler.add_job(run_monitoring_job, 'interval', hours=6, id='monitor_job', replace_existing=True)

def start_scheduler():
    if not scheduler.running:
        scheduler.start()
        print("Monitoring Scheduler Started")
