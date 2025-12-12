import json
import time
import os
from datetime import datetime
from typing import Dict, Any, List
from PyQt6.QtCore import QObject, pyqtSignal, QTimer

# Import Config dan DataStore
from src.config.settings import MQTT_SETTINGS, DATA_FORMAT, DEFAULT_SETTINGS, CONNECTION_RETRY
from src.services.data_store import DataStore

# Cek Library MQTT
try:
    import paho.mqtt.client as mqtt
    MQTT_AVAILABLE = True
except ImportError:
    MQTT_AVAILABLE = False
    print("❌ paho-mqtt not installed. Run: pip install paho-mqtt")

class MqttService(QObject):
    """
    Service utama yang menangani logika bisnis IoT & Inkubasi
    """
    
    # Sinyal untuk Controller
    data_received = pyqtSignal(dict)      # Data sensor baru
    connection_changed = pyqtSignal(bool) # Status koneksi berubah
    error_occurred = pyqtSignal(str)      # Error message
    status_updated = pyqtSignal(dict)     # Update status perangkat (Motor/Timer)
    
    def __init__(self):
        super().__init__()
        self.store = DataStore()
        
        self.current_data = {
            "temperature": 0.0, "humidity": 0.0, "power": 0, "rotate_on": 0,
            "SET": DEFAULT_SETTINGS["target_temperature"], "humidifier_power": 0
        }
        
        self.device_settings = DEFAULT_SETTINGS.copy()
        self.target_temperature = DEFAULT_SETTINGS["target_temperature"]
        
        self.is_connected = False
        self.mqtt_client = None
        self.user_disconnected = False
        self.manual_connect_required = True
        
        # Load Tanggal Mulai
        self.incubation_start_date = self.store.load_incubation_data()
        
        self.historical_data = {
            "timestamps": [], "temperature": [], "humidity": [],
            "max_points": DATA_FORMAT["history_max_points"]
        }
        
        # Motor Logic
        self.motor_start_time = None
        self.motor_duration = self.device_settings["relay_on_time"]
        self.motor_remaining_time = 0
        self.last_motor_state = False

        # Timers
        self.connection_timer = QTimer()
        self.connection_timer.timeout.connect(self._check_connection)
        self.connection_timer.start(30000)
        
        self.motor_timer = QTimer()
        self.motor_timer.timeout.connect(self._update_motor_logic)
        self.motor_timer.start(1000)
        
        self.daily_timer = QTimer()
        self.daily_timer.timeout.connect(self._check_daily_milestones)
        self.daily_timer.start(60000)

        if MQTT_AVAILABLE: self._setup_mqtt_client()
        else: self.error_occurred.emit("Library MQTT tidak ditemukan!")

    # =========================================================================
    # FITUR BARU: MANUAL DATE SETTING
    # =========================================================================
    
    def set_manual_start_date(self, year, month, day):
        """Update tanggal mulai secara manual dari GUI"""
        try:
            # Set waktu ke awal hari (00:00:00) dari tanggal yang dipilih
            new_date = datetime(year, month, day)
            self.incubation_start_date = new_date
            
            # Simpan ke JSON agar permanen
            self.store.save_incubation_data(
                self.incubation_start_date, 
                self.device_settings["total_days"]
            )
            
            print(f"📅 Start Date Updated Manually: {new_date.strftime('%Y-%m-%d')}")
            
            # Paksa update UI Header (Hari ke-X)
            # Kita emit connection_changed karena Header menyimak sinyal ini
            self.connection_changed.emit(self.is_connected) 
            
            return True
        except Exception as e:
            print(f"❌ Error setting date: {e}")
            return False

    def get_start_date(self):
        """Mengambil tanggal mulai saat ini untuk inisialisasi kalender di GUI"""
        return self.incubation_start_date

    # =========================================================================
    # MQTT CONNECTION
    # =========================================================================
    
    def _setup_mqtt_client(self):
        try:
            client_id = f"kartel_gui_{int(time.time())}"
            self.mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, client_id=client_id)
            self.mqtt_client.on_connect = self._on_connect
            self.mqtt_client.on_disconnect = self._on_disconnect
            self.mqtt_client.on_message = self._on_message
        except Exception as e:
            self.error_occurred.emit(f"MQTT Setup Error: {e}")

    def set_credentials(self, username, password):
        MQTT_SETTINGS["username"] = username
        MQTT_SETTINGS["password"] = password

    def connect(self):
        if not MQTT_AVAILABLE or not self.mqtt_client: return False
        try:
            self.user_disconnected = False
            username = MQTT_SETTINGS["username"]
            password = MQTT_SETTINGS["password"]
            if not username or not password:
                self.error_occurred.emit("Username/Password kosong")
                return False
            self.mqtt_client.username_pw_set(username, password)
            self.mqtt_client.connect_async(MQTT_SETTINGS["broker"], MQTT_SETTINGS["port"], MQTT_SETTINGS["keepalive"])
            self.mqtt_client.loop_start()
            return True
        except Exception as e:
            self.error_occurred.emit(f"Connection Error: {e}")
            return False

    def disconnect(self):
        self.user_disconnected = True
        if self.mqtt_client:
            self.mqtt_client.loop_stop()
            self.mqtt_client.disconnect()

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.is_connected = True
            self.connection_changed.emit(True)
            topic = MQTT_SETTINGS["topics"]["sensor_data"]
            client.subscribe(topic, MQTT_SETTINGS["qos"])
            
            # Auto-start incubation date if None
            if not self.incubation_start_date:
                self.incubation_start_date = datetime.now()
                self.store.save_incubation_data(self.incubation_start_date, self.device_settings["total_days"])
        else:
            self.is_connected = False
            self.connection_changed.emit(False)

    def _on_disconnect(self, client, userdata, rc):
        self.is_connected = False
        self.connection_changed.emit(False)
        self._reset_motor_state()

    def _on_message(self, client, userdata, msg):
        try:
            payload = msg.payload.decode('utf-8')
            data = json.loads(payload)
            self._process_sensor_data(data)
        except Exception: pass

    def _process_sensor_data(self, data):
        updated = False
        valid_keys = ["temperature", "humidity", "power", "rotate_on", "SET"]
        for key in valid_keys:
            if key in data:
                try:
                    val = float(data[key])
                    if key == "relay_interval":
                        self.device_settings["relay_interval"] = int(val)
                    else:
                        self.current_data[key] = val
                    updated = True
                    if key == "SET":
                        self.target_temperature = val
                        self.device_settings["target_temperature"] = val
                except ValueError: pass
        if updated:
            self._update_history(self.current_data["temperature"], self.current_data["humidity"])
            self.data_received.emit(self.current_data.copy())

    def _update_history(self, temp, humidity):
        self.historical_data["timestamps"].append(time.time())
        self.historical_data["temperature"].append(temp)
        self.historical_data["humidity"].append(humidity)
        max_pts = self.historical_data["max_points"]
        if len(self.historical_data["timestamps"]) > max_pts:
             self.historical_data["timestamps"] = self.historical_data["timestamps"][-max_pts:]
             self.historical_data["temperature"] = self.historical_data["temperature"][-max_pts:]
             self.historical_data["humidity"] = self.historical_data["humidity"][-max_pts:]

    def _update_motor_logic(self):
        rotate_val = self.current_data.get("rotate_on", 0)
        is_rotating=rotate_val !=0
        self.motor_remaining_time=rotate_val

    def _reset_motor_state(self):
        self.last_motor_state = False
        self.motor_remaining_time = 0

    def get_device_status(self) -> Dict[str, Any]:
        rotate_val = self.current_data.get("rotate_on")
        
        if rotate_val > 5:
            is_rotating = False
            status_text = "Idle"

            # Format H:M:S untuk countdown aktif
            hours = int(self.motor_remaining_time // 3600)
            minutes = int((self.motor_remaining_time % 3600)) // 60
            seconds = int(self.motor_remaining_time % 60)
            timer_text = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            is_rotating = True
            status_text = "Berputar"
            
            # Format H:M:S untuk interval (idle)
            interval_hours = self.device_settings["relay_interval"]
            timer_text = f"{interval_hours:02d}:00:00"

            hours = int(self.motor_remaining_time // 3600)
            minutes = int((self.motor_remaining_time % 3600)) // 60
            seconds = int(self.motor_remaining_time % 60)
            timer_text = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

        current_day = self._calculate_day()
        total_days = self.device_settings.get("total_days", 21)

        return {
            "power": { "value": self.current_data["power"], "status": "ON" if self.current_data["power"] > 0 else "OFF", "active": self.current_data["power"] > 0 },
            "motor": { "status": status_text, "active": is_rotating },
            "timer": { "countdown": timer_text },
            "incubation": { "day": current_day, "total": total_days }
        }

    def set_target_temperature(self, temp: float) -> bool:
        if not (20.0 <= temp <= 50.0): return False
        self.target_temperature = temp
        self.device_settings["target_temperature"] = temp
        return self._send_command({"SET": temp})

    def apply_profile(self, profile_name: str) -> bool:
        profiles = self.get_incubation_profiles()
        for p in profiles:
            if p["name"] == profile_name:
                self.target_temperature = p["temperature"]
                self.device_settings["total_days"] = p["duration"]
                # Update Data Store jika sudah ada tanggal
                if self.incubation_start_date:
                    self.store.save_incubation_data(self.incubation_start_date, p["duration"])
                self._send_command({"SET": p["temperature"]})
                return True
        return False

    def get_incubation_profiles(self):
        return [{"name": "Ayam (38°C)", "temperature": 38.0, "duration": 21}, {"name": "Bebek (37.5°C)", "temperature": 37.5, "duration": 28}]

    def get_target_values(self):
        return { "temperature": self.target_temperature, "humidity": self.device_settings["target_humidity"] }
    
    def get_historical_data(self): return self.historical_data
    def get_mqtt_settings(self): return MQTT_SETTINGS
        
    def get_connection_status(self):
        day = self._calculate_day()
        total = self.device_settings.get("total_days", 21)
        return { "connected": self.is_connected, "day_text": f"Hari ke-{day} dari {total}" }

    def _send_command(self, command_dict):
        if not self.is_connected: return False
        try:
            payload = json.dumps(command_dict)
            topic = MQTT_SETTINGS["topics"]["command"]
            self.mqtt_client.publish(topic, payload, MQTT_SETTINGS["qos"])
            return True
        except Exception: return False
            
    def _check_connection(self):
        if self.user_disconnected: return
        if not self.is_connected and self.mqtt_client:
            try: self.mqtt_client.reconnect()
            except: pass

    def _calculate_day(self):
        if not self.incubation_start_date: return 1
        delta = datetime.now() - self.incubation_start_date
        return max(1, delta.days + 1)

    def _check_daily_milestones(self): pass