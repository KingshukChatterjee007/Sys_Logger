import psutil
import logging
import os
import sys
import time
import atexit
from datetime import datetime, timedelta
import requests
import socket
import threading
from flask import Flask, jsonify
from flask_cors import CORS
from werkzeug.serving import make_server
from dotenv import load_dotenv
try:
    import GPUtil
    NVIDIA_AVAILABLE = True
except ImportError:
    NVIDIA_AVAILABLE = False
AMD_AVAILABLE = False  # AMD GPU monitoring not available - library not found

# Load environment variables
if getattr(sys, 'frozen', False):
    # Running as exe, load from bundled .env file
    bundle_dir = getattr(sys, '_MEIPASS', '.')
    env_path = os.path.join(bundle_dir, '.env')
    load_dotenv(env_path)
else:
    # Running as script, load from current directory
    load_dotenv()

app = Flask(__name__)
# CORS will be configured after environment variables are loaded

# Load Flask debug flag early for use in functions
FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'

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
                            if FLASK_DEBUG:
                                print(f"PowerShell GPU Detection: {usage_value:.1f}%")
                            return gpu_info
                        except ValueError:
                            continue

        except Exception as e:
            if FLASK_DEBUG:
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
                    if FLASK_DEBUG:
                        print(f"TypePerf GPU Detection: {engine_count} engines, max usage: {max_gpu_usage:.1f}%")
                    return gpu_info

        if FLASK_DEBUG:
            print("No GPU usage detected")
        gpu_info['overall_gpu_usage'] = 0.0
        gpu_info['detection_method'] = 'none'

    except subprocess.TimeoutExpired:
        gpu_info['gpu_monitoring_timeout'] = 'GPU monitoring timed out'
        gpu_info['overall_gpu_usage'] = 0.0
    except Exception as e:
        gpu_info['gpu_monitoring_error'] = str(e)
        gpu_info['overall_gpu_usage'] = 0.0

    return gpu_info

# Configuration - Load before routes
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')  # Set your GitHub personal access token as environment variable
LOG_FOLDER = os.getenv('LOG_FOLDER', 'C://Usage_Logs')
LOG_RETENTION_DAYS = int(os.getenv('LOG_RETENTION_DAYS', '2'))
LOG_INTERVAL = int(os.getenv('LOG_INTERVAL', '4'))
CREDENTIALS_FILE = 'credentials.json'
TOKEN_FILE = 'token.json'
UPLOAD_FOLDER_ID = 'Usage Logs'  # Set this to your Google Drive folder ID

# Flask Configuration
FLASK_ENV = os.getenv('FLASK_ENV', 'development')
# FLASK_DEBUG already defined above
PORT = int(os.getenv('PORT', '5000'))
HOST = os.getenv('HOST', '0.0.0.0')

# CORS Configuration - Configure before routes
CORS_ORIGINS_STR = os.getenv('CORS_ORIGINS', 'http://localhost:3000')
if CORS_ORIGINS_STR.strip() == '*':
    CORS(app, resources={r"/api/*": {"origins": "*"}})
else:
    CORS_ORIGINS = [origin.strip() for origin in CORS_ORIGINS_STR.split(',')]
    CORS(app, resources={r"/api/*": {"origins": CORS_ORIGINS}})

# Set up logging directory
if not os.path.exists(LOG_FOLDER):
    os.makedirs(LOG_FOLDER)

# Create session start timestamp
session_start = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
LOG_FILE = os.path.join(LOG_FOLDER, f'system_usage_{session_start}.log')

# Set up logging
logging.basicConfig(filename=LOG_FILE, level=logging.INFO,
                    format='%(asctime)s - %(message)s')

