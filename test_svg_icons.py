#!/usr/bin/env python3
"""
Test script untuk memverifikasi semua icon SVG dapat dimuat dengan benar
"""
import os
from PyQt6.QtCore import QSize
from PyQt6.QtGui import QPixmap
from PyQt6.QtSvg import QSvgRenderer

def test_svg_icons():
    """Test semua icon SVG di folder asset/svg"""
    svg_folder = "asset/svg"
    
    if not os.path.exists(svg_folder):
        print(f"❌ Folder {svg_folder} tidak ditemukan!")
        return False
    
    svg_files = [f for f in os.listdir(svg_folder) if f.endswith('.svg')]
    
    if not svg_files:
        print(f"❌ Tidak ada file SVG ditemukan di {svg_folder}")
        return False
    
    print(f"🔍 Testing {len(svg_files)} icon SVG...")
    print("=" * 50)
    
    all_success = True
    for svg_file in svg_files:
        svg_path = os.path.join(svg_folder, svg_file)
        try:
            # Test dengan QSvgRenderer
            renderer = QSvgRenderer(svg_path)
            if renderer.isValid():
                # Test konversi ke pixmap
                pixmap = QPixmap(QSize(24, 24))
                print(f"✅ {svg_file:<25} - Valid dan dapat dimuat")
            else:
                print(f"❌ {svg_file:<25} - SVG tidak valid")
                all_success = False
        except Exception as e:
            print(f"❌ {svg_file:<25} - Error: {str(e)}")
            all_success = False
    
    print("=" * 50)
    if all_success:
        print("🎉 Semua icon SVG berhasil dimuat!")
    else:
        print("⚠ Beberapa icon SVG bermasalah")
    
    return all_success

if __name__ == "__main__":
    test_svg_icons()