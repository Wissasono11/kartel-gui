#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KARTEL Controller
Menangani interaksi GUI dan terhubung dengan pengelola data real
Menggunakan data MQTT REAL dari ESP32 melalui Teknohole

Author: KARTEL Team
Created: November 18, 2025
Updated: November 27, 2025
"""

from PyQt6.QtCore import QTimer, QObject, pyqtSignal
from kartel_data import get_real_data_manager

class KartelController(QObject):
    """Controller untuk menangani interaksi GUI dan pembaruan data"""
    
    # Sinyal untuk pembaruan GUI
    data_updated = pyqtSignal(dict)  # Emit data sensor baru
    status_updated = pyqtSignal(dict)  # Emit status perangkat
    connection_updated = pyqtSignal(dict)  # Emit status koneksi
    error_occurred = pyqtSignal(str)  # Emit pesan error
    
    def __init__(self):
        super().__init__()
        
        # Inisialisasi pengelola data real
        self.data_manager = get_real_data_manager()
        self.setup_real_data_connections()
        
        print("✅ Using REAL MQTT data from ESP32 via Teknohole")
    
    def setup_real_data_connections(self):
        """Pengaturan koneksi untuk pengelola data MQTT real"""
        # Hubungkan sinyal data real
        self.data_manager.data_received.connect(self.on_real_data_received)
        self.data_manager.connection_changed.connect(self.on_connection_changed)
        self.data_manager.error_occurred.connect(self.on_error_occurred)
        
        # Pengaturan callback status untuk pembaruan motor real-time
        self.data_manager._status_callback = self.emit_status_update
        
        # Pengaturan timer untuk pembaruan status koneksi
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_connection_status)
        self.status_timer.start(5000)  # Perbarui setiap 5 detik
        
        # Pengaturan timer status perangkat real-time
        self.device_status_timer = QTimer()
        self.device_status_timer.timeout.connect(self.update_device_status_realtime)
        self.device_status_timer.start(1000)  # Perbarui setiap detik untuk countdown real-time
    
    def emit_status_update(self, device_status):
        """Emit sinyal pembaruan status perangkat"""
        self.status_updated.emit(device_status)
    
    def update_device_status_realtime(self):
        """Perbarui status perangkat secara real-time"""
        device_status = self.data_manager.get_device_status()
        self.status_updated.emit(device_status)
    
    def on_real_data_received(self, data):
        """Tangani data real yang diterima dari ESP32 melalui MQTT"""
        # Konversi ke format yang diharapkan GUI
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
        
        # Emit sinyal untuk update dashboard
        self.data_updated.emit(data_packet)
        
        # Perbarui status perangkat ketika data baru datang
        device_status = self.data_manager.get_device_status()
        self.status_updated.emit(device_status)
    
    def on_connection_changed(self, connected):
        """Tangani perubahan status koneksi MQTT"""
        connection_status = self.data_manager.get_connection_status()
        self.connection_updated.emit(connection_status)
    
    def on_error_occurred(self, error_message):
        """Tangani error dari pengelola data real"""
        self.error_occurred.emit(error_message)
    
    def update_connection_status(self):
        """Perbarui status koneksi"""
        connection_status = self.data_manager.get_connection_status()
        self.connection_updated.emit(connection_status)
    
    def set_target_temperature(self, temperature: float):
        """Atur suhu target"""
        success = self.data_manager.set_target_temperature(temperature)
        if success:
            print(f"✅ Target temperature set to {temperature}°C")
        return success
    
    def set_target_humidity(self, humidity: float):
        """Atur kelembaban target"""
        # Perbarui target internal untuk tujuan tampilan
        self.data_manager.device_settings["target_humidity"] = humidity
        print(f"📝 Humidity target updated to {humidity}% (display only)")
        return True
    
    def control_buzzer(self, state: str):
        """Kontrol buzzer ON/OFF"""
        return self.data_manager.set_buzzer(state)
    
    def set_relay_timing(self, on_time: int, interval: int):
        """Atur waktu relay"""
        return self.data_manager.set_relay_timing(on_time, interval)
    
    def apply_profile(self, profile_name: str):
        """Terapkan profil penetasan"""
        return self.data_manager.apply_profile(profile_name)
    
    def get_incubation_profiles(self):
        """Dapatkan profil yang tersedia"""
        return self.data_manager.get_incubation_profiles()
    
    def get_historical_data(self):
        """Dapatkan data historis untuk grafik"""
        return self.data_manager.get_historical_data()
    
    def simulate_mqtt_connection(self, username: str, password: str):
        """Coba koneksi MQTT real dengan kredensial yang diberikan"""
        try:
            # Perbarui pengaturan MQTT dengan kredensial yang diberikan
            from config import MQTT_SETTINGS
            MQTT_SETTINGS["username"] = username
            MQTT_SETTINGS["password"] = password
            
            # Coba terhubung dengan pengelola data real
            success = self.data_manager.connect()
            
            if success:
                # Paksa pembaruan status koneksi
                self.update_connection_status()
                
            return success
            
        except Exception as e:
            print(f"❌ MQTT connection failed: {e}")
            return False
    
    def get_mqtt_settings(self):
        """Dapatkan pengaturan MQTT"""
        from config import MQTT_SETTINGS
        return {
            "broker": MQTT_SETTINGS["broker"],
            "port": MQTT_SETTINGS["port"],
            "username": MQTT_SETTINGS["username"],
            "password": "***",  # Sembunyikan password
            "topics": MQTT_SETTINGS["topics"]
        }
    
    def get_connection_info(self):
        """Dapatkan informasi koneksi yang detail"""
        mqtt_settings = self.get_mqtt_settings()
        return {
            "connection_mode": "MQTT Real-time",
            "broker": f"{mqtt_settings['broker']}:{mqtt_settings['port']}",
            "connected": self.data_manager.is_connected,
            "using_real_data": True
        }
    
    def disconnect(self):
        """Putuskan koneksi dari broker MQTT"""
        if hasattr(self.data_manager, 'disconnect'):
            self.data_manager.disconnect()