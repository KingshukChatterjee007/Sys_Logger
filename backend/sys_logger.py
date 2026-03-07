import psutil
import logging
import os
import sys
import time
import atexit
import signal
import json
import shutil
import zipfile
import tempfile
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from functools import wraps
from datetime import datetime, timedelta
import requests
import socket
import threading
import uuid
import pickle
import csv
import io
import jwt
import psycopg2
from psycopg2.extras import RealDictCursor
from werkzeug.security import generate_password_hash, check_password_hash
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

# DB Config
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASS = os.getenv('DB_PASS', 'postgres')
DB_NAME = 'sys_logger'

# Auth Config
JWT_SECRET = os.getenv('JWT_SECRET', 'syslogger-default-secret-change-me')
JWT_EXPIRATION_HOURS = int(os.getenv('JWT_EXPIRATION_HOURS', '24'))

# SMTP Config
SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
SMTP_USER = os.getenv('SMTP_USER', '')
SMTP_PASS = os.getenv('SMTP_PASS', '')
SMTP_FROM = os.getenv('SMTP_FROM', SMTP_USER)

# Tier definitions
TIERS = {
    'individual': {'name': 'Individual', 'max_nodes': 1, 'price_label': 'Free / Basic'},
    'business':   {'name': 'Business',   'max_nodes': 2, 'price_label': 'Contact Sales'},
}

def get_db_connection():
    conn = psycopg2.connect(host=DB_HOST, user=DB_USER, password=DB_PASS, dbname=DB_NAME)
    return conn

# ============================================================
# AUTH SEED DATA (tables created by database_schema.sql)
# ============================================================
def seed_auth_data():
    """Seed default admin user and NIELIT-BBSR org. Tables must already exist via database_schema.sql."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Check that auth tables exist (schema must have been applied)
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables WHERE table_name = 'users'
            ) AND EXISTS (
                SELECT FROM information_schema.tables WHERE table_name = 'organizations'
            )
        """)
        if not cur.fetchone()[0]:
            print("[AUTH] Tables 'users' and 'organizations' not found. Run database_schema.sql first!")
            cur.close()
            conn.close()
            return

        # Seed: Admin user (admin / admin123 — CHANGE IN PRODUCTION)
        cur.execute("SELECT 1 FROM users WHERE username = 'admin'")
        if not cur.fetchone():
            cur.execute("""
                INSERT INTO users (username, email, password_hash, role)
                VALUES (%s, %s, %s, 'admin')
            """, ('admin', 'admin@syslogger.local', generate_password_hash('admin123')))
            print("[AUTH] Default admin user created (admin / admin123)")

        # Seed: NIELIT-BBSR organization + org user
        cur.execute("SELECT org_id FROM organizations WHERE slug = 'NIELIT-BBSR'")
        row = cur.fetchone()
        if not row:
            cur.execute("""
                INSERT INTO organizations (name, slug, tier, node_limit, contact_email, next_payment_date)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING org_id
            """, ('NIELIT Bhubaneswar', 'NIELIT-BBSR', 'business', 2, 'nielit@example.com',
                  (datetime.now() + timedelta(days=30)).date()))
            org_id = cur.fetchone()[0]

            cur.execute("""
                INSERT INTO users (username, email, password_hash, role, org_id)
                VALUES (%s, %s, %s, 'org', %s)
            """, ('nielit', 'nielit@example.com', generate_password_hash('nielit123'), org_id))
            print("[AUTH] NIELIT-BBSR org + user created (nielit / nielit123)")

        conn.commit()
        cur.close()
        conn.close()
        print("[AUTH] Auth seed data initialized.")
    except Exception as e:
        print(f"[AUTH] Error seeding auth data: {e}")

# Run at import time
seed_auth_data()

# ============================================================
# JWT HELPERS & AUTH DECORATOR
# ============================================================
def create_token(user_dict):
    payload = {
        'user_id': user_dict['user_id'],
        'username': user_dict['username'],
        'role': user_dict['role'],
        'org_id': user_dict.get('org_id'),
        'exp': datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm='HS256')

def decode_token(token):
    return jwt.decode(token, JWT_SECRET, algorithms=['HS256'])

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            token = auth_header[7:]
        if not token:
            return jsonify({'error': 'Token required'}), 401
        try:
            data = decode_token(token)
            request.current_user = data
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            token = auth_header[7:]
        if not token:
            return jsonify({'error': 'Token required'}), 401
        try:
            data = decode_token(token)
            if data.get('role') != 'admin':
                return jsonify({'error': 'Admin access required'}), 403
            request.current_user = data
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401
        return f(*args, **kwargs)
    return decorated

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

# ============================================================
# AUTH ROUTES
# ============================================================

