# ui/reports_widget.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QComboBox, QMessageBox, QFileDialog
)
from PySide6.QtCore import Qt
import matplotlib.pyplot as plt
import tempfile
import os

class ReportsWidget(QWidget):
    def __init__(self, storage):
        super().__init__()
        self.storage = storage
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        title = QLabel("📈 Generador de Reportes")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px;")

        self.session_selector = QComboBox()
        self.refresh_button = QPushButton("🔄 Cargar sesiones")
        self.report_button = QPushButton("📊 Generar gráfico")
        self.export_button = QPushButton("💾 Exportar reporte")

        self.refresh_button.clicked.connect(self.load_sessions)
        self.report_button.clicked.connect(self.generate_report)
        self.export_button.clicked.connect(self.export_report)

        layout.addWidget(title)
        layout.addWidget(self.session_selector)
        layout.addWidget(self.refresh_button)
        layout.addWidget(self.report_button)
        layout.addWidget(self.export_button)

        self.setLayout(layout)
        self.load_sessions()

    def load_sessions(self):
        """Carga las sesiones disponibles para generar reportes."""
        try:
            sessions = self.storage.get_sessions()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"No se puede acceder al historial de sesiones: {e}")
            return

        self.session_selector.clear()
        for s in sessions:
            start = s.get("summary", {}).get("start", "")
            total = s.get("summary", {}).get("totalReadings", 0)
            self.session_selector.addItem(f"ID {s['id']} - {start} ({total} lecturas)")

    def generate_report(self):
        """Genera un gráfico simple del registro seleccionado."""
        idx = self.session_selector.currentIndex()
        if idx < 0:
            QMessageBox.warning(self, "Atención", "Selecciona una sesión para graficar.")
            return

        sessions = self.storage.get_sessions()
        session_id = sessions[idx]["id"]
        registros = self.storage.get_session_data(session_id)

        if not registros:
            QMessageBox.warning(self, "Sin datos", "Esta sesión no contiene registros.")
            return

        # Extraemos la fuerza de cada registro
        fuerzas = [r.get("force", 0) for r in registros]

        plt.figure(figsize=(8, 4))
        plt.plot(fuerzas, color='blue', label='Fuerza registrada (N)')
        plt.title(f"Sesión {session_id}")
        plt.xlabel("Muestra")
        plt.ylabel("Fuerza (N)")
        plt.legend()
        plt.grid(True)
        plt.show()

    def export_report(self):
        """Exporta la sesión seleccionada como archivo CSV, permitiendo elegir la ubicación."""
        idx = self.session_selector.currentIndex()
        if idx < 0:
            QMessageBox.warning(self, "Atención", "Selecciona una sesión para exportar.")
            return

        sessions = self.storage.get_sessions()
        session_id = sessions[idx]["id"]
        registros = self.storage.get_session_data(session_id)

        if not registros:
            QMessageBox.warning(self, "Sin datos", "Esta sesión no contiene registros.")
            return

        # Abrimos un diálogo para seleccionar ruta y nombre del archivo
        default_name = f"reporte_sesion_{session_id}.csv"
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar reporte",
            default_name,
            "Archivos CSV (*.csv)"
        )

        if not file_path:
            # El usuario canceló
            return

        # Guardamos el CSV
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("index,sensorId,force,timestamp,date,event\n")
            for i, r in enumerate(registros):
                f.write(f"{i},{r.get('sensorId',1)},{r.get('force',0)},{r.get('timestamp','')},{r.get('date','')},{r.get('event',0.0)}\n")

        QMessageBox.information(self, "Exportación completa",
                                f"El reporte se guardó en:\n{file_path}")