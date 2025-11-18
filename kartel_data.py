#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KARTEL Data Manager
Handles dummy data generation and simulation for the dashboard

Author: KARTEL Team
Created: November 18, 2025
"""

import random
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any

class KartelDataManager:
    """Manages sensor data simulation and device status"""
    
    def __init__(self):
        # Current sensor values
        self.current_temperature = 37.5
        self.current_humidity = 58.0
        
        # Target values
        self.target_temperature = 38.0
        self.target_humidity = 60.0
        
        # Device status
        self.device_status = {
            "pemanas": {"active": True, "status": "Aktif"},
            "humidifier": {"active": False, "status": "Non-aktif"},
            "motor": {"active": False, "status": "Menunggu", "rotation_time": 0},
            "timer": {"countdown": "2:30:15"}
        }
        
        # Motor pembalik schedule tracking
        self.motor_schedule = {
            "last_turn_time": time.time() - 3600,  # Last turn was 1 hour ago
            "turn_interval": 14400,  # Turn every 4 hours (4*60*60 seconds)
            "rotation_duration": 30,  # Motor runs for 30 seconds
            "current_rotation_start": None,
            "is_stopped": False  # Track if motor is manually stopped
        }
        
        # Connection status
        self.is_connected = False
        self.incubation_day = 3
        self.total_days = 21
        
        # Historical data (24 hours)
        self.generate_historical_data()
        
        # MQTT settings
        self.mqtt_settings = {
            "username": "kartel_esp32",
            "password": "KartelTest123",
            "broker": "localhost",
            "port": 1883
        }
    
    def generate_historical_data(self):
        """Generate 24 hours of historical sensor data"""
        self.historical_data = {
            "timestamps": [],
            "temperature": [],
            "humidity": []
        }
        
        # Generate data for last 24 hours
        base_time = datetime.now() - timedelta(hours=23)
        
        for i in range(24):
            timestamp = base_time + timedelta(hours=i)
            self.historical_data["timestamps"].append(timestamp)
            
            # Simulate realistic temperature variations
            temp_base = 37.8 + random.uniform(-0.5, 0.5)
            if 6 <= timestamp.hour <= 18:  # Daytime - slightly warmer
                temp_variation = random.uniform(-0.2, 0.8)
            else:  # Nighttime - slightly cooler
                temp_variation = random.uniform(-0.5, 0.3)
            
            temperature = temp_base + temp_variation
            self.historical_data["temperature"].append(round(temperature, 1))
            
            # Simulate humidity variations (inverse relationship with temperature)
            humidity_base = 60.0 + random.uniform(-2, 2)
            humidity_variation = random.uniform(-1.5, 1.5)
            humidity = humidity_base + humidity_variation
            self.historical_data["humidity"].append(round(max(40, min(80, humidity)), 1))
    
    def get_current_readings(self) -> Dict[str, float]:
        """Get current sensor readings with small random variations"""
        # Simulate small sensor fluctuations
        temp_noise = random.uniform(-0.1, 0.1)
        humidity_noise = random.uniform(-0.5, 0.5)
        
        self.current_temperature += temp_noise
        self.current_humidity += humidity_noise
        
        # Keep values in realistic ranges
        self.current_temperature = max(35.0, min(42.0, self.current_temperature))
        self.current_humidity = max(45.0, min(75.0, self.current_humidity))
        
        return {
            "temperature": round(self.current_temperature, 1),
            "humidity": round(self.current_humidity, 1)
        }
    
    def get_target_values(self) -> Dict[str, float]:
        """Get target setpoint values"""
        return {
            "temperature": self.target_temperature,
            "humidity": self.target_humidity
        }
    
    def set_target_values(self, temperature: float = None, humidity: float = None):
        """Set new target values"""
        if temperature is not None:
            self.target_temperature = max(30.0, min(45.0, temperature))
        if humidity is not None:
            self.target_humidity = max(40.0, min(80.0, humidity))
    
    def get_device_status(self) -> Dict[str, Any]:
        """Get current device status with dynamic updates"""
        # Simulate timer countdown
        current_time = time.time()
        if not hasattr(self, '_last_timer_update'):
            self._last_timer_update = current_time
            self._timer_seconds = 2 * 3600 + 30 * 60 + 15  # 2:30:15 in seconds
        
        elapsed = current_time - self._last_timer_update
        if elapsed >= 1.0:  # Update every second
            self._timer_seconds = max(0, self._timer_seconds - int(elapsed))
            self._last_timer_update = current_time
            
            hours = self._timer_seconds // 3600
            minutes = (self._timer_seconds % 3600) // 60
            seconds = self._timer_seconds % 60
            self.device_status["timer"]["countdown"] = f"{hours}:{minutes:02d}:{seconds:02d}"
        
        # Simulate device logic based on temperature/humidity
        temp_diff = self.target_temperature - self.current_temperature
        humidity_diff = self.target_humidity - self.current_humidity
        
        # Auto-control pemanas
        if temp_diff > 0.5:
            self.device_status["pemanas"]["active"] = True
            self.device_status["pemanas"]["status"] = "Aktif"
        elif temp_diff < -0.5:
            self.device_status["pemanas"]["active"] = False
            self.device_status["pemanas"]["status"] = "Non-aktif"
        
        # Auto-control humidifier
        if humidity_diff > 2.0:
            self.device_status["humidifier"]["active"] = True
            self.device_status["humidifier"]["status"] = "Aktif"
        elif humidity_diff < -2.0:
            self.device_status["humidifier"]["active"] = False
            self.device_status["humidifier"]["status"] = "Non-aktif"
        
        # Motor status (realistic turning schedule with rotation states)
        self._update_motor_status(current_time)
            
        return self.device_status.copy()
    
    def _update_motor_status(self, current_time: float):
        """Update motor pembalik status - Simplified 3 states: Menunggu, Berputar, Berhenti"""
        time_since_last_turn = current_time - self.motor_schedule["last_turn_time"]
        turn_interval = self.motor_schedule["turn_interval"]
        rotation_duration = self.motor_schedule["rotation_duration"]
        
        # Check if motor is currently rotating
        if self.motor_schedule["current_rotation_start"] is not None:
            rotation_elapsed = current_time - self.motor_schedule["current_rotation_start"]
            
            if rotation_elapsed < rotation_duration:
                # Motor is currently rotating
                self.device_status["motor"]["active"] = True
                self.device_status["motor"]["status"] = "Berputar"
                self.device_status["motor"]["rotation_time"] = int(rotation_duration - rotation_elapsed)
            else:
                # Rotation finished, set to stopped
                self.device_status["motor"]["active"] = False
                self.device_status["motor"]["status"] = "Berhenti"
                self.device_status["motor"]["rotation_time"] = 0
                self.motor_schedule["current_rotation_start"] = None
                self.motor_schedule["last_turn_time"] = current_time
                self.motor_schedule["is_stopped"] = True
        else:
            # Motor not rotating
            if self.motor_schedule["is_stopped"]:
                # Motor was stopped after rotation
                self.device_status["motor"]["status"] = "Berhenti"
                self.device_status["motor"]["active"] = False
                
                # Reset to Menunggu after some time (simulate cooldown)
                if time_since_last_turn > 120:  # 2 minutes cooldown after rotation
                    self.motor_schedule["is_stopped"] = False
                    self.device_status["motor"]["status"] = "Menunggu"
            else:
                # Check if it's time to turn
                if time_since_last_turn >= turn_interval:
                    # Time to start rotation
                    self.motor_schedule["current_rotation_start"] = current_time
                    self.device_status["motor"]["active"] = True
                    self.device_status["motor"]["status"] = "Berputar"
                    self.device_status["motor"]["rotation_time"] = rotation_duration
                else:
                    # Still waiting for next turn
                    self.device_status["motor"]["status"] = "Menunggu"
                    self.device_status["motor"]["active"] = False
                    self.device_status["motor"]["rotation_time"] = 0
    
    def toggle_device(self, device: str) -> bool:
        """Toggle device on/off manually"""
        if device in self.device_status:
            if device == "motor":
                # Special handling for motor pembalik - 3 states: Menunggu, Berputar, Berhenti
                current_status = self.device_status["motor"]["status"]
                
                if current_status == "Berputar":
                    # Stop current rotation
                    self.device_status["motor"]["active"] = False
                    self.device_status["motor"]["status"] = "Berhenti"
                    self.device_status["motor"]["rotation_time"] = 0
                    self.motor_schedule["current_rotation_start"] = None
                    self.motor_schedule["is_stopped"] = True
                    return False
                elif current_status == "Berhenti":
                    # Start from stopped state
                    self.motor_schedule["current_rotation_start"] = time.time()
                    self.device_status["motor"]["active"] = True
                    self.device_status["motor"]["status"] = "Berputar"
                    self.device_status["motor"]["rotation_time"] = self.motor_schedule["rotation_duration"]
                    self.motor_schedule["is_stopped"] = False
                    return True
                else:  # "Menunggu"
                    # Start manual rotation from waiting state
                    self.motor_schedule["current_rotation_start"] = time.time()
                    self.device_status["motor"]["active"] = True
                    self.device_status["motor"]["status"] = "Berputar"
                    self.device_status["motor"]["rotation_time"] = self.motor_schedule["rotation_duration"]
                    self.motor_schedule["is_stopped"] = False
                    return True
            else:
                # Normal toggle for other devices
                current_active = self.device_status[device].get("active", False)
                new_active = not current_active
                self.device_status[device]["active"] = new_active
                self.device_status[device]["status"] = "Aktif" if new_active else "Non-aktif"
                return new_active
        return False
    
    def get_connection_status(self) -> Dict[str, Any]:
        """Get connection and incubation status"""
        # Simulate connection attempts
        if random.random() < 0.1:  # 10% chance to toggle connection
            self.is_connected = not self.is_connected
        
        # Simulate day progression (very slowly for demo)
        if random.random() < 0.01:  # 1% chance to advance day
            if self.incubation_day < self.total_days:
                self.incubation_day += 1
        
        return {
            "connected": self.is_connected,
            "status_text": "Terhubung" if self.is_connected else "Tidak Terhubung",
            "day": self.incubation_day,
            "total_days": self.total_days,
            "day_text": f"Hari ke- {self.incubation_day} dari {self.total_days}"
        }
    
    def get_historical_data(self) -> Dict[str, List]:
        """Get historical data for graph plotting"""
        return {
            "hours": [t.hour for t in self.historical_data["timestamps"]],
            "time_labels": [f"{t.hour:02d}.{t.minute:02d}" for t in self.historical_data["timestamps"]],
            "temperature": self.historical_data["temperature"],
            "humidity": self.historical_data["humidity"]
        }
    
    def get_incubation_profiles(self) -> List[Dict[str, Any]]:
        """Get available incubation profiles"""
        return [
            {
                "name": "Ayam (38°C, 60%)",
                "temperature": 38.0,
                "humidity": 60.0,
                "duration": 21
            },
            {
                "name": "Bebek (37.5°C, 65%)",
                "temperature": 37.5,
                "humidity": 65.0,
                "duration": 28
            },
            {
                "name": "Burung Puyuh (37.8°C, 55%)",
                "temperature": 37.8,
                "humidity": 55.0,
                "duration": 17
            }
        ]
    
    def apply_profile(self, profile_name: str):
        """Apply an incubation profile"""
        profiles = self.get_incubation_profiles()
        for profile in profiles:
            if profile["name"] == profile_name:
                self.set_target_values(profile["temperature"], profile["humidity"])
                self.total_days = profile["duration"]
                return True
        return False
    
    def get_mqtt_settings(self) -> Dict[str, Any]:
        """Get MQTT connection settings"""
        return self.mqtt_settings.copy()
    
    def update_mqtt_settings(self, username: str = None, password: str = None):
        """Update MQTT connection settings"""
        if username:
            self.mqtt_settings["username"] = username
        if password:
            self.mqtt_settings["password"] = password
    
    def simulate_mqtt_connection(self) -> bool:
        """Simulate MQTT connection attempt"""
        # Simulate connection success/failure
        success = random.random() > 0.2  # 80% success rate
        if success:
            self.is_connected = True
        return success
    
    def advance_incubation_day(self) -> bool:
        """Manually advance incubation day"""
        if self.incubation_day < self.total_days:
            self.incubation_day += 1
            return True
        return False
    
    def reset_incubation_day(self, day: int = 1):
        """Reset incubation to specific day"""
        self.incubation_day = max(1, min(day, self.total_days))

# Global instance
data_manager = KartelDataManager()

def get_data_manager() -> KartelDataManager:
    """Get the global data manager instance"""
    return data_manager