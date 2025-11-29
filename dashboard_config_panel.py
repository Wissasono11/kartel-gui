from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, 
    QLineEdit, QPushButton, QComboBox, QScrollArea
)
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import QSize
from dashboard_ui_components import DashboardUIComponents


class DashboardConfigPanel:
    """Contains configuration panel creation methods"""
    
    def __init__(self, parent):
        self.parent = parent
        self.ui_components = DashboardUIComponents(parent)
    
    def create_config_panel(self):
        """Create configuration panel"""
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
        icon_label.setPixmap(self.ui_components.load_svg_icon("settings.svg", QSize(40, 40)))
        
        title_label = QLabel("PANEL KONFIGURASI")
        title_label.setObjectName("sectionTitle")
        
        title_layout.addWidget(icon_label)
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        config_layout.addLayout(title_layout)
        
        # Profile section
        self.add_profile_section(config_layout)
        
        # Setpoint section
        self.add_setpoint_section(config_layout)
        
        # MQTT section
        self.add_mqtt_section(config_layout)
        
        # Info section
        self.add_info_section(config_layout)
        
        config_layout.addStretch()

        # Action buttons
        self.add_action_buttons(config_layout)
        
        scroll_area.setWidget(config_widget)
        return scroll_area
    
    def add_profile_section(self, layout):
        """Add profile selection section"""
        layout.addWidget(self.ui_components.create_form_label("Profil Inkubasi"))
        self.parent.profil_combo = QComboBox()
        
        # Load profiles from controller
        profiles = self.parent.controller.get_incubation_profiles()
        for profile in profiles:
            self.parent.profil_combo.addItem(profile["name"])
        
        self.parent.profil_combo.currentTextChanged.connect(self.parent.event_handlers.on_profile_changed)
        layout.addWidget(self.parent.profil_combo)
    
    def add_setpoint_section(self, layout):
        """Add setpoint configuration section"""
        layout.addWidget(self.ui_components.create_form_label("Pengaturan Setpoint"))
        layout.addWidget(QLabel("Target Suhu(°C)"))
        
        # Get current target values from controller
        target_data = self.parent.controller.data_manager.get_target_values()
        
        self.parent.suhu_input = QLineEdit(str(target_data["temperature"]))
        self.parent.suhu_input.textChanged.connect(self.parent.event_handlers.validate_temperature_input)
        self.parent.suhu_input.textChanged.connect(self.parent.event_handlers.on_manual_setpoint_change)
        layout.addWidget(self.parent.suhu_input)
        
        # Removed humidity input field as it's not needed
        
        # Apply default profile after input fields are created
        profiles = self.parent.controller.get_incubation_profiles()
        if profiles:
            default_profile = profiles[0]
            # Apply default profile quietly
            success = self.parent.controller.apply_profile(default_profile["name"])
            if success:
                # Sync input field with default profile (only temperature)
                self.parent.suhu_input.setText(str(default_profile["temperature"]))
                # Humidity input field removed
        
        # Store references for cross-updates (temperature only)
        self.parent.input_fields['temperature'] = self.parent.suhu_input
        
        apply_btn = QPushButton("Terapkan Pengaturan")
        apply_btn.setObjectName("applyButton")
        apply_btn.clicked.connect(self.parent.event_handlers.apply_settings)
        layout.addWidget(apply_btn)
        
        layout.addWidget(self.ui_components.create_divider())
    

    
    def add_mqtt_section(self, layout):
        """Add MQTT configuration section"""
        layout.addWidget(self.ui_components.create_form_label("Koneksi MQTT"))
        
        # Username
        username_layout = QHBoxLayout()
        username_icon = QLabel()
        username_icon.setPixmap(self.ui_components.load_svg_icon("username.svg", QSize(24, 24)))
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
        password_icon.setPixmap(self.ui_components.load_svg_icon("password.svg", QSize(24, 24)))
        password_label = QLabel("Password")
        password_layout.addWidget(password_icon)
        password_layout.addWidget(password_label)
        password_layout.addStretch()
        layout.addLayout(password_layout)
        
        self.parent.pass_input = QLineEdit()
        self.parent.pass_input.setPlaceholderText("Masukkan password MQTT")
        self.parent.pass_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.parent.pass_input)
    
    def add_info_section(self, layout):
        """Add information section"""
        info_box = QFrame()
        info_box.setObjectName("infoBox")
        
        info_main_layout = QVBoxLayout(info_box)
        info_main_layout.setContentsMargins(0, 0, 0, 0)
        info_main_layout.setSpacing(12)
        
        info_header_layout = QHBoxLayout()
        info_header_layout.setContentsMargins(0, 0, 0, 0)
        info_header_layout.setSpacing(8)
        
        info_icon = QLabel()
        info_icon.setPixmap(self.ui_components.load_svg_icon("information-mqtt.svg", QSize(24, 24)))
        
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
        layout.addWidget(info_box)
    
    def add_action_buttons(self, layout):
        """Add action buttons"""
        button_layout = QHBoxLayout()
        cancel_btn = QPushButton("Putuskan Koneksi")
        cancel_btn.setObjectName("disconnectButton")
        cancel_btn.clicked.connect(self.parent.event_handlers.reset_mqtt_settings)
        
        self.parent.connect_btn = QPushButton("Hubungkan Ke Broker")
        self.parent.connect_btn.setObjectName("connectButton")
        self.parent.connect_btn.clicked.connect(self.parent.event_handlers.attempt_mqtt_connection)
        
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(self.parent.connect_btn)
        layout.addLayout(button_layout)