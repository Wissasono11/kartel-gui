#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KARTEL Controller
Handles GUI interactions and connects with data manager

Author: KARTEL Team
Created: November 18, 2025
"""

from PyQt6.QtCore import QTimer, QObject, pyqtSignal
from kartel_data import get_data_manager

class KartelController(QObject):
    """Controller to handle GUI interactions and data updates"""
    
    # Signals for GUI updates
    data_updated = pyqtSignal(dict)  # Emits new sensor data
    status_updated = pyqtSignal(dict)  # Emits device status
    connection_updated = pyqtSignal(dict)  # Emits connection status
    
    def __init__(self):
        super().__init__()
        self.data_manager = get_data_manager()
        
        # Setup update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_data)
        self.update_timer.start(3000) 
        
        # Setup faster timer for device status
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_device_status)
        self.status_timer.start(1000)  # Update every 1 second
    
    def update_data(self):
        """Update sensor data and emit signals"""
        # Get current readings
        current_data = self.data_manager.get_current_readings()
        target_data = self.data_manager.get_target_values()
        
        # Combine data
        data_packet = {
            "current": current_data,
            "target": target_data
        }
        
        self.data_updated.emit(data_packet)
    
    def update_device_status(self):
        """Update device status and emit signals"""
        device_status = self.data_manager.get_device_status()
        self.status_updated.emit(device_status)
        
        # Also update connection status
        connection_status = self.data_manager.get_connection_status()
        self.connection_updated.emit(connection_status)
    
    def set_target_temperature(self, temperature: float):
        """Set target temperature"""
        self.data_manager.set_target_values(temperature=temperature)
        self.update_data()  # Immediate update
    
    def set_target_humidity(self, humidity: float):
        """Set target humidity"""
        self.data_manager.set_target_values(humidity=humidity)
        self.update_data()  # Immediate update
    
    def toggle_device(self, device: str):
        """Toggle device on/off"""
        result = self.data_manager.toggle_device(device)
        self.update_device_status()  # Immediate update
        return result
    
    def apply_profile(self, profile_name: str):
        """Apply incubation profile"""
        success = self.data_manager.apply_profile(profile_name)
        if success:
            self.update_data()  # Immediate update
        return success
    
    def get_incubation_profiles(self):
        """Get available profiles"""
        return self.data_manager.get_incubation_profiles()
    
    def get_historical_data(self):
        """Get historical data for graph"""
        return self.data_manager.get_historical_data()
    
    def simulate_mqtt_connection(self, username: str, password: str):
        """Simulate MQTT connection"""
        self.data_manager.update_mqtt_settings(username, password)
        success = self.data_manager.simulate_mqtt_connection()
        self.update_device_status()  # Update connection status
        return success
    
    def get_mqtt_settings(self):
        """Get MQTT settings"""
        return self.data_manager.get_mqtt_settings()