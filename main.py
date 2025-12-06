import sys
import os
import signal
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont
from PyQt6.QtCore import qInstallMessageHandler, QtMsgType # <--- Import ini
import pyqtgraph as pg

# Tambahkan path root ke sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.views.main_window import KartelMainWindow

# =========================================================
# HANDLER UNTUK MEMBISUKAN WARNING QT YANG MENGGANGGU
# =========================================================
def qt_message_handler(mode, context, message):
    # Jika pesan berisi error font spesifik ini, abaikan (jangan print)
    if "QFont::setPointSize" in message:
        return
    
    # Jika pesan berisi peringatan layout yang sering muncul tapi tidak fatal
    if "QWindowsWindow::setGeometry" in message:
        return

    # Untuk pesan lain, tetap tampilkan agar kita tahu jika ada error serius
    msg_type_str = {
        QtMsgType.QtDebugMsg: "[Qt Debug]",
        QtMsgType.QtInfoMsg: "[Qt Info]",
        QtMsgType.QtWarningMsg: "[Qt Warning]",
        QtMsgType.QtCriticalMsg: "[Qt Critical]",
        QtMsgType.QtFatalMsg: "[Qt Fatal]"
    }.get(mode, "[Qt Unknown]")
    
    print(f"{msg_type_str}: {message}")

def main():
    # Pasang handler kustom KITA SEBELUM membuat QApplication
    qInstallMessageHandler(qt_message_handler) # <--- Pasang di sini

    # Setup PyqtGraph
    pg.setConfigOptions(antialias=True)
    
    # Enable CTRL+C
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    
    app = QApplication(sys.argv)
    
    # Set Font Default
    app.setFont(QFont("Manrope", 10))
    
    # Init Window
    window = KartelMainWindow()
    window.show()
    
    try:
        sys.exit(app.exec())
    except KeyboardInterrupt:
        sys.exit(0)

if __name__ == "__main__":
    main()