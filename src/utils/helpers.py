# File: src/utils/helpers.py
import sys
import os

def resource_path(relative_path):
    """ Dapatkan path absolut ke resource untuk PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)