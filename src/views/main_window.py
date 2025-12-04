import sys
import os
import time
import signal
import pyqtgraph as pg
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QApplication
)
from PyQt6.QtGui import QFont, QFontDatabase, QIcon
from PyQt6.QtCore import Qt, pyqtSlot, QTimer, QSize

# --- IMPORT MODULES DARI STRUKTUR BARU ---
from src.controllers.main_controller import MainController
from src.controllers.event_handlers import DashboardEventHandlers
from src.views.components.widgets import DashboardWidgets
from src.views.components.graphs import DashboardGraphs
from src.views.components.panels import DashboardPanels
from src.config.settings import ASSET_DIR

class KartelMainWindow(QWidget):
    """
    Jendela Utama Aplikasi (Dashboard).
    Menyatukan semua komponen UI dan menghubungkannya dengan Controller.
    """
    
    def __init__(self):
        super().__init__()
        
        # State Data untuk Grafik
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
        
        # 1. Inisialisasi Controller (Logic)
        self.controller = MainController()
        
        # 2. Inisialisasi Event Handlers (Interaction)
        self.event_handlers = DashboardEventHandlers(self)
        
        # 3. Inisialisasi Komponen UI (View Helpers)
        self.widgets_helper = DashboardWidgets(self)
        self.graphs_helper = DashboardGraphs(self)
        self.panels_helper = DashboardPanels(self)
        
        # 4. Setup Koneksi Controller -> UI
        self.setup_controller_connections()
        
        # 5. Bangun Antarmuka
        self.load_custom_fonts()
        self.init_ui()
        
        # 6. Startup Sequence
        QTimer.singleShot(500, self.force_sync_current_profile)
        
        # Timer Refresh Data (Polling UI)
        self.data_refresh_timer = QTimer()
        self.data_refresh_timer.timeout.connect(self.refresh_display_data)
        self.data_refresh_timer.start(2000) 
        
        print("📡 Dashboard initialized and ready.")
        
        # Setup Signal Handler (Ctrl+C)
        self.setup_signal_handlers()
    
    def init_ui(self):
        """Inisialisasi antarmuka pengguna"""
        self.setWindowTitle("KARTEL Dashboard")
        self.setGeometry(100, 100, 1400, 900)
        self.setMinimumSize(1000, 600)
        
        # Icon Window
        icon_path = os.path.join(ASSET_DIR, 'img', 'kartel-logo.png')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        # Layout Utama
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(24)

        # === KOLOM KIRI (Monitoring) ===
        left_column = self.create_left_column()
        
        # === KOLOM KANAN (Konfigurasi) ===
        right_column = self.panels_helper.create_config_panel()
        
        main_layout.addWidget(left_column, 7)
        main_layout.addWidget(right_column, 3)

        # Stylesheet
        self.set_stylesheet()
    
    def create_left_column(self):
        """Buat kolom monitoring kiri"""
        left_scroll_area = QScrollArea()
        left_scroll_area.setWidgetResizable(True)
        left_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        left_scroll_area.setObjectName("leftScrollArea")
        
        left_column = QWidget()
        left_layout = QVBoxLayout(left_column)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(20)

        # Gunakan Helper Widgets
        left_layout.addWidget(self.widgets_helper.create_header())
        left_layout.addWidget(self.widgets_helper.create_vital_cards())
        left_layout.addWidget(self.widgets_helper.create_status_system())
        
        # Gunakan Helper Graphs
        graph_panel = self.graphs_helper.create_graph_panel()
        left_layout.addWidget(graph_panel, 1)
        
        left_layout.addStretch(0)
        
        left_scroll_area.setWidget(left_column)
        return left_scroll_area

    def setup_controller_connections(self):
        """Hubungkan sinyal controller ke metode update GUI"""
        self.controller.data_updated.connect(self.update_sensor_display)
        self.controller.data_updated.connect(self.update_graph_data)
        self.controller.status_updated.connect(self.update_device_status_display)
        self.controller.connection_updated.connect(self.update_connection_display)

    # === UPDATE SLOTS (Dipanggil oleh Controller) ===
    
    @pyqtSlot(dict)
    def update_sensor_display(self, data):
        """Update teks sensor"""
        current = data["current"]
        target = data["target"]
        
        if hasattr(self, 'temp_current_label'):
            self.temp_current_label.setText(f"{current['temperature']:.1f}°C")
            self.humidity_current_label.setText(f"{current['humidity']:.1f}%")
            self.temp_target_label.setText(f"Target: {target['temperature']:.1f}°C")
    
    @pyqtSlot(dict)
    def update_graph_data(self, data):
        """Update data grafik"""
        # Logic update data grafik dipindah ke Graph Component agar lebih rapi?
        # Untuk sekarang biarkan di sini agar logic flow tidak berubah drastis
        current = data["current"]
        current_time = time.time()
        
        self.graph_data["timestamps"].append(current_time)
        self.graph_data["temperature"].append(current['temperature'])
        self.graph_data["humidity"].append(current['humidity'])
        
        # Limit data points
        max_points = self.graph_data["max_points"]
        if len(self.graph_data["timestamps"]) > max_points:
            self.graph_data["timestamps"] = self.graph_data["timestamps"][-max_points:]
            self.graph_data["temperature"] = self.graph_data["temperature"][-max_points:]
            self.graph_data["humidity"] = self.graph_data["humidity"][-max_points:]
            
        # Panggil method update di graph component
        self.graphs_helper.update_graph_plot()

    @pyqtSlot(dict)
    def update_device_status_display(self, status):
        """Update status visual (Power, Motor, Timer)"""
        # Power
        if "power" in status and hasattr(self, 'power_status_label'):
            power_val = status["power"]["value"]
            self.power_status_label.setText(f"{status['power']['status']} ({power_val}%)")
            style_obj = "statusAktif" if status["power"]["active"] else "statusNonAktif"
            self.power_status_label.setObjectName(style_obj)
            self._refresh_style(self.power_status_label)

        # Motor
        if "motor" in status and hasattr(self, 'motor_status_label'):
            motor_st = status["motor"]["status"]
            self.motor_status_label.setText(motor_st)
            
            style_obj = "statusMotorIdle"
            if motor_st == "Berputar": style_obj = "statusMotorBerputar"
            elif motor_st == "Error": style_obj = "statusMotorError"
            
            self.motor_status_label.setObjectName(style_obj)
            self._refresh_style(self.motor_status_label)

        # Timer
        if "timer" in status and hasattr(self, 'timer_status_label'):
            self.timer_status_label.setText(status["timer"]["countdown"])
            
    @pyqtSlot(dict)
    def update_connection_display(self, connection):
        """Update tombol status koneksi"""
        if not hasattr(self, 'status_connect_btn'): return
        
        if connection["connected"]:
            self.status_connect_btn.setText(" Terhubung")
            self.status_connect_btn.setObjectName("statusConnected")
            self.status_connect_btn.setIcon(QIcon(self.widgets_helper.load_svg_icon("wifi.svg", QSize(20, 20))))
        else:
            self.status_connect_btn.setText(" Tidak Terhubung")
            self.status_connect_btn.setObjectName("statusNotConnected")
            self.status_connect_btn.setIcon(QIcon(self.widgets_helper.load_svg_icon("wifi-notconnect.svg", QSize(20, 20))))
            
        self.status_day_btn.setText(f" {connection['day_text']}")
        self._refresh_style(self.status_connect_btn)

    def _refresh_style(self, widget):
        """Helper untuk force refresh stylesheet pada widget tertentu"""
        widget.style().unpolish(widget)
        widget.style().polish(widget)

    # === STARTUP & CLEANUP ===
    
    def refresh_display_data(self):
        """Polling method untuk update data jika diperlukan"""
        # Cek koneksi via controller
        # self.controller.mqtt_service.connect() # (Opsional, sudah ada auto connect di service)
        pass

    def force_sync_current_profile(self):
        if hasattr(self, 'profil_combo'):
            current_profile = self.profil_combo.currentText()
            if current_profile and current_profile != "Custom (Manual)":
                self.event_handlers.on_profile_changed(current_profile)

    def setup_signal_handlers(self):
        signal.signal(signal.SIGINT, self.signal_handler)
        self.signal_timer = QTimer()
        self.signal_timer.timeout.connect(lambda: None)
        self.signal_timer.start(100)
    
    def signal_handler(self, signum, frame):
        print("\n🛑 Menerima sinyal shutdown...")
        self.shutdown_application()

    def shutdown_application(self):
        print("🔄 Melakukan cleanup...")
        self.controller.cleanup()
        QApplication.instance().quit()
    
    def closeEvent(self, event):
        self.shutdown_application()
        event.accept()

    def set_stylesheet(self):
        path = os.path.join(ASSET_DIR, 'style', 'styles.qss')
        if os.path.exists(path):
            with open(path, 'r') as f:
                self.setStyleSheet(f.read())
    
    def load_custom_fonts(self):
        # Implementasi load font sederhana
        font_path = os.path.join(ASSET_DIR, 'fonts', 'Manrope-Regular.ttf')
        if os.path.exists(font_path):
            QFontDatabase.addApplicationFont(font_path)