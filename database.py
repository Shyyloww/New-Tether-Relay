# database.py (Unified, Multi-User)
import sqlite3
import json

class DatabaseManager:
    def __init__(self, db_file="tether_global.db"):
        self.conn = sqlite3.connect(db_file, check_same_thread=False)
        self.conn.execute("CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password_hash TEXT NOT NULL)")
        self.conn.execute("CREATE TABLE IF NOT EXISTS sessions (session_id TEXT PRIMARY KEY, owner_username TEXT NOT NULL, metadata TEXT, FOREIGN KEY (owner_username) REFERENCES users(username))")
        self.conn.execute("CREATE TABLE IF NOT EXISTS vault (session_id TEXT, module_name TEXT, data TEXT, PRIMARY KEY (session_id, module_name))")

    def create_user(self, username, password_hash):
        try:
            self.conn.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, password_hash))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
            
    def get_user(self, username):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        return cursor.fetchone()

    def create_or_update_session(self, session_id, owner_username, metadata):
        self.conn.execute("INSERT OR REPLACE INTO sessions (session_id, owner_username, metadata) VALUES (?, ?, ?)", (session_id, owner_username, json.dumps(metadata)))
        self.conn.commit()
        
    def get_sessions_for_user(self, username):
        cursor = self.conn.cursor()
        cursor.execute("SELECT session_id, metadata FROM sessions WHERE owner_username = ?", (username,))
        return {row[0]: json.loads(row[1]) for row in cursor.fetchall()}

    def save_vault_data(self, session_id, module_name, data):
        self.conn.execute("INSERT OR REPLACE INTO vault (session_id, module_name, data) VALUES (?, ?, ?)", (session_id, module_name, json.dumps(data)))
        self.conn.commit()

    def load_vault_data_for_user(self, username):
        user_sessions = self.get_sessions_for_user(username)
        vault_data = {}
        for session_id, metadata in user_sessions.items():
            vault_data[session_id] = {"metadata": metadata}

        if not user_sessions:
            return {}
            
        session_ids_placeholder = ','.join('?' for _ in user_sessions)
        query = f"SELECT session_id, module_name, data FROM vault WHERE session_id IN ({session_ids_placeholder})"
        
        for session_id, module_name, data_json in self.conn.execute(query, tuple(user_sessions.keys())):
            if session_id in vault_data:
                vault_data[session_id][module_name] = json.loads(data_json)
        return vault_data