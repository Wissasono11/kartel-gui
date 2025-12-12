import sys
from PyQt6.QtCore import QTimer, QObject, pyqtSignal

# Import Config
from src.config.settings import MQTT_SETTINGS

# Import Service
from src.services.mqtt_service import MqttService 

class MainController(QObject):
    """
    Controller Utama (The Brain).
    Bertugas mengoordinasikan antara UI (View) dan MQTT/Data (Service).
    """
    
    # Sinyal untuk pembaruan GUI
    data_updated = pyqtSignal(dict)       # Emit data sensor baru
    status_updated = pyqtSignal(dict)     # Emit status perangkat (ON/OFF)
    connection_updated = pyqtSignal(dict) # Emit status koneksi MQTT
    error_occurred = pyqtSignal(str)      # Emit pesan error
    
    def __init__(self):
        super().__init__()
        
        # Inisialisasi Service
        self.mqtt_service = MqttService()
        
        self.setup_service_connections()
        print("✅ MainController initialized with MqttService")
    
    def setup_service_connections(self):
        """Menghubungkan sinyal dari Service ke Controller"""
        self.mqtt_service.data_received.connect(self.on_real_data_received)
        self.mqtt_service.connection_changed.connect(self.on_connection_changed)
        self.mqtt_service.error_occurred.connect(self.on_error_occurred)
        self.mqtt_service.status_updated.connect(self.emit_status_update)
        
        # Timer Heartbeat UI
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_connection_status)
        self.status_timer.start(5000)
        
        # Timer Realtime Status
        self.device_status_timer = QTimer()
        self.device_status_timer.timeout.connect(self.update_device_status_realtime)
        self.device_status_timer.start(1000) 
    
    def cleanup(self):
        try:
            print("🔄 Controller cleanup...")
            if self.status_timer.isActive(): self.status_timer.stop()
            if self.device_status_timer.isActive(): self.device_status_timer.stop()
            self.mqtt_service.disconnect()
        except Exception as e:
            print(f"⚠ Cleanup error: {e}")

    # =========================================================================
    # LOGIC HANDLERS
    # =========================================================================

    def on_real_data_received(self, data):
        target_values = self.mqtt_service.get_target_values()
        
        data_packet = {
            "current": {
                "temperature": data.get("temperature", 0.0),
                "humidity": data.get("humidity", 0.0)
            },
            "target": {
                "temperature": target_values["temperature"],
                "humidity": target_values["humidity"]
            },
            "extra": {
                "power": data.get("power", 0),
                "rotate_on": data.get("rotate_on", 0)
            }
        }
        self.data_updated.emit(data_packet)
        self.update_device_status_realtime()

    def update_device_status_realtime(self):
        device_status = self.mqtt_service.get_device_status()
        self.status_updated.emit(device_status)

    def emit_status_update(self, device_status):
        self.status_updated.emit(device_status)

    def on_connection_changed(self, connected):
        status = self.mqtt_service.get_connection_status()
        self.connection_updated.emit(status)

    def update_connection_status(self):
        status = self.mqtt_service.get_connection_status()
        self.connection_updated.emit(status)

    def on_error_occurred(self, error_message):
        self.error_occurred.emit(error_message)

    # =========================================================================
    # PUBLIC METHODS (Dipanggil oleh View/EventHandlers)
    # =========================================================================

    def get_historical_data(self):
        """Mengambil data historis dari service untuk grafik"""
        return self.mqtt_service.get_historical_data()

    def simulate_mqtt_connection(self, username, password):
        try:
            self.mqtt_service.set_credentials(username, password)
            success = self.mqtt_service.connect()
            if success:
                self.update_connection_status()
            return success
        except Exception as e:
            print(f"❌ Connection fail: {e}")
            return False

    def disconnect(self):
        self.mqtt_service.disconnect()

    def set_target_temperature(self, temperature: float):
        return self.mqtt_service.set_target_temperature(temperature)

    def apply_profile(self, profile_name: str):
        return self.mqtt_service.apply_profile(profile_name)

    def get_incubation_profiles(self):
        return self.mqtt_service.get_incubation_profiles()
    
    # --- Compatibility Property ---
    @property
    def data_manager(self):
        return self.mqtt_service