@app.route('/api/auth/login', methods=['POST'])
def auth_login():
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '')
    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400

    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT * FROM users WHERE username = %s AND is_active = TRUE", (username,))
        user = cur.fetchone()
        cur.close()
        conn.close()

        if not user or not check_password_hash(user['password_hash'], password):
            return jsonify({'error': 'Invalid credentials'}), 401

        # Get org slug if org user
        org_slug = None
        org_name = None
        if user['role'] == 'org' and user['org_id']:
            conn2 = get_db_connection()
            cur2 = conn2.cursor(cursor_factory=RealDictCursor)
            cur2.execute("SELECT slug, name FROM organizations WHERE org_id = %s", (user['org_id'],))
            org = cur2.fetchone()
            cur2.close()
            conn2.close()
            if org:
                org_slug = org['slug']
                org_name = org['name']

        token = create_token(dict(user))
        return jsonify({
            'token': token,
            'user': {
                'user_id': user['user_id'],
                'username': user['username'],
                'role': user['role'],
                'org_id': user['org_id'],
                'org_slug': org_slug,
                'org_name': org_name,
            }
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/auth/me', methods=['GET'])
@token_required
def auth_me():
    user = request.current_user
    org_slug = None
    org_name = None
    tier = None
    if user.get('role') == 'org' and user.get('org_id'):
        try:
            conn = get_db_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute("SELECT slug, name, tier FROM organizations WHERE org_id = %s", (user['org_id'],))
            org = cur.fetchone()
            cur.close()
            conn.close()
            if org:
                org_slug = org['slug']
                org_name = org['name']
                tier = org['tier']
        except: pass
    return jsonify({
        'user_id': user['user_id'],
        'username': user['username'],
        'role': user['role'],
        'org_id': user.get('org_id'),
        'org_slug': org_slug,
        'org_name': org_name,
        'tier': tier,
    }), 200

@app.route('/api/auth/forgot-password', methods=['POST'])
def auth_forgot_password():
    data = request.get_json()
    email = data.get('email', '').strip()
    if not email:
        return jsonify({'error': 'Email required'}), 400
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT * FROM users WHERE email = %s AND is_active = TRUE", (email,))
        user = cur.fetchone()
        cur.close()
        conn.close()
        if not user:
            return jsonify({'message': 'If an account with that email exists, a reset link has been sent.'}), 200

        reset_payload = {
            'user_id': user['user_id'],
            'purpose': 'password_reset',
            'exp': datetime.utcnow() + timedelta(hours=1)
        }
        reset_token = jwt.encode(reset_payload, JWT_SECRET, algorithm='HS256')
        frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:3000')
        reset_link = f"{frontend_url}/reset-password?token={reset_token}"

        if SMTP_USER and SMTP_PASS:
            msg = MIMEMultipart()
            msg['From'] = SMTP_FROM
            msg['To'] = email
            msg['Subject'] = 'Sys_Logger Password Reset'
            body = f"Hello {user['username']},\n\nClick the link below to reset your password:\n{reset_link}\n\nThis link expires in 1 hour.\n\n— Sys_Logger Team"
            msg.attach(MIMEText(body, 'plain'))
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.starttls()
                server.login(SMTP_USER, SMTP_PASS)
                server.send_message(msg)
            print(f"[AUTH] Password reset email sent to {email}")
        else:
            print(f"[AUTH] SMTP not configured. Reset link: {reset_link}")

        return jsonify({'message': 'If an account with that email exists, a reset link has been sent.'}), 200
    except Exception as e:
        print(f"[AUTH] Forgot password error: {e}")
        return jsonify({'error': 'Failed to process request'}), 500

@app.route('/api/auth/reset-password', methods=['POST'])
def auth_reset_password():
    data = request.get_json()
    token_val = data.get('token', '')
    new_password = data.get('password', '')
    if not token_val or not new_password:
        return jsonify({'error': 'Token and new password required'}), 400
    try:
        payload = jwt.decode(token_val, JWT_SECRET, algorithms=['HS256'])
        if payload.get('purpose') != 'password_reset':
            return jsonify({'error': 'Invalid token'}), 400
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("UPDATE users SET password_hash = %s WHERE user_id = %s",
                    (generate_password_hash(new_password), payload['user_id']))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'message': 'Password updated successfully'}), 200
    except jwt.ExpiredSignatureError:
        return jsonify({'error': 'Reset link expired'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================
# ADMIN DASHBOARD
# ============================================================

@app.route('/api/admin/dashboard', methods=['GET'])
@admin_required
def admin_dashboard():
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT COUNT(*) as total FROM organizations WHERE is_active = TRUE")
        total_orgs = cur.fetchone()['total']
        cur.execute("SELECT COUNT(*) as total FROM users WHERE is_active = TRUE AND role = 'org'")
        total_org_users = cur.fetchone()['total']

        all_units = UnitStore.get_all_units()
        total_nodes = len(all_units)
        online_nodes = len([u for u in all_units if u.get('status') == 'online'])

        cur.execute("""
            SELECT o.*,
                   (SELECT COUNT(*) FROM users u WHERE u.org_id = o.org_id AND u.is_active = TRUE) as user_count
            FROM organizations o WHERE o.is_active = TRUE
            ORDER BY o.created_at DESC
        """)
        orgs = cur.fetchall()
        for org in orgs:
            org['created_at'] = org['created_at'].isoformat() if org.get('created_at') else None
            org['next_payment_date'] = org['next_payment_date'].isoformat() if org.get('next_payment_date') else None
            org_units = [u for u in all_units if u.get('org_id') == org['slug']]
            org['node_count'] = len(org_units)
            org['online_nodes'] = len([u for u in org_units if u.get('status') == 'online'])

        upcoming_payments = [o for o in orgs if o.get('next_payment_date') and
                            datetime.fromisoformat(o['next_payment_date']).date() <= (datetime.now() + timedelta(days=7)).date()]
        cur.close()
        conn.close()

        return jsonify({
            'total_orgs': total_orgs,
            'total_org_users': total_org_users,
            'total_nodes': total_nodes,
            'online_nodes': online_nodes,
            'organizations': orgs,
            'upcoming_payments': len(upcoming_payments),
            'server_stats': latest_server_stats,
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/orgs', methods=['GET'])
@admin_required
def admin_list_orgs():
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT * FROM organizations ORDER BY created_at DESC")
        orgs = cur.fetchall()
        for org in orgs:
            org['created_at'] = org['created_at'].isoformat() if org.get('created_at') else None
            org['next_payment_date'] = org['next_payment_date'].isoformat() if org.get('next_payment_date') else None
        cur.close()
        conn.close()
        return jsonify(orgs), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/register-org', methods=['POST'])
@admin_required
def admin_register_org():
    """Admin endpoint to register a new organization and its user account."""
    data = request.get_json()
    org_name = data.get('name', '').strip()
    org_slug = data.get('slug', '').strip()
    tier = data.get('tier', 'individual')
    contact_email = data.get('contact_email', '').strip()
    username = data.get('username', '').strip()
    password = data.get('password', '')

    if not org_name or not org_slug or not username or not password:
        return jsonify({'error': 'name, slug, username, and password are required'}), 400
    if tier not in TIERS:
        return jsonify({'error': f"Invalid tier. Choose from: {list(TIERS.keys())}"}), 400

    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        # Check existing
        cur.execute("SELECT 1 FROM organizations WHERE slug = %s OR name = %s", (org_slug, org_name))
        if cur.fetchone():
            cur.close(); conn.close()
            return jsonify({'error': 'Organization name or slug already exists'}), 409

        cur.execute("SELECT 1 FROM users WHERE username = %s", (username,))
        if cur.fetchone():
            cur.close(); conn.close()
            return jsonify({'error': 'Username already taken'}), 409

        node_limit = TIERS[tier]['max_nodes']
        cur.execute("""
            INSERT INTO organizations (name, slug, tier, node_limit, contact_email, next_payment_date)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING org_id
        """, (org_name, org_slug, tier, node_limit, contact_email,
              (datetime.now() + timedelta(days=30)).date()))
        org_id = cur.fetchone()['org_id']

        cur.execute("""
            INSERT INTO users (username, email, password_hash, role, org_id)
            VALUES (%s, %s, %s, 'org', %s)
        """, (username, contact_email, generate_password_hash(password), org_id))

        conn.commit()
        cur.close()
        conn.close()
        print(f"[AUTH] Org '{org_slug}' registered with user '{username}'")
        return jsonify({
            'message': f"Organization '{org_name}' created with user '{username}'",
            'org_id': org_id,
            'slug': org_slug,
            'tier': tier,
            'node_limit': node_limit,
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================
# ORG DASHBOARD & NODE MANAGEMENT
# ============================================================

@app.route('/api/org/dashboard', methods=['GET'])
@token_required
def org_dashboard():
    user = request.current_user
    org_id_param = user.get('org_id')
    if not org_id_param:
        return jsonify({'error': 'No organization linked'}), 400
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT * FROM organizations WHERE org_id = %s", (org_id_param,))
        org = cur.fetchone()
        cur.close()
        conn.close()
        if not org:
            return jsonify({'error': 'Organization not found'}), 404

        org['created_at'] = org['created_at'].isoformat() if org.get('created_at') else None
        org['next_payment_date'] = org['next_payment_date'].isoformat() if org.get('next_payment_date') else None

        all_units = UnitStore.get_all_units()
        org_units = [u for u in all_units if u.get('org_id') == org['slug']]

        return jsonify({
            'organization': org,
            'tier_info': TIERS.get(org['tier'], TIERS['individual']),
            'nodes': org_units,
            'total_nodes': len(org_units),
            'online_nodes': len([u for u in org_units if u.get('status') == 'online']),
            'node_limit': org['node_limit'],
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/org/nodes', methods=['GET'])
@token_required
def org_nodes():
    user = request.current_user
    org_id_param = user.get('org_id')
    if user.get('role') == 'admin':
        org_slug = request.args.get('org_slug')
        if org_slug:
            all_units = UnitStore.get_all_units()
            return jsonify([u for u in all_units if u.get('org_id') == org_slug]), 200
        return jsonify(UnitStore.get_all_units()), 200
    if not org_id_param:
        return jsonify({'error': 'No organization linked'}), 400
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT slug, node_limit FROM organizations WHERE org_id = %s", (org_id_param,))
        org = cur.fetchone()
        cur.close()
        conn.close()
        if not org:
            return jsonify([]), 200
        all_units = UnitStore.get_all_units()
        return jsonify([u for u in all_units if u.get('org_id') == org['slug']]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/org/nodes/add', methods=['POST'])
@token_required
def org_add_node():
    """Add a new node for the org. Checks tier limit."""
    user = request.current_user
    org_id_param = user.get('org_id')
    if user.get('role') == 'admin':
        org_id_param = request.get_json().get('org_db_id', org_id_param)
    if not org_id_param:
        return jsonify({'error': 'No organization linked'}), 400

    data = request.get_json()
    comp_id = data.get('comp_id', '').strip()
    if not comp_id:
        return jsonify({'error': 'Node name (comp_id) is required'}), 400

    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT slug, node_limit, tier FROM organizations WHERE org_id = %s", (org_id_param,))
        org = cur.fetchone()
        cur.close()
        conn.close()
        if not org:
            return jsonify({'error': 'Organization not found'}), 404

        org_slug = org['slug']
        all_units = UnitStore.get_all_units()
        org_units = [u for u in all_units if u.get('org_id') == org_slug]

        if len(org_units) >= org['node_limit']:
            return jsonify({
                'error': f"Node limit reached ({org['node_limit']}). Upgrade your tier or request additional nodes.",
                'current': len(org_units),
                'limit': org['node_limit']
            }), 403

        for u in org_units:
            if u.get('comp_id') == comp_id:
                return jsonify({'error': f"A node named '{comp_id}' already exists in this organization."}), 409

        unit_id = str(uuid.uuid4())[:8]
        system_id = str(uuid.uuid4())
        unit = {
            'id': unit_id,
            'system_id': system_id,
            'org_id': org_slug,
            'comp_id': comp_id,
            'ip': 'pending',
            'name': f"{org_slug}/{comp_id}",
            'status': 'offline',
            'last_seen': datetime.now().isoformat(),
            'hostname': comp_id,
            'os_info': 'Pending first connect',
            'cpu_info': '',
            'ram_total': 0,
            'gpu_info': '{}',
            'network_interfaces': '{}',
            'alerts': []
        }
        UnitStore.save_unit(unit_id, unit)
        socketio.emit('units_update', UnitStore.get_all_units())

        return jsonify({
            'message': f"Node '{comp_id}' created.",
            'unit_id': unit_id,
            'system_id': system_id,
            'org_id': org_slug,
            'comp_id': comp_id,
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================
# CLIENT DEPLOY ZIP GENERATOR
# ============================================================

@app.route('/api/org/download-client', methods=['POST'])
@token_required
def download_client_zip():
    """Generate a pre-filled client deploy ZIP for a specific node."""
    data = request.get_json()
    org_slug = data.get('org_id', '')
    comp_id = data.get('comp_id', '')
    system_id = data.get('system_id', str(uuid.uuid4()))

    if not org_slug or not comp_id:
        return jsonify({'error': 'org_id and comp_id are required'}), 400

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    source_dir = os.path.join(project_root, 'client_deploy')
    if not os.path.isdir(source_dir):
        return jsonify({'error': 'client_deploy directory not found on server'}), 404

    try:
        tmpdir = tempfile.mkdtemp()
        inner_dir = os.path.join(tmpdir, 'SysLogger_Client', 'client_deploy')
        shutil.copytree(source_dir, inner_dir)

        server_url = request.host_url.rstrip('/')
        if os.getenv('BACKEND_URL'):
            server_url = os.getenv('BACKEND_URL').rstrip('/')

        config_path = os.path.join(inner_dir, 'unit_client_config.json')
        config = {
            'system_id': system_id,
            'server_url': server_url,
            'org_id': org_slug,
            'comp_id': comp_id,
            'auth_token': '',
            '_provisioned': True,
            '_provisioned_at': datetime.now().isoformat()
        }
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=4)

        zip_filename = f"SysLogger_Client_{org_slug}_{comp_id}.zip"
        zip_path = os.path.join(tmpdir, zip_filename)
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for root, dirs, files in os.walk(os.path.join(tmpdir, 'SysLogger_Client')):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, tmpdir)
                    zf.write(file_path, arcname)

        return send_file(zip_path, as_attachment=True, download_name=zip_filename,
                        mimetype='application/zip')
    except Exception as e:
        print(f"[DEPLOY] Error generating client zip: {e}")
        return jsonify({'error': str(e)}), 500

# ============================================================
# BILLING INFO
# ============================================================

@app.route('/api/billing/info', methods=['GET'])
@token_required
def billing_info():
    user = request.current_user
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        if user.get('role') == 'admin':
            cur.execute("""
                SELECT o.org_id, o.name, o.slug, o.tier, o.node_limit, o.next_payment_date, o.is_active, o.created_at
                FROM organizations o ORDER BY o.next_payment_date ASC NULLS LAST
            """)
            orgs = cur.fetchall()
            for o in orgs:
                o['created_at'] = o['created_at'].isoformat() if o.get('created_at') else None
                o['next_payment_date'] = o['next_payment_date'].isoformat() if o.get('next_payment_date') else None
            active_subs = len([o for o in orgs if o['is_active']])
            upcoming = [o for o in orgs if o.get('next_payment_date') and
                       datetime.fromisoformat(o['next_payment_date']).date() <= (datetime.now() + timedelta(days=7)).date()]
            cur.close()
            conn.close()
            return jsonify({
                'role': 'admin',
                'active_subscriptions': active_subs,
                'total_orgs': len(orgs),
                'upcoming_payments': len(upcoming),
                'upcoming_payment_orgs': upcoming,
                'all_orgs': orgs,
                'tiers': TIERS,
            }), 200
        else:
            org_id_param = user.get('org_id')
            if not org_id_param:
                return jsonify({'error': 'No organization linked'}), 400
            cur.execute("SELECT * FROM organizations WHERE org_id = %s", (org_id_param,))
            org = cur.fetchone()
            cur.close()
            conn.close()
            if not org:
                return jsonify({'error': 'Organization not found'}), 404
            org['created_at'] = org['created_at'].isoformat() if org.get('created_at') else None
            org['next_payment_date'] = org['next_payment_date'].isoformat() if org.get('next_payment_date') else None
            return jsonify({
                'role': 'org',
                'organization': org,
                'tier_info': TIERS.get(org['tier'], TIERS['individual']),
                'tiers': TIERS,
            }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/billing/switch-tier', methods=['POST'])
@token_required
def switch_tier():
    user = request.current_user
    data = request.get_json()
    new_tier = data.get('tier', '')
    if new_tier not in TIERS:
        return jsonify({'error': f"Invalid tier. Choose from: {list(TIERS.keys())}"}), 400
    org_id_param = user.get('org_id')
    if user.get('role') == 'admin':
        org_id_param = data.get('org_db_id', org_id_param)
    if not org_id_param:
        return jsonify({'error': 'No organization linked'}), 400
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        new_limit = TIERS[new_tier]['max_nodes']
        cur.execute("UPDATE organizations SET tier = %s, node_limit = %s WHERE org_id = %s",
                    (new_tier, new_limit, org_id_param))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'message': f"Tier switched to {TIERS[new_tier]['name']}", 'tier': new_tier, 'node_limit': new_limit}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


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

# ============================================================
# AUTH ROUTES
# ============================================================

@app.route('/api/auth/login', methods=['POST'])
def auth_login():
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '')
    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400

    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT * FROM users WHERE username = %s AND is_active = TRUE", (username,))
        user = cur.fetchone()
        cur.close()
        conn.close()

        if not user or not check_password_hash(user['password_hash'], password):
            return jsonify({'error': 'Invalid credentials'}), 401

        # Get org slug if org user
        org_slug = None
        org_name = None
        if user['role'] == 'org' and user['org_id']:
            conn2 = get_db_connection()
            cur2 = conn2.cursor(cursor_factory=RealDictCursor)
            cur2.execute("SELECT slug, name FROM organizations WHERE org_id = %s", (user['org_id'],))
            org = cur2.fetchone()
            cur2.close()
            conn2.close()
            if org:
                org_slug = org['slug']
                org_name = org['name']

        token = create_token(dict(user))
        return jsonify({
            'token': token,
            'user': {
                'user_id': user['user_id'],
                'username': user['username'],
                'role': user['role'],
                'org_id': user['org_id'],
                'org_slug': org_slug,
                'org_name': org_name,
            }
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/auth/me', methods=['GET'])
@token_required
def auth_me():
    user = request.current_user
    org_slug = None
    org_name = None
    tier = None
    if user.get('role') == 'org' and user.get('org_id'):
        try:
            conn = get_db_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute("SELECT slug, name, tier FROM organizations WHERE org_id = %s", (user['org_id'],))
            org = cur.fetchone()
            cur.close()
            conn.close()
            if org:
                org_slug = org['slug']
                org_name = org['name']
                tier = org['tier']
        except: pass
    return jsonify({
        'user_id': user['user_id'],
        'username': user['username'],
        'role': user['role'],
        'org_id': user.get('org_id'),
        'org_slug': org_slug,
        'org_name': org_name,
        'tier': tier,
    }), 200

@app.route('/api/auth/forgot-password', methods=['POST'])
def auth_forgot_password():
    data = request.get_json()
    email = data.get('email', '').strip()
    if not email:
        return jsonify({'error': 'Email required'}), 400

    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT * FROM users WHERE email = %s AND is_active = TRUE", (email,))
        user = cur.fetchone()
        cur.close()
        conn.close()

        if not user:
            # Don't reveal whether user exists
            return jsonify({'message': 'If an account with that email exists, a reset link has been sent.'}), 200

        # Generate reset token (short-lived: 1 hour)
        reset_payload = {
            'user_id': user['user_id'],
            'purpose': 'password_reset',
            'exp': datetime.utcnow() + timedelta(hours=1)
        }
        reset_token = jwt.encode(reset_payload, JWT_SECRET, algorithm='HS256')

        # Build reset link (frontend handles the reset page)
        frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:3000')
        reset_link = f"{frontend_url}/reset-password?token={reset_token}"

        # Send email
        if SMTP_USER and SMTP_PASS:
            msg = MIMEMultipart()
            msg['From'] = SMTP_FROM
            msg['To'] = email
            msg['Subject'] = 'Sys_Logger Password Reset'
            body = f"Hello {user['username']},\n\nClick the link below to reset your password:\n{reset_link}\n\nThis link expires in 1 hour.\n\n— Sys_Logger Team"
            msg.attach(MIMEText(body, 'plain'))

            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.starttls()
                server.login(SMTP_USER, SMTP_PASS)
                server.send_message(msg)
            print(f"[AUTH] Password reset email sent to {email}")
        else:
            print(f"[AUTH] SMTP not configured. Reset link: {reset_link}")

        return jsonify({'message': 'If an account with that email exists, a reset link has been sent.'}), 200
    except Exception as e:
        print(f"[AUTH] Forgot password error: {e}")
        return jsonify({'error': 'Failed to process request'}), 500

@app.route('/api/auth/reset-password', methods=['POST'])
def auth_reset_password():
    data = request.get_json()
    token = data.get('token', '')
    new_password = data.get('password', '')
    if not token or not new_password:
        return jsonify({'error': 'Token and new password required'}), 400
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
        if payload.get('purpose') != 'password_reset':
            return jsonify({'error': 'Invalid token'}), 400

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("UPDATE users SET password_hash = %s WHERE user_id = %s",
                    (generate_password_hash(new_password), payload['user_id']))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'message': 'Password updated successfully'}), 200
    except jwt.ExpiredSignatureError:
        return jsonify({'error': 'Reset link expired'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================
# ADMIN DASHBOARD
# ============================================================

@app.route('/api/admin/dashboard', methods=['GET'])
@admin_required
def admin_dashboard():
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        cur.execute("SELECT COUNT(*) as total FROM organizations WHERE is_active = TRUE")
        total_orgs = cur.fetchone()['total']

        cur.execute("SELECT COUNT(*) as total FROM users WHERE is_active = TRUE AND role = 'org'")
        total_org_users = cur.fetchone()['total']

        # Count total registered nodes from in-memory store
        all_units = UnitStore.get_all_units()
        total_nodes = len(all_units)
        online_nodes = len([u for u in all_units if u.get('status') == 'online'])

        # Orgs list with details
        cur.execute("""
            SELECT o.*, 
                   (SELECT COUNT(*) FROM users u WHERE u.org_id = o.org_id AND u.is_active = TRUE) as user_count
            FROM organizations o WHERE o.is_active = TRUE
            ORDER BY o.created_at DESC
        """)
        orgs = cur.fetchall()
        for org in orgs:
            org['created_at'] = org['created_at'].isoformat() if org.get('created_at') else None
            org['next_payment_date'] = org['next_payment_date'].isoformat() if org.get('next_payment_date') else None
            # Count nodes for this org
            org_units = [u for u in all_units if u.get('org_id') == org['slug']]
            org['node_count'] = len(org_units)
            org['online_nodes'] = len([u for u in org_units if u.get('status') == 'online'])

        # Billing summary
        upcoming_payments = [o for o in orgs if o.get('next_payment_date') and
                            datetime.fromisoformat(o['next_payment_date']).date() <= (datetime.now() + timedelta(days=7)).date()]

        cur.close()
        conn.close()

        return jsonify({
            'total_orgs': total_orgs,
            'total_org_users': total_org_users,
            'total_nodes': total_nodes,
            'online_nodes': online_nodes,
            'organizations': orgs,
            'upcoming_payments': len(upcoming_payments),
            'server_stats': latest_server_stats,
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/orgs', methods=['GET'])
@admin_required
def admin_list_orgs():
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT * FROM organizations ORDER BY created_at DESC")
        orgs = cur.fetchall()
        for org in orgs:
            org['created_at'] = org['created_at'].isoformat() if org.get('created_at') else None
            org['next_payment_date'] = org['next_payment_date'].isoformat() if org.get('next_payment_date') else None
        cur.close()
        conn.close()
        return jsonify(orgs), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================
# ORG DASHBOARD & NODE MANAGEMENT
# ============================================================

@app.route('/api/org/dashboard', methods=['GET'])
@token_required
def org_dashboard():
    user = request.current_user
    org_id_param = user.get('org_id')
    if not org_id_param:
        return jsonify({'error': 'No organization linked'}), 400
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT * FROM organizations WHERE org_id = %s", (org_id_param,))
        org = cur.fetchone()
        cur.close()
        conn.close()
        if not org:
            return jsonify({'error': 'Organization not found'}), 404

        org['created_at'] = org['created_at'].isoformat() if org.get('created_at') else None
        org['next_payment_date'] = org['next_payment_date'].isoformat() if org.get('next_payment_date') else None

        # Nodes for this org
        all_units = UnitStore.get_all_units()
        org_units = [u for u in all_units if u.get('org_id') == org['slug']]

        return jsonify({
            'organization': org,
            'tier_info': TIERS.get(org['tier'], TIERS['individual']),
            'nodes': org_units,
            'total_nodes': len(org_units),
            'online_nodes': len([u for u in org_units if u.get('status') == 'online']),
            'node_limit': org['node_limit'],
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/org/nodes', methods=['GET'])
@token_required
def org_nodes():
    user = request.current_user
    org_id_param = user.get('org_id')
    if user.get('role') == 'admin':
        org_slug = request.args.get('org_slug')
        if org_slug:
            all_units = UnitStore.get_all_units()
            return jsonify([u for u in all_units if u.get('org_id') == org_slug]), 200
        return jsonify(UnitStore.get_all_units()), 200

    if not org_id_param:
        return jsonify({'error': 'No organization linked'}), 400
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT slug, node_limit FROM organizations WHERE org_id = %s", (org_id_param,))
        org = cur.fetchone()
        cur.close()
        conn.close()
        if not org:
            return jsonify([]), 200
        all_units = UnitStore.get_all_units()
        org_units = [u for u in all_units if u.get('org_id') == org['slug']]
        return jsonify(org_units), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/org/nodes/add', methods=['POST'])
@token_required
def org_add_node():
    """Add a new node for the org. Checks tier limit. Returns node info for client installer."""
    user = request.current_user
    org_id_param = user.get('org_id')
    if user.get('role') == 'admin':
        # Admin can add for any org by passing org_db_id
        org_id_param = request.get_json().get('org_db_id', org_id_param)
    if not org_id_param:
        return jsonify({'error': 'No organization linked'}), 400

    data = request.get_json()
    comp_id = data.get('comp_id', '').strip()
    if not comp_id:
        return jsonify({'error': 'Node name (comp_id) is required'}), 400

    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT slug, node_limit, tier FROM organizations WHERE org_id = %s", (org_id_param,))
        org = cur.fetchone()
        cur.close()
        conn.close()
        if not org:
            return jsonify({'error': 'Organization not found'}), 404

        org_slug = org['slug']
        all_units = UnitStore.get_all_units()
        org_units = [u for u in all_units if u.get('org_id') == org_slug]

        if len(org_units) >= org['node_limit']:
            return jsonify({
                'error': f"Node limit reached ({org['node_limit']}). Upgrade your tier or request additional nodes.",
                'current': len(org_units),
                'limit': org['node_limit']
            }), 403

        # Check duplicate comp_id for this org
        for u in org_units:
            if u.get('comp_id') == comp_id:
                return jsonify({'error': f"A node named '{comp_id}' already exists in this organization."}), 409

        # Pre-register the node (it will update on first client heartbeat)
        unit_id = str(uuid.uuid4())[:8]
        system_id = str(uuid.uuid4())
        unit = {
            'id': unit_id,
            'system_id': system_id,
            'org_id': org_slug,
            'comp_id': comp_id,
            'ip': 'pending',
            'name': f"{org_slug}/{comp_id}",
            'status': 'offline',
            'last_seen': datetime.now().isoformat(),
            'hostname': comp_id,
            'os_info': 'Pending first connect',
            'cpu_info': '',
            'ram_total': 0,
            'gpu_info': '{}',
            'network_interfaces': '{}',
            'alerts': []
        }
        UnitStore.save_unit(unit_id, unit)

        socketio.emit('units_update', UnitStore.get_all_units())

        return jsonify({
            'message': f"Node '{comp_id}' created.",
            'unit_id': unit_id,
            'system_id': system_id,
            'org_id': org_slug,
            'comp_id': comp_id,
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================
# CLIENT DEPLOY ZIP GENERATOR
# ============================================================

@app.route('/api/org/download-client', methods=['POST'])
@token_required
def download_client_zip():
    """Generate a pre-filled client deploy ZIP for a specific node."""
    user = request.current_user
    data = request.get_json()
    org_slug = data.get('org_id', '')
    comp_id = data.get('comp_id', '')
    system_id = data.get('system_id', str(uuid.uuid4()))

    if not org_slug or not comp_id:
        return jsonify({'error': 'org_id and comp_id are required'}), 400

    # Path to client_deploy source
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    source_dir = os.path.join(project_root, 'client_deploy')
    if not os.path.isdir(source_dir):
        return jsonify({'error': 'client_deploy directory not found on server'}), 404

    try:
        tmpdir = tempfile.mkdtemp()
        # Nest inside SysLogger_Client/client_deploy/
        inner_dir = os.path.join(tmpdir, 'SysLogger_Client', 'client_deploy')
        shutil.copytree(source_dir, inner_dir)

        # Determine server URL
        server_url = request.host_url.rstrip('/')
        frontend_origin = request.headers.get('Origin', '')
        # Use the backend URL that the client will connect to
        if os.getenv('BACKEND_URL'):
            server_url = os.getenv('BACKEND_URL').rstrip('/')

        # Overwrite config
        config_path = os.path.join(inner_dir, 'unit_client_config.json')
        config = {
            'system_id': system_id,
            'server_url': server_url,
            'org_id': org_slug,
            'comp_id': comp_id,
            'auth_token': '',
            '_provisioned': True,
            '_provisioned_at': datetime.now().isoformat()
        }
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=4)

        # Create zip
        zip_filename = f"SysLogger_Client_{org_slug}_{comp_id}.zip"
        zip_path = os.path.join(tmpdir, zip_filename)
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for root, dirs, files in os.walk(os.path.join(tmpdir, 'SysLogger_Client')):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, tmpdir)
                    zf.write(file_path, arcname)

        return send_file(zip_path, as_attachment=True, download_name=zip_filename,
                        mimetype='application/zip')
    except Exception as e:
        print(f"[DEPLOY] Error generating client zip: {e}")
        return jsonify({'error': str(e)}), 500

# ============================================================
# BILLING INFO
# ============================================================

@app.route('/api/billing/info', methods=['GET'])
@token_required
def billing_info():
    user = request.current_user
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        if user.get('role') == 'admin':
            # Admin sees all orgs billing
            cur.execute("""
                SELECT o.org_id, o.name, o.slug, o.tier, o.node_limit, o.next_payment_date, o.is_active, o.created_at
                FROM organizations o ORDER BY o.next_payment_date ASC NULLS LAST
            """)
            orgs = cur.fetchall()
            for o in orgs:
                o['created_at'] = o['created_at'].isoformat() if o.get('created_at') else None
                o['next_payment_date'] = o['next_payment_date'].isoformat() if o.get('next_payment_date') else None

            active_subs = len([o for o in orgs if o['is_active']])
            upcoming = [o for o in orgs if o.get('next_payment_date') and
                       datetime.fromisoformat(o['next_payment_date']).date() <= (datetime.now() + timedelta(days=7)).date()]

            cur.close()
            conn.close()
            return jsonify({
                'role': 'admin',
                'active_subscriptions': active_subs,
                'total_orgs': len(orgs),
                'upcoming_payments': len(upcoming),
                'upcoming_payment_orgs': upcoming,
                'all_orgs': orgs,
                'tiers': TIERS,
            }), 200
        else:
            # Org user sees their own billing
            org_id_param = user.get('org_id')
            if not org_id_param:
                return jsonify({'error': 'No organization linked'}), 400
            cur.execute("SELECT * FROM organizations WHERE org_id = %s", (org_id_param,))
            org = cur.fetchone()
            cur.close()
            conn.close()
            if not org:
                return jsonify({'error': 'Organization not found'}), 404

            org['created_at'] = org['created_at'].isoformat() if org.get('created_at') else None
            org['next_payment_date'] = org['next_payment_date'].isoformat() if org.get('next_payment_date') else None

            return jsonify({
                'role': 'org',
                'organization': org,
                'tier_info': TIERS.get(org['tier'], TIERS['individual']),
                'tiers': TIERS,
            }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/billing/switch-tier', methods=['POST'])
@token_required
def switch_tier():
    user = request.current_user
    data = request.get_json()
    new_tier = data.get('tier', '')
    if new_tier not in TIERS:
        return jsonify({'error': f"Invalid tier. Choose from: {list(TIERS.keys())}"}), 400

    org_id_param = user.get('org_id')
    if user.get('role') == 'admin':
        org_id_param = data.get('org_db_id', org_id_param)
    if not org_id_param:
        return jsonify({'error': 'No organization linked'}), 400

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        new_limit = TIERS[new_tier]['max_nodes']
        cur.execute("UPDATE organizations SET tier = %s, node_limit = %s WHERE org_id = %s",
                    (new_tier, new_limit, org_id_param))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'message': f"Tier switched to {TIERS[new_tier]['name']}", 'tier': new_tier, 'node_limit': new_limit}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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