import os
import json
import base64
from pathlib import Path
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import platform

try:
    if platform.system() == "Windows":
        import keyring
        KEYRING_AVAILABLE = True
    else:
        KEYRING_AVAILABLE = False
except ImportError:
    KEYRING_AVAILABLE = False

# Untuk koneksi real-time ke sensor
CONNECTION_TYPE = 'MQTT'

# File untuk menyimpan kredensial user (terenkripsi)
CREDENTIALS_FILE = "user_credentials.enc"
APP_NAME = "KartelDashboard"

def _generate_key_from_machine():
    """Generate kunci enkripsi unik berdasarkan mesin"""
    try:
        # Gunakan kombinasi nama mesin dan username sebagai salt
        import socket
        import getpass
        machine_id = f"{socket.gethostname()}_{getpass.getuser()}"
        salt = machine_id.encode()[:16].ljust(16, b'0')  # Pastikan 16 bytes
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(machine_id.encode()))
        return key
    except Exception:
        # Fallback ke kunci static jika gagal
        return base64.urlsafe_b64encode(b'fallback_key_32_bytes_length!!')

def _encrypt_data(data: str) -> str:
    """Enkripsi data menggunakan kunci yang digenerate dari mesin"""
    try:
        key = _generate_key_from_machine()
        f = Fernet(key)
        encrypted = f.encrypt(data.encode())
        return base64.urlsafe_b64encode(encrypted).decode()
    except Exception as e:
        print(f"⚠ Encryption failed: {e}")
        return data  # Return original jika enkripsi gagal

def _decrypt_data(encrypted_data: str) -> str:
    """Dekripsi data menggunakan kunci yang digenerate dari mesin"""
    try:
        key = _generate_key_from_machine()
        f = Fernet(key)
        decoded = base64.urlsafe_b64decode(encrypted_data.encode())
        decrypted = f.decrypt(decoded)
        return decrypted.decode()
    except Exception as e:
        print(f"⚠ Decryption failed: {e}")
        return ""  # Return empty jika dekripsi gagal

# MQTT Settings untuk menerima data real dari sensor ESP32 via Teknohole
MQTT_SETTINGS = {
    "broker": "mqtt.teknohole.com",
    "port": 1884,  
    "username": "kartel",
    "password": "kartel123",
    "topics": {
        "sensor_data": "topic/penetasan/status",     # Data yang diterima dari ESP32
        "command": "topic/penetasan/command"         # Command yang dikirim ke ESP32
    },
    "keepalive": 60,
    "qos": 1
}

def save_user_credentials(username: str, password: str, method: str = "auto"):
    """Simpan kredensial user dengan metode yang aman
    
    Args:
        username: Username untuk disimpan
        password: Password untuk disimpan  
        method: Metode penyimpanan ('auto', 'keyring', 'encrypted_file')
    """
    try:
        # Auto select method: prioritas keyring > encrypted file
        if method == "auto":
            if KEYRING_AVAILABLE:
                method = "keyring"
            else:
                method = "encrypted_file"
        
        if method == "keyring" and KEYRING_AVAILABLE:
            # Gunakan Windows Credential Manager
            keyring.set_password(APP_NAME, "username", username)
            keyring.set_password(APP_NAME, "password", password)
            keyring.set_password(APP_NAME, "remember", "true")
            print(f"🔐 Credentials saved securely in Windows Credential Manager")
            return True
            
        elif method == "encrypted_file":
            # Simpan ke file terenkripsi
            credentials = {
                "username": username,
                "password": password,
                "remember": True,
                "method": "encrypted"
            }
            
            # Enkripsi seluruh data
            json_data = json.dumps(credentials)
            encrypted_data = _encrypt_data(json_data)
            
            with open(CREDENTIALS_FILE, 'w') as f:
                f.write(encrypted_data)
            
            print(f"🔐 Credentials saved with encryption")
            return True
            
        else:
            print(f"❌ No secure storage method available")
            return False
            
    except Exception as e:
        print(f"❌ Error saving credentials: {e}")
        return False

def load_user_credentials():
    """Muat kredensial user dari penyimpanan aman"""
    try:
        # Coba load dari Windows Credential Manager dulu
        if KEYRING_AVAILABLE:
            try:
                username = keyring.get_password(APP_NAME, "username")
                password = keyring.get_password(APP_NAME, "password")
                remember = keyring.get_password(APP_NAME, "remember")
                
                if username and password and remember == "true":
                    print(f"🔐 Loaded credentials from Windows Credential Manager")
                    return {
                        "username": username,
                        "password": password,
                        "remember": True,
                        "method": "keyring"
                    }
            except Exception as e:
                print(f"⚠ Failed to load from Credential Manager: {e}")
        
        # Coba load dari file terenkripsi
        if os.path.exists(CREDENTIALS_FILE):
            try:
                with open(CREDENTIALS_FILE, 'r') as f:
                    encrypted_data = f.read().strip()
                
                # Dekripsi data
                json_data = _decrypt_data(encrypted_data)
                if json_data:
                    credentials = json.loads(json_data)
                    
                    if credentials.get("remember", False):
                        print(f"🔐 Loaded encrypted credentials from file")
                        return credentials
                        
            except Exception as e:
                print(f"⚠ Failed to load encrypted credentials: {e}")
                # Coba load file lama (plain JSON) untuk backward compatibility
                try:
                    with open("user_credentials.json", 'r') as f:
                        credentials = json.load(f)
                    if credentials.get("remember", False):
                        print(f"⚠ Loaded old unencrypted credentials - consider saving again for encryption")
                        return credentials
                except:
                    pass
        
        return None
        
    except Exception as e:
        print(f"❌ Error loading credentials: {e}")
        return None

def clear_user_credentials():
    """Hapus kredensial user dari semua metode penyimpanan"""
    success = True
    
    try:
        # Hapus dari Windows Credential Manager
        if KEYRING_AVAILABLE:
            try:
                keyring.delete_password(APP_NAME, "username")
                keyring.delete_password(APP_NAME, "password") 
                keyring.delete_password(APP_NAME, "remember")
                print(f"🔐 Cleared credentials from Windows Credential Manager")
            except Exception as e:
                print(f"⚠ No credentials found in Credential Manager or error: {e}")
        
        # Hapus file terenkripsi
        if os.path.exists(CREDENTIALS_FILE):
            os.remove(CREDENTIALS_FILE)
            print(f"🔐 Cleared encrypted credentials file")
            
        # Hapus file lama (plain JSON) jika ada
        old_file = "user_credentials.json"
        if os.path.exists(old_file):
            os.remove(old_file)
            print(f"🧹 Cleared old unencrypted credentials file")
        
        return success
        
    except Exception as e:
        print(f"❌ Error clearing credentials: {e}")
        return False

# Format data sensor real-time
DATA_FORMAT = {
    "sensor_keys": ["temperature", "humidity", "power", "rotate_on", "SET"],
    "update_interval": 3000,  # ms - interval update dari sensor
    "history_max_points": 100  # maksimal data point untuk grafik
}

# Default device settings
DEFAULT_SETTINGS = {
    "target_temperature": 38.0,
    "target_humidity": 60.0,
    "buzzer_state": "OFF",
    "relay_on_time": 10,     # seconds
    "relay_interval": 3,     # minutes
    "incubation_day": 1,
    "total_days": 21
}

# Connection retry settings
CONNECTION_RETRY = {
    "max_attempts": 5,
    "retry_delay": 5,  # seconds
    "reconnect_delay": 30  # seconds
}