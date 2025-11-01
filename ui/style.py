# ui/style.py
APP_QSS = """
QMainWindow {
    background-color: #0b1220;
    color: #e6eef6;
    font-family: "Segoe UI", "Roboto", sans-serif;
    font-size: 13px;
}
QLabel#appTitle {
    color: #7ee7ff;
    font-size: 18px;
    font-weight: 700;
    padding: 10px;
}
QWidget#leftPanel {
    background-color: #071028;
    border-right: 1px solid #122032;
}
QPushButton {
    background-color: #FFFFFF;
    color: #e6eef6;
    border: 1px solid #213247;
    border-radius: 8px;
    padding: 8px 12px;
}
QPushButton:hover {
    background-color: #1e90ff;
    color: #07202b;
}
QPushButton:disabled {
    background-color: #16202a;
    color: #6b7280;
}
QFrame#card {
    background-color: #071827;
    border-radius: 8px;
    padding: 8px;
}
QLabel#status {
    color: #94a3b8;
}
"""