@app.route('/api/usage', methods=['GET'])
def get_usage():
    """API endpoint to get current system usage"""
    try:
        cpu_usage, ram_usage, gpu_usage = get_system_usage()
        data = {
            'cpu': cpu_usage,
            'ram': ram_usage,
            'gpu': gpu_usage,
            'timestamp': datetime.now().isoformat()
        }
        return jsonify(data)
    except Exception as e:
        logging.error(f"Error getting usage: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/logs', methods=['GET'])
def get_logs():
    """API endpoint to get usage logs from local folder"""
    try:
        logs = []
        if os.path.exists(LOG_FOLDER):
            for filename in sorted(os.listdir(LOG_FOLDER), reverse=True):
                if filename.startswith('system_usage_') and filename.endswith('.log'):
                    file_path = os.path.join(LOG_FOLDER, filename)
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            lines = f.readlines()
                            for line in lines[1:]:  # Skip header
                                if 'CPU Usage:' in line:
                                    timestamp_str = line.split(' - ')[0]
                                    try:
                                        timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S,%f')
                                    except (ValueError, AttributeError):
                                        try:
                                            timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                                        except (ValueError, AttributeError):
                                            continue  # Skip invalid timestamp
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
                                            except (ValueError, IndexError, AttributeError):
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
    except Exception as e:
        logging.error(f"Error getting logs: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/gist-logs', methods=['GET'])
def get_gist_logs():
    """API endpoint to get usage logs from GitHub Gist"""
    try:
        if not GITHUB_TOKEN:
            return jsonify({'error': 'GITHUB_TOKEN environment variable not set'}), 500

        # First, get the user's gists to find the system_usage gist
        headers = {
            'Authorization': f'token {GITHUB_TOKEN}',
            'Accept': 'application/vnd.github.v3+json'
        }

        response = requests.get('https://api.github.com/gists', headers=headers)
        if response.status_code != 200:
            return jsonify({'error': f'Failed to fetch gists: {response.text}'}), response.status_code

        gists = response.json()
        usage_gist = None

        # Find the gist with system_usage_ in the filename
        for gist in gists:
            for filename in gist['files']:
                if 'system_usage_' in filename:
                    usage_gist = gist
                    break
            if usage_gist:
                break

        if not usage_gist:
            return jsonify({'error': 'No system usage gist found'}), 404

        # Get the content of the latest file
        for filename, file_info in usage_gist['files'].items():
            if 'system_usage_' in filename:
                raw_url = file_info['raw_url']
                content_response = requests.get(raw_url)
                if content_response.status_code != 200:
                    return jsonify({'error': f'Failed to fetch gist content: {content_response.text}'}), content_response.status_code

                file_content = content_response.text
                break

        logs = []
        lines = file_content.strip().split('\n')
        for line in lines[1:]:  # Skip header
            if 'CPU Usage:' in line:
                timestamp_str = line.split(' - ')[0]
                try:
                    timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S,%f')
                except (ValueError, AttributeError):
                    try:
                        timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                    except (ValueError, AttributeError):
                        continue  # Skip invalid timestamp
                parts = line.split(' - ')[1].strip()
                cpu_part = parts.split(', ')[0].split(': ')[1].rstrip('%')
                ram_part = parts.split(', ')[1].split(': ')[1].rstrip('%')
                gpu_part = ', '.join(parts.split(', ')[2:]) if len(parts.split(', ')) > 2 else ''

                # Extract GPU usage for charting
                gpu_load = 0
                if gpu_part:
                    # Look for "GPU Usage: X%" pattern from logs
                    if 'GPU Usage: ' in gpu_part:
                        try:
                            usage_str = gpu_part.split('GPU Usage: ')[1].split('%')[0].strip()
                            gpu_load = float(usage_str)
                        except Exception as e:
                            if FLASK_DEBUG:
                                logging.debug(f"Error parsing GPU usage: {e}")
                            pass
                    # Also check for overall_gpu_usage in the GPU string (for future compatibility)
                    elif 'overall_gpu_usage' in gpu_part:
                        try:
                            usage_part = gpu_part.split('overall_gpu_usage: ')[1].split(',')[0]
                            gpu_load = float(usage_part)
                        except (ValueError, IndexError, AttributeError):
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

# Health check endpoint
@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint for monitoring"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'system-logger'
    })

