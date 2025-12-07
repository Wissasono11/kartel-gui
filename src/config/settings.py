# File: src/config/settings.py
import os
import sys

# --- FUNGSI HELPER PATH (MODIFIKASI KHUSUS EXE) ---
def resource_path(relative_path):
    try:
        # PyInstaller membuat folder temp di sys._MEIPASS saat mode EXE
        base_path = sys._MEIPASS
    except Exception:
        # Jika mode biasa, gunakan path relatif dari file ini
        base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    return os.path.join(base_path, relative_path)

# --- IMPLEMENTASI PATH ---
ASSET_DIR = resource_path('asset')

# --- APP INFO ---
APP_NAME = "KartelDashboard"
CREDENTIALS_FILE = "user_credentials.enc"

# --- MQTT CONFIGURATION ---
MQTT_SETTINGS = {
    "broker": "mqtt.teknohole.com",
    "port": 1884,  
    "username": "", 
    "password": "",
    "topics": {
        "sensor_data": "topic/penetasan/status",
        "command": "topic/penetasan/command"
    },
    "keepalive": 60,
    "qos": 1
}

# --- SENSOR DATA FORMAT ---
DATA_FORMAT = {
    "sensor_keys": ["temperature", "humidity", "power", "rotate_on", "SET"],
    "update_interval": 3000, 
    "history_max_points": 100
}

# --- DEFAULT DEVICE SETTINGS ---
DEFAULT_SETTINGS = {
    "target_temperature": 38.0,
    "target_humidity": 60.0,
    "buzzer_state": "OFF",
    "relay_on_time": 6,     
    "relay_interval": 3,    
    "incubation_day": 1,
    "total_days": 21
}

# --- SYSTEM CONFIG ---
CONNECTION_RETRY = {
    "max_attempts": 5,
    "retry_delay": 5,      
    "reconnect_delay": 30  
}