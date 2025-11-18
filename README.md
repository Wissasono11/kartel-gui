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

## 🚀 Quick Start

### Install & Run
```bash
# Install dependencies
pip install -r requirements.txt

# Jalankan dashboard utama (recommended)
python kartel_dashboard.py

# Atau jalankan dashboard static
python dashboard-gui.py
```

### Dependencies
```
PyQt6>=6.4.0
PyQtGraph>=0.13.0
qtawesome>=1.2.0
```

## 📁 Struktur Project
```
KARTEL/
├── kartel_dashboard.py    # Main app (real-time)
├── kartel_data.py         # Data simulation
├── kartel_controller.py   # Logic controller  
├── dashboard-gui.py       # Static dashboard
├── asset/
│   ├── svg/              # Custom icons
│   └── style/styles.qss  # Styling
└── requirements.txt
```

## ⚙️ Konfigurasi

### Profil Inkubasi
| Telur | Suhu | Kelembaban | Durasi |
|-------|------|------------|--------|
| 🐔 **Ayam** | 38.0°C | 60% | 21 hari |
| 🦆 **Bebek** | 37.5°C | 65% | 28 hari |
| 🐦 **Puyuh** | 37.8°C | 55% | 17 hari |

### MQTT Settings (ESP32)
```python
{
  "username": "kartel_esp32",
  "password": "KartelTest123", 
  "broker": "localhost",
  "port": 1883
}
```

## 🔧 Troubleshooting

**ModuleNotFoundError PyQt6**
```bash
pip install PyQt6 pyqtgraph qtawesome
```

**Icon tidak muncul**
- Pastikan folder `asset/svg/` berisi file SVG

**Grafik tidak update**
- Gunakan `kartel_dashboard.py` bukan `dashboard-gui.py`

## 📊 Fitur Detail

### Real-time Dashboard
- **Card Vital**: Gradient suhu (orange) & kelembaban (purple)
- **Status System**: Auto-control pemanas/humidifier
- **Live Graph**: Update setiap 3 detik dengan tooltip
- **WiFi Indicator**: Dynamic icon sesuai koneksi

### Controls
- **Profil Dropdown**: Auto-apply setpoint
- **Manual Control**: Toggle pemanas/humidifier
- **MQTT Integration**: Simulasi koneksi ESP32
- **Day Counter**: Progress inkubasi

## 🔗 ESP32 Integration

### MQTT Topics
```bash
# Sensor data
kartel/sensor/temperature
kartel/sensor/humidity

# Control commands  
kartel/control/heater
kartel/control/humidifier

# Device status
kartel/status/devices
```

## 📝 Changelog

### v2.0.0 (2025-11-18) - MAJOR UPDATE
- ✅ Full functional dashboard dengan live data
- ✅ PyQt6 migration dari PyQt5
- ✅ Real-time graph dengan tooltip
- ✅ Smart auto-control logic
- ✅ Dynamic icons & improved styling
- ✅ Clean MVC architecture

## 📄 License
MIT License © 2025 KARTEL Team

---
<div align="center">

**KARTEL - Kendali Automasi Ruangan Telur**  
🥚 **Built with ❤️ for Poultry Farmers** 🥚

[![GitHub](https://img.shields.io/badge/GitHub-Wissasono11-black?logo=github)](https://github.com/Wissasono11)  
[![Python](https://img.shields.io/badge/Made%20with-Python-blue?logo=python)](https://python.org)  

</div>