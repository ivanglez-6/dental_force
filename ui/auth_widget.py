# ui/auth_widget.py
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox, QFrame
from services.data_storage import DataStorage

class AuthWidget(QFrame):
    def __init__(self, storage: DataStorage):
        super().__init__()
        self.storage = storage
        self.setObjectName("card")
        self.layout = QVBoxLayout()
        self.title = QLabel("User")
        self.username = QLineEdit()
        self.username.setPlaceholderText("Username")
        self.password = QLineEdit()
        self.password.setPlaceholderText("Password")
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        self.login_btn = QPushButton("Login")
        self.signup_btn = QPushButton("Sign up")
        self.login_btn.clicked.connect(self.login)
        self.signup_btn.clicked.connect(self.signup)
        self.layout.addWidget(self.title)
        self.layout.addWidget(self.username)
        self.layout.addWidget(self.password)
        self.layout.addWidget(self.login_btn)
        self.layout.addWidget(self.signup_btn)
        self.setLayout(self.layout)
        self.current_user = None

    def login(self):
        u = self.username.text().strip()
        p = self.password.text().strip()
        if not u or not p:
            QMessageBox.warning(self, "Credentials", "Enter username and password")
            return
        row = self.storage.check_login(u, p)
        if row:
            self.current_user = {"id": row[0], "username": row[1], "full_name": row[2]}
            QMessageBox.information(self, "Logged", f"Welcome {self.current_user.get('username')}")
        else:
            QMessageBox.warning(self, "Failed", "Invalid credentials")

    def signup(self):
        u = self.username.text().strip()
        p = self.password.text().strip()
        if not u or not p:
            QMessageBox.warning(self, "Credentials", "Enter username and password")
            return
        ok = self.storage.create_user(u, p, full_name=u)
        if ok:
            QMessageBox.information(self, "Created", "User created. You can login now.")
        else:
            QMessageBox.warning(self, "Exists", "Username already exists.")
