# File: src/config/settings.py
import os

# --- PATH SETTINGS ---
# Mendapatkan lokasi folder root project secara otomatis
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ASSET_DIR = os.path.join(BASE_DIR, 'asset')

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
        "sensor_data": "topic/penetasan/status",  # Subscribe (Masuk)
        "command": "topic/penetasan/command"      # Publish (Keluar)
    },
    "keepalive": 60,
    "qos": 1
}

# --- SENSOR DATA FORMAT ---
DATA_FORMAT = {
    "sensor_keys": ["temperature", "humidity", "power", "rotate_on", "SET"],
    "update_interval": 3000,  # ms
    "history_max_points": 100
}

# --- DEFAULT DEVICE SETTINGS ---
DEFAULT_SETTINGS = {
    "target_temperature": 38.0,
    "target_humidity": 60.0,
    "buzzer_state": "OFF",
    "relay_on_time": 6,     # seconds (RT_ON)
    "relay_interval": 3,    # hours (RT_INT)
    "incubation_day": 1,
    "total_days": 21
}

# --- SYSTEM CONFIG ---
CONNECTION_RETRY = {
    "max_attempts": 5,
    "retry_delay": 5,      # seconds
    "reconnect_delay": 30  # seconds
}