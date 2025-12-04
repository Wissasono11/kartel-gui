import sys
import os
import time
import signal
import pyqtgraph as pg
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QScrollArea
)
from PyQt6.QtGui import QFont, QFontDatabase, QIcon
from PyQt6.QtCore import Qt, pyqtSlot, QTimer, QSize

# Import modul kustom kami
from kartel_controller import KartelController
from ui_components import DashboardUIComponents
from graph_components import DashboardGraphComponents
from event_handlers import DashboardEventHandlers
from config_panel import DashboardConfigPanel


class KartelDashboard(QWidget):
    """Kelas dashboard utama - desain modular untuk maintainability yang lebih baik"""
    
    def __init__(self):
        super().__init__()
        
        self.graph_data = {
            "timestamps": [],
            "temperature": [],
            "humidity": [],
            "max_points": 24 
        }
        
        self.input_fields = {
            'temperature': None,
            'humidity': None
        }
        
        # Inisiasi komponen UI modular
        self.ui_components = DashboardUIComponents(self)
        self.graph_components = DashboardGraphComponents(self)
        self.event_handlers = DashboardEventHandlers(self)
        self.config_panel = DashboardConfigPanel(self)
        
        # Controller untuk data real-time
        self.controller = KartelController()
        self.setup_controller_connections()
        
        # Antarmuka Pengguna
        self.load_custom_fonts()
        self.init_ui()
        
        # Untuk sinkronisasi awal setelah profil diterapkan
        self.sync_initial_card_targets()
        QTimer.singleShot(500, self.force_sync_current_profile)
        
        self.update_display_from_real_data()
        
        # Siapkan timer untuk refresh display periodik
        self.data_refresh_timer = QTimer()
        self.data_refresh_timer.timeout.connect(self.refresh_display_data)
        self.data_refresh_timer.start(2000)  # Refresh display setiap 2 detik
        
        print("📡 KARTEL Dashboard siap - Silakan connect manual untuk menerima data sensor")
        
        # Setup signal handler untuk Ctrl+C
        self.setup_signal_handlers()
    
    def setup_signal_handlers(self):
        """Setup signal handlers untuk menangani Ctrl+C"""
        signal.signal(signal.SIGINT, self.signal_handler)
        
        # Timer untuk memungkinkan signal processing di PyQt
        self.signal_timer = QTimer()
        self.signal_timer.timeout.connect(lambda: None)  # Dummy untuk processing signals
        self.signal_timer.start(100)  # Check signals setiap 100ms
    
    def signal_handler(self, signum, frame):
        """Handler untuk SIGINT (Ctrl+C)"""
        print("\n🛑 Menerima sinyal shutdown (Ctrl+C)...")
        self.shutdown_application()
    
    def shutdown_application(self):
        """Shutdown aplikasi dengan cleanup yang proper"""
        try:
            print("🔄 Melakukan cleanup...")
            
            # Stop semua timer
            if hasattr(self, 'data_refresh_timer'):
                self.data_refresh_timer.stop()
            if hasattr(self, 'signal_timer'):
                self.signal_timer.stop()
            
            # Stop timer di controller
            if hasattr(self.controller, 'status_timer'):
                self.controller.status_timer.stop()
            if hasattr(self.controller, 'device_status_timer'):
                self.controller.device_status_timer.stop()
                
            # Disconnect MQTT connection dengan aman
            if hasattr(self.controller, 'disconnect'):
                print("📡 Memutus koneksi MQTT...")
                self.controller.disconnect()
            
            # Tutup aplikasi
            print("✅ Cleanup selesai. Menutup aplikasi...")
            QApplication.instance().quit()
            
        except Exception as e:
            print(f"⚠ Error saat cleanup: {e}")
            QApplication.instance().quit()
    
    def closeEvent(self, event):
        """Override closeEvent untuk cleanup saat window ditutup"""
        self.shutdown_application()
        event.accept()

    def setup_controller_connections(self):
        """Hubungkan sinyal controller ke metode update GUI"""
        self.controller.data_updated.connect(self.update_sensor_display)
        self.controller.data_updated.connect(self.update_graph_data)
        self.controller.status_updated.connect(self.update_device_status_display)
        self.controller.connection_updated.connect(self.update_connection_display)
    
    def load_custom_fonts(self):
        """Muat font Manrope dari berbagai sumber"""
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
                    font_loaded = True
                    break
        
        return font_loaded
    
    def init_ui(self):
        """Inisialisasi antarmuka pengguna"""
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
        """Buat kolom monitoring kiri"""
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
        left_layout.addWidget(graph_panel, 1)  # Faktor stretch 1 untuk expand
        
        # Kurangi stretch di bawah agar grafik dapat space lebih
        left_layout.addStretch(0)
        
        # Atur widget scroll area
        left_scroll_area.setWidget(left_column)
        return left_scroll_area
    
    # === METODE SIMULASI DAN SINKRONISASI ===
    
    def force_sync_current_profile(self):
        """Paksa sinkronisasi dengan profil yang sedang dipilih"""
        try:
            if hasattr(self, 'profil_combo'):
                current_profile_name = self.profil_combo.currentText()
                if current_profile_name and current_profile_name != "Custom (Manual)":
                    # Paksa sinkronisasi secara diam-diam
                    self.event_handlers.on_profile_changed(current_profile_name)
        except Exception as e:
            print(f"⚠ Error in force sync: {e}")
    
    def update_display_from_real_data(self):
        """Perbarui display dengan data real dari sensor MQTT"""
        # Ambil data real dari data manager
        current_readings = self.controller.data_manager.get_current_readings()
        target_values = self.controller.data_manager.get_target_values()
        
        # Perbarui vital cards dengan data real
        if hasattr(self, 'temp_current_label') and hasattr(self, 'humidity_current_label'):
            self.temp_current_label.setText(f"{current_readings['temperature']:.1f}°C")
            self.humidity_current_label.setText(f"{current_readings['humidity']:.1f}%")
        
        # Perbarui tampilan target
        if hasattr(self, 'temp_target_label'):
            self.temp_target_label.setText(f"Target: {target_values['temperature']:.1f}°C")
        # Tidak ada label target kelembaban untuk diperbarui
        
        # Update graph dengan data yang sama
        if len(self.graph_data["temperature"]) == 0:
            # Jika grafik kosong, tambahkan data point pertama
            self.update_graph_with_real_data(current_readings['temperature'], current_readings['humidity'])
    
    def refresh_display_data(self):
        """Refresh data tampilan dari MQTT real-time - TANPA simulasi"""
        # Periksa status koneksi MQTT
        self.check_mqtt_connection_status()
        
        # Perbarui display dengan data terbaru dari data manager (yang diterima via MQTT)
        current_readings = self.controller.data_manager.get_current_readings()
        
        if hasattr(self, 'temp_current_label') and hasattr(self, 'humidity_current_label'):
            # Perbarui vital cards dengan data real dari ESP32
            self.temp_current_label.setText(f"{current_readings['temperature']:.1f}°C")
            self.humidity_current_label.setText(f"{current_readings['humidity']:.1f}%")
            
            # Log hanya saat ada data real dari ESP32
            if current_readings['temperature'] != 0.0 or current_readings['humidity'] != 0.0:
                # Perbarui grafik dengan data real
                self.update_graph_with_real_data(current_readings['temperature'], current_readings['humidity'])
            # Lewati logging untuk data kosong agar tidak spam terminal
    
    def check_mqtt_connection_status(self):
        """Periksa status koneksi MQTT (minimal logging)"""
        if hasattr(self.controller.data_manager, 'is_connected'):
            if not self.controller.data_manager.is_connected:
                # Mencegah auto reconnect jika user memutus koneksi secara manual
                if hasattr(self.controller.data_manager, 'user_disconnected') and self.controller.data_manager.user_disconnected:
                    pass  # Lewati logging untuk user disconnectct
                # Mencegah auto connect jika user belum pernah connect manual
                elif hasattr(self.controller.data_manager, 'manual_connect_required') and self.controller.data_manager.manual_connect_required:
                    pass  # Lewati logging untuk waiting manual connect
                else:
                    self.controller.data_manager.connect()
    
    def sync_initial_card_targets(self):
        """Sinkronkan target card vital dengan profil saat ini saat startup"""
        try:
            # Dapatkan nilai target saat ini setelah penerapan profil
            target_data = self.controller.data_manager.get_target_values()
            
            # Perbarui target card vital
            if hasattr(self, 'temp_target_label') and hasattr(self, 'humidity_target_label'):
                self.update_vital_card_targets(
                    target_data["temperature"], 
                    target_data["humidity"]
                )
                # Target disinkronkan secara diam-diam
        except Exception as e:
            print(f"⚠ Failed to sync initial card targets: {e}")
    
    # === METODE UPDATE ===
    
    def update_vital_card_targets(self, temperature, humidity):
        """Perbarui nilai target di card vital (hanya suhu yang memiliki tampilan target)"""
        self.temp_target_label.setText(f"Target: {temperature}°C")
        # Tidak ada label target kelembaban untuk diperbarui karena telah dihapustelah dihapus
        
        current_readings = self.controller.data_manager.get_current_readings()
        self.update_graph_with_real_data(current_readings['temperature'], current_readings['humidity'])
        
        self.add_target_update_animation()
    
    def add_target_update_animation(self):
        """Tambahkan feedback visual halus ketika target diperbarui"""
        # Temporarily change the target box style to indicate update
        original_style = self.temp_target_label.styleSheet()
        
        # Tambahkan efek highlight singkat
        highlight_style = """
            QLabel {
                background-color: rgba(79, 70, 229, 0.1);
                border: 1px solid #4f46e5;
                border-radius: 6px;
                padding: 4px 8px;
            }
        """
        
        self.temp_target_label.setStyleSheet(highlight_style)
        # Tidak ada label target kelembaban karena telah dihapusihapus
        
        # Reset setelah delay singkat
        QTimer.singleShot(500, lambda: (
            self.temp_target_label.setStyleSheet(original_style)
        ))
    
    def update_graph_with_real_data(self, temperature, humidity):
        """Perbarui grafik dengan data real dari sensor MQTT"""
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
        
        # Perbarui plot grafik segera
        self.graph_components.update_graph_plot()
        
        # Grafik diperbarui secara diam-diamara diam-diam
    
    # === SLOT UPDATE DINAMIS ===
    
    @pyqtSlot(dict)
    def update_sensor_display(self, data):
        """Perbarui tampilan sensor dengan data real dari sensor MQTT"""
        current = data["current"]
        target = data["target"]
        
        # Perbarui nilai current di vital cards dengan data real
        self.temp_current_label.setText(f"{current['temperature']:.1f}°C")
        self.humidity_current_label.setText(f"{current['humidity']:.1f}%")
        
        # Perbarui target (hanya suhu yang memiliki tampilan target)
        self.temp_target_label.setText(f"Target: {target['temperature']:.1f}°C")
        # Tidak ada label target kelembaban untuk diperbaruiuntuk diperbarui
        
        # Perbarui grafik dengan data real dari sensor
        self.update_graph_with_real_data(current['temperature'], current['humidity'])
        
    @pyqtSlot(dict)
    def update_graph_data(self, data):
        """Perbarui grafik dengan data real-time dari sensor MQTT"""
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
        
        # Perbarui plot grafik dengan data real
        self.graph_components.update_graph_plot()
        
        # Grafik diperbarui dengan data sensor real

    @pyqtSlot(dict)
    def update_device_status_display(self, status):
        """Perbarui tampilan status perangkat dengan data real-time"""
        # Perbarui status daya berdasarkan data MQTT power
        if "power" in status:
            power_value = status["power"]["value"]
            power_status = status["power"]["status"]
            self.power_status_label.setText(f"{power_status} ({power_value}%)")
            if status["power"]["active"]:
                self.power_status_label.setObjectName("statusAktif")
            else:
                self.power_status_label.setObjectName("statusNonAktif")
            # Segarkan style
            self.power_status_label.style().unpolish(self.power_status_label)
            self.power_status_label.style().polish(self.power_status_label)
        
        if "motor" in status:
            motor_status = status["motor"]["status"]
            # Tidak menampilkan detik countdown pada card motor
            display_text = motor_status
                
            self.motor_status_label.setText(display_text)
            
            # Atur nama objek untuk status motor
            if motor_status == "Berputar":
                self.motor_status_label.setObjectName("statusMotorBerputar")
            elif motor_status == "Error":
                self.motor_status_label.setObjectName("statusMotorError")
            else:  # "Idle"
                self.motor_status_label.setObjectName("statusMotorIdle")
        
        # Perbarui timer dengan countdown real (format 3:00:00)
        if "timer" in status:
            countdown = status["timer"]["countdown"]
            self.timer_status_label.setText(countdown)
        
        # Terapkan ulang stylesheet untuk memperbarui warna
        self.set_stylesheet()

    @pyqtSlot(dict)
    def update_connection_display(self, connection):
        """Perbarui tampilan status koneksi"""
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
        
        # Terapkan ulang stylesheet
        self.set_stylesheet()
    
    # === STYLESHEET ===
    
    def set_stylesheet(self):
        """Terapkan stylesheet dari file eksternal"""
        stylesheet = self.load_stylesheet("styles.qss")
        
        if not stylesheet:
            print("⚠ Stylesheet tidak ditemukan, menggunakan default")
            
        self.setStyleSheet(stylesheet)

    def load_stylesheet(self, file_path="styles.qss"):
        """Muat stylesheet dari file QSS eksternal"""
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


def setup_signal_handling():
    """Setup global signal handling untuk aplikasi"""
    # Enable CTRL+C handling di Windows
    if sys.platform == "win32":
        import os
        os.system("")
    
    # Pastikan Python dapat menerima signals
    signal.signal(signal.SIGINT, signal.SIG_DFL)

if __name__ == "__main__":
    pg.setConfigOptions(antialias=True)
    
    # Setup signal handling sebelum membuat aplikasi
    setup_signal_handling()
    
    app = QApplication(sys.argv)
    
    # Enable signal handling di PyQt
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    
    default_font = QFont("Manrope", 10)
    if default_font.exactMatch():
        print("✅ Font aplikasi: Manrope")
    else:
        print("⚠ Font aplikasi: Arial fallback")
        default_font = QFont("Arial", 10)
    app.setFont(default_font)
    
    print("💡 Tip: Gunakan Ctrl+C untuk shutdown aplikasi dengan aman")
    
    window = KartelDashboard()
    window.show()
    
    try:
        sys.exit(app.exec())
    except KeyboardInterrupt:
        print("\n🛑 Keyboard interrupt detected, shutting down...")
        if hasattr(window, 'shutdown_application'):
            window.shutdown_application()
        sys.exit(0)