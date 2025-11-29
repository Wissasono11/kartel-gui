import json
import time
import threading
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
    """Manages real sensor data from ESP32 via MQTT Teknohole"""
    
    # Signals for real-time updates
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
        
        # Device settings dan status
        self.device_settings = DEFAULT_SETTINGS.copy()
        self.is_connected = False  
        self.connection_attempts = 0
        self.last_data_time = 0
        self.user_disconnected = False  # Flag untuk mencegah auto reconnect setelah user disconnect
        self.manual_connect_required = True  # Flag untuk mencegah auto connect sampai user manual connect pertama kali
        
        # Historical data storage
        self.historical_data = {
            "timestamps": [],
            "temperature": [],
            "humidity": [],
            "max_points": DATA_FORMAT["history_max_points"]
        }
        
        # MQTT client setup
        self.mqtt_client = None
        self.connection_timer = QTimer()
        self.connection_timer.timeout.connect(self.check_connection)
        self.connection_timer.start(30000)  # Check every 30 seconds
        
        # Real-time motor schedule timer
        self.motor_timer = QTimer()
        self.motor_timer.timeout.connect(self.update_motor_realtime)
        self.motor_timer.start(1000)  # Update every second for real-time countdown
        
        # Initialize MQTT client (TANPA auto connect - user harus manual connect)
        if MQTT_AVAILABLE:
            self.setup_mqtt_connection()
        else:
            self.error_occurred.emit("MQTT library tidak tersedia")
    
    def setup_mqtt_connection(self):
        """Setup MQTT client (doesn't connect until credentials provided)"""
        try:
            # Create MQTT client with clean session
            self.mqtt_client = mqtt.Client(client_id="kartel_gui_" + str(int(time.time())))
            
            # Setup callbacks
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
        """MQTT connect callback"""
        if rc == 0:
            self.is_connected = True
            self.connection_attempts = 0
            self.connection_changed.emit(True)
            
            # Subscribe to sensor data topic
            topic = MQTT_SETTINGS["topics"]["sensor_data"]
            result, mid = client.subscribe(topic, MQTT_SETTINGS["qos"])
            
            if result == mqtt.MQTT_ERR_SUCCESS:
                print(f"✅ MQTT Connected - Listening for sensor data on: {topic}")
                    
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
        """MQTT connection fail callback"""
        print("❌ MQTT connection failed to establish")
        self.is_connected = False
        self.connection_changed.emit(False)
    
    def on_mqtt_disconnect(self, client, userdata, rc):
        """MQTT disconnect callback"""
        self.is_connected = False
        self.connection_changed.emit(False)
        
        # Reset motor to idle state when disconnected
        self._reset_motor_to_idle()
        
        if rc != 0:
            print(f"⚠ MQTT unexpected disconnect: {rc}")
            # Auto-reconnect will be handled by check_connection
        else:
            print("🔌 MQTT disconnected cleanly")
    
    def on_mqtt_message(self, client, userdata, msg):
        """MQTT message received callback"""
        try:
            # Decode message
            topic = msg.topic
            payload = msg.payload.decode('utf-8')
            
            # Parse JSON data
            data = json.loads(payload)
            
            # Process received data
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
        """Process received sensor data from ESP32"""
        try:
            # Update current data if keys exist
            updated = False
            old_temp = self.current_data["temperature"]
            old_humidity = self.current_data["humidity"]
            old_power = self.current_data.get("power", 0)
            old_rotate = self.current_data.get("rotate_on", 0)
            
            # Process each expected field
            for key in ["temperature", "humidity", "power", "rotate_on", "SET", "humidifier_power"]:
                if key in data:
                    value = data[key]
                    # Convert to float if it's a number
                    if isinstance(value, (int, float)):
                        self.current_data[key] = float(value)
                        updated = True
                    elif isinstance(value, str) and value.replace('.', '').replace('-', '').isdigit():
                        self.current_data[key] = float(value)
                        updated = True
            
            if updated:
                # Update last data time
                self.last_data_time = time.time()
                
                # Add to historical data if temperature or humidity changed significantly
                temp_changed = abs(self.current_data["temperature"] - old_temp) > 0.1
                humidity_changed = abs(self.current_data["humidity"] - old_humidity) > 0.5
                
                if temp_changed or humidity_changed:
                    self.add_to_history(
                        self.current_data["temperature"],
                        self.current_data["humidity"]
                    )
                    # Log temperature and humidity changes
                    print(f"🌡️ Temperature: {self.current_data['temperature']:.1f}°C")
                    print(f"💧 Humidity: {self.current_data['humidity']:.1f}%")
                
                # Log power changes for heater status tracking
                power_changed = abs(self.current_data.get("power", 0) - old_power) > 5
                if power_changed:
                    power_status = "ON" if self.current_data["power"] > 0 else "OFF"
                    print(f"🔥 Heater Power: {self.current_data['power']}% ({power_status})")
                
                # Log motor rotation status changes from ESP32
                rotate_changed = self.current_data.get("rotate_on", 0) != old_rotate
                if rotate_changed:
                    motor_status = "Berputar" if self.current_data["rotate_on"] == 1 else "Idle"
                    print(f"🔄 Motor Status: {motor_status} (dari ESP32)")
                
                # Only log data status occasionally to avoid spam
                if temp_changed or humidity_changed or power_changed or rotate_changed:
                    power_status = "ON" if self.current_data["power"] > 0 else "OFF"
                    print(f"🔥 Heater Power: {self.current_data['power']}% ({power_status})")
                
                # Emit signal untuk update GUI real-time
                self.data_received.emit(self.current_data.copy())
                
                # Log data penting dari ESP32
                print(f"📡 ESP32 Data: T={self.current_data['temperature']:.1f}°C, H={self.current_data['humidity']:.1f}%, Power={self.current_data['power']}%")
        
        except Exception as e:
            error_msg = f"Error processing sensor data: {str(e)}"
            print(f"⚠ {error_msg}")
            self.error_occurred.emit(error_msg)
    
    def add_to_history(self, temperature, humidity):
        """Add data point to historical data"""
        current_time = time.time()
        
        self.historical_data["timestamps"].append(current_time)
        self.historical_data["temperature"].append(temperature)
        self.historical_data["humidity"].append(humidity)
        
        # Keep only last N points
        max_points = self.historical_data["max_points"]
        if len(self.historical_data["timestamps"]) > max_points:
            self.historical_data["timestamps"] = self.historical_data["timestamps"][-max_points:]
            self.historical_data["temperature"] = self.historical_data["temperature"][-max_points:]
            self.historical_data["humidity"] = self.historical_data["humidity"][-max_points:]
    
    def check_connection(self):
        """Check connection health (tidak auto-reconnect jika user sudah disconnect manual)"""
        # Jangan reconnect jika user sudah disconnect secara manual
        if self.user_disconnected:
            return
            
        # Only attempt reconnection if credentials are available and we previously connected
        if (not self.is_connected and self.mqtt_client and 
            MQTT_SETTINGS["username"] and MQTT_SETTINGS["password"]):
            
            self.connection_attempts += 1
            if self.connection_attempts <= CONNECTION_RETRY["max_attempts"]:
                try:
                    self.mqtt_client.reconnect()
                except:
                    pass  # Will be handled by callbacks
        
        # Check if we're receiving data
        if self.is_connected and self.last_data_time > 0:
            time_since_data = time.time() - self.last_data_time
            if time_since_data > 60:  # No data for 1 minute
                print("⚠ No data received for 1 minute")
    
    # ========== Command Methods ==========
    
    def send_command(self, command: dict) -> bool:
        """Send command to ESP32 via MQTT"""
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
                error_msg = f"Failed to send command: {result.rc}"
                print(f"❌ {error_msg}")
                self.error_occurred.emit(error_msg)
                return False
                
        except Exception as e:
            error_msg = f"Error sending command: {str(e)}"
            print(f"❌ {error_msg}")
            self.error_occurred.emit(error_msg)
            return False
    
    def set_target_temperature(self, temperature: float) -> bool:
        """Send target temperature to ESP32"""
        if not (20.0 <= temperature <= 50.0):
            error_msg = f"Invalid temperature: {temperature}. Must be 20-50°C"
            print(f"⚠ {error_msg}")
            self.error_occurred.emit(error_msg)
            return False
        
        command = {"SET": str(temperature)}
        success = self.send_command(command)
        if success:
            self.device_settings["target_temperature"] = temperature
            print(f"🎯 Target Temperature: {temperature}°C (Set via MQTT)")
        return success
    
    def set_buzzer(self, state: str) -> bool:
        """Control buzzer ON/OFF"""
        if state not in ["ON", "OFF"]:
            error_msg = f"Invalid buzzer state: {state}. Must be ON or OFF"
            print(f"⚠ {error_msg}")
            self.error_occurred.emit(error_msg)
            return False
        
        command = {"BUZZER": state}
        success = self.send_command(command)
        if success:
            self.device_settings["buzzer_state"] = state
        return success
    
    def set_relay_timing(self, on_time: int, interval: int) -> bool:
        """Set relay timing (on_time in seconds, interval in minutes)"""
        if not (1 <= on_time <= 300) or not (1 <= interval <= 60):
            error_msg = f"Invalid relay timing: {on_time}s/{interval}min. Valid ranges: 1-300s, 1-60min"
            print(f"⚠ {error_msg}")
            self.error_occurred.emit(error_msg)
            return False
        
        command = {"RT_ON": str(on_time), "RT_INT": str(interval)}
        success = self.send_command(command)
        if success:
            self.device_settings["relay_on_time"] = on_time
            self.device_settings["relay_interval"] = interval
        return success
    

    
    # ========== Interface Methods for Controller ==========
    
    def get_current_readings(self) -> Dict[str, float]:
        """Get current sensor readings"""
        return {
            "temperature": self.current_data["temperature"],
            "humidity": self.current_data["humidity"]
        }
    
    def get_target_values(self) -> Dict[str, float]:
        """Get target setpoint values"""
        return {
            "temperature": self.current_data["SET"],
            "humidity": self.device_settings["target_humidity"]
        }
    
    def set_target_values(self, temperature: float = None, humidity: float = None):
        """Set new target values"""
        if temperature is not None:
            self.set_target_temperature(temperature)
        if humidity is not None:
            self.device_settings["target_humidity"] = max(60.0, min(80.0, humidity))
    
    def get_device_status(self) -> Dict[str, Any]:
        """Get device status based on real sensor data and MQTT commands"""
        # Motor status now directly from MQTT rotate_on data
        return {
            "power": {
                "value": self.current_data["power"],
                "status": "ON" if self.current_data["power"] > 0 else "OFF",
                "active": self.current_data["power"] > 0
            },
            "motor": {
                "status": "Berputar" if self.current_data.get("rotate_on", 0) == 1 else "Idle",
                "active": self.current_data.get("rotate_on", 0) == 1,
                "rotation_time": 0  # Not needed when using MQTT data
            },
            "timer": {
                "countdown": "03:00:00"  # Static display since rotation is now MQTT-controlled
            },
            "buzzer": {
                "status": self.device_settings.get("buzzer_state", "OFF"),
                "active": self.device_settings.get("buzzer_state", "OFF") == "ON"
            }
        }
    

    
    def update_motor_realtime(self):
        """Update motor status in real-time using MQTT rotate_on data"""
        # Motor status now directly from MQTT rotate_on data
        # No need for internal scheduling logic
        
        # Emit device status update
        device_status = self.get_device_status()
        self.emit_status_update(device_status)
        
        # Emit device status update for real-time GUI refresh
        device_status = self.get_device_status()
        # Only emit if we have listeners (GUI connected)
        if hasattr(self, 'data_received'):
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(0, lambda: self.emit_status_update(device_status))
    
    def emit_status_update(self, device_status):
        """Emit status update signal"""
        # This will be connected to GUI update in controller
        if hasattr(self, '_status_callback'):
            self._status_callback(device_status)
    
    def get_connection_status(self) -> Dict[str, Any]:
        """Get connection status"""
        return {
            "connected": self.is_connected,
            "status_text": "Terhubung" if self.is_connected else "Tidak Terhubung",
            "connection_type": "MQTT Teknohole",
            "broker": f"{MQTT_SETTINGS['broker']}:{MQTT_SETTINGS['port']}",
            "day": self.device_settings["incubation_day"],
            "total_days": self.device_settings["total_days"],
            "day_text": f"Hari ke- {self.device_settings['incubation_day']} dari {self.device_settings['total_days']}"
        }
    
    def get_historical_data(self) -> Dict[str, List]:
        """Get historical data for graph"""
        if not self.historical_data["timestamps"]:
            return {"hours": [], "time_labels": [], "temperature": [], "humidity": []}
        
        # Convert timestamps to hours and time labels
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
        """Get available incubation profiles (temperature only)"""
        return [
            {"name": "Ayam (38°C)", "temperature": 38.0, "duration": 21},
            {"name": "Bebek (37.5°C)", "temperature": 37.5, "duration": 28}
        ]
    
    def apply_profile(self, profile_name: str) -> bool:
        """Apply incubation profile (temperature only)"""
        profiles = self.get_incubation_profiles()
        for profile in profiles:
            if profile["name"] == profile_name:
                # Update temperature target only
                temp_success = self.set_target_temperature(profile["temperature"])
                # Use default humidity (60%) for all profiles
                self.device_settings["target_humidity"] = 60.0
                
                if temp_success:
                    self.device_settings["total_days"] = profile["duration"]
                    print(f"✅ Profile '{profile_name}' applied: {profile['temperature']}°C, Default Humidity: 60%")
                return temp_success
        return False
    
    def connect(self):
        """Manually connect to MQTT broker with current credentials"""
        if not MQTT_AVAILABLE:
            self.error_occurred.emit("MQTT library tidak tersedia")
            return False
            
        try:
            # Reset flag user disconnected ketika user manual connect
            self.user_disconnected = False
            
            # Check if credentials are provided
            if not MQTT_SETTINGS["username"] or not MQTT_SETTINGS["password"]:
                error_msg = "Username dan password MQTT diperlukan"
                print(f"❌ {error_msg}")
                self.error_occurred.emit(error_msg)
                return False
            
            # Setup MQTT client first if not exists
            if self.mqtt_client is None:
                self.setup_mqtt_connection()
            
            # Set username and password
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
            
            # Start MQTT loop in background
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
        """Disconnect from MQTT broker"""
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
    

    

    
    def log_real_data_status(self):
        """Log status penerimaan data real untuk debugging"""
        if self.current_data["temperature"] != 0.0 or self.current_data["humidity"] != 0.0:
            print(f"📊 Data REAL tersimpan: T={self.current_data['temperature']:.1f}°C, H={self.current_data['humidity']:.1f}%")
        else:
            print(f"⏳ Belum ada data REAL dari ESP32 - Listening pada topic: topic/penetasan/status")

# Global instance
real_data_manager = None

def get_real_data_manager() -> KartelRealDataManager:
    """Get the global real data manager instance"""
    global real_data_manager
    if real_data_manager is None:
        real_data_manager = KartelRealDataManager()
    return real_data_manager