def run_flask_server():
    """Run Flask server in a separate thread"""
    print(f"Starting Flask server on http://{HOST}:{PORT}")
    server = make_server(HOST, PORT, app)
    print(f"Flask server started successfully on {HOST}:{PORT}")
    server.serve_forever()

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
        time.sleep(LOG_INTERVAL)  # Log at configured interval

def is_connected():
    try:
        socket.create_connection(("www.google.com", 80))
        return True
    except OSError:
        pass
    return False

def cleanup_old_logs():
    """Delete log files older than specified retention days"""
    if not os.path.exists(LOG_FOLDER):
        return

    cutoff_date = datetime.now() - timedelta(days=LOG_RETENTION_DAYS)

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

def upload_to_gist():
    if not GITHUB_TOKEN:
        logging.error("GITHUB_TOKEN environment variable not set. Skipping gist upload.")
        return

    headers = {
        'Authorization': f'token {GITHUB_TOKEN}',
        'Accept': 'application/vnd.github.v3+json'
    }

    # Check if gist already exists
    gist_id = None
    response = requests.get('https://api.github.com/gists', headers=headers)
    if response.status_code == 200:
        gists = response.json()
        for gist in gists:
            for filename in gist['files']:
                if 'system_usage_' in filename:
                    gist_id = gist['id']
                    break
            if gist_id:
                break

    # Read the log file content
    try:
        with open(LOG_FILE, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
    except FileNotFoundError:
        logging.error(f"Log file not found: {LOG_FILE}")
        return
    except Exception as e:
        logging.error(f"Error reading log file: {e}")
        return

    gist_data = {
        'description': f'System usage logs - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
        'public': False,
        'files': {
            os.path.basename(LOG_FILE): {
                'content': content
            }
        }
    }

    if gist_id:
        # Update existing gist
        response = requests.patch(f'https://api.github.com/gists/{gist_id}', headers=headers, json=gist_data)
    else:
        # Create new gist
        response = requests.post('https://api.github.com/gists', headers=headers, json=gist_data)

    if response.status_code in [200, 201]:
        print('Gist uploaded successfully')
        # Delete the log file locally after successful upload
        if os.path.exists(LOG_FILE):
            os.remove(LOG_FILE)
    else:
        logging.error(f"Gist upload failed: {response.text}")

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

    # Check if running as frozen exe or in service mode
    is_frozen = getattr(sys, 'frozen', False)
    is_service = len(sys.argv) > 1 and sys.argv[1] == '--service'

    if is_frozen or is_service:
        logging.info("Running in service mode")
        # In service mode, keep the main thread alive
        # Upload happens periodically (every hour) or on exit
        upload_interval = 3600  # Upload every hour in service mode
        last_upload_time = time.time()
        
        while True:
            time.sleep(60)  # Check every minute
            current_time = time.time()
            
            # Upload if interval has passed
            if current_time - last_upload_time >= upload_interval:
                if GITHUB_TOKEN:
                    if is_connected():
                        try:
                            upload_to_gist()
                            last_upload_time = current_time
                            logging.info("Logs uploaded successfully to gist in service mode.")
                        except Exception as e:
                            logging.error(f"Gist upload failed in service mode: {e}")
                    else:
                        logging.info("Skipping upload: No internet connection in service mode.")
                else:
                    logging.info("Skipping upload: GITHUB_TOKEN environment variable not set (logging works without upload).")
    else:
        input("Press Enter to exit and upload logs...\n")
        if GITHUB_TOKEN:
            if is_connected():
                try:
                    upload_to_gist()
                    print("Logs uploaded to gist successfully.")
                except Exception as e:
                    logging.error(f"Gist upload failed: {e}")
                    print(f"Gist upload failed: {e}")
            else:
                print("Skipping upload: No internet connection.")
        else:
            print("Skipping upload: GITHUB_TOKEN environment variable not found (logging works without upload).")

if __name__ == "__main__":
    main()