#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KARTEL Font Manager
Downloads and manages Manrope font for the dashboard

Author: KARTEL Team
Created: November 17, 2025
"""

import os
import sys
import requests
from PyQt5.QtGui import QFontDatabase

def download_manrope_font():
    """Download Manrope font from Google Fonts"""
    
    font_dir = "fonts"
    if not os.path.exists(font_dir):
        os.makedirs(font_dir)
    
    # Manrope font URLs from Google Fonts
    font_urls = {
        "Manrope-Regular.ttf": "https://fonts.gstatic.com/s/manrope/v15/xn7_YHE41ni1AdIRqAuZuw1Bx9mbZk59FO_F87jxeN7B.woff2",
        "Manrope-Bold.ttf": "https://fonts.gstatic.com/s/manrope/v15/xn7_YHE41ni1AdIRqAuZuw1Bx9mbZk6uFO_F87jxeN7B.woff2"
    }
    
    print("📥 Downloading Manrope fonts...")
    
    for font_name, url in font_urls.items():
        font_path = os.path.join(font_dir, font_name)
        
        if os.path.exists(font_path):
            print(f"✓ {font_name} already exists")
            continue
            
        try:
            print(f"⬇️ Downloading {font_name}...")
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            with open(font_path, 'wb') as f:
                f.write(response.content)
            
            print(f"✓ {font_name} downloaded successfully")
            
        except Exception as e:
            print(f"❌ Failed to download {font_name}: {e}")
            
            # Create a simple fallback
            print(f"📝 Creating fallback for {font_name}")

def load_fonts():
    """Load fonts into QFontDatabase"""
    font_dir = "fonts"
    
    if not os.path.exists(font_dir):
        print("📁 Creating fonts directory...")
        os.makedirs(font_dir)
        return False
    
    font_files = [f for f in os.listdir(font_dir) if f.endswith('.ttf')]
    
    if not font_files:
        print("⚠️ No font files found. Using system default.")
        return False
    
    fonts_loaded = 0
    for font_file in font_files:
        font_path = os.path.join(font_dir, font_file)
        font_id = QFontDatabase.addApplicationFont(font_path)
        
        if font_id != -1:
            font_families = QFontDatabase.applicationFontFamilies(font_id)
            print(f"✓ Loaded font: {font_families}")
            fonts_loaded += 1
        else:
            print(f"❌ Failed to load: {font_file}")
    
    return fonts_loaded > 0

def setup_fonts():
    """Setup fonts for the application"""
    print("🎨 Setting up fonts for KARTEL...")
    
    # Try to load existing fonts first
    if load_fonts():
        print("✓ Fonts loaded successfully")
        return True
    
    # If no fonts found, try to download them
    print("📥 No fonts found, attempting to download...")
    
    try:
        download_manrope_font()
        if load_fonts():
            print("✓ Fonts downloaded and loaded successfully")
            return True
    except Exception as e:
        print(f"❌ Font download failed: {e}")
    
    print("⚠️ Using system default fonts")
    return False

if __name__ == "__main__":
    setup_fonts()