import sys
import os
import pyqtgraph as pg
import qtawesome as qta
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, 
    QLineEdit, QPushButton, QComboBox, QScrollArea, QSpacerItem, 
    QSizePolicy, QGridLayout
)
from PyQt6.QtGui import QFont, QPixmap, QIcon, QFontDatabase, QColor, QPainter
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtSvg import QSvgRenderer

class KartelDashboard(QWidget):
    def __init__(self):
        super().__init__()
        self.load_custom_fonts()  # Load font sebelum init UI
        self.init_ui()
    
    def load_svg_icon(self, svg_filename, size=QSize(24, 24)):
        """Load SVG icon dengan warna asli tanpa customisasi"""
        svg_path = f"asset/svg/{svg_filename}"
        if os.path.exists(svg_path):
            renderer = QSvgRenderer(svg_path)
            pixmap = QPixmap(size)
            pixmap.fill(Qt.GlobalColor.transparent)
            
            painter = QPainter(pixmap)
            renderer.render(painter)
            painter.end()
            
            return pixmap
        else:
            # Fallback ke qtawesome jika SVG tidak ditemukan
            print(f"⚠ SVG icon tidak ditemukan: {svg_path}, menggunakan fallback")
            return qta.icon("fa5s.question", color="#666666").pixmap(size)
    
    def load_custom_fonts(self):
        """Load font Manrope dari berbagai sumber"""
        
        # Test apakah font Manrope tersedia di sistem
        test_font = QFont("Manrope", 12)
        if test_font.exactMatch():
            print("✅ Font Manrope ditemukan di sistem!")
            return True
        
        # Jika tidak ada di sistem, coba load dari file lokal
        font_loaded = False
        font_paths = [
            "fonts/Manrope-Regular.ttf",
            "fonts/Manrope.ttf", 
            "asset/fonts/Manrope-Regular.ttf",
            "Manrope-Regular.ttf"
        ]
        
        for font_path in font_paths:
            if os.path.exists(font_path):
                font_id = QFontDatabase.addApplicationFont(font_path)
                if font_id != -1:
                    families = QFontDatabase.applicationFontFamilies(font_id)
                    print(f"✅ Font Manrope berhasil dimuat dari: {font_path}")
                    print(f"   Font families: {families}")
                    font_loaded = True
                    break
        
        if not font_loaded:
            print("⚠ Font Manrope tidak ditemukan dalam file lokal")
            print("  Namun font mungkin tersedia di sistem - CSS fallback akan digunakan")
        
        return font_loaded
        
    def init_ui(self):
        # Pengaturan Jendela Utama
        self.setWindowTitle("KARTEL Dashboard")
        self.setGeometry(100, 100, 1400, 900) # Atur ukuran jendela
        
        # Layout Utama
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(24)

        # === KOLOM KIRI ===
        left_column = QWidget()
        left_layout = QVBoxLayout(left_column)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(20)

        # 1. Header
        left_layout.addWidget(self.create_header())
        
        # 2. Card Vital (Suhu & Kelembaban)
        left_layout.addWidget(self.create_vital_cards())
        
        # 3. Status Sistem
        left_layout.addWidget(self.create_status_system())
        
        # 4. Grafik Tren
        left_layout.addWidget(self.create_graph_panel())
        
        left_layout.addStretch() # Mendorong semua konten ke atas

        # === KOLOM KANAN (Konfigurasi) ===
        right_column = self.create_config_panel()
        
        # Tambahkan kolom ke layout utama
        main_layout.addWidget(left_column, 7) # Kolom kiri mengambil 70%
        main_layout.addWidget(right_column, 3) # Kolom kanan mengambil 30%

        # Terapkan Stylesheet
        self.set_stylesheet()

    # --- 1. Widget Header ---
    def create_header(self):
        header_widget = QFrame()
        header_widget.setObjectName("headerCard") # Beri nama untuk styling
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)

        # Logo dan Judul - dengan pengecekan file
        logo_label = QLabel()
        logo_path = "asset/img/kartel-logo.png"
        if os.path.exists(logo_path):
            logo_pixmap = QPixmap(logo_path)
            if not logo_pixmap.isNull():
                logo_label.setPixmap(logo_pixmap.scaled(64, 64, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            else:
                # Gunakan ikon default jika logo corrupt
                logo_label.setPixmap(qta.icon("fa5s.cube", color="#4f46e5").pixmap(QSize(60, 60)))
        else:
            # Gunakan ikon default jika logo tidak ada
            logo_label.setPixmap(qta.icon("fa5s.cube", color="#4f46e5").pixmap(QSize(60, 60)))

        title_layout = QVBoxLayout()
        title_layout.setSpacing(0)
        title_label = QLabel("KARTEL")
        title_label.setObjectName("headerTitle")
        subtitle_label = QLabel("Kendali Automasi Ruangan Telur")
        subtitle_label.setObjectName("headerSubtitle")
        title_layout.addWidget(title_label)
        title_layout.addWidget(subtitle_label)

        header_layout.addWidget(logo_label)
        header_layout.addLayout(title_layout)
        header_layout.addStretch()

        # Tombol Status
        status_connect_btn = QPushButton(" Tidak Terhubung")
        status_connect_btn.setIcon(QIcon(self.load_svg_icon("wifi.svg", QSize(20, 20))))
        status_connect_btn.setObjectName("statusNotConnected")

        status_day_btn = QPushButton(" Hari ke- 3 dari 21")
        status_day_btn.setIcon(QIcon(self.load_svg_icon("calendar.svg", QSize(20, 20))))
        status_day_btn.setObjectName("statusDay")
        
        header_layout.addWidget(status_connect_btn)
        header_layout.addWidget(status_day_btn)
        
        return header_widget

    # --- 2. Widget Card Vital ---
    def create_vital_cards(self):
        vitals_widget = QWidget()
        vitals_layout = QHBoxLayout(vitals_widget)
        vitals_layout.setContentsMargins(0, 0, 0, 0)
        vitals_layout.setSpacing(20)
        
        # Card Suhu
        vitals_layout.addWidget(
            self.create_single_vital_card(
                icon_svg="temperature.svg",
                icon_size=QSize(50, 50),
                title="SUHU",
                current_value="36.2°C",
                target_value="38.4°C",
                description="Setpoint yang diinginkan",
                object_name="suhuCard"
            )
        )
        
        # Card Kelembaban
        vitals_layout.addWidget(
            self.create_single_vital_card(
                icon_svg="humidity.svg",
                icon_size=QSize(50, 50),
                title="KELEMBABAN",
                current_value="58.5%",
                target_value="60%",
                description="Setpoint yang diinginkan",
                object_name="kelembabanCard"
            )
        )
        return vitals_widget

    def create_single_vital_card(self, icon_svg, icon_size, title, current_value, target_value, description, object_name):
        card = QFrame()
        card.setObjectName(object_name)
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(4)

        # Baris Judul
        title_layout = QHBoxLayout()
        icon_label = QLabel()
        icon_label.setPixmap(self.load_svg_icon(icon_svg, icon_size))
        
        title_label = QLabel(title)
        title_label.setObjectName("vitalTitle")
        title_layout.addWidget(icon_label)
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        card_layout.addLayout(title_layout)

        # Nilai Saat Ini
        current_desc_label = QLabel(f"{title.capitalize()} saat ini")
        current_desc_label.setObjectName("vitalCurrentDesc")
        
        current_value_label = QLabel(current_value)
        current_value_label.setObjectName("vitalCurrentValue")
        
        card_layout.addWidget(current_desc_label)
        card_layout.addWidget(current_value_label)
        card_layout.addSpacing(10)

        # Target (di dalam box terpisah)
        target_box = QFrame()
        target_box.setObjectName("targetBox")
        target_box_layout = QVBoxLayout(target_box)
        target_box_layout.setContentsMargins(12, 8, 12, 8)
        
        target_label = QLabel(f"Target: {target_value}")
        target_label.setObjectName("vitalTarget")
        
        target_desc_label = QLabel(description)
        target_desc_label.setObjectName("vitalTargetDesc")
        
        target_box_layout.addWidget(target_label)
        target_box_layout.addWidget(target_desc_label)
        
        card_layout.addWidget(target_box)
        
        return card

    # --- 3. Widget Status Sistem ---
    def create_status_system(self):
        status_widget_container = QWidget()
        status_main_layout = QVBoxLayout(status_widget_container)
        status_main_layout.setContentsMargins(0, 0, 0, 0)
        status_main_layout.setSpacing(10)

        # Judul "STATUS SISTEM"
        title_layout = QHBoxLayout()
        icon_label = QLabel()
        icon_label.setPixmap(self.load_svg_icon("status-system.svg", QSize(40, 40)))
        
        title_label = QLabel("STATUS SISTEM")
        title_label.setObjectName("sectionTitle")
        
        title_layout.addWidget(icon_label)
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        status_main_layout.addLayout(title_layout)

        # 4 Kartu Status
        status_cards_widget = QWidget()
        status_cards_layout = QHBoxLayout(status_cards_widget)
        status_cards_layout.setContentsMargins(0, 0, 0, 0)
        status_cards_layout.setSpacing(15)

        status_cards_layout.addWidget(
            self.create_single_status_card("pemanas.svg", "Pemanas", "Aktif", "statusAktif")
        )
        status_cards_layout.addWidget(
            self.create_single_status_card("humidifier.svg", "Humidifier", "Non-aktif", "statusNonAktif")
        )
        status_cards_layout.addWidget(
            self.create_single_status_card("motor-dinamo.svg", "Motor Pembalik", "Menunggu", "statusMenunggu")
        )
        status_cards_layout.addWidget(
            self.create_single_status_card("sand-clock.svg", "Putaran Berikutnya", "2:30:15", "statusTimer")
        )
        
        status_main_layout.addWidget(status_cards_widget)
        return status_widget_container

    def create_single_status_card(self, icon_svg, title, status_text, status_style_name):
        card = QFrame()
        card.setObjectName("statusCard")
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(15)

        # Ikon dan Judul
        icon_title_layout = QHBoxLayout()
        icon_label = QLabel()
        icon_label.setPixmap(self.load_svg_icon(icon_svg, QSize(40, 40)))
        icon_label.setObjectName("statusCardIcon")
        
        title_label = QLabel(title)
        title_label.setObjectName("statusCardTitle")
        
        icon_title_layout.addWidget(icon_label)
        icon_title_layout.addWidget(title_label)
        icon_title_layout.addStretch()
        
        card_layout.addLayout(icon_title_layout)

        # Status Label
        status_label = QLabel(status_text)
        status_label.setObjectName(status_style_name)
        status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        card_layout.addWidget(status_label)
        return card

    # --- 4. Widget Grafik ---
    def create_graph_panel(self):
        graph_widget_container = QFrame()
        graph_widget_container.setObjectName("graphCard")
        graph_main_layout = QVBoxLayout(graph_widget_container)
        
        # Judul
        title_layout = QHBoxLayout()
        icon_label = QLabel()
        icon_label.setPixmap(self.load_svg_icon("graph.svg", QSize(40, 40)))
        
        title_label = QLabel("GRAFIK TREN (24 JAM TERAKHIR)")
        title_label.setObjectName("sectionTitle")
        
        title_layout.addWidget(icon_label)
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        graph_main_layout.addLayout(title_layout)
        
        # Plot Widget dengan tooltip
        plot_widget = pg.PlotWidget()
        plot_widget.setBackground('#ffffff')  # Background putih
        plot_widget.setMenuEnabled(False)  # Sembunyikan menu klik kanan
        plot_widget.showGrid(x=True, y=True, alpha=0.3)

        # Data Contoh (disesuaikan dengan format gambar)
        hours = list(range(20, 24)) + list(range(0, 19))  # 20-23, 00-18
        time_labels = [f"{h:02d}.22" for h in hours]
        x_data = list(range(len(hours)))  # Index untuk plotting
        suhu_data = [37.8, 37.8, 38.0, 38.1, 38.2, 38.5, 38.7, 38.8, 38.5, 38.3, 38.2, 38.0, 37.8, 37.7, 37.8, 37.9, 38.0, 38.2, 38.1, 38.0, 37.9, 37.8, 38.0]
        kelembaban_data = [60, 59, 60, 61, 62, 63, 64, 65, 64, 63, 62, 61, 60.5, 60.3, 59.8, 59.5, 59.0, 58.5, 58.0, 58.2, 58.4, 58.6, 60.3]

        # Setup sumbu
        plot_widget.setYRange(30, 45)  # Range untuk suhu
        plot_widget.setXRange(-1, len(hours))
        
        # Sumbu X (Waktu)
        x_ticks = [list(zip(x_data, time_labels))]
        ax_bottom = plot_widget.getAxis('bottom')
        ax_bottom.setTicks(x_ticks)
        ax_bottom.setTextPen(QColor("#6b7280"))
        ax_bottom.setPen(QColor("#e5e7eb"))

        # Sumbu Y Kiri (Suhu)
        ax_left = plot_widget.getAxis('left')
        ax_left.setLabel("Suhu (°C)", color="#FFC107")
        ax_left.setTextPen(QColor("#FFC107"))
        ax_left.setPen(QColor("#e5e7eb"))
        ax_left.setRange(30, 45)

        # Plot garis suhu dengan styling yang sesuai gambar
        suhu_plot = plot_widget.plot(
            x_data, suhu_data, 
            pen=pg.mkPen(color="#FFC107", width=3),
            symbol='o', symbolSize=6, symbolBrush='#FFC107',
            name="Suhu"
        )

        # Buat ViewBox kedua untuk kelembaban
        view_box_2 = pg.ViewBox()
        plot_widget.plotItem.scene().addItem(view_box_2)
        view_box_2.setXRange(0, len(hours)-1)
        view_box_2.setYRange(40, 80)

        # Sumbu Y Kanan (Kelembaban)
        ax_right = pg.AxisItem('right')
        ax_right.setLabel("Kelembaban (%)", color="#5A3FFF")
        ax_right.setTextPen(QColor("#5A3FFF"))
        ax_right.setPen(QColor("#e5e7eb"))
        ax_right.linkToView(view_box_2)
        
        plot_widget.plotItem.layout.addItem(ax_right, 2, 3)
        view_box_2.linkView(pg.ViewBox.XAxis, plot_widget.plotItem.getViewBox())

        # Plot garis kelembaban
        kelembaban_plot = pg.PlotCurveItem(
            x_data, kelembaban_data,
            pen=pg.mkPen(color="#5A3FFF", width=3),
        )
        kelembaban_symbol = pg.ScatterPlotItem(
            x_data, kelembaban_data,
            symbol='o', size=6, brush='#5A3FFF'
        )
        view_box_2.addItem(kelembaban_plot)
        view_box_2.addItem(kelembaban_symbol)

        # Tooltip untuk hover
        self.tooltip = QLabel(plot_widget)
        self.tooltip.setStyleSheet("""
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
        self.tooltip.hide()

        # Mouse move event untuk tooltip
        def on_mouse_move(event):
            if plot_widget.sceneBoundingRect().contains(event):
                mouse_pos = plot_widget.plotItem.vb.mapSceneToView(event)
                x_pos = int(mouse_pos.x())
                
                if 0 <= x_pos < len(hours):
                    time_str = time_labels[x_pos]
                    suhu_val = suhu_data[x_pos]
                    kelembaban_val = kelembaban_data[x_pos]
                    
                    tooltip_text = f"""<div style="color: #6b7280; font-size: 11px; margin-bottom: 4px;">{time_str}</div>
<div style="color: #5A3FFF;">Kelembaban (%): {kelembaban_val}</div>
<div style="color: #FFC107;">Suhu (°C): {suhu_val}</div>"""
                    
                    self.tooltip.setText(tooltip_text)
                    self.tooltip.adjustSize()
                    
                    # Position tooltip
                    try:
                        tooltip_pos = plot_widget.mapFromScene(event)
                        self.tooltip.move(tooltip_pos.x() + 10, tooltip_pos.y() - 60)
                        self.tooltip.show()
                    except:
                        pass
                else:
                    self.tooltip.hide()
            else:
                self.tooltip.hide()

        plot_widget.scene().sigMouseMoved.connect(on_mouse_move)

        # Update view saat resize
        def update_views():
            view_box_2.setGeometry(plot_widget.plotItem.vb.sceneBoundingRect())
        
        plot_widget.plotItem.vb.sigResized.connect(update_views)
        update_views()

        graph_main_layout.addWidget(plot_widget)
        return graph_widget_container
        
    # --- 5. Widget Panel Konfigurasi ---
    def create_config_panel(self):
        # Gunakan QScrollArea agar bisa di-scroll jika kontennya panjang
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setObjectName("configScrollArea")
        
        config_widget = QWidget()
        config_widget.setObjectName("configWidget")
        config_layout = QVBoxLayout(config_widget)
        config_layout.setSpacing(20)
        
        # Judul
        title_layout = QHBoxLayout()
        icon_label = QLabel()
        icon_label.setPixmap(self.load_svg_icon("settings.svg", QSize(40, 40)))
        
        title_label = QLabel("KONFIGURASI")
        title_label.setObjectName("sectionTitle")
        
        title_layout.addWidget(icon_label)
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        config_layout.addLayout(title_layout)
        
        # --- Profil Inkubasi ---
        config_layout.addWidget(self.create_form_label("Profil Inkubasi"))
        profil_combo = QComboBox()
        profil_combo.addItems([
            "Ayam (38°C, 60 %)",
            "Bebek (37.5°C, 65%)",
            "Burung Puyuh (37.8°C, 55%)"
        ])
        config_layout.addWidget(profil_combo)
        
        # --- Pengaturan Setpoint ---
        config_layout.addWidget(self.create_form_label("Pengaturan Setpoint"))
        config_layout.addWidget(QLabel("Target Suhu(°C)"))
        self.suhu_input = QLineEdit("38")
        config_layout.addWidget(self.suhu_input)
        
        config_layout.addWidget(QLabel("Target Kelembaban(%)"))
        self.kelembaban_input = QLineEdit("60")
        config_layout.addWidget(self.kelembaban_input)
        
        apply_btn = QPushButton("Terapkan Pengaturan")
        apply_btn.setObjectName("applyButton")
        config_layout.addWidget(apply_btn)
        
        config_layout.addWidget(self.create_divider()) # Pemisah

        # --- Kontrol Manual ---
        config_layout.addWidget(self.create_form_label("Kontrol Manual"))
        
        heater_toggle_btn = QPushButton(" Toggle Pemanas")
        heater_toggle_btn.setIcon(QIcon(self.load_svg_icon("pemanas-control.svg", QSize(20, 20))))
        heater_toggle_btn.setObjectName("heaterButton")
        config_layout.addWidget(heater_toggle_btn)
        
        humidifier_toggle_btn = QPushButton(" Toggle Humidifier")
        humidifier_toggle_btn.setIcon(QIcon(self.load_svg_icon("humidifier-control.svg", QSize(20, 20))))
        humidifier_toggle_btn.setObjectName("humidifierButton")
        config_layout.addWidget(humidifier_toggle_btn)
        
        config_layout.addWidget(self.create_divider()) # Pemisah

        # --- Koneksi MQTT ---
        config_layout.addWidget(self.create_form_label("Koneksi MQTT"))
        
        # Username dengan icon
        username_layout = QHBoxLayout()
        username_icon = QLabel()
        username_icon.setPixmap(self.load_svg_icon("username.svg", QSize(24, 24)))
        username_label = QLabel("Username")
        username_layout.addWidget(username_icon)
        username_layout.addWidget(username_label)
        username_layout.addStretch()
        config_layout.addLayout(username_layout)
        
        self.user_input = QLineEdit("kartel_esp32")
        config_layout.addWidget(self.user_input)
        
        # Password dengan icon
        password_layout = QHBoxLayout()
        password_icon = QLabel()
        password_icon.setPixmap(self.load_svg_icon("password.svg", QSize(24, 24)))
        password_label = QLabel("Password")
        password_layout.addWidget(password_icon)
        password_layout.addWidget(password_label)
        password_layout.addStretch()
        config_layout.addLayout(password_layout)
        
        self.pass_input = QLineEdit("KartelTest123")
        self.pass_input.setEchoMode(QLineEdit.EchoMode.Password)
        config_layout.addWidget(self.pass_input)
        
        # --- Info Koneksi ---
        info_box = QFrame()
        info_box.setObjectName("infoBox")
        
        info_main_layout = QVBoxLayout(info_box)
        info_main_layout.setContentsMargins(0, 0, 0, 0)
        info_main_layout.setSpacing(12)
        
        # Header dengan icon dan judul
        info_header_layout = QHBoxLayout()
        info_header_layout.setContentsMargins(0, 0, 0, 0)
        info_header_layout.setSpacing(8)
        
        info_icon = QLabel()
        info_icon.setPixmap(self.load_svg_icon("information-mqtt.svg", QSize(24, 24)))
        
        info_title = QLabel("Informasi Koneksi")
        info_title.setObjectName("infoHeaderTitle")
        
        info_header_layout.addWidget(info_icon)
        info_header_layout.addWidget(info_title)
        info_header_layout.addStretch()
        
        # Teks informasi
        info_text = QLabel("Pastikan perangkat IoT ESP32 Anda sudah terkonfigurasi dengan broker MQTT yang sama. Aplikasi ini akan subscribe ke topic yang Anda tentukan untuk menerima data sensor secara real-time.")
        info_text.setWordWrap(True)
        info_text.setObjectName("infoContentText")
        
        info_main_layout.addLayout(info_header_layout)
        info_main_layout.addWidget(info_text)
        config_layout.addWidget(info_box)
        
        config_layout.addStretch() # Mendorong tombol ke bawah

        # --- Tombol Aksi Bawah ---
        button_layout = QHBoxLayout()
        cancel_btn = QPushButton("Batalkan")
        cancel_btn.setObjectName("cancelButton")
        connect_btn = QPushButton("Hubungkan Ke Broker")
        connect_btn.setObjectName("connectButton")
        
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(connect_btn)
        config_layout.addLayout(button_layout)
        
        scroll_area.setWidget(config_widget)
        return scroll_area

    # --- Helper Widgets ---
    def create_form_label(self, text):
        label = QLabel(text)
        label.setObjectName("formSectionTitle")
        return label
        
    def create_divider(self):
        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setFrameShadow(QFrame.Shadow.Sunken)
        divider.setObjectName("divider")
        return divider
        
    # --- STYLESHEET (QSS) ---
    def set_stylesheet(self):
        """Terapkan stylesheet dari file eksternal"""
        stylesheet = self.load_stylesheet("styles.qss")
        
        # Jika file tidak ditemukan, gunakan style default
        if not stylesheet:
            stylesheet = self.get_default_stylesheet()
            
        self.setStyleSheet(stylesheet)
    
    def load_stylesheet(self, file_path="styles.qss"):
        """Memuat stylesheet dari file QSS eksternal"""
        try:
            # Coba beberapa lokasi untuk file stylesheet
            possible_paths = [
                file_path,                           # Root folder
                f"asset/style/{file_path}",          # Asset/style folder
                f"asset/{file_path}",                # Asset folder
                f"style/{file_path}"                 # Style folder
            ]
            
            for style_file in possible_paths:
                if os.path.exists(style_file):
                    with open(style_file, 'r', encoding='utf-8') as file:
                        stylesheet = file.read()
                    print(f"✅ Stylesheet berhasil dimuat dari: {style_file}")
                    return stylesheet
            
            raise FileNotFoundError(f"File tidak ditemukan di semua lokasi")
            
        except Exception as e:
            print(f"⚠ Error saat memuat stylesheet: {e}")
            return ""
    
    def get_default_stylesheet(self):
        """Fallback stylesheet jika file eksternal tidak tersedia"""
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

if __name__ == "__main__":
    # Konfigurasi untuk pyqtgraph agar garis terlihat halus
    pg.setConfigOptions(antialias=True)
    
    app = QApplication(sys.argv)
    
    # Set font default untuk aplikasi
    default_font = QFont("Manrope", 10)
    if default_font.exactMatch():
        print("✅ Font aplikasi: Manrope berhasil diset sebagai font default")
    else:
        print("⚠ Font aplikasi: Menggunakan fallback font (Arial)")
        default_font = QFont("Arial", 10)  # fallback
    app.setFont(default_font)
    
    window = KartelDashboard()
    window.show()
    sys.exit(app.exec())