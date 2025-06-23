import requests
import base64
import socket
import time
import json
import random  # <-- To shuffle the servers

# --- Configuration ---
UPSTREAM_SUBSCRIPTION_URLS = [
    "https://raw.githubusercontent.com/soroushmirzaei/telegram-configs-collector/main/subscribe/protocols/vless"
]
OUTPUT_FILE = "filtered_sub.txt"
LATENCY_THRESHOLD_MS = 800

# --- DIAGNOSTIC SETTINGS ---
# We will test one-by-one to be safe and avoid resource limits.
MAX_WORKERS = 1
# We will stop the test after 25 minutes to make sure the script always finishes.
PROCESS_TIMEOUT_SECONDS = 25 * 60

# --- End of Configuration ---

def get_configs_from_subscription(url):
    """Fetches and decodes configs from a subscription URL."""
    try:
        print(f"Fetching subscription from: {url}")
        response = requests.get(url, timeout=20)
        response.raise_for_status()
        decoded_content = base64.b64decode(response.content).decode('utf-8')
        return decoded_content.splitlines()
    except Exception as e:
        print(f"ERROR fetching subscription {url}: {e}")
        return []

def test_tcp_latency(ip, port, timeout=2):
    """Tests TCP connection latency to an IP and port."""
    start_time = time.time()
    try:
        with socket.create_connection((ip, port), timeout=timeout):
            end_time = time.time()
            return int((end_time - start_time) * 1000)
    except Exception:
        return None

def extract_server_info(config_link):
    """Extracts server address and port from a vmess link."""
    try:
        if config_link.startswith("vmess://"):
            padding_needed = len(config_link[8:]) % 4
            padded_b64 = config_link[8:] + "=" * padding_needed
            decoded_json_str = base64.b64decode(padded_b64).decode('utf-8')
            config_json = json.loads(decoded_json_str)
            return config_json.get('add'), int(config_json.get('port', 0))
    except Exception:
        return None, None
    return None, None

def main():
    """Main diagnostic function."""
    script_start_time = time.time()
    print("--- STARTING DIAGNOSTIC RUN ---")
    print(f"Timeout is set to {PROCESS_TIMEOUT_SECONDS / 60} minutes.")
    
    all_configs = []
    for url in UPSTREAM_SUBSCRIPTION_URLS:
        all_configs.extend(get_configs_from_subscription(url))
    
    if not all_configs:
        print("Could not fetch any configs. Exiting.")
        # Still write an empty file to complete the workflow
        with open(OUTPUT_FILE, 'w') as f:
            f.write("")
        return

    unique_configs = list(set(all_configs))
    
    # --- NEW: Shuffle the list to see if the crash is random or fixed ---
    random.shuffle(unique_configs)
    print(f"Found and shuffled {len(unique_configs)} unique server configs.")

    good_configs = []
    total_to_check = len(unique_configs)
    
    print("Starting server tests one-by-one...")
    for i, config in enumerate(unique_configs):
        # --- NEW: Check if we have run out of time ---
        elapsed_time = time.time() - script_start_time
        if elapsed_time > PROCESS_TIMEOUT_SECONDS:
            print(f"\n--- TIME LIMIT REACHED ({PROCESS_TIMEOUT_SECONDS / 60} minutes) ---")
            print("Stopping tests to save results.")
            break
            
        print(f"--> [{(i+1)}/{total_to_check}] Testing: {config[:40]}...")
        
        address, port = extract_server_info(config)
        if address and port:
            latency = test_tcp_latency(address, port)
            if latency is not None and latency < LATENCY_THRESHOLD_MS:
                print(f"    [GOOD] Latency: {latency}ms. Added to list.")
                good_configs.append(config)

    print(f"\n--- FINISHED TESTING ---")
    print(f"Found {len(good_configs)} servers that meet the criteria.")
    
    final_subscription_content = "\n".join(good_configs)
    encoded_subscription = base64.b64encode(final_subscription_content.encode('utf-8')).decode('utf-8')

    with open(OUTPUT_FILE, 'w') as f:
        f.write(encoded_subscription)

    print(f"Successfully created/updated subscription file at '{OUTPUT_FILE}'")
    print("--- DIAGNOSTIC RUN COMPLETE ---")

if __name__ == "__main__":
    main()
