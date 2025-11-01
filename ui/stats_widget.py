# ui/stats_widget.py
from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel
from PySide6.QtGui import QFont

class StatsWidget(QFrame):
    def __init__(self, storage=None):
        super().__init__()
        self.storage = storage
        self.setObjectName("card")
        self.layout = QVBoxLayout()

        # Combined statistics label (bold, larger)
        self.combined_label = QLabel("Combinado:  Prom --  Máx --  Mín --")
        combined_font = QFont("Arial", 12, QFont.Bold)
        self.combined_label.setFont(combined_font)
        self.combined_label.setStyleSheet("color:#1c4db0;")

        # Left sensor statistics label (blue)
        self.left_label = QLabel("Izq:        Prom --  Máx --  Mín --")
        left_font = QFont("Arial", 10)
        self.left_label.setFont(left_font)

        # Right sensor statistics label (orange)
        self.right_label = QLabel("Der:        Prom --  Máx --  Mín --")
        right_font = QFont("Arial", 10)
        self.right_label.setFont(right_font)

        # Add labels to layout
        self.layout.addWidget(self.combined_label)
        self.layout.addSpacing(3)
        self.layout.addWidget(self.left_label)
        self.layout.addWidget(self.right_label)

        self.setLayout(self.layout)

    def _n_to_kg(self, n_value):
        return n_value / 9.81

    def update(self, storage=None):
        if storage is None:
            storage = self.storage
        if not storage or not storage.current_session_data:
            self.combined_label.setText("Combinado:  Prom --  Máx --  Mín --")
            self.left_label.setText("Izq:        Prom --  Máx --  Mín --")
            self.right_label.setText("Der:        Prom --  Máx --  Mín --")
            return

        data = storage.current_session_data

        # Filter data by sensor ID
        left_records = [r for r in data if r.get('sensorId', 1) == 1]
        right_records = [r for r in data if r.get('sensorId', 1) == 2]

        # Extract force values - Combined
        all_forces = [r['force'] for r in data]

        # Extract force values - Left sensor
        left_forces = [r['force'] for r in left_records]

        # Extract force values - Right sensor
        right_forces = [r['force'] for r in right_records]

        # Calculate combined statistics
        if all_forces:
            combined_avg = sum(all_forces) / len(all_forces)
            combined_max = max(all_forces)
            combined_min = min(all_forces)
        else:
            combined_avg = 0
            combined_max = 0
            combined_min = 0

        # Calculate left sensor statistics
        if left_forces:
            left_avg = sum(left_forces) / len(left_forces)
            left_max = max(left_forces)
            left_min = min(left_forces)
        else:
            left_avg = 0
            left_max = 0
            left_min = 0

        # Calculate right sensor statistics
        if right_forces:
            right_avg = sum(right_forces) / len(right_forces)
            right_max = max(right_forces)
            right_min = min(right_forces)
        else:
            right_avg = 0
            right_max = 0
            right_min = 0

        # Format combined statistics text
        combined_text = f"Combinado:  Prom {combined_avg:.1f}  Máx {combined_max:.1f}  Mín {combined_min:.1f}"
        self.combined_label.setText(combined_text)

        # Format left sensor statistics text
        if left_forces:
            left_text = f"<span style='color:#2196F3'>Izq:        Prom {left_avg:.1f}  Máx {left_max:.1f}  Mín {left_min:.1f}</span>"
            self.left_label.setText(left_text)
        else:
            # Hide or show placeholder for backwards compatibility
            self.left_label.setText("")

        # Format right sensor statistics text
        if right_forces:
            right_text = f"<span style='color:#FF5722'>Der:        Prom {right_avg:.1f}  Máx {right_max:.1f}  Mín {right_min:.1f}</span>"
            self.right_label.setText(right_text)
        else:
            # Hide if no right sensor data (backwards compatibility)
            self.right_label.setText("")

    def auto_update(self):
        """Se llama periódicamente desde el MainWindow."""
        self.update(self.storage)
