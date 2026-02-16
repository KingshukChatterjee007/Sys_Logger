import psutil
import logging
import os
import sys
import time
import atexit
import signal
import json
from datetime import datetime, timedelta
import requests
import socket
import threading
import uuid
import pickle
try:
    import redis
except ImportError:
    redis = None
import subprocess
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from werkzeug.serving import make_server
from dotenv import load_dotenv
import pickle
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

# Global data structures for units, usage, and alerts
# Global data structures for units, usage, and alerts
units = {}  # Dictionary to store registered units (Local Fallback)
unit_usage = {}  # Dictionary to store usage data per unit (Local Fallback)
alerts = []  # List to store all alerts (Local Fallback)
ngrok_url = None  # Store ngrok tunnel URL
ngrok_process = None  # Store ngrok process handle

# Redis Configuration
USE_REDIS = os.getenv('USE_REDIS', 'false').lower() == 'true'
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
redis_client = None

if USE_REDIS and redis:
    try:
        redis_client = redis.from_url(REDIS_URL)
        redis_client.ping()
        print(f"Connected to Redis at {REDIS_URL}")
    except Exception as e:
        print(f"Failed to connect to Redis: {e}. Falling back to in-memory storage.")
        USE_REDIS = False
elif USE_REDIS and not redis:
    print("Redis enabled but 'redis' library not installed. Falling back to in-memory storage.")
    USE_REDIS = False

class UnitStore:
    """Abstract store for units and usage to switch between Memory and Redis"""
    
    @staticmethod
    def get_unit(unit_id):
        if USE_REDIS:
            data = redis_client.hget('units', unit_id)
            return json.loads(data) if data else None
        return units.get(unit_id)

    @staticmethod
    def get_unit_by_org_comp(org_id, comp_id):
        """Find a unit by its organization and computer ID"""
        all_units = UnitStore.get_all_units()
        for unit in all_units:
            if unit.get('org_id') == org_id and unit.get('comp_id') == comp_id:
                return unit
        return None

    @staticmethod
    def save_unit(unit_id, unit_data):
        if USE_REDIS:
            redis_client.hset('units', unit_id, json.dumps(unit_data))
        else:
            units[unit_id] = unit_data

    @staticmethod
    def delete_unit(unit_id):
        if USE_REDIS:
            redis_client.hdel('units', unit_id)
            redis_client.delete(f'usage:{unit_id}')
        else:
            if unit_id in units: del units[unit_id]
            if unit_id in unit_usage: del unit_usage[unit_id]

    @staticmethod
    def get_all_units():
        if USE_REDIS:
            raw_units = redis_client.hgetall('units')
            return [json.loads(u) for u in raw_units.values()]
        return list(units.values())

    @staticmethod
    def get_units_by_org(org_id):
        """Get all units for a specific organization"""
        all_units = UnitStore.get_all_units()
        return [unit for unit in all_units if unit.get('org_id') == org_id]

    @staticmethod
    def add_usage(unit_id, usage_data):
        if USE_REDIS:
            # Store as list in Redis, capped at 100
            key = f'usage:{unit_id}'
            redis_client.rpush(key, json.dumps(usage_data))
            redis_client.ltrim(key, -100, -1)
        else:
            if unit_id not in unit_usage:
                unit_usage[unit_id] = []
            unit_usage[unit_id].append(usage_data)
            if len(unit_usage[unit_id]) > 100:
                unit_usage[unit_id] = unit_usage[unit_id][-100:]

    @staticmethod
    def get_usage(unit_id, limit=50):
        if USE_REDIS:
            raw_data = redis_client.lrange(f'usage:{unit_id}', -limit, -1)
            return [json.loads(d) for d in raw_data]
        return unit_usage.get(unit_id, [])[-limit:]

    @staticmethod
    def get_all_usage_grouped():
        """Helper to get all usage for aggregation"""
        if USE_REDIS:
            all_usage = {}
            keys = redis_client.keys('usage:*')
            for key in keys:
                unit_id = key.decode().split(':')[1]
                raw = redis_client.lrange(key, -100, -1)
                all_usage[unit_id] = [json.loads(d) for d in raw]
            return all_usage
        return unit_usage


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

# CORS Configuration - Configure BEFORE routes are defined
CORS_ORIGINS_STR = os.getenv('CORS_ORIGINS', 'http://localhost:3000')
if CORS_ORIGINS_STR.strip() == '*':
    CORS(app, allow_origins="*")
