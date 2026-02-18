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
import csv
import io
try:
    import redis
except ImportError:
    redis = None
import subprocess
from flask import Flask, jsonify, request, make_response, send_file
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from werkzeug.serving import make_server
from dotenv import load_dotenv
try:
    import GPUtil
    NVIDIA_AVAILABLE = True
except ImportError:
    NVIDIA_AVAILABLE = False
AMD_AVAILABLE = False

# Load environment variables
if getattr(sys, 'frozen', False):
    bundle_dir = getattr(sys, '_MEIPASS', '.')
    env_path = os.path.join(bundle_dir, '.env')
    load_dotenv(env_path)
else:
    load_dotenv()

app = Flask(__name__)
DATA_DIR = 'unit_data'
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

UNITS_DB_FILE = 'units_db.json'

# Global data structures
units = {}  # In-memory cache of units
unit_usage = {}
alerts = []
ngrok_url = None
ngrok_process = None

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

def load_units_db():
    """Load units from JSON file on startup"""
    global units
    if os.path.exists(UNITS_DB_FILE):
        try:
            with open(UNITS_DB_FILE, 'r') as f:
                units = json.load(f)
            print(f"Loaded {len(units)} units from {UNITS_DB_FILE}")
        except Exception as e:
            print(f"Error loading units db: {e}")
            units = {}
    else:
        units = {}

def save_units_db():
    """Save units to JSON file"""
    try:
        with open(UNITS_DB_FILE, 'w') as f:
            json.dump(units, f, indent=2)
    except Exception as e:
        print(f"Error saving units db: {e}")

class UnitStore:
    """Store for units and usage with Persistence"""
    
    @staticmethod
    def get_unit(unit_id):
        if USE_REDIS:
            data = redis_client.hget('units', unit_id)
            return json.loads(data) if data else None
        return units.get(unit_id)

    @staticmethod
    def get_unit_by_org_comp(org_id, comp_id):
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
            save_units_db() # Persist to disk

    @staticmethod
    def delete_unit(unit_id):
        if USE_REDIS:
            redis_client.hdel('units', unit_id)
            redis_client.delete(f'usage:{unit_id}')
        else:
            if unit_id in units: 
                del units[unit_id]
                save_units_db() # Persist to disk
            if unit_id in unit_usage: del unit_usage[unit_id]

    @staticmethod
    def get_all_units():
        if USE_REDIS:
            raw_units = redis_client.hgetall('units')
            return [json.loads(u) for u in raw_units.values()]
        return list(units.values())

    @staticmethod
    def get_unique_orgs():
        all_units = UnitStore.get_all_units()
        orgs = set()
        for unit in all_units:
            if unit.get('org_id'):
                orgs.add(unit.get('org_id'))
        return sorted(list(orgs))

    @staticmethod
    def get_units_by_org(org_id):
        all_units = UnitStore.get_all_units()
        return [unit for unit in all_units if unit.get('org_id') == org_id]

    @staticmethod
    def add_usage(unit_id, usage_data):
        # Persist usage history to disk (JSONL)
        try:
            log_file = os.path.join(DATA_DIR, f'{unit_id}.jsonl')
            with open(log_file, 'a') as f:
                f.write(json.dumps(usage_data) + '\n')
        except Exception as e:
            print(f"Failed to log usage to disk: {e}")

        if USE_REDIS:
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

CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# --- Routes ---

def get_local_ip():
    """Detect the local IP address of this machine"""
    try:
        # Connect to a public DNS to determine the routing IP (doesn't actually send data)
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'ok', 
        'timestamp': datetime.now().isoformat(),
        'local_ip': get_local_ip()
    }), 200

@app.route('/api/units', methods=['GET'])
def get_units():
    return jsonify(UnitStore.get_all_units())

@app.route('/api/orgs', methods=['GET'])
def get_orgs():
    return jsonify(UnitStore.get_unique_orgs())

@app.route('/api/orgs/<org_id>/units', methods=['GET'])
def get_org_units(org_id):
    units = UnitStore.get_units_by_org(org_id)
    return jsonify(units)

@app.route('/api/units/<unit_id>/usage', methods=['GET'])
def get_unit_usage(unit_id):
    data = UnitStore.get_usage(unit_id, limit=100)
    return jsonify(data)

# --- SERVER MONITORING ---

