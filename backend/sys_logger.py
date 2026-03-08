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
import psycopg2
from psycopg2.extras import RealDictCursor
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
import jwt
from functools import wraps
import bcrypt
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

# DB Config
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASS = os.getenv('DB_PASS', 'postgres')
DB_NAME = 'sys_logger'

def get_db_connection():
    conn = psycopg2.connect(host=DB_HOST, user=DB_USER, password=DB_PASS, dbname=DB_NAME)
    return conn

app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'sys-logger-super-secret-key')
socketio = SocketIO(app, cors_allowed_origins="*")

# Auth Decorator
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header.split(" ")[1]
        
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            # In a real app, query DB for user to ensure they still exist
            current_user = data
        except Exception as e:
            return jsonify({'message': 'Token is invalid!', 'error': str(e)}), 401
            
        return f(current_user, *args, **kwargs)
    return decorated

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

# --- AUTHENTICATION ROUTES ---

@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    org_id = data.get('org_id')
    role = data.get('role', 'USER')
    
    if not email or not password or not org_id:
        return jsonify({'message': 'Missing required fields!'}), 400
        
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    # Check if user exists
    cur.execute("SELECT * FROM users WHERE email = %s", (email,))
    if cur.fetchone():
        return jsonify({'message': 'User already exists!'}), 400
        
    # Check if org exists, if not create it (auto-bootstrap)
    cur.execute("SELECT * FROM organizations WHERE org_id = %s", (org_id,))
    if not cur.fetchone():
        cur.execute("INSERT INTO organizations (org_id, name) VALUES (%s, %s)", (org_id, org_id))
    
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    cur.execute(
        "INSERT INTO users (email, password_hash, role, org_id) VALUES (%s, %s, %s, %s)",
        (email, password_hash, role, org_id)
    )
    
    conn.commit()
    cur.close()
    conn.close()
    
    return jsonify({'message': 'User registered successfully!'}), 201

@app.route('/api/auth/login', methods=['POST'])
def login():
    auth = request.get_json()
    if not auth or not auth.get('email') or not auth.get('password'):
        return make_response('Could not verify', 401, {'WWW-Authenticate': 'Basic realm="Login required!"'})
    
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM users WHERE email = %s", (auth.get('email'),))
    user = cur.fetchone()
    cur.close()
    conn.close()
    
    if not user:
        return make_response('Could not verify', 401, {'WWW-Authenticate': 'Basic realm="Login required!"'})
        
    if bcrypt.checkpw(auth.get('password').encode('utf-8'), user['password_hash'].encode('utf-8')):
        token = jwt.encode({
            'user_id': user['user_id'],
            'email': user['email'],
            'role': user['role'],
            'org_id': user['org_id'],
            'exp': datetime.utcnow() + timedelta(hours=24)
        }, app.config['SECRET_KEY'], algorithm="HS256")
        
        return jsonify({
            'token': token,
            'user': {
                'email': user['email'],
                'role': user['role'],
                'org_id': user['org_id']
            }
        })
        
    return make_response('Could not verify', 401, {'WWW-Authenticate': 'Basic realm="Login required!"'})