else:
    CORS_ORIGINS = [origin.strip() for origin in CORS_ORIGINS_STR.split(',')]
    CORS(app, allow_origins=CORS_ORIGINS)

print(f"CORS configured for origins: {CORS_ORIGINS if CORS_ORIGINS_STR.strip() != '*' else '*'}")

# Initialize SocketIO
socketio = SocketIO(app, cors_allowed_origins=CORS_ORIGINS if CORS_ORIGINS_STR.strip() != '*' else "*")

# Set up logging directory
if not os.path.exists(LOG_FOLDER):
    os.makedirs(LOG_FOLDER)

# Create session start timestamp
session_start = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
LOG_FILE = os.path.join(LOG_FOLDER, f'system_usage_{session_start}.log')

# Set up logging
logging.basicConfig(filename=LOG_FILE, level=logging.INFO,
                    format='%(asctime)s - %(message)s')

# Flag to track if logging thread has been started
_logging_thread_started = False

def start_logging_thread():
    """Start the logging thread if not already started (for Gunicorn/WSGI servers)"""
    global _logging_thread_started
    if not _logging_thread_started:
        # Clean up old logs
        cleanup_old_logs()
        
        # Register exit handler
        atexit.register(on_exit)
        
        # Start logging thread
        logging_thread = threading.Thread(target=log_usage)
        logging_thread.daemon = True
        logging_thread.start()
        _logging_thread_started = True
        logging.info("Logging thread started automatically")

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
    global ngrok_url, ngrok_process
    health_data = {
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'system-logger',
        'version': '1.0.0',
        'uptime': time.time() - _start_time if '_start_time' in globals() else 0,
        #'units_count': len(units),
        'units_count': len(UnitStore.get_all_units()),
        'alerts_count': len(alerts),
        'service_mode': len(sys.argv) > 1 and sys.argv[1] == '--service'
    }

    # Add ngrok status if available
    if ngrok_process:
        health_data['ngrok'] = {
            'active': ngrok_process.poll() is None,
            'url': ngrok_url
        }

    return jsonify(health_data)

@app.route('/api/config', methods=['GET'])
def get_config():
    """Get server configuration"""
    global ngrok_url
    config = {
        'host': HOST,
        'port': PORT,
        'cors_origins': CORS_ORIGINS_STR if CORS_ORIGINS_STR.strip() != '*' else '*'
    }

    # Add ngrok URL if available
    if ngrok_url:
        config['ngrok_url'] = ngrok_url
        config['public_url'] = ngrok_url
    else:
        # Fallback to local URL
        config['public_url'] = f"http://{HOST}:{PORT}"

    return jsonify(config)

