import os
import subprocess
import json
import logging
from hashlib import sha256
import urllib.request

# Set up logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Function to fetch and process the blocklist from a URL
def fetch_and_process_blocklist(url):
    try:
        # Tạo Request object với User-Agent tùy chỉnh
        request = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0"}
        )
        
        # Fetch the content from the URL
        with urllib.request.urlopen(request) as response:
            content = response.read().decode('utf-8')
        
        # Filter the lines starting with '||' and ending with '^' for domains
        url_filters = [
            line.strip()[2:-1]  # Remove the '||' prefix and the '^' suffix
            for line in content.split("\n")
            if line.startswith("||") and line.endswith("^")
        ]
        
        return url_filters
    except Exception as e:
        logger.error(f"Error fetching blocklist from {url}: {e}")
        return []

# Function to read URLs from list.txt
def read_urls_from_file(file_path):
    urls = []
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            urls = [line.strip() for line in file.readlines() if line.strip()]
    else:
        logger.error(f"{file_path} not found!")
    return urls

# Function to remove subdomains if a higher domain exists
def remove_subdomains_if_higher(domains: set[str]) -> set[str]:
    top_level_domains = set()
    
    for domain in domains:
        parts = domain.split(".")
            
        is_lower_subdomain = False            
        for i in range(1, len(parts)):
            higher_domain = ".".join(parts[i:])
            if higher_domain in domains:
                is_lower_subdomain = True
                break
                    
        if not is_lower_subdomain:
            top_level_domains.add(domain)
                
    return top_level_domains

# Function to generate Chrome extension rules
def generate_chrome_rules(filters):
    rules = []
    unique_domains = sorted(remove_subdomains_if_higher(set(filters)))  # Remove subdomains and sort
    
    # Ensure IDs start from 1
    for idx, filter in enumerate(unique_domains, 1):  # Start from 1
        rule = {
            "id": idx,
            "priority": 1,
            "action": {
                "type": "block"
            },
            "condition": {
                "urlFilter": f"||{filter}"  # Re-add '||' before domain
            }
        }
        rules.append(rule)
    
    return rules

def get_file_hash(file_path):
    sha256_hash = sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        return None

# Function to compress JSON by removing spaces and newlines
def compress_json(file_path):
    """
    Compress a JSON file by removing spaces and newlines.
    """
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)  # Đọc JSON
        
        # Ghi lại JSON với cấu trúc nén
        with open(file_path, 'w') as file:
            json.dump(data, file, separators=(',', ':'))  # Nén bằng cách loại bỏ khoảng trắng
        
        logger.info(f"Đã nén file {file_path}.")
    except Exception as e:
        logger.error(f"Lỗi khi nén file JSON {file_path}: {e}")

# Main function to create rules.json
def create_rules_json():
    url_file_path = "list.txt"  # Path to the external list.txt file containing URLs
    urls = read_urls_from_file(url_file_path)
    
    if not urls:
        logger.error("No URLs found in the list.txt file. Exiting.")
        return
    
    # Fetch and process blocklist for each URL in the list
    all_domains = []
    for url in urls:
        domains = fetch_and_process_blocklist(url)
        all_domains.extend(domains)
    
    # Remove duplicates and process the domains
    all_domains = sorted(set(all_domains))  # Remove duplicates and sort
    
    dynamic_rules = generate_chrome_rules(all_domains)
    
    rules_file = "rules.json"
    
    # Save the generated rules into rules.json
    with open(rules_file, "w") as file:
        json.dump(dynamic_rules, file, indent=4)
    
    logger.info(f"Đã tạo file {rules_file} với {len(all_domains)} tên miền.")
    
    # Merge with custom rules and create a final rules.json
    merge_custom_rules(rules_file)
    
    # Nén file rules.json
    compress_json(rules_file)
    
    # Commit và đẩy lên git
    commit_and_push(rules_file)

def merge_custom_rules(rules_file):
    custom_rules_file = "custom_rules.json"
    
    # Load existing rules from rules.json
    existing_rules = load_json(rules_file)
    custom_rules = load_json(custom_rules_file)

    # Find the last ID in existing rules (rules.json)
    max_existing_id = max((rule['id'] for rule in existing_rules), default=0)
    
    # Update custom rule IDs to continue from the highest existing ID
    for rule in custom_rules:
        rule['id'] += max_existing_id  # Adjust ID to avoid duplication

    # Append custom rules to existing rules
    existing_rules.extend(custom_rules)
    
    # Save the final combined rules to rules.json
    save_json(rules_file, existing_rules)

    logger.info(f"Đã kết hợp {len(custom_rules)} custom rules vào {rules_file}.")

def load_json(file_path):
    """Load JSON data from a file."""
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            return json.load(file)
    return []

def save_json(file_path, data):
    """Save data to a JSON file."""
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4)

def commit_and_push(file_path):
    try:
        subprocess.run(["git", "config", "--global", "user.name", "github-actions"], check=True)
        subprocess.run(["git", "config", "--global", "user.email", "actions@github.com"], check=True)

        status_result = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
        status_output = status_result.stdout.strip()
        
        if status_output:
            logger.info(f"Đã thay đổi file {file_path}. Tiến hành commit và push.")
            
            # Add only the rules.json file to git
            subprocess.run(["git", "add", file_path], check=True)  # Add rules.json
            
            subprocess.run(["git", "commit", "-m", f"Update {file_path}"], check=True)
            subprocess.run(["git", "push"], check=True)
        else:
            logger.warning(f"Không có thay đổi trong {file_path}. Không cần commit.")
    
    except subprocess.CalledProcessError as e:
        logger.error(f"Lỗi khi thực hiện lệnh git: {e}")


if __name__ == "__main__":
    create_rules_json()
