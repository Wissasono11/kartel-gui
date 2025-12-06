from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, 
    QLineEdit, QPushButton, QComboBox, QScrollArea, QCheckBox, QDateEdit
)
from PyQt6.QtCore import QSize, QDate
from datetime import datetime

# Import komponen widget kita
from src.views.components.widgets import DashboardWidgets
# Import service untuk kredensial
from src.services.auth_service import AuthService

class DashboardPanels:
    """
    Menangani pembuatan Panel Konfigurasi (Sidebar Kanan).
    Berisi form setting suhu, profil inkubasi, dan koneksi MQTT.
    """
    
    def __init__(self, main_window):
        self.parent = main_window
        # Helper widget untuk load icon & label
        self.widgets = DashboardWidgets(main_window)
    
    def create_config_panel(self):
        """Membuat panel konfigurasi utama"""
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setObjectName("configScrollArea")
        
        config_widget = QWidget()
        config_widget.setObjectName("configWidget")
        config_layout = QVBoxLayout(config_widget)
        config_layout.setSpacing(20)
        
        # --- Judul Panel ---
        title_layout = QHBoxLayout()
        icon_label = QLabel()
        icon_label.setPixmap(self.widgets.load_svg_icon("settings.svg", QSize(40, 40)))
        
        title_label = QLabel("PANEL KONFIGURASI")
        title_label.setObjectName("sectionTitle")
        
        title_layout.addWidget(icon_label)
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        config_layout.addLayout(title_layout)
        
        # --- Bagian-bagian Form ---
        self.add_profile_section(config_layout)
        self.add_setpoint_section(config_layout)
        self.add_mqtt_section(config_layout)
        self.add_info_section(config_layout)
        
        config_layout.addStretch()

        # --- Tombol Aksi ---
        self.add_action_buttons(config_layout)
        
        scroll_area.setWidget(config_widget)
        return scroll_area
    
    def add_profile_section(self, layout):
        """Dropdown Pemilihan Profil"""
        layout.addWidget(self.widgets.create_form_label("Profil Inkubasi"))
        self.parent.profil_combo = QComboBox()
        
        # Ambil profil dari Controller (Pastikan Controller sudah init)
        if hasattr(self.parent, 'controller'):
            profiles = self.parent.controller.get_incubation_profiles()
            for profile in profiles:
                self.parent.profil_combo.addItem(profile["name"])
            
            print(f"✅ Profile combo initialized with {len(profiles)} profiles")
        
        # Hubungkan Sinyal (Pastikan EventHandlers sudah init)
        if hasattr(self.parent, 'event_handlers'):
            self.parent.profil_combo.currentTextChanged.connect(
                self.parent.event_handlers.on_profile_changed
            )
        
        layout.addWidget(self.parent.profil_combo)
        
        # Tanggal Mulai Inkubasi
        layout.addWidget(self.widgets.create_form_label("Tanggal Mulai Inkubasi"))
    
        self.parent.start_date_input = QDateEdit()
        self.parent.start_date_input.setCalendarPopup(True) 
        self.parent.start_date_input.setDisplayFormat("dd MMM yyyy")
        
        # [BARU] Set ID agar bisa di-style di QSS untuk tinggi/padding
        self.parent.start_date_input.setObjectName("dateInput") 
        
        # Inisialisasi tanggal
        if hasattr(self.parent, 'controller'):
            saved_date = self.parent.controller.mqtt_service.get_start_date()
            if saved_date:
                qdate = QDate(saved_date.year, saved_date.month, saved_date.day)
                self.parent.start_date_input.setDate(qdate)
            else:
                self.parent.start_date_input.setDate(QDate.currentDate())
                
        layout.addWidget(self.parent.start_date_input)
        
        # Tombol Update Tanggal
        update_date_btn = QPushButton("Update Tanggal")
        update_date_btn.setObjectName("applyButton") 
        
        update_date_btn.clicked.connect(self.parent.event_handlers.update_incubation_date)
        layout.addWidget(update_date_btn)
    
    def add_setpoint_section(self, layout):
        """Form Input Suhu Manual"""
        layout.addWidget(self.widgets.create_form_label("Pengaturan Setpoint"))
        layout.addWidget(QLabel("Target Suhu(°C)"))
        
        # Default value placeholder
        initial_temp = "38.0"
        if hasattr(self.parent, 'controller'):
            target_data = self.parent.controller.data_manager.get_target_values()
            initial_temp = str(target_data["temperature"])
            
        self.parent.suhu_input = QLineEdit(initial_temp)
        
        # Hubungkan sinyal validasi input
        if hasattr(self.parent, 'event_handlers'):
            self.parent.suhu_input.textChanged.connect(
                self.parent.event_handlers.validate_temperature_input
            )
            self.parent.suhu_input.textChanged.connect(
                self.parent.event_handlers.on_manual_setpoint_change
            )
            
        layout.addWidget(self.parent.suhu_input)
        
        # Simpan referensi field input ke parent agar mudah diakses
        if not hasattr(self.parent, 'input_fields'):
            self.parent.input_fields = {}
        self.parent.input_fields['temperature'] = self.parent.suhu_input        
        
        # Tombol Terapkan
        apply_btn = QPushButton("Terapkan Pengaturan")
        apply_btn.setObjectName("applyButton")
        if hasattr(self.parent, 'event_handlers'):
            apply_btn.clicked.connect(self.parent.event_handlers.apply_settings)
        layout.addWidget(apply_btn)
        
        layout.addWidget(self.widgets.create_divider())
        
        # Inisialisasi Profil Default (Logic Startup)
        # Sebaiknya logic 'apply profile' dipanggil di Main Window setelah UI ready, 
        # bukan di sini agar constructor tidak terlalu berat.
    
    def add_mqtt_section(self, layout):
        """Form Login MQTT"""
        layout.addWidget(self.widgets.create_form_label("Koneksi MQTT"))
        
        # Username
        username_layout = QHBoxLayout()
        username_icon = QLabel()
        username_icon.setPixmap(self.widgets.load_svg_icon("username.svg", QSize(24, 24)))
        username_label = QLabel("Username")
        username_layout.addWidget(username_icon)
        username_layout.addWidget(username_label)
        username_layout.addStretch()
        layout.addLayout(username_layout)
        
        self.parent.user_input = QLineEdit()
        self.parent.user_input.setPlaceholderText("Masukkan username MQTT")
        layout.addWidget(self.parent.user_input)
        
        # Password
        password_layout = QHBoxLayout()
        password_icon = QLabel()
        password_icon.setPixmap(self.widgets.load_svg_icon("password.svg", QSize(24, 24)))
        password_label = QLabel("Password")
        password_layout.addWidget(password_icon)
        password_layout.addWidget(password_label)
        password_layout.addStretch()
        layout.addLayout(password_layout)
        
        self.parent.pass_input = QLineEdit()
        self.parent.pass_input.setPlaceholderText("Masukkan password MQTT")
        self.parent.pass_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.parent.pass_input)
        
        # Remember Me
        self.parent.remember_checkbox = QCheckBox("Ingat kredensial saya")
        self.parent.remember_checkbox.setObjectName("rememberCheckbox")
        layout.addWidget(self.parent.remember_checkbox)
        
        # Load Credential via Service
        self.load_saved_credentials()
    
    def add_info_section(self, layout):
        """Box Informasi"""
        info_box = QFrame()
        info_box.setObjectName("infoBox")
        
        info_main_layout = QVBoxLayout(info_box)
        info_main_layout.setContentsMargins(0, 0, 0, 0)
        info_main_layout.setSpacing(12)
        
        info_header_layout = QHBoxLayout()
        info_header_layout.setContentsMargins(0, 0, 0, 0)
        info_header_layout.setSpacing(8)
        
        info_icon = QLabel()
        info_icon.setPixmap(self.widgets.load_svg_icon("information-mqtt.svg", QSize(24, 24)))
        
        info_title = QLabel("Informasi Koneksi")
        info_title.setObjectName("infoHeaderTitle")
        
        info_header_layout.addWidget(info_icon)
        info_header_layout.addWidget(info_title)
        info_header_layout.addStretch()
        
        info_text = QLabel("Aplikasi ini akan subscribe ke topic yang Anda tentukan untuk menerima data sensor secara real-time.")
        info_text.setWordWrap(True)
        info_text.setObjectName("infoContentText")
        
        info_main_layout.addLayout(info_header_layout)
        info_main_layout.addWidget(info_text)
        layout.addWidget(info_box)
    
    def add_action_buttons(self, layout):
        """Tombol Connect/Disconnect"""
        button_layout = QHBoxLayout()
        cancel_btn = QPushButton("Putuskan Koneksi")
        cancel_btn.setObjectName("disconnectButton")
        
        self.parent.connect_btn = QPushButton("Hubungkan Ke Broker")
        self.parent.connect_btn.setObjectName("connectButton")
        
        if hasattr(self.parent, 'event_handlers'):
            cancel_btn.clicked.connect(self.parent.event_handlers.reset_mqtt_settings)
            self.parent.connect_btn.clicked.connect(self.parent.event_handlers.attempt_mqtt_connection)
        
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(self.parent.connect_btn)
        layout.addLayout(button_layout)
    
    def load_saved_credentials(self):
        """Muat kredensial menggunakan AuthService"""
        try:
            saved_creds = AuthService.load_credentials()
            
            if saved_creds:
                username = saved_creds.get("username", "")
                password = saved_creds.get("password", "")
                
                if username and password:
                    self.parent.user_input.setText(username)
                    self.parent.pass_input.setText(password)
                    self.parent.remember_checkbox.setChecked(True)
                    print(f"✅ Auto-loaded saved credentials for: {username}")
        except Exception as e:
            print(f"⚠ Error loading saved credentials: {e}")