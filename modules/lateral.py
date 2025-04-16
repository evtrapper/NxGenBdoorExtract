import socket
import ipaddress
import threading
import queue
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

def scan_port(ip, port, timeout=0.5):
    """Scan a single port on an IP address"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((ip, port))
        sock.close()
        return result == 0
    except:
        return False

def scan_host(ip, ports=None):
    """Scan common ports on a host"""
    if ports is None:
        ports = [80, 443, 8080, 8443]  # Common web ports
    
    open_ports = []
    for port in ports:
        if scan_port(ip, port):
            open_ports.append(port)
    
    return (ip, open_ports)

def discover_network():
    """Discover the local network range"""
    try:
        # Get hostname
        hostname = socket.gethostname()
        # Get local IP
        local_ip = socket.gethostbyname(hostname)
        # Convert to network range
        ip_parts = local_ip.split('.')
        network_range = f"{ip_parts[0]}.{ip_parts[1]}.{ip_parts[2]}.0/24"
        
        return network_range
    except:
        # Default to common private network
        return "192.168.1.0/24"

def scan_network(network_range=None, ports=None, max_threads=10):
    """Scan a network range for open ports"""
    if network_range is None:
        network_range = discover_network()
    
    if ports is None:
        ports = [80, 443, 8080, 8443]
    
    hosts = []
    try:
        network = ipaddress.ip_network(network_range)
        hosts = [str(ip) for ip in network.hosts()]
    except:
        print(f"[!] Invalid network range: {network_range}")
        return []
    
    results = []
    with ThreadPoolExecutor(max_workers=max_threads) as executor:
        future_to_ip = {executor.submit(scan_host, ip, ports): ip for ip in hosts}
        for future in as_completed(future_to_ip):
            ip = future_to_ip[future]
            try:
                ip, open_ports = future.result()
                if open_ports:
                    results.append((ip, open_ports))
            except Exception as e:
                print(f"[!] Error scanning {ip}: {e}")
    
    return results

def probe_endpoint(url, timeout=2):
    """Check if an endpoint exists"""
    try:
        response = requests.head(url, timeout=timeout)
        return response.status_code < 400  # Consider any non-error code as existing
    except:
        return False

def scan_for_internal_endpoints(base_endpoints=None, common_paths=None):
    """Scan for available internal endpoints"""
    if base_endpoints is None:
        # Default endpoints to check
        base_endpoints = [
            "https://nxgen.internal",
            "http://nxgen.internal",
            "https://api.internal",
            "http://api.internal"
        ]
    
    if common_paths is None:
        # Common API paths to check
        common_paths = [
            "/api",
            "/api/v1",
            "/api/v2",
            "/api/cases",
            "/api/user_profiles",
            "/v1/cases",
            "/v2/cases",
            "/data/cases"
        ]
    
    discovered_endpoints = []
    
    # Check all combinations
    for base in base_endpoints:
        for path in common_paths:
            endpoint = f"{base}{path}"
            if probe_endpoint(endpoint):
                discovered_endpoints.append(endpoint)
    
    # If no endpoints found, return defaults
    if not discovered_endpoints:
        return [
            "https://nxgen.internal/api/cases",
            "https://nxgen.internal/api/user_profiles"
        ]
    
    return discovered_endpoints