latest_server_stats = {
    'cpu': 0,
    'ram': 0,
    'gpu_load': 0,
    'timestamp': datetime.now().isoformat()
}

class ServerMonitor(threading.Thread):
    def __init__(self):
        super().__init__(daemon=True)
        self.running = True
        self.typeperf_proc = None

    def run(self):
        print("Starting Background Server Monitor...")
        
        # Windows GPU Monitoring via Typeperf (Generic)
        if not NVIDIA_AVAILABLE and os.name == 'nt':
            try:
                # -si 0.1 for 10Hz updates
                cmd = ['typeperf', r'\GPU Engine(*)\Utilization Percentage', '-sc', '0', '-si', '0.1']
                self.typeperf_proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                
                # Skip header lines
                for _ in range(2):
                    self.typeperf_proc.stdout.readline()
            except Exception as e:
                print(f"Failed to start typeperf: {e}")

        while self.running:
            try:
                # 1. CPU & RAM (Fast)
                cpu = psutil.cpu_percent(interval=None)
                ram = psutil.virtual_memory().percent
                gpu = 0.0

                # 2. GPU
                if NVIDIA_AVAILABLE:
                    try:
                        gpus = GPUtil.getGPUs()
                        if gpus:
                            gpu = max(gpu.load * 100 for gpu in gpus)
                    except: pass
                
                elif self.typeperf_proc:
                    try:
                        line = self.typeperf_proc.stdout.readline()
                        if line:
                            parts = line.split(',')
                            # First part is timestamp, rest are values
                            # Remove quotes and convert to float
                            values = []
                            for p in parts[1:]:
                                try:
                                    val = float(p.replace('"', ''))
                                    values.append(val)
                                except: pass
                            
                            if values:
                                gpu = max(values)
                    except Exception as e:
                        print(f"Error reading typeperf: {e}")
                        # Restart typeperf if needed?
                        pass

                # Update Global State
                global latest_server_stats
                latest_server_stats = {
                    'cpu': cpu,
                    'ram': ram,
                    'gpu_load': round(gpu, 1),
                    'timestamp': datetime.now().isoformat()
                }

                # Sleep small amount if not using typeperf blocking read
                if not self.typeperf_proc:
                     time.sleep(0.1)

            except Exception as e:
                print(f"Monitor error: {e}")
                time.sleep(1)

# Start Monitor
monitor = ServerMonitor()
monitor.start()

# Fallback for Global Dashboard
@app.route('/api/usage', methods=['GET'])
def get_system_usage_route():
    # Return cached high-frequency stats
    return jsonify([latest_server_stats])


# --- FLEET MANAGEMENT APIS ---

@app.route('/api/units/<unit_id>', methods=['DELETE'])
def delete_unit(unit_id):
    """Delete a unit from the registry"""
    unit = UnitStore.get_unit(unit_id)
    if not unit:
        return jsonify({'error': 'Unit not found'}), 404
    
    UnitStore.delete_unit(unit_id)
    # Broadcast update
    socketio.emit('units_update', UnitStore.get_all_units())
    return jsonify({'status': 'deleted'}), 200

@app.route('/api/units/<unit_id>', methods=['PUT'])
def update_unit(unit_id):
    """Update unit details (rename/move)"""
    data = request.get_json()
    unit = UnitStore.get_unit(unit_id)
    if not unit:
        return jsonify({'error': 'Unit not found'}), 404
    
    if 'comp_id' in data: unit['comp_id'] = data['comp_id']
    if 'org_id' in data: unit['org_id'] = data['org_id']
    if 'name' in data: unit['name'] = data['name']
    
    UnitStore.save_unit(unit_id, unit)
    socketio.emit('units_update', UnitStore.get_all_units())
    return jsonify(unit), 200

# --- DEPLOYMENT GENERATOR ---

@app.route('/api/deploy/client_source', methods=['GET'])
def serve_client_source():
    """Serve the full unit_client.py source code"""
    try:
        # Assuming unit_client.py is one level up from backend/
        client_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'unit_client.py')
        if os.path.exists(client_path):
            return send_file(client_path, mimetype='text/x-python')
        else:
            return "Client source not found on server.", 404
    except Exception as e:
        return str(e), 500

