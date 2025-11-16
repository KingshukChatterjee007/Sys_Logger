import psutil
import logging
import os
import time
import atexit
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.auth.transport.requests import Request
import socket
import threading
try:
    import GPUtil
    NVIDIA_AVAILABLE = True
except ImportError:
    NVIDIA_AVAILABLE = False
AMD_AVAILABLE = False  # AMD GPU monitoring not available - library not found

def get_gpu_usage():
    """Get GPU usage for NVIDIA GPUs with process-level monitoring"""
    gpu_info = {}

    if NVIDIA_AVAILABLE:
        try:
            gpus = GPUtil.getGPUs()
            for i, gpu in enumerate(gpus):
                gpu_info[f'nvidia_gpu_{i}_load'] = gpu.load * 100
                gpu_info[f'nvidia_gpu_{i}_memory_used'] = gpu.memoryUsed
                gpu_info[f'nvidia_gpu_{i}_memory_total'] = gpu.memoryTotal
                gpu_info[f'nvidia_gpu_{i}_memory_percent'] = gpu.memoryUtil * 100
                gpu_info[f'nvidia_gpu_{i}_temperature'] = gpu.temperature
        except Exception as e:
            gpu_info['nvidia_error'] = str(e)

    # AMD GPU monitoring - try to get basic usage via Windows Performance Counters
    try:
        import subprocess
        # Check for AMD GPU presence
        result = subprocess.run(['wmic', 'path', 'win32_videocontroller', 'get', 'name'],
                               capture_output=True, text=True, timeout=5)
        if 'AMD' in result.stdout.upper() or 'RADEON' in result.stdout.upper():
            gpu_info['amd_available'] = True
            # Try to get GPU usage via typeperf (Windows Performance Monitor)
            try:
                usage_result = subprocess.run(['typeperf', '\\GPU Engine(*)\\Utilization Percentage', '-sc', '1'],
                                            capture_output=True, text=True, timeout=10)
                if usage_result.returncode == 0 and usage_result.stdout:
                    # Parse the output to extract GPU usage
                    lines = usage_result.stdout.strip().split('\n')
                    if len(lines) > 2:
                        # Last line typically contains the value
                        last_line = lines[-1].strip()
                        if ',' in last_line:
                            parts = last_line.split(',')
                            if len(parts) > 1:
                                try:
                                    usage_value = float(parts[-1].strip('"\r\n'))
                                    gpu_info['amd_gpu_usage'] = usage_value
                                except ValueError:
                                    pass
            except subprocess.TimeoutExpired:
                gpu_info['amd_note'] = 'AMD GPU detected - usage monitoring timed out'
            except Exception:
                gpu_info['amd_note'] = 'AMD GPU detected - detailed monitoring limited'
        else:
            gpu_info['amd_available'] = False
    except Exception:
        gpu_info['amd_available'] = False

    return gpu_info

# Configuration
SCOPES = ['https://www.googleapis.com/auth/drive.file']
LOG_FOLDER = 'C://Usage_Logs'
CREDENTIALS_FILE = 'credentials.json'
TOKEN_FILE = 'token.json'
UPLOAD_FOLDER_ID = 'Usage Logs'  # Set this to your Google Drive folder ID

# Create session start timestamp
session_start = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
LOG_FILE = os.path.join(LOG_FOLDER, f'system_usage_{session_start}.log')

# Set up logging directory
if not os.path.exists(LOG_FOLDER):
    os.makedirs(LOG_FOLDER)

# Set up logging
logging.basicConfig(filename=LOG_FILE, level=logging.INFO,
                    format='%(asctime)s - %(message)s')

def get_system_usage():
    cpu_usage = psutil.cpu_percent(interval=1)
    ram_usage = psutil.virtual_memory().percent
    gpu_usage = get_gpu_usage()
    return cpu_usage, ram_usage, gpu_usage

def log_usage():
    logging.info("Session started")
    while True:
        cpu, ram, gpu = get_system_usage()
        gpu_str = ", ".join([f"{key}: {value}" for key, value in gpu.items()])
        logging.info(f"CPU Usage: {cpu}%, RAM Usage: {ram}%, GPU Usage: {gpu_str}")

def is_connected():
    try:
        socket.create_connection(("www.google.com", 80))
        return True
    except OSError:
        pass
    return False

def cleanup_old_logs():
    """Delete log files older than 2 days"""
    if not os.path.exists(LOG_FOLDER):
        return

    cutoff_date = datetime.now() - timedelta(days=2)

    for filename in os.listdir(LOG_FOLDER):
        if filename.startswith('system_usage_') and filename.endswith('.log'):
            file_path = os.path.join(LOG_FOLDER, filename)
            try:
                file_mod_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                if file_mod_time < cutoff_date:
                    os.remove(file_path)
                    logging.info(f"Deleted old log file: {filename}")
            except Exception as e:
                logging.error(f"Failed to delete {filename}: {e}")

def on_exit():
    logging.info("Session ended")

def upload_to_drive():
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())

    service = build('drive', 'v3', credentials=creds)

    file_metadata = {
        'name': os.path.basename(LOG_FILE),
        'parents': [UPLOAD_FOLDER_ID] if UPLOAD_FOLDER_ID else []
    }
    media = MediaFileUpload(LOG_FILE, mimetype='text/plain')
    file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    print('File ID: %s' % file.get('id'))

    # Delete the log file locally after successful upload
    if os.path.exists(LOG_FILE):
        os.remove(LOG_FILE)

def main():
    atexit.register(on_exit)

    # Clean up old logs before starting
    cleanup_old_logs()

    # Start logging thread
    logging_thread = threading.Thread(target=log_usage)
    logging_thread.daemon = True
    logging_thread.start()

    # For service mode, run indefinitely without waiting for input
    if len(os.sys.argv) > 1 and os.sys.argv[1] == '--service':
        logging.info("Running in service mode")
        while True:
            time.sleep(3600)  # Upload every hour in service mode
            if os.path.exists(CREDENTIALS_FILE):
                if is_connected():
                    try:
                        upload_to_drive()
                        logging.info("Logs uploaded successfully in service mode.")
                    except Exception as e:
                        logging.error(f"Upload failed in service mode: {e}")
                else:
                    logging.info("Skipping upload: No internet connection in service mode.")
            else:
                logging.info("Skipping upload: credentials.json not found (logging works without upload).")
    else:
        input("Press Enter to exit and upload logs...\n")
        if os.path.exists(CREDENTIALS_FILE):
            if is_connected():
                try:
                    upload_to_drive()
                    print("Logs uploaded successfully.")
                except Exception as e:
                    logging.error(f"Upload failed: {e}")
                    print(f"Upload failed: {e}")
            else:
                print("Skipping upload: No internet connection.")
        else:
            print("Skipping upload: credentials.json not found (logging works without upload).")

if __name__ == "__main__":
    main()