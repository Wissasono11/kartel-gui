#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KARTEL Dashboard - Graph Components
Contains graph setup and management methods

Author: KARTEL Team
Created: November 28, 2025
"""

import os
import time
import pyqtgraph as pg
from datetime import datetime
from PyQt6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QSizePolicy
from PyQt6.QtGui import QColor
from PyQt6.QtCore import QSize, Qt


class DashboardGraphComponents:
    """Contains graph-related functionality"""
    
    def __init__(self, parent):
        self.parent = parent
    
    def create_graph_panel(self):
        """Create graph panel widget"""
        graph_widget_container = QFrame()
        graph_widget_container.setObjectName("graphCard")
        graph_widget_container.setMinimumHeight(380)
        graph_main_layout = QVBoxLayout(graph_widget_container)
        graph_main_layout.setContentsMargins(16, 16, 16, 20)
        
        # Judul
        title_layout = QHBoxLayout()
        icon_label = QLabel()
        from dashboard_ui_components import DashboardUIComponents
        ui_components = DashboardUIComponents(self.parent)
        icon_label.setPixmap(ui_components.load_svg_icon("graph.svg", QSize(40, 40)))
        
        title_label = QLabel("GRAFIK TREN (REAL-TIME)")
        title_label.setObjectName("sectionTitle")
        
        title_layout.addWidget(icon_label)
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        graph_main_layout.addLayout(title_layout)
        
        # Plot Widget
        self.parent.plot_widget = pg.PlotWidget()
        self.parent.plot_widget.setBackground('#ffffff')
        self.parent.plot_widget.setMenuEnabled(False)
        self.parent.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        self.parent.plot_widget.setMinimumHeight(280)
        self.parent.plot_widget.setSizePolicy(
            QSizePolicy.Policy.Expanding, 
            QSizePolicy.Policy.Expanding
        )

        # Initialize dengan data historis real yang ada
        hist_data = self.parent.controller.get_historical_data()
        self.initialize_graph_with_real_data(hist_data)
        
        # Setup plot
        self.setup_graph_plot()

        graph_main_layout.addWidget(self.parent.plot_widget)
        return graph_widget_container
    
    def initialize_graph_with_real_data(self, hist_data):
        """Initialize graph dengan data historis real dari sensor"""
        # Jika tidak ada data historis, mulai dengan data kosong
        if not hist_data["temperature"] or not hist_data["humidity"]:
            print("📊 Tidak ada data historis, graph dimulai kosong - menunggu data real dari sensor")
            return
            
        current_time = time.time()
        
        # Gunakan timestamp yang ada dari data historis atau buat jika tidak ada
        if hist_data.get("timestamps"):
            # Gunakan timestamp real dari data historis
            for i, (timestamp, temp, humidity) in enumerate(zip(
                hist_data["timestamps"], 
                hist_data["temperature"], 
                hist_data["humidity"]
            )):
                self.parent.graph_data["timestamps"].append(timestamp)
                self.parent.graph_data["temperature"].append(temp)
                self.parent.graph_data["humidity"].append(humidity)
        else:
            # Fallback: buat timestamp mundur dari waktu sekarang
            for i, (temp, humidity) in enumerate(zip(hist_data["temperature"], hist_data["humidity"])):
                timestamp = current_time - (len(hist_data["temperature"]) - i - 1) * 300  # 5 menit interval
                self.parent.graph_data["timestamps"].append(timestamp)
                self.parent.graph_data["temperature"].append(temp)
                self.parent.graph_data["humidity"].append(humidity)
        
        print(f"📊 Graph diinisialisasi dengan {len(hist_data['temperature'])} data point historis real")
    
    def setup_graph_plot(self):
        """Setup the graph plotting elements"""
        # Setup axes ranges berdasarkan rentang yang diizinkan
        self.parent.plot_widget.setYRange(20, 50)  # Temperature range: 20-50°C
        
        # Add some margin for bottom axis labels
        self.parent.plot_widget.plotItem.setContentsMargins(10, 10, 10, 25)  # Extra bottom margin
        
        # Setup X axis (time labels)
        self.update_x_axis()

        # Setup Y axis left (Temperature)
        ax_left = self.parent.plot_widget.getAxis('left')
        ax_left.setLabel("Suhu (°C)", color="#FFC107")
        ax_left.setTextPen(QColor("#FFC107"))

        # Create temperature plot line
        self.parent.temp_plot = self.parent.plot_widget.plot(
            [], [], 
            pen=pg.mkPen(color="#FFC107", width=3),
            symbol='o', symbolSize=6, symbolBrush='#FFC107',
            name="Suhu"
        )

        # Create second ViewBox for humidity dengan range yang sesuai
        self.parent.view_box_2 = pg.ViewBox()
        self.parent.plot_widget.plotItem.scene().addItem(self.parent.view_box_2)
        self.parent.view_box_2.setYRange(60, 80)  # Humidity range: 60-80%

        # Setup Y axis right (Humidity)
        ax_right = pg.AxisItem('right')
        ax_right.setLabel("Kelembaban (%)", color="#5A3FFF")
        ax_right.setTextPen(QColor("#5A3FFF"))
        ax_right.linkToView(self.parent.view_box_2)
        
        self.parent.plot_widget.plotItem.layout.addItem(ax_right, 2, 3)
        self.parent.view_box_2.linkView(pg.ViewBox.XAxis, self.parent.plot_widget.plotItem.getViewBox())

        # Create humidity plot elements
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

        # Setup tooltip
        self.setup_graph_tooltip()
        
        # Update view when resized
        def update_views():
            self.parent.view_box_2.setGeometry(self.parent.plot_widget.plotItem.vb.sceneBoundingRect())
        
        self.parent.plot_widget.plotItem.vb.sigResized.connect(update_views)
        
        # Initial plot
        self.update_graph_plot()
        update_views()
    
    def setup_graph_tooltip(self):
        """Setup interactive tooltip for graph"""
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

        # Mouse move event for tooltip
        def on_mouse_move(event):
            if self.parent.plot_widget.sceneBoundingRect().contains(event):
                mouse_pos = self.parent.plot_widget.plotItem.vb.mapSceneToView(event)
                x_pos = int(mouse_pos.x())
                
                if 0 <= x_pos < len(self.parent.graph_data["temperature"]):
                    timestamp = self.parent.graph_data["timestamps"][x_pos]
                    time_str = datetime.fromtimestamp(timestamp).strftime("%H:%M")
                    temp_val = self.parent.graph_data["temperature"][x_pos]
                    humidity_val = self.parent.graph_data["humidity"][x_pos]
                    
                    tooltip_text = f"""<div style="color: #6b7280; font-size: 11px; margin-bottom: 4px;">{time_str}</div>
