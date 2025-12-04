# File: src/services/auth_service.py

import os
import json
import base64
import socket
import getpass
import platform

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# Import variabel konfigurasi dari settings
from src.config.settings import APP_NAME, CREDENTIALS_FILE

# Cek ketersediaan Keyring (Windows Credential Manager)
try:
    if platform.system() == "Windows":
        import keyring
        KEYRING_AVAILABLE = True
    else:
        KEYRING_AVAILABLE = False
except ImportError:
    KEYRING_AVAILABLE = False

class AuthService:
    """
    Service untuk menangani enkripsi, dekripsi, dan penyimpanan
    kredensial user secara aman.
    """

    @staticmethod
    def _generate_key_from_machine():
        """Private: Membuat kunci enkripsi unik berdasarkan hardware ID mesin"""
        try:
            machine_id = f"{socket.gethostname()}_{getpass.getuser()}"
            salt = machine_id.encode()[:16].ljust(16, b'0')  # Padding 16 bytes
            
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(machine_id.encode()))
            return key
        except Exception:
            # Fallback key jika gagal generate dari hardware ID
            return base64.urlsafe_b64encode(b'fallback_key_32_bytes_length!!')

    @classmethod
    def _encrypt_data(cls, data: str) -> str:
        """Private: Enkripsi string data"""
        try:
            key = cls._generate_key_from_machine()
            f = Fernet(key)
            encrypted = f.encrypt(data.encode())
            return base64.urlsafe_b64encode(encrypted).decode()
        except Exception as e:
            print(f"⚠ Encryption failed: {e}")
            return data

    @classmethod
    def _decrypt_data(cls, encrypted_data: str) -> str:
        """Private: Dekripsi string data"""
        try:
            key = cls._generate_key_from_machine()
            f = Fernet(key)
            decoded = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted = f.decrypt(decoded)
            return decrypted.decode()
        except Exception as e:
            print(f"⚠ Decryption failed: {e}")
            return ""

    @classmethod
    def save_credentials(cls, username, password, method="auto"):
        """Simpan username/password ke Keyring atau File Terenkripsi"""
        try:
            # Logika pemilihan metode penyimpanan
            if method == "auto":
                method = "keyring" if KEYRING_AVAILABLE else "encrypted_file"
            
            # OPSI 1: Windows Credential Manager (Paling Aman)
            if method == "keyring" and KEYRING_AVAILABLE:
                keyring.set_password(APP_NAME, "username", username)
                keyring.set_password(APP_NAME, "password", password)
                keyring.set_password(APP_NAME, "remember", "true")
                print(f"🔐 Credentials saved securely in Windows Credential Manager")
                return True
                
            # OPSI 2: File JSON Terenkripsi
            elif method == "encrypted_file":
                credentials = {
                    "username": username,
                    "password": password,
                    "remember": True,
                    "method": "encrypted"
                }
                
                json_data = json.dumps(credentials)
                encrypted_data = cls._encrypt_data(json_data)
                
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

    @classmethod
    def load_credentials(cls):
        """Ambil username/password yang tersimpan"""
        try:
            # 1. Coba baca dari Keyring
            if KEYRING_AVAILABLE:
                try:
                    u = keyring.get_password(APP_NAME, "username")
                    p = keyring.get_password(APP_NAME, "password")
                    r = keyring.get_password(APP_NAME, "remember")
                    
                    if u and p and r == "true":
                        print(f"🔐 Loaded credentials from Windows Credential Manager")
                        return {
                            "username": u, 
                            "password": p, 
                            "remember": True, 
                            "method": "keyring"
                        }
                except Exception as e:
                    print(f"⚠ Failed to load from Credential Manager: {e}")
            
            # 2. Coba baca dari File Terenkripsi
            if os.path.exists(CREDENTIALS_FILE):
                try:
                    with open(CREDENTIALS_FILE, 'r') as f:
                        encrypted_data = f.read().strip()
                    
                    json_data = cls._decrypt_data(encrypted_data)
                    if json_data:
                        creds = json.loads(json_data)
                        print(f"🔐 Loaded encrypted credentials from file")
                        return creds
                except Exception as e:
                    print(f"⚠ Failed to load encrypted file: {e}")

            return None
            
        except Exception as e:
            print(f"❌ Error loading credentials: {e}")
            return None

    @staticmethod
    def clear_credentials():
        """Hapus semua data login yang tersimpan"""
        try:
            # Hapus Keyring
            if KEYRING_AVAILABLE:
                try:
                    keyring.delete_password(APP_NAME, "username")
                    keyring.delete_password(APP_NAME, "password")
                    keyring.delete_password(APP_NAME, "remember")
                except: pass # Abaikan jika memang tidak ada
            
            # Hapus File
            if os.path.exists(CREDENTIALS_FILE):
                os.remove(CREDENTIALS_FILE)
                
            print(f"🧹 Credentials cleared successfully")
            return True
        except Exception as e:
            print(f"❌ Error clearing credentials: {e}")
            return False