import requests
import base64
import socket
import time
import json
import random
from urllib.parse import urlparse # <-- NEW: To help parse VLESS links

# --- Configuration ---
# !!! IMPORTANT: Change this to your new VLESS link !!!
UPSTREAM_SUBSCRIPTION_URLS = [
    "https://raw.githubusercontent.com/soroushmirzaei/telegram-configs-collector/main/networks/tcp"
]
OUTPUT_FILE = "filtered_sub.txt"
LATENCY_THRESHOLD_MS = 800

# --- DIAGNOSTIC SETTINGS ---
MAX_WORKERS = 1
PROCESS_TIMEOUT_SECONDS = 25 * 60

# --- End of Configuration ---

def get_configs_from_subscription(url):
    """Fetches and decodes configs from a subscription URL."""
    try:
        print(f"Fetching subscription from: {url}")
        # For VLESS and other plain text lists, we don't need to base64 decode
        response = requests.get(url, timeout=20)
        response.raise_for_status()
        # The VLESS file is not Base64 encoded, it's just plain text
        return response.text.splitlines()
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
    """
    --- UPDATED FUNCTION ---
    Extracts server address and port from vmess or vless links.
    """
    try:
        if config_link.startswith("vmess://"):
            # Handle VMess
            padding_needed = len(config_link[8:]) % 4
            padded_b64 = config_link[8:] + "=" * padding_needed
            decoded_json_str = base64.b64decode(padded_b64).decode('utf-8')
            config_json = json.loads(decoded_json_str)
            return config_json.get('add'), int(config_json.get('port', 0))

        elif config_link.startswith("vless://"):
            # Handle VLESS
            # Use urlparse for robust parsing of vless links
            parsed_url = urlparse(config_link)
            address = parsed_url.hostname
            port = parsed_url.port
            if address and port:
                return address, int(port)

    except Exception as e:
        print(f"    [ERROR] Could not parse config link: {config_link[:40]}... | Error: {e}")
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
        with open(OUTPUT_FILE, 'w') as f:
            f.write("")
        return

    unique_configs = list(set(all_configs))
    random.shuffle(unique_configs)
    print(f"Found and shuffled {len(unique_configs)} unique server configs.")

    good_configs = []
    total_to_check = len(unique_configs)
    
    print("Starting server tests one-by-one...")
    for i, config in enumerate(unique_configs):
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
        else:
            print(f"    [SKIP] Could not extract server info from link.")

    print(f"\n--- FINISHED TESTING ---")
    print(f"Found {len(good_configs)} servers that meet the criteria.")
    
    final_subscription_content = "\n".join(good_configs)
    # The final subscription list should be base64 encoded for V2Ray apps
    encoded_subscription = base64.b64encode(final_subscription_content.encode('utf-8')).decode('utf-8')

    with open(OUTPUT_FILE, 'w') as f:
        f.write(encoded_subscription)

    print(f"Successfully created/updated subscription file at '{OUTPUT_FILE}'")
    print("--- DIAGNOSTIC RUN COMPLETE ---")

if __name__ == "__main__":
    main()
