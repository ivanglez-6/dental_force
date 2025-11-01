# ui/history_widget.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
    QPushButton, QHeaderView, QMessageBox
)
from PySide6.QtCore import Qt

class HistoryWidget(QWidget):
    def __init__(self, storage):
        super().__init__()
        self.storage = storage
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        title = QLabel("📜 Historial de Sesiones")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px;")

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["ID", "Fecha", "Lecturas", "Duración (s)"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.cellDoubleClicked.connect(self.view_session_details)

        self.refresh_button = QPushButton("🔄 Actualizar historial")
        self.refresh_button.clicked.connect(self.load_history)

        layout.addWidget(title)
        layout.addWidget(self.table)
        layout.addWidget(self.refresh_button)
        self.setLayout(layout)

        self.load_history()

    def load_history(self):
        """Carga los datos del historial desde el almacenamiento."""
        try:
            sessions = self.storage.get_sessions()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"No se puede cargar el historial: {e}")
            return

        self.table.setRowCount(len(sessions))

        for row, session in enumerate(sessions):
            summary = session.get("summary", {})
            start = summary.get("start", "")
            end = summary.get("end", "")
            total_readings = summary.get("totalReadings", 0)
            duration = 0
            if start and end:
                try:
                    from datetime import datetime
                    start_dt = datetime.fromisoformat(start)
                    end_dt = datetime.fromisoformat(end)
                    duration = round((end_dt - start_dt).total_seconds(), 2)
                except Exception:
                    duration = 0

            self.table.setItem(row, 0, QTableWidgetItem(str(session["id"])))
            self.table.setItem(row, 1, QTableWidgetItem(start))
            self.table.setItem(row, 2, QTableWidgetItem(str(total_readings)))
            self.table.setItem(row, 3, QTableWidgetItem(str(duration)))

    def view_session_details(self, row, _):
        """Muestra detalles de una sesión seleccionada."""
        session_id_item = self.table.item(row, 0)
        if not session_id_item:
            return
        session_id = int(session_id_item.text())

        session_data = self.storage.get_session_data(session_id)
        summary = next((s for s in self.storage.get_sessions() if s["id"] == session_id), {})
        summary_info = summary.get("summary", {})

        QMessageBox.information(
            self,
            "Detalles de Sesión",
            f"🆔 ID: {session_id}\n"
            f"📅 Inicio: {summary_info.get('start', '')}\n"
            f"⏱️ Duración: {self.table.item(row, 3).text()} s\n"
            f"📊 Total lecturas: {summary_info.get('totalReadings', 0)}\n"
            f"🔹 Datos de fuerza disponibles: {len(session_data)}"
        )
