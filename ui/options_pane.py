# ui/options_pane.py (Full Code)
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QGroupBox, QComboBox, 
                             QCheckBox, QPushButton, QLabel, QMessageBox, QFormLayout)
from PyQt6.QtCore import pyqtSignal

class OptionsPane(QWidget):
    sign_out_requested = pyqtSignal()
    sanitize_requested = pyqtSignal()
    setting_changed = pyqtSignal(str, object)
    panel_reset_requested = pyqtSignal()
    
    def __init__(self, db_manager):
        super().__init__()
        self.db = db_manager
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("<h2>OPTIONS</h2>"))
        
        appearance_group = QGroupBox("Appearance")
        appearance_layout = QFormLayout(appearance_group)
        self.theme_selector = QComboBox()
        self.theme_selector.addItems([
            "Dark (Default)", "Light", "Cyber", "Matrix", 
            "Sunrise", "Sunset", "Jungle", "Ocean", "Galaxy", "Candy"
        ])
        self.theme_selector.currentTextChanged.connect(lambda val: self.setting_changed.emit("theme", val))
        
        self.reset_panels_button = QPushButton("Reset Panel Sizing")
        self.reset_panels_button.clicked.connect(self.panel_reset_requested)
        
        self.animations_toggle = QCheckBox("Enable Animations (Not Implemented)")
        self.animations_toggle.stateChanged.connect(lambda state: self.setting_changed.emit("animations", bool(state)))
        
        appearance_layout.addRow("Theme:", self.theme_selector)
        appearance_layout.addRow(self.reset_panels_button)
        appearance_layout.addRow(self.animations_toggle)
        layout.addWidget(appearance_group)
        
        build_group = QGroupBox("Build Process")
        build_layout = QFormLayout(build_group)
        self.obfuscation_selector = QComboBox(); self.obfuscation_selector.addItems(["None", "Light", "Heavy"])
        self.obfuscation_selector.currentTextChanged.connect(lambda val: self.setting_changed.emit("obfuscation", val))
        self.compression_selector = QComboBox(); self.compression_selector.addItems(["None", "Normal (UPX)"])
        self.compression_selector.currentTextChanged.connect(lambda val: self.setting_changed.emit("compression", val))
        self.build_priority_combo = QComboBox()
        self.build_priority_combo.addItems(["Normal", "Low", "High"])
        self.build_priority_combo.currentTextChanged.connect(lambda val: self.setting_changed.emit("build_priority", val))
        
        # FIX: Removed "(Recommended)" from the text
        self.simple_logs_toggle = QCheckBox("Use Simple Build Logs")
        self.simple_logs_toggle.stateChanged.connect(lambda state: self.setting_changed.emit("simple_logs", bool(state)))

        build_layout.addRow("Obfuscation Level:", self.obfuscation_selector)
        build_layout.addRow("Compression:", self.compression_selector)
        build_layout.addRow("Process Priority:", self.build_priority_combo)
        build_layout.addRow(self.simple_logs_toggle)
        layout.addWidget(build_group)
        
        layout.addStretch()
        
        caution_group = QGroupBox("Caution")
        caution_layout = QVBoxLayout(caution_group)
        self.sanitize_button = QPushButton("Sanitize All Data")
        self.sanitize_button.setObjectName("SanitizeButton")
        self.sanitize_button.clicked.connect(self.confirm_sanitize)
        caution_layout.addWidget(self.sanitize_button)
        layout.addWidget(caution_group)
        
        self.sign_out_button = QPushButton("Sign Out")
        self.sign_out_button.clicked.connect(self.sign_out_requested)
        layout.addWidget(self.sign_out_button)
        
        self.load_settings()
        
    def load_settings(self):
        self.theme_selector.setCurrentText(self.db.load_setting("theme", "Dark (Default)"))
        self.animations_toggle.setChecked(self.db.load_setting("animations", True))
        self.obfuscation_selector.setCurrentText(self.db.load_setting("obfuscation", "None"))
        self.compression_selector.setCurrentText(self.db.load_setting("compression", "None"))
        self.build_priority_combo.setCurrentText(self.db.load_setting("build_priority", "Normal"))
        self.simple_logs_toggle.setChecked(self.db.load_setting("simple_logs", True))
        
    def handle_padding_status_change(self, is_padding_enabled):
        self.compression_selector.setEnabled(not is_padding_enabled)
        if is_padding_enabled:
            self.compression_selector.setCurrentText("None")

    def confirm_sanitize(self):
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("CONFIRM SANITIZE")
        msg_box.setText("<b><font color='red'>WARNING: THIS IS IRREVERSIBLE.</font></b>")
        msg_box.setInformativeText(
            "This will perform two actions:\n\n"
            "1. Send a <b>self-destruct command</b> to all currently online sessions.\n"
            "2. Permanently <b>delete all session history</b> and harvested data from the C2 database.\n\n"
            "Are you absolutely sure you want to proceed?"
        )
        msg_box.setIcon(QMessageBox.Icon.Warning)
        msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg_box.setDefaultButton(QMessageBox.StandardButton.No)
        if msg_box.exec() == QMessageBox.StandardButton.Yes:
            self.sanitize_requested.emit()

    # --- NEW: Method to disable controls during build ---
    def set_build_controls_enabled(self, enabled):
        """Enables or disables all controls related to the build process."""
        self.obfuscation_selector.setEnabled(enabled)
        self.compression_selector.setEnabled(enabled)
        self.build_priority_combo.setEnabled(enabled)
        self.simple_logs_toggle.setEnabled(enabled)