# canary_payload.py
import requests
import os
import traceback

# --- UPDATE THIS LINE ---
RELAY_URL = "https://tether-c2-communication-line-by-ebowluh.onrender.com"

LOG_FILE = "canary_log.txt"

def run_test():
    try:
        if os.path.exists(LOG_FILE): os.remove(LOG_FILE)
        
        # Test against the live Render server
        with open(LOG_FILE, "a") as f:
            f.write(f"--- TESTING LIVE RENDER URL: {RELAY_URL} ---\n")
        response = requests.get(f"{RELAY_URL}/ping", timeout=40, verify=False)
        
        if response.status_code == 200 and response.text == "pong":
            with open(LOG_FILE, "a") as f:
                f.write("SUCCESS! Live Render server is reachable.\n")
        else:
            with open(LOG_FILE, "a") as f:
                f.write(f"FAILURE! Unexpected response from Render server.\n")
                f.write(f"Status: {response.status_code}, Text: {response.text}\n")

    except Exception:
        with open(LOG_FILE, "a") as f:
            f.write("CRITICAL FAILURE!\n")
            f.write("The payload could not complete the network request.\n")
            f.write("THE ERROR IS:\n\n")
            f.write(traceback.format_exc())

if __name__ == "__main__":
    run_test()