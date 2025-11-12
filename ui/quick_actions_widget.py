# ui/quick_actions_widget.py
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
from PySide6.QtCore import Signal, Qt

class QuickActionsWidget(QWidget):
    # señales que MainWindow escuchará
    start_real = Signal()
    stop = Signal()
    clear = Signal()
    load_demo = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8,8,8,8)

        title = QLabel("<b>Acciones Rápidas</b>")
        title.setObjectName("quickTitle")
        layout.addWidget(title, alignment=Qt.AlignTop)

        # Buttons row
        self.btn_start_real = QPushButton("🔌 Iniciar sesión real")
        self.btn_stop = QPushButton("⏹️ Detener sesión")
        self.btn_clear = QPushButton("🧹 Limpiar datos")
        self.btn_load_demo = QPushButton("📊 Cargar Noche Simulada")

        for b in (self.btn_start_real, self.btn_stop, self.btn_clear, self.btn_load_demo):
            b.setMinimumHeight(36)
            b.setStyleSheet("font-weight:600; border-radius:6px; text-align:left; padding-left:8px;")

        # conexión interna: emiten señales
        self.btn_start_real.clicked.connect(lambda: self.start_real.emit())
        self.btn_stop.clicked.connect(lambda: self.stop.emit())
        self.btn_clear.clicked.connect(lambda: self.clear.emit())
        self.btn_load_demo.clicked.connect(lambda: self.load_demo.emit())

        # botón vertical (mejor para sidebar pequeño)
        layout.addWidget(self.btn_start_real)
        layout.addWidget(self.btn_stop)
        layout.addWidget(self.btn_clear)

        # Separator for demo section
        separator = QLabel()
        separator.setFixedHeight(1)
        separator.setStyleSheet("background-color: #444; margin: 8px 0;")
        layout.addWidget(separator)

        demo_label = QLabel("<b>Demostración</b>")
        demo_label.setStyleSheet("color: #888; font-size: 10px; margin-top: 4px;")
        layout.addWidget(demo_label)

        layout.addWidget(self.btn_load_demo)
        layout.addStretch()
