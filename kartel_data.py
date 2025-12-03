import json
import time
import threading
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List
from PyQt6.QtCore import QObject, pyqtSignal, QTimer

# Import MQTT client
try:
    import paho.mqtt.client as mqtt
    MQTT_AVAILABLE = True
except ImportError:
    MQTT_AVAILABLE = False
    print("❌ paho-mqtt not installed. Run: pip install paho-mqtt")

from config import MQTT_SETTINGS, DATA_FORMAT, DEFAULT_SETTINGS, CONNECTION_RETRY

class KartelRealDataManager(QObject):
    """Mengelola data sensor real dari ESP32 melalui MQTT Teknohole"""
    
    # Sinyal untuk pembaruan real-time
    data_received = pyqtSignal(dict)
    connection_changed = pyqtSignal(bool)
    error_occurred = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        
        # Current sensor values dari ESP32 (awalnya kosong, menunggu data real)
        self.current_data = {
            "temperature": 0.0,  # Akan diisi dari data MQTT real
            "humidity": 0.0,     # Akan diisi dari data MQTT real
            "power": 0,
            "rotate_on": 0,
            "SET": DEFAULT_SETTINGS["target_temperature"],
            "humidifier_power": 0  # Track humidifier status
        }
        
        # Pengaturan perangkat dan status
        self.device_settings = DEFAULT_SETTINGS.copy()
        self.target_temperature = DEFAULT_SETTINGS["target_temperature"]  # Target terpisah yang tidak ter-override MQTT
        self.current_data["SET"] = self.target_temperature  # Sync SET dengan target
        self.is_connected = False  
        self.connection_attempts = 0
        self.last_data_time = 0
        self.user_disconnected = False  # Flag untuk mencegah auto reconnect setelah user disconnect
        self.manual_connect_required = True  # Flag untuk mencegah auto connect sampai user manual connect pertama kali
        
        # Pelacakan hari penetasan
        self.incubation_data_file = "incubation_data.json"
        self.incubation_start_date = None
        self.load_incubation_data()  # Memuat data penetasan yang ada
        
        # Timer pembaruan harian untuk pelacakan hari penetasan
        self.daily_timer = QTimer()
        self.daily_timer.timeout.connect(self.update_daily_tracking)
        self.daily_timer.start(60000)  # Cek setiap menit
        
        # Penyimpanan data historis
        self.historical_data = {
            "timestamps": [],
            "temperature": [],
            "humidity": [],
            "max_points": DATA_FORMAT["history_max_points"]
        }
        
        # Pengaturan klien MQTT
        self.mqtt_client = None
        self.connection_timer = QTimer()
        self.connection_timer.timeout.connect(self.check_connection)
        self.connection_timer.start(30000)  # Cek setiap 30 detik
        
        # Timer jadwal motor real-time
        self.motor_timer = QTimer()
        self.motor_timer.timeout.connect(self.update_motor_realtime)
        self.motor_timer.start(1000)  # Perbarui setiap detik untuk countdown real-time
        
        # Inisialisasi klien MQTT (TANPA auto connect - user harus manual connect)
        if MQTT_AVAILABLE:
            self.setup_mqtt_connection()
        else:
            self.error_occurred.emit("MQTT library tidak tersedia")
    
    def setup_mqtt_connection(self):
        """Pengaturan klien MQTT (tidak langsung terhubung sampai kredensial diberikan)"""
        try:
            # Buat klien MQTT dengan sesi bersih
            self.mqtt_client = mqtt.Client(client_id="kartel_gui_" + str(int(time.time())))
            
            # Atur callback
            self.mqtt_client.on_connect = self.on_mqtt_connect
            self.mqtt_client.on_disconnect = self.on_mqtt_disconnect
            self.mqtt_client.on_message = self.on_mqtt_message
            self.mqtt_client.on_connect_fail = self.on_connect_fail
            
        except Exception as e:
            error_msg = f"MQTT setup error: {str(e)}"
            print(f"❌ {error_msg}")
            self.error_occurred.emit(error_msg)
            self.is_connected = False
            self.connection_changed.emit(False)
    
    def on_mqtt_connect(self, client, userdata, flags, rc):
        """Callback koneksi MQTT"""
        if rc == 0:
            self.is_connected = True
            self.connection_attempts = 0
            self.connection_changed.emit(True)
            
            # Berlangganan topik data sensor
            topic = MQTT_SETTINGS["topics"]["sensor_data"]
            result, mid = client.subscribe(topic, MQTT_SETTINGS["qos"])
            
            if result == mqtt.MQTT_ERR_SUCCESS:
                print(f"✅ MQTT Connected - Listening for sensor data on: {topic}")
                
                # Mulai pelacakan hari penetasan pada koneksi pertama yang berhasil
                self.start_incubation_tracking()
                    
            else:
                print(f"⚠ Subscription failed: {result}")
        else:
            error_codes = {
                1: "Incorrect protocol version",
                2: "Invalid client identifier", 
                3: "Server unavailable",
                4: "Bad username or password",
                5: "Not authorised"
            }
            error_msg = f"MQTT connection failed: {error_codes.get(rc, f'Unknown error {rc}')}"
            print(f"❌ {error_msg}")
            self.error_occurred.emit(error_msg)
            self.is_connected = False
            self.connection_changed.emit(False)
    
    def on_connect_fail(self, client, userdata):
        """Callback kegagalan koneksi MQTT"""
        print("❌ MQTT connection failed to establish")
        self.is_connected = False
        self.connection_changed.emit(False)
    
    def on_mqtt_disconnect(self, client, userdata, rc):
        """Callback pemutusan koneksi MQTT"""
        self.is_connected = False
        self.connection_changed.emit(False)
        
        # Reset motor ke state idle ketika terputus
        self._reset_motor_to_idle()
        
        if rc != 0:
            print(f"⚠ MQTT unexpected disconnect: {rc}")
            # Auto-reconnect akan ditangani oleh check_connection
        else:
            print("🔌 MQTT disconnected cleanly")
    
    def on_mqtt_message(self, client, userdata, msg):
        """Callback pesan MQTT diterima"""
        try:
            # Decode pesan
            topic = msg.topic
            payload = msg.payload.decode('utf-8')
            
            # Parse data JSON
            data = json.loads(payload)
            
            # Proses data sensor yang diterima
            self.process_sensor_data(data)
            
        except json.JSONDecodeError as e:
            error_msg = f"Invalid JSON received from topic '{msg.topic}': {payload}"
            print(f"⚠ {error_msg}")
            self.error_occurred.emit(error_msg)
        except Exception as e:
            error_msg = f"Error processing MQTT message from '{msg.topic}': {str(e)}"
            print(f"⚠ {error_msg}")
            self.error_occurred.emit(error_msg)
    
    def process_sensor_data(self, data):
        """Proses data sensor yang diterima dari ESP32"""
        try:
            # Perbarui data saat ini jika kunci ada
            updated = False
            old_temp = self.current_data["temperature"]
            old_humidity = self.current_data["humidity"]
            old_power = self.current_data.get("power", 0)
            old_rotate = self.current_data.get("rotate_on", 0)
            
            # Proses setiap field yang diharapkan (kecuali SET yang bisa override target kita)
            for key in ["temperature", "humidity", "power", "rotate_on", "humidifier_power"]:
                if key in data:
                    value = data[key]
                    # Konversi ke float jika berupa angka
                    if isinstance(value, (int, float)):
                        self.current_data[key] = float(value)
                        updated = True
                    elif isinstance(value, str) and value.replace('.', '').replace('-', '').isdigit():
                        self.current_data[key] = float(value)
                        updated = True
            
            # Proses SET secara terpisah - hanya update jika ada nilai valid dan berbeda
            if "SET" in data and data["SET"] != 0:
                try:
                    set_value = float(data["SET"])
                    if set_value > 0 and set_value != self.target_temperature:
                        # Hanya update target jika nilai SET dari ESP32 valid dan berbeda
                        print(f"📡 Received SET command from ESP32: {set_value}°C")
                        self.current_data["SET"] = set_value
                        self.target_temperature = set_value
                        updated = True
                except (ValueError, TypeError):
                    pass  # Ignore invalid SET values
            
            if updated:
                # Perbarui waktu data terakhir
                self.last_data_time = time.time()
                
                # Tambahkan ke data historis jika suhu atau kelembaban berubah signifikan
                temp_changed = abs(self.current_data["temperature"] - old_temp) > 0.1
                humidity_changed = abs(self.current_data["humidity"] - old_humidity) > 0.5
                
                if temp_changed or humidity_changed:
                    self.add_to_history(
                        self.current_data["temperature"],
                        self.current_data["humidity"]
                    )
                    # Log perubahan suhu dan kelembaban
                    print(f"🌡️ Temperature: {self.current_data['temperature']:.1f}°C")
                    print(f"💧 Humidity: {self.current_data['humidity']:.1f}%")
                
                # Log perubahan daya untuk pelacakan status heater
                power_changed = abs(self.current_data.get("power", 0) - old_power) > 5
                if power_changed:
                    power_status = "ON" if self.current_data["power"] > 0 else "OFF"
                    print(f"🔥 Heater Power: {self.current_data['power']}% ({power_status})")
                
                # Log perubahan status rotasi motor dari ESP32
                rotate_changed = self.current_data.get("rotate_on", 0) != old_rotate
                if rotate_changed:
                    motor_status = "Berputar" if self.current_data["rotate_on"] == 1 else "Idle"
                    print(f"🔄 Motor Status: {motor_status} (dari ESP32)")
                
                # Hanya log status data sesekali untuk menghindari spam
                if temp_changed or humidity_changed or power_changed or rotate_changed:
                    power_status = "ON" if self.current_data["power"] > 0 else "OFF"
                    print(f"🔥 Heater Power: {self.current_data['power']}% ({power_status})")
                
                # Emit sinyal untuk update GUI real-time
                self.data_received.emit(self.current_data.copy())
                
                # Log data penting dari ESP32
                print(f"📡 ESP32 Data: T={self.current_data['temperature']:.1f}°C, H={self.current_data['humidity']:.1f}%, Power={self.current_data['power']}%")
        
        except Exception as e:
            error_msg = f"Error memproses data sensor: {str(e)}"
            print(f"⚠ {error_msg}")
            self.error_occurred.emit(error_msg)
    
    def add_to_history(self, temperature, humidity):
        """Tambahkan titik data ke data historis"""
        current_time = time.time()
        
        self.historical_data["timestamps"].append(current_time)
        self.historical_data["temperature"].append(temperature)
        self.historical_data["humidity"].append(humidity)
        
        # Simpan hanya N titik terakhir
        max_points = self.historical_data["max_points"]
        if len(self.historical_data["timestamps"]) > max_points:
            self.historical_data["timestamps"] = self.historical_data["timestamps"][-max_points:]
            self.historical_data["temperature"] = self.historical_data["temperature"][-max_points:]
            self.historical_data["humidity"] = self.historical_data["humidity"][-max_points:]
    
    def check_connection(self):
        """Cek kesehatan koneksi (tidak auto-reconnect jika user sudah disconnect manual)"""
        # Jangan reconnect jika user sudah disconnect secara manual
        if self.user_disconnected:
            return
            
        # Hanya coba reconnection jika kredensial tersedia dan kita pernah terhubung sebelumnya
        if (not self.is_connected and self.mqtt_client and 
            MQTT_SETTINGS["username"] and MQTT_SETTINGS["password"]):
            
            self.connection_attempts += 1
            if self.connection_attempts <= CONNECTION_RETRY["max_attempts"]:
                try:
                    self.mqtt_client.reconnect()
                except:
                    pass  # Akan ditangani oleh callbacks
        
        # Cek apakah kita menerima data
        if self.is_connected and self.last_data_time > 0:
            time_since_data = time.time() - self.last_data_time
            if time_since_data > 60:  # Tidak ada data selama 1 menit
                print("⚠ No data received for 1 minute")
    
    # ========== Metode Perintah ==========
    
    def send_command(self, command: dict) -> bool:
        """Kirim perintah ke ESP32 melalui MQTT"""
        if not self.is_connected or not self.mqtt_client:
            error_msg = "Tidak terhubung ke MQTT broker"
            print(f"❌ {error_msg}")
            self.error_occurred.emit(error_msg)
            return False
        
        try:
            command_json = json.dumps(command)
            topic = MQTT_SETTINGS["topics"]["command"]
            
            result = self.mqtt_client.publish(topic, command_json, MQTT_SETTINGS["qos"])
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                print(f"✅ Command sent: {command_json}")
                return True
            else:
                error_msg = f"Gagal mengirim perintah: {result.rc}"
                print(f"❌ {error_msg}")
                self.error_occurred.emit(error_msg)
                return False
                
        except Exception as e:
            error_msg = f"Error mengirim perintah: {str(e)}"
            print(f"❌ {error_msg}")
            self.error_occurred.emit(error_msg)
            return False
    
    def set_target_temperature(self, temperature: float) -> bool:
        """Kirim suhu target ke ESP32"""
        if not (20.0 <= temperature <= 50.0):
            error_msg = f"Suhu tidak valid: {temperature}. Harus 20-50°C"
            print(f"⚠ {error_msg}")
            self.error_occurred.emit(error_msg)
            return False
        
        command = {"SET": str(temperature)}
        success = self.send_command(command)
        if success:
            self.target_temperature = temperature  # Simpan target terpisah
            self.device_settings["target_temperature"] = temperature
            print(f"🎯 Target Temperature: {temperature}°C (Set via MQTT)")
        return success
    
    def set_buzzer(self, state: str) -> bool:
        """Kontrol buzzer ON/OFF"""
        if state not in ["ON", "OFF"]:
            error_msg = f"Status buzzer tidak valid: {state}. Harus ON atau OFF"
            print(f"⚠ {error_msg}")
            self.error_occurred.emit(error_msg)
            return False
        
        command = {"BUZZER": state}
        success = self.send_command(command)
        if success:
            self.device_settings["buzzer_state"] = state
        return success
    
    def set_relay_timing(self, on_time: int, interval: int) -> bool:
        """Atur waktu relay (on_time dalam detik, interval dalam menit)"""
        if not (1 <= on_time <= 300) or not (1 <= interval <= 60):
            error_msg = f"Waktu relay tidak valid: {on_time}s/{interval}min. Rentang valid: 1-300s, 1-60min"
            print(f"⚠ {error_msg}")
            self.error_occurred.emit(error_msg)
            return False
        
        command = {"RT_ON": str(on_time), "RT_INT": str(interval)}
        success = self.send_command(command)
        if success:
            self.device_settings["relay_on_time"] = on_time
            self.device_settings["relay_interval"] = interval
        return success
    

    
    # ========== Metode Interface untuk Controller ==========
    
    def get_current_readings(self) -> Dict[str, float]:
        """Dapatkan pembacaan sensor saat ini"""
        return {
            "temperature": self.current_data["temperature"],
            "humidity": self.current_data["humidity"]
        }
    
    def get_target_values(self) -> Dict[str, float]:
        """Dapatkan nilai target setpoint"""
        return {
            "temperature": self.target_temperature,  # Gunakan target terpisah, bukan dari MQTT SET
            "humidity": self.device_settings["target_humidity"]
        }
    
    def set_target_values(self, temperature: float = None, humidity: float = None):
        """Atur nilai target baru"""
        if temperature is not None:
            self.target_temperature = temperature  # Set target terpisah
            self.current_data["SET"] = temperature  # Sync dengan current_data
            self.set_target_temperature(temperature)
        if humidity is not None:
            self.device_settings["target_humidity"] = max(60.0, min(80.0, humidity))
    
    def get_device_status(self) -> Dict[str, Any]:
        """Dapatkan status perangkat berdasarkan data sensor real dan perintah MQTT"""
        # Status motor sekarang langsung dari data MQTT rotate_on
        return {
            "power": {
                "value": self.current_data["power"],
                "status": "ON" if self.current_data["power"] > 0 else "OFF",
                "active": self.current_data["power"] > 0
            },
            "motor": {
                "status": "Berputar" if self.current_data.get("rotate_on", 0) == 1 else "Idle",
                "active": self.current_data.get("rotate_on", 0) == 1,
                "rotation_time": 0  
            },
            "timer": {
                "countdown": "03:00:00"  
            },
            "buzzer": {
                "status": self.device_settings.get("buzzer_state", "OFF"),
                "active": self.device_settings.get("buzzer_state", "OFF") == "ON"
            }
        }
    

    
    def update_motor_realtime(self):
        """Perbarui status motor secara real-time menggunakan data MQTT rotate_on"""
        # Status motor sekarang langsung dari data MQTT rotate_on
        # Tidak perlu logika penjadwalan internal
        
        # Emit pembaruan status perangkat
        device_status = self.get_device_status()
        self.emit_status_update(device_status)
        
        # Emit pembaruan status perangkat untuk refresh GUI real-time
        device_status = self.get_device_status()
        # Hanya emit jika ada listeners (GUI terhubung)
        if hasattr(self, 'data_received'):
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(0, lambda: self.emit_status_update(device_status))
    
    def emit_status_update(self, device_status):
        """Emit sinyal pembaruan status"""
        # Ini akan terhubung ke pembaruan GUI di controller
        if hasattr(self, '_status_callback'):
            self._status_callback(device_status)
    
    def get_connection_status(self) -> Dict[str, Any]:
        """Dapatkan status koneksi MQTT saat ini dan info hari penetasan"""
        current_day = self.get_current_incubation_day()
        total_days = self.device_settings.get("total_days", 21)
        
        # Perbarui pengaturan perangkat dengan hari yang dihitung saat ini
        self.device_settings["incubation_day"] = current_day
        
        return {
            "connected": self.is_connected,
            "status_text": "Terhubung" if self.is_connected else "Tidak Terhubung",
            "connection_type": "MQTT Teknohole",
            "broker": f"{MQTT_SETTINGS['broker']}:{MQTT_SETTINGS['port']}",
            "day": current_day,
            "total_days": total_days,
            "day_text": f"Hari ke- {current_day} dari {total_days}",
            "start_date": self.incubation_start_date.strftime('%Y-%m-%d') if self.incubation_start_date else None,
            "days_remaining": max(0, total_days - current_day)
        }
    
    def get_historical_data(self) -> Dict[str, List]:
        """Dapatkan data historis untuk grafik"""
        if not self.historical_data["timestamps"]:
            return {"hours": [], "time_labels": [], "temperature": [], "humidity": []}
        
        # Konversi timestamp ke jam dan label waktu
        hours = []
        time_labels = []
        
        for timestamp in self.historical_data["timestamps"]:
            dt = datetime.fromtimestamp(timestamp)
            hours.append(dt.hour + dt.minute/60.0)
            time_labels.append(f"{dt.hour:02d}:{dt.minute:02d}")
        
        return {
            "hours": hours,
            "time_labels": time_labels,
            "temperature": self.historical_data["temperature"],
            "humidity": self.historical_data["humidity"]
        }
    
    def get_incubation_profiles(self) -> List[Dict]:
        """Dapatkan profil penetasan yang tersedia (suhu saja)"""
        return [
            {"name": "Ayam (38°C)", "temperature": 38.0, "duration": 21},
            {"name": "Bebek (37.5°C)", "temperature": 37.5, "duration": 28}
        ]
    
    def apply_profile(self, profile_name: str) -> bool:
        """Terapkan profil penetasan (suhu saja)"""
        profiles = self.get_incubation_profiles()
        for profile in profiles:
            if profile["name"] == profile_name:
                # Perbarui target suhu saja
                temp_success = self.set_target_temperature(profile["temperature"])
                # Gunakan kelembaban default (60%) untuk semua profil
                self.device_settings["target_humidity"] = 60.0
                
                if temp_success:
                    self.target_temperature = profile["temperature"]  # Set target terpisah juga
                    self.device_settings["total_days"] = profile["duration"]
                    # Simpan data penetasan yang diperbarui ketika profil berubah
                    if self.incubation_start_date:
                        self.save_incubation_data()
                    print(f"✅ Profile '{profile_name}' applied: {profile['temperature']}°C, Default Humidity: 60%")
                    print(f"📊 Incubation duration updated: {profile['duration']} days")
                return temp_success
        return False
    
    def connect(self):
        """Terhubung secara manual ke broker MQTT dengan kredensial saat ini"""
        if not MQTT_AVAILABLE:
            self.error_occurred.emit("MQTT library tidak tersedia")
            return False
            
        try:
            # Reset flag user disconnected ketika user manual connect
            self.user_disconnected = False
            
            # Cek apakah kredensial disediakan
            if not MQTT_SETTINGS["username"] or not MQTT_SETTINGS["password"]:
                error_msg = "Username dan password MQTT diperlukan"
                print(f"❌ {error_msg}")
                self.error_occurred.emit(error_msg)
                return False
            
            # Setup klien MQTT dulu jika belum ada
            if self.mqtt_client is None:
                self.setup_mqtt_connection()
            
            # Set username dan password
            self.mqtt_client.username_pw_set(
                MQTT_SETTINGS["username"], 
                MQTT_SETTINGS["password"]
            )
            
            # Connect to Teknohole broker
            print(f"🔄 Connecting to {MQTT_SETTINGS['broker']}:{MQTT_SETTINGS['port']} with credentials...")
            print(f"📡 Username: {MQTT_SETTINGS['username']}")
            print(f"📡 Topic untuk data sensor: topic/penetasan/status")
            
            self.mqtt_client.connect_async(
                MQTT_SETTINGS["broker"], 
                MQTT_SETTINGS["port"], 
                MQTT_SETTINGS["keepalive"]
            )
            
            # Mulai loop MQTT di background
            self.mqtt_client.loop_start()
            
            return True
            
        except Exception as e:
            error_msg = f"MQTT connection error: {str(e)}"
            print(f"❌ {error_msg}")
            self.error_occurred.emit(error_msg)
            self.is_connected = False
            self.connection_changed.emit(False)
            return False
    
    def disconnect(self):
        """Putuskan koneksi dari broker MQTT"""
        # Set flag bahwa user disconnect secara manual
        self.user_disconnected = True
        
        if self.mqtt_client and self.is_connected:
            self.mqtt_client.loop_stop()
            self.mqtt_client.disconnect()
            print(f"🔌 MQTT Disconnected")
        elif self.mqtt_client:
            self.mqtt_client.loop_stop()
        
        self.is_connected = False
        self.connection_changed.emit(False)
        
        if hasattr(self, 'connection_timer'):
            self.connection_timer.stop()
            print("⏹️ Connection timer stopped")
            
        if hasattr(self, 'motor_timer'):
            self.motor_timer.stop()
            print("⏹️ Motor real-time timer stopped")
    
    ## Pelacakan Hari Proses Penetasan
    def load_incubation_data(self):
        """Muat data pelacakan penetasan dari file lokal"""
        try:
            if os.path.exists(self.incubation_data_file):
                with open(self.incubation_data_file, 'r') as f:
                    data = json.load(f)
                    self.incubation_start_date = data.get('start_date')
                    if self.incubation_start_date:
                        # Parse string tanggal mulai kembali ke datetime
                        self.incubation_start_date = datetime.fromisoformat(self.incubation_start_date)
                        print(f"📅 Loaded incubation start date: {self.incubation_start_date.strftime('%Y-%m-%d %H:%M:%S')}")
                    else:
                        print("📅 No incubation start date found in data file")
            else:
                print("📅 No incubation data file found - will create on first MQTT connection")
        except Exception as e:
            print(f"⚠️ Error loading incubation data: {e}")
            self.incubation_start_date = None
    
    def save_incubation_data(self):
        """Simpan data pelacakan penetasan ke file lokal"""
        try:
            data = {
                'start_date': self.incubation_start_date.isoformat() if self.incubation_start_date else None,
                'total_days': self.device_settings.get('total_days', 21),
                'last_updated': datetime.now().isoformat()
            }
            with open(self.incubation_data_file, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"💾 Incubation data saved to {self.incubation_data_file}")
        except Exception as e:
            print(f"❌ Error saving incubation data: {e}")
    
    def start_incubation_tracking(self):
        """Mulai pelacakan hari penetasan ketika MQTT terhubung untuk pertama kali"""
        if not self.incubation_start_date:
            self.incubation_start_date = datetime.now()
            self.save_incubation_data()
            print(f"🥚 Incubation tracking started: {self.incubation_start_date.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"📊 Target duration: {self.device_settings.get('total_days', 21)} days")
        else:
            current_day = self.get_current_incubation_day()
            print(f"🥚 Continuing incubation tracking: Day {current_day} of {self.device_settings.get('total_days', 21)}")
    
    def get_current_incubation_day(self):
        """Hitung hari penetasan saat ini berdasarkan tanggal mulai"""
        if not self.incubation_start_date:
            return 1  # Default ke hari 1 jika tidak ada tanggal mulai
        
        current_time = datetime.now()
        days_passed = (current_time - self.incubation_start_date).days + 1
        max_days = self.device_settings.get('total_days', 21)
        
        # Batasi di hari maksimum untuk profil
        return min(days_passed, max_days)
    
    def update_daily_tracking(self):
        """Perbarui pelacakan harian dan cek milestone penting"""
        if not self.incubation_start_date:
            return
            
        current_day = self.get_current_incubation_day()
        total_days = self.device_settings.get('total_days', 21)
        
        # Cek milestone penting
        if current_day == total_days:
            print(f"🎉 HARI MENETAS! Hari ke-{current_day} - Telur seharusnya siap menetas!")
        elif current_day > total_days:
            print(f"⏰ Terlambat: Hari ke-{current_day} (Diharapkan: {total_days} hari)")
        elif current_day == total_days - 1:
            print(f"⚠️ Besok hari menetas! Saat ini Hari ke-{current_day} dari {total_days}")
        elif current_day % 7 == 0:  # Milestone mingguan
            print(f"📅 Milestone mingguan: Hari ke-{current_day} dari {total_days} ({total_days - current_day} hari tersisa)")
    
    def reset_incubation_tracking(self):
        """Reset pelacakan penetasan (untuk batch telur baru)"""
        try:
            if os.path.exists(self.incubation_data_file):
                os.remove(self.incubation_data_file)
            self.incubation_start_date = None
            print("🔄 Pelacakan penetasan di-reset - siap untuk batch baru")
        except Exception as e:
            print(f"❌ Error mereset data penetasan: {e}")
    
    def log_real_data_status(self):
        """Log status penerimaan data real untuk debugging"""
        if self.current_data["temperature"] != 0.0 or self.current_data["humidity"] != 0.0:
            print(f"📊 Data REAL tersimpan: T={self.current_data['temperature']:.1f}°C, H={self.current_data['humidity']:.1f}%")
        else:
            print(f"⏳ Belum ada data REAL dari ESP32 - Listening pada topic: topic/penetasan/status")

# Instance global
real_data_manager = None

def get_real_data_manager() -> KartelRealDataManager:
    """Dapatkan instance global real data manager"""
    global real_data_manager
    if real_data_manager is None:
        real_data_manager = KartelRealDataManager()
    return real_data_manager