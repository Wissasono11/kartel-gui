#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KARTEL Configuration
Real data connection settings for Teknohole MQTT

Author: KARTEL Team
Created: November 27, 2025
"""

# Connection Type: 'MQTT', 'SERIAL', or 'DUMMY'
CONNECTION_TYPE = 'MQTT'

# MQTT Settings for Teknohole
MQTT_SETTINGS = {
    "broker": "mqtt.teknohole.com",
    "port": 1884,
    "username": "kartel",  
    "password": "kartel123",  
    "topics": {
        "sensor_data": "topic/penetasan/message",    # Data yang diterima dari ESP32
        "command": "topic/penetasan/command"         # Command yang dikirim ke ESP32
    },
    "keepalive": 60,
    "qos": 1
}

# Data format settings
DATA_FORMAT = {
    "sensor_keys": ["temperature", "humidity", "power", "rotate_on", "SET"],
    "update_interval": 3000,  # ms
    "history_max_points": 100
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