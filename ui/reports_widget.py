# ui/reports_widget.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QComboBox, QMessageBox, QFileDialog
)
from PySide6.QtCore import Qt
import matplotlib.pyplot as plt
import tempfile
import os
from pathlib import Path
from services.dashboard_generator import generate_dashboard
from ui.image_viewer_dialog import ImageViewerDialog

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
        """Genera un dashboard completo de bruxismo del registro seleccionado."""
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

        # Validar que los registros tienen los campos necesarios
        for r in registros:
            if 'sensorId' not in r:
                r['sensorId'] = 1
            if 'force' not in r:
                r['force'] = 0
            if 'timestamp' not in r:
                r['timestamp'] = ''
            if 'date' not in r:
                r['date'] = ''
            if 'event' not in r:
                r['event'] = 0.0

        # Create temporary directory for CSV and PNG
        temp_dir = tempfile.mkdtemp()
        temp_csv = Path(temp_dir) / f"session_{session_id}.csv"
        output_png = Path(temp_dir) / f"dashboard_{session_id}.png"

        try:
            # Write CSV file silently (same logic as export_report)
            with open(temp_csv, "w", encoding="utf-8") as f:
                f.write("index,sensorId,force,timestamp,date,event\n")
                for i, r in enumerate(registros):
                    f.write(f"{i},{r.get('sensorId',1)},{r.get('force',0)},{r.get('timestamp','')},{r.get('date','')},{r.get('event',0.0)}\n")

            # Generate and display dashboard for sensor 1
            output_png_sensor1 = Path(temp_dir) / f"dashboard_{session_id}_sensor1.png"
            generate_dashboard(str(temp_csv), str(output_png_sensor1), sensor_id=1)

            viewer1 = ImageViewerDialog(self, str(output_png_sensor1))
            viewer1.exec()

            # Generate and display dashboard for sensor 2
            output_png_sensor2 = Path(temp_dir) / f"dashboard_{session_id}_sensor2.png"
            generate_dashboard(str(temp_csv), str(output_png_sensor2), sensor_id=2)

            viewer2 = ImageViewerDialog(self, str(output_png_sensor2))
            viewer2.exec()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error generando dashboard: {str(e)}")
            import traceback
            traceback.print_exc()

    def export_report(self):
        """Exporta la sesión seleccionada como reporte PDF con análisis clínico dual-sensor."""
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

        # Abrimos un diálogo para seleccionar ruta y nombre del archivo PDF
        default_name = f"reporte_bruxismo_sesion_{session_id}.pdf"
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar reporte PDF",
            default_name,
            "Archivos PDF (*.pdf)"
        )

        if not file_path:
            # El usuario canceló
            return

        try:
            # Import PDF generator
            from services.pdf_generator import generate_bruxism_pdf_report

            # Generate the PDF
            generate_bruxism_pdf_report(registros, file_path)

            QMessageBox.information(self, "Exportación completa",
                                    f"El reporte PDF se guardó exitosamente en:\n{file_path}")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error generando PDF: {str(e)}")
            import traceback
            traceback.print_exc()