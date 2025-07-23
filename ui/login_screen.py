# ui/login_screen.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLineEdit, QPushButton, QLabel, QStackedWidget, QCheckBox
from PyQt6.QtCore import pyqtSignal, Qt

class LoginScreen(QWidget):
    login_successful = pyqtSignal(str)
    def __init__(self, db_manager):
        super().__init__(); self.db = db_manager; self.stack = QStackedWidget()
        login_widget = QWidget(); login_layout = QVBoxLayout(login_widget); login_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.username_input = QLineEdit(); self.username_input.setPlaceholderText("Username"); self.username_input.setFixedWidth(300)
        self.password_input = QLineEdit(); self.password_input.setPlaceholderText("Password"); self.password_input.setEchoMode(QLineEdit.EchoMode.Password); self.password_input.setFixedWidth(300)
        self.remember_me_checkbox = QCheckBox("Remember Me"); self.remember_me_checkbox.setChecked(True); login_layout.addWidget(self.remember_me_checkbox, alignment=Qt.AlignmentFlag.AlignCenter)
        login_button = QPushButton("Log In"); login_button.clicked.connect(self.handle_login); login_button.setFixedWidth(300)
        create_account_button = QPushButton("Create Account"); create_account_button.clicked.connect(lambda: self.stack.setCurrentIndex(1)); create_account_button.setFixedWidth(300)
        self.feedback_label = QLabel(""); self.feedback_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        login_layout.addWidget(QLabel("<h2>Tether C2 Login</h2>"), alignment=Qt.AlignmentFlag.AlignCenter); login_layout.addWidget(self.username_input, alignment=Qt.AlignmentFlag.AlignCenter); login_layout.addWidget(self.password_input, alignment=Qt.AlignmentFlag.AlignCenter)
        login_layout.addWidget(login_button, alignment=Qt.AlignmentFlag.AlignCenter); login_layout.addWidget(create_account_button, alignment=Qt.AlignmentFlag.AlignCenter); login_layout.addWidget(self.feedback_label, alignment=Qt.AlignmentFlag.AlignCenter)

        create_widget = QWidget(); create_layout = QVBoxLayout(create_widget); create_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.new_username = QLineEdit(); self.new_username.setPlaceholderText("Username"); self.new_username.setFixedWidth(300)
        self.new_password = QLineEdit(); self.new_password.setPlaceholderText("Password"); self.new_password.setEchoMode(QLineEdit.EchoMode.Password); self.new_password.setFixedWidth(300)
        self.confirm_password = QLineEdit(); self.confirm_password.setPlaceholderText("Confirm Password"); self.confirm_password.setEchoMode(QLineEdit.EchoMode.Password); self.confirm_password.setFixedWidth(300)
        create_button = QPushButton("Create Account"); create_button.clicked.connect(self.handle_create_account); create_button.setFixedWidth(300)
        back_button = QPushButton("< Back to Login"); back_button.clicked.connect(lambda: self.stack.setCurrentIndex(0)); back_button.setFixedWidth(300)
        self.create_feedback = QLabel(""); self.create_feedback.setAlignment(Qt.AlignmentFlag.AlignCenter)
        create_layout.addWidget(QLabel("<h2>Create New Account</h2>"), alignment=Qt.AlignmentFlag.AlignCenter); create_layout.addWidget(self.new_username, alignment=Qt.AlignmentFlag.AlignCenter); create_layout.addWidget(self.new_password, alignment=Qt.AlignmentFlag.AlignCenter); create_layout.addWidget(self.confirm_password, alignment=Qt.AlignmentFlag.AlignCenter); create_layout.addWidget(create_button, alignment=Qt.AlignmentFlag.AlignCenter); create_layout.addWidget(back_button, alignment=Qt.AlignmentFlag.AlignCenter); create_layout.addWidget(self.create_feedback, alignment=Qt.AlignmentFlag.AlignCenter)
        
        self.stack.addWidget(login_widget); self.stack.addWidget(create_widget)
        main_layout = QVBoxLayout(self); main_layout.addWidget(self.stack)
        self.load_remembered_user()

    def load_remembered_user(self):
        remembered_user = self.db.load_setting("remembered_user")
        if remembered_user: self.username_input.setText(remembered_user); self.remember_me_checkbox.setChecked(True)
        else: self.remember_me_checkbox.setChecked(False)

    def handle_login(self):
        username = self.username_input.text()
        if self.db.check_user(username, self.password_input.text()):
            if not self.remember_me_checkbox.isChecked():
                self.db.save_setting("remembered_user", "")
            self.feedback_label.setText(""); self.login_successful.emit(username)
        else: self.feedback_label.setText("<font color='red'>Invalid username or password.</font>")

    def handle_create_account(self):
        username = self.new_username.text(); password = self.new_password.text()
        if not username or not password: self.create_feedback.setText("<font color='red'>Fields cannot be empty.</font>"); return
        if password != self.confirm_password.text(): self.create_feedback.setText("<font color='red'>Passwords do not match.</font>"); return
        if self.db.create_user(username, password):
            self.stack.setCurrentIndex(0); self.feedback_label.setText("<font color='green'>Account created. Please log in.</font>")
        else: self.create_feedback.setText("<font color='red'>Username already exists.</font>")