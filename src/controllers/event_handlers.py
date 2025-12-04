from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtCore import Qt, QTimer

# Import dari struktur baru
from src.services.auth_service import AuthService
from src.config.settings import DEFAULT_SETTINGS

class DashboardEventHandlers:
    """
    Menangani interaksi UI (Klik tombol, Input teks, Perubahan Combo box).
    Bertindak sebagai jembatan antara View (UI) dan Logic (Controller Utama).
    """
    
    def __init__(self, main_window):
        # Kita namakan 'main_window' agar lebih jelas daripada 'parent'
        self.view = main_window
        
        # Shortcut ke logic controller (pastikan main_window punya atribut 'controller')
        # Jika belum ada, nanti kita pasang di main_window.py
        self.controller = main_window.controller 

    # =========================================================================
    # 1. PROFILE & SETTINGS HANDLERS
    # =========================================================================

    def on_profile_changed(self, profile_name):
        """Tangani perubahan pemilihan profil dengan sinkronisasi penuh"""
        print(f"🔄 Profile changed to: {profile_name}")
        
        if profile_name == "Custom (Manual)":
            print("⏭ Skipping Custom profile setup")
            return
        
        # Ambil list profil dari controller logika
        profiles = self.controller.get_incubation_profiles()
        selected_profile = next((p for p in profiles if p["name"] == profile_name), None)
        
        if not selected_profile:
            print(f"❌ Profile '{profile_name}' not found")
            return
        
        print(f"📋 Applying profile: {selected_profile}")
        
        # Putuskan sinyal sementara (mencegah loop)
        try:
            self.view.suhu_input.textChanged.disconnect()
        except TypeError: pass # Abaikan jika belum terkoneksi

        # Update UI Input Field
        self.view.suhu_input.setText(str(selected_profile["temperature"]))
        
        # Sambungkan sinyal kembali
        self.view.suhu_input.textChanged.connect(self.validate_temperature_input)
        self.view.suhu_input.textChanged.connect(self.on_manual_setpoint_change)
        
        # Terapkan profil ke sistem logika
        success = self.controller.apply_profile(profile_name)
        
        if success:
            self.view.temp_target_label.setText(f"Target: {selected_profile['temperature']}°C")
            
            # Tampilkan pesan sukses sedikit tertunda agar UI refresh dulu
            QTimer.singleShot(100, lambda: self.show_message(
                "Info", 
                f"Profil '{profile_name}' berhasil diterapkan!\nTarget Suhu: {selected_profile['temperature']}°C"
            ))
        else:
            print(f"❌ Failed to apply profile '{profile_name}'")
            # Restore nilai lama jika gagal
            target_data = self.controller.data_manager.get_target_values()
            self.view.suhu_input.setText(str(target_data["temperature"]))

    def apply_settings(self):
        """Terapkan pengaturan suhu manual dari tombol 'Terapkan'"""
        print("🔧 Applying manual temperature settings...")
        try:
            temp_text = self.view.suhu_input.text()
            if not temp_text: return
            
            temp = float(temp_text)
            
            # Validasi input range
            if not (30.0 <= temp <= 45.0):
                self.show_message("Error", "Suhu harus dalam rentang 30.0 - 45.0°C!")
                return
                
            success = self.controller.set_target_temperature(temp)
            
            if success:
                self.view.temp_target_label.setText(f"Target: {temp}°C")
                
                # Cek apakah jadi Custom atau sesuai profil
                default_humidity = DEFAULT_SETTINGS['target_humidity']
                self.update_profile_indicator(temp, default_humidity)
                
                self.show_message("Sukses", f"Pengaturan suhu berhasil diterapkan!\nTarget: {temp}°C")
            else:
                self.show_message("Error", "Gagal menerapkan pengaturan suhu!")
                
        except ValueError:
            self.show_message("Error", "Mohon masukkan nilai suhu yang valid (angka)!")

    def validate_temperature_input(self, text):
        """Visual feedback (Border Merah/Normal) saat mengetik"""
        if not text.strip():
            self.view.suhu_input.setStyleSheet("")
            return

        try:
            value = float(text)
            if not (20.0 <= value <= 50.0):
                self.view.suhu_input.setStyleSheet("border: 2px solid red;")
            else:
                self.view.suhu_input.setStyleSheet("")
        except ValueError:
            self.view.suhu_input.setStyleSheet("border: 2px solid red;")

    def on_manual_setpoint_change(self, text):
        """Real-time update logic saat user mengetik suhu"""
        try:
            if not text.strip(): return
            
            temp = float(text)
            if (30.0 <= temp <= 45.0):
                # Update Label Target Real-time
                self.view.temp_target_label.setText(f"Target: {temp}°C")
                
                # Cek Profile Match
                default_humidity = DEFAULT_SETTINGS['target_humidity']
                self.update_profile_indicator(temp, default_humidity)
        except ValueError:
            pass # Jangan lakukan apa-apa jika input belum valid

    # =========================================================================
    # 2. HELPER PROFILE MATCHING
    # =========================================================================

    def update_profile_indicator(self, temp, humidity):
        """Cek apakah settingan saat ini cocok dengan salah satu profil"""
        profiles = self.controller.get_incubation_profiles()
        
        matching_profile = None
        for profile in profiles:
            # Toleransi perbedaan 0.1 derajat
            if abs(profile["temperature"] - temp) < 0.1:
                matching_profile = profile["name"]
                break
        
        # Mencegah trigger signal loop saat mengubah combobox secara programatik
        try:
            self.view.profil_combo.currentTextChanged.disconnect()
        except TypeError: pass

        if matching_profile:
            self.remove_custom_profile_option()
            index = self.view.profil_combo.findText(matching_profile)
            if index >= 0:
                self.view.profil_combo.setCurrentIndex(index)
        else:
            self.add_custom_profile_option()
        
        # Sambungkan lagi
        self.view.profil_combo.currentTextChanged.connect(self.on_profile_changed)

    def add_custom_profile_option(self):
        custom_text = "Custom (Manual)"
        if self.view.profil_combo.findText(custom_text) == -1:
            self.view.profil_combo.addItem(custom_text)
        
        index = self.view.profil_combo.findText(custom_text)
        if index >= 0:
            self.view.profil_combo.setCurrentIndex(index)

    def remove_custom_profile_option(self):
        custom_text = "Custom (Manual)"
        index = self.view.profil_combo.findText(custom_text)
        if index >= 0:
            self.view.profil_combo.removeItem(index)

    # =========================================================================
    # 3. AUTH & MQTT CONNECTION HANDLERS
    # =========================================================================

    def attempt_mqtt_connection(self):
        """Handle tombol Connect"""
        username = self.view.user_input.text().strip()
        password = self.view.pass_input.text().strip()
        remember_me = self.view.remember_checkbox.isChecked()
        
        if not username or not password:
            self.show_message("Error", "Username dan password tidak boleh kosong!")
            return
        
        # Validasi sederhana (sebaiknya ini dipindah ke AuthService atau Controller logic nanti)
        # Untuk sekarang kita biarkan di sini agar logic tidak terlalu banyak berubah
        valid_u = "kartel"
        valid_p = "kartel123"
        
        if username != valid_u or password != valid_p:
            self.show_message("Error", "Username atau password salah!")
            return
        
        # Update UI State
        self.view.connect_btn.setText("Menghubungkan...")
        self.view.connect_btn.setEnabled(False)
        
        # Panggil logic koneksi di Controller Utama
        success = self.controller.simulate_mqtt_connection(username, password)
        
        if success:
            if remember_me:
                # MENGGUNAKAN SERVICE BARU
                AuthService.save_credentials(username, password)
            else:
                # Jika user uncheck remember me, hapus kredensial lama jika ada
                AuthService.clear_credentials()
                
            self.show_message("Sukses", "Berhasil terhubung ke broker MQTT!")
        else:
            self.show_message("Error", "Gagal terhubung ke broker MQTT!")
        
        self.view.connect_btn.setText("Hubungkan Ke Broker")
        self.view.connect_btn.setEnabled(True)

    def reset_mqtt_settings(self):
        """Handle tombol Disconnect / Reset"""
        try:
            # Panggil disconnect logic di controller
            if self.controller.data_manager.is_connected:
                self.controller.data_manager.disconnect()
            
            # Set flag agar tidak auto-reconnect
            self.controller.data_manager.user_disconnected = True
            
        except Exception as e:
            print(f"⚠ Error during MQTT disconnect: {e}")
        
        # Bersihkan UI
        self.view.user_input.clear()
        self.view.pass_input.clear()
        self.view.remember_checkbox.setChecked(False)
        
        # Hapus kredensial tersimpan (MENGGUNAKAN SERVICE BARU)
        AuthService.clear_credentials()
        
        # Update UI Indicator
        if hasattr(self.view, 'status_connect_btn'):
            self.view.status_connect_btn.setText(" Tidak Terhubung")
            self.view.status_connect_btn.setObjectName("statusNotConnected")
            # Refresh style
            self.view.setStyleSheet(self.view.styleSheet()) 

    # =========================================================================
    # 4. UTILITIES
    # =========================================================================

    def show_message(self, title, message):
        """Helper menampilkan pop-up message"""
        msg = QMessageBox(self.view)
        msg.setWindowTitle(title)
        msg.setText(message)
        
        # Pastikan pop-up selalu di atas (TopMost)
        msg.setWindowFlags(msg.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        msg.raise_()
        msg.activateWindow()
        
        self.view.raise_()
        self.view.activateWindow()
        
        msg.exec()