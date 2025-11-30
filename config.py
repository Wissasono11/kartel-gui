# Untuk koneksi real-time ke sensor
CONNECTION_TYPE = 'MQTT'

# MQTT Settings untuk menerima data real dari sensor ESP32 via Teknohole
MQTT_SETTINGS = {
    "broker": "mqtt.teknohole.com",
    "port": 1884,
    "username": "kartel",  
    "password": "kartel123",  
    "topics": {
        "sensor_data": "topic/penetasan/status",     # Data yang diterima dari ESP32
        "command": "topic/penetasan/command"         # Command yang dikirim ke ESP32
    },
    "keepalive": 60,
    "qos": 1
}

# Format data sensor real-time
DATA_FORMAT = {
    "sensor_keys": ["temperature", "humidity", "power", "rotate_on", "SET"],
    "update_interval": 3000,  # ms - interval update dari sensor
    "history_max_points": 100  # maksimal data point untuk grafik
}

# Default device settings
DEFAULT_SETTINGS = {
    "target_temperature": 38.0,
    "target_humidity": 60.0,
    "buzzer_state": "OFF",
    "relay_on_time": 10,     # seconds
    "relay_interval": 3,     # minutes
    "incubation_day": 1,
    "total_days": 21
}

# Connection retry settings
CONNECTION_RETRY = {
    "max_attempts": 5,
    "retry_delay": 5,  # seconds
    "reconnect_delay": 30  # seconds
}