@app.route('/api/auth/me', methods=['GET'])
@token_required
def get_me(current_user):
    return jsonify(current_user)

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
        # 1. Clean up PostgreSQL if enabled
        unit = UnitStore.get_unit(unit_id)
        if unit and 'system_id' in unit:
            system_uuid = unit['system_id']
            conn = get_db_connection()
            if conn:
                try:
                    cur = conn.cursor()
                    # Delete metrics first due to FK
                    cur.execute("DELETE FROM system_metrics WHERE system_id IN (SELECT system_id FROM systems WHERE system_uuid = %s)", (system_uuid,))
                    cur.execute("DELETE FROM systems WHERE system_uuid = %s", (system_uuid,))
                    conn.commit()
                    cur.close()
                    conn.close()
                except Exception as e:
                    print(f"Error cleaning up PostgreSQL for unit {unit_id}: {e}")

        # 2. Clean up in-memory/JSON storage
        if USE_REDIS:
            redis_client.hdel('units', unit_id)
            redis_client.delete(f'usage:{unit_id}')
        else:
            if unit_id in units: 
                del units[unit_id]
                save_units_db() # Persist to disk
            if unit_id in unit_usage: del unit_usage[unit_id]

    @staticmethod
    def get_all_units(user=None):
        all_units = []
        if USE_REDIS:
            raw_units = redis_client.hgetall('units')
            all_units = [json.loads(u) for u in raw_units.values()]
        else:
            all_units = list(units.values())
            
        # Filter by Org if not ROOT
        if user and user.get('role') != 'ROOT':
            org_id = user.get('org_id')
            return [u for u in all_units if u.get('org_id') == org_id]
        return all_units

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
        # 1. Update In-Memory Cache for Real-time Graphs (last 100)
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

        # 2. Persist to PostgreSQL (Deep Storage)
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            
            # Resolve System ID (Upsert logic to ensure system exists)
            # Use unit_id as system_name (Short ID for URLs)
            # Use system_id as system_uuid (Full UUID for uniqueness/proper tracking)
            
            timestamp = usage_data.get('timestamp')
            if timestamp.endswith('Z'): timestamp = timestamp[:-1]
            
            # Extract metadata from payload
            sys_uuid = usage_data.get('system_id') 
            hostname = usage_data.get('hostname', 'unknown_host')
            
            cur.execute("""
                INSERT INTO systems (system_name, system_uuid, hostname, last_seen)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (system_name) DO UPDATE SET 
                    last_seen = EXCLUDED.last_seen,
                    system_uuid = COALESCE(EXCLUDED.system_uuid, systems.system_uuid),
                    hostname = EXCLUDED.hostname
                RETURNING system_id
            """, (unit_id, sys_uuid, hostname, timestamp))
            
            sys_int_id = cur.fetchone()[0]
            
            cpu = usage_data.get('cpu', usage_data.get('cpu_usage', 0))
            ram = usage_data.get('ram', usage_data.get('ram_usage', 0))
            gpu = 0
            if usage_data.get('gpu_load') is not None: gpu = usage_data.get('gpu_load')
            elif usage_data.get('gpu_usage') is not None: gpu = usage_data.get('gpu_usage')
            
            net_rx = usage_data.get('network_rx', 0)
            net_tx = usage_data.get('network_tx', 0)

            cur.execute("""
                INSERT INTO system_metrics 
                (system_id, timestamp, cpu_usage, ram_usage, gpu_usage, network_rx_mb, network_tx_mb)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING
            """, (sys_int_id, timestamp, cpu, ram, gpu, net_rx, net_tx))
            
            conn.commit()
            cur.close()
            conn.close()
        except Exception as e:
            print(f"Failed to write to DB: {e}")

    @staticmethod
    def get_usage(unit_id, limit=50):
        # Read from Postgres (Single Source of Truth)
        try:
            conn = get_db_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)
            
            # Get System ID
            cur.execute("SELECT system_id FROM systems WHERE system_name = %s", (unit_id,))
            res = cur.fetchone()
            if not res: return []
            sys_int_id = res['system_id']
            
            cur.execute("""
                SELECT timestamp, cpu_usage as cpu, ram_usage as ram, gpu_usage as gpu, network_rx_mb as network_rx, network_tx_mb as network_tx 
                FROM system_metrics 
                WHERE system_id = %s 
                ORDER BY timestamp DESC 
                LIMIT %s
            """, (sys_int_id, limit))
            
            rows = cur.fetchall()
            
            # Reverse to Chronological Order (Oldest -> Newest) for Graph
            rows.reverse()
            
            # Format dates to string if needed by frontend, or let JSON encoder handle it
            # Frontend likely expects 'timestamp' string in specific format?
            # Existing JSONL had 'timestamp': '2026-...'
            # DB returns datetime object.
            
            cleaned_rows = []
            for r in rows:
                r['timestamp'] = r['timestamp'].isoformat()
                # Ensure Decimals are floats for JSON serialization
                if r.get('cpu') is not None: r['cpu'] = float(r['cpu'])
                if r.get('ram') is not None: r['ram'] = float(r['ram'])
                if r.get('gpu') is not None: r['gpu'] = float(r['gpu'])
                if r.get('network_rx') is not None: r['network_rx'] = float(r['network_rx'])
                if r.get('network_tx') is not None: r['network_tx'] = float(r['network_tx'])
                cleaned_rows.append(r)
                
            cur.close()
            conn.close()
            return cleaned_rows
            
        except Exception as e:
            print(f"Error reading usage from DB: {e}")
            return []

