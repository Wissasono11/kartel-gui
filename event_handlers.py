from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtCore import Qt, QTimer
from config import save_user_credentials, clear_user_credentials


class DashboardEventHandlers:
    """Berisi semua metode penanganan event"""
    
    def __init__(self, parent):
        self.parent = parent
    
    def on_profile_changed(self, profile_name):
        """Tangani perubahan pemilihan profil dengan sinkronisasi penuh"""
        print(f"🔄 Profile changed to: {profile_name}")
        
        # Lewati ketika user memilih "Custom (Manual)"
        if profile_name == "Custom (Manual)":
            print("⏭ Skipping Custom profile")
            return
        
        # memilih profil dan memperbarui setelan
        profiles = self.parent.controller.get_incubation_profiles()
        selected_profile = None
        for profile in profiles:
            if profile["name"] == profile_name:
                selected_profile = profile
                break
        
        if not selected_profile:
            print(f"❌ Profile '{profile_name}' not found")
            return
        
        print(f"📋 Applying profile: {selected_profile}")
        
        # Putuskan sinyal sementara untuk menghindari rekursi saat update input field
        self.parent.suhu_input.textChanged.disconnect()
        
        # perbarui input form dari profil yang dipilih SEBELUM apply_profile
        old_temp = self.parent.suhu_input.text()
        self.parent.suhu_input.setText(str(selected_profile["temperature"]))
        print(f"🌡 Temperature input updated: {old_temp} -> {selected_profile['temperature']}°C")
        
        # Hubungkan kembali sinyal setelah update
        self.parent.suhu_input.textChanged.connect(self.validate_temperature_input)
        self.parent.suhu_input.textChanged.connect(self.on_manual_setpoint_change)
        
        # Terapkan profil ke controller
        success = self.parent.controller.apply_profile(profile_name)
        if success:
            # Update target label secara langsung untuk memastikan sinkronisasi
            self.parent.temp_target_label.setText(f"Target: {selected_profile['temperature']}°C")
            print(f"✅ Profile '{profile_name}' applied successfully")
            
            # Target card akan diupdate otomatis melalui apply_profile dan controller emit
            # Tidak perlu manual update_vital_card_targets lagi
            
            # Gunakan QTimer untuk memastikan pesan muncul di atas setelah UI diperbarui
            QTimer.singleShot(100, lambda: self.show_message("Info", f"Profil '{profile_name}' berhasil diterapkan!\nTarget Suhu: {selected_profile['temperature']}°C"))
        else:
            print(f"❌ Failed to apply profile '{profile_name}'")
            # Jika gagal, kembalikan field input ke nilai sebelumnya
            target_data = self.parent.controller.data_manager.get_target_values()
            self.parent.suhu_input.setText(str(target_data["temperature"]))

    def apply_settings(self):
        """Terapkan pengaturan suhu (kelembaban dihapus dari UI)"""
        print("🔧 Applying manual temperature settings...")
        try:
            temp = float(self.parent.suhu_input.text())
            print(f"🌡 Temperature value: {temp}°C")
            
            # Validasi rentang untuk suhu
            if not (30.0 <= temp <= 45.0):
                self.show_message("Error", "Suhu harus dalam rentang 30.0-45.0°C!")
                return
                
            success = self.parent.controller.set_target_temperature(temp)
            
            if success:
                print(f"✅ Temperature setting applied: {temp}°C")
                
                # Update target label secara langsung
                self.parent.temp_target_label.setText(f"Target: {temp}°C")
                
                # Update profile indicator untuk menunjukkan Custom jika tidak cocok dengan profil
                default_humidity = 60.0
                self.update_profile_indicator(temp, default_humidity)
                
                # Target card akan diupdate otomatis melalui controller emit
                # Tidak perlu manual update_vital_card_targets lagi
                
                self.show_message("Sukses", f"Pengaturan suhu berhasil diterapkan!\nTarget: {temp}°C")
            else:
                print("❌ Failed to apply temperature setting")
                self.show_message("Error", "Gagal menerapkan pengaturan suhu!")
                
        except ValueError:
            print("❌ Invalid temperature input")
            self.show_message("Error", "Mohon masukkan nilai suhu yang valid!")

    def validate_temperature_input(self, text):
        """Validasi input suhu"""
        try:
            if text.strip():  # Hanya validasi jika ada teks
                value = float(text)
                if not (20.0 <= value <= 50.0):
                    self.parent.suhu_input.setStyleSheet("border: 2px solid red;")
                    print(f"⚠ Temperature out of range: {value}°C (allowed: 20-50°C)")
                else:
                    self.parent.suhu_input.setStyleSheet("")
                    print(f"✅ Temperature input valid: {value}°C")
            else:
                self.parent.suhu_input.setStyleSheet("")
        except ValueError:
            if text.strip():  # Hanya tampilkan error jika ada teks yang tidak kosong
                self.parent.suhu_input.setStyleSheet("border: 2px solid red;")
                print(f"❌ Invalid temperature format: '{text}'")
    
    def on_manual_setpoint_change(self, text):
        """Tangani perubahan setpoint manual secara real-time (suhu saja)"""
        try:
            # Dapatkan nilai suhu saat ini
            temp_text = self.parent.suhu_input.text().strip()
            
            # Hanya perbarui jika nilai suhu valid dan tidak kosong
            if temp_text:
                temp = float(temp_text)
                
                # Validasi rentang suhu
                if (30.0 <= temp <= 45.0):
                    # Perbarui target suhu secara real-time
                    self.parent.temp_target_label.setText(f"Target: {temp}°C")
                    print(f"🎯 Target temperature updated to: {temp}°C")
                    
                    # Periksa apakah suhu saat ini cocok dengan profil 
                    default_humidity = 60.0  # Kelembaban default untuk pencocokan profil
                    self.update_profile_indicator(temp, default_humidity)
                else:
                    print(f"⚠ Temperature {temp}°C is out of valid range (30-45°C)")
                    
        except ValueError:
            # Jika input tidak valid, kembalikan ke nilai suhu terakhir yang diketahui baik
            print(f"❌ Invalid temperature input: '{text}'")
            try:
                target_data = self.parent.controller.data_manager.get_target_values()
                self.parent.temp_target_label.setText(f"Target: {target_data['temperature']}°C")
            except Exception as e:
                print(f"⚠ Error restoring target temperature: {e}")
                # Fallback ke default
                self.parent.temp_target_label.setText("Target: 37°C")

    def update_profile_indicator(self, temp, humidity):
        """Perbarui combo profil untuk menampilkan apakah suhu saat ini cocok dengan profil apa pun"""
        profiles = self.parent.controller.get_incubation_profiles()
        
        # Periksa apakah suhu saat ini cocok dengan profil
        matching_profile = None
        for profile in profiles:
            if abs(profile["temperature"] - temp) < 0.1:
                matching_profile = profile["name"]
                break
        
        print(f"🔍 Checking profile match for temp {temp}°C: {matching_profile or 'No match'}")
        
        # Putuskan sinyal sementara untuk menghindari rekursi
        try:
            self.parent.profil_combo.currentTextChanged.disconnect()
        except:
            pass  # Sinyal mungkin sudah terputus
        
        if matching_profile:
            # Hapus opsi kustom jika ada
            self.remove_custom_profile_option()
            
            # Atur combo ke profil yang cocok
            index = self.parent.profil_combo.findText(matching_profile)
            if index >= 0:
                self.parent.profil_combo.setCurrentIndex(index)
                print(f"✅ Profile combo set to: {matching_profile}")
        else:
            # Tambahkan atau pilih opsi "Custom"
            self.add_custom_profile_option()
            print("📝 Profile combo set to Custom (Manual)")
        
        # Hubungkan kembali sinyal
        self.parent.profil_combo.currentTextChanged.connect(self.on_profile_changed)
    
    def add_custom_profile_option(self):
        """Tambahkan opsi profil kustom ke combo jika belum ada"""
        custom_text = "Custom (Manual)"
        custom_index = self.parent.profil_combo.findText(custom_text)
        
        if custom_index == -1:
            # Tambahkan opsi kustom di akhir
            self.parent.profil_combo.addItem(custom_text)
            print(f"➕ Added custom profile option")
        
        # Pilih opsi kustom
        custom_index = self.parent.profil_combo.findText(custom_text)
        if custom_index >= 0:
            self.parent.profil_combo.setCurrentIndex(custom_index)
            print(f"✅ Selected custom profile option")
    
    def remove_custom_profile_option(self):
        """Hapus opsi profil kustom dari combo"""
        custom_text = "Custom (Manual)"
        custom_index = self.parent.profil_combo.findText(custom_text)
        
        if custom_index >= 0:
            self.parent.profil_combo.removeItem(custom_index)
            print(f"➖ Removed custom profile option")

    def attempt_mqtt_connection(self):
        """Coba koneksi MQTT dengan validasi kredensial"""
        username = self.parent.user_input.text().strip()
        password = self.parent.pass_input.text().strip()
        remember_me = self.parent.remember_checkbox.isChecked()
        
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
            # Simpan kredensial jika user mencentang remember me
            if remember_me:
                save_result = save_user_credentials(username, password)
                if save_result:
                    print(f"💾 Credentials saved for future use")
                else:
                    print(f"⚠ Failed to save credentials")
            
            self.show_message("Sukses", "Berhasil terhubung ke broker MQTT!")
        else:
            self.show_message("Error", "Gagal terhubung ke broker MQTT!")
        
        self.parent.connect_btn.setText("Hubungkan Ke Broker")
        self.parent.connect_btn.setEnabled(True)

    def reset_mqtt_settings(self):
        """Putuskan koneksi MQTT dengan broker dan reset pengaturan"""
        try:
            # Putuskan koneksi MQTT
            if hasattr(self.parent.controller, 'data_manager'):
                if self.parent.controller.data_manager.is_connected:
                    self.parent.controller.data_manager.disconnect()
                    print("✅ MQTT disconnected safely - Auto reconnect disabled")
                else:
                    # Atur flag untuk mencegah auto reconnect
                    self.parent.controller.data_manager.user_disconnected = True
                    print("✅ Auto reconnect disabled")
        except Exception as e:
            print(f"⚠ Error during MQTT disconnect: {e}")
        
        # Kosongkan field input
        self.parent.user_input.clear()
        self.parent.pass_input.clear()
        self.parent.remember_checkbox.setChecked(False)
        
        # Hapus kredensial yang tersimpan
        clear_result = clear_user_credentials()
        if clear_result:
            print(f"🗏 Saved credentials cleared")
        
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