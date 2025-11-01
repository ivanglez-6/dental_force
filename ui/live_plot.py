# ui/live_plot.py
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QProgressBar, QHBoxLayout
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PySide6.QtGui import QPixmap, QFont
from PySide6.QtCore import Qt
import matplotlib.ticker as ticker
import os
import random
import time
import math

class LivePlot(QWidget):
    def __init__(self, storage):
        super().__init__()
        self.storage = storage
        self.simulating = False

        # Matplotlib figure
        self.fig = Figure(figsize=(6, 3), tight_layout=True)
        self.canvas = FigureCanvas(self.fig)
        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor("#071827")
        self.ax.tick_params(colors="#004166")
        self.ax.xaxis.set_major_locator(ticker.MaxNLocator(integer=True))
        self.ax.set_title("Force over time (last samples)", color="#0E2C46")
        self.ax.set_xlabel("Sample", color="#0E2C46")
        self.ax.set_ylabel("Force (N)", color="#0E2C46")

        # Force label + semaphore bar
        self.force_label = QLabel("Fuerza: -- N | -- kg")
        self.force_label.setAlignment(Qt.AlignCenter)
        self.force_label.setFont(QFont("Arial", 12, QFont.Bold))
        self.force_label.setStyleSheet("color: white;")

        self.force_bar = QProgressBar()
        self.force_bar.setRange(0, 100)
        self.force_bar.setTextVisible(False)
        self.force_bar.setFixedHeight(20)
        self.force_bar.setStyleSheet("""
            QProgressBar { border-radius: 8px; background: #333; }
            QProgressBar::chunk { border-radius: 8px; background-color: #00ff7f; }
        """)

        # Three dental images (left, center, right)
        self.img_left = QLabel()
        self.img_center = QLabel()
        self.img_right = QLabel()
        base = os.path.dirname(__file__)
        left_path = os.path.join(base, "teeth_left.png")
        center_path = os.path.join(base, "teeth_model.png")
        right_path = os.path.join(base, "teeth_right.png")

        def load_label(lbl, p, placeholder):
            if os.path.exists(p):
                pix = QPixmap(p).scaledToWidth(200, Qt.SmoothTransformation)
                lbl.setPixmap(pix)
                lbl.setAlignment(Qt.AlignCenter)
            else:
                lbl.setText(placeholder)
                lbl.setStyleSheet("color: gray;")
                lbl.setAlignment(Qt.AlignCenter)

        load_label(self.img_left, left_path, "[Izq no encontrada]")
        load_label(self.img_center, center_path, "[Centro no encontrada]")
        load_label(self.img_right, right_path, "[Der no encontrada]")

        # Layouts
        main = QVBoxLayout()
        main.addWidget(self.canvas)
        main.addWidget(self.force_label)
        main.addWidget(self.force_bar)

        # images row
        img_row = QHBoxLayout()
        img_row.addWidget(self.img_left)
        img_row.addWidget(self.img_center)
        img_row.addWidget(self.img_right)
        main.addLayout(img_row)

        self.setLayout(main)

    # conversion: raw sensor (0-1023) -> N, kg
    def _convert_raw_to_force(self, raw_value):
        try:
            max_sensor = 1023.0
            max_force = 50.0  # N (ajusta si necesitas otra calibración)
            # Si el valor proviene ya en Newtons (ej: si firmware envía N), detectarlo:
            if raw_value > 2000:  # heurístico: si es muy grande, quizás ya es microsegundos o mala lectura
                raw_value = 0.0
            force_n = (float(raw_value) * 1023 / max_sensor) * max_force
            force_kg = force_n / 9.81
            return force_n, force_kg
        except Exception:
            return 0.0, 0.0

    # llamada periódica para dibujar
    def update_plot(self):
        # if simulating, maybe generate a new sample into storage
        if self.simulating:
            self._simulate_one_sample()

        data = getattr(self.storage, "current_session_data", [])[-200:]
        if not data:
            self.ax.clear()
            self.ax.set_title("Waiting for data...", color="#0E2C46")
            self.canvas.draw()
            # keep label default
            self.force_label.setText("Fuerza: -- N | -- kg")
            self.force_bar.setValue(0)
            return

        raw = [d.get("force", 0) for d in data]
        y_n = [self._convert_raw_to_force(r)[0] for r in raw]
        x = list(range(len(y_n)))

        # draw plot
        self.ax.clear()
        self.ax.set_facecolor("#294B69")
        self.ax.plot(x, y_n, linewidth=2, color="#0003cf")
        self.ax.set_title("Force over time (last samples)", color="#0003cf")
        self.ax.set_xlabel("Sample", color="#0003cf")
        self.ax.set_ylabel("Force (N)", color="#0003cf")
        self.ax.grid(alpha=0.2)
        # set y limits a little padding
        max_y = max(y_n) if y_n else 1
        self.ax.set_ylim(0, max(10, max_y * 1.2))
        self.canvas.draw()

        # update last sample display
        fn, fk = self._convert_raw_to_force(raw[-1])
        self.force_label.setText(f"Fuerza: {fn:.2f} N | {fk:.3f} kg")

        # update semaphore bar (scale relative to max_force)
        max_force = 50.0
        level = min(fn / max_force * 100, 100)
        self.force_bar.setValue(int(level))

        if fn < 15:
            color = "#00ff7f"
        elif fn < 35:
            color = "#ffd700"
        else:
            color = "#ff4040"

        self.force_bar.setStyleSheet(f"""
            QProgressBar {{
                border-radius: 8px;
                background: #333;
            }}
            QProgressBar::chunk {{
                border-radius: 8px;
                background-color: {color};
            }}
        """)

    def _simulate_one_sample(self):
        """Genera y añade un único valor de simulación al storage."""
        t = time.time() % 10
        if 2 < t < 3 or 7 < t < 8:
            raw = random.uniform(600, 900)  # alto (sensor raw)
        else:
            raw = random.uniform(20, 200)   # bajo
        # usa la API de DataStorage correcta
        if hasattr(self.storage, "add_force_value"):
            self.storage.add_force_value(raw)
        else:
            # fallback: si storage guarda dicts directamente
            if not hasattr(self.storage, "current_session_data"):
                self.storage.current_session_data = []
            self.storage.current_session_data.append({"timestamp": time.time(), "force": raw})

    def start_simulation(self):
        self.simulating = True
        # iniciar sesión en storage si existe
        if hasattr(self.storage, "start_new_session"):
            self.storage.start_new_session()

    def stop_simulation(self, save=True):
        self.simulating = False
        if hasattr(self.storage, "end_session"):
            self.storage.end_session(save)