<div style="color: #5A3FFF;">Kelembaban: {humidity_val}%</div>
<div style="color: #FFC107;">Suhu: {temp_val}°C</div>"""
                    
                    self.parent.tooltip.setText(tooltip_text)
                    self.parent.tooltip.adjustSize()
                    
                    # Position tooltip
                    try:
                        tooltip_pos = self.parent.plot_widget.mapFromScene(event)
                        self.parent.tooltip.move(tooltip_pos.x() + 10, tooltip_pos.y() - 60)
                        self.parent.tooltip.show()
                    except:
                        pass
                else:
                    self.parent.tooltip.hide()
            else:
                self.parent.tooltip.hide()

        self.parent.plot_widget.scene().sigMouseMoved.connect(on_mouse_move)
    
    def update_x_axis(self):
        """Update X axis with time labels"""
        if not self.parent.graph_data["timestamps"]:
            return
            
        # Create time labels
        time_labels = []
        x_positions = []
        
        for i, timestamp in enumerate(self.parent.graph_data["timestamps"]):
            time_str = datetime.fromtimestamp(timestamp).strftime("%H:%M")
            time_labels.append(time_str)
            x_positions.append(i)
        
        # Update X axis ticks
        x_ticks = [list(zip(x_positions, time_labels))]
        ax_bottom = self.parent.plot_widget.getAxis('bottom')
        ax_bottom.setTicks(x_ticks)
        ax_bottom.setTextPen(QColor("#6b7280"))
        
        # Set X range
        if len(x_positions) > 1:
            self.parent.plot_widget.setXRange(-0.5, len(x_positions) - 0.5)
    
    def update_graph_plot(self):
        """Update the graph with current data"""
        if not self.parent.graph_data["temperature"]:
            return
            
        # Create x-axis positions
        x_data = list(range(len(self.parent.graph_data["temperature"])))
        
        # Update temperature plot
        self.parent.temp_plot.setData(x_data, self.parent.graph_data["temperature"])
        
        # Update humidity plot
        self.parent.humidity_plot.setData(x_data, self.parent.graph_data["humidity"])
        self.parent.humidity_symbol.setData(x_data, self.parent.graph_data["humidity"])
        
        # Update X axis
        self.update_x_axis()
        
        # Update humidity ViewBox range
        self.parent.view_box_2.setXRange(-0.5, len(x_data) - 0.5)