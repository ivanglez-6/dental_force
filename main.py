# main.py
import sys
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow
from ui.style import APP_QSS

if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Aplicar estilo
    app.setStyleSheet(APP_QSS)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())
