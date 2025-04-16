import requests
import json
import os
import base64
import time
from datetime import datetime, timedelta

class TokenManager:
    def __init__(self, config_path="config/auth.json"):
        self.config_path = config_path
        self.token_cache = None
        self.expiry_time = None
    
    def _load_config(self):
        try:
            with open(self.config_path) as f:
                return json.load(f)
        except Exception as e:
            raise Exception(f"Failed to load config: {e}")
    
    def _token_valid(self):
        return (self.token_cache is not None and 
                self.expiry_time is not None and 
                datetime.now() < self.expiry_time)
    
    def get_token(self, force_refresh=False):
        if not force_refresh and self._token_valid():
            return self.token_cache
        
        creds = self._load_config()
        
        # Add basic auth fallback
        auth_headers = {}
        if "client_id" in creds and "client_secret" in creds:
            auth_string = f"{creds['client_id']}:{creds['client_secret']}"
            encoded = base64.b64encode(auth_string.encode()).decode()
            auth_headers["Authorization"] = f"Basic {encoded}"
        
        # Support multiple auth methods
        auth_data = {
            "system_user": creds["system_user"],
            "static_key": creds["static_key"]
        }
        
        # Add optional parameters if they exist
        if "scope" in creds:
            auth_data["scope"] = creds["scope"]
        
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                response = requests.post(
                    creds["auth_url"],
                    json=auth_data,
                    headers=auth_headers,
                    timeout=10
                )
                response.raise_for_status()
                
                token_data = response.json()
                self.token_cache = token_data["access_token"]
                
                # Calculate expiry with 10% safety margin
                expires_in = token_data.get("expires_in", 3600)
                self.expiry_time = datetime.now() + timedelta(seconds=int(expires_in * 0.9))
                
                return self.token_cache
            
            except requests.RequestException as e:
                retry_count += 1
                if retry_count >= max_retries:
                    raise Exception(f"Failed to get auth token after {max_retries} attempts: {e}")
                time.sleep(2 ** retry_count)  # Exponential backoff

def get_auth_token(config_path="config/auth.json"):
    token_manager = TokenManager(config_path)
    return token_manager.get_token()