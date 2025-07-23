# database.py
import sqlite3, json, bcrypt

class DatabaseManager:
    def __init__(self, db_file="tether_unified.db"):
        self.conn = sqlite3.connect(db_file, check_same_thread=False)
        self.conn.execute("CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password_hash TEXT NOT NULL)")
        self.conn.execute("CREATE TABLE IF NOT EXISTS sessions (session_id TEXT, c2_user TEXT, metadata TEXT, PRIMARY KEY (session_id, c2_user))")
        self.conn.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)")
        self.save_setting("last_user", "")

    def create_user(self, username, password):
        if not username or not password: return False
        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
        try: self.conn.execute("INSERT INTO users VALUES (?, ?)", (username, hashed.decode())); self.conn.commit(); return True
        except sqlite3.IntegrityError: return False
        
    def check_user(self, username, password):
        cursor = self.conn.execute("SELECT password_hash FROM users WHERE username = ?", (username,)); result = cursor.fetchone()
        if result and bcrypt.checkpw(password.encode(), result[0].encode()):
            self.save_setting("remembered_user", username); return True
        return False

    def save_setting(self, key, value):
        self.conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, json.dumps(value)))
        self.conn.commit()

    def load_setting(self, key, default=None):
        cursor = self.conn.execute("SELECT value FROM settings WHERE key = ?", (key,))
        result = cursor.fetchone()
        return json.loads(result[0]) if result else default

    def save_all_sessions_for_user(self, c2_user, sessions_dict):
        cursor = self.conn.cursor()
        cursor.execute("BEGIN TRANSACTION")
        try:
            # Clear old sessions for this user to avoid stale entries
            cursor.execute("DELETE FROM sessions WHERE c2_user = ?", (c2_user,))
            for session_id, data in sessions_dict.items():
                metadata_to_save = data.get('metadata', {})
                cursor.execute("INSERT OR REPLACE INTO sessions (c2_user, session_id, metadata) VALUES (?, ?, ?)", (c2_user, session_id, json.dumps(metadata_to_save)))
            cursor.execute("COMMIT")
        except Exception:
            cursor.execute("ROLLBACK")
            raise

    def load_all_sessions_for_user(self, c2_user):
        sessions = {}
        cursor = self.conn.execute("SELECT session_id, metadata FROM sessions WHERE c2_user = ?", (c2_user,))
        for session_id, metadata_json in cursor.fetchall():
            if metadata_json: sessions[session_id] = {"metadata": json.loads(metadata_json)}
        return sessions
    
    def sanitize_all_data(self, c2_user):
        self.conn.execute("DELETE FROM sessions WHERE c2_user = ?", (c2_user,))
        self.conn.commit()