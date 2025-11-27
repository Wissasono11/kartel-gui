#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KARTEL Controller
Handles GUI interactions and connects with real data manager
Uses REAL MQTT data from ESP32 via Teknohole

Author: KARTEL Team
Created: November 18, 2025
Updated: November 27, 2025
"""

from PyQt6.QtCore import QTimer, QObject, pyqtSignal
from kartel_data import get_real_data_manager

class KartelController(QObject):
    """Controller to handle GUI interactions and data updates"""
    
    # Signals for GUI updates
    data_updated = pyqtSignal(dict)  # Emits new sensor data
    status_updated = pyqtSignal(dict)  # Emits device status
    connection_updated = pyqtSignal(dict)  # Emits connection status
    error_occurred = pyqtSignal(str)  # Emits error messages
    
    def __init__(self):
        super().__init__()
        
        # Initialize real data manager
        self.data_manager = get_real_data_manager()
        self.setup_real_data_connections()
        
        print("✅ Using REAL MQTT data from ESP32 via Teknohole")
    
    def setup_real_data_connections(self):
        """Setup connections for real MQTT data manager"""
        # Connect real data signals
        self.data_manager.data_received.connect(self.on_real_data_received)
        self.data_manager.connection_changed.connect(self.on_connection_changed)
        self.data_manager.error_occurred.connect(self.on_error_occurred)
        
        # Setup status callback for real-time motor updates
        self.data_manager._status_callback = self.emit_status_update
        
        # Setup timer for connection status updates
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_connection_status)
        self.status_timer.start(5000)  # Update every 5 seconds
        
        # Setup real-time device status timer
        self.device_status_timer = QTimer()
        self.device_status_timer.timeout.connect(self.update_device_status_realtime)
        self.device_status_timer.start(1000)  # Update every second for real-time countdown
    
    def emit_status_update(self, device_status):
        """Emit device status update signal"""
        self.status_updated.emit(device_status)
    
    def update_device_status_realtime(self):
        """Update device status in real-time"""
        device_status = self.data_manager.get_device_status()
        self.status_updated.emit(device_status)
    
    def on_real_data_received(self, data):
        """Handle real data received from ESP32 via MQTT"""
        # Convert to expected format for GUI
        data_packet = {
            "current": {
                "temperature": data.get("temperature", 0.0),
                "humidity": data.get("humidity", 0.0)
            },
            "target": {
                "temperature": data.get("SET", 38.0),
                "humidity": 60.0  # Default
            },
            "extra": {
                "power": data.get("power", 0),
                "rotate_on": data.get("rotate_on", 0)
            }
        }
        
        self.data_updated.emit(data_packet)
        
        # Also update device status when new data arrives
        device_status = self.data_manager.get_device_status()
        self.status_updated.emit(device_status)
    
    def on_connection_changed(self, connected):
        """Handle MQTT connection status change"""
        connection_status = self.data_manager.get_connection_status()
        self.connection_updated.emit(connection_status)
    
    def on_error_occurred(self, error_message):
        """Handle errors from real data manager"""
        self.error_occurred.emit(error_message)
    
    def update_connection_status(self):
        """Update connection status"""
        connection_status = self.data_manager.get_connection_status()
        self.connection_updated.emit(connection_status)
    
    def set_target_temperature(self, temperature: float):
        """Set target temperature"""
        success = self.data_manager.set_target_temperature(temperature)
        if success:
            print(f"✅ Target temperature set to {temperature}°C")
        return success
    
    def set_target_humidity(self, humidity: float):
        """Set target humidity"""
        # Update internal target for display purposes
        self.data_manager.device_settings["target_humidity"] = humidity
        print(f"📝 Humidity target updated to {humidity}% (display only)")
        return True
    
    def control_buzzer(self, state: str):
        """Control buzzer ON/OFF"""
        return self.data_manager.set_buzzer(state)
    
    def set_relay_timing(self, on_time: int, interval: int):
        """Set relay timing"""
        return self.data_manager.set_relay_timing(on_time, interval)
    
    def toggle_device(self, device: str):
        """Toggle device on/off"""
        # Map GUI device names to real commands
        if device == "pemanas" or device == "heater":
            return self.data_manager.toggle_heater()
        elif device == "humidifier":
            return self.data_manager.toggle_humidifier()
        elif device == "motor":
            return self.data_manager.toggle_motor()
        elif device == "buzzer":
            current_state = getattr(self.data_manager, 'device_settings', {}).get('buzzer_state', 'OFF')
            new_state = 'OFF' if current_state == 'ON' else 'ON'
            return self.control_buzzer(new_state)
        else:
            print(f"⚠ Device '{device}' toggle not implemented")
            return False
    
    def apply_profile(self, profile_name: str):
        """Apply incubation profile"""
        return self.data_manager.apply_profile(profile_name)
    
    def get_incubation_profiles(self):
        """Get available profiles"""
        return self.data_manager.get_incubation_profiles()
    
    def get_historical_data(self):
        """Get historical data for graph"""
        return self.data_manager.get_historical_data()
    
    def simulate_mqtt_connection(self, username: str, password: str):
        """Attempt real MQTT connection with provided credentials"""
        try:
            # Update MQTT settings with provided credentials
            from config import MQTT_SETTINGS
            MQTT_SETTINGS["username"] = username
            MQTT_SETTINGS["password"] = password
            
            # Attempt to connect with real data manager
            success = self.data_manager.connect()
            
            if success:
                # Force connection status update
                self.update_connection_status()
                
            return success
            
        except Exception as e:
            print(f"❌ MQTT connection failed: {e}")
            return False
    
    def get_mqtt_settings(self):
        """Get MQTT settings"""
        from config import MQTT_SETTINGS
        return {
            "broker": MQTT_SETTINGS["broker"],
            "port": MQTT_SETTINGS["port"],
            "username": MQTT_SETTINGS["username"],
            "password": "***",  # Hide password
            "topics": MQTT_SETTINGS["topics"]
        }
    
    def get_connection_info(self):
        """Get detailed connection information"""
        mqtt_settings = self.get_mqtt_settings()
        return {
            "connection_mode": "MQTT Real-time",
            "broker": f"{mqtt_settings['broker']}:{mqtt_settings['port']}",
            "connected": self.data_manager.is_connected,
            "using_real_data": True
        }
    
    def disconnect(self):
        """Disconnect from MQTT broker"""
        if hasattr(self.data_manager, 'disconnect'):
            self.data_manager.disconnect()