# ui/main_window_theme.py
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSizePolicy, QFrame, QStackedWidget, QToolButton, QSpacerItem, QGraphicsOpacityEffect
)
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QIcon, QPixmap
import os, json, csv, time

from services.data_storage import DataStorage
from services.csv_parser import CSVParser
from ui.live_plot import LivePlot
from ui.stats_widget import StatsWidget
from ui.ble_panel import BLEPanel
from ui.auth_widget import AuthWidget
from ui.reports_widget import ReportsWidget
from ui.history_widget import HistoryWidget
from ui.quick_actions_widget import QuickActionsWidget   # nuevo

SETTINGS_FILE = os.path.join(os.path.dirname(__file__), "..", "settings.json")


class SidebarButton(QPushButton):
    def __init__(self, text, icon_path=None, parent=None):
        super().__init__(text, parent)
        self.setCheckable(True)
        self.setMinimumHeight(44)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setStyleSheet("text-align: left; padding-left: 12px;")
        if icon_path and os.path.exists(icon_path):
            self.setIcon(QIcon(icon_path))
            self.setIconSize(QPixmap(icon_path).rect().size())


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Monitor de Fuerza Dental — Panel Principal")
        self.resize(1200, 760)

        # Settings
        self.settings = {"theme": "dark"}
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    self.settings.update(json.load(f))
            except Exception as e:
                print("Settings load error:", e)

        # Data
        self.storage = DataStorage()
        self.parser = CSVParser(self.storage)

        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- HEADER ---
        header = QFrame()
        header.setObjectName("topHeader")
        header.setFixedHeight(60)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(12, 8, 12, 8)

        self.title_label = QLabel("<b>🦷 Dental Force Monitor</b>")
        self.title_label.setObjectName("windowTitle")
        header_layout.addWidget(self.title_label, alignment=Qt.AlignVCenter)
        header_layout.addSpacerItem(QSpacerItem(20, 10, QSizePolicy.Expanding, QSizePolicy.Minimum))

        # Theme toggle
        self.theme_btn = QToolButton()
        self.theme_btn.setCheckable(True)
        self.theme_btn.setText("🌙" if self.settings.get("theme") == "dark" else "☀️")
        self.theme_btn.clicked.connect(self.toggle_theme)
        header_layout.addWidget(self.theme_btn)

        main_layout.addWidget(header)

        # --- BODY ---
        body_widget = QWidget()
        body_layout = QHBoxLayout(body_widget)
        body_layout.setContentsMargins(0, 0, 0, 0)

        # Sidebar
        self.sidebar = QFrame()
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setMinimumWidth(220)
        self.sidebar.setMaximumWidth(320)
        self.side_layout = QVBoxLayout(self.sidebar)
        self.side_layout.setContentsMargins(8, 8, 8, 8)
        self.side_layout.setSpacing(6)

        # Hamburger
        self.hamburger = QToolButton()
        self.hamburger.setText("☰")
        self.hamburger.setFixedSize(36, 36)
        self.hamburger.clicked.connect(self.toggle_sidebar)
        self.side_layout.addWidget(self.hamburger, alignment=Qt.AlignLeft)

        # Sidebar buttons
        icon_base = os.path.join(os.path.dirname(__file__), "icons")
        self.btn_dashboard = SidebarButton("Panel Principal", os.path.join(icon_base, "dashboard.svg"))
        self.btn_ble = SidebarButton("BLE / Dispositivo", os.path.join(icon_base, "ble.svg"))
        self.btn_history = SidebarButton("Historial / Registros", os.path.join(icon_base, "history.svg"))
        self.btn_reports = SidebarButton("Reportes / Exportar", os.path.join(icon_base, "reports.svg"))
        self.btn_auth = SidebarButton("Cuenta / Autenticación", os.path.join(icon_base, "user.svg"))

        for b in [self.btn_dashboard, self.btn_ble, self.btn_history, self.btn_reports, self.btn_auth]:
            b.clicked.connect(self.on_nav_clicked)
            self.side_layout.addWidget(b)

        self.side_layout.addStretch()
        self.sidebar_footer = QLabel("© Proyecto Final — Presentación")
        self.side_layout.addWidget(self.sidebar_footer, alignment=Qt.AlignLeft | Qt.AlignBottom)
        body_layout.addWidget(self.sidebar)

        # --- STACK ---
        self.stack = QStackedWidget()

        # instantiate pages
        self.live_plot = LivePlot(self.storage)
        self.stats = StatsWidget(self.storage)
        self.ble_panel = BLEPanel(self.storage)
        self.ble_panel.data_callback = self.on_ble_data  # Connect BLE data callback
        self.history = HistoryWidget(self.storage)
        self.reports = ReportsWidget(self.storage)
        self.auth = AuthWidget(self.storage)

        # Dashboard page and layout
        dashboard_page = QWidget()
        dash_layout = QHBoxLayout(dashboard_page)
        dash_layout.setContentsMargins(10, 10, 10, 10)

        # Left column: graph only (stats now integrated in live_plot)
        left_col = QVBoxLayout()
        left_col.addWidget(self.live_plot, 1)
        # self.stats widget removed - statistics now shown in StatisticsCards within LivePlot
        dash_layout.addLayout(left_col, 3)

        # Right column: use QuickActionsWidget (separate widget)
        from ui.quick_actions_widget import QuickActionsWidget
        self.quick_widget = QuickActionsWidget()
        # conectar señales del quick widget a métodos del MainWindow
        self.quick_widget.start_sim.connect(self.start_simulation_session)
        self.quick_widget.start_real.connect(self.start_real_session)
        self.quick_widget.stop.connect(self.stop_session)
        self.quick_widget.clear.connect(self.clear_data)

        right_col = QVBoxLayout()
        right_col.addWidget(self.quick_widget)
        right_col.addStretch()
        dash_layout.addLayout(right_col, 1)

        self.stack.addWidget(dashboard_page)
        self.stack.addWidget(self.ble_panel)
        self.stack.addWidget(self.history)
        self.stack.addWidget(self.reports)
        self.stack.addWidget(self.auth)

        body_layout.addWidget(self.stack, 1)
        main_layout.addWidget(body_widget)

        # Default page
        self.btn_dashboard.setChecked(True)
        self.stack.setCurrentIndex(0)

        # Timer that refreshes plots/stats periodically
        self.refresh_timer = QTimer(self)
        self.refresh_timer.setInterval(400)  # 400 ms refresh
        self.refresh_timer.timeout.connect(self._refresh)
        self.refresh_timer.start()

        # Timer used for simulation (kept separate so we can pause/resume)
        self.simulation_timer = QTimer(self)
        self.simulation_timer.setInterval(200)
        self.simulation_timer.timeout.connect(self.live_plot.update_plot)

        # Aplicar tema inicial
        self.apply_theme(self.settings.get("theme", "dark"))

    # --- methods (theme/sidebar/ nav) ---
    def apply_theme(self, theme_name):
        try:
            qss_file = os.path.join(os.path.dirname(__file__), "style.qss" if theme_name == "dark" else "style_light.qss")
            if os.path.exists(qss_file):
                with open(qss_file, "r", encoding="utf-8") as f:
                    self.setStyleSheet(f.read())
            text_color = "#BEBCBC" if theme_name == "dark" else "#3038AD"
            bg_color = "#000000" if theme_name == "dark" else "#BEBCBC"
            for btn in [self.btn_dashboard, self.btn_ble, self.btn_history, self.btn_reports, self.btn_auth]:
                btn.setStyleSheet(f"text-align: left; padding-left: 12px; color: {text_color}; background-color: {bg_color}; border: none;")
            self.sidebar_footer.setStyleSheet(f"color:{text_color}; font-size:10pt;")
            self.title_label.setStyleSheet(f"color:{text_color};")
            self.theme_btn.setStyleSheet(f"color:{text_color};")
            # quick widget buttons style
            btn_bg = "#818181" if theme_name == "dark" else "#e0e0e0"
            btn_bg_hover = "#818181" if theme_name == "dark" else "#d0d0d0"
            btn_text = "#00a2d8" if theme_name == "dark" else "#3038AD"
            for b in getattr(self.quick_widget, "__dict__", {}).get("btn_start_sim", []):
                pass
            # style quick actions buttons properly (iterate attributes)
            for attr in ("btn_start_sim","btn_start_real","btn_stop","btn_clear"):
                b = getattr(self.quick_widget, attr, None)
                if b:
                    b.setStyleSheet(f"background-color:{btn_bg}; color:{btn_text}; font-weight:600; border-radius:6px; text-align:left; padding-left:8px;")
            qtitle = self.findChild(QLabel, "quickTitle")
            if qtitle:
                qtitle.setStyleSheet(f"font-size:12pt; color:{text_color}; margin-bottom:8px;")
        except Exception as e:
            print("Theme load error:", e)

    def toggle_theme(self):
        cur = self.settings.get("theme", "dark")
        new = "light" if cur == "dark" else "dark"
        self.settings["theme"] = new
        self.apply_theme(new)
        self.theme_btn.setText("🌙" if new == "dark" else "☀️")
        try:
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(self.settings, f, indent=2)
        except Exception as e:
            print("Could not save settings:", e)

    def toggle_sidebar(self):
        collapsed = self.sidebar.maximumWidth() < 100
        if collapsed:
            self.sidebar.setMaximumWidth(320)
            self.sidebar.setMinimumWidth(220)
            self.btn_dashboard.setText("Panel Principal")
            self.btn_ble.setText("BLE / Dispositivo")
            self.btn_history.setText("Historial / Registros")
            self.btn_reports.setText("Reportes / Exportar")
            self.btn_auth.setText("Cuenta / Autenticación")
        else:
            self.sidebar.setMaximumWidth(64)
            self.sidebar.setMinimumWidth(64)
            for btn in [self.btn_dashboard, self.btn_ble, self.btn_history, self.btn_reports, self.btn_auth]:
                btn.setText("")

    def on_nav_clicked(self):
        sender = self.sender()
        mapping = {
            self.btn_dashboard: 0,
            self.btn_ble: 1,
            self.btn_history: 2,
            self.btn_reports: 3,
            self.btn_auth: 4
        }
        for b in mapping.keys():
            b.setChecked(False)
        sender.setChecked(True)
        idx = mapping.get(sender, 0)
        self.stack.setCurrentIndex(idx)

    def _refresh(self):
        try:
            if hasattr(self.live_plot, "update_plot"):
                # call update_plot so it will read storage (simulated or real)
                # Statistics are now updated within LivePlot.update_plot()
                self.live_plot.update_plot()
            # Old stats widget removed - stats now integrated in LivePlot
            # if hasattr(self.stats, "update"):
            #     self.stats.update(self.storage)
        except Exception as e:
            print("Refresh error:", e)

    # --- Quick Actions handlers ---
    def start_simulation_session(self):
        """Inicia sesión simulada: activa LivePlot.simulating y arranca timer"""
        try:
            # start session in storage
            if hasattr(self.storage, "start_new_session"):
                self.storage.start_new_session()
            # start live_plot sim
            if hasattr(self.live_plot, "start_simulation"):
                self.live_plot.start_simulation()
            # start timers
            if not self.simulation_timer.isActive():
                self.simulation_timer.start()
            print("Simulación iniciada.")
        except Exception as e:
            print("Error iniciando simulación:", e)

    def start_real_session(self):
        """Marca session real como iniciada; luego BLE/serial debe alimentar storage.add_force_value()"""
        try:
            if hasattr(self.storage, "start_new_session"):
                self.storage.start_new_session()
            # in real mode we expect BLEPanel to call storage.add_force_value(...) when data arrives
            print("Sesión real iniciada. Esperando datos del microcontrolador (BLE/Serial).")
        except Exception as e:
            print("Error iniciando sesión real:", e)

    def stop_session(self):
        """Detener sesión (si es simulada detiene simulación). Guarda automáticamente y actualiza historial."""
        try:
            # Mark session as inactive to stop displaying live data
            self.storage.session_active = False

            # if live_plot simulating, stop it
            if hasattr(self.live_plot, "stop_simulation") and getattr(self.live_plot, "simulating", False):
                self.live_plot.stop_simulation(save=True)
            else:
                # otherwise ask storage to end session and save
                if hasattr(self.storage, "end_session"):
                    self.storage.end_session(save=True)
                else:
                    # fallback: call save_session directly
                    try:
                        self.storage.save_session()
                    except Exception:
                        pass
            # stop the simulation timer to avoid more updates from simulation
            if self.simulation_timer.isActive():
                self.simulation_timer.stop()
            # refresh history widget so it shows the newly saved session
            try:
                self.history.load()
            except Exception:
                pass
            print("Sesión detenida y guardada.")
        except Exception as e:
            print("Error deteniendo sesión:", e)

    def clear_data(self):
        """Limpiar datos actuales de la sesión y la gráfica (sin afectar historial)."""
        try:
            # Deactivate session when clearing
            self.storage.session_active = False

            if hasattr(self.storage, "clear_current_session"):
                self.storage.clear_current_session()
            else:
                self.storage.current_session_data = []
            # also clear plot's display
            try:
                self.live_plot.update_plot()
            except Exception:
                pass
            print("Datos borrados.")
        except Exception as e:
            print("clear_data error:", e)

    def on_ble_data(self, raw_csv):
        """Handle incoming BLE data from BLEPanel"""
        try:
            record = self.parser.parse(raw_csv)
            if record:
                self.storage.add_record(record)
        except Exception as e:
            print(f"Error processing BLE data: {e}")
