# modules/ip_rotation.py
import random
import json
import requests
import time
import os

class ProxyManager:
    def __init__(self, config_path="config/auth.json"):
        self.config_path = config_path
        self.proxies = []
        self.current_proxy = None
        self.last_rotation = time.time()
        self.rotation_interval = random.uniform(300, 900)  # 5-15 minutes
        self.load_proxies()
    
    def load_proxies(self):
        """Load proxies from configuration file"""
        try:
            with open(self.config_path) as f:
                cfg = json.load(f)
            
            if "proxy_pool" in cfg and isinstance(cfg["proxy_pool"], list):
                self.proxies = cfg["proxy_pool"]
        except Exception:
            # Fallback to hardcoded proxies if config fails
            self.proxies = [
                "http://192.168.100.1:8080",
                "http://192.168.100.2:8080"
            ]
    
    def should_rotate(self):
        """Check if we should rotate to a new proxy"""
        current_time = time.time()
        time_since_rotation = current_time - self.last_rotation
        
        # Rotate if enough time has passed
        if time_since_rotation > self.rotation_interval:
            return True
        
        # Also rotate with a small random chance (1%)
        if random.random() < 0.01:
            return True
        
        return False
    
    def get_proxy(self, test=False):
        """Get a proxy with stealth rotation"""
        if not self.proxies:
            return None
        
        if self.current_proxy is None or self.should_rotate():
            # Generate a new rotation interval
            self.rotation_interval = random.uniform(300, 900)  # 5-15 minutes
            self.last_rotation = time.time()
            
            # Get a random proxy, preferably different from current
            available_proxies = [p for p in self.proxies if p != self.current_proxy]
            if not available_proxies:
                available_proxies = self.proxies
            
            self.current_proxy = random.choice(available_proxies)
        
        return self.current_proxy
    
    def apply_proxy_to_environment(self):
        """Apply the current proxy to environment variables"""
        if self.current_proxy:
            os.environ["HTTP_PROXY"] = self.current_proxy
            os.environ["HTTPS_PROXY"] = self.current_proxy
            return True
        return False

def get_proxy(test=False, config_path="config/auth.json"):
    """Get a proxy from the configuration"""
    proxy_manager = ProxyManager(config_path)
    return proxy_manager.get_proxy(test)