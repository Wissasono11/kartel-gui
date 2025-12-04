import os
import qtawesome as qta
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, 
    QPushButton, QSizePolicy
)
from PyQt6.QtGui import QPixmap, QIcon, QPainter, QColor
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtSvg import QSvgRenderer

# Import konfigurasi path agar gambar selalu ketemu
from src.config.settings import ASSET_DIR

class DashboardWidgets:
    """
    Factory Class untuk membuat komponen UI (Widgets).
    Berfungsi memisahkan kode tampilan yang 'berantakan' dari Main Window.
    """
    
    def __init__(self, main_window):
        self.parent = main_window
    
    def _get_asset_path(self, subfolder, filename):
        """Helper private untuk mendapatkan path aset yang valid"""
        return os.path.join(ASSET_DIR, subfolder, filename)

    def load_svg_icon(self, svg_filename, size=QSize(24, 24)):
        """Load SVG icon dengan warna asli tanpa customisasi"""
        svg_path = self._get_asset_path('svg', svg_filename)
        
        if os.path.exists(svg_path):
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
    
    def create_header(self):
        """Create header widget with logo and status buttons"""
        header_widget = QFrame()
        header_widget.setObjectName("headerCard")
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)

        # Logo dan Judul
        logo_label = QLabel()
        logo_path = self._get_asset_path('img', 'kartel-logo.png')
        
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

        # Tombol Status (Disimpan ke parent agar bisa diupdate Controller)
        self.parent.status_connect_btn = QPushButton(" Tidak Terhubung")
        self.parent.status_connect_btn.setIcon(QIcon(self.load_svg_icon("wifi-notconnect.svg", QSize(20, 20))))
        self.parent.status_connect_btn.setObjectName("statusNotConnected")

        self.parent.status_day_btn = QPushButton(" Hari ke- --")
        self.parent.status_day_btn.setIcon(QIcon(self.load_svg_icon("calendar.svg", QSize(20, 20))))
        self.parent.status_day_btn.setObjectName("statusDay")
        
        header_layout.addWidget(self.parent.status_connect_btn)
        header_layout.addWidget(self.parent.status_day_btn)
        
        return header_widget
    
    def create_vital_cards(self):
        """Create temperature and humidity vital cards"""
        vitals_widget = QWidget()
        vitals_layout = QHBoxLayout(vitals_widget)
        vitals_layout.setContentsMargins(0, 0, 0, 0)
        vitals_layout.setSpacing(20)
        
        # Card Suhu
        self.parent.suhu_card = self.create_single_vital_card(
            icon_svg="temperature.svg",
            icon_size=QSize(50, 50),
            title="SUHU",
            current_value="--.-°C",
            target_value="--.-°C",
            description="Setpoint yang diinginkan",
            object_name="suhuCard"
        )
        vitals_layout.addWidget(self.parent.suhu_card)
        
        # Card Kelembaban
        self.parent.humidity_card = self.create_single_vital_card(
            icon_svg="humidity.svg",
            icon_size=QSize(50, 50),
            title="KELEMBABAN",
            current_value="--.-%",
            target_value=None,  
            description=None,   
            object_name="kelembabanCard"
        )
        vitals_layout.addWidget(self.parent.humidity_card)
        
        return vitals_widget

    def create_single_vital_card(self, icon_svg, icon_size, title, current_value, target_value, description, object_name):
        """Create a single vital monitoring card"""
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
            self.parent.temp_current_label = current_value_label
        elif title == "KELEMBABAN":
            self.parent.humidity_current_label = current_value_label
        
        card_layout.addWidget(current_desc_label)
        card_layout.addWidget(current_value_label)
        card_layout.addSpacing(10)

        # Target (only if target_value is provided)
        if target_value is not None and description is not None:
            target_box = QFrame()
            target_box.setObjectName("targetBox")
            target_box_layout = QVBoxLayout(target_box)
            target_box_layout.setContentsMargins(12, 8, 12, 8)
            
            target_label = QLabel(f"Target: {target_value}")
            target_label.setObjectName("vitalTarget")
            
            # Store references for updates (only for temperature)
            if title == "SUHU":
                self.parent.temp_target_label = target_label
            
            target_desc_label = QLabel(description)
            target_desc_label.setObjectName("vitalTargetDesc")
            
            target_box_layout.addWidget(target_label)
            target_box_layout.addWidget(target_desc_label)
            
            card_layout.addWidget(target_box)
        else:
            if title == "KELEMBABAN":
                card_layout.addSpacing(20)
        
        return card
    
    def create_status_system(self):
        """Create device status system widget"""
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

        # 3 Kartu Status
        status_cards_widget = QWidget()
        status_cards_layout = QHBoxLayout(status_cards_widget)
        status_cards_layout.setContentsMargins(0, 0, 0, 0)
        status_cards_layout.setSpacing(15)

        # Create status cards with references
        self.parent.power_card = self.create_single_status_card("pemanas.svg", "Power", "OFF", "statusNonAktif")
        self.parent.motor_card = self.create_single_status_card("motor-dinamo.svg", "Motor Pembalik", "Idle", "statusMotorIdle")
        self.parent.timer_card = self.create_single_status_card("sand-clock.svg", "Putaran Berikutnya", "--:--", "statusTimer")
        
        status_cards_layout.addWidget(self.parent.power_card)
        status_cards_layout.addWidget(self.parent.motor_card)
        status_cards_layout.addWidget(self.parent.timer_card)
        
        status_main_layout.addWidget(status_cards_widget)
        return status_widget_container

    def create_single_status_card(self, icon_svg, title, status_text, status_style_name):
        """Create a single device status card"""
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
        if "Power" in title:
            self.parent.power_status_label = status_label
        elif "Motor" in title:
            self.parent.motor_status_label = status_label
        elif "Putaran" in title:
            self.parent.timer_status_label = status_label
        
        card_layout.addWidget(status_label)
        return card
    
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