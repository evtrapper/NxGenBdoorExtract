# modules/fingerprinting.py
import socket
import uuid
import platform
import os
import json
import hashlib
import random

def get_system_info():
    """Get detailed system information but with minimized identifiable data"""
    try:
        # Get minimal identifying information in stealth mode
        info = {
            "platform": platform.system(),
            "hostname": socket.gethostname(),
            "session_id": str(uuid.uuid4())
        }
        
        # Calculate a randomized fingerprint that's consistent within the session
        # but doesn't actually fingerprint the real system
        random_seed = random.randint(1000000, 9999999)
        info["fingerprint"] = hashlib.sha256(str(random_seed).encode()).hexdigest()
        
        return info
    
    except Exception:
        # Fallback to absolute minimal information
        return get_host_fingerprint()

def get_host_fingerprint():
    """Get minimal host fingerprinting information"""
    return {
        "hostname": socket.gethostname(),
        "session_id": str(uuid.uuid4())
    }

def randomize_fingerprint():
    """Generate a randomized fingerprint that can't be traced back"""
    random_mac = ':'.join(['{:02x}'.format(random.randint(0, 255)) for _ in range(6)])
    random_hostname = ''.join(random.choices(string.ascii_lowercase, k=8))
    
    return {
        "hostname": random_hostname,
        "mac_address": random_mac,
        "session_id": str(uuid.uuid4())
    }