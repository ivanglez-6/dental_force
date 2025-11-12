# ui/image_viewer_dialog.py
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton, QScrollArea
)
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt


class ImageViewerDialog(QDialog):
    """Dialog to display a dashboard image with scroll capability."""

    def __init__(self, parent, image_path):
        super().__init__(parent)
        self.image_path = image_path
        self.init_ui()

    def init_ui(self):
        """Initialize the user interface."""
        # Set window properties
        self.setWindowTitle("Dashboard de Análisis de Bruxismo")
        self.resize(1400, 900)

        # Create layout
        layout = QVBoxLayout()

        # Create label to hold the image
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)

        # Load and display the image
        try:
            pixmap = QPixmap(self.image_path)
            if pixmap.isNull():
                raise ValueError("Error cargando imagen generada")
            # Scale the image to fit within reasonable bounds while preserving aspect ratio
            scaled_pixmap = pixmap.scaled(1150, 750, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.image_label.setPixmap(scaled_pixmap)
            self.image_label.setScaledContents(False)  # Preserve aspect ratio
        except Exception as e:
            self.image_label.setText(f"Error cargando imagen: {str(e)}")

        # Create scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidget(self.image_label)
        scroll_area.setWidgetResizable(True)

        # Create close button
        close_button = QPushButton("Cerrar")
        close_button.clicked.connect(self.close)

        # Add widgets to layout
        layout.addWidget(scroll_area)
        layout.addWidget(close_button)

        self.setLayout(layout)
