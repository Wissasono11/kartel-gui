import sys
import os
import signal
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont
import pyqtgraph as pg

# Tambahkan path root ke sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.views.main_window import KartelMainWindow

def main():
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