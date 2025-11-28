import sys
import os
import time
import pyqtgraph as pg
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QScrollArea
)
from PyQt6.QtGui import QFont, QFontDatabase, QIcon
from PyQt6.QtCore import Qt, pyqtSlot, QTimer, QSize

# Import our custom modules
from kartel_controller import KartelController
from dashboard_ui_components import DashboardUIComponents
from dashboard_graph_components import DashboardGraphComponents
from dashboard_event_handlers import DashboardEventHandlers
from dashboard_config_panel import DashboardConfigPanel


class KartelDashboard(QWidget):
    """Main dashboard class - modular design for better maintainability"""
    
    def __init__(self):
        super().__init__()
        
        # Initialize data structures
        self.graph_data = {
            "timestamps": [],
            "temperature": [],
            "humidity": [],
            "max_points": 24  # Keep last 24 data points
        }
        
        self.input_fields = {
            'temperature': None,
            'humidity': None
        }
        
        # Initialize components
        self.ui_components = DashboardUIComponents(self)
        self.graph_components = DashboardGraphComponents(self)
        self.event_handlers = DashboardEventHandlers(self)
        self.config_panel = DashboardConfigPanel(self)
        
        # Initialize controller
        self.controller = KartelController()
        self.setup_controller_connections()
        
        # Initialize UI
        self.load_custom_fonts()
        self.init_ui()
        
        # Setup initial state
        self.sync_initial_card_targets()
        QTimer.singleShot(500, self.force_sync_current_profile)
        
        # Initialize display with current values from data manager
        self.update_display_from_real_data()
        
        # Setup timer untuk periodic refresh display (TANPA simulasi)
        self.data_refresh_timer = QTimer()
        self.data_refresh_timer.timeout.connect(self.refresh_display_data)
        self.data_refresh_timer.start(2000)  # Refresh display setiap 2 detik
        
        print("📡 Dashboard siap menerima data REAL dari topic: topic/penetasan/status")
    
    def setup_controller_connections(self):
        """Connect controller signals to GUI update methods"""
        self.controller.data_updated.connect(self.update_sensor_display)
        self.controller.data_updated.connect(self.update_graph_data)
        self.controller.status_updated.connect(self.update_device_status_display)
        self.controller.connection_updated.connect(self.update_connection_display)
    
    def load_custom_fonts(self):
        """Load font Manrope dari berbagai sumber"""
        test_font = QFont("Manrope", 12)
        if test_font.exactMatch():
            print("✅ Font Manrope ditemukan di sistem!")
            return True
        
        font_loaded = False
        font_paths = [
            "fonts/Manrope-Regular.ttf",
            "fonts/Manrope.ttf", 
            "asset/fonts/Manrope-Regular.ttf",
            "Manrope-Regular.ttf"
        ]
        
        for font_path in font_paths:
            if os.path.exists(font_path):
                font_id = QFontDatabase.addApplicationFont(font_path)
                if font_id != -1:
                    print(f"✅ Font Manrope berhasil dimuat dari: {font_path}")
                    font_loaded = True
                    break
        
        if not font_loaded:
            print("⚠ Font Manrope tidak ditemukan, menggunakan fallback")
        
        return font_loaded
    
    def init_ui(self):
        """Initialize user interface"""
        # Pengaturan Jendela Utama
        self.setWindowTitle("KARTEL Dashboard")
        self.setGeometry(100, 100, 1400, 900)
        self.setMinimumSize(1000, 600)
        
        # Layout Utama
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(24)

        # === KOLOM KIRI (Monitoring) ===
        left_column = self.create_left_column()
        
        # === KOLOM KANAN (Konfigurasi) ===
        right_column = self.config_panel.create_config_panel()
        
        # Tambahkan kolom ke layout utama
        main_layout.addWidget(left_column, 7)
        main_layout.addWidget(right_column, 3)

        # Terapkan Stylesheet
        self.set_stylesheet()
    
    def create_left_column(self):
        """Create left monitoring column"""
        left_scroll_area = QScrollArea()
        left_scroll_area.setWidgetResizable(True)
        left_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        left_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        left_scroll_area.setObjectName("leftScrollArea")
        
        left_column = QWidget()
        left_layout = QVBoxLayout(left_column)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(20)

        # 1. Header
        left_layout.addWidget(self.ui_components.create_header())
        
        # 2. Card Vital (Suhu & Kelembaban)
        left_layout.addWidget(self.ui_components.create_vital_cards())
        
        # 3. Status Sistem
        left_layout.addWidget(self.ui_components.create_status_system())
        
        # 4. Grafik Tren (beri space lebih besar)
        graph_panel = self.graph_components.create_graph_panel()
        left_layout.addWidget(graph_panel, 1)  # Stretch factor 1 untuk expand
        
        # Kurangi stretch di bawah agar grafik dapat space lebih
        left_layout.addStretch(0)
        
        # Set scroll area widget
        left_scroll_area.setWidget(left_column)
        return left_scroll_area
    
    # === SIMULATION AND SYNC METHODS ===
    
    def force_sync_current_profile(self):
        """Force sync with currently selected profile"""
        try:
            if hasattr(self, 'profil_combo'):
                current_profile_name = self.profil_combo.currentText()
                if current_profile_name and current_profile_name != "Custom (Manual)":
                    print(f">>> Force syncing with current profile: {current_profile_name}")
                    self.event_handlers.on_profile_changed(current_profile_name)
        except Exception as e:
            print(f"⚠ Error in force sync: {e}")
    
    def update_display_from_real_data(self):
        """Update display dengan data real dari sensor MQTT"""
        # Ambil data real dari data manager
        current_readings = self.controller.data_manager.get_current_readings()
        target_values = self.controller.data_manager.get_target_values()
        
        # Update vital cards dengan data real
        if hasattr(self, 'temp_current_label') and hasattr(self, 'humidity_current_label'):
            self.temp_current_label.setText(f"{current_readings['temperature']:.1f}°C")
            self.humidity_current_label.setText(f"{current_readings['humidity']:.1f}%")
        
        # Update target displays
        if hasattr(self, 'temp_target_label') and hasattr(self, 'humidity_target_label'):
            self.temp_target_label.setText(f"Target: {target_values['temperature']:.1f}°C")
            self.humidity_target_label.setText(f"Target: {target_values['humidity']:.1f}%")
        
        # Update graph dengan data yang sama
        if len(self.graph_data["temperature"]) == 0:
            # Jika graph kosong, tambahkan data point pertama
            self.update_graph_with_real_data(current_readings['temperature'], current_readings['humidity'])
        
        print(f"📊 Display updated from real data: T={current_readings['temperature']:.1f}°C, H={current_readings['humidity']:.1f}%")
        print(f"🎯 Connection status: {self.controller.data_manager.is_connected}")
        
        # Force koneksi MQTT jika belum terhubung
        if not self.controller.data_manager.is_connected:
            print("🔄 Attempting MQTT connection to topic/penetasan/status...")
            self.controller.data_manager.connect()
    
    def refresh_display_data(self):
        """Refresh display data dari MQTT real-time - TANPA simulasi"""
        # Check status koneksi MQTT
        self.check_mqtt_connection_status()
        
        # Update display dengan data terbaru dari data manager (yang diterima via MQTT)
        current_readings = self.controller.data_manager.get_current_readings()
        
        if hasattr(self, 'temp_current_label') and hasattr(self, 'humidity_current_label'):
            # Update vital cards dengan data real dari ESP32
            self.temp_current_label.setText(f"{current_readings['temperature']:.1f}°C")
            self.humidity_current_label.setText(f"{current_readings['humidity']:.1f}%")
            
            # Log data yang diterima untuk debugging
            if current_readings['temperature'] != 0.0 or current_readings['humidity'] != 0.0:
                print(f"📊 Data REAL dari ESP32: T={current_readings['temperature']:.1f}°C, H={current_readings['humidity']:.1f}%")
                # Update graph dengan data real
                self.update_graph_with_real_data(current_readings['temperature'], current_readings['humidity'])
            else:
                print("⏳ Menunggu data REAL dari ESP32 pada topic: topic/penetasan/status")
                print(f"🔄 Display refreshed: T={current_readings['temperature']:.1f}°C, H={current_readings['humidity']:.1f}%")
    
    def check_mqtt_connection_status(self):
        """Check dan log status koneksi MQTT untuk debugging"""
        if hasattr(self.controller.data_manager, 'is_connected'):
            if self.controller.data_manager.is_connected:
                print(f"✅ MQTT terhubung - Listening pada topic: topic/penetasan/status")
            else:
                print(f"❌ MQTT tidak terhubung - Mencoba koneksi ulang...")
                self.controller.data_manager.connect()
    
    def sync_initial_card_targets(self):
        """Sync card vital targets with current profile on startup"""
        try:
            # Get current target values after profile application
            target_data = self.controller.data_manager.get_target_values()
            
            # Update card vital targets
            if hasattr(self, 'temp_target_label') and hasattr(self, 'humidity_target_label'):
                self.update_vital_card_targets(
                    target_data["temperature"], 
                    target_data["humidity"]
                )
                print(f"✅ Card vital targets synced: {target_data['temperature']}°C, {target_data['humidity']}%")
        except Exception as e:
            print(f"⚠ Failed to sync initial card targets: {e}")
    
    # === UPDATE METHODS ===
    
    def update_vital_card_targets(self, temperature, humidity):
        """Update target values in vital cards immediately"""
        self.temp_target_label.setText(f"Target: {temperature}°C")
        self.humidity_target_label.setText(f"Target: {humidity}%")
        
        # Update graph menggunakan data real dari sensor
        current_readings = self.controller.data_manager.get_current_readings()
        self.update_graph_with_real_data(current_readings['temperature'], current_readings['humidity'])
        
        # Optional: Add visual feedback for updates
        self.add_target_update_animation()
    
    def add_target_update_animation(self):
        """Add subtle visual feedback when targets are updated"""
        # Temporarily change the target box style to indicate update
        original_style = self.temp_target_label.styleSheet()
        
        # Add brief highlight effect
        highlight_style = """
            QLabel {
                background-color: rgba(79, 70, 229, 0.1);
                border: 1px solid #4f46e5;
                border-radius: 6px;
                padding: 4px 8px;
            }
        """
        
        self.temp_target_label.setStyleSheet(highlight_style)
        self.humidity_target_label.setStyleSheet(highlight_style)
        
        # Reset after short delay
        QTimer.singleShot(500, lambda: (
            self.temp_target_label.setStyleSheet(original_style),
            self.humidity_target_label.setStyleSheet(original_style)
        ))
    
    def update_graph_with_real_data(self, temperature, humidity):
        """Update graph dengan data real dari sensor MQTT"""
        current_time = time.time()
        
        # Tambah data point baru dengan nilai real dari sensor
        self.graph_data["timestamps"].append(current_time)
        self.graph_data["temperature"].append(temperature)
        self.graph_data["humidity"].append(humidity)
        
        # Simpan hanya N data terakhir untuk mencegah pertumbuhan memori
        max_points = self.graph_data["max_points"]
        if len(self.graph_data["timestamps"]) > max_points:
            self.graph_data["timestamps"] = self.graph_data["timestamps"][-max_points:]
            self.graph_data["temperature"] = self.graph_data["temperature"][-max_points:]
            self.graph_data["humidity"] = self.graph_data["humidity"][-max_points:]
        
        # Update plot graph segera
        self.graph_components.update_graph_plot()
        
        print(f"📊 Graph updated dengan data real: {temperature:.1f}°C, {humidity:.1f}% pada {time.strftime('%H:%M:%S')}")
    
    # === DYNAMIC UPDATE SLOTS ===
    
    @pyqtSlot(dict)
    def update_sensor_display(self, data):
        """Update sensor display dengan data real dari MQTT sensor"""
        current = data["current"]
        target = data["target"]
        
        # Update nilai current di vital cards dengan data real
        self.temp_current_label.setText(f"{current['temperature']:.1f}°C")
        self.humidity_current_label.setText(f"{current['humidity']:.1f}%")
        
        # Update targets
        self.temp_target_label.setText(f"Target: {target['temperature']:.1f}°C")
        self.humidity_target_label.setText(f"Target: {target['humidity']:.1f}%")
        
        # Update graph dengan data real dari sensor
        self.update_graph_with_real_data(current['temperature'], current['humidity'])
        
        print(f"📡 Sensor data received - T: {current['temperature']:.1f}°C, H: {current['humidity']:.1f}%")
    
    @pyqtSlot(dict)
    def update_graph_data(self, data):
        """Update graph dengan data real-time dari sensor MQTT"""
        current = data["current"]
        current_time = time.time()
        
        # Tambahkan data point baru dari sensor real
        self.graph_data["timestamps"].append(current_time)
        self.graph_data["temperature"].append(current['temperature'])
        self.graph_data["humidity"].append(current['humidity'])
        
        # Simpan hanya N data terakhir untuk mencegah pertumbuhan memori
        max_points = self.graph_data["max_points"]
        if len(self.graph_data["timestamps"]) > max_points:
            self.graph_data["timestamps"] = self.graph_data["timestamps"][-max_points:]
            self.graph_data["temperature"] = self.graph_data["temperature"][-max_points:]
            self.graph_data["humidity"] = self.graph_data["humidity"][-max_points:]
        
        # Update plot graph dengan data real
        self.graph_components.update_graph_plot()
        
        print(f"📊 Graph diperbarui dengan data sensor real: T={current['temperature']:.1f}°C, H={current['humidity']:.1f}%")

    @pyqtSlot(dict)
    def update_device_status_display(self, status):
        """Update device status display with real-time data"""
        # Update pemanas (heater)
        if "pemanas" in status:
            self.pemanas_status_label.setText(status["pemanas"]["status"])
            if status["pemanas"]["active"]:
                self.pemanas_status_label.setObjectName("statusAktif")
            else:
                self.pemanas_status_label.setObjectName("statusNonAktif")
        
        # Update humidifier  
        if "humidifier" in status:
            self.humidifier_status_label.setText(status["humidifier"]["status"])
            if status["humidifier"]["active"]:
                self.humidifier_status_label.setObjectName("statusAktif")
            else:
                self.humidifier_status_label.setObjectName("statusNonAktif")
        
        # Update motor with countdown display
        if "motor" in status:
            motor_status = status["motor"]["status"]
            rotation_time = status["motor"].get("rotation_time", 0)
            
            # Add rotation countdown to status text when rotating
            if motor_status == "Berputar" and rotation_time > 0:
                display_text = f"{motor_status} ({rotation_time}s)"
            else:
                display_text = motor_status
                
            self.motor_status_label.setText(display_text)
            
            # Set object names for motor states
            if motor_status == "Berputar":
                self.motor_status_label.setObjectName("statusMotorBerputar")
            elif motor_status == "Error":
                self.motor_status_label.setObjectName("statusMotorError")
            else:  # "Idle"
                self.motor_status_label.setObjectName("statusMotorIdle")
        
        # Update timer with real countdown (3:00:00 format)
        if "timer" in status:
            countdown = status["timer"]["countdown"]
            self.timer_status_label.setText(countdown)
        
        # Reapply stylesheet to update colors
        self.set_stylesheet()

    @pyqtSlot(dict)
    def update_connection_display(self, connection):
        """Update connection status display"""
        if connection["connected"]:
            self.status_connect_btn.setText(" Terhubung")
            self.status_connect_btn.setObjectName("statusConnected")
            # Gunakan icon wifi.svg untuk status terhubung
            self.status_connect_btn.setIcon(QIcon(self.ui_components.load_svg_icon("wifi.svg", QSize(20, 20))))
        else:
            self.status_connect_btn.setText(" Tidak Terhubung")
            self.status_connect_btn.setObjectName("statusNotConnected")
            # Gunakan icon wifi-notconnect.svg untuk status tidak terhubung
            self.status_connect_btn.setIcon(QIcon(self.ui_components.load_svg_icon("wifi-notconnect.svg", QSize(20, 20))))
        
        self.status_day_btn.setText(f" {connection['day_text']}")
        
        # Reapply stylesheet
        self.set_stylesheet()
    
    # === STYLESHEET ===
    
    def set_stylesheet(self):
        """Terapkan stylesheet dari file eksternal"""
        stylesheet = self.load_stylesheet("styles.qss")
        
        if not stylesheet:
            print("⚠ Stylesheet tidak ditemukan, menggunakan default")
            
        self.setStyleSheet(stylesheet)

    def load_stylesheet(self, file_path="styles.qss"):
        """Memuat stylesheet dari file QSS eksternal"""
        try:
            possible_paths = [
                file_path,
                f"asset/style/{file_path}",
                f"asset/{file_path}",
                f"style/{file_path}"
            ]
            
            for style_file in possible_paths:
                if os.path.exists(style_file):
                    with open(style_file, 'r', encoding='utf-8') as file:
                        stylesheet = file.read()
                    return stylesheet
            
            raise FileNotFoundError("Stylesheet tidak ditemukan")
            
        except Exception as e:
            print(f"⚠ Error saat memuat stylesheet: {e}")
            return ""


if __name__ == "__main__":
    pg.setConfigOptions(antialias=True)
    
    app = QApplication(sys.argv)
    
    default_font = QFont("Manrope", 10)
    if default_font.exactMatch():
        print("✅ Font aplikasi: Manrope")
    else:
        print("⚠ Font aplikasi: Arial fallback")
        default_font = QFont("Arial", 10)
    app.setFont(default_font)
    
    window = KartelDashboard()
    window.show()
    sys.exit(app.exec())