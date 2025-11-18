#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KARTEL Dashboard - Functional Version
Interactive dashboard with dummy data and working controls

Author: KARTEL Team
Created: November 18, 2025
"""

import sys
import os
import pyqtgraph as pg
import qtawesome as qta
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, 
    QLineEdit, QPushButton, QComboBox, QScrollArea, QSpacerItem, 
    QSizePolicy, QGridLayout, QMessageBox
)
from PyQt6.QtGui import QFont, QPixmap, QIcon, QFontDatabase, QColor, QPainter
from PyQt6.QtCore import Qt, QSize, pyqtSlot

# Import our custom modules
from kartel_controller import KartelController

class KartelDashboardFunctional(QWidget):
    def __init__(self):
        super().__init__()
        
        # Initialize graph data storage first
        self.graph_data = {
            "timestamps": [],
            "temperature": [],
            "humidity": [],
            "max_points": 24  # Keep last 24 data points
        }
        
        # Initialize controller
        self.controller = KartelController()
        self.setup_controller_connections()
        
        # Initialize UI
        self.load_custom_fonts()
        self.init_ui()
        
        # Store widget references for updates
        self.ui_elements = {}
        self.setup_ui_references()
    
    def setup_controller_connections(self):
        """Connect controller signals to GUI update methods"""
        self.controller.data_updated.connect(self.update_sensor_display)
        self.controller.data_updated.connect(self.update_graph_data)  # Add graph update
        self.controller.status_updated.connect(self.update_device_status_display)
        self.controller.connection_updated.connect(self.update_connection_display)
    
    def load_svg_icon(self, svg_filename, size=QSize(24, 24)):
        """Load SVG icon dengan warna asli tanpa customisasi"""
        svg_path = f"asset/svg/{svg_filename}"
        if os.path.exists(svg_path):
            from PyQt6.QtSvg import QSvgRenderer
            renderer = QSvgRenderer(svg_path)
            pixmap = QPixmap(size)
            pixmap.fill(Qt.GlobalColor.transparent)
            
            painter = QPainter(pixmap)
            renderer.render(painter)
            painter.end()
            
            return pixmap
        else:
            # Fallback ke qtawesome jika SVG tidak ditemukan
            print(f"⚠ SVG icon tidak ditemukan: {svg_path}, menggunakan fallback")
            return qta.icon("fa5s.question", color="#666666").pixmap(size)
    
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
                    families = QFontDatabase.applicationFontFamilies(font_id)
                    print(f"✅ Font Manrope berhasil dimuat dari: {font_path}")
                    font_loaded = True
                    break
        
        if not font_loaded:
            print("⚠ Font Manrope tidak ditemukan, menggunakan fallback")
        
        return font_loaded
    
    def init_ui(self):
        # Pengaturan Jendela Utama
        self.setWindowTitle("KARTEL Dashboard - Functional")
        self.setGeometry(100, 100, 1400, 900)
        
        # Layout Utama
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(24)

        # === KOLOM KIRI ===
        left_column = QWidget()
        left_layout = QVBoxLayout(left_column)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(20)

        # 1. Header
        left_layout.addWidget(self.create_header())
        
        # 2. Card Vital (Suhu & Kelembaban)
        left_layout.addWidget(self.create_vital_cards())
        
        # 3. Status Sistem
        left_layout.addWidget(self.create_status_system())
        
        # 4. Grafik Tren (beri space lebih besar)
        graph_panel = self.create_graph_panel()
        left_layout.addWidget(graph_panel, 1)  # Stretch factor 1 untuk expand
        
        # Kurangi stretch di bawah agar grafik dapat space lebih
        left_layout.addStretch(0)

        # === KOLOM KANAN (Konfigurasi) ===
        right_column = self.create_config_panel()
        
        # Tambahkan kolom ke layout utama
        main_layout.addWidget(left_column, 7)
        main_layout.addWidget(right_column, 3)

        # Terapkan Stylesheet
        self.set_stylesheet()

    def setup_ui_references(self):
        """Setup references to UI elements for dynamic updates"""
        # Will be populated as widgets are created
        pass
    
    # --- 1. Widget Header ---
    def create_header(self):
        header_widget = QFrame()
        header_widget.setObjectName("headerCard")
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)

        # Logo dan Judul
        logo_label = QLabel()
        logo_path = "asset/img/kartel-logo.png"
        if os.path.exists(logo_path):
            logo_pixmap = QPixmap(logo_path)
            if not logo_pixmap.isNull():
                logo_label.setPixmap(logo_pixmap.scaled(64, 64, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            else:
                logo_label.setPixmap(qta.icon("fa5s.cube", color="#4f46e5").pixmap(QSize(60, 60)))
        else:
            logo_label.setPixmap(qta.icon("fa5s.cube", color="#4f46e5").pixmap(QSize(60, 60)))

        title_layout = QVBoxLayout()
        title_layout.setSpacing(0)
        title_label = QLabel("KARTEL")
        title_label.setObjectName("headerTitle")
        subtitle_label = QLabel("Kendali Automasi Ruangan Telur")
        subtitle_label.setObjectName("headerSubtitle")
        title_layout.addWidget(title_label)
        title_layout.addWidget(subtitle_label)

        header_layout.addWidget(logo_label)
        header_layout.addLayout(title_layout)
        header_layout.addStretch()

        # Tombol Status (akan diupdate secara dinamis)
        self.status_connect_btn = QPushButton(" Tidak Terhubung")
        # Gunakan icon wifi-notconnect.svg untuk initial state (tidak terhubung)
        self.status_connect_btn.setIcon(QIcon(self.load_svg_icon("wifi-notconnect.svg", QSize(20, 20))))
        self.status_connect_btn.setObjectName("statusNotConnected")

        self.status_day_btn = QPushButton(" Hari ke- 3 dari 21")
        self.status_day_btn.setIcon(QIcon(self.load_svg_icon("calendar.svg", QSize(20, 20))))
        self.status_day_btn.setObjectName("statusDay")
        self.status_day_btn.clicked.connect(self.demo_advance_day)  # Add click handler untuk demo
        
        header_layout.addWidget(self.status_connect_btn)
        header_layout.addWidget(self.status_day_btn)
        
        return header_widget

    # --- 2. Widget Card Vital ---
    def create_vital_cards(self):
        vitals_widget = QWidget()
        vitals_layout = QHBoxLayout(vitals_widget)
        vitals_layout.setContentsMargins(0, 0, 0, 0)
        vitals_layout.setSpacing(20)
        
        # Card Suhu
        self.suhu_card = self.create_single_vital_card(
            icon_svg="temperature.svg",
            icon_size=QSize(50, 50),
            title="SUHU",
            current_value="37.5°C",
            target_value="38.0°C",
            description="Setpoint yang diinginkan",
            object_name="suhuCard"
        )
        vitals_layout.addWidget(self.suhu_card)
        
        # Card Kelembaban
        self.humidity_card = self.create_single_vital_card(
            icon_svg="humidity.svg",
            icon_size=QSize(50, 50),
            title="KELEMBABAN",
            current_value="58.0%",
            target_value="60.0%",
            description="Setpoint yang diinginkan",
            object_name="kelembabanCard"
        )
        vitals_layout.addWidget(self.humidity_card)
        
        return vitals_widget

    def create_single_vital_card(self, icon_svg, icon_size, title, current_value, target_value, description, object_name):
        card = QFrame()
        card.setObjectName(object_name)
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(4)

        # Baris Judul
        title_layout = QHBoxLayout()
        icon_label = QLabel()
        icon_label.setPixmap(self.load_svg_icon(icon_svg, icon_size))
        
        title_label = QLabel(title)
        title_label.setObjectName("vitalTitle")
        title_layout.addWidget(icon_label)
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        card_layout.addLayout(title_layout)

        # Nilai Saat Ini
        current_desc_label = QLabel(f"{title.capitalize()} saat ini")
        current_desc_label.setObjectName("vitalCurrentDesc")
        
        current_value_label = QLabel(current_value)
        current_value_label.setObjectName("vitalCurrentValue")
        
        # Store references for updates
        if title == "SUHU":
            self.temp_current_label = current_value_label
        elif title == "KELEMBABAN":
            self.humidity_current_label = current_value_label
        
        card_layout.addWidget(current_desc_label)
        card_layout.addWidget(current_value_label)
        card_layout.addSpacing(10)

        # Target
        target_box = QFrame()
        target_box.setObjectName("targetBox")
        target_box_layout = QVBoxLayout(target_box)
        target_box_layout.setContentsMargins(12, 8, 12, 8)
        
        target_label = QLabel(f"Target: {target_value}")
        target_label.setObjectName("vitalTarget")
        
        # Store references for updates
        if title == "SUHU":
            self.temp_target_label = target_label
        elif title == "KELEMBABAN":
            self.humidity_target_label = target_label
        
        target_desc_label = QLabel(description)
        target_desc_label.setObjectName("vitalTargetDesc")
        
        target_box_layout.addWidget(target_label)
        target_box_layout.addWidget(target_desc_label)
        
        card_layout.addWidget(target_box)
        
        return card

    # --- 3. Widget Status Sistem ---
    def create_status_system(self):
        status_widget_container = QWidget()
        status_main_layout = QVBoxLayout(status_widget_container)
        status_main_layout.setContentsMargins(0, 0, 0, 0)
        status_main_layout.setSpacing(10)

        # Judul "STATUS SISTEM"
        title_layout = QHBoxLayout()
        icon_label = QLabel()
        icon_label.setPixmap(self.load_svg_icon("status-system.svg", QSize(40, 40)))
        
        title_label = QLabel("STATUS SISTEM")
        title_label.setObjectName("sectionTitle")
        
        title_layout.addWidget(icon_label)
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        status_main_layout.addLayout(title_layout)

        # 4 Kartu Status
        status_cards_widget = QWidget()
        status_cards_layout = QHBoxLayout(status_cards_widget)
        status_cards_layout.setContentsMargins(0, 0, 0, 0)
        status_cards_layout.setSpacing(15)

        # Create status cards with references
        self.pemanas_card = self.create_single_status_card("pemanas.svg", "Pemanas", "Aktif", "statusAktif")
        self.humidifier_card = self.create_single_status_card("humidifier.svg", "Humidifier", "Non-aktif", "statusNonAktif")
        self.motor_card = self.create_single_status_card("motor-dinamo.svg", "Motor Pembalik", "Menunggu", "statusMenunggu")
        self.timer_card = self.create_single_status_card("sand-clock.svg", "Putaran Berikutnya", "2:30:15", "statusTimer")
        
        status_cards_layout.addWidget(self.pemanas_card)
        status_cards_layout.addWidget(self.humidifier_card)
        status_cards_layout.addWidget(self.motor_card)
        status_cards_layout.addWidget(self.timer_card)
        
        status_main_layout.addWidget(status_cards_widget)
        return status_widget_container

    def create_single_status_card(self, icon_svg, title, status_text, status_style_name):
        card = QFrame()
        card.setObjectName("statusCard")
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(15)

        # Ikon dan Judul
        icon_title_layout = QHBoxLayout()
        icon_label = QLabel()
        icon_label.setPixmap(self.load_svg_icon(icon_svg, QSize(40, 40)))
        icon_label.setObjectName("statusCardIcon")
        
        title_label = QLabel(title)
        title_label.setObjectName("statusCardTitle")
        
        icon_title_layout.addWidget(icon_label)
        icon_title_layout.addWidget(title_label)
        icon_title_layout.addStretch()
        
        card_layout.addLayout(icon_title_layout)

        # Status Label
        status_label = QLabel(status_text)
        status_label.setObjectName(status_style_name)
        status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Store references
        if "Pemanas" in title:
            self.pemanas_status_label = status_label
        elif "Humidifier" in title:
            self.humidifier_status_label = status_label
        elif "Motor" in title:
            self.motor_status_label = status_label
        elif "Putaran" in title:
            self.timer_status_label = status_label
        
        card_layout.addWidget(status_label)
        return card

    # --- 4. Widget Grafik ---
    def create_graph_panel(self):
        graph_widget_container = QFrame()
        graph_widget_container.setObjectName("graphCard")
        graph_widget_container.setMinimumHeight(380)  # Kurangi sedikit dari 450 ke 380
        graph_main_layout = QVBoxLayout(graph_widget_container)
        graph_main_layout.setContentsMargins(16, 16, 16, 20)  # Tambah bottom margin
        
        # Judul
        title_layout = QHBoxLayout()
        icon_label = QLabel()
        icon_label.setPixmap(self.load_svg_icon("graph.svg", QSize(40, 40)))
        
        title_label = QLabel("GRAFIK TREN (REAL-TIME)")
        title_label.setObjectName("sectionTitle")
        
        title_layout.addWidget(icon_label)
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        graph_main_layout.addLayout(title_layout)
        
        # Plot Widget
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground('#ffffff')
        self.plot_widget.setMenuEnabled(False)
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        self.plot_widget.setMinimumHeight(280)  # Kurangi dari 350 ke 280
        self.plot_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # Initialize with historical data
        hist_data = self.controller.get_historical_data()
        self.initialize_graph_data(hist_data)
        
        # Setup plot
        self.setup_graph_plot()

        graph_main_layout.addWidget(self.plot_widget)
        return graph_widget_container
    
    def initialize_graph_data(self, hist_data):
        """Initialize graph with historical data"""
        from datetime import datetime, timedelta
        import time
        
        # Convert historical data to our format
        current_time = time.time()
        
        for i, (temp, humidity) in enumerate(zip(hist_data["temperature"], hist_data["humidity"])):
            # Create timestamps going backwards from current time
            timestamp = current_time - (len(hist_data["temperature"]) - i - 1) * 300  # 5 minute intervals
            
            self.graph_data["timestamps"].append(timestamp)
            self.graph_data["temperature"].append(temp)
            self.graph_data["humidity"].append(humidity)
    
    def setup_graph_plot(self):
        """Setup the graph plotting elements"""
        # Setup axes ranges
        self.plot_widget.setYRange(30, 45)  # Temperature range
        
        # Add some margin for bottom axis labels
        self.plot_widget.plotItem.setContentsMargins(10, 10, 10, 25)  # Extra bottom margin
        
        # Setup X axis (time labels)
        self.update_x_axis()

        # Setup Y axis left (Temperature)
        ax_left = self.plot_widget.getAxis('left')
        ax_left.setLabel("Suhu (°C)", color="#FFC107")
        ax_left.setTextPen(QColor("#FFC107"))

        # Create temperature plot line
        self.temp_plot = self.plot_widget.plot(
            [], [], 
            pen=pg.mkPen(color="#FFC107", width=3),
            symbol='o', symbolSize=6, symbolBrush='#FFC107',
            name="Suhu"
        )

        # Create second ViewBox for humidity
        self.view_box_2 = pg.ViewBox()
        self.plot_widget.plotItem.scene().addItem(self.view_box_2)
        self.view_box_2.setYRange(40, 80)

        # Setup Y axis right (Humidity)
        ax_right = pg.AxisItem('right')
        ax_right.setLabel("Kelembaban (%)", color="#5A3FFF")
        ax_right.setTextPen(QColor("#5A3FFF"))
        ax_right.linkToView(self.view_box_2)
        
        self.plot_widget.plotItem.layout.addItem(ax_right, 2, 3)
        self.view_box_2.linkView(pg.ViewBox.XAxis, self.plot_widget.plotItem.getViewBox())

        # Create humidity plot elements
        self.humidity_plot = pg.PlotCurveItem(
            [], [],
            pen=pg.mkPen(color="#5A3FFF", width=3),
        )
        self.humidity_symbol = pg.ScatterPlotItem(
            [], [],
            symbol='o', size=6, brush='#5A3FFF'
        )
        self.view_box_2.addItem(self.humidity_plot)
        self.view_box_2.addItem(self.humidity_symbol)

        # Setup tooltip
        self.setup_graph_tooltip()
        
        # Update view when resized
        def update_views():
            self.view_box_2.setGeometry(self.plot_widget.plotItem.vb.sceneBoundingRect())
        
        self.plot_widget.plotItem.vb.sigResized.connect(update_views)
        
        # Initial plot
        self.update_graph_plot()
        update_views()
    
    def setup_graph_tooltip(self):
        """Setup interactive tooltip for graph"""
        self.tooltip = QLabel(self.plot_widget)
        self.tooltip.setStyleSheet("""
            QLabel {
                background-color: rgba(255, 255, 255, 0.95);
                border: 1px solid #e5e7eb;
                border-radius: 8px;
                padding: 8px 12px;
                color: #374151;
                font-size: 12px;
                font-weight: 600;
            }
        """)
        self.tooltip.hide()

        # Mouse move event for tooltip
        def on_mouse_move(event):
            if self.plot_widget.sceneBoundingRect().contains(event):
                mouse_pos = self.plot_widget.plotItem.vb.mapSceneToView(event)
                x_pos = int(mouse_pos.x())
                
                if 0 <= x_pos < len(self.graph_data["temperature"]):
                    from datetime import datetime
                    
                    timestamp = self.graph_data["timestamps"][x_pos]
                    time_str = datetime.fromtimestamp(timestamp).strftime("%H:%M")
                    temp_val = self.graph_data["temperature"][x_pos]
                    humidity_val = self.graph_data["humidity"][x_pos]
                    
                    tooltip_text = f"""<div style="color: #6b7280; font-size: 11px; margin-bottom: 4px;">{time_str}</div>
