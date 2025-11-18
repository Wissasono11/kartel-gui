"""
KARTEL Dashboard Styling Module
Modul untuk memuat dan mengelola stylesheet dari file eksternal
"""

import os
from pathlib import Path

def load_stylesheet(file_path="styles.qss"):
    """
    Memuat stylesheet dari file QSS eksternal
    
    Args:
        file_path (str): Path ke file QSS, default "styles.qss"
        
    Returns:
        str: Konten stylesheet atau string kosong jika file tidak ditemukan
    """
    try:
        # Dapatkan direktori script saat ini
        current_dir = Path(__file__).parent
        
        # Coba beberapa lokasi untuk file stylesheet
        possible_paths = [
            current_dir / file_path,                    # Root folder
            current_dir / "asset" / "style" / file_path, # Asset/style folder
            current_dir / "asset" / file_path,           # Asset folder
            current_dir / "style" / file_path            # Style folder
        ]
        
        for style_file in possible_paths:
            if style_file.exists():
                # Baca file stylesheet
                with open(style_file, 'r', encoding='utf-8') as file:
                    stylesheet = file.read()
                    
                print(f"✅ Stylesheet berhasil dimuat dari: {style_file}")
                return stylesheet
        
        # Jika tidak ada yang ditemukan
        raise FileNotFoundError(f"File tidak ditemukan di semua lokasi yang dicoba")
        
    except FileNotFoundError:
        print(f"⚠ File stylesheet tidak ditemukan: {file_path}")
        print("   Lokasi yang dicoba:")
        for path in possible_paths:
            print(f"   - {path}")
        print("Menggunakan style default...")
        return ""
        
    except Exception as e:
        print(f"⚠ Error saat memuat stylesheet: {e}")
        return ""

def get_default_stylesheet():
    """
    Fallback stylesheet jika file eksternal tidak tersedia
    
    Returns:
        str: Basic stylesheet
    """
    return """
    QWidget {
        font-family: 'Manrope', 'Arial', sans-serif;
        font-size: 14px;
        color: #374151;
    }
    
    KartelDashboard {
        background-color: #f8f9fa;
    }
    """