# Strict CORS for production if needed, but for now allow all to fix frontend connection issues
CORS(app, resources={r"/*": {"origins": "*"}})
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
@token_required
def get_units_route(current_user):
    """Get all registered units (filtered by org)"""
    return jsonify(UnitStore.get_all_units(current_user))

@app.route('/api/orgs', methods=['GET'])
@token_required
def get_orgs(current_user):
    """Filter orgs list for ROOT admins only"""
    if current_user['role'] != 'ROOT':
        return jsonify({'error': 'Unauthorized'}), 403
    return jsonify(UnitStore.get_unique_orgs())

@app.route('/api/orgs/<org_id>/units', methods=['GET'])
@token_required
def get_org_units(current_user, org_id):
    """Get units for a specific org (ROOT or Org Admin check)"""
    if current_user['role'] != 'ROOT' and current_user['org_id'] != org_id:
        return jsonify({'error': 'Unauthorized'}), 403
    units = UnitStore.get_units_by_org(org_id)
    return jsonify(units)

@app.route('/api/units/<unit_id>/usage', methods=['GET'])
@token_required
def get_unit_usage(current_user, unit_id):
    """Get usage for a unit, with strict org-based access control"""
    all_units = UnitStore.get_all_units()
    target_unit = next((u for u in all_units if u['id'] == unit_id), None)
    
    if not target_unit:
        return jsonify({'error': 'Unit not found'}), 404
        
    # Security check: User must be ROOT or belong to the same organization
    if current_user['role'] != 'ROOT' and current_user['org_id'] != target_unit.get('org_id'):
        return jsonify({'error': 'Unauthorized: This unit does not belong to your organization'}), 403
        
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
    
    if 'comp_id' in data: 
        unit['comp_id'] = data['comp_id']
        unit['name'] = f"{unit.get('org_id', 'unknown')}/{data['comp_id']}"
    if 'org_id' in data: 
        unit['org_id'] = data['org_id']
        unit['name'] = f"{data['org_id']}/{unit.get('comp_id', 'unknown')}"
    if 'name' in data: unit['name'] = data['name']
    
    UnitStore.save_unit(unit_id, unit)
    
    # Broadcast to all so sidebar updates immediately
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
            # Logic to handle machine renames or org moves
            if existing_unit.get('org_id') != org_id or existing_unit.get('comp_id') != comp_id:
                print(f"Unit {unit_id} identity updated: {existing_unit.get('org_id')}/{existing_unit.get('comp_id')} -> {org_id}/{comp_id}")
                existing_unit['org_id'] = org_id
                existing_unit['comp_id'] = comp_id
                existing_unit['name'] = f"{org_id}/{comp_id}"

            existing_unit['last_seen'] = datetime.now().isoformat()
            existing_unit['status'] = 'online'
            existing_unit['ip'] = request.remote_addr
            
            if hostname != 'Unknown': existing_unit['hostname'] = hostname
            if os_info != 'Unknown': existing_unit['os_info'] = os_info
            if cpu_info != 'Unknown': existing_unit['cpu_info'] = cpu_info
            if ram_total > 0: existing_unit['ram_total'] = ram_total
            if gpu_info != '{}': existing_unit['gpu_info'] = gpu_info
            if network_interfaces != '{}': existing_unit['network_interfaces'] = network_interfaces
            
            UnitStore.save_unit(unit_id, existing_unit)
            
            # Broadcast update because identities might have changed
            socketio.emit('units_update', UnitStore.get_all_units())
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
    # DEBUG: Print incoming data to console
    print(f"Received Data: {data}")
    
    if not data or 'unit_id' not in data:
        return False, 'unit_id required'

    unit_id = data['unit_id']
    org_id = data.get('org_id')
    unit = UnitStore.get_unit(unit_id)
    
    if not unit:
        return False, 'Unit not registered'

    unit['last_seen'] = datetime.now().isoformat()
    unit['status'] = 'online'
    
    # Update metadata if it has changed (e.g. rename or org move)
    changed = False
    if 'org_id' in data and data['org_id'] != unit.get('org_id'):
        unit['org_id'] = data['org_id']
        changed = True
    if 'comp_id' in data and data['comp_id'] != unit.get('comp_id'):
        unit['comp_id'] = data['comp_id']
        unit['name'] = f"{unit.get('org_id', 'unknown')}/{data['comp_id']}"
        changed = True
    
    if 'hostname' in data: unit['hostname'] = data['hostname']
    unit['ip'] = request.remote_addr

    UnitStore.save_unit(unit_id, unit)
    if changed:
        socketio.emit('units_update', UnitStore.get_all_units())
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
        # DB Connection
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # 1. Resolve System ID
        cur.execute("SELECT system_id FROM systems WHERE system_name = %s", (unit_id,))
        res = cur.fetchone()
        if not res:
             return jsonify({'error': 'No data found for this unit'}), 404
        sys_int_id = res['system_id']

        # 2. Check for custom date range
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        
        filter_start = None
        filter_end = None
        filename_dates = ""
        
        query = "SELECT * FROM system_metrics WHERE system_id = %s "
        params = [sys_int_id]

        if start_date_str and end_date_str:
            try:
                # Parse YYYY-MM-DD
                filter_start = datetime.strptime(start_date_str, '%Y-%m-%d')
                # Set end date to end of that day (23:59:59)
                filter_end = datetime.strptime(end_date_str, '%Y-%m-%d') + timedelta(days=1, seconds=-1)
                
                query += "AND timestamp >= %s AND timestamp <= %s "
                params.extend([filter_start, filter_end])
                filename_dates = f"{start_date_str}_to_{end_date_str}"
            except ValueError:
                return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
        else:
            # 2. Fallback to relative range
            time_range = request.args.get('range', '1d')
            days = 1
            if time_range == '5d': days = 5
            elif time_range == '10d': days = 10
            elif time_range == 'all': days = 3650
            
            filter_start = datetime.now() - timedelta(days=days)
            query += "AND timestamp >= %s "
            params.append(filter_start)
            filename_dates = time_range
            
        query += "ORDER BY timestamp ASC"

        cur.execute(query, tuple(params))
        rows = cur.fetchall()

        si = io.StringIO()
        cw = csv.writer(si)
        cw.writerow(['Timestamp', 'CPU (%)', 'RAM (%)', 'GPU Load (%)', 'Network RX (MB)', 'Network TX (MB)'])
        
        for r in rows:
            # Convert timestamp to local string if needed, DB returns datetime obj
            ts_str = r['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
            cw.writerow([
                ts_str,
                r['cpu_usage'],
                r['ram_usage'],
                r['gpu_usage'],
                r['network_rx_mb'],
                r['network_tx_mb']
            ])

        cur.close()
        conn.close()

        output = make_response(si.getvalue())
        output.headers["Content-Disposition"] = f"attachment; filename={unit_id}_usage_{filename_dates}.csv"
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
    socketio.run(app, host='0.0.0.0', port=5010, debug=True, allow_unsafe_werkzeug=True)