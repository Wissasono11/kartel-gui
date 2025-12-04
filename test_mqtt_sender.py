import time
import json
import random
import paho.mqtt.client as mqtt

# --- KONFIGURASI ---
BROKER = "mqtt.teknohole.com"
PORT = 1884
TOPIC_STATUS = "topic/penetasan/status"   # Topic untuk MENGIRIM data
TOPIC_COMMAND = "topic/penetasan/command" # Topic untuk MENDENGAR perintah
USERNAME = ""
PASSWORD = ""

# Variabel Global untuk State Simulator
current_target = 38.0  # Default awal

# Callback ketika simulator berhasil konek
def on_connect(client, userdata, flags, rc):
    print(f"✅ Simulator Connected with result code {rc}")
    # Simulator harus SUBSCRIBE ke topic command agar bisa diperintah dashboard
    client.subscribe(TOPIC_COMMAND)
    print(f"👂 Listening for commands on: {TOPIC_COMMAND}")

# Callback ketika simulator menerima perintah dari Dashboard
def on_message(client, userdata, msg):
    global current_target
    try:
        payload = msg.payload.decode('utf-8')
        print(f"📩 Command Received: {payload}")
        
        data = json.loads(payload)
        
        # Jika ada perintah SET, update target simulasi
        if "SET" in data:
            new_target = float(data["SET"])
            print(f"⚙️ CHANGE SETPOINT: {current_target} -> {new_target}")
            current_target = new_target
            
    except Exception as e:
        print(f"⚠ Error parsing command: {e}")

def main():
    # Setup Client
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, "kartel_smart_simulator")
    client.username_pw_set(USERNAME, PASSWORD)
    
    # Pasang Callbacks
    client.on_connect = on_connect
    client.on_message = on_message
    
    print(f"Connecting to {BROKER}...")
    try:
        client.connect(BROKER, PORT, 60)
        client.loop_start() # Loop background untuk handle receive message
        
        while True:
            # 1. Simulasi Data Sensor (Mengikuti target yang baru!)
            # Suhu akan berfluktuasi di sekitar current_target
            temp = round(random.uniform(current_target - 0.5, current_target + 0.5), 1)
            hum = round(random.uniform(55.0, 65.0), 1)
            
            # 2. Simulasi Power
            if temp < current_target:
                power = random.randint(50, 100) # Panaskan jika dibawah target
            else:
                power = random.randint(0, 20)   # Dinginkan jika diatas target
            
            # 3. Simulasi Motor
            current_time = int(time.time())
            rotate_on = 1 if current_time % 20 < 5 else 0
            
            # --- PAYLOAD ---
            # Simulator sekarang mengirim balik SET sesuai dengan yang diminta Dashboard
            payload = {
                "temperature": temp,
                "humidity": hum,
                "power": power,
                "rotate_on": rotate_on,
                "SET": current_target  # <-- Ini sekarang dinamis!
            }
            
            client.publish(TOPIC_STATUS, json.dumps(payload))
            print(f"📤 Sent Status: T={temp}°C, SET={current_target}°C")
            
            time.sleep(2) 
            
    except KeyboardInterrupt:
        print("\nStopped.")
        client.loop_stop()
    except Exception as e:
        print(f"Connection failed: {e}")

if __name__ == "__main__":
    main()