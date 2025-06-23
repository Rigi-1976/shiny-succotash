import requests
import base64
import socket
import time
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

# --- Configuration ---
# Add the subscription links from the original GitHub script here
# You can add more than one
UPSTREAM_SUBSCRIPTION_URLS = [
    "https://raw.githubusercontent.com/soroushmirzaei/telegram-configs-collector/main/networks/tcp,
    # You can add other subscription links here if you want
]

# The file where the filtered subscription will be saved
OUTPUT_FILE = "filtered_sub.txt"

# Maximum latency in milliseconds. Servers slower than this will be removed.
LATENCY_THRESHOLD_MS = 3800

# Number of concurrent workers to test servers
MAX_WORKERS = 50

# --- End of Configuration ---

def get_configs_from_subscription(url):
    """Fetches and decodes configs from a subscription URL."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        decoded_content = base64.b64decode(response.content).decode('utf-8')
        return decoded_content.splitlines()
    except Exception as e:
        print(f"Error fetching subscription {url}: {e}")
        return []

def test_tcp_latency(ip, port, timeout=2):
    """Tests TCP connection latency to an IP and port."""
    start_time = time.time()
    try:
        with socket.create_connection((ip, port), timeout=timeout):
            end_time = time.time()
            return int((end_time - start_time) * 1000)  # Return latency in ms
    except (socket.timeout, ConnectionRefusedError, OSError):
        return None

def extract_server_info(config_link):
    """Extracts server address and port from a vmess link."""
    try:
        if config_link.startswith("vmess://"):
            decoded_json_str = base64.b64decode(config_link[8:]).decode('utf-8')
            config_json = json.loads(decoded_json_str)
            return config_json.get('add'), int(config_json.get('port', 0))
    except Exception:
        return None, None
    return None, None


def main():
    """Main function to run the filtering process."""
    print("Fetching all configs...")
    all_configs = []
    for url in UPSTREAM_SUBSCRIPTION_URLS:
        all_configs.extend(get_configs_from_subscription(url))
    
    unique_configs = list(set(all_configs))
    print(f"Found {len(unique_configs)} unique server configs.")

    good_configs = []
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_config = {}
        for config in unique_configs:
            address, port = extract_server_info(config)
            if address and port:
                future = executor.submit(test_tcp_latency, address, port)
                future_to_config[future] = config

        for i, future in enumerate(as_completed(future_to_config)):
            config = future_to_config[future]
            try:
                latency = future.result()
                if latency is not None and latency < LATENCY_THRESHOLD_MS:
                    print(f"  [GOOD] {config[:30]}... | Latency: {latency}ms")
                    good_configs.append(config)
                else:
                    # Optional: uncomment to see rejected servers
                    # print(f"  [BAD] {config[:30]}... | Latency: {latency or 'Timeout'}")
                    pass
            except Exception as e:
                # print(f"Error testing config {config[:30]}...: {e}")
                pass
            
            # Print progress
            print(f"Progress: {i+1}/{len(unique_configs)} tested. Found {len(good_configs)} good servers.", end='\r')

    print(f"\nFinished testing. Found {len(good_configs)} servers that meet the criteria.")

    if not good_configs:
        print("No good servers found. Exiting.")
        return

    # Create the final subscription file
    final_subscription_content = "\n".join(good_configs)
    encoded_subscription = base64.b64encode(final_subscription_content.encode('utf-8')).decode('utf-8')

    with open(OUTPUT_FILE, 'w') as f:
        f.write(encoded_subscription)

print(f"Successfully created filtered subscription file at '{OUTPUT_FILE}'")

if name == "main":
    main()
