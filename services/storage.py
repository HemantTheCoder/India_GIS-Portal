import sqlite3
import json
import os
from datetime import datetime

DB_FILE = "monitoring.db"

def init_db():
    """Initialize the SQLite database with required tables."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # User Preferences
    c.execute('''CREATE TABLE IF NOT EXISTS preferences (
        key TEXT PRIMARY KEY,
        value TEXT
    )''')
    
    # Monitored Regions
    # geometry is stored as GeoJSON string
    c.execute('''CREATE TABLE IF NOT EXISTS regions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE,
        geometry TEXT,
        created_at TEXT
    )''')
    
    # Thresholds
    c.execute('''CREATE TABLE IF NOT EXISTS thresholds (
        region_id INTEGER,
        metric TEXT,
        operator TEXT, 
        value REAL,
        enabled INTEGER DEFAULT 1,
        FOREIGN KEY(region_id) REFERENCES regions(id),
        PRIMARY KEY (region_id, metric)
    )''')
    
    # Alert History
    c.execute('''CREATE TABLE IF NOT EXISTS alerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        region_name TEXT,
        metric TEXT,
        value REAL,
        message TEXT,
        read INTEGER DEFAULT 0
    )''')
    
    conn.commit()
    conn.close()

def get_connection():
    return sqlite3.connect(DB_FILE)

# --- Preferences ---
def save_preference(key, value):
    conn = get_connection()
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO preferences (key, value) VALUES (?, ?)", (key, str(value)))
    conn.commit()
    conn.close()

def get_preference(key, default=None):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT value FROM preferences WHERE key = ?", (key,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else default

# --- Regions ---
def add_region(name, geometry_geojson):
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute("INSERT INTO regions (name, geometry, created_at) VALUES (?, ?, ?)",
                  (name, json.dumps(geometry_geojson), datetime.now().isoformat()))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def get_all_regions():
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM regions")
    rows = c.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def delete_region(region_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM thresholds WHERE region_id = ?", (region_id,))
    c.execute("DELETE FROM regions WHERE id = ?", (region_id,))
    conn.commit()
    conn.close()

# --- Thresholds ---
def set_threshold(region_id, metric, operator, value, enabled=True):
    conn = get_connection()
    c = conn.cursor()
    c.execute('''INSERT OR REPLACE INTO thresholds (region_id, metric, operator, value, enabled)
                 VALUES (?, ?, ?, ?, ?)''', (region_id, metric, operator, value, 1 if enabled else 0))
    conn.commit()
    conn.close()

def get_thresholds(region_id):
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM thresholds WHERE region_id = ?", (region_id,))
    rows = c.fetchall()
    conn.close()
    return [dict(row) for row in rows]

# --- Alerts ---
def log_alert(region_name, metric, value, message):
    conn = get_connection()
    c = conn.cursor()
    c.execute('''INSERT INTO alerts (timestamp, region_name, metric, value, message, read)
                 VALUES (?, ?, ?, ?, ?, 0)''', 
              (datetime.now().isoformat(), region_name, metric, value, message))
    conn.commit()
    conn.close()

def get_recent_alerts(limit=50):
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM alerts ORDER BY timestamp DESC LIMIT ?", (limit,))
    rows = c.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_unread_count():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM alerts WHERE read = 0")
    count = c.fetchone()[0]
    conn.close()
    return count

def mark_all_read():
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE alerts SET read = 1 WHERE read = 0")
    conn.commit()
    conn.close()

# Initialize on import
init_db()
