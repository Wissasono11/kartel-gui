import time
import json
import random
import paho.mqtt.client as mqtt
import re  # Diperlukan untuk parsing regex

# ================= KONFIGURASI =================
BROKER = "mqtt.teknohole.com"
PORT = 1884
USERNAME = "kartel"
PASSWORD = "kartel123"

# Topik
TOPIC_STATUS = "topic/penetasan/status"   # Publish
TOPIC_COMMAND = "topic/penetasan/command" # Subscribe

# ================= STATE VARIABLES =================
class IncubatorState:
    def __init__(self):
        # Settingan Default
        self.target_temp = 37.5
        self.relay_on_duration = 6      # Detik (Default lama putaran 6 detik)
        self.relay_interval = 60000     # Milidetik (Default 1 menit agar cepat dites)
                                        # Nanti bisa diubah lewat GUI jadi 1 jam/3 jam
        
        # Variabel Sensor & Aktuator
        self.current_temp = 28.0        # Suhu awal simulasi
        self.current_hum = 60.0
        self.dimmer_power = 0
        self.buzzer_active = False
        
        # Logika Relay / Motor
        self.relay_currently_on = False
        self.last_relay_run = 0
        self.future_rotate = int(time.time() * 1000) + self.relay_interval
        
        # PID Konstanta
        self.Kp = 40

    def update_physics(self):
        """Simulasi fisika sederhana"""
        # Hitung PID Sederhana
        error = self.target_temp - self.current_temp
        self.dimmer_power = int(max(0, min(100, error * self.Kp)))
        
        # Efek Fisika
        heating_power = self.dimmer_power * 0.05
        cooling_factor = 0.02
        
        self.current_temp += heating_power
        self.current_temp -= cooling_factor
        
        # Random noise
        self.current_temp += random.uniform(-0.05, 0.05)
        self.current_hum += random.uniform(-0.5, 0.5)

    def check_relay(self):
        """Simulasi Logika Timer Rotasi"""
        now = int(time.time() * 1000)
        
        # Cek apakah waktunya berputar
        if now >= self.future_rotate:
            print("\n[SIMULATOR] 🔄 ROTATING EGG NOW! (Relay ON)")
            self.relay_currently_on = True
            self.last_relay_run = now
            self.future_rotate = now + self.relay_interval
            
        # Cek durasi nyala relay
        if self.relay_currently_on:
            if (now - self.last_relay_run) >= (self.relay_on_duration * 1000):
                self.relay_currently_on = False
                print("[SIMULATOR] ⏹️ Rotation Done (Relay OFF)")

state = IncubatorState()

# ================= MQTT CALLBACKS =================

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"✅ Terhubung ke Broker! (RC: {rc})")
        client.subscribe(TOPIC_COMMAND)
        print(f"👂 Mendengarkan perintah di: {TOPIC_COMMAND}")
    else:
        print(f"❌ Gagal konek (RC: {rc})")

def on_message(client, userdata, msg):
    payload = msg.payload.decode('utf-8')
    print(f"\n📩 Perintah Diterima: {payload}")
    
    try:
        # 1. Parsing format string "SET" (Sesuai kode C++)
        if '"SET"' in payload:
            try:
                match = re.search(r'"SET"[^\d\.]*([\d\.]+)', payload)
                if match:
                    new_temp = float(match.group(1))
                    state.target_temp = new_temp
                    print(f"⚙️ Target Setpoint diubah ke: {state.target_temp}C")
            except: pass

        # 2. Parsing Buzzer
        if '"BUZZER":"ON"' in payload:
            state.buzzer_active = True
            print("🔔 BUZZER NYALA")
        if '"BUZZER":"OFF"' in payload:
            state.buzzer_active = False
            print("🔕 BUZZER MATI")

        # 3. Parsing JSON (RT_ON, RT_INT)
        if payload.startswith("{"):
            data = json.loads(payload)
            
            if "RT_ON" in data:
                state.relay_on_duration = int(data["RT_ON"])
                print(f"⏱️ Durasi Relay diupdate: {state.relay_on_duration} detik")
                
            if "RT_INT" in data:
                minutes = int(data["RT_INT"])
                state.relay_interval = minutes * 60000
                
                # Reset Timer
                state.future_rotate = int(time.time() * 1000) + state.relay_interval
                print(f"⏳ Interval Rotasi diupdate: {minutes} menit")
            
            # Fallback jika SET dikirim dalam format JSON murni
            if "SET" in data: 
                 state.target_temp = float(data["SET"])
                 print(f"⚙️ Target Setpoint (JSON) diubah ke: {state.target_temp}C")

    except Exception as e:
        print(f"⚠️ Error parsing: {e}")

# ================= MAIN PROGRAM =================

def main():
    # Menambahkan mqtt.CallbackAPIVersion.VERSION1 agar kompatibel
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, "ESP32_Simulator_Python")
    
    client.username_pw_set(USERNAME, PASSWORD)
    client.on_connect = on_connect
    client.on_message = on_message
    
    print(f"Menghubungkan ke {BROKER}...")
    try:
        client.connect(BROKER, PORT, 60)
        client.loop_start() # Jalankan loop MQTT di background
        
        last_publish = 0
        
        print("💡 Simulator Aktif. Default Interval: 1 Menit (agar cepat dites)")
        
        while True:
            current_millis = int(time.time() * 1000)
            
            # 1. Update Fisika & Timer
            state.update_physics()
            state.check_relay()
            
            # 2. Publish Data (Setiap 2 detik agar lebih responsif)
            if (current_millis - last_publish) >= 2000:
                last_publish = current_millis
                
                # --- LOGIKA STATUS MOTOR (UPDATED) ---
                if state.relay_currently_on:
                    # Jika relay sedang ON, kirim sisa durasi ON dalam detik
                    elapsed = current_millis - state.last_relay_run
                    # Hitung sisa waktu (total durasi - waktu berjalan)
                    rem_sec = max(0, int(state.relay_on_duration - (elapsed / 1000)))
                    
                    # Pastikan minimal bernilai 1 jika relay masih ON
                    # Agar GUI tetap membaca "Berputar" (karena != 0)
                    if rem_sec == 0: rem_sec = 1
                else:
                    # Jika relay OFF, kirim 0 (Idle)
                    rem_sec = 0
                
                # Format JSON
                payload = {
                    "temperature": round(state.current_temp, 1),
                    "humidity": round(state.current_hum, 1),
                    "power": state.dimmer_power,
                    "rotate_on": rem_sec,  
                    "SET": state.target_temp
                }
                
                json_str = json.dumps(payload)
                client.publish(TOPIC_STATUS, json_str)
                
                status_relay = "ON" if state.relay_currently_on else "OFF"
                print(f"📤 Sent: {json_str} | Relay: {status_relay}")
            
            time.sleep(0.1) # Sleep kecil
            
    except KeyboardInterrupt:
        print("\nSimulasi Dihentikan.")
        client.loop_stop()
        client.disconnect()

if __name__ == "__main__":
    main()