@app.route('/api/deploy/generate', methods=['GET'])
def generate_deploy_script():
    """Generate a PowerShell script for bulk deployment"""
    org_id = request.args.get('org_id', 'default_org')
    server_url = request.args.get('server', 'http://localhost:5000') 
    
    script_content = f"""
# Sys_Logger Bulk Deployment Script
# Organization: {org_id}
# Target Server: {server_url}

param(
    [string]$OrgId = "{org_id}",
    [string]$ServerUrl = "{server_url}"
)

Write-Host ">>> Starting Sys_Logger Deployment for Org: $OrgId" -ForegroundColor Cyan

# 1. Check Python
if (!(Get-Command python -ErrorAction SilentlyContinue)) {{
    Write-Host "ERROR: Python 3.10+ required." -ForegroundColor Red
    exit
}}

# 2. Install Dependencies
Write-Host "Installing dependencies..."
pip install requests psutil GPUtil flask flask-socketio flask-cors python-dotenv

# 3. Download Client Source
$ClientUrl = "$ServerUrl/api/deploy/client_source"
$ClientPath = Join-Path $PWD "unit_client.py"
$ConfigPath = Join-Path $PWD "unit_client_config.json"

Write-Host "Downloading client from $ClientUrl..."
try {{
    Invoke-WebRequest -Uri $ClientUrl -OutFile $ClientPath
}} catch {{
    Write-Host "Failed to download client source. Connectivity issue?" -ForegroundColor Red
    exit
}}

# 4. Configure Client
$ConfigJson = @"
{{
    "server_url": "$ServerUrl",
    "org_id": "$OrgId",
    "comp_id": "$env:COMPUTERNAME",
    "system_id": "$(New-Guid)"
}}
"@
Set-Content -Path $ConfigPath -Value $ConfigJson

Write-Host "Client configured for $OrgId at $ServerUrl" -ForegroundColor Green
Write-Host "Starting Client..."

# 5. Start Client
Start-Process python -ArgumentList "unit_client.py"
Write-Host "Sys_Logger Client started in background!"
"""
    
    # Return as file download
    response = make_response(script_content)
    response.headers["Content-Disposition"] = f"attachment; filename=deploy_{org_id}.ps1"
    response.headers["Content-Type"] = "text/plain"
    return response

@app.route('/api/alerts', methods=['GET'])
def get_alerts():
    return jsonify(alerts)

@app.route('/api/alerts/<alert_id>/acknowledge', methods=['POST'])
def acknowledge_alert(alert_id):
    global alerts
    for alert in alerts:
        if alert['id'] == alert_id:
            alert['acknowledged'] = True
            return jsonify({'status': 'acknowledged'}), 200
    return jsonify({'error': 'Alert not found'}), 404

