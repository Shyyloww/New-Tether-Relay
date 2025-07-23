# ui/builder_pane.py (Definitive, Imports Fixed & Syntax Corrected)
import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, 
                             QTextEdit, QCheckBox, QComboBox, QSpinBox, QGroupBox,
                             QFileDialog, QLabel, QStackedWidget, QMessageBox)
from PyQt6.QtCore import pyqtSignal

class BuilderPane(QWidget):
    build_requested = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.stack = QStackedWidget()
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10,10,10,10); main_layout.setSpacing(10)
        main_layout.addWidget(self.stack)

        builder_widget = QWidget(); layout = QVBoxLayout(builder_widget)
        layout.addWidget(QLabel("<h2>BUILDER</h2>"))
        payload_name_layout = QHBoxLayout()
        self.payload_name = QLineEdit(); self.payload_name.setPlaceholderText("Payload File Name")
        self.payload_ext = QComboBox(); self.payload_ext.addItems([".exe", ".scr", ".com"])
        payload_name_layout.addWidget(self.payload_name, 3); payload_name_layout.addWidget(self.payload_ext, 1)
        layout.addLayout(payload_name_layout)

        persist_group = QGroupBox("Resilience"); persist_layout = QVBoxLayout(persist_group)
        self.startup_persist = QCheckBox("Startup Persistence"); persist_layout.addWidget(self.startup_persist)
        hydra_line_layout = QHBoxLayout()
        self.hydra_revival = QCheckBox("Hydra Revival (Watchdog)"); hydra_line_layout.addWidget(self.hydra_revival)
        self.hydra_amount = QSpinBox(); self.hydra_amount.setRange(2, 5); self.hydra_amount.valueChanged.connect(self.update_hydra_inputs)
        hydra_line_layout.addWidget(self.hydra_amount); hydra_line_layout.addStretch()
        persist_layout.addLayout(hydra_line_layout)
        self.hydra_guardian_group = QGroupBox("Guardian Configuration"); self.hydra_guardian_group.setVisible(False)
        self.hydra_guardian_layout = QVBoxLayout(self.hydra_guardian_group); self.hydra_inputs = []
        persist_layout.addWidget(self.hydra_guardian_group); self.hydra_revival.stateChanged.connect(self.hydra_guardian_group.setVisible)
        self.revive_message_checkbox = QCheckBox("Enable Custom Revive Message"); persist_layout.addWidget(self.revive_message_checkbox)
        self.revive_message_group = QGroupBox("Revive Message"); self.revive_message_group.setVisible(False)
        revive_layout = QVBoxLayout(self.revive_message_group)
        self.revive_title_input = QLineEdit(); self.revive_title_input.setPlaceholderText("Message Title (e.g., Graphics Driver Error)")
        self.revive_message_input = QTextEdit(); self.revive_message_input.setPlaceholderText("Message Body (e.g., A critical component has failed...)"); self.revive_message_input.setMaximumHeight(80)
        revive_layout.addWidget(self.revive_title_input); revive_layout.addWidget(self.revive_message_input)
        persist_layout.addWidget(self.revive_message_group); self.revive_message_checkbox.stateChanged.connect(self.revive_message_group.setVisible)
        layout.addWidget(persist_group)

        deception_group = QGroupBox("Deception & Lures"); deception_layout = QVBoxLayout(deception_group)
        self.custom_popup_checkbox = QCheckBox("Show Custom Popup on First Execution"); deception_layout.addWidget(self.custom_popup_checkbox)
        self.custom_popup_group = QGroupBox("Popup Message"); self.custom_popup_group.setVisible(False)
        popup_layout = QVBoxLayout(self.custom_popup_group)
        self.popup_title_input = QLineEdit(); self.popup_title_input.setPlaceholderText("Popup Title")
        self.popup_message_input = QTextEdit(); self.popup_message_input.setPlaceholderText("Popup Message"); self.popup_message_input.setMaximumHeight(80)
        popup_layout.addWidget(self.popup_title_input); popup_layout.addWidget(self.popup_message_input)
        deception_layout.addWidget(self.custom_popup_group); self.custom_popup_checkbox.stateChanged.connect(self.custom_popup_group.setVisible)
        clone_layout = QHBoxLayout(); self.clone_exe_button = QPushButton("Clone Executable (Icon/Metadata)"); self.clone_exe_button.clicked.connect(self.select_clone_file)
        self.clone_label = QLabel("None"); clone_layout.addWidget(self.clone_exe_button); clone_layout.addWidget(self.clone_label, 1); deception_layout.addLayout(clone_layout)
        bind_layout = QHBoxLayout(); self.bind_file_button = QPushButton("Bind Decoy File"); self.bind_file_button.clicked.connect(self.select_bind_file)
        self.bind_label = QLabel("None"); bind_layout.addWidget(self.bind_file_button); bind_layout.addWidget(self.bind_label, 1); deception_layout.addLayout(bind_layout); layout.addWidget(deception_group)

        layout.addStretch(); self.build_button = QPushButton("Build Payload"); self.build_button.clicked.connect(self.on_build); layout.addWidget(self.build_button)
        self.clone_exe_path = None; self.bind_file_path = None
        
        self.build_log_pane = QWidget()
        log_layout = QVBoxLayout(self.build_log_pane); self.build_log_output = QTextEdit(); self.build_log_output.setReadOnly(True)
        self.stop_build_button = QPushButton("Stop Build"); self.stop_build_button.setEnabled(False)
        self.back_to_builder_button = QPushButton("< Back to Builder"); self.back_to_builder_button.clicked.connect(self.show_builder_pane); self.back_to_builder_button.hide()
        log_layout.addWidget(QLabel("<h3>BUILDING PAYLOAD...</h3>")); log_layout.addWidget(self.build_log_output, 1);
        log_layout.addWidget(self.stop_build_button); log_layout.addWidget(self.back_to_builder_button)

        self.stack.addWidget(builder_widget); self.stack.addWidget(self.build_log_pane)
        self.update_hydra_inputs(self.hydra_amount.value())

    def update_hydra_inputs(self, amount):
        while self.hydra_guardian_layout.count():
            child = self.hydra_guardian_layout.takeAt(0)
            if child.widget(): child.widget().deleteLater()
        self.hydra_inputs.clear()
        for i in range(amount):
            row_widget = QWidget(); layout = QHBoxLayout(row_widget); layout.setContentsMargins(0,0,0,0)
            name_input = QLineEdit(); name_input.setPlaceholderText(f"Guardian #{i+1} Name")
            ext_input = QComboBox(); ext_input.addItems([".exe", ".dll", ".scr"])
            layout.addWidget(name_input); layout.addWidget(ext_input)
            self.hydra_guardian_layout.addWidget(row_widget)
            self.hydra_inputs.append((name_input, ext_input))

    def select_clone_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Executable to Clone", "", "Executables (*.exe)");
        if path: self.clone_exe_path = path; self.clone_label.setText(os.path.basename(path))

    def select_bind_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select File to Bind")
        if path: self.bind_file_path = path; self.bind_label.setText(os.path.basename(path))

    def on_build(self):
        if not self.payload_name.text():
            msg = QMessageBox(); msg.setIcon(QMessageBox.Icon.Warning); msg.setText("Payload name cannot be empty."); msg.exec(); return
        
        guardian_names = [name_input.text() + ext_input.currentText() for name_input, ext_input in self.hydra_inputs] if self.hydra_revival.isChecked() else []
        
        # --- THIS IS THE CORRECTED LINE ---
        settings = {
            "payload_name": self.payload_name.text() + self.payload_ext.currentText(),
            "persistence": self.startup_persist.isChecked(),
            "hydra": self.hydra_revival.isChecked(),
            "hydra_guardians": guardian_names,
            "revive_msg_enabled": self.revive_message_checkbox.isChecked(),
            "revive_title": self.revive_title_input.text(),
            "revive_message": self.revive_message_input.toPlainText(),
            "popup_enabled": self.custom_popup_checkbox.isChecked(),
            "popup_title": self.popup_title_input.text(),
            "popup_message": self.popup_message_input.toPlainText(),
            "clone_path": self.clone_exe_path,
            "bind_path": self.bind_file_path
        }
        self.build_requested.emit(settings)
        
    def show_build_log_pane(self):
        self.build_log_output.clear(); self.back_to_builder_button.hide(); self.stop_build_button.setEnabled(True); self.stack.setCurrentIndex(1)

    def show_builder_pane(self): 
        self.stack.setCurrentIndex(0)