@app.route('/api/register_unit', methods=['POST'])
def register_unit():
    """Register a new unit with the system (supports Org/Comp multi-tenancy)"""
    try:
        data = request.get_json()
        if not data or 'system_id' not in data:
            return jsonify({'error': 'system_id required'}), 400

        system_id = data['system_id']
        org_id = data.get('org_id', 'default_org')
        comp_id = data.get('comp_id', 'default_comp')
        hostname = data.get('hostname', 'Unknown')
        os_info = data.get('os_info', 'Unknown')
        cpu_info = data.get('cpu_info', 'Unknown')
        ram_total = data.get('ram_total', 0)
        gpu_info = data.get('gpu_info', '{}')
        network_interfaces = data.get('network_interfaces', '{}')

        # Check if already registered by system_id or org/comp pair
        existing_unit = None
        all_units = UnitStore.get_all_units()
        for unit in all_units:
            if unit['system_id'] == system_id or (unit.get('org_id') == org_id and unit.get('comp_id') == comp_id):
                existing_unit = unit
                break

        if existing_unit:
            unit_id = existing_unit['id']
            existing_unit['last_seen'] = datetime.now().isoformat()
            existing_unit['status'] = 'online'
            existing_unit['org_id'] = org_id
            existing_unit['comp_id'] = comp_id
            
            # Update unit info if provided
            if hostname != 'Unknown': existing_unit['hostname'] = hostname
            if os_info != 'Unknown': existing_unit['os_info'] = os_info
            if cpu_info != 'Unknown': existing_unit['cpu_info'] = cpu_info
            if ram_total > 0: existing_unit['ram_total'] = ram_total
            if gpu_info != '{}': existing_unit['gpu_info'] = gpu_info
            if network_interfaces != '{}': existing_unit['network_interfaces'] = network_interfaces
            
            UnitStore.save_unit(unit_id, existing_unit)
            return jsonify({'unit_id': unit_id, 'org_id': org_id, 'comp_id': comp_id}), 200

        # Create new unit
        unit_id = str(uuid.uuid4())[:8]
        unit = {
            'id': unit_id,
            'system_id': system_id,
            'org_id': org_id,
            'comp_id': comp_id,
            'name': f"{org_id}/{comp_id}",
            'status': 'online',
            'last_seen': datetime.now().isoformat(),
            'hostname': hostname,
            'os_info': os_info,
            'cpu_info': cpu_info,
            'ram_total': ram_total,
            'gpu_info': gpu_info,
            'network_interfaces': network_interfaces,
            'alerts': []
        }

        UnitStore.save_unit(unit_id, unit)
        print(f"Unit registered: {org_id}/{comp_id} (ID: {unit_id})")

        # Broadcast update (optionally join room)
        socketio.emit('units_update', UnitStore.get_all_units())
        socketio.emit('org_units_update', UnitStore.get_units_by_org(org_id), room=org_id)

        return jsonify({'unit_id': unit_id, 'org_id': org_id, 'comp_id': comp_id}), 201

    except Exception as e:
        print(f"Error registering unit: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/submit_usage', methods=['POST'])
def submit_usage():
    """Submit usage data from a unit"""
    try:
        data = request.get_json()
        if not data or 'system_id' not in data:
            return jsonify({'error': 'system_id required'}), 400

        system_id = data['system_id']
        org_id = data.get('org_id', 'default_org')
        timestamp = data.get('timestamp', datetime.now().isoformat())
        cpu_usage = data.get('cpu_usage', 0)
        ram_usage = data.get('ram_usage', 0)
        gpu_usage = data.get('gpu_usage', 0)
        temperature = data.get('temperature')
        network_rx = data.get('network_rx', 0)
        network_tx = data.get('network_tx', 0)

        # Find unit by system_id
        unit_id = None
        current_unit = None
        all_units = UnitStore.get_all_units()
        for unit in all_units:
            if unit['system_id'] == system_id:
                unit_id = unit['id']
                current_unit = unit
                org_id = unit.get('org_id', org_id)
                break

        if not unit_id:
            return jsonify({'error': 'Unit not registered'}), 404

        # Update unit status
        if current_unit:
            current_unit['last_seen'] = datetime.now().isoformat()
            current_unit['status'] = 'online'
            UnitStore.save_unit(unit_id, current_unit)

        # Store usage data
        usage_entry = {
            'timestamp': timestamp,
            'unit_id': unit_id,
            'cpu': cpu_usage,
            'ram': ram_usage,
            'gpu': gpu_usage,
            'temperature': temperature,
            'network_rx': network_rx,
            'network_tx': network_tx
        }
        UnitStore.add_usage(unit_id, usage_entry)

        # Check for alerts
        new_alerts = []
        if cpu_usage > 90:
            new_alerts.append({
                'id': str(uuid.uuid4())[:8],
                'unit_id': unit_id,
                'type': 'cpu',
                'message': f'High CPU usage: {cpu_usage:.1f}%',
                'severity': 'high',
                'timestamp': datetime.now().isoformat(),
                'acknowledged': False
            })
        if ram_usage > 95:
            new_alerts.append({
                'id': str(uuid.uuid4())[:8],
                'unit_id': unit_id,
                'type': 'ram',
                'message': f'High RAM usage: {ram_usage:.1f}%',
                'severity': 'high',
                'timestamp': datetime.now().isoformat(),
                'acknowledged': False
            })
        if gpu_usage > 95:
            new_alerts.append({
                'id': str(uuid.uuid4())[:8],
                'unit_id': unit_id,
                'type': 'gpu',
                'message': f'High GPU usage: {gpu_usage:.1f}%',
                'severity': 'medium',
                'timestamp': datetime.now().isoformat(),
                'acknowledged': False
            })
        if temperature and temperature > 80:
            new_alerts.append({
                'id': str(uuid.uuid4())[:8],
                'unit_id': unit_id,
                'type': 'temperature',
                'message': f'High temperature: {temperature:.1f}°C',
                'severity': 'high',
                'timestamp': datetime.now().isoformat(),
                'acknowledged': False
            })

        alerts.extend(new_alerts)

        # Broadcast updates via WebSocket (segmented by org)
        socketio.emit('units_update', UnitStore.get_all_units())
        socketio.emit('org_units_update', UnitStore.get_units_by_org(org_id), room=org_id)
        socketio.emit('org_usage_update', usage_entry, room=org_id)
        
        if new_alerts:
            socketio.emit('alerts_update', alerts)

        print(f"Usage data received from {org_id}/{current_unit.get('comp_id')}: CPU={cpu_usage:.1f}%")

        return jsonify({'status': 'success'}), 200

    except Exception as e:
        print(f"Error submitting usage: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/units', methods=['GET'])
def get_units():
    """Get all registered units"""
    try:
        return jsonify(UnitStore.get_all_units()), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/alerts', methods=['GET'])
def get_alerts():
    """Get all alerts"""
    try:
        return jsonify(alerts), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/orgs/<org_id>/units', methods=['GET'])
def get_org_units(org_id):
    """Get all units for an organization"""
    try:
        return jsonify(UnitStore.get_units_by_org(org_id)), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/orgs/<org_id>/usage', methods=['GET'])
def get_org_usage(org_id):
    """Get latest usage for all units in an organization"""
    try:
        units = UnitStore.get_units_by_org(org_id)
        result = []
        for unit in units:
            usage = UnitStore.get_usage(unit['id'], limit=1)
            if usage:
                result.append(usage[0])
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/alerts/<alert_id>/acknowledge', methods=['POST'])
def acknowledge_alert(alert_id):
    """Acknowledge an alert"""
    try:
        for alert in alerts:
            if alert['id'] == alert_id:
                alert['acknowledged'] = True
                socketio.emit('alerts_update', alerts)
                return jsonify({'status': 'success'}), 200
        return jsonify({'error': 'Alert not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/units/<unit_id>', methods=['GET'])
def get_unit(unit_id):
    """Get a specific unit by ID"""
    try:
        unit = UnitStore.get_unit(unit_id)
        if not unit:
            return jsonify({'error': 'Unit not found'}), 404
        return jsonify(unit), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/units/<unit_id>', methods=['PUT'])
def update_unit(unit_id):
    """Update unit information (e.g., custom name)"""
    try:
        unit = UnitStore.get_unit(unit_id)
        if not unit:
            return jsonify({'error': 'Unit not found'}), 404

        data = request.get_json()
        if not data:
            return jsonify({'error': 'No update data provided'}), 400

        # Allow updating name (custom name)
        if 'name' in data:
            unit['name'] = data['name']
            UnitStore.save_unit(unit_id, unit)

        # Broadcast unit update via WebSocket
        socketio.emit('units_update', UnitStore.get_all_units())

        return jsonify(unit), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/units/<unit_id>', methods=['DELETE'])
def delete_unit(unit_id):
    """Remove a unit"""
    try:
        unit = UnitStore.get_unit(unit_id)
        if not unit:
            return jsonify({'error': 'Unit not found'}), 404

        # Remove from units and unit_usage dictionaries
        UnitStore.delete_unit(unit_id)

        # Broadcast unit update via WebSocket
        socketio.emit('units_update', UnitStore.get_all_units())

        return jsonify({'status': 'success', 'message': f'Unit {unit_id} deleted'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/units/<unit_id>/status', methods=['PATCH'])
def update_unit_status(unit_id):
    """Enable/disable monitoring for a unit"""
    try:
        unit = UnitStore.get_unit(unit_id)
        if not unit:
            return jsonify({'error': 'Unit not found'}), 404

        data = request.get_json()
        if not data or 'monitoring_enabled' not in data:
            return jsonify({'error': 'monitoring_enabled field required'}), 400

        monitoring_enabled = data['monitoring_enabled']

        # Initialize monitoring_enabled if not present
        if 'monitoring_enabled' not in unit:
            unit['monitoring_enabled'] = True

        unit['monitoring_enabled'] = monitoring_enabled

        # If disabling monitoring, set status to offline
        if not monitoring_enabled:
            unit['status'] = 'offline'
        # If re-enabling, check if recently seen - for simplicity keep as is
        
        UnitStore.save_unit(unit_id, unit)

        # Broadcast unit update via WebSocket
        socketio.emit('units_update', UnitStore.get_all_units())

        return jsonify(unit), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/unit/<unit_id>/usage', methods=['GET'])
def get_unit_usage(unit_id):
    """Get usage data for a specific unit"""
    try:
        usage_data = UnitStore.get_usage(unit_id, limit=50)

        # Format data to match the expected format (add gpu_load for compatibility)
        formatted_data = []
        for usage in usage_data:
            formatted_entry = dict(usage)
            # Ensure gpu_load is set for frontend compatibility
            if 'gpu' in formatted_entry and 'gpu_load' not in formatted_entry:
                formatted_entry['gpu_load'] = formatted_entry['gpu']
            formatted_data.append(formatted_entry)

        return jsonify(formatted_data), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/all-units-usage', methods=['GET'])
def get_all_units_usage():
    """Get averaged usage data across all units grouped by timestamp"""
    try:
        # Dictionary to aggregate data by timestamp
        aggregated_data = {}

        all_usages = UnitStore.get_all_usage_grouped()
        for unit_id, usages in all_usages.items():
            for usage in usages[-100:]:  # Look at last 100 entries per unit
                timestamp = usage.get('timestamp')
                if not timestamp:
                    continue

                if timestamp not in aggregated_data:
                    aggregated_data[timestamp] = {
                        'cpu': [],
                        'ram': [],
                        'gpu': [],
                        'temperature': [],
                        'count': 0
                    }

                # Collect values for averaging
                if 'cpu' in usage and usage['cpu'] is not None:
                    aggregated_data[timestamp]['cpu'].append(float(usage['cpu']))
                if 'ram' in usage and usage['ram'] is not None:
                    aggregated_data[timestamp]['ram'].append(float(usage['ram']))
                if 'gpu' in usage and usage['gpu'] is not None:
                    aggregated_data[timestamp]['gpu'].append(float(usage['gpu']))
                if 'temperature' in usage and usage['temperature'] is not None:
                    aggregated_data[timestamp]['temperature'].append(float(usage['temperature']))

                aggregated_data[timestamp]['count'] += 1

        # Calculate averages and format output
        result = []
        for timestamp in sorted(aggregated_data.keys())[-50:]:  # Last 50 timestamps
            data = aggregated_data[timestamp]
            avg_entry = {
                'timestamp': timestamp,
                'cpu': sum(data['cpu']) / len(data['cpu']) if data['cpu'] else 0,
                'ram': sum(data['ram']) / len(data['ram']) if data['ram'] else 0,
                'gpu': sum(data['gpu']) / len(data['gpu']) if data['gpu'] else 0,
                'gpu_load': sum(data['gpu']) / len(data['gpu']) if data['gpu'] else 0,  # For compatibility
                'temperature': sum(data['temperature']) / len(data['temperature']) if data['temperature'] else None,
                'unit_count': data['count']  # Number of units contributing to this average
            }
            result.append(avg_entry)

        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@socketio.on('connect')
def handle_connect():
    """Handle WebSocket connection"""
    print("Client connected to WebSocket")

@socketio.on('join_org')
def on_join(data):
    """Join a WebSocket room for an organization"""
    org_id = data.get('org_id')
    if org_id:
        import flask_socketio
        flask_socketio.join_room(org_id)
        print(f"Client joined room: {org_id}")

@socketio.on('disconnect')
def handle_disconnect():
    """Handle WebSocket disconnection"""
    print("Client disconnected from WebSocket")

def run_flask_server():
    """Run Flask-SocketIO server in a separate thread"""
    print(f"Starting Flask-SocketIO server on http://{HOST}:{PORT}")
    socketio.run(app, host=HOST, port=PORT, debug=FLASK_DEBUG, allow_unsafe_werkzeug=True)

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
    global _start_time
    _start_time = time.time()
    atexit.register(on_exit)

    # Set up signal handlers for graceful shutdown
    def signal_handler(signum, frame):
        logging.info(f"Received signal {signum}, initiating graceful shutdown")
        on_exit()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

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
        # Interactive mode - keep running until interrupted
        print("Backend is running. Press Ctrl+C to stop and upload logs...")
        try:
            # Keep the main thread alive
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nShutting down...")
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

# Start logging thread automatically when imported by Gunicorn
# This ensures data collection happens even when not running via main()
# Note: cleanup_old_logs and on_exit are defined above, so this is safe
if __name__ != "__main__":
    # Start in a separate thread to avoid blocking module import
    def _init_logging():
        time.sleep(0.5)  # Give time for all imports to complete
        start_logging_thread()
    threading.Thread(target=_init_logging, daemon=True).start()

if __name__ == "__main__":
    main()