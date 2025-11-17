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
from flask import Flask, jsonify
from flask_cors import CORS
from werkzeug.serving import make_server
try:
    import GPUtil
    NVIDIA_AVAILABLE = True
except ImportError:
    NVIDIA_AVAILABLE = False
AMD_AVAILABLE = False  # AMD GPU monitoring not available - library not found

app = Flask(__name__)
CORS(app)

def get_gpu_usage():
    """Get GPU usage for both NVIDIA and AMD GPUs using Windows Performance Counters"""
    gpu_info = {}

    # Get all GPU usage data from Windows Performance Monitor
    try:
        import subprocess

        # Try PowerShell method for better GPU detection
        try:
            ps_command = '''
            $counters = Get-Counter -ListSet "GPU Engine" -ErrorAction SilentlyContinue
            if ($counters) {
                $paths = $counters.Paths | Where-Object { $_ -like "*Utilization*" }
                if ($paths) {
                    $gpuCounters = Get-Counter -Counter $paths -SampleInterval 1 -MaxSamples 2 -ErrorAction SilentlyContinue
                    if ($gpuCounters) {
                        $maxValue = 0
                        $gpuCounters.CounterSamples | ForEach-Object {
                            $value = [math]::Round($_.CookedValue, 1)
                            if ($value -gt $maxValue) { $maxValue = $value }
                        }
                        if ($maxValue -gt 0) {
                            Write-Output "GPU:$maxValue"
                        }
                    }
                }
            }
            '''
            ps_result = subprocess.run([
                'powershell', '-ExecutionPolicy', 'Bypass', '-Command', ps_command
            ], capture_output=True, text=True, timeout=15)

            if ps_result.returncode == 0 and ps_result.stdout.strip():
                for line in ps_result.stdout.strip().split('\n'):
                    if line.startswith('GPU:'):
                        try:
                            _, value = line.split(':', 1)
                            usage_value = float(value.strip())
                            gpu_info['overall_gpu_usage'] = usage_value
                            gpu_info['detection_method'] = 'powershell'
                            print(f"PowerShell GPU Detection: {usage_value:.1f}%")
                            print(f"DEBUG - Returning gpu_info: {gpu_info}")
                            return gpu_info
                        except ValueError:
                            continue

        except Exception as e:
            print(f"PowerShell GPU detection failed: {e}")

        # Fallback to typeperf method
        result = subprocess.run([
            'typeperf',
            '\\GPU Engine(*)\\Utilization Percentage',
            '-sc', '2'
        ], capture_output=True, text=True, timeout=15)

        if result.returncode == 0 and result.stdout:
            lines = result.stdout.strip().split('\n')
            data_lines = [line for line in lines if line.strip() and not line.startswith('"') and not 'Exiting' in line and not 'completed' in line.lower()]

            if len(data_lines) >= 1:
                # Get the last data line
                last_data_line = data_lines[-1]
                values = last_data_line.split(',')

                # Find maximum GPU usage from all engines
                max_gpu_usage = 0
                engine_count = 0

                for value in values[1:]:  # Skip timestamp
                    try:
                        usage_value = float(value.strip('"\r\n'))
                        if usage_value > max_gpu_usage:
                            max_gpu_usage = usage_value
                        engine_count += 1
                    except (ValueError, IndexError):
                        continue

                if max_gpu_usage > 0:
                    gpu_info['overall_gpu_usage'] = max_gpu_usage
                    gpu_info['gpu_engine_count'] = engine_count
                    gpu_info['detection_method'] = 'typeperf'
                    print(f"TypePerf GPU Detection: {engine_count} engines, max usage: {max_gpu_usage:.1f}%")
                    print(f"DEBUG - Returning gpu_info: {gpu_info}")
                    return gpu_info

        print("No GPU usage detected")
        gpu_info['overall_gpu_usage'] = 0.0
        gpu_info['detection_method'] = 'none'

    except subprocess.TimeoutExpired:
        gpu_info['gpu_monitoring_timeout'] = 'GPU monitoring timed out'
        gpu_info['overall_gpu_usage'] = 0.0
    except Exception as e:
        gpu_info['gpu_monitoring_error'] = str(e)
        gpu_info['overall_gpu_usage'] = 0.0

    print(f"DEBUG - Final gpu_info: {gpu_info}")
    return gpu_info

@app.route('/api/usage', methods=['GET'])
def get_usage():
    """API endpoint to get current system usage"""
    cpu_usage, ram_usage, gpu_usage = get_system_usage()
    data = {
        'cpu': cpu_usage,
        'ram': ram_usage,
        'gpu': gpu_usage,
        'timestamp': datetime.now().isoformat()
    }
    return jsonify(data)

