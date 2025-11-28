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
        
        # Device settings and status
        self.device_settings = DEFAULT_SETTINGS.copy()
        self.is_connected = False  # Default: tidak terhubung sampai kredensial valid diinput
        self.connection_attempts = 0
        self.last_data_time = 0
        
        # Initialize motor schedule with default idle state
        import time
        current_time = time.time()
        self.motor_schedule = {
            "last_turn_time": current_time - 10800,  # 3 hours ago (so ready to turn when connected)
            "turn_interval": 10800,  # 3 hours in seconds (3*60*60)
            "rotation_duration": 10,  # 10 seconds
            "current_rotation_start": None,
            "status": "Idle",  # Default idle state when not connected
            "waiting_for_connection": True  # Flag to indicate we're waiting for MQTT connection
        }
        
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
        
        # Initialize MQTT client and connect automatically
        if MQTT_AVAILABLE:
            self.setup_mqtt_connection()
            # Auto connect dengan kredensial yang ada
            self.connect()
            print("✅ MQTT client initialized and attempting connection...")
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
            
            print("🔧 MQTT client configured, ready for connection")
            
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
                print(f"✅ MQTT connected to Teknohole, subscribed to: {topic}")
                print(f"🔊 Listening for sensor data on topic: topic/penetasan/status")
                print(f"🅰️ Waiting for ESP32 to send data on topic: topic/penetasan/status")
                print(f"🅰️ Expected format: {{'temperature': X, 'humidity': Y, 'power': Z, 'rotate_on': A, 'SET': B}}")
                
                # Start motor rotation when MQTT connects for the first time
                if self.motor_schedule["waiting_for_connection"]:
                    self._start_motor_on_connection()
                    
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
            print(f"📩 Message received from topic '{topic}': {payload}")
            
            # Parse JSON data
            data = json.loads(payload)
            print(f"📊 Parsed sensor data: {data}")
            
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
                
                # Log power changes for heater status tracking
                power_changed = abs(self.current_data.get("power", 0) - old_power) > 5
                if power_changed:
                    power_status = "ON" if self.current_data["power"] > 0 else "OFF"
                    print(f"🔥 Heater power: {self.current_data['power']}% ({power_status})")
                
                # Emit signal untuk update GUI real-time
                self.data_received.emit(self.current_data.copy())
                
                print(f"📡 Data REAL dari ESP32 diterima dan diteruskan ke GUI:")
                print(f"    🌡️ Suhu: {self.current_data['temperature']:.1f}°C")
                print(f"    💧 Kelembaban: {self.current_data['humidity']:.1f}%") 
                print(f"    ⚡ Power: {self.current_data['power']}%")
                print(f"    🔄 Rotate: {self.current_data['rotate_on']}s")
                print(f"    🎯 Target: {self.current_data['SET']:.1f}°C")
        
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
        """Check connection health (no auto-reconnect until credentials provided)"""
        # Only attempt reconnection if credentials are available and we previously connected
        if (not self.is_connected and self.mqtt_client and 
            MQTT_SETTINGS["username"] and MQTT_SETTINGS["password"]):
            
            self.connection_attempts += 1
            if self.connection_attempts <= CONNECTION_RETRY["max_attempts"]:
                print(f"🔄 Reconnection attempt {self.connection_attempts}/{CONNECTION_RETRY['max_attempts']}")
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
    
    def toggle_heater(self) -> bool:
        """Toggle heater manually"""
        command = {"HEATER": "TOGGLE"}
        success = self.send_command(command)
        if success:
            # Update local status immediately for UI feedback
            current_power = self.current_data.get("power", 0)
            self.current_data["power"] = 100 if current_power == 0 else 0
            print(f"🔥 Heater toggled: {'ON' if self.current_data['power'] > 0 else 'OFF'}")
        return success
    
    def toggle_humidifier(self) -> bool:
        """Toggle humidifier manually"""
        command = {"HUMIDIFIER": "TOGGLE"}
        success = self.send_command(command)
        if success:
            # Update local status immediately for UI feedback
            current_humidifier_power = self.current_data.get("humidifier_power", 0)
            self.current_data["humidifier_power"] = 100 if current_humidifier_power == 0 else 0
            print(f"💧 Humidifier toggled: {'ON' if self.current_data['humidifier_power'] > 0 else 'OFF'}")
        return success
    
    def toggle_motor(self) -> bool:
        """Manually trigger motor rotation"""
        # Immediately start manual rotation regardless of schedule
        import time
        current_time = time.time()
        
        if not hasattr(self, 'motor_schedule'):
            self.motor_schedule = {
                "last_turn_time": current_time - 10800,
                "turn_interval": 10800,
                "rotation_duration": 10,
                "current_rotation_start": None,
                "status": "Idle"
            }
        
        if self.motor_schedule["status"] == "Berputar":
            # Stop current rotation
            self.motor_schedule["status"] = "Idle"
            self.motor_schedule["current_rotation_start"] = None
            print(f"⏹️ Motor rotation stopped manually")
            return False
        else:
            # Start manual rotation
            self.motor_schedule["current_rotation_start"] = current_time
            self.motor_schedule["status"] = "Berputar"
            print(f"🔄 Manual motor rotation started")
            # Send command to ESP32 if needed
            command = {"MOTOR": "ROTATE"}
            self.send_command(command)
            return True
    
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
        import time
        
        current_time = time.time()
        
        # Initialize motor schedule if not exists
        if not hasattr(self, 'motor_schedule'):
            self.motor_schedule = {
                "last_turn_time": current_time - 10800,  # 3 hours ago
                "turn_interval": 10800,  # 3 hours in seconds (3*60*60)
                "rotation_duration": 10,  # 10 seconds
                "current_rotation_start": None,
                "status": "Idle",
                "waiting_for_connection": True
            }
        
        # Check connection status and update motor accordingly
        if not self.is_connected:
            # When not connected, motor stays idle and countdown shows default 3:00:00
            self.motor_schedule["status"] = "Idle"
            self.motor_schedule["current_rotation_start"] = None
            countdown_text = "03:00:00"
        else:
            # Update motor status based on schedule when connected
            self._update_motor_status(current_time)
            
            # Calculate countdown based on motor status
            if self.motor_schedule["status"] == "Berputar":
                if self.motor_schedule["current_rotation_start"] is not None:
                    rotation_elapsed = current_time - self.motor_schedule["current_rotation_start"]
                    remaining_time = max(0, int(self.motor_schedule["rotation_duration"] - rotation_elapsed))
                    countdown_text = f"{remaining_time}s"
                else:
                    countdown_text = "Berputar"
            else:
                # Calculate time until next rotation
                time_since_last_turn = current_time - self.motor_schedule["last_turn_time"]
                remaining_time = max(0, int(self.motor_schedule["turn_interval"] - time_since_last_turn))
                hours = remaining_time // 3600
                minutes = (remaining_time % 3600) // 60
                seconds = remaining_time % 60
                countdown_text = f"{hours}:{minutes:02d}:{seconds:02d}"
        
        return {
            "pemanas": {
                "status": "Aktif" if self.current_data["power"] > 0 else "Non-aktif",
                "active": self.current_data["power"] > 0
            },
            "humidifier": {
                "status": "Aktif" if self.current_data.get("humidifier_power", 0) > 0 else "Non-aktif",
                "active": self.current_data.get("humidifier_power", 0) > 0
            },
            "motor": {
                "status": self.motor_schedule["status"],
                "active": self.motor_schedule["status"] == "Berputar",
                "rotation_time": remaining_time if self.motor_schedule["status"] == "Berputar" else 0
            },
            "timer": {
                "countdown": countdown_text
            },
            "buzzer": {
                "status": self.device_settings.get("buzzer_state", "OFF"),
                "active": self.device_settings.get("buzzer_state", "OFF") == "ON"
            }
        }
    
    def _update_motor_status(self, current_time: float):
        """Update motor status based on 3-hour schedule (only when connected)"""
        # Only update motor status if connected to MQTT
        if not self.is_connected:
            self.motor_schedule["status"] = "Idle"
            self.motor_schedule["current_rotation_start"] = None
            return
            
        time_since_last_turn = current_time - self.motor_schedule["last_turn_time"]
        turn_interval = self.motor_schedule["turn_interval"]
        rotation_duration = self.motor_schedule["rotation_duration"]
        
        # Check if motor is currently rotating
        if self.motor_schedule["current_rotation_start"] is not None:
            rotation_elapsed = current_time - self.motor_schedule["current_rotation_start"]
            
            if rotation_elapsed < rotation_duration:
                # Motor is currently rotating
                self.motor_schedule["status"] = "Berputar"
            else:
                # Rotation finished, set to idle
                self.motor_schedule["status"] = "Idle"
                self.motor_schedule["current_rotation_start"] = None
                self.motor_schedule["last_turn_time"] = current_time
                print(f"✅ Motor rotation completed (10s)")
        else:
            # Motor not rotating - check if it's time to start
            if time_since_last_turn >= turn_interval:
                # Time to start rotation
                self.motor_schedule["current_rotation_start"] = current_time
                self.motor_schedule["status"] = "Berputar"
                print(f"🔄 Motor rotation started (10s every 3 hours)")
            else:
                # Still waiting for next turn
                self.motor_schedule["status"] = "Idle"
    
    def update_motor_realtime(self):
        """Real-time motor status update every second"""
        import time
        current_time = time.time()
        
        # Initialize motor schedule if not exists
        if not hasattr(self, 'motor_schedule'):
            self.motor_schedule = {
                "last_turn_time": current_time - 10800,  # 3 hours ago
                "turn_interval": 10800,  # 3 hours in seconds (3*60*60)
                "rotation_duration": 10,  # 10 seconds
                "current_rotation_start": None,
                "status": "Idle",
                "waiting_for_connection": True
            }
        
        # Update motor status (only when connected)
        self._update_motor_status(current_time)
        
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
        """Get available incubation profiles"""
        return [
            {"name": "Ayam (38°C, 60%)", "temperature": 38.0, "humidity": 60.0, "duration": 21},
            {"name": "Bebek (37.5°C, 65%)", "temperature": 37.5, "humidity": 65.0, "duration": 28}
        ]
    
    def apply_profile(self, profile_name: str) -> bool:
        """Apply incubation profile"""
        profiles = self.get_incubation_profiles()
        for profile in profiles:
            if profile["name"] == profile_name:
                # Update both temperature and humidity targets
                temp_success = self.set_target_temperature(profile["temperature"])
                self.device_settings["target_humidity"] = profile["humidity"]
                
                if temp_success:
                    self.device_settings["total_days"] = profile["duration"]
                    print(f"✅ Profile '{profile_name}' applied: {profile['temperature']}°C, {profile['humidity']}%")
                return temp_success
        return False
    
    def connect(self):
        """Manually connect to MQTT broker with current credentials"""
        if not MQTT_AVAILABLE:
            self.error_occurred.emit("MQTT library tidak tersedia")
            return False
            
        try:
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
        if self.mqtt_client:
            print("🔌 Disconnecting from MQTT broker...")
            self.mqtt_client.loop_stop()
            self.mqtt_client.disconnect()
        
        self.is_connected = False
        self.connection_changed.emit(False)
        
        if hasattr(self, 'connection_timer'):
            self.connection_timer.stop()
            
        if hasattr(self, 'motor_timer'):
            self.motor_timer.stop()
            print("⏹️ Motor real-time timer stopped")
    
    def _start_motor_on_connection(self):
        """Start motor rotation when MQTT first connects"""
        import time
        current_time = time.time()
        
        # Clear waiting flag
        self.motor_schedule["waiting_for_connection"] = False
        
        # Start immediate rotation upon connection
        self.motor_schedule["current_rotation_start"] = current_time
        self.motor_schedule["status"] = "Berputar"
        self.motor_schedule["last_turn_time"] = current_time
        
        print(f"🔄 Motor rotation started immediately upon MQTT connection (10s)")
        
        # Send motor command to ESP32 if needed
        command = {"MOTOR": "ROTATE"}
        self.send_command(command)
    
    def _reset_motor_to_idle(self):
        """Reset motor to idle state when MQTT disconnects"""
        self.motor_schedule["status"] = "Idle"
        self.motor_schedule["current_rotation_start"] = None
        self.motor_schedule["waiting_for_connection"] = True
        print(f"⏸️ Motor reset to idle state (disconnected from MQTT)")
    
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