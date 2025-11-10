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
from datetime import datetime

# Color constants for dual sensor display
COLOR_LEFT = '#2196F3'   # Blue for left sensor
COLOR_RIGHT = '#FF5722'  # Orange for right sensor


class TeethVisualization(QWidget):
    """Custom widget for layered teeth visualization with event-based overlays"""

    def __init__(self, parent=None):
        super().__init__(parent)
        # Larger size for horizontal layout - more vertical space available
        # Maintains aspect ratio of 1728x2034 (0.85:1)
        self.setFixedSize(293, 345)

        # Create container for absolute positioning
        container = QWidget(self)
        container.setGeometry(0, 0, 293, 345)

        # Base image (always visible)
        self.base_label = QLabel(container)
        self.base_label.setAlignment(Qt.AlignCenter)

        # Left overlay (visible during left sensor event)
        self.left_overlay = QLabel(container)
        self.left_overlay.setAlignment(Qt.AlignCenter)
        self.left_overlay.hide()  # Hidden by default

        # Right overlay (visible during right sensor event)
        self.right_overlay = QLabel(container)
        self.right_overlay.setAlignment(Qt.AlignCenter)
        self.right_overlay.hide()  # Hidden by default

        # Load images
        base_dir = os.path.dirname(__file__)
        self._load_images(base_dir)

    def _load_images(self, base_dir):
        """Load and scale the images"""
        base_path = os.path.join(base_dir, "arcada superior.png")
        left_path = os.path.join(base_dir, "left_mark.png")
        right_path = os.path.join(base_dir, "right_mark.png")

        # Load base image
        if os.path.exists(base_path):
            base_pixmap = QPixmap(base_path)
            scaled_base = base_pixmap.scaled(293, 345, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.base_label.setPixmap(scaled_base)
            self.base_label.setGeometry(0, 0, 293, 345)
        else:
            self.base_label.setText("[Base image not found]")
            self.base_label.setStyleSheet("color: gray;")

        # Load left overlay
        if os.path.exists(left_path):
            left_pixmap = QPixmap(left_path)
            scaled_left = left_pixmap.scaled(293, 345, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.left_overlay.setPixmap(scaled_left)
            self.left_overlay.setGeometry(0, 0, 293, 345)
        else:
            print(f"Warning: Left overlay image not found at {left_path}")

        # Load right overlay
        if os.path.exists(right_path):
            right_pixmap = QPixmap(right_path)
            scaled_right = right_pixmap.scaled(293, 345, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.right_overlay.setPixmap(scaled_right)
            self.right_overlay.setGeometry(0, 0, 293, 345)
        else:
            print(f"Warning: Right overlay image not found at {right_path}")

    def update_event_visualization(self, left_event, right_event):
        """
        Update the visibility of overlay images based on event status

        Args:
            left_event (float): 1.0 if left sensor event, 0.0 otherwise
            right_event (float): 1.0 if right sensor event, 0.0 otherwise
        """
        # Show/hide left overlay
        if left_event == 1.0:
            self.left_overlay.show()
        else:
            self.left_overlay.hide()

        # Show/hide right overlay
        if right_event == 1.0:
            self.right_overlay.show()
        else:
            self.right_overlay.hide()


class StatisticsCards(QWidget):
    """Professional statistics cards for displaying sensor metrics"""

    def __init__(self, storage=None, parent=None):
        super().__init__(parent)
        self.storage = storage

        # Vertical layout for cards (stacked) - better for right column
        main_layout = QVBoxLayout()
        main_layout.setSpacing(12)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Card 1: Left sensor statistics
        self.left_card = self._create_card("🔵 SENSOR IZQUIERDO", COLOR_LEFT)
        self.left_prom = QLabel("--")
        self.left_max = QLabel("--")
        self.left_min = QLabel("--")
        self._populate_card(self.left_card, self.left_prom, self.left_max, self.left_min)

        # Card 2: Right sensor statistics
        self.right_card = self._create_card("🟠 SENSOR DERECHO", COLOR_RIGHT)
        self.right_prom = QLabel("--")
        self.right_max = QLabel("--")
        self.right_min = QLabel("--")
        self._populate_card(self.right_card, self.right_prom, self.right_max, self.right_min)

        # Add cards to layout (only individual sensor cards)
        main_layout.addWidget(self.left_card)
        main_layout.addWidget(self.right_card)

        self.setLayout(main_layout)

    def _create_card(self, title, accent_color):
        """Create a styled card widget"""
        card = QWidget()
        # Remove fixed width to allow cards to expand in right column
        card.setMinimumHeight(120)
        card.setMaximumHeight(140)
        card.setStyleSheet(f"""
            QWidget {{
                background-color: #1e293b;
                border-radius: 8px;
                border-left: 4px solid {accent_color};
            }}
        """)

        # Card layout
        card_layout = QVBoxLayout()
        card_layout.setContentsMargins(15, 12, 15, 12)
        card_layout.setSpacing(8)

        # Title
        title_label = QLabel(title)
        title_label.setFont(QFont("Arial", 11, QFont.Bold))
        title_label.setStyleSheet(f"color: {accent_color}; background: transparent; border: none;")
        card_layout.addWidget(title_label)

        # Add separator line
        separator = QWidget()
        separator.setFixedHeight(1)
        separator.setStyleSheet(f"background-color: {accent_color}; opacity: 0.3;")
        card_layout.addWidget(separator)

        card.setLayout(card_layout)
        return card

    def _populate_card(self, card, prom_label, max_label, min_label):
        """Add statistics labels to a card"""
        layout = card.layout()

        # Create stats container
        stats_widget = QWidget()
        stats_widget.setStyleSheet("background: transparent; border: none;")
        stats_layout = QVBoxLayout()
        stats_layout.setSpacing(6)
        stats_layout.setContentsMargins(0, 5, 0, 0)

        # Style for labels
        label_style = "color: #94a3b8; font-size: 11px; background: transparent; border: none;"
        value_style = "color: #e2e8f0; font-size: 18px; font-weight: bold; background: transparent; border: none;"

        # Promedio
        prom_container = QHBoxLayout()
        prom_label_text = QLabel("Promedio:")
        prom_label_text.setStyleSheet(label_style)
        prom_label.setStyleSheet(value_style)
        prom_label.setAlignment(Qt.AlignRight)
        prom_container.addWidget(prom_label_text)
        prom_container.addStretch()
        prom_container.addWidget(prom_label)
        stats_layout.addLayout(prom_container)

        # Máximo
        max_container = QHBoxLayout()
        max_label_text = QLabel("Máximo:")
        max_label_text.setStyleSheet(label_style)
        max_label.setStyleSheet(value_style)
        max_label.setAlignment(Qt.AlignRight)
        max_container.addWidget(max_label_text)
        max_container.addStretch()
        max_container.addWidget(max_label)
        stats_layout.addLayout(max_container)

        # Mínimo
        min_container = QHBoxLayout()
        min_label_text = QLabel("Mínimo:")
        min_label_text.setStyleSheet(label_style)
        min_label.setStyleSheet(value_style)
        min_label.setAlignment(Qt.AlignRight)
        min_container.addWidget(min_label_text)
        min_container.addStretch()
        min_container.addWidget(min_label)
        stats_layout.addLayout(min_container)

        stats_widget.setLayout(stats_layout)
        layout.addWidget(stats_widget)

    def update_statistics(self):
        """Update statistics cards for individual sensors using ALL session data"""

        if not self.storage or not self.storage.current_session_data:
            self.left_prom.setText("--")
            self.left_max.setText("--")
            self.left_min.setText("--")
            self.right_prom.setText("--")
            self.right_max.setText("--")
            self.right_min.setText("--")
            return

        # Get ALL session data (not limited to last 200 samples)
        data = self.storage.current_session_data

        # Filter data by sensor ID
        left_records = [r for r in data if r.get('sensorId', 1) == 1]
        right_records = [r for r in data if r.get('sensorId', 1) == 2]

        # Calculate left sensor stats
        if left_records:
            left_forces = [r['force'] for r in left_records]
            left_avg = sum(left_forces) / len(left_forces)
            left_max_val = max(left_forces)
            left_min_val = min(left_forces)

            self.left_prom.setText(f"{left_avg:.1f} kg")
            self.left_max.setText(f"{left_max_val:.1f} kg")
            self.left_min.setText(f"{left_min_val:.1f} kg")
        else:
            self.left_prom.setText("--")
            self.left_max.setText("--")
            self.left_min.setText("--")

        # Calculate right sensor stats
        if right_records:
            right_forces = [r['force'] for r in right_records]
            right_avg = sum(right_forces) / len(right_forces)
            right_max_val = max(right_forces)
            right_min_val = min(right_forces)

            self.right_prom.setText(f"{right_avg:.1f} kg")
            self.right_max.setText(f"{right_max_val:.1f} kg")
            self.right_min.setText(f"{right_min_val:.1f} kg")
        else:
            self.right_prom.setText("--")
            self.right_max.setText("--")
            self.right_min.setText("--")


class LivePlot(QWidget):
    def __init__(self, storage):
        super().__init__()
        self.storage = storage
        self.simulating = False

        # Matplotlib figure - increased height for better visibility
        self.fig = Figure(figsize=(7, 5))
        self.canvas = FigureCanvas(self.fig)
        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor("#071827")
        self.ax.tick_params(colors="#004166")
        self.ax.xaxis.set_major_locator(ticker.MaxNLocator(integer=True))
        self.ax.set_title("Fuerza en el tiempo (últimas muestras)", color="#0E2C46")
        self.ax.set_xlabel("Muestra", color="#0E2C46")
        self.ax.set_ylabel("Fuerza (kg)", color="#0E2C46")

        # Force label + semaphore bar
        self.force_label = QLabel("Fuerza: -- kg")
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

        # Event status indicator
        self.event_label = QLabel("✓ Sin evento | Monitoreo activo")
        self.event_label.setAlignment(Qt.AlignCenter)
        self.event_label.setFont(QFont("Arial", 10, QFont.Bold))
        self.event_label.setFixedHeight(32)
        self.event_label.setStyleSheet("""
            background-color: #1a3a1a;
            color: #4ade80;
            border-radius: 4px;
            padding: 6px;
        """)

        # Layered teeth visualization with event-based overlays
        self.teeth_viz = TeethVisualization()

        # Statistics cards (pass storage to track ALL session data)
        self.stats_cards = StatisticsCards(storage=self.storage)

        # Main vertical layout: graph on top, details below
        main_layout = QVBoxLayout()

        # Top section: Full-width graph and controls
        top_section = QVBoxLayout()
        top_section.addWidget(self.canvas, stretch=1)  # Graph expands to fill available space
        top_section.addWidget(self.force_label)
        top_section.addWidget(self.event_label)
        top_section.addWidget(self.force_bar)

        # Bottom section: Two columns (teeth left, stats right)
        bottom_section = QHBoxLayout()

        # Left: Teeth visualization (vertically centered)
        bottom_left_column = QVBoxLayout()
        bottom_left_column.addStretch()  # Space above
        bottom_left_column.addWidget(self.teeth_viz, alignment=Qt.AlignCenter)
        bottom_left_column.addStretch()  # Space below

        # Right: Statistics cards (vertically centered)
        bottom_right_column = QVBoxLayout()
        bottom_right_column.addStretch()  # Space above
        bottom_right_column.addWidget(self.stats_cards)
        bottom_right_column.addStretch()  # Space below

        # Assemble bottom section (50/50 split)
        bottom_section.addLayout(bottom_left_column, 1)
        bottom_section.addLayout(bottom_right_column, 1)

        # Assemble main layout
        main_layout.addLayout(top_section)
        main_layout.addLayout(bottom_section)

        self.setLayout(main_layout)

    # llamada periódica para dibujar
    def update_plot(self):
        # if simulating, maybe generate a new sample into storage
        if self.simulating:
            self._simulate_one_sample()

        # Get all current session data
        data = getattr(self.storage, "current_session_data", [])

        if not data:
            self.ax.clear()
            self.ax.set_title("Esperando datos...", color="#0E2C46")
            self.canvas.draw()
            # keep label default
            self.force_label.setText("Fuerza: -- kg")
            self.force_bar.setValue(0)
            return

        # Filter data by sensor ID
        left_data = [r for r in data if r.get('sensorId', 1) == 1]
        right_data = [r for r in data if r.get('sensorId', 1) == 2]

        # Limit to last 200 records per sensor
        left_data = left_data[-200:]
        right_data = right_data[-200:]

        # Get force values in kg (already calculated by hardware)
        left_forces_kg = [r['force'] for r in left_data]
        right_forces_kg = [r['force'] for r in right_data]

        # Clear the plot
        self.ax.clear()
        self.ax.set_facecolor("#294B69")

        # Plot left sensor data if available
        if left_forces_kg:
            self.ax.plot(left_forces_kg, color=COLOR_LEFT, linewidth=2)

        # Plot right sensor data if available
        if right_forces_kg:
            self.ax.plot(right_forces_kg, color=COLOR_RIGHT, linewidth=2)

        # Add legend if both sensors have data
        if left_forces_kg and right_forces_kg:
            self.ax.legend(loc='upper right', fontsize=9)

        # Set plot styling
        self.ax.set_title("Fuerza en el tiempo (últimas muestras)", color="#0003cf")
        self.ax.set_xlabel("Muestra", color="#0003cf")
        self.ax.set_ylabel("Fuerza (kg)", color="#0003cf")
        self.ax.grid(alpha=0.2)

        # Set y limits with padding
        all_forces = left_forces_kg + right_forces_kg
        max_y = max(all_forces) if all_forces else 1
        self.ax.set_ylim(0, max(1, max_y * 1.2))

        self.canvas.draw()

        # Calculate latest force values
        latest_left = left_forces_kg[-1] if left_forces_kg else 0
        latest_right = right_forces_kg[-1] if right_forces_kg else 0

        # Update force display label
        if latest_left > 0 and latest_right > 0:
            # Dual sensor mode - show both with color coding
            label_text = f"<span style='color:{COLOR_LEFT}'>Izq: {latest_left:.2f} kg</span>  <span style='color:{COLOR_RIGHT}'>Der: {latest_right:.2f} kg</span>"
            self.force_label.setText(label_text)
        elif latest_left > 0:
            # Single sensor mode (backwards compatible)
            self.force_label.setText(f"Fuerza: {latest_left:.2f} kg")
        else:
            self.force_label.setText("Fuerza: -- kg")

        # Calculate maximum force for progress bar
        max_force_value = max(latest_left, latest_right)

        # Update progress bar with maximum force
        max_force = 5.0  # kg (approximately 50 N)
        level = min(max_force_value / max_force * 100, 100)
        self.force_bar.setValue(int(level))

        # Update progress bar color based on thresholds
        if max_force_value < 1.5:  # Low (< 1.5 kg ≈ 15 N)
            color = "#00ff7f"
        elif max_force_value < 3.5:  # Medium (< 3.5 kg ≈ 35 N)
            color = "#ffd700"
        else:  # High (≥ 3.5 kg)
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

        # Update event status indicator
        latest_event_left = left_data[-1].get('event', 0.0) if left_data else 0.0
        latest_event_right = right_data[-1].get('event', 0.0) if right_data else 0.0

        if latest_event_left == 1.0 and latest_event_right == 1.0:
            self.event_label.setText("⚠ EVENTO DE BRUXISMO | Ambos Sensores")
            self.event_label.setStyleSheet("""
                background-color: #7f1d1d;
                color: #fca5a5;
                border: 2px solid #dc2626;
                border-radius: 4px;
                padding: 6px;
                font-weight: bold;
            """)
        elif latest_event_left == 1.0:
            self.event_label.setText("⚠ EVENTO DE BRUXISMO | Sensor Izquierdo")
            self.event_label.setStyleSheet("""
                background-color: #7f1d1d;
                color: #fca5a5;
                border: 2px solid #dc2626;
                border-radius: 4px;
                padding: 6px;
                font-weight: bold;
            """)
        elif latest_event_right == 1.0:
            self.event_label.setText("⚠ EVENTO DE BRUXISMO | Sensor Derecho")
            self.event_label.setStyleSheet("""
                background-color: #7f1d1d;
                color: #fca5a5;
                border: 2px solid #dc2626;
                border-radius: 4px;
                padding: 6px;
                font-weight: bold;
            """)
        else:
            self.event_label.setText("✓ Sin evento | Monitoreo activo")
            self.event_label.setStyleSheet("""
                background-color: #1a3a1a;
                color: #4ade80;
                border-radius: 4px;
                padding: 6px;
            """)

        # Update teeth visualization with event states
        self.teeth_viz.update_event_visualization(latest_event_left, latest_event_right)

        # Update statistics cards (uses ALL session data, not just visible samples)
        self.stats_cards.update_statistics()

    def _simulate_one_sample(self):
        """Genera y añade un único valor de simulación al storage."""
        t = time.time() % 10
        if 2 < t < 3 or 7 < t < 8:
            force_kg = random.uniform(2.5, 4.5)  # High force event
            event = 1.0
        else:
            force_kg = random.uniform(0.1, 1.0)  # Normal force
            event = 0.0

        # Create properly formatted record
        record = {
            "sensorId": random.choice([1, 2]),
            "force": force_kg,
            "timestamp": int(time.time() * 1000),
            "date": datetime.utcnow().isoformat(),
            "event": event
        }
        self.storage.add_record(record)

    def start_simulation(self):
        self.simulating = True
        # iniciar sesión en storage si existe
        if hasattr(self.storage, "start_new_session"):
            self.storage.start_new_session()

    def stop_simulation(self, save=True):
        self.simulating = False
        if hasattr(self.storage, "end_session"):
            self.storage.end_session(save)
