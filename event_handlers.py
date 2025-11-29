from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtCore import Qt, QTimer


class DashboardEventHandlers:
    """Contains all event handling methods"""
    
    def __init__(self, parent):
        self.parent = parent
    
    def on_profile_changed(self, profile_name):
        """Handle profile selection change with full synchronization"""
        # Skip if user selects custom manual option
        if profile_name == "Custom (Manual)":
            return
        
        # Get the selected profile data
        profiles = self.parent.controller.get_incubation_profiles()
        selected_profile = None
        for profile in profiles:
            if profile["name"] == profile_name:
                selected_profile = profile
                break
        
        if not selected_profile:
            return
            
        success = self.parent.controller.apply_profile(profile_name)
        if success:
            # Update input fields to match profile values
            self.parent.suhu_input.setText(str(selected_profile["temperature"]))
            self.parent.kelembaban_input.setText(str(selected_profile["humidity"]))
            
            # Update card vital targets immediately with profile values
            self.parent.update_vital_card_targets(
                selected_profile["temperature"], 
                selected_profile["humidity"]
            )
            
            # Use QTimer to ensure message appears on top after UI updates
            QTimer.singleShot(100, lambda: self.show_message("Info", f"Profil '{profile_name}' berhasil diterapkan!\nTarget: {selected_profile['temperature']}°C, {selected_profile['humidity']}%"))

    def apply_settings(self):
        """Apply temperature and humidity settings"""
        try:
            temp = float(self.parent.suhu_input.text())
            humidity = float(self.parent.kelembaban_input.text())
            
            # Validate ranges
            if not (30.0 <= temp <= 45.0):
                self.show_message("Error", "Suhu harus dalam rentang 30.0-45.0°C!")
                return
            
            if not (40.0 <= humidity <= 80.0):
                self.show_message("Error", "Kelembaban harus dalam rentang 40.0-80.0%!")
                return
                
            self.parent.controller.set_target_temperature(temp)
            self.parent.controller.set_target_humidity(humidity)
            
            # Update card vital targets immediately
            self.parent.update_vital_card_targets(temp, humidity)
            
            self.show_message("Sukses", "Pengaturan berhasil diterapkan!")
        except ValueError:
            self.show_message("Error", "Mohon masukkan nilai yang valid!")

    def toggle_device(self, device):
        """Toggle device on/off with real-time status update"""
        result = self.parent.controller.toggle_device(device)
        
        # Get current device status to determine actual state
        device_status = self.parent.controller.data_manager.get_device_status()
        
        # Determine actual status message based on real device state
        if device == "pemanas":
            is_active = device_status.get("pemanas", {}).get("active", False)
            status = "diaktifkan" if is_active else "dinonaktifkan"
        elif device == "humidifier":
            is_active = device_status.get("humidifier", {}).get("active", False)
            status = "diaktifkan" if is_active else "dinonaktifkan"
        else:
            # For other devices, use the toggle result
            status = "diaktifkan" if result else "dinonaktifkan"
        
        # Immediately update device status display for better UX
        self.parent.update_device_status_display(device_status)
        
        self.show_message("Info", f"{device.capitalize()} berhasil {status}!")

    def validate_temperature_input(self, text):
        """Validate temperature input"""
        try:
            value = float(text)
            if not (20.0 <= value <= 50.0):
                self.parent.suhu_input.setStyleSheet("border: 2px solid red;")
            else:
                self.parent.suhu_input.setStyleSheet("")
        except ValueError:
            if text:  # Only show error if there's text
                self.parent.suhu_input.setStyleSheet("border: 2px solid red;")

    def validate_humidity_input(self, text):
        """Validate humidity input"""
        try:
            value = float(text)
            if not (60.0 <= value <= 80.0):
                self.parent.kelembaban_input.setStyleSheet("border: 2px solid red;")
            else:
                self.parent.kelembaban_input.setStyleSheet("")
        except ValueError:
            if text:
                self.parent.kelembaban_input.setStyleSheet("border: 2px solid red;")
    
    def on_manual_setpoint_change(self, text):
        """Handle real-time manual setpoint changes"""
        try:
            # Get current values from both inputs
            temp_text = self.parent.suhu_input.text()
            humidity_text = self.parent.kelembaban_input.text()
            
            # Only update if both values are valid
            if temp_text and humidity_text:
                temp = float(temp_text)
                humidity = float(humidity_text)
                
                # Validate ranges
                if (30.0 <= temp <= 45.0) and (40.0 <= humidity <= 80.0):
                    # Update card vital targets in real-time (preview mode)
                    self.parent.temp_target_label.setText(f"Target: {temp}°C")
                    self.parent.humidity_target_label.setText(f"Target: {humidity}%")
                    
                    # Check if current values match any profile
                    self.update_profile_indicator(temp, humidity)
                    
        except ValueError:
            # If invalid input, revert to last known good values
            target_data = self.parent.controller.data_manager.get_target_values()
            self.parent.temp_target_label.setText(f"Target: {target_data['temperature']}°C")
            self.parent.humidity_target_label.setText(f"Target: {target_data['humidity']}%")

    def update_profile_indicator(self, temp, humidity):
        """Update profile combo to show if current settings match any profile"""
        profiles = self.parent.controller.get_incubation_profiles()
        
        # Check if current values match any profile
        matching_profile = None
        for profile in profiles:
            if (abs(profile["temperature"] - temp) < 0.1 and 
                abs(profile["humidity"] - humidity) < 0.1):
                matching_profile = profile["name"]
                break
        
        # Temporarily disconnect signal to avoid recursion
        self.parent.profil_combo.currentTextChanged.disconnect()
        
        if matching_profile:
            # Remove custom option if it exists
            self.remove_custom_profile_option()
            
            # Set combo to matching profile
            index = self.parent.profil_combo.findText(matching_profile)
            if index >= 0:
                self.parent.profil_combo.setCurrentIndex(index)
        else:
            # Add or select "Custom" option
            self.add_custom_profile_option()
        
        # Reconnect signal
        self.parent.profil_combo.currentTextChanged.connect(self.on_profile_changed)
    
    def add_custom_profile_option(self):
        """Add custom profile option to combo if it doesn't exist"""
        custom_text = "Custom (Manual)"
        custom_index = self.parent.profil_combo.findText(custom_text)
        
        if custom_index == -1:
            # Add custom option at the end
            self.parent.profil_combo.addItem(custom_text)
        
        # Select the custom option
        custom_index = self.parent.profil_combo.findText(custom_text)
        if custom_index >= 0:
            self.parent.profil_combo.setCurrentIndex(custom_index)
    
    def remove_custom_profile_option(self):
        """Remove custom profile option from combo"""
        custom_text = "Custom (Manual)"
        custom_index = self.parent.profil_combo.findText(custom_text)
        
        if custom_index >= 0:
            self.parent.profil_combo.removeItem(custom_index)

    def attempt_mqtt_connection(self):
        """Attempt MQTT connection with credential validation"""
        username = self.parent.user_input.text()
        password = self.parent.pass_input.text()
        
        if not username or not password:
            self.show_message("Error", "Username dan password tidak boleh kosong!")
            return
        
        # Validate credentials (hardcoded for security)
        valid_username = "kartel"
        valid_password = "kartel123"
        
        if username != valid_username or password != valid_password:
            self.show_message("Error", f"Username atau password salah!\nGunakan: username='{valid_username}', password='{valid_password}'")
            return
        
        self.parent.connect_btn.setText("Menghubungkan...")
        self.parent.connect_btn.setEnabled(False)
        
        # Attempt connection with validated credentials
        success = self.parent.controller.simulate_mqtt_connection(username, password)
        
        if success:
            self.show_message("Sukses", "Berhasil terhubung ke broker MQTT!")
        else:
            self.show_message("Error", "Gagal terhubung ke broker MQTT!")
        
        self.parent.connect_btn.setText("Hubungkan Ke Broker")
        self.parent.connect_btn.setEnabled(True)

    def reset_mqtt_settings(self):
        """Putuskan koneksi MQTT dengan broker dan reset settings"""
        # Putuskan koneksi MQTT
        if hasattr(self.parent.controller, 'data_manager'):
            if self.parent.controller.data_manager.is_connected:
                self.parent.controller.data_manager.disconnect()
                print("✅ MQTT disconnected - Auto reconnect disabled")
            else:
                # Set flag untuk mencegah auto reconnect
                self.parent.controller.data_manager.user_disconnected = True
        
        # Kosongkan input field
        self.parent.user_input.clear()
        self.parent.pass_input.clear()
        
        # Update status koneksi pada UI
        if hasattr(self.parent, 'status_connect_btn'):
            self.parent.status_connect_btn.setText(" Tidak Terhubung")
            self.parent.status_connect_btn.setObjectName("statusNotConnected")
            self.parent.set_stylesheet()  # Refresh stylesheet
    
    def show_message(self, title, message):
        """Show message box with proper parent and focus"""
        msg = QMessageBox(self.parent)  # Set proper parent
        msg.setWindowTitle(title)
        msg.setText(message)
        
        # Ensure the message box appears on top
        msg.setWindowFlags(msg.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        msg.raise_()  # Bring to front
        msg.activateWindow()  # Activate window
        
        # Make sure parent window is active before showing dialog
        self.parent.raise_()
        self.parent.activateWindow()
        
        msg.exec()