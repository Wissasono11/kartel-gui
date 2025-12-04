import json
import os
from datetime import datetime

class DataStore:
    """
    Service khusus untuk menangani penyimpanan data persisten (File JSON).
    Fokus: Save/Load data inkubasi agar tidak hilang saat aplikasi ditutup.
    """
    
    def __init__(self, filename="data/incubation_data.json"):
        # Kita simpan di folder 'data' agar rapi
        self.filename = filename
        self._ensure_data_dir()
        
    def _ensure_data_dir(self):
        """Pastikan folder data tersedia"""
        directory = os.path.dirname(self.filename)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)

    def load_incubation_data(self):
        """Muat data tanggal mulai inkubasi"""
        try:
            if os.path.exists(self.filename):
                with open(self.filename, 'r') as f:
                    data = json.load(f)
                    start_date_str = data.get('start_date')
                    
                    if start_date_str:
                        return datetime.fromisoformat(start_date_str)
            return None
        except Exception as e:
            print(f"⚠️ Error loading incubation data: {e}")
            return None

    def save_incubation_data(self, start_date, total_days):
        """Simpan data inkubasi ke file"""
        try:
            data = {
                'start_date': start_date.isoformat() if start_date else None,
                'total_days': total_days,
                'last_updated': datetime.now().isoformat()
            }
            with open(self.filename, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"💾 Incubation data saved to {self.filename}")
            return True
        except Exception as e:
            print(f"❌ Error saving incubation data: {e}")
            return False

    def reset_data(self):
        """Hapus file data (Reset Batch)"""
        try:
            if os.path.exists(self.filename):
                os.remove(self.filename)
            return True
        except Exception as e:
            print(f"❌ Error resetting data: {e}")
            return False