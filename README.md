<div align="center">
  <img src="asset/img/kartel-logo.png" alt="KARTEL Logo" width="120" height="120">
  
  # KARTEL - Kendali Automasi Ruangan Telur
  
  [![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
  [![PyQt6](https://img.shields.io/badge/GUI-PyQt6-green.svg)](https://pypi.org/project/PyQt6/)
  [![MQTT](https://img.shields.io/badge/MQTT-Teknohole-orange.svg)](https://mqtt.teknohole.com)
</div>

Dashboard monitoring dan kontrol inkubator telur dengan koneksi real-time MQTT ke ESP32.

## ✨ Fitur Utama

- 📊 **Real-time Monitoring** - Data suhu & kelembaban dari ESP32
- 🔄 **Motor Pembalik** - Otomatis berputar setiap 3 jam saat terhubung MQTT
- 🎮 **Kontrol Perangkat** - Toggle pemanas & humidifier manual
- 📈 **Grafik Live** - Visualisasi data dengan tooltip interaktif
- 🔌 **MQTT Integration** - Koneksi ke broker Teknohole
- ⏰ **Timer Countdown** - Display waktu putaran berikutnya

## 🚀 Instalasi & Menjalankan

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Jalankan Dashboard
```bash
python kartel_dashboard.py
```

### 3. Koneksi MQTT (Opsional)
- Username: `kartel`
- Password: `kartel123` 
- Klik "Hubungkan Ke Broker" di panel konfigurasi

## 📁 Struktur Project
```
KARTEL/
├── kartel_dashboard.py    # 🎯 Main application (GUI dashboard)
├── kartel_controller.py   # 🎮 Logic controller & MQTT handler  
├── kartel_data.py         # 📊 Data manager & ESP32 communication
├── config.py              # ⚙️ MQTT settings & configuration
├── requirements.txt       # 📦 Python dependencies
├── README.md              # 📖 Project documentation
└── asset/                 # 🎨 UI Assets
    ├── img/              # Logo & images
    ├── svg/              # Custom SVG icons
    └── style/
        └── styles.qss    # Qt stylesheet
```

## ⚙️ Konfigurasi Profil Inkubasi

| Jenis Telur | Suhu Target | Kelembaban | Durasi |
|-------------|-------------|------------|--------|
| 🐔 **Ayam** | 38.0°C | 60% | 21 hari |
| 🦆 **Bebek** | 37.5°C | 65% | 28 hari |

## 🔧 Cara Penggunaan

### Mode Tanpa Koneksi (Default)
- Motor pembalik: Status **Idle**
- Timer countdown: **03:00:00** 
- Kontrol manual tersedia

### Mode Terhubung MQTT
- Motor pembalik: Otomatis berputar **10 detik** saat connect
- Timer countdown: Mulai hitung mundur dari **3 jam**
- Data real-time dari ESP32

### Panel Konfigurasi
1. **Profil Inkubasi**: Pilih preset Ayam/Bebek
2. **Pengaturan Manual**: Set suhu & kelembaban custom  
3. **Kontrol Manual**: Toggle pemanas/humidifier
4. **Koneksi MQTT**: Input kredensial untuk connect ke broker

## 🔌 MQTT Configuration

**Broker Settings:**
- Host: `mqtt.teknohole.com`
- Port: `1884`
- QoS: `1`

**Topics:**
- **Data sensor**: `topic/penetasan/message` 
- **Command**: `topic/penetasan/command`

## 📊 Status Sistem

### Device Status Cards
- **Pemanas**: Auto ON/OFF berdasarkan suhu target
- **Humidifier**: Auto ON/OFF berdasarkan kelembaban target  
- **Motor Pembalik**: Siklus 10s setiap 3 jam (saat terhubung)
- **Timer**: Countdown waktu putaran berikutnya

### Grafik Real-time
- **Sumbu Kiri**: Suhu (°C) - garis orange
- **Sumbu Kanan**: Kelembaban (%) - garis purple
- **Tooltip**: Hover untuk detail nilai & waktu

## 🔧 Troubleshooting

**Error: ModuleNotFoundError**
```bash
pip install PyQt6 pyqtgraph qtawesome paho-mqtt
```

**MQTT tidak connect**
- Pastikan kredensial benar: `kartel` / `kartel123`
- Check koneksi internet
- Firewall mungkin memblokir port 1884

**Icons tidak muncul**
```bash
# Pastikan folder asset/svg/ ada dan berisi file SVG
ls asset/svg/
```

**Motor tidak berputar**
- Motor hanya aktif saat terhubung MQTT
- Cek status koneksi di header dashboard

## 📝 Changelog

### v3.0.0 (2025-11-28)
- ✅ MQTT connection-dependent motor control
- ✅ Default idle state saat tidak terhubung
- ✅ Auto motor rotation saat MQTT connect
- ✅ Real-time countdown timer (3 jam)
- ✅ Simplified project structure

### v2.0.0 (2025-11-18)  
- ✅ Full functional dashboard dengan real-time data
- ✅ PyQt6 migration & modern UI
- ✅ MQTT integration via Teknohole

---

<div align="center">

**🥚 KARTEL - Teknologi untuk Peternak Modern 🥚**

*Built with Python & PyQt6 | MQTT Real-time Communication*

</div>