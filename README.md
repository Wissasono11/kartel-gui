# 🥚 KARTEL - Dashboard Monitoring Inkubator Telur

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![PyQt6](https://img.shields.io/badge/GUI-PyQt6-green.svg)](https://pypi.org/project/PyQt6/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Dashboard modern untuk monitoring dan kontrol inkubator telur dengan interface PyQt6 yang elegan.

## ✨ Fitur Utama

- 📊 **Real-time Monitoring** - Grafik suhu & kelembaban live
- 🎮 **Kontrol Otomatis** - Auto pemanas & humidifier  
- 📱 **UI Modern** - Interface dengan SVG icons & gradients
- 🔄 **Data Simulation** - Dummy data untuk testing
- 📈 **Grafik Interaktif** - Tooltip dan zoom support
- ⚡ **Status Real-time** - WiFi connection indicator

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Jalankan Dashboard
```bash
# Dashboard lengkap dengan fitur real-time:
python kartel_dashboard.py

# Dashboard static untuk preview:
python dashboard-gui.py
```

### 3. File Structure
```
📁 KARTEL/
├── 📄 kartel_dashboard.py    # Main app (RECOMMENDED)
├── 📄 kartel_data.py            # Data simulation
├── 📄 kartel_controller.py      # Logic controller
├── 📁 asset/
│   ├── 📁 svg/                  # Custom icons
│   └── 📁 style/styles.qss      # Styling
└── 📄 requirements.txt
```

## 🎯 Dependencies
```
PyQt6>=6.4.0
PyQtGraph>=0.13.0
qtawesome>=1.2.0
```

## ⚙️ Konfigurasi

### Dummy Data Settings
```python
# Edit di kartel_data.py:
TEMP_RANGE = (37.0, 38.0)      # Target suhu (°C)
HUMIDITY_RANGE = (55, 65)       # Target kelembaban (%)
UPDATE_INTERVAL = 3000          # Update setiap 3 detik
```

### Profil Inkubasi
- 🐣 **Ayam**: 21 hari, 37.5°C, 60% RH
- 🦆 **Bebek**: 28 hari, 37.2°C, 58% RH
- 🦢 **Angsa**: 30 hari, 37.4°C, 62% RH

## 🔧 Troubleshooting

### Error Font Loading
```bash
# Install font Manrope (opsional):
# Download dari Google Fonts dan install di system
```

### Error SVG Icons
```bash
# Pastikan folder asset/svg/ ada dan berisi icons
ls asset/svg/  # Harus ada wifi.svg, temperature.svg, dll.
```

### PyQt6 Issues
```bash
# Reinstall PyQt6:
pip uninstall PyQt6
pip install PyQt6>=6.4.0
```

## 📊 Screenshots

### Main Dashboard
- Card vital dengan real-time data
- Grafik trending 24 jam
- Status connection indicator

### Controls Panel  
- Profile selection dropdown
- Auto control toggles
- Temperature & humidity targets

## 🚀 Production Ready

Untuk ESP32 integration, ganti simulation di `kartel_data.py` dengan:
```python
# MQTT real connection
# Sensor readings dari hardware
# Relay control untuk pemanas/humidifier
```

## 📄 License
MIT License © 2025 KARTEL Team

---
🥚 **Built with ❤️ for Poultry Farmers** 🥚
- **Gradient Cards**: Card suhu (orange-yellow) dan kelembaban (purple-indigo)  
- **Icon SVG**: Koleksi 20+ icon kustom dengan desain konsisten
- **Dynamic Icons**: Icon WiFi berubah sesuai status koneksi
- **Responsive Layout**: Adaptif dengan berbagai ukuran layar
- **QSS Styling**: Stylesheet terpusat untuk maintenance yang mudah

#### 🔄 **Functional Features**
- **Real-time Data**: Update sensor setiap 3 detik dengan fluktuasi realistis
- **Interactive Graph**: Grafik live dengan tooltip dan dual-axis
- **Smart Control**: Auto-control pemanas/humidifier berdasarkan setpoint
- **Profile Management**: Preset inkubasi untuk berbagai jenis telur
- **MQTT Integration**: Koneksi wireless dengan ESP32/IoT devices
- **Data Simulation**: Sistem dummy data untuk testing dan demo

### 🚀 Cara Menjalankan

#### 1. Persyaratan Sistem
- **Python**: 3.8 atau lebih baru
- **OS**: Windows 10/11, macOS, Linux
- **RAM**: Minimal 4GB 
- **Storage**: 100MB untuk aplikasi

#### 2. Quick Start
```bash
# Clone repository
git clone https://github.com/Wissasono11/kartel-gui.git
cd kartel-gui

# Install dependencies
pip install -r requirements.txt

# Jalankan dashboard fungsional
python kartel_dashboard.py

# Atau jalankan dashboard static
python dashboard-gui.py
```

#### 3. Dependencies
```
PyQt6>=6.0.0
pyqtgraph>=0.13.0
qtawesome>=1.2.0
numpy>=1.21.0
```

### 📁 Struktur Project
```
KARTEL/
├── 📄 dashboard-gui.py          # Dashboard static (tampilan saja)
├── 🚀 kartel_dashboard.py   # Dashboard fungsional (dengan data dummy)
├── 🎮 kartel_controller.py      # Logic controller untuk GUI
├── 📊 kartel_data.py           # Data manager dan simulasi sensor
├── 🎨 asset/
│   ├── 📁 style/
│   │   └── styles.qss          # Centralized QSS stylesheet
│   └── 📁 svg/                 # SVG icon collection (20+ icons)
│       ├── temperature.svg
│       ├── humidity.svg
│       ├── wifi.svg
│       ├── wifi-notconnect.svg
│       ├── calendar.svg
│       ├── dropdown.svg
│       └── ... (dan lainnya)
├── 📋 requirements.txt         # Python dependencies
└── 📖 README.md               # Documentation lengkap
```

### 🔧 Konfigurasi

#### 📋 Profil Inkubasi
Dashboard mendukung profil preset untuk berbagai jenis telur:

| Telur | Suhu | Kelembaban | Durasi |
|-------|------|------------|--------|
| 🐔 **Ayam** | 38.0°C | 60% | 21 hari |
| 🦆 **Bebek** | 37.5°C | 65% | 28 hari |
| 🐦 **Puyuh** | 37.8°C | 55% | 17 hari |

#### ⚙️ MQTT Settings
```python
# Default configuration
{
  "username": "kartel_esp32",
  "password": "KartelTest123",
  "broker": "localhost",
  "port": 1883
}
```

### 📊 Fitur Dashboard Detail

#### 🏠 **Panel Header**
- **Logo KARTEL**: Gradient modern dengan typography Manrope
- **Status WiFi**: Icon dinamis (wifi.svg / wifi-notconnect.svg)
  - 🟢 **Terhubung**: Background hijau #10B981
  - 🔴 **Tidak Terhubung**: Background merah #EF4444  
- **Counter Inkubasi**: Clickable button untuk demo advance day

#### 📊 **Card Vital**
- **Card Suhu**: Gradient kuning-orange (#FFD54F → #FF8F00)
  - Nilai current: Font size 48px, bold
  - Target dalam box terpisah dengan background transparan
- **Card Kelembaban**: Gradient ungu (#7C3AED → #4338CA)
  - Update real-time setiap 3 detik
  - Fluktuasi natural ±0.5°C untuk suhu, ±1% untuk kelembaban

#### 🔧 **Status System**
- **Pemanas**: 
  - 🟢 Aktif (background hijau #D1FAE5, text #065F46)
  - 🔴 Non-aktif (background merah #FEE2E2, text #991B1B)
- **Humidifier**: Auto-control berdasarkan selisih kelembaban >2%
- **Motor Pembalik**: Status "Menunggu" dengan countdown 4 jam
- **Timer**: Real-time countdown dengan format HH:MM:SS

#### 📈 **Grafik Tren Real-time**
- **Dual Axis**: Suhu (kiri) dan Kelembaban (kanan)
- **Live Data**: Update setiap 3 detik dengan animasi smooth
- **Interactive**: Hover tooltip dengan detail nilai dan waktu  
- **Colors**: Suhu (#FFC107), Kelembaban (#5A3FFF)
- **Rolling Data**: Menyimpan 24 data point terakhir
- **Time Labels**: Format HH:MM pada sumbu X

#### ⚙️ **Panel Konfigurasi**
- **Profil Dropdown**: Auto-apply setpoint saat dipilih
- **Manual Input**: Validasi real-time dengan border merah untuk nilai invalid
- **Toggle Devices**: Instant feedback dengan popup message
- **MQTT Form**: Simulasi koneksi dengan success rate 80%
- **Info Box**: Background #E6DDFF dengan text justified alignment

### 🔗 Integrasi ESP32 (Untuk Produksi)

Dashboard ini dirancang untuk integrasi dengan ESP32/IoT devices melalui MQTT:

#### 📡 **MQTT Topics**
```bash
# Sensor data dari ESP32 ke Dashboard
kartel/sensor/temperature    # {"value": 37.5, "timestamp": "2025-11-18T10:30:00"}
kartel/sensor/humidity       # {"value": 62.3, "timestamp": "2025-11-18T10:30:00"}

# Control commands dari Dashboard ke ESP32  
kartel/control/heater        # {"action": "on", "timestamp": "2025-11-18T10:30:00"}
kartel/control/humidifier    # {"action": "off", "timestamp": "2025-11-18T10:30:00"}

# Device status dari ESP32
kartel/status/devices        # {"heater": true, "humidifier": false, "motor": "idle"}
```

#### 🎮 **Mode Demo vs Production**
```python
# Mode Demo (saat ini) - untuk testing UI
python kartel_dashboard.py  # Data dummy dengan simulasi real-time

# Mode Production (integrasi ESP32)
python dashboard-gui.py         # Static UI, siap untuk integrasi MQTT
```

### 🎯 Cara Penggunaan

#### 🚀 **Quick Demo**
1. **Start**: `python kartel_dashboard.py`
2. **Monitoring**: Lihat data real-time di card vital dan grafik  
3. **Interaction**: 
   - Klik profil inkubasi untuk auto-apply setpoint
   - Toggle manual pemanas/humidifier
   - Klik tombol hari untuk advance inkubasi
   - Test koneksi MQTT dengan form
4. **Visual**: Perhatikan perubahan warna dan icon sesuai status

#### 📱 **Features Testing**
- **Real-time Graph**: Data point baru setiap 3 detik
- **Auto Control**: Pemanas on/off berdasarkan suhu vs target
- **Status Updates**: Device status berubah setiap detik
- **WiFi Simulation**: Random connect/disconnect (10% chance)
- **Day Progression**: Auto advance atau manual click

### 🛠 Troubleshooting

#### ❌ **Common Issues**

**Error: "ModuleNotFoundError: No module named 'PyQt6'"**
```bash
pip install PyQt6 pyqtgraph qtawesome
```

**Icon tidak muncul**
```bash
# Pastikan folder asset/svg/ exist dan berisi file SVG
ls asset/svg/  # Should show: wifi.svg, wifi-notconnect.svg, temperature.svg, etc.
```

**Font Manrope tidak terdeteksi**
- ✅ **Normal**: Aplikasi akan fallback ke Arial
- 🔧 **Fix**: Install Manrope font di sistem atau add ke folder fonts/

**Grafik tidak update**
- 🔧 **Check**: Pastikan menggunakan `kartel_dashboard.py` bukan `dashboard-gui.py`
- 🔧 **Restart**: Close dan buka kembali aplikasi

#### 🐛 **Debug Mode**
```python
# Enable verbose logging
export KARTEL_DEBUG=1
python kartel_dashboard.py

# Output akan menampilkan:
# ✅ Font aplikasi: Manrope/Arial fallback  
# ✅ Stylesheet berhasil dimuat dari: asset/style/styles.qss
# 📊 Data updated: {"temperature": 37.5, "humidity": 62.3}
```

### 🎨 Technical Details

#### 🏗️ **Architecture**
```
┌─────────────────────────┐
│   kartel_dashboard.py   │ ← Main GUI (PyQt6)
│         (View)          │
└───────────┬─────────────┘
            │ Signals/Slots
┌───────────▼─────────────┐
│   kartel_controller.py  │ ← Logic Controller  
│      (Controller)       │
└───────────┬─────────────┘  
            │ Data Access
┌───────────▼─────────────┐
│    kartel_data.py      │ ← Data Manager
│        (Model)         │ ← Simulation Engine
└─────────────────────────┘
```

#### 🎨 **Styling System**
- **Centralized QSS**: `asset/style/styles.qss`
- **Dynamic Classes**: `#statusConnected`, `#statusNotConnected`
- **Gradient Support**: CSS gradients untuk card backgrounds
- **Icon Integration**: SVG loading dengan `load_svg_icon()`
- **Font Management**: Manrope loading dengan Arial fallback

#### � **Real-time Updates**
```python
# Controller timers:
update_timer.start(3000)     # Sensor data setiap 3 detik
status_timer.start(1000)     # Device status setiap 1 detik

# Data flow:
Data Manager → Controller → GUI Signals → Widget Updates
```

### �📝 Changelog

#### v2.0.0 (2025-11-18) - **MAJOR UPDATE**
- 🔄 **Full Functional Dashboard**: Live data dengan dummy simulation
- 🎨 **PyQt6 Migration**: Upgrade dari PyQt5 ke PyQt6
- 📊 **Real-time Graph**: Grafik live dengan tooltip interaktif  
- 🎮 **Interactive Controls**: Semua tombol dan input berfungsi
- 📱 **Dynamic Icons**: WiFi icon berubah sesuai status
- 🎯 **Smart Auto-control**: Logic untuk pemanas/humidifier
- 📈 **Data Management**: Rolling data dengan memory efficiency
- 🎨 **Improved Styling**: QSS centralized + gradient enhancements
- 🔧 **Clean Architecture**: Separation of concerns (MVC pattern)

#### v1.5.0 (2025-11-18)
- ✅ **Icon Integration**: 20+ custom SVG icons
- ✅ **Styling Consolidation**: Centralized QSS file
- ✅ **Graph Improvements**: Interactive tooltips
- ✅ **Font Optimization**: Weight adjustments
- ✅ **Text Alignment**: Justified text in info box

#### v1.0.0 (2025-11-17) - **Initial Release**
- ✅ **Dashboard Layout**: Sesuai mockup design
- ✅ **Card Vital**: Gradient backgrounds
- ✅ **Status System**: Icon dan color coding  
- ✅ **Graph Panel**: Static 24h data visualization
- ✅ **Configuration Panel**: Form inputs dan controls
- ✅ **MQTT Structure**: Ready for ESP32 integration

### 🚀 Roadmap

#### 🔜 **Next Features**
- [ ] **Database Integration**: SQLite untuk data logging
- [ ] **Historical Reports**: Export data ke CSV/PDF
- [ ] **Alert System**: Notifications untuk suhu/kelembaban abnormal  
- [ ] **Multi-device**: Support multiple incubator monitoring
- [ ] **Web Interface**: Dashboard web untuk remote monitoring
- [ ] **Mobile App**: Companion app untuk smartphone

#### 🎯 **Production Ready**
- [ ] **ESP32 Integration**: Real MQTT connection testing
- [ ] **Hardware Interfacing**: Sensor calibration dan relay control
- [ ] **Error Handling**: Robust error recovery
- [ ] **Logging System**: Comprehensive logging
- [ ] **Configuration UI**: Settings panel untuk advanced config

### 👥 Contributors & Credits

#### 🛠️ **Development Team**
- **Lead Developer**: KARTEL Team
- **UI/UX Design**: Modern dashboard concept
- **Technical Stack**: PyQt6, PyQtGraph, QtAwesome
- **Icon Design**: Custom SVG collection

#### 🙏 **Acknowledgments**
- **PyQt6**: Cross-platform GUI framework
- **PyQtGraph**: Real-time plotting library  
- **Manrope Font**: Modern typography
- **QtAwesome**: Icon library for fallbacks

### 📄 License & Usage

#### 📋 **MIT License**
```
Copyright (c) 2025 KARTEL Team

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

[Full MIT License text...]
```

#### 🎯 **Usage Guidelines**
- ✅ **Commercial Use**: Diizinkan untuk proyek komersial
- ✅ **Modification**: Bebas dimodifikasi sesuai kebutuhan  
- ✅ **Distribution**: Dapat didistribusikan dengan/tanpa modifikasi
- ⚠️ **Attribution**: Mohon credit kepada KARTEL Team jika menggunakan

---
<div align="center">

**KARTEL - Kendali Automasi Ruangan Telur**  
*Professional Egg Incubator Monitoring Dashboard*

🥚 **Built with ❤️ for Poultry Farmers** 🥚

[![GitHub](https://img.shields.io/badge/GitHub-Wissasono11-black?logo=github)](https://github.com/Wissasono11)  
[![Python](https://img.shields.io/badge/Made%20with-Python-blue?logo=python)](https://python.org)  
[![PyQt6](https://img.shields.io/badge/GUI-PyQt6-green?logo=qt)](https://pypi.org/project/PyQt6/)  

*© 2025 KARTEL Team - All Rights Reserved*

</div>