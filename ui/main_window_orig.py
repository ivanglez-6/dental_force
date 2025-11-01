# ui/main_window.py
from PySide6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QSplitter, QMessageBox, QSizePolicy
from PySide6.QtCore import Qt, QTimer
from services.data_storage import DataStorage
from services.csv_parser import CSVParser
from ui.live_plot import LivePlot
from ui.stats_widget import StatsWidget
from ui.ble_panel import BLEPanel
from ui.auth_widget import AuthWidget
from ui.reports_widget import ReportsWidget
from ui.history_widget import HistoryWidget
from PySide6.QtCore import QTimer

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Dental Force Monitor — Dashboard")
        self.resize(1200, 720)

        self.storage = DataStorage()
        self.csv_parser = CSVParser()

        # Header
        self.header = QLabel("🦷 Dental Force Monitor")
        self.header.setObjectName("appTitle")
        self.header.setAlignment(Qt.AlignmentFlag.AlignLeft)

        # Left column (controls)
        self.left_panel = QWidget()
        self.left_panel.setObjectName("leftPanel")
        left_layout = QVBoxLayout()
        # Auth
        self.auth = AuthWidget(self.storage)
        left_layout.addWidget(self.auth)
        # BLE panel
        self.ble_panel = BLEPanel(self.storage)
        # conectar callback de BLEPanel -> almacenar y actualizar gráficas
        self.ble_panel.data_callback = self.on_ble_data
        left_layout.addWidget(self.ble_panel)
        # reports and history
        self.reports = ReportsWidget(self.storage)
        left_layout.addWidget(self.reports)
        self.history = HistoryWidget(self.storage)
        left_layout.addWidget(self.history)

        left_layout.addStretch()
        self.left_panel.setLayout(left_layout)
        self.left_panel.setMinimumWidth(260)

        #Simulación

         # --- Instancias de servicios y widgets ---
        self.storage = DataStorage()
        self.live_plot = LivePlot(self.storage)
        self.history_widget = HistoryWidget(self.storage)

        # --- Instancias de servicios y widgets ---
        self.storage = DataStorage()
        self.live_plot = LivePlot(self.storage)
        self.history_widget = HistoryWidget(self.storage)

        # --- Botones de control ---
        self.start_btn = QPushButton("🟢 Iniciar Simulación")
        self.stop_btn = QPushButton("🔴 Detener Simulación")
        self.mode_label = QLabel("Modo: <b>Simulación</b>")
        self.mode_label.setStyleSheet("color: cyan;")

        self.start_btn.setStyleSheet("background-color: #1f9d55; color: white; font-weight: bold;")
        self.stop_btn.setStyleSheet("background-color: #c92a2a; color: white; font-weight: bold;")

        # --- Layout superior (controles) ---
        controls_layout = QHBoxLayout()
        controls_layout.addWidget(self.start_btn)
        controls_layout.addWidget(self.stop_btn)
        controls_layout.addWidget(self.mode_label)

        # --- Layout principal ---
        main_layout = QVBoxLayout()
        main_layout.addLayout(controls_layout)
        main_layout.addWidget(self.live_plot)
        main_layout.addWidget(self.history_widget)
        self.setLayout(main_layout)

        # --- Conexión de botones ---
        self.start_btn.clicked.connect(self.start_simulation)
        self.stop_btn.clicked.connect(self.stop_simulation)

        # Right column (visualization)
        self.right_panel = QWidget()
        right_layout = QVBoxLayout()
        self.live_plot = LivePlot(self.storage)
        self.stats = StatsWidget()
        control_row = QWidget()
        control_layout = QHBoxLayout()
        self.save_btn = QPushButton("Save Session")
        self.save_btn.clicked.connect(self.save_session)
        self.export_btn = QPushButton("Export current CSV")
        self.export_btn.clicked.connect(self.export_current)
        control_layout.addWidget(self.save_btn)
        control_layout.addWidget(self.export_btn)
        control_row.setLayout(control_layout)
        right_layout.addWidget(self.live_plot)
        right_layout.addWidget(self.stats)
        right_layout.addWidget(control_row)
        self.right_panel.setLayout(right_layout)

        self.simulation_timer = QTimer()
        self.simulation_timer.timeout.connect(self.live_plot.update_plot)

        # Splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self.left_panel)
        splitter.addWidget(self.right_panel)
        splitter.setSizes([280, 920])

        central = QWidget()
        central_layout = QVBoxLayout()
        central_layout.addWidget(self.header)
        central_layout.addWidget(splitter)
        central.setLayout(central_layout)
        self.setCentralWidget(central)

        # Timer para refrescar UI
        self.timer = QTimer()
        self.timer.timeout.connect(self._refresh)
        self.timer.start(800)

    def on_ble_data(self, raw_csv):
        record = self.csv_parser.parse(raw_csv)
        if record:
            self.storage.add_record(record)
            # actualizar componentes (plot/stat vienen desde timer o directo)
            self.live_plot.update_plot()
            self.stats.update(self.storage)

    def save_session(self):
        try:
            s = self.storage.save_session()
            QMessageBox.information(self, "Saved", f"Session saved with {s['summary']['totalReadings']} readings.")
            self.history.load()
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))

    def export_current(self):
        from PySide6.QtWidgets import QFileDialog
        path, _ = QFileDialog.getSaveFileName(self, "Save CSV", "", "CSV Files (*.csv)")
        if not path:
            return
        try:
            self.storage.export_current_csv(path)
            QMessageBox.information(self, "Exported", f"Saved to {path}")
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))

    def _refresh(self):
        # refrescar stats y plot periódicamente
        try:
            self.stats.update(self.storage)
            # la gráfica solo redibuja si hay datos nuevos
            self.live_plot.update_plot()
        except Exception as e:
            print("Refresh error:", e)

    # --- Funciones de control ---
    def start_simulation(self):
        """Arranca el modo de simulación"""
        self.live_plot.start_simulation()
        self.mode_label.setText("Modo: <b>Simulación activa</b>")
        self.mode_label.setStyleSheet("color: lime; font-weight: bold;")

    def stop_simulation(self):
        """Detiene y guarda los datos de simulación"""
        self.live_plot.stop_simulation()
        self.mode_label.setText("Modo: <b>Simulación detenida</b>")
        self.mode_label.setStyleSheet("color: orange; font-weight: bold;")
        # Refrescar historial para ver la nueva sesión
        self.history_widget.load()