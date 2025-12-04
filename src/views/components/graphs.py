import time
import pyqtgraph as pg
from datetime import datetime
from PyQt6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QSizePolicy
from PyQt6.QtGui import QColor
from PyQt6.QtCore import QSize

# Import Widgets untuk meminjam fungsi load_svg_icon
from src.views.components.widgets import DashboardWidgets

class DashboardGraphs:
    """
    Komponen khusus untuk menangani Grafik PyQtGraph.
    Memisahkan logika plotting yang berat dari UI utama.
    """
    
    def __init__(self, main_window):
        # Kita sebut main_window agar jelas (karena dia parentnya)
        self.parent = main_window
    
    def create_graph_panel(self):
        """Buat widget panel grafik"""
        graph_widget_container = QFrame()
        graph_widget_container.setObjectName("graphCard")
        graph_widget_container.setMinimumHeight(380)
        graph_main_layout = QVBoxLayout(graph_widget_container)
        graph_main_layout.setContentsMargins(16, 16, 16, 20)
        
        # --- Bagian Judul ---
        title_layout = QHBoxLayout()
        icon_label = QLabel()
        
        # Menggunakan Helper dari DashboardWidgets untuk load icon
        # Kita inisialisasi sementara hanya untuk akses fungsi load_svg_icon
        widgets_helper = DashboardWidgets(self.parent)
        icon_label.setPixmap(widgets_helper.load_svg_icon("graph.svg", QSize(40, 40)))
        
        title_label = QLabel("GRAFIK TREN (REAL-TIME)")
        title_label.setObjectName("sectionTitle")
        
        title_layout.addWidget(icon_label)
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        graph_main_layout.addLayout(title_layout)
        
        # --- Bagian Plotting ---
        self.parent.plot_widget = pg.PlotWidget()
        self.parent.plot_widget.setBackground('#ffffff')
        self.parent.plot_widget.setMenuEnabled(False)
        self.parent.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        self.parent.plot_widget.setMinimumHeight(280)
        self.parent.plot_widget.setSizePolicy(
            QSizePolicy.Policy.Expanding, 
            QSizePolicy.Policy.Expanding
        )

        # Inisialisasi dengan data historis (Mengambil dari Controller)
        # Pastikan controller sudah terpasang di parent sebelum memanggil ini
        if hasattr(self.parent, 'controller'):
            hist_data = self.parent.controller.get_historical_data()
            self.initialize_graph_with_real_data(hist_data)
        
        # Pengaturan plot style
        self.setup_graph_plot()

        graph_main_layout.addWidget(self.parent.plot_widget)
        return graph_widget_container
    
    def initialize_graph_with_real_data(self, hist_data):
        """Inisialisasi grafik dengan data historis real dari sensor"""
        if not hist_data or not hist_data.get("temperature") or not hist_data.get("humidity"):
            return
            
        current_time = time.time()
        
        # Pastikan parent memiliki variable penampung data grafik
        # (Nanti kita pastikan ini ada di Main Window)
        if not hasattr(self.parent, 'graph_data'):
            self.parent.graph_data = {"timestamps": [], "temperature": [], "humidity": []}

        # Gunakan timestamp yang ada dari data historis atau buat jika tidak ada
        if hist_data.get("timestamps"):
            for timestamp, temp, humidity in zip(
                hist_data["timestamps"], 
                hist_data["temperature"], 
                hist_data["humidity"]
            ):
                self.parent.graph_data["timestamps"].append(timestamp)
                self.parent.graph_data["temperature"].append(temp)
                self.parent.graph_data["humidity"].append(humidity)
        else:
            # Fallback: buat timestamp mundur
            count = len(hist_data["temperature"])
            for i, (temp, humidity) in enumerate(zip(hist_data["temperature"], hist_data["humidity"])):
                timestamp = current_time - (count - i - 1) * 300  # Interval 5 menit
                self.parent.graph_data["timestamps"].append(timestamp)
                self.parent.graph_data["temperature"].append(temp)
                self.parent.graph_data["humidity"].append(humidity)
        
        print(f"📊 Graph initialized with {len(hist_data['temperature'])} points")
    
    def setup_graph_plot(self):
        """Pengaturan elemen plotting grafik"""
        # Rentang Suhu: 20-50°C
        self.parent.plot_widget.setYRange(20, 50)
        self.parent.plot_widget.plotItem.setContentsMargins(10, 10, 10, 25)
        
        self.update_x_axis()

        # Sumbu Y Kiri (Suhu)
        ax_left = self.parent.plot_widget.getAxis('left')
        ax_left.setLabel("Suhu (°C)", color="#FFC107")
        ax_left.setTextPen(QColor("#FFC107"))

        # Garis Plot Suhu
        self.parent.temp_plot = self.parent.plot_widget.plot(
            [], [], 
            pen=pg.mkPen(color="#FFC107", width=3),
            symbol='o', symbolSize=6, symbolBrush='#FFC107',
            name="Suhu"
        )

        # ViewBox kedua untuk Kelembaban
        self.parent.view_box_2 = pg.ViewBox()
        self.parent.plot_widget.plotItem.scene().addItem(self.parent.view_box_2)
        self.parent.view_box_2.setYRange(60, 80) 

        # Sumbu Y Kanan (Kelembaban)
        ax_right = pg.AxisItem('right')
        ax_right.setLabel("Kelembaban (%)", color="#5A3FFF")
        ax_right.setTextPen(QColor("#5A3FFF"))
        ax_right.linkToView(self.parent.view_box_2)
        
        self.parent.plot_widget.plotItem.layout.addItem(ax_right, 2, 3)
        self.parent.view_box_2.linkView(pg.ViewBox.XAxis, self.parent.plot_widget.plotItem.getViewBox())

        # Elemen Plot Kelembaban
        self.parent.humidity_plot = pg.PlotCurveItem(
            [], [],
            pen=pg.mkPen(color="#5A3FFF", width=3),
        )
        self.parent.humidity_symbol = pg.ScatterPlotItem(
            [], [],
            symbol='o', size=6, brush='#5A3FFF'
        )
        self.parent.view_box_2.addItem(self.parent.humidity_plot)
        self.parent.view_box_2.addItem(self.parent.humidity_symbol)

        # Tooltip Setup
        self.setup_graph_tooltip()
        
        # Resize Handler
        def update_views():
            self.parent.view_box_2.setGeometry(self.parent.plot_widget.plotItem.vb.sceneBoundingRect())
        
        self.parent.plot_widget.plotItem.vb.sigResized.connect(update_views)
        
        self.update_graph_plot()
        update_views()
    
    def setup_graph_tooltip(self):
        """Pengaturan tooltip interaktif"""
        self.parent.tooltip = QLabel(self.parent.plot_widget)
        self.parent.tooltip.setStyleSheet("""
            QLabel {
                background-color: rgba(255, 255, 255, 0.95);
                border: 1px solid #e5e7eb;
                border-radius: 8px;
                padding: 8px 12px;
                color: #374151;
                font-size: 12px;
                font-weight: 600;
            }
        """)
        self.parent.tooltip.hide()

        def on_mouse_move(event):
            if self.parent.plot_widget.sceneBoundingRect().contains(event):
                mouse_pos = self.parent.plot_widget.plotItem.vb.mapSceneToView(event)
                x_pos = int(mouse_pos.x())
                
                # Cek apakah index valid
                if hasattr(self.parent, 'graph_data') and \
                   0 <= x_pos < len(self.parent.graph_data["temperature"]):
                    
                    timestamp = self.parent.graph_data["timestamps"][x_pos]
                    time_str = datetime.fromtimestamp(timestamp).strftime("%H:%M")
                    temp_val = self.parent.graph_data["temperature"][x_pos]
                    humidity_val = self.parent.graph_data["humidity"][x_pos]
                    
                    tooltip_text = f"""<div style="color: #6b7280; font-size: 11px; margin-bottom: 4px;">{time_str}</div>
<div style="color: #5A3FFF;">Kelembaban: {humidity_val}%</div>
<div style="color: #FFC107;">Suhu: {temp_val}°C</div>"""
                    
                    self.parent.tooltip.setText(tooltip_text)
                    self.parent.tooltip.adjustSize()
                    
                    try:
                        tooltip_pos = self.parent.plot_widget.mapFromScene(event)
                        self.parent.tooltip.move(tooltip_pos.x() + 10, tooltip_pos.y() - 60)
                        self.parent.tooltip.show()
                    except: pass
                else:
                    self.parent.tooltip.hide()
            else:
                self.parent.tooltip.hide()

        self.parent.plot_widget.scene().sigMouseMoved.connect(on_mouse_move)
    
    def update_x_axis(self):
        """Perbarui sumbu X dengan label waktu"""
        if not hasattr(self.parent, 'graph_data') or not self.parent.graph_data["timestamps"]:
            return
            
        time_labels = []
        x_positions = []
        
        for i, timestamp in enumerate(self.parent.graph_data["timestamps"]):
            time_str = datetime.fromtimestamp(timestamp).strftime("%H:%M")
            time_labels.append(time_str)
            x_positions.append(i)
        
        x_ticks = [list(zip(x_positions, time_labels))]
        ax_bottom = self.parent.plot_widget.getAxis('bottom')
        ax_bottom.setTicks(x_ticks)
        ax_bottom.setTextPen(QColor("#6b7280"))
        
        if len(x_positions) > 1:
            self.parent.plot_widget.setXRange(-0.5, len(x_positions) - 0.5)
    
    def update_graph_plot(self):
        """Perbarui grafik dengan data saat ini"""
        if not hasattr(self.parent, 'graph_data') or not self.parent.graph_data["temperature"]:
            return
            
        x_data = list(range(len(self.parent.graph_data["temperature"])))
        
        self.parent.temp_plot.setData(x_data, self.parent.graph_data["temperature"])
        
        self.parent.humidity_plot.setData(x_data, self.parent.graph_data["humidity"])
        self.parent.humidity_symbol.setData(x_data, self.parent.graph_data["humidity"])
        
        self.update_x_axis()
        self.parent.view_box_2.setXRange(-0.5, len(x_data) - 0.5)