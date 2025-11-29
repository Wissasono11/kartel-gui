<div align="center">
  <img src="asset/img/kartel-logo.png" alt="KARTEL Logo" width="120" height="120">
  
  # KARTEL - Kendali Automasi Ruangan Telur
  
  [![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
  [![PyQt6](https://img.shields.io/badge/GUI-PyQt6-green.svg)](https://pypi.org/project/PyQt6/)
  [![MQTT](https://img.shields.io/badge/MQTT-Teknohole-orange.svg)](https://mqtt.teknohole.com)
</div>

Dashboard monitoring inkubator telur dengan data real-time dari ESP32 via MQTT.

## ✨ Fitur Utama

- 📊 **Real-time Data** - Suhu & kelembaban langsung dari ESP32
- 🔌 **MQTT Connection** - Manual connect/disconnect ke broker
- 📈 **Live Charts** - Grafik dengan tooltip interaktif
- ⚙️ **Profile Settings** - Preset untuk telur ayam & bebek
- 🎛️ **Device Status** - Monitor power & motor rotation

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run Application
```bash
python kartel_dashboard.py
```

### 3. Connect to MQTT
- Username: `kartel`
- Password: `kartel123`
- Click "Hubungkan Ke Broker"

## 📊 Status Cards

- **Power** - Heater power status from ESP32 data
- **Motor Pembalik** - Rotation status from ESP32 `rotate_on` data  
- **Putaran Berikutnya** - Static timer display

## ⚙️ Incubation Profiles

| Type | Temperature | Duration |
|------|-------------|----------|
| 🐔 Ayam | 38.0°C | 21 days |
| 🦆 Bebek | 37.5°C | 28 days |

## 🔌 MQTT Settings

- **Broker**: `mqtt.teknohole.com:1884`
- **Topic**: `topic/penetasan/status`
- **Data Format**: `{"temperature": 38.5, "humidity": 65.2, "power": 75, "rotate_on": 1}`

## 📝 Recent Updates (v4.0.0)

- ✅ Manual connection requirement (no auto-connect)
- ✅ Power card shows ESP32 heater power data
- ✅ Motor status from ESP32 `rotate_on` field
- ✅ Removed manual device controls
- ✅ Simplified UI - monitoring focused
- ✅ Temperature-only setpoint configuration

---

<div align="center">

**🥚 KARTEL - Modern Egg Incubator Monitoring 🥚**

</div>