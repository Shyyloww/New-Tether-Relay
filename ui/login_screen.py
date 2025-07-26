# ui/login_screen.py (Reworked for API Client)
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLineEdit, QPushButton, QLabel, QStackedWidget
from PyQt6.QtCore import pyqtSignal, Qt

class LoginScreen(QWidget):
    login_successful = pyqtSignal(str)

    def __init__(self, api_client):
        super().__init__()
        self.api = api_client
        self.stack = QStackedWidget()
        
        login_widget = QWidget()
        login_layout = QVBoxLayout(login_widget)
        login_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")
        self.username_input.setFixedWidth(300)
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setFixedWidth(300)
        
        login_button = QPushButton("Log In")
        login_button.clicked.connect(self.handle_login)
        login_button.setFixedWidth(300)
        
        create_account_button = QPushButton("Create Account")
        create_account_button.clicked.connect(lambda: self.stack.setCurrentIndex(1))
        create_account_button.setFixedWidth(300)
        
        self.feedback_label = QLabel("")
        self.feedback_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        login_layout.addWidget(QLabel("<h2>Tether C2 Login</h2>"), alignment=Qt.AlignmentFlag.AlignCenter)
        login_layout.addWidget(self.username_input, alignment=Qt.AlignmentFlag.AlignCenter)
        login_layout.addWidget(self.password_input, alignment=Qt.AlignmentFlag.AlignCenter)
        login_layout.addWidget(login_button, alignment=Qt.AlignmentFlag.AlignCenter)
        login_layout.addWidget(create_account_button, alignment=Qt.AlignmentFlag.AlignCenter)
        login_layout.addWidget(self.feedback_label, alignment=Qt.AlignmentFlag.AlignCenter)

        create_widget = QWidget()
        create_layout = QVBoxLayout(create_widget)
        create_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.new_username = QLineEdit()
        self.new_username.setPlaceholderText("New Username")
        self.new_username.setFixedWidth(300)
        self.new_password = QLineEdit()
        self.new_password.setPlaceholderText("New Password (min. 4 chars)")
        self.new_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.new_password.setFixedWidth(300)
        
        create_button = QPushButton("Create Account")
        create_button.clicked.connect(self.handle_create_account)
        create_button.setFixedWidth(300)
        
        back_button = QPushButton("< Back to Login")
        back_button.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        back_button.setFixedWidth(300)
        
        self.create_feedback = QLabel("")
        self.create_feedback.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        create_layout.addWidget(QLabel("<h2>Create New Account</h2>"), alignment=Qt.AlignmentFlag.AlignCenter)
        create_layout.addWidget(self.new_username, alignment=Qt.AlignmentFlag.AlignCenter)
        create_layout.addWidget(self.new_password, alignment=Qt.AlignmentFlag.AlignCenter)
        create_layout.addWidget(create_button, alignment=Qt.AlignmentFlag.AlignCenter)
        create_layout.addWidget(back_button, alignment=Qt.AlignmentFlag.AlignCenter)
        create_layout.addWidget(self.create_feedback, alignment=Qt.AlignmentFlag.AlignCenter)
        
        self.stack.addWidget(login_widget)
        self.stack.addWidget(create_widget)
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.stack)

    def handle_login(self):
        username = self.username_input.text()
        password = self.password_input.text()
        if not username or not password:
            self.feedback_label.setText("<font color='red'>Username and password are required.</font>")
            return
        
        response = self.api.login(username, password)
        if response and response.get("success"):
            self.feedback_label.setText("")
            self.password_input.clear()
            self.login_successful.emit(response.get("username"))
        else:
            error = response.get("error", "Login failed.") if response else "Could not connect to server."
            self.feedback_label.setText(f"<font color='red'>{error}</font>")

    def handle_create_account(self):
        username = self.new_username.text()
        password = self.new_password.text()
        if not username or not password:
            self.create_feedback.setText("<font color='red'>Fields cannot be empty.</font>")
            return

        response = self.api.register(username, password)
        if response and response.get("success"):
            self.stack.setCurrentIndex(0)
            self.feedback_label.setText("<font color='green'>Account created. Please log in.</font>")
            self.create_feedback.setText("")
            self.new_username.clear()
            self.new_password.clear()
        else:
            error = response.get("error", "Registration failed.") if response else "Could not connect to server."
            self.create_feedback.setText(f"<font color='red'>{error}</font>")