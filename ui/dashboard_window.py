# ui/dashboard_window.py (Definitive, as a QWidget)
from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QSplitter, QTableWidget, QVBoxLayout, QLabel, QHeaderView, QTableWidgetItem)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor
from .builder_pane import BuilderPane
from .options_pane import OptionsPane

class DashboardWindow(QWidget): # MODIFIED: Inherits from QWidget
    build_requested = pyqtSignal(dict); sign_out_requested = pyqtSignal(); sanitize_requested = pyqtSignal(); setting_changed = pyqtSignal(str, object)
    def __init__(self, db_manager):
        super().__init__()
        main_layout = QHBoxLayout(self) # MODIFIED: Layout is applied directly
        splitter = QSplitter(Qt.Orientation.Horizontal); main_layout.addWidget(splitter)
        self.builder_pane = BuilderPane(); self.builder_pane.build_requested.connect(self.build_requested)
        self.sessions_pane = QWidget(); sessions_layout = QVBoxLayout(self.sessions_pane); sessions_layout.setContentsMargins(10,10,10,10); sessions_layout.addWidget(QLabel("<h2>SESSIONS</h2>"))
        self.session_table = QTableWidget(); self.session_table.setColumnCount(5); self.session_table.setHorizontalHeaderLabels(["Status", "User", "Public IP", "Session ID", "Host Name"])
        self.session_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch); self.session_table.verticalHeader().setVisible(False); self.session_table.setSortingEnabled(True)
        sessions_layout.addWidget(self.session_table)
        self.options_pane = OptionsPane(db_manager)
        self.options_pane.sign_out_requested.connect(self.sign_out_requested); self.options_pane.sanitize_requested.connect(self.sanitize_requested); self.options_pane.setting_changed.connect(self.setting_changed)
        splitter.addWidget(self.builder_pane); splitter.addWidget(self.sessions_pane); splitter.addWidget(self.options_pane)
        splitter.setSizes([350, 700, 350])
    def update_session_table(self, sessions_data):
        self.session_table.setSortingEnabled(False); self.session_table.setRowCount(len(sessions_data))
        for row, (session_id, data) in enumerate(sessions_data.items()):
            status = data.get('status', 'Offline'); status_item = QTableWidgetItem(status)
            if status == 'Online': status_item.setForeground(QColor('lightgreen'))
            else: status_item.setForeground(QColor('red'))
            self.session_table.setItem(row, 0, status_item); self.session_table.setItem(row, 1, QTableWidgetItem(data.get('user', 'N/A'))); self.session_table.setItem(row, 2, QTableWidgetItem(data.get('ip', 'N/A'))); self.session_table.setItem(row, 3, QTableWidgetItem(session_id)); self.session_table.setItem(row, 4, QTableWidgetItem(data.get('hostname', 'N/A')))
        self.session_table.setSortingEnabled(True)