@app.route('/api/register_unit', methods=['POST'])
def register_unit():
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

        # Check existing
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
            existing_unit['ip'] = request.remote_addr
            
            if hostname != 'Unknown': existing_unit['hostname'] = hostname
            if os_info != 'Unknown': existing_unit['os_info'] = os_info
            if cpu_info != 'Unknown': existing_unit['cpu_info'] = cpu_info
            if ram_total > 0: existing_unit['ram_total'] = ram_total
            if gpu_info != '{}': existing_unit['gpu_info'] = gpu_info
            if network_interfaces != '{}': existing_unit['network_interfaces'] = network_interfaces
            
            UnitStore.save_unit(unit_id, existing_unit)
            return jsonify({'unit_id': unit_id, 'org_id': org_id, 'comp_id': comp_id}), 200

        # New Unit
        unit_id = str(uuid.uuid4())[:8]
        unit = {
            'id': unit_id,
            'system_id': system_id,
            'org_id': org_id,
            'comp_id': comp_id,
            'ip': request.remote_addr,
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

        socketio.emit('units_update', UnitStore.get_all_units())
        socketio.emit('org_units_update', UnitStore.get_units_by_org(org_id), room=org_id)

        return jsonify({'unit_id': unit_id, 'org_id': org_id, 'comp_id': comp_id}), 201

    except Exception as e:
        print(f"Error registering unit: {e}")
        return jsonify({'error': str(e)}), 500

def process_usage_record(data):
    """Process a single usage record"""
    if not data or 'unit_id' not in data:
        return False, 'unit_id required'

    unit_id = data['unit_id']
    org_id = data.get('org_id')
    unit = UnitStore.get_unit(unit_id)
    
    if not unit:
        return False, 'Unit not registered'

    unit['last_seen'] = datetime.now().isoformat()
    unit['status'] = 'online'
    UnitStore.save_unit(unit_id, unit) # Updates last_seen
    UnitStore.add_usage(unit_id, data)

    socketio.emit('usage_update', {'unit_id': unit_id, 'data': data})
    if org_id:
            socketio.emit('org_usage_update', {'unit_id': unit_id, 'data': data}, room=org_id)
            
    return True, 'processed'

@app.route('/api/report_usage', methods=['POST'])
def report_usage():
    try:
        data = request.get_json()
        
        # Batch Processing
        if isinstance(data, list):
            success_count = 0
            for item in data:
                success, _ = process_usage_record(item)
                if success: success_count += 1
            
            return jsonify({'status': 'received batch', 'processed': success_count}), 200

        # Single Record Processing
        else:
            success, msg = process_usage_record(data)
            if not success:
                # Keep 404 for "Unit not registered" to trigger client re-registration
                if msg == 'Unit not registered':
                    return jsonify({'error': msg}), 404
                return jsonify({'error': msg}), 400
                
            return jsonify({'status': 'received'}), 200

    except Exception as e:
        print(f"Error reporting usage: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/units/<unit_id>/export', methods=['GET'])
def export_unit_data(unit_id):
    try:
        time_range = request.args.get('range', '1d')
        days = 1
        if time_range == '5d': days = 5
        elif time_range == '10d': days = 10
        elif time_range == 'all': days = 9999
        
        start_date = datetime.now() - timedelta(days=days)
        log_file = os.path.join(DATA_DIR, f'{unit_id}.jsonl')
        
        if not os.path.exists(log_file):
            return jsonify({'error': 'No data found for this unit'}), 404

        si = io.StringIO()
        cw = csv.writer(si)
        cw.writerow(['Timestamp', 'CPU (%)', 'RAM (%)', 'GPU Load (%)'])
        
        records = []
        with open(log_file, 'r') as f:
            for line in f:
                try:
                    record = json.loads(line)
                    ts_str = record.get('timestamp', '')
                    if ts_str.endswith('Z'): ts_str = ts_str[:-1]
                    try: 
                        record_time = datetime.fromisoformat(ts_str)
                    except: 
                        continue
                    
                    if record_time >= start_date:
                        # Normalize keys
                        cpu = record.get('cpu') if record.get('cpu') is not None else record.get('cpu_usage', 0)
                        ram = record.get('ram') if record.get('ram') is not None else record.get('ram_usage', 0)
                        
                        # GPU Logic: Try gpu_load -> gpu_usage -> gpu (complex)
                        gpu = 0
                        if record.get('gpu_load') is not None:
                            gpu = record.get('gpu_load')
                        elif record.get('gpu_usage') is not None:
                            gpu = record.get('gpu_usage')
                        elif record.get('gpu'):
                             # Fallback for old complex objects if any
                             try: gpu = float(record['gpu'])
                             except: pass

                        # Convert to IST (UTC + 5:30)
                        ist_offset = timedelta(hours=5, minutes=30)
                        dt_ist = record_time + ist_offset
                        
                        records.append({
                            'timestamp': dt_ist.strftime('%Y-%m-%d %H:%M:%S'),
                            'dt': record_time, # Keep original for sorting
                            'cpu': cpu,
                            'ram': ram,
                            'gpu': gpu
                        })
                except Exception:
                    continue

        # Sort by timestamp
        records.sort(key=lambda x: x['dt'])

        for r in records:
            cw.writerow([
                r['timestamp'],
                r['cpu'],
                r['ram'],
                r['gpu']
            ])

        output = make_response(si.getvalue())
        output.headers["Content-Disposition"] = f"attachment; filename={unit_id}_usage_{time_range}.csv"
        output.headers["Content-type"] = "text/csv"
        return output

    except Exception as e:
        print(f"Export error: {e}")
        return jsonify({'error': str(e)}), 500

@socketio.on('connect')
def handle_connect():
    emit('units_update', UnitStore.get_all_units())

@socketio.on('join_org')
def handle_join_org(data):
    org_id = data.get('org_id')
    if org_id:
        from flask_socketio import join_room
        join_room(org_id)
        emit('org_units_update', UnitStore.get_units_by_org(org_id))

if __name__ == '__main__':
    load_units_db() # Load saved units
    socketio.run(app, host='0.0.0.0', port=5001, debug=True, allow_unsafe_werkzeug=True)