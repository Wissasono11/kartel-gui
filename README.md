<div align="center">
  <img src="asset/img/kartel-logo.png" alt="KARTEL Logo" width="140" height="140">
  
  # KARTEL (Kendali Automasi Ruangan Telur)
  
  **Dashboard Monitoring Inkubator Cerdas Berbasis IoT & Desktop**

  [![Python](https://img.shields.io/badge/Python-3.8+-blue.svg?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
  [![PyQt6](https://img.shields.io/badge/GUI-PyQt6-green.svg?style=for-the-badge&logo=qt&logoColor=white)](https://pypi.org/project/PyQt6/)
  [![MQTT](https://img.shields.io/badge/Protocol-MQTT-orange.svg?style=for-the-badge&logo=mqtt&logoColor=white)](https://mqtt.org)
  [![Architecture](https://img.shields.io/badge/Architecture-MVC-purple.svg?style=for-the-badge)](https://en.wikipedia.org/wiki/Model%E2%80%93view%E2%80%93controller)

</div>

---

## 📖 Tentang Proyek

**KARTEL** adalah aplikasi desktop modern yang dibangun menggunakan Python (PyQt6) untuk memantau dan mengendalikan mesin penetas telur secara *real-time*. Aplikasi ini berkomunikasi dengan perangkat keras (seperti ESP32) melalui protokol MQTT, memungkinkan pemantauan suhu, kelembaban, dan status motor pembalik telur dari jarak jauh.

Proyek ini telah direfaktor sepenuhnya menggunakan arsitektur **MVC (Model-View-Controller)** untuk memastikan kode yang modular, mudah dipelihara, dan *scalable*.

## ✨ Fitur Utama

*   📊 **Real-time Monitoring** - Menampilkan grafik Suhu & Kelembaban secara langsung (live) dengan data dari sensor.
*   🔄 **Komunikasi Dua Arah** - Mengirim perintah *Setpoint* suhu ke alat dan menerima umpan balik status.
*   📈 **Grafik Interaktif** - Visualisasi data historis dengan fitur *tooltip* interaktif menggunakan `PyQtGraph`.
*   ⚙️ **Manajemen Profil** - Tersedia profil inkubasi otomatis (Ayam/Bebek) atau pengaturan manual (Custom).
*   🔌 **Koneksi MQTT Stabil** - Dilengkapi fitur *auto-reconnect*, *heartbeat*, dan indikator status koneksi.
*   🔒 **Keamanan Kredensial** - Penyimpanan username/password MQTT terenkripsi aman menggunakan `cryptography` dan `keyring`.
*   🎨 **UI Modern** - Antarmuka yang bersih dengan tema warna intuitif dan responsif.

## 📂 Struktur Proyek (v5.0)

Struktur direktori telah dirapikan untuk memisahkan logika bisnis, tampilan, dan data:

```text
KARTEL-GUI/
├── main.py                  # Entry Point Aplikasi
├── test_mqtt_sender.py      # Simulator Perangkat (untuk testing)
├── requirements.txt         # Daftar dependensi
├── asset/                   # Aset Gambar, Ikon SVG, & Stylesheet (.qss)
├── data/                    # Penyimpanan Data Lokal (JSON)
└── src/                     # Source Code Utama
    ├── config/              # Konfigurasi Global (Settings)
    ├── controllers/         # Logika Penghubung (Event Handlers)
    ├── services/            # Logika Bisnis (MQTT, Auth, Data Store)
    └── views/               # Komponen Tampilan (Widgets, Graphs, Panels)
```

## 🚀 Instalasi & Penggunaan

Ikuti langkah-langkah berikut untuk menjalankan aplikasi di komputer Anda:

### 1. Persiapan Lingkungan
Pastikan Python 3.8+ sudah terinstall. Disarankan menggunakan *Virtual Environment*.

```bash
# Buat virtual environment (Opsional)
python -m venv venv

# Aktifkan virtual environment
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate
```

### 2. Install Dependensi
Install semua pustaka yang dibutuhkan melalui `requirements.txt`:

```bash
pip install -r requirements.txt
```

### 3. Jalankan Aplikasi
Jalankan file utama untuk membuka dashboard:

```bash
python main.py
```

### 4. Jalankan Simulator (Opsional)
Jika Anda tidak memiliki perangkat keras ESP32, Anda dapat menjalankan simulator untuk mengirim data palsu ke dashboard:

```bash
python test_mqtt_sender.py
```

## ⚙️ Konfigurasi MQTT

Pengaturan default broker dapat diubah di file `src/config/settings.py`.

| Parameter | Default Value | Deskripsi |
| :--- | :--- | :--- |
| **Broker** | `mqtt.teknohole.com` | Alamat server MQTT |
| **Port** | `1884` | Port koneksi |
| **Topic Status** | `topic/penetasan/status` | Topic untuk menerima data sensor (Subscribe) |
| **Topic Command** | `topic/penetasan/command` | Topic untuk mengirim perintah (Publish) |

## 📡 Protokol Data (JSON)

Aplikasi mengharapkan format JSON berikut dari perangkat keras (ESP32):

```json
{
  "temperature": 38.5,   // Float: Suhu saat ini
  "humidity": 60.2,      // Float: Kelembaban saat ini
  "power": 45,           // Int: Persentase daya pemanas (0-100)
  "rotate_on": 1,        // Int: 1 = Motor berputar, 0 = Diam
  "SET": 38.0            // Float: Target suhu yang sedang aktif di alat
}
```

## 🛠️ Teknologi yang Digunakan

*   **Bahasa:** Python 3.10+
*   **GUI Framework:** PyQt6
*   **Plotting Library:** PyQtGraph
*   **IoT Protocol:** Paho MQTT Client
*   **Security:** Cryptography & Keyring
*   **Icons:** QtAwesome & SVG Custom