<div style="color: #5A3FFF;">Kelembaban: {humidity_val}%</div>
<div style="color: #FFC107;">Suhu: {temp_val}°C</div>"""
                    
                    self.tooltip.setText(tooltip_text)
                    self.tooltip.adjustSize()
                    
                    # Position tooltip
                    try:
                        tooltip_pos = self.plot_widget.mapFromScene(event)
                        self.tooltip.move(tooltip_pos.x() + 10, tooltip_pos.y() - 60)
                        self.tooltip.show()
                    except:
                        pass
                else:
                    self.tooltip.hide()
            else:
                self.tooltip.hide()

        self.plot_widget.scene().sigMouseMoved.connect(on_mouse_move)
    
    def update_x_axis(self):
        """Update X axis with time labels"""
        if not self.graph_data["timestamps"]:
            return
            
        from datetime import datetime
        
        # Create time labels
        time_labels = []
        x_positions = []
        
        for i, timestamp in enumerate(self.graph_data["timestamps"]):
            time_str = datetime.fromtimestamp(timestamp).strftime("%H:%M")
            time_labels.append(time_str)
            x_positions.append(i)
        
        # Update X axis ticks
        x_ticks = [list(zip(x_positions, time_labels))]
        ax_bottom = self.plot_widget.getAxis('bottom')
        ax_bottom.setTicks(x_ticks)
        ax_bottom.setTextPen(QColor("#6b7280"))
        
        # Set X range
        if len(x_positions) > 1:
            self.plot_widget.setXRange(-0.5, len(x_positions) - 0.5)
    
    def update_graph_plot(self):
        """Update the graph with current data"""
        if not self.graph_data["temperature"]:
            return
            
        # Create x-axis positions
        x_data = list(range(len(self.graph_data["temperature"])))
        
        # Update temperature plot
        self.temp_plot.setData(x_data, self.graph_data["temperature"])
        
        # Update humidity plot
        self.humidity_plot.setData(x_data, self.graph_data["humidity"])
        self.humidity_symbol.setData(x_data, self.graph_data["humidity"])
        
        # Update X axis
        self.update_x_axis()
        
        # Update humidity ViewBox range
        self.view_box_2.setXRange(-0.5, len(x_data) - 0.5)
        
    # --- 5. Widget Panel Konfigurasi ---
    def create_config_panel(self):
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setObjectName("configScrollArea")
        
        config_widget = QWidget()
        config_widget.setObjectName("configWidget")
        config_layout = QVBoxLayout(config_widget)
        config_layout.setSpacing(20)
        
        # Judul
        title_layout = QHBoxLayout()
        icon_label = QLabel()
        icon_label.setPixmap(self.load_svg_icon("settings.svg", QSize(40, 40)))
        
        title_label = QLabel("KONFIGURASI")
        title_label.setObjectName("sectionTitle")
        
        title_layout.addWidget(icon_label)
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        config_layout.addLayout(title_layout)
        
        # --- Profil Inkubasi ---
        config_layout.addWidget(self.create_form_label("Profil Inkubasi"))
        self.profil_combo = QComboBox()
        
        # Load profiles from controller
        profiles = self.controller.get_incubation_profiles()
        for profile in profiles:
            self.profil_combo.addItem(profile["name"])
        
        self.profil_combo.currentTextChanged.connect(self.on_profile_changed)
        config_layout.addWidget(self.profil_combo)
        
        # --- Pengaturan Setpoint ---
        config_layout.addWidget(self.create_form_label("Pengaturan Setpoint"))
        config_layout.addWidget(QLabel("Target Suhu(°C)"))
        self.suhu_input = QLineEdit("38.0")
        self.suhu_input.textChanged.connect(self.validate_temperature_input)
        config_layout.addWidget(self.suhu_input)
        
        config_layout.addWidget(QLabel("Target Kelembaban(%)"))
        self.kelembaban_input = QLineEdit("60.0")
        self.kelembaban_input.textChanged.connect(self.validate_humidity_input)
        config_layout.addWidget(self.kelembaban_input)
        
        apply_btn = QPushButton("Terapkan Pengaturan")
        apply_btn.setObjectName("applyButton")
        apply_btn.clicked.connect(self.apply_settings)
        config_layout.addWidget(apply_btn)
        
        config_layout.addWidget(self.create_divider())

        # --- Kontrol Manual ---
        config_layout.addWidget(self.create_form_label("Kontrol Manual"))
        
        self.heater_toggle_btn = QPushButton(" Toggle Pemanas")
        self.heater_toggle_btn.setIcon(QIcon(self.load_svg_icon("pemanas-control.svg", QSize(20, 20))))
        self.heater_toggle_btn.setObjectName("heaterButton")
        self.heater_toggle_btn.clicked.connect(lambda: self.toggle_device("pemanas"))
        config_layout.addWidget(self.heater_toggle_btn)
        
        self.humidifier_toggle_btn = QPushButton(" Toggle Humidifier")
        self.humidifier_toggle_btn.setIcon(QIcon(self.load_svg_icon("humidifier-control.svg", QSize(20, 20))))
        self.humidifier_toggle_btn.setObjectName("humidifierButton")
        self.humidifier_toggle_btn.clicked.connect(lambda: self.toggle_device("humidifier"))
        config_layout.addWidget(self.humidifier_toggle_btn)
        
        config_layout.addWidget(self.create_divider())

        # --- Koneksi MQTT ---
        config_layout.addWidget(self.create_form_label("Koneksi MQTT"))
        
        # Username
        username_layout = QHBoxLayout()
        username_icon = QLabel()
        username_icon.setPixmap(self.load_svg_icon("username.svg", QSize(24, 24)))
        username_label = QLabel("Username")
        username_layout.addWidget(username_icon)
        username_layout.addWidget(username_label)
        username_layout.addStretch()
        config_layout.addLayout(username_layout)
        
        mqtt_settings = self.controller.get_mqtt_settings()
        self.user_input = QLineEdit(mqtt_settings["username"])
        config_layout.addWidget(self.user_input)
        
        # Password
        password_layout = QHBoxLayout()
        password_icon = QLabel()
        password_icon.setPixmap(self.load_svg_icon("password.svg", QSize(24, 24)))
        password_label = QLabel("Password")
        password_layout.addWidget(password_icon)
        password_layout.addWidget(password_label)
        password_layout.addStretch()
        config_layout.addLayout(password_layout)
        
        self.pass_input = QLineEdit(mqtt_settings["password"])
        self.pass_input.setEchoMode(QLineEdit.EchoMode.Password)
        config_layout.addWidget(self.pass_input)
        
        # --- Info Box ---
        info_box = QFrame()
        info_box.setObjectName("infoBox")
        
        info_main_layout = QVBoxLayout(info_box)
        info_main_layout.setContentsMargins(0, 0, 0, 0)
        info_main_layout.setSpacing(12)
        
        info_header_layout = QHBoxLayout()
        info_header_layout.setContentsMargins(0, 0, 0, 0)
        info_header_layout.setSpacing(8)
        
        info_icon = QLabel()
        info_icon.setPixmap(self.load_svg_icon("information-mqtt.svg", QSize(24, 24)))
        
        info_title = QLabel("Informasi Koneksi")
        info_title.setObjectName("infoHeaderTitle")
        
        info_header_layout.addWidget(info_icon)
        info_header_layout.addWidget(info_title)
        info_header_layout.addStretch()
        
        info_text = QLabel("Pastikan perangkat IoT ESP32 Anda sudah terkonfigurasi dengan broker MQTT yang sama. Aplikasi ini akan subscribe ke topic yang Anda tentukan untuk menerima data sensor secara real-time.")
        info_text.setWordWrap(True)
        info_text.setObjectName("infoContentText")
        
        info_main_layout.addLayout(info_header_layout)
        info_main_layout.addWidget(info_text)
        config_layout.addWidget(info_box)
        
        config_layout.addStretch()

        # --- Tombol Aksi ---
        button_layout = QHBoxLayout()
        cancel_btn = QPushButton("Batalkan")
        cancel_btn.setObjectName("cancelButton")
        cancel_btn.clicked.connect(self.reset_mqtt_settings)
        
        self.connect_btn = QPushButton("Hubungkan Ke Broker")
        self.connect_btn.setObjectName("connectButton")
        self.connect_btn.clicked.connect(self.attempt_mqtt_connection)
        
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(self.connect_btn)
        config_layout.addLayout(button_layout)
        
        scroll_area.setWidget(config_widget)
        return scroll_area

    # --- Event Handlers ---
    def on_profile_changed(self, profile_name):
        """Handle profile selection change"""
        success = self.controller.apply_profile(profile_name)
        if success:
            # Update input fields
            target_data = self.controller.data_manager.get_target_values()
            self.suhu_input.setText(str(target_data["temperature"]))
            self.kelembaban_input.setText(str(target_data["humidity"]))
            self.show_message("Info", f"Profil '{profile_name}' berhasil diterapkan!")

    def apply_settings(self):
        """Apply temperature and humidity settings"""
        try:
            temp = float(self.suhu_input.text())
            humidity = float(self.kelembaban_input.text())
            
            self.controller.set_target_temperature(temp)
            self.controller.set_target_humidity(humidity)
            
            self.show_message("Sukses", "Pengaturan berhasil diterapkan!")
        except ValueError:
            self.show_message("Error", "Mohon masukkan nilai yang valid!")

    def toggle_device(self, device):
        """Toggle device on/off"""
        result = self.controller.toggle_device(device)
        status = "diaktifkan" if result else "dinonaktifkan"
        self.show_message("Info", f"{device.capitalize()} berhasil {status}!")

    def validate_temperature_input(self, text):
        """Validate temperature input"""
        try:
            value = float(text)
            if not (30.0 <= value <= 45.0):
                self.suhu_input.setStyleSheet("border: 2px solid red;")
            else:
                self.suhu_input.setStyleSheet("")
        except ValueError:
            if text:  # Only show error if there's text
                self.suhu_input.setStyleSheet("border: 2px solid red;")

    def validate_humidity_input(self, text):
        """Validate humidity input"""
        try:
            value = float(text)
            if not (40.0 <= value <= 80.0):
                self.kelembaban_input.setStyleSheet("border: 2px solid red;")
            else:
                self.kelembaban_input.setStyleSheet("")
        except ValueError:
            if text:
                self.kelembaban_input.setStyleSheet("border: 2px solid red;")

    def attempt_mqtt_connection(self):
        """Attempt MQTT connection"""
        username = self.user_input.text()
        password = self.pass_input.text()
        
        if not username or not password:
            self.show_message("Error", "Username dan password tidak boleh kosong!")
            return
        
        self.connect_btn.setText("Menghubungkan...")
        self.connect_btn.setEnabled(False)
        
        # Simulate connection attempt
        success = self.controller.simulate_mqtt_connection(username, password)
        
        if success:
            self.show_message("Sukses", "Berhasil terhubung ke broker MQTT!")
        else:
            self.show_message("Error", "Gagal terhubung ke broker MQTT!")
        
        self.connect_btn.setText("Hubungkan Ke Broker")
        self.connect_btn.setEnabled(True)

    def reset_mqtt_settings(self):
        """Reset MQTT settings to default"""
        mqtt_settings = self.controller.get_mqtt_settings()
        self.user_input.setText(mqtt_settings["username"])
        self.pass_input.setText(mqtt_settings["password"])

    def demo_advance_day(self):
        """Demo function to advance incubation day"""
        success = self.controller.data_manager.advance_incubation_day()
        if success:
            self.show_message("Info", f"Hari inkubasi maju ke hari {self.controller.data_manager.incubation_day}!")
        else:
            self.show_message("Info", "Inkubasi sudah selesai (21 hari)!")
            # Reset to day 1 for demo
            self.controller.data_manager.reset_incubation_day(1)

    def show_message(self, title, message):
        """Show message box"""
        msg = QMessageBox()
        msg.setWindowTitle(title)
        msg.setText(message)
        msg.exec()

    # --- Dynamic Update Slots ---
    @pyqtSlot(dict)
    def update_sensor_display(self, data):
        """Update sensor display with new data"""
        current = data["current"]
        target = data["target"]
        
        # Update current values
        self.temp_current_label.setText(f"{current['temperature']}°C")
        self.humidity_current_label.setText(f"{current['humidity']}%")
        
        # Update targets
        self.temp_target_label.setText(f"Target: {target['temperature']}°C")
        self.humidity_target_label.setText(f"Target: {target['humidity']}%")
    
    @pyqtSlot(dict)
    def update_graph_data(self, data):
        """Update graph with new real-time data"""
        import time
        
        current = data["current"]
        current_time = time.time()
        
        # Add new data point
        self.graph_data["timestamps"].append(current_time)
        self.graph_data["temperature"].append(current['temperature'])
        self.graph_data["humidity"].append(current['humidity'])
        
        # Keep only last N points to prevent memory growth
        max_points = self.graph_data["max_points"]
        if len(self.graph_data["timestamps"]) > max_points:
            self.graph_data["timestamps"] = self.graph_data["timestamps"][-max_points:]
            self.graph_data["temperature"] = self.graph_data["temperature"][-max_points:]
            self.graph_data["humidity"] = self.graph_data["humidity"][-max_points:]
        
        # Update the graph plot
        self.update_graph_plot()

    @pyqtSlot(dict)
    def update_device_status_display(self, status):
        """Update device status display"""
        # Update pemanas
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
        
        # Update motor
        if "motor" in status:
            self.motor_status_label.setText(status["motor"]["status"])
        
        # Update timer
        if "timer" in status:
            self.timer_status_label.setText(status["timer"]["countdown"])
        
        # Reapply stylesheet to update colors
        self.set_stylesheet()

    @pyqtSlot(dict)
    def update_connection_display(self, connection):
        """Update connection status display"""
        if connection["connected"]:
            self.status_connect_btn.setText(" Terhubung")
            self.status_connect_btn.setObjectName("statusConnected")
            # Gunakan icon wifi.svg untuk status terhubung
            self.status_connect_btn.setIcon(QIcon(self.load_svg_icon("wifi.svg", QSize(20, 20))))
        else:
            self.status_connect_btn.setText(" Tidak Terhubung")
            self.status_connect_btn.setObjectName("statusNotConnected")
            # Gunakan icon wifi-notconnect.svg untuk status tidak terhubung
            self.status_connect_btn.setIcon(QIcon(self.load_svg_icon("wifi-notconnect.svg", QSize(20, 20))))
        
        self.status_day_btn.setText(f" {connection['day_text']}")
        
        # Reapply stylesheet
        self.set_stylesheet()

    # --- Helper Methods ---
    def create_form_label(self, text):
        label = QLabel(text)
        label.setObjectName("formSectionTitle")
        return label
        
    def create_divider(self):
        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setFrameShadow(QFrame.Shadow.Sunken)
        divider.setObjectName("divider")
        return divider

    # --- Stylesheet ---
    def set_stylesheet(self):
        """Terapkan stylesheet dari file eksternal"""
        stylesheet = self.load_stylesheet("styles.qss")
        
        if not stylesheet:
            stylesheet = self.get_default_stylesheet()
            
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
                    print(f"✅ Stylesheet berhasil dimuat dari: {style_file}")
                    return stylesheet
            
            raise FileNotFoundError("Stylesheet tidak ditemukan")
            
        except Exception as e:
            print(f"⚠ Error saat memuat stylesheet: {e}")
            return ""

    def get_default_stylesheet(self):
        """Fallback stylesheet"""
        return """
        QWidget {
            font-family: 'Manrope', 'Arial', sans-serif;
            font-size: 14px;
            color: #374151;
        }
        
        KartelDashboardFunctional {
            background-color: #f8f9fa;
        }
        
        #statusConnected {
            background-color: #22c55e;
            color: white;
        }
        
        #statusNotConnected {
            background-color: #ef4444;
            color: white;
        }
        
        #statusAktif {
            background-color: #22c55e;
            color: white;
            padding: 8px;
            border-radius: 4px;
        }
        
        #statusNonAktif {
            background-color: #6b7280;
            color: white;
            padding: 8px;
            border-radius: 4px;
        }
        """

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
    
    window = KartelDashboardFunctional()
    window.show()
    sys.exit(app.exec())