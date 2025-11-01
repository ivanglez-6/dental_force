# ui/stats_widget.py
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel

class StatsWidget(QFrame):
    def __init__(self, storage=None):
        super().__init__()
        self.storage = storage
        self.setObjectName("card")
        self.layout = QHBoxLayout()

        self.avg_label = QLabel("Avg: -- N | -- kg")
        self.max_label = QLabel("Max: -- N | -- kg")
        self.min_label = QLabel("Min: -- N | -- kg")

        for lbl in (self.avg_label, self.max_label, self.min_label):
            lbl.setStyleSheet("font-weight:600; color:#1c4db0; bold")
            self.layout.addWidget(lbl)

        self.setLayout(self.layout)

    def _n_to_kg(self, n_value):
        return n_value / 9.81

    def update(self, storage=None):
        if storage is None:
            storage = self.storage
        if not storage or not storage.current_session_data:
            self.avg_label.setText("Avg: -- N | -- kg")
            self.max_label.setText("Max: -- N | -- kg")
            self.min_label.setText("Min: -- N | -- kg")
            return

        data = storage.current_session_data
        forces = [d["force"] for d in data]
        avg_n = sum(forces) / len(forces)
        max_n = max(forces)
        min_n = min(forces)

        avg_kg = self._n_to_kg(avg_n)
        max_kg = self._n_to_kg(max_n)
        min_kg = self._n_to_kg(min_n)

        self.avg_label.setText(f"Avg: {avg_n:.2f} N | {avg_kg:.3f} kg")
        self.max_label.setText(f"Max: {max_n:.2f} N | {max_kg:.3f} kg")
        self.min_label.setText(f"Min: {min_n:.2f} N | {min_kg:.3f} kg")

    def auto_update(self):
        """Se llama periódicamente desde el MainWindow."""
        self.update(self.storage)
