from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtCore import Qt, QTimer


class DashboardEventHandlers:
    """Berisi semua metode penanganan event"""
    
    def __init__(self, parent):
        self.parent = parent
    
    def on_profile_changed(self, profile_name):
        """Tangani perubahan pemilihan profil dengan sinkronisasi penuh"""
        # Lewati ketika user memilih "Custom (Manual)"
        if profile_name == "Custom (Manual)":
            return
        
        # memilih profil dan memperbarui setelan
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
            # perbarui input form dari profil yang dipilih
            self.parent.suhu_input.setText(str(selected_profile["temperature"]))
            # Field input kelembaban telah dihapus dihapus
            
            # Perbarui target kartu vital segera dengan nilai profil (gunakan kelembaban default)lt)
            default_humidity = 60.0  # Kelembaban default untuk semua profil
            self.parent.update_vital_card_targets(
                selected_profile["temperature"], 
                default_humidity
            )
            
            # Gunakan QTimer untuk memastikan pesan muncul di atas setelah UI diperbarui
            QTimer.singleShot(100, lambda: self.show_message("Info", f"Profil '{profile_name}' berhasil diterapkan!\nTarget Suhu: {selected_profile['temperature']}°C"))

    def apply_settings(self):
        """Terapkan pengaturan suhu (kelembaban dihapus dari UI)"""
        try:
            temp = float(self.parent.suhu_input.text())
            
            # Validasi rentang untuk suhu
            if not (30.0 <= temp <= 45.0):
                self.show_message("Error", "Suhu harus dalam rentang 30.0-45.0°C!")
                return
                
            self.parent.controller.set_target_temperature(temp)
            
            # Perbarui target kartu vital 
            default_humidity = 60.0  # Nilai kelembaban default
            self.parent.update_vital_card_targets(temp, default_humidity)
            
            self.show_message("Sukses", "Pengaturan suhu berhasil diterapkan!")
        except ValueError:
            self.show_message("Error", "Mohon masukkan nilai suhu yang valid!")

    def validate_temperature_input(self, text):
        """Validasi input suhu"""
        try:
            value = float(text)
            if not (20.0 <= value <= 50.0):
                self.parent.suhu_input.setStyleSheet("border: 2px solid red;")
            else:
                self.parent.suhu_input.setStyleSheet("")
        except ValueError:
            if text:  # Hanya tampilkan error jika ada teks
                self.parent.suhu_input.setStyleSheet("border: 2px solid red;")
    
    def on_manual_setpoint_change(self, text):
        """Tangani perubahan setpoint manual secara real-time (suhu saja)"""
        try:
            # Dapatkan nilai suhu saat ini
            temp_text = self.parent.suhu_input.text()
            
            # Hanya perbarui jika nilai suhu valid
            if temp_text:
                temp = float(temp_text)
                
                # Validasi rentang suhu
                if (30.0 <= temp <= 45.0):
                    # Perbarui target suhu secara real-time
                    self.parent.temp_target_label.setText(f"Target: {temp}°C")
                    
                    # Periksa apakah suhu saat ini cocok dengan profil 
                    default_humidity = 60.0  # Kelembaban default untuk pencocokan profil
                    self.update_profile_indicator(temp, default_humidity)
                    
        except ValueError:
            # Jika input tidak valid, kembalikan ke nilai suhu terakhir yang diketahui baik
            target_data = self.parent.controller.data_manager.get_target_values()
            self.parent.temp_target_label.setText(f"Target: {target_data['temperature']}°C")

    def update_profile_indicator(self, temp, humidity):
        """Perbarui combo profil untuk menampilkan apakah suhu saat ini cocok dengan profil apa pun"""
        profiles = self.parent.controller.get_incubation_profiles()
        
        # Periksa apakah suhu saat ini cocok dengan profil
        matching_profile = None
        for profile in profiles:
            if abs(profile["temperature"] - temp) < 0.1:
                matching_profile = profile["name"]
                break
        
        # Putuskan sinyal sementara untuk menghindari rekursi
        self.parent.profil_combo.currentTextChanged.disconnect()
        
        if matching_profile:
            # Hapus opsi kustom jika ada
            self.remove_custom_profile_option()
            
            # Atur combo ke profil yang cocok
            index = self.parent.profil_combo.findText(matching_profile)
            if index >= 0:
                self.parent.profil_combo.setCurrentIndex(index)
        else:
            # Tambahkan atau pilih opsi "Custom"
            self.add_custom_profile_option()
        
        # Hubungkan kembali sinyal
        self.parent.profil_combo.currentTextChanged.connect(self.on_profile_changed)
    
    def add_custom_profile_option(self):
        """Tambahkan opsi profil kustom ke combo jika belum ada"""
        custom_text = "Custom (Manual)"
        custom_index = self.parent.profil_combo.findText(custom_text)
        
        if custom_index == -1:
            # Tambahkan opsi kustom di akhir
            self.parent.profil_combo.addItem(custom_text)
        
        # Pilih opsi kustom
        custom_index = self.parent.profil_combo.findText(custom_text)
        if custom_index >= 0:
            self.parent.profil_combo.setCurrentIndex(custom_index)
    
    def remove_custom_profile_option(self):
        """Hapus opsi profil kustom dari combo"""
        custom_text = "Custom (Manual)"
        custom_index = self.parent.profil_combo.findText(custom_text)
        
        if custom_index >= 0:
            self.parent.profil_combo.removeItem(custom_index)

    def attempt_mqtt_connection(self):
        """Coba koneksi MQTT dengan validasi kredensial"""
        username = self.parent.user_input.text()
        password = self.parent.pass_input.text()
        
        if not username or not password:
            self.show_message("Error", "Username dan password tidak boleh kosong!")
            return
        
        # Validasi kredensial
        valid_username = "kartel"
        valid_password = "kartel123"
        
        if username != valid_username or password != valid_password:
            self.show_message("Error", f"Username atau password salah!\nGunakan: username='{valid_username}', password='{valid_password}'")
            return
        
        self.parent.connect_btn.setText("Menghubungkan...")
        self.parent.connect_btn.setEnabled(False)
        
        # Coba koneksi dengan kredensial yang tervalidasi
        success = self.parent.controller.simulate_mqtt_connection(username, password)
        
        if success:
            self.show_message("Sukses", "Berhasil terhubung ke broker MQTT!")
        else:
            self.show_message("Error", "Gagal terhubung ke broker MQTT!")
        
        self.parent.connect_btn.setText("Hubungkan Ke Broker")
        self.parent.connect_btn.setEnabled(True)

    def reset_mqtt_settings(self):
        """Putuskan koneksi MQTT dengan broker dan reset pengaturan"""""
        # Putuskan koneksi MQTT
        if hasattr(self.parent.controller, 'data_manager'):
            if self.parent.controller.data_manager.is_connected:
                self.parent.controller.data_manager.disconnect()
                print("✅ MQTT disconnected - Auto reconnect disabled")
            else:
                # Atur flag untuk mencegah auto reconnect
                self.parent.controller.data_manager.user_disconnected = True
        
        # Kosongkan field input
        self.parent.user_input.clear()
        self.parent.pass_input.clear()
        
        # Perbarui status koneksi pada UI
        if hasattr(self.parent, 'status_connect_btn'):
            self.parent.status_connect_btn.setText(" Tidak Terhubung")
            self.parent.status_connect_btn.setObjectName("statusNotConnected")
            self.parent.set_stylesheet()  # Segarkan stylesheet
    
    def show_message(self, title, message):
        """Tampilkan kotak pesan dengan parent dan fokus yang tepat"""
        msg = QMessageBox(self.parent)
        msg.setWindowTitle(title)
        msg.setText(message)
        
        msg.setWindowFlags(msg.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        msg.raise_()  
        msg.activateWindow()          
        
        self.parent.raise_()
        self.parent.activateWindow()
        
        msg.exec()