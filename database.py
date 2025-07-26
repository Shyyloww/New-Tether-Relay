# database.py (Full Code)
import sqlite3
import json
import bcrypt
from datetime import datetime

class DatabaseManager:
    def __init__(self, db_file="tether_unified.db"):
        self.conn = sqlite3.connect(db_file, check_same_thread=False)
        self.conn.execute("PRAGMA journal_mode=WAL;")
        self.conn.execute("PRAGMA foreign_keys = ON;")
        self._create_tables()

    def _create_tables(self):
        """Creates all necessary tables if they don't exist."""
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY, 
                password_hash TEXT NOT NULL
            )
        """)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY, 
                value TEXT
            )
        """)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY, 
                c2_user TEXT NOT NULL, 
                metadata TEXT,
                FOREIGN KEY (c2_user) REFERENCES users(username) ON DELETE CASCADE
            )
        """)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS harvested_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                command_name TEXT NOT NULL,
                data TEXT,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
            )
        """)
        self.conn.commit()

    def create_user(self, username, password):
        if not username or not password: return False
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        try:
            self.conn.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, hashed.decode('utf-8')))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        
    def check_user(self, username, password):
        cursor = self.conn.execute("SELECT password_hash FROM users WHERE username = ?", (username,))
        result = cursor.fetchone()
        if result and bcrypt.checkpw(password.encode('utf-8'), result[0].encode('utf-8')):
            if self.load_setting("remember_me", True):
                 self.save_setting("remembered_user", username)
            return True
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
        try:
            cursor.execute("BEGIN TRANSACTION")
            for session_id, data in sessions_dict.items():
                metadata_to_save = data.get('metadata', {})
                cursor.execute("INSERT OR REPLACE INTO sessions (session_id, c2_user, metadata) VALUES (?, ?, ?)",
                               (session_id, c2_user, json.dumps(metadata_to_save)))
            cursor.execute("COMMIT")
        except Exception as e:
            cursor.execute("ROLLBACK")
            print(f"Error saving sessions: {e}")

    def load_all_sessions_for_user(self, c2_user):
        sessions = {}
        cursor = self.conn.execute("SELECT session_id, metadata FROM sessions WHERE c2_user = ?", (c2_user,))
        for session_id, metadata_json in cursor.fetchall():
            if metadata_json:
                sessions[session_id] = {"metadata": json.loads(metadata_json)}
        return sessions
    
    def save_result(self, session_id, command_name, data):
        """Saves a piece of harvested data to the database."""
        timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
        try:
            # First, ensure the session exists to satisfy the foreign key constraint
            self.conn.execute("INSERT OR IGNORE INTO sessions (session_id, c2_user) SELECT ?, c2_user FROM sessions LIMIT 1", (session_id,))

            self.conn.execute(
                "INSERT INTO harvested_data (session_id, command_name, data, timestamp) VALUES (?, ?, ?, ?)",
                (session_id, command_name, data, timestamp)
            )
            self.conn.commit()
        except Exception as e:
            print(f"Error saving result to database: {e}")

    def load_results_for_session(self, session_id):
        """Loads all historical data for a given session, ordered by time."""
        results = []
        cursor = self.conn.execute(
            "SELECT command_name, data, timestamp FROM harvested_data WHERE session_id = ? ORDER BY timestamp ASC",
            (session_id,)
        )
        for command_name, data, timestamp in cursor.fetchall():
            results.append({"command_name": command_name, "data": data, "timestamp": timestamp})
        return results

    def sanitize_all_data(self, c2_user):
        """Deletes all sessions and harvested data associated with a user."""
        try:
            self.conn.execute("DELETE FROM sessions WHERE c2_user = ?", (c2_user,))
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            print(f"Error during sanitization: {e}")