@app.route('/api/logs', methods=['GET'])
def get_logs():
    """API endpoint to get usage logs from local folder"""
    logs = []
    if os.path.exists(LOG_FOLDER):
        for filename in sorted(os.listdir(LOG_FOLDER), reverse=True):
            if filename.startswith('system_usage_') and filename.endswith('.log'):
                file_path = os.path.join(LOG_FOLDER, filename)
                try:
                    with open(file_path, 'r') as f:
                        lines = f.readlines()
                        for line in lines[1:]:  # Skip header
                            if 'CPU Usage:' in line:
                                timestamp_str = line.split(' - ')[0]
                                try:
                                    timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S,%f')
                                except:
                                    timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                                parts = line.split(' - ')[1].strip()
                                cpu_part = parts.split(', ')[0].split(': ')[1].rstrip('%')
                                ram_part = parts.split(', ')[1].split(': ')[1].rstrip('%')
                                gpu_part = ', '.join(parts.split(', ')[2:]) if len(parts.split(', ')) > 2 else ''

                                # Extract GPU usage for charting
                                gpu_load = 0
                                if gpu_part:
                                    # Look for overall_gpu_usage in the GPU string
                                    if 'overall_gpu_usage' in gpu_part:
                                        try:
                                            usage_part = gpu_part.split('overall_gpu_usage: ')[1].split(',')[0]
                                            gpu_load = float(usage_part)
                                        except:
                                            pass

                                logs.append({
                                    'timestamp': timestamp.isoformat(),
                                    'cpu': float(cpu_part),
                                    'ram': float(ram_part),
                                    'gpu': gpu_part,
                                    'gpu_load': gpu_load
                                })
                        break  # Only read the latest log file
                except Exception as e:
                    continue
    return jsonify(logs)

@app.route('/api/drive-logs', methods=['GET'])
def get_drive_logs():
    """API endpoint to get usage logs from Google Drive"""
    try:
        creds = None
        if os.path.exists(TOKEN_FILE):
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                return jsonify({'error': 'Authentication required. Please run the backend locally first to authenticate with Google Drive.'}), 401

        service = build('drive', 'v3', credentials=creds)

        # Search for log files in the specified folder
        query = f"name contains 'system_usage_' and '{UPLOAD_FOLDER_ID}' in parents" if UPLOAD_FOLDER_ID else "name contains 'system_usage_'"
        results = service.files().list(q=query, orderBy='createdTime desc', pageSize=10).execute()
        files = results.get('files', [])

        if not files:
            return jsonify({'error': 'No log files found in Google Drive'}), 404

        # Get the most recent log file
        file_id = files[0]['id']
        file_content = service.files().get_media(fileId=file_id).execute().decode('utf-8')

        logs = []
        lines = file_content.strip().split('\n')
        for line in lines[1:]:  # Skip header
            if 'CPU Usage:' in line:
                timestamp_str = line.split(' - ')[0]
                try:
                    timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S,%f')
                except:
                    timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                parts = line.split(' - ')[1].strip()
                cpu_part = parts.split(', ')[0].split(': ')[1].rstrip('%')
                ram_part = parts.split(', ')[1].split(': ')[1].rstrip('%')
                gpu_part = ', '.join(parts.split(', ')[2:]) if len(parts.split(', ')) > 2 else ''

                # Extract GPU usage for charting
                gpu_load = 0
                if gpu_part:
                    print(f"Parsing GPU part: '{gpu_part}'")  # Debug
                    # Look for "GPU Usage: X%" pattern from logs
                    if 'GPU Usage: ' in gpu_part:
                        try:
                            usage_str = gpu_part.split('GPU Usage: ')[1].split('%')[0].strip()
                            print(f"Extracted usage string: '{usage_str}'")  # Debug
                            gpu_load = float(usage_str)
                            print(f"Parsed GPU load: {gpu_load}")  # Debug
                        except Exception as e:
                            print(f"Error parsing GPU usage: {e}")
                            pass
                    # Also check for overall_gpu_usage in the GPU string (for future compatibility)
                    elif 'overall_gpu_usage' in gpu_part:
                        try:
                            usage_part = gpu_part.split('overall_gpu_usage: ')[1].split(',')[0]
                            gpu_load = float(usage_part)
                        except:
                            pass

                logs.append({
                    'timestamp': timestamp.isoformat(),
                    'cpu': float(cpu_part),
                    'ram': float(ram_part),
                    'gpu': gpu_part,
                    'gpu_load': gpu_load
                })

        return jsonify(logs)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def run_flask_server():
    """Run Flask server in a separate thread"""
    print("Starting Flask server on http://localhost:5000")
    server = make_server('0.0.0.0', 5000, app)
    print("Flask server started successfully")
    server.serve_forever()

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
        gpu_str = ", ".join([f"{key}: {value}" for key, value in (gpu or {}).items()])
        gpu_usage = gpu.get('overall_gpu_usage', 0) if gpu else 0
        logging.info(f"CPU Usage: {cpu:.1f}%, RAM Usage: {ram:.1f}%, GPU Usage: {gpu_usage:.1f}%")
        time.sleep(4)  # Log every 4 seconds to match the 5-second frontend refresh

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

    # Start Flask server thread
    flask_thread = threading.Thread(target=run_flask_server)
    flask_thread.daemon = True
    flask_thread.start()

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