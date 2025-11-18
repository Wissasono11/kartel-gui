#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KARTEL Dashboard Launcher
Quick launcher with dependency checking

Author: KARTEL Team
Created: November 17, 2025
"""

import sys
import os
import subprocess

def check_dependencies():
    """Check if required dependencies are installed"""
    required_packages = [
        ('PyQt5', 'PyQt5'),
        ('pyqtgraph', 'pyqtgraph'),
        ('numpy', 'numpy'),
        ('paho.mqtt', 'paho-mqtt')
    ]
    
    missing_packages = []
    
    for package, pip_name in required_packages:
        try:
            __import__(package)
            print(f"✓ {package} found")
        except ImportError:
            print(f"✗ {package} missing")
            missing_packages.append(pip_name)
    
    if missing_packages:
        print(f"\nMissing packages: {', '.join(missing_packages)}")
        print("Install them with:")
        print(f"pip install {' '.join(missing_packages)}")
        
        install = input("\nInstall missing packages now? (y/N): ")
        if install.lower() in ['y', 'yes']:
            try:
                subprocess.run([sys.executable, '-m', 'pip', 'install'] + missing_packages, 
                             check=True)
                print("✓ Packages installed successfully")
                return True
            except subprocess.CalledProcessError:
                print("✗ Failed to install packages")
                return False
        return False
    
    print("✓ All dependencies found")
    return True

def main():
    """Main launcher function"""
    print("=" * 50)
    print("KARTEL - Kendali Automasi Ruangan Telur")
    print("Dashboard Monitoring System")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        print("\nPlease install missing dependencies and try again.")
        return
    
    # Launch dashboard
    print("\n🚀 Launching KARTEL Dashboard...")
    
    try:
        from dashboard-gui import main as dashboard_main
        dashboard_main()
    except ImportError:
        # Fallback - run as subprocess
        script_path = os.path.join(os.path.dirname(__file__), 'dashboard-gui.py')
        subprocess.run([sys.executable, script_path])

if __name__ == "__main__":
    main()