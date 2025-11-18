# KARTEL - Kendali Automasi Ruangan Telur
## Dashboard Monitoring Penetas Telur

### 📋 Deskripsi
KARTEL adalah sistem monitoring dashboard untuk penetas telur otomatis yang menggunakan PyQt5 untuk tampilan GUI yang modern dan responsif. Dashboard ini menyediakan:

- **Panel Header**: Logo dan status koneksi MQTT + counter hari inkubasi
- **Card Vital**: Monitoring suhu dan kelembaban real-time
- **Status System**: Status pemanas, humidifier, motor pembalik, dan timer
- **Grafik Tren**: Visualisasi data 24 jam terakhir
- **Panel Konfigurasi**: Pengaturan profil, setpoint, kontrol manual, dan MQTT

### 🎨 Fitur Desain
- **Modern UI**: Sesuai dengan mockup yang diberikan
- **Gradient Cards**: Card suhu (orange) dan kelembaban (purple)
- **Icon SVG**: Menggunakan icon kustom dari folder `asset/svg/`
- **Font Manrope**: Typography yang clean dan modern
- **Responsive Layout**: Adaptif dengan berbagai ukuran layar

### 🚀 Cara Menjalankan

#### 1. Persyaratan Sistem
- Python 3.7 atau lebih baru
- Windows 10/11 (tested)
- Koneksi internet untuk instalasi package

#### 2. Instalasi Otomatis
```bash
# Jalankan setup batch file
setup.bat
```

#### 3. Instalasi Manual
```bash
# Install dependencies
pip install PyQt5 PyQtGraph numpy paho-mqtt

# Buat direktori yang diperlukan
mkdir data logs fonts

# Jalankan dashboard
python dashboard-gui.py
```

#### 4. Menggunakan Launcher
```bash
python run_kartel.py
```

### 📁 Struktur Project
```
KARTEL/
├── dashboard-gui.py          # Main dashboard application
├── kartel_icons.py          # Icon management system
├── kartel_mqtt.py           # MQTT communication handler
├── kartel_data.py           # Data logging and session management
├── kartel_fonts.py          # Font management
├── run_kartel.py            # Application launcher
├── requirements.txt         # Python dependencies
├── setup.bat                # Windows setup script
├── config/
│   └── kartel_config.json   # Configuration settings
├── styles/
│   └── kartel_styles.qss    # Qt stylesheet
├── asset/
│   └── svg/                 # SVG icons
│       ├── temperature.svg
│       ├── humidity.svg
│       ├── humidifier.svg
│       ├── pemanas.svg
│       ├── settings.svg
│       ├── wifi.svg
│       ├── calendar.svg
│       ├── graph.svg
│       └── ...
├── data/                    # SQLite database
└── logs/                    # Application logs
```

### 🔧 Konfigurasi

#### MQTT Settings
Ubah pengaturan MQTT di `config/kartel_config.json`:
```json
{
  "mqtt": {
    "broker": "localhost",
    "port": 1883,
    "username": "kartel_esp32",
    "password": "KartelTest123"
  }
}
```

#### Profil Inkubasi
Dashboard mendukung beberapa profil telur:
- **Ayam**: 38°C, 60%, 21 hari
- **Bebek**: 37.5°C, 65%, 28 hari
- **Puyuh**: 37.8°C, 58%, 17 hari
- **Angsa**: 37.4°C, 62%, 30 hari

### 📊 Fitur Dashboard

#### 1. Panel Header
- Logo KARTEL dengan gradient orange
- Status koneksi MQTT (merah/hijau)
- Counter hari inkubasi (hari ke-X dari 21)

#### 2. Card Vital
- **Card Suhu** (gradient orange): Suhu saat ini + target
- **Card Kelembaban** (gradient purple): Kelembaban saat ini + target
- Update real-time dari sensor ESP32

#### 3. Status System
- **Pemanas**: Status aktif/non-aktif (hijau/merah)
- **Humidifier**: Status aktif/non-aktif (hijau/merah)
- **Motor Pembalik**: Status menunggu (kuning)
- **Timer**: Countdown putaran berikutnya

#### 4. Grafik Tren
- Grafik garis untuk suhu (orange) dan kelembaban (purple)
- Data 24 jam terakhir
- Update real-time setiap 5 detik

#### 5. Panel Konfigurasi
- **Profil Inkubasi**: Dropdown preset untuk jenis telur
- **Pengaturan Setpoint**: Input manual suhu dan kelembaban
- **Kontrol Manual**: Toggle pemanas dan humidifier
- **Koneksi MQTT**: Username, password, dan tombol connect

### 🔗 Integrasi ESP32

Dashboard ini dirancang untuk berintegrasi dengan ESP32 melalui MQTT. Format data yang diharapkan:

#### Topic: `kartel/sensor/data`
```json
{
  "temperature": 37.5,
  "humidity": 62.3,
  "device_id": "ESP32_KARTEL_01",
  "heater_active": true,
  "humidifier_active": false,
  "motor_status": "idle"
}
```

#### Topic: `kartel/control/heater`
```json
{
  "action": "on", // atau "off"
  "timestamp": "2025-11-17T10:30:00"
}
```

### 🎯 Penggunaan

1. **Startup**: Jalankan dashboard dengan `python dashboard-gui.py`
2. **Koneksi**: Masukkan username/password MQTT dan klik "Hubungkan Ke Broker"
3. **Profil**: Pilih jenis telur dari dropdown "Profil Inkubasi"
4. **Monitoring**: Pantau suhu/kelembaban dan grafik tren
5. **Kontrol**: Gunakan toggle manual untuk pemanas/humidifier jika diperlukan

### 🛠 Troubleshooting

#### Error: "ModuleNotFoundError: No module named 'PyQt5'"
```bash
pip install PyQt5
```

#### Error: "cannot import name 'QAction'"
Pastikan menggunakan PyQt5 versi terbaru:
```bash
pip install --upgrade PyQt5
```

#### Dashboard tidak menampilkan icon
Pastikan folder `asset/svg/` berisi file SVG yang diperlukan.

#### MQTT tidak terkoneksi
1. Periksa broker MQTT berjalan di localhost:1883
2. Verifikasi username/password di konfigurasi
3. Cek firewall tidak memblokir port 1883

### 📝 Changelog

#### v1.0.0 (2025-11-17)
- ✅ Dashboard layout sesuai mockup
- ✅ Card vital dengan gradient
- ✅ Status system dengan icon
- ✅ Grafik tren real-time
- ✅ Panel konfigurasi lengkap
- ✅ MQTT integration
- ✅ SQLite data logging
- ✅ Profil inkubasi preset

### 👥 Kontributor
- **KARTEL Team** - Initial development

### 📄 Lisensi
MIT License - Silakan gunakan dan modifikasi sesuai kebutuhan.

---
*KARTEL - Kendali Automasi Ruangan Telur © 2025*