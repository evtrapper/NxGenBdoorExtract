import datetime
import time
import pytz  # Would need to be installed

def current_ts():
    """Get current timestamp in ISO format with UTC timezone"""
    return datetime.datetime.utcnow().isoformat() + "Z"

def current_unix_ts():
    """Get current timestamp in Unix format (seconds since epoch)"""
    return int(time.time())

def current_unix_ms():
    """Get current timestamp in Unix format with milliseconds"""
    return int(time.time() * 1000)

def format_timestamp(timestamp, format_str="%Y-%m-%d %H:%M:%S"):
    """Format a timestamp into a specific string format"""
    if isinstance(timestamp, (int, float)):
        # Convert Unix timestamp to datetime
        dt = datetime.datetime.fromtimestamp(timestamp)
    elif isinstance(timestamp, str):
        # Try to parse ISO format
        dt = datetime.datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    else:
        # Assume it's already a datetime
        dt = timestamp
    
    return dt.strftime(format_str)

def to_timezone(timestamp, timezone="UTC"):
    """Convert a timestamp to a specific timezone"""
    if isinstance(timestamp, (int, float)):
        # Convert Unix timestamp to datetime
        dt = datetime.datetime.fromtimestamp(timestamp, tz=pytz.UTC)
    elif isinstance(timestamp, str):
        # Try to parse ISO format
        dt = datetime.datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    else:
        # Assume it's already a datetime, ensure it has timezone
        dt = timestamp
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=pytz.UTC)
    
    # Convert to target timezone
    target_tz = pytz.timezone(timezone)
    return dt.astimezone(target_tz)

def get_timestamp_range(days=7, end_time=None):
    """Get a range of timestamps for the past N days"""
    if end_time is None:
        end_time = datetime.datetime.utcnow()
    
    start_time = end_time - datetime.timedelta(days=days)
    
    return {
        "start": start_time.isoformat() + "Z",
        "end": end_time.isoformat() + "Z",
        "start_unix": int(start_time.timestamp()),
        "end_unix": int(end_time.timestamp())
    }