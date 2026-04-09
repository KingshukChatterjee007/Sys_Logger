import psutil
import logging
import os
import sys
import re
import time
import atexit
import signal
import json
from datetime import datetime, timedelta, timezone
import requests
import socket
import threading
import uuid
import pickle
import csv
import io
import zipfile
import tempfile
import shutil
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
import razorpay
try:
    import GPUtil
    NVIDIA_AVAILABLE = True
except ImportError:
    NVIDIA_AVAILABLE = False
AMD_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler()]
)

# Load environment variables
if getattr(sys, 'frozen', False):
    bundle_dir = getattr(sys, '_MEIPASS', '.')
    env_path = os.path.join(bundle_dir, '.env')
    load_dotenv(env_path)
else:
    load_dotenv()

# Initialize Razorpay Client (Keys to be provided by user later)
RAZORPAY_KEY_ID = os.getenv('RAZORPAY_KEY_ID', 'rzp_test_placeholder')
RAZORPAY_KEY_SECRET = os.getenv('RAZORPAY_KEY_SECRET', 'secret_placeholder')
razorpay_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))

# Public URL for the agent to connect back to (useful for hosting/proxies)
# Defaults to request host during registration/installer generation
PUBLIC_SERVER_URL = os.getenv('PUBLIC_SERVER_URL', '')

# DB Config
DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_USER = os.getenv('DB_USER', 'postgres')
    DB_PASS = os.getenv('DB_PASS', 'postgres')
    DB_NAME = os.getenv('DB_NAME', 'sys_logger')
else:
    DB_HOST = DB_USER = DB_PASS = DB_NAME = None

def get_db_connection():
    try:
        if DATABASE_URL:
            conn = psycopg2.connect(DATABASE_URL)
        else:
            conn = psycopg2.connect(host=DB_HOST, user=DB_USER, password=DB_PASS, dbname=DB_NAME)
        return conn
    except psycopg2.OperationalError as e:
        logging.error(f"DATABASE CONNECTION FAILED: host={DB_HOST}, user={DB_USER}, db={DB_NAME}")
        logging.error(f"Error details: {e}")
        raise
    except Exception as e:
        logging.error(f"Unexpected DB error: {e}")
        raise

app = Flask(__name__)

# CORS Configuration — read allowed origins from env, fallback to allow-all for dev
cors_origins_env = os.getenv('CORS_ORIGINS', '*')
if cors_origins_env == '*':
    CORS(app)
else:
    allowed_origins = [o.strip() for o in cors_origins_env.split(',') if o.strip()]
    CORS(app, origins=allowed_origins, supports_credentials=True)

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'sys-logger-super-secret-key-32-chars-long-for-jwt')
from werkzeug.middleware.proxy_fix import ProxyFix
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
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
            # Try new long key first
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = data
        except Exception:
            try:
                # Fallback to old short key
                data = jwt.decode(token, 'sys-logger-super-secret-key', algorithms=["HS256"])
                current_user = data
            except Exception as e:
                return jsonify({'message': 'Token is invalid!', 'error': str(e)}), 401
            
        return f(current_user, *args, **kwargs)
    return decorated

DATA_DIR = 'unit_data'
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# Global data structures (Deprecated JSON storage)
# units = {}  # Removed to enforce SQL as source of truth
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
    email = data.get('email', '').lower()
    password = data.get('password')
    org_name = data.get('org_name')
    org_type = data.get('org_type') # 'Individual' or 'Business'
    
    if not email or not password or not org_name or not org_type:
        return jsonify({'message': 'Missing required fields!'}), 400
        
    def slugify(text):
        text = text.lower().strip()
        text = re.sub(r'[^\w\s-]', '', text)
        text = re.sub(r'[\s_-]+', '-', text)
        text = re.sub(r'^-+|-+$', '', text)
        return text

    slug = slugify(org_name)
    username = email.split('@')[0]
    
    # All new registrations start on INDIVIDUAL tier with 1 node limit
    tier = 'INDIVIDUAL'
    node_limit = 1
        
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # 1. Check if user exists
        cur.execute("SELECT * FROM users WHERE email = %s OR username = %s", (email, username))
        if cur.fetchone():
            return jsonify({'message': 'User or email already exists!'}), 400
            
        # 2. Create Organization
        # Check if slug exists, if so append unique suffix
        base_slug = slug
        counter = 1
        while True:
            cur.execute("SELECT * FROM organizations WHERE slug = %s", (slug,))
            if not cur.fetchone():
                break
            slug = f"{base_slug}-{counter}"
            counter += 1
            
        cur.execute(
            "INSERT INTO organizations (name, slug, tier, node_limit, contact_email) VALUES (%s, %s, %s, %s, %s) RETURNING org_id",
            (org_name, slug, tier, node_limit, email)
        )
        org_id = cur.fetchone()['org_id']
        
        # 3. Create User
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        cur.execute(
            "INSERT INTO users (username, email, password_hash, role, org_id) VALUES (%s, %s, %s, %s, %s)",
            (username, email, password_hash, 'ADMIN', org_id)
        )
        
        conn.commit()
    except Exception as e:
        conn.rollback()
        return jsonify({'message': f'Registration failed: {str(e)}'}), 500
    finally:
        cur.close()
        conn.close()
    
    return jsonify({'message': 'Account created successfully! You can now log in.'}), 201

@app.route('/api/units/download-installer', methods=['POST'])
@token_required
def download_installer(current_user):
    data = request.get_json()
    comp_id = data.get('comp_id')
    
    if not comp_id:
        return jsonify({'message': 'Component ID is required!'}), 400
        
    org_id = current_user.get('org_id')
    
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # 1. Check Tier Limits - now including tier and contact_email to avoid KeyError
        cur.execute("SELECT node_limit, tier, contact_email FROM organizations WHERE org_id = %s", (org_id,))
        org = cur.fetchone()
        if not org:
            return jsonify({'message': 'Organization not found!'}), 404
            
        # Use ::text cast because org_id is VARCHAR in the systems table
        cur.execute("SELECT COUNT(*) FROM systems WHERE org_id::text = %s::text", (str(org_id),))
        current_count = cur.fetchone()['count']
        
        if current_user.get('role') != 'ROOT':
            # 1a. Per-Organization Limit
            if current_count >= org['node_limit']:
                return jsonify({
                    'error': 'limit_reached',
                    'current_count': current_count,
                    'limit': org['node_limit'],
                    'message': f"Organization limit reached! Your tier allows {org['node_limit']} nodes. Upgrade to add more monitors."
                }), 403
            
            # 1b. Global Free Tier Check (Prevent multi-org free node loophole)
            if org['tier'].upper() == 'INDIVIDUAL' or org['tier'].upper() == 'FREE':
                contact_email = org.get('contact_email') or current_user.get('email')
                if contact_email:
                    cur.execute("""
                        SELECT COUNT(*) 
                        FROM systems s
                        JOIN organizations o ON s.org_id::text = o.org_id::text
                        WHERE o.contact_email = %s AND o.tier IN ('FREE', 'INDIVIDUAL')
                    """, (contact_email,))
                    global_free_count = cur.fetchone()['count']
                    
                    if global_free_count >= 1:
                        return jsonify({
                            'error': 'limit_reached',
                            'global_notice': True,
                            'message': "Global free node limit reached! You already have a free node in another organization. Upgrade to Business or Pro to add more monitors."
                        }), 403

        # 2. Package Installer
        # Create a temporary ZIP file
        temp_dir = tempfile.mkdtemp()
        zip_path = os.path.join(temp_dir, f"sys_logger_installer_{comp_id}.zip")
        
        # Correct path: client_deploy is in the project root, one level up from backend/
        deploy_src = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'client_deploy'))
        
        print(f"DEBUG: Generating installer. Source: {deploy_src}, Target: {zip_path}")
        
        if not os.path.exists(deploy_src):
             return jsonify({'message': f'Source directory not found: {deploy_src}'}), 500

        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add all files from client_deploy
            for root, dirs, files in os.walk(deploy_src):
                # Skip venv and logs
                if 'venv' in dirs: dirs.remove('venv')
                if 'logs' in dirs: dirs.remove('logs')
                
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, deploy_src)
                    # Wrap in a folder
                    zipf.write(file_path, os.path.join('sys_logger_installer', arcname))
            
            # Inject pre-filled config with one-time install_token
            install_token = str(uuid.uuid4())
            
            # Dynamically determine server URL
            # 1. Use environment variable if set (best for hosting/proxies)
            # 2. Fallback to browser's request URL
            server_url = PUBLIC_SERVER_URL or request.host_url.rstrip('/')
            
            # 3. Aggressive HTTPS force: If we are on the production domain via a proxy, force HTTPS
            if 'lab-monitoring.nielitbhubaneswar.in' in server_url:
                server_url = server_url.replace('http://', 'https://')
            
            config_data = {
                'system_id': str(uuid.uuid4()),
                'server_url': server_url,
                'org_id': str(org_id),
                'comp_id': comp_id,
                'install_token': install_token
            }
            zipf.writestr('sys_logger_installer/src/unit_client_config.json', json.dumps(config_data, indent=4))

        # 3. Create Node in Database (Pending State) with install_token
        name = f"{org_id}/{comp_id}"
        cur.execute("""
            INSERT INTO systems (system_name, org_id, install_token, created_at)
            VALUES (%s, %s, %s, NOW())
            ON CONFLICT (system_name) DO UPDATE SET
                org_id = EXCLUDED.org_id,
                install_token = EXCLUDED.install_token
        """, (name, org_id, install_token))
        conn.commit()

        print(f"DEBUG: Node created/verified as PENDING for {name}")
        sync_units_state(str(org_id))

        return send_file(
            zip_path,
            mimetype='application/zip',
            as_attachment=True,
            download_name=f"sys_logger_installer_{comp_id}.zip"
        )

    except Exception as e:
        print(f"ERROR generating installer: {str(e)}")
        return jsonify({'message': f'Failed to generate installer: {str(e)}'}), 500
    finally:
        cur.close()
        conn.close()

@app.route('/api/units/installer/<signed_token>', methods=['GET'])
def download_installer_signed(signed_token):
    """Public GET endpoint for downloading pre-configured installer via signed token"""
    try:
        # Note: JWT decode will verify the signature using SECRET_KEY
        data = jwt.decode(signed_token, app.config['SECRET_KEY'], algorithms=["HS256"])
        org_id = data.get('org_id')
        comp_id = data.get('comp_id')
        
        if not org_id or not comp_id:
            return jsonify({'message': 'Invalid token content!'}), 400
            
        if data.get('type') != 'installer_download':
            return jsonify({'message': 'Invalid token type!'}), 400

        # Create package (re-using logic from download_installer)
        temp_dir = tempfile.mkdtemp()
        zip_path = os.path.join(temp_dir, f"sys_logger_installer_{comp_id}.zip")
        deploy_src = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'client_deploy'))
        
        if not os.path.exists(deploy_src):
             return jsonify({'message': 'Source directory not found'}), 500

        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(deploy_src):
                if 'venv' in dirs: dirs.remove('venv')
                if 'logs' in dirs: dirs.remove('logs')
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, deploy_src)
                    zipf.write(file_path, os.path.join('sys_logger_installer', arcname))
            
            # Inject config into the src/ folder as expected by the updated setup scripts
            install_token = str(uuid.uuid4())
            config_data = {
                'system_id': str(uuid.uuid4()),
                'org_id': str(org_id),
                'comp_id': comp_id,
                'install_token': install_token
            }
            zipf.writestr('sys_logger_installer/src/unit_client_config.json', json.dumps(config_data, indent=4))

        # Register pending node
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        name = f"{org_id}/{comp_id}"
        cur.execute("""
            INSERT INTO systems (system_name, org_id, install_token, created_at)
            VALUES (%s, %s, %s, NOW())
            ON CONFLICT (system_name) DO UPDATE SET
                org_id = EXCLUDED.org_id,
                install_token = EXCLUDED.install_token
        """, (name, org_id, install_token))
        conn.commit()
        cur.close()
        conn.close()

        print(f"DEBUG: Node created/verified via SIGNED LINK for {name}")
        sync_units_state(str(org_id))

        return send_file(
            zip_path,
            mimetype='application/zip',
            as_attachment=True,
            download_name=f"sys_logger_installer_{comp_id}.zip"
        )
    except jwt.ExpiredSignatureError:
        return jsonify({'message': 'Download link has expired!'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'message': 'Invalid download link!'}), 401
    except Exception as e:
        print(f"ERROR downloading signed installer: {str(e)}")
        return jsonify({'message': f'Internal error: {str(e)}'}), 500

@app.route('/api/units/generate-link', methods=['POST'])
@token_required
def generate_installer_link(current_user):
    """Generate a short-lived (24h) signed download link"""
    data = request.get_json()
    comp_id = data.get('comp_id')
    
    if not comp_id:
        return jsonify({'message': 'Component ID is required!'}), 400
        
    org_id = current_user.get('org_id')
    
    token = jwt.encode({
        'org_id': org_id,
        'comp_id': comp_id,
        'type': 'installer_download',
        'exp': datetime.now(timezone.utc) + timedelta(hours=24)
    }, app.config['SECRET_KEY'], algorithm="HS256")
    
    host = request.host_url.rstrip('/')
    download_url = f"{host}/api/units/installer/{token}"
    
    return jsonify({'download_url': download_url})


@app.route('/api/auth/login', methods=['POST'])
def login():
    auth = request.get_json()
    if not auth or not auth.get('email') or not auth.get('password'):
        return make_response('Could not verify', 401)
    
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT u.*, o.tier 
        FROM users u 
        JOIN organizations o ON u.org_id = o.org_id 
        WHERE u.email = %s
    """, (auth.get('email', '').lower(),))
    user = cur.fetchone()
    cur.close()
    conn.close()
    
    if not user:
        return make_response('Could not verify', 401)
        
    if bcrypt.checkpw(auth.get('password').encode('utf-8'), user['password_hash'].encode('utf-8')):
        token = jwt.encode({
            'user_id': user['user_id'],
            'email': user['email'],
            'role': user['role'],
            'org_id': user['org_id'],
            'tier': user['tier'],
            'exp': datetime.now(timezone.utc) + timedelta(hours=24)
        }, app.config['SECRET_KEY'], algorithm="HS256")
        
        return jsonify({
            'token': token,
            'user': {
                'email': user['email'],
                'role': user['role'],
                'org_id': user['org_id'],
                'tier': user['tier']
            }
        })
        
    return make_response('Could not verify', 401)

@app.route('/api/auth/me', methods=['GET'])
@token_required
def get_me(current_user):
    return jsonify(current_user)

@app.route('/api/users', methods=['GET'])
@token_required
def get_users(current_user):
    """List users (ROOT sees all, ADMIN sees org only)"""
    if current_user['role'] not in ['ROOT', 'ADMIN']:
        return jsonify({'error': 'Unauthorized'}), 403
        
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        if current_user['role'] == 'ROOT':
            cur.execute("""
                SELECT u.user_id, u.username, u.email, u.role, o.name as org_name 
                FROM users u 
                LEFT JOIN organizations o ON u.org_id = o.org_id
                ORDER BY u.user_id DESC
            """)
        else:
            cur.execute("""
                SELECT u.user_id, u.username, u.email, u.role, o.name as org_name 
                FROM users u 
                LEFT JOIN organizations o ON u.org_id = o.org_id
                WHERE u.org_id::varchar = %s::varchar
                ORDER BY u.user_id DESC
            """, (current_user['org_id'],))
            
        users = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify(users)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/users', methods=['POST'])
@token_required
def create_user(current_user):
    """Create a new user (ROOT writes anywhere, ADMIN writes to own org)"""
    if current_user['role'] not in ['ROOT', 'ADMIN']:
        return jsonify({'error': 'Unauthorized'}), 403
        
    data = request.get_json()
    username = data.get('username')
    email = data.get('email', '').lower()
    password = data.get('password')
    role = data.get('role', 'USER')
    
    # If ADMIN, they can only create users in their own org
    if current_user['role'] == 'ADMIN':
        org_id = current_user['org_id']
    else:
        org_id = data.get('org_id')
    
    if not username or not email or not password:
        return jsonify({'error': 'Missing required fields (username, email, password)'}), 400
        
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Check if email exists
        cur.execute("SELECT 1 FROM users WHERE email = %s", (email,))
        if cur.fetchone():
            return jsonify({'error': f'User with email {email} already exists'}), 409

        # Check if username exists
        cur.execute("SELECT 1 FROM users WHERE username = %s", (username,))
        if cur.fetchone():
            return jsonify({'error': f'Username {username} is already taken'}), 409
            
        cur.execute(
            """INSERT INTO users (username, email, password_hash, role, org_id) 
               VALUES (%s, %s, %s, %s, %s) RETURNING user_id""", 
            (username, email, password_hash, role, org_id)
        )
        new_user = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({
            'message': 'User created successfully',
            'user_id': new_user['user_id'],
            'username': username,
            'email': email,
            'role': role
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# --- Database Schema Bootstrapping ---

def ensure_schema_ready():
    """Ensure required SQL functions (like partitioning) exist in the database"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # 1. Create Partitioning Function if missing
        cur.execute("""
            CREATE OR REPLACE FUNCTION create_system_metrics_partition(target_date DATE)
            RETURNS VOID AS $$
            DECLARE
                partition_name TEXT;
                start_date DATE;
                end_date DATE;
            BEGIN
                start_date := DATE_TRUNC('month', target_date);
                end_date := start_date + INTERVAL '1 month';
                partition_name :=
                    'system_metrics_y' || EXTRACT(YEAR FROM start_date) ||
                    'm' || LPAD(EXTRACT(MONTH FROM start_date)::TEXT, 2, '0');

                EXECUTE FORMAT(
                    'CREATE TABLE IF NOT EXISTS %I PARTITION OF system_metrics
                     FOR VALUES FROM (%L) TO (%L)',
                    partition_name, start_date, end_date
                );
            END;
            $$ LANGUAGE plpgsql;
        """)
        
        # 2. Pre-create current and next month partitions
        cur.execute("SELECT create_system_metrics_partition(CURRENT_DATE)")
        cur.execute("SELECT create_system_metrics_partition(CURRENT_DATE + INTERVAL '1 month')")
        
        conn.commit()
        cur.close()
        conn.close()
        logging.info("Database schema bootstrap complete (Partitions initialized)")
    except Exception as e:
        logging.error(f"Database bootstrap failed: {e}")

# Run bootstrap on startup
ensure_schema_ready()

class UnitStore:
    """Store for units and usage with PostgreSQL Persistence"""
    
    @staticmethod
    def _row_to_unit(row):
        """Convert a DB row to the frontend unit format"""
        if not row: return None
        
        last_seen = row['last_seen']
        db_status = row.get('status', 'pending')
        
        # Recalculate online/offline based on last_seen if it was previously online
        status = db_status
        if last_seen:
            now = datetime.now(timezone.utc).replace(tzinfo=last_seen.tzinfo) if last_seen.tzinfo else datetime.now(timezone.utc)
            if (now - last_seen).total_seconds() < 300:
                status = 'online'
            else:
                status = 'offline'
        elif db_status == 'online':
             # If it was marked online but no last_seen (unexpected), fallback to offline
             status = 'offline'

        return {
            'id': str(row['system_id']), 
            'system_id': str(row['system_uuid']) if row['system_uuid'] else row['system_name'],
            'org_id': row['org_id'],
            'org_name': row.get('org_display_name', 'Unknown'),
            'org_slug': row.get('org_slug', 'unknown'),
            'comp_id': row['system_name'].split('/')[-1] if '/' in row['system_name'] else row['system_name'],
            'name': row['system_name'],
            'status': status,
            'last_seen': last_seen.isoformat() if last_seen else None,
            'hostname': row['hostname'],
            'os_info': row['os'],
            'ram_total': float(row['ram_gb']) if row['ram_gb'] else 0,
            'ip': row['ip_address'],
            'metrics': {
                'cpu': float(row.get('cpu_usage', 0) or 0),
                'ram': float(row.get('ram_usage', 0) or 0),
                'gpu': float(row.get('gpu_usage', 0) or 0),
                'network_rx': float(row.get('network_rx_mb', 0) or 0),
                'network_tx': float(row.get('network_tx_mb', 0) or 0)
            } if row.get('cpu_usage') is not None else None,
            'alerts': [] 
        }

    @staticmethod
    def get_unit(unit_id):
        try:
            conn = get_db_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute("""
                SELECT s.*, o.name as org_display_name, o.slug as org_slug 
                FROM systems s 
                LEFT JOIN organizations o ON s.org_id::varchar = o.org_id::varchar 
                WHERE s.system_id = %s OR s.system_name = %s
            """, (unit_id, unit_id))
            row = cur.fetchone()
            cur.close()
            conn.close()
            return UnitStore._row_to_unit(row)
        except Exception as e:
            print(f"Error in UnitStore.get_unit: {e}")
            return None

    @staticmethod
    def get_unit_by_org_comp(org_id, comp_id):
        try:
            # Ensure org_id is an integer if possible
            try: org_id = int(org_id)
            except: return None

            conn = get_db_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)
            name = f"{org_id}/{comp_id}"
            cur.execute("""
                SELECT s.*, o.name as org_display_name, o.slug as org_slug 
                FROM systems s 
                LEFT JOIN organizations o ON s.org_id::varchar = o.org_id::varchar 
                WHERE s.org_id::varchar = %s::varchar AND (LOWER(s.system_name) = LOWER(%s) OR LOWER(s.system_name) = LOWER(%s))
            """, (org_id, name, comp_id))
            row = cur.fetchone()
            cur.close()
            conn.close()
            return UnitStore._row_to_unit(row)
        except Exception as e:
            print(f"Error in UnitStore.get_unit_by_org_comp: {e}")
            return None

    @staticmethod
    def save_unit(unit_id, unit_data):
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            
            # Robust org_id handling
            raw_org = unit_data.get('org_id')
            try:
                org_id = int(raw_org) if raw_org else None
            except:
                org_id = None # Default to None if not a valid integer/ID
                
            name = unit_data.get('name', f"{org_id or 'unknown'}/{unit_data.get('comp_id', unit_id)}")
            
            cur.execute("""
                INSERT INTO systems 
                (system_name, system_uuid, hostname, ip_address, os, ram_gb, org_id, last_seen, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (system_name) DO UPDATE SET
                    system_uuid = COALESCE(EXCLUDED.system_uuid, systems.system_uuid),
                    hostname = EXCLUDED.hostname,
                    ip_address = EXCLUDED.ip_address,
                    os = EXCLUDED.os,
                    ram_gb = EXCLUDED.ram_gb,
                    org_id = EXCLUDED.org_id,
                    last_seen = EXCLUDED.last_seen,
                    status = EXCLUDED.status
            """, (
                name,
                unit_data.get('system_id') if '-' in str(unit_data.get('system_id', '')) else None,
                unit_data.get('hostname', 'Unknown'),
                unit_data.get('ip'),
                unit_data.get('os_info'),
                unit_data.get('ram_total'),
                org_id,
                datetime.now(timezone.utc), # Always update last_seen to now for heartbeats/registration
                'online'        # Always force to online during save_unit (heartbeat/reg)
            ))
            conn.commit()
            cur.close()
            conn.close()
        except Exception as e:
            print(f"Error in UnitStore.save_unit: {e}")

    @staticmethod
    def delete_unit(unit_id):
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            # Delete metrics first due to FK
            cur.execute("DELETE FROM system_metrics WHERE system_id = %s OR system_id IN (SELECT system_id FROM systems WHERE system_name = %s)", (unit_id, unit_id))
            cur.execute("DELETE FROM systems WHERE system_id = %s OR system_name = %s", (unit_id, unit_id))
            conn.commit()
            cur.close()
            conn.close()
        except Exception as e:
            print(f"Error in UnitStore.delete_unit: {e}")

    @staticmethod
    def get_all_units(user=None):
        try:
            conn = get_db_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)
            
            query = """
                SELECT s.*, o.name as org_display_name, o.slug as org_slug,
                       m.cpu_usage, m.ram_usage, m.gpu_usage, m.network_rx_mb, m.network_tx_mb
                FROM systems s 
                LEFT JOIN organizations o ON s.org_id::varchar = o.org_id::varchar
                LEFT JOIN LATERAL (
                    SELECT cpu_usage, ram_usage, gpu_usage, network_rx_mb, network_tx_mb
                    FROM system_metrics
                    WHERE system_id = s.system_id
                    ORDER BY timestamp DESC
                    LIMIT 1
                ) m ON TRUE
            """
            params = []
            
            # STRICT SQL ISOLATION
            if user and user.get('role') != 'ROOT':
                org_id = user.get('org_id')
                if not org_id:
                    return []
                query += " WHERE s.org_id::varchar = %s::varchar"
                params.append(org_id)
                
            cur.execute(query, params)
            rows = cur.fetchall()
            cur.close()
            conn.close()
            return [UnitStore._row_to_unit(r) for r in rows]
        except Exception as e:
            print(f"Error in UnitStore.get_all_units: {e}")
            return []

    @staticmethod
    def get_unique_orgs():
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("SELECT DISTINCT org_id FROM systems WHERE org_id IS NOT NULL")
            rows = cur.fetchall()
            cur.close()
            conn.close()
            return sorted([r[0] for r in rows])
        except Exception as e:
            print(f"Error in UnitStore.get_unique_orgs: {e}")
            return []
            
    @staticmethod
    def get_units_by_org(org_id):
        return UnitStore.get_all_units(user={'role': 'USER', 'org_id': org_id})

    @staticmethod
    def add_usage(unit_id, usage_data):
        # 1. Update In-Memory Cache for Real-time Graphs (last 100)
        if unit_id not in unit_usage:
            unit_usage[unit_id] = []
        unit_usage[unit_id].append(usage_data)
        if len(unit_usage[unit_id]) > 100:
            unit_usage[unit_id] = unit_usage[unit_id][-100:]

        # 2. Persist to PostgreSQL (system_metrics table)
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            
            # Resolve System ID
            try:
                int(unit_id)
                cur.execute("SELECT system_id FROM systems WHERE system_id = %s OR system_name = %s LIMIT 1", (unit_id, unit_id))
            except (ValueError, TypeError):
                cur.execute("SELECT system_id FROM systems WHERE system_name = %s LIMIT 1", (unit_id,))

            res = cur.fetchone()
            if not res:
                print(f"Error: Unit {unit_id} not found in DB for usage reporting")
                cur.close()
                conn.close()
                return
            sys_int_id = res[0]

            timestamp = usage_data.get('timestamp')
            if not timestamp: 
                timestamp = datetime.now(timezone.utc)
            elif isinstance(timestamp, str):
                try:
                    # Handle ISO format from frontend/client
                    timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                except:
                    timestamp = datetime.now(timezone.utc)
            
            # CRITICAL: Automatic Partition Management
            # Ensure a partition exists for this metric's timestamp
            try:
                cur.execute("SELECT create_system_metrics_partition(%s)", (timestamp.date(),))
            except Exception as pe:
                # Log detailed error for VPS debugging
                logging.error(f"[DB ERROR] Partition check failed for date {timestamp.date()}: {pe}")

            cpu = usage_data.get('cpu', usage_data.get('cpu_usage', 0))
            ram = usage_data.get('ram', usage_data.get('ram_usage', 0))
            gpu = usage_data.get('gpu_load', usage_data.get('gpu_usage', 0))
            net_rx = usage_data.get('network_rx', 0)
            net_tx = usage_data.get('network_tx', 0)

            try:
                cur.execute("""
                    INSERT INTO system_metrics 
                    (system_id, timestamp, cpu_usage, ram_usage, gpu_usage, network_rx_mb, network_tx_mb)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT DO NOTHING
                """, (sys_int_id, timestamp, cpu, ram, gpu, net_rx, net_tx))
            except Exception as ie:
                 # If this fails, it's almost certainly a missing partition
                 logging.error(f"[CRITICAL DB ERROR] Could not save metrics for {unit_id}. This usually means a partition table is missing on the VPS: {ie}")
                 # We still want to update last_seen though!
            
            # Update status to online and refresh last_seen (Use GMT/UTC)
            cur.execute("UPDATE systems SET last_seen = %s, status = 'online' WHERE system_id = %s", (datetime.now(timezone.utc), sys_int_id))
            
            conn.commit()
            cur.close()
            conn.close()
        except Exception as e:
            logging.error(f"Failed to write usage to DB for unit {unit_id}: {e}")

    @staticmethod
    def get_usage(unit_id, limit=50):
        try:
            conn = get_db_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)
            
            # Resolve System ID
            cur.execute("SELECT system_id FROM systems WHERE system_id = %s OR system_name = %s", (unit_id, unit_id))
            res = cur.fetchone()
            if not res: return []
            sys_int_id = res['system_id']
            
            cur.execute("""
                SELECT timestamp, cpu_usage as cpu, ram_usage as ram, gpu_usage as gpu, 
                       network_rx_mb as network_rx, network_tx_mb as network_tx 
                FROM system_metrics 
                WHERE system_id = %s 
                ORDER BY timestamp DESC 
                LIMIT %s
            """, (sys_int_id, limit))
            
            rows = cur.fetchall()
            cur.close()
            conn.close()
            
            # Formatting for frontend
            formatted_rows = []
            for r in rows:
                formatted_rows.append({
                    'timestamp': r['timestamp'].isoformat() if hasattr(r['timestamp'], 'isoformat') else r['timestamp'],
                    'cpu': float(r['cpu']) if r['cpu'] is not None else 0,
                    'ram': float(r['ram']) if r['ram'] is not None else 0,
                    'gpu': float(r['gpu']) if r['gpu'] is not None else 0,
                    'network_rx': float(r['network_rx']) if r['network_rx'] is not None else 0,
                    'network_tx': float(r['network_tx']) if r['network_tx'] is not None else 0
                })
            
            return formatted_rows[::-1] # Newest last
        except Exception as e:
            print(f"Error in UnitStore.get_usage: {e}")
            return []


def sync_units_state(org_id=None):
    """
    Broadcast unit updates to the correct Socket.io rooms to ensure multi-tenant isolation.
    - All updates are sent to the 'ROOT' room.
    - If org_id is provided, updates are sent to that specific room.
    """
    try:
        all_units = UnitStore.get_all_units()
        
        # 1. Always sync the ROOT admins (total visibility)
        socketio.emit('units_update', all_units, room='ROOT')
        
        # 2. Sync the specific organization room if provided
        if org_id:
            target_org = str(org_id)
            org_units = [u for u in all_units if str(u.get('org_id')) == target_org]
            socketio.emit('units_update', org_units, room=target_org)
            socketio.emit('org_units_update', org_units, room=target_org)
        else:
            # If no org_id, broadcast to all individual org rooms to be safe
            unique_orgs = UnitStore.get_unique_orgs()
            for org in unique_orgs:
                target_org = str(org)
                org_units = [u for u in all_units if str(u.get('org_id')) == target_org]
                socketio.emit('units_update', org_units, room=target_org)
    except Exception as e:
        print(f"Error in sync_units_state: {e}")

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
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'local_ip': get_local_ip()
    }), 200

@app.route('/api/units', methods=['GET'])
@token_required
def get_units_route(current_user):
    """Get all registered units (filtered by org)"""
    units = UnitStore.get_all_units(current_user)
    # Log detailed context for debugging sync issues
    user_email = current_user.get('email', 'unknown')
    user_role = current_user.get('role', 'unknown')
    user_org = current_user.get('org_id', 'unknown')
    print(f"DEBUG [SYNC]: Fetching units for {user_email} | Role: {user_role} | Org: {user_org} | Found: {len(units)} units")
    return jsonify(units)

@app.route('/api/orgs', methods=['GET'])
@token_required
def get_orgs(current_user):
    """Filter orgs list for ROOT admins only"""
    if current_user['role'] != 'ROOT':
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT org_id, name, slug, tier FROM organizations ORDER BY name")
        orgs = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify(orgs)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/pricing', methods=['GET'])
def get_pricing():
    """Fetch plans (Public sees active only, ROOT sees all)"""
    try:
        # Check if requester is ROOT (optional auth)
        is_root = False
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(" ")[1]
            try:
                data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
                is_root = data.get('role') == 'ROOT'
            except:
                pass
        
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        query = "SELECT plan_id, name, slug, price_monthly, node_limit, features, is_active FROM pricing_plans"
        if not is_root:
            query += " WHERE is_active = true"
        query += " ORDER BY price_monthly ASC"
        
        cur.execute(query)
        plans = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify(plans)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/pricing', methods=['PUT'])
@token_required
def update_pricing(current_user):
    """ROOT-only endpoint to update plan details"""
    if current_user['role'] != 'ROOT':
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    plan_id = data.get('plan_id')
    price = data.get('price_monthly')
    limit = data.get('node_limit')
    features = data.get('features') # Expecting an array
    is_active = data.get('is_active')
    
    if plan_id is None:
        return jsonify({'error': 'Plan ID is required'}), 400
        
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            UPDATE pricing_plans 
            SET price_monthly = COALESCE(%s, price_monthly),
                node_limit = COALESCE(%s, node_limit),
                features = COALESCE(%s, features),
                is_active = COALESCE(%s, is_active),
                updated_at = NOW()
            WHERE plan_id = %s
        """, (price, limit, json.dumps(features) if features is not None else None, is_active, plan_id))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'message': 'Pricing updated successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/payments/create-order', methods=['POST'])
@token_required
def create_payment_order(current_user):
    """Create a Razorpay order before checkout"""
    data = request.get_json()
    plan_slug = data.get('plan_slug')
    
    if not plan_slug:
        return jsonify({'error': 'Plan slug is required'}), 400
        
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # 1. Fetch plan details
        cur.execute("SELECT plan_id, price_monthly FROM pricing_plans WHERE slug = %s AND is_active = true", (plan_slug.lower(),))
        plan = cur.fetchone()
        
        if not plan:
            conn.close()
            return jsonify({'error': 'Invalid or inactive plan'}), 404
            
        # 1.1 Check if plan is free
        if float(plan['price_monthly']) <= 0:
            conn.close()
            return jsonify({'error': 'Free plans do not require payment'}), 400
            
        # 2. Create Razorpay order
        amount_in_paise = int(plan['price_monthly'] * 100)
        order_data = {
            'amount': amount_in_paise,
            'currency': 'INR',
            'payment_capture': 1
        }
        
        order = razorpay_client.order.create(data=order_data)
        
        # 3. Log transaction as 'created'
        cur.execute("""
            INSERT INTO transactions (org_id, plan_id, amount, razorpay_order_id, status)
            VALUES (%s, %s, %s, %s, 'created')
        """, (str(current_user['org_id']), plan['plan_id'], plan['price_monthly'], order['id']))
        
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({
            'order_id': order['id'],
            'amount': amount_in_paise,
            'currency': 'INR',
            'key_id': RAZORPAY_KEY_ID,
            'plan_name': plan_slug.capitalize()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/payments/verify', methods=['POST'])
@token_required
def verify_payment(current_user):
    """Verify Razorpay payment signature and update org tier"""
    data = request.get_json()
    razorpay_order_id = data.get('razorpay_order_id')
    razorpay_payment_id = data.get('razorpay_payment_id')
    razorpay_signature = data.get('razorpay_signature')
    
    if not all([razorpay_order_id, razorpay_payment_id, razorpay_signature]):
        return jsonify({'error': 'Missing payment verification details'}), 400
        
    try:
        # Verify signature
        params_dict = {
            'razorpay_order_id': razorpay_order_id,
            'razorpay_payment_id': razorpay_payment_id,
            'razorpay_signature': razorpay_signature
        }
        
        razorpay_client.utility.verify_payment_signature(params_dict)
        
        # Signature verified -> Update DB
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # 1. Update transaction status
        cur.execute("""
            UPDATE transactions 
            SET razorpay_payment_id = %s, status = 'success' 
            WHERE razorpay_order_id = %s 
            RETURNING plan_id, amount
        """, (razorpay_payment_id, razorpay_order_id))
        
        txn = cur.fetchone()
        if not txn:
            conn.close()
            return jsonify({'error': 'Transaction record not found'}), 404
            
        # 2. Fetch new tier limits
        cur.execute("SELECT name, node_limit FROM pricing_plans WHERE plan_id = %s", (txn['plan_id'],))
        plan = cur.fetchone()
        
        # 3. Update organization tier and node_limit
        cur.execute("""
            UPDATE organizations 
            SET tier = %s, node_limit = %s 
            WHERE org_id = %s
        """, (plan['name'].upper(), plan['node_limit'], str(current_user['org_id'])))
        
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({'message': 'Payment verified and subscription updated!', 'tier': plan['name']})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/orgs/<org_id>/units', methods=['GET'])
@token_required
def get_org_units(current_user, org_id):
    """Get units for a specific org (ROOT or Org Admin check)"""
    if current_user['role'] != 'ROOT' and str(current_user['org_id']) != str(org_id):
        return jsonify({'error': 'Unauthorized'}), 403
    
    units = UnitStore.get_all_units({'role': 'ADMIN', 'org_id': org_id})
    return jsonify(units)

@app.route('/api/orgs', methods=['POST'])
@token_required
def create_org(current_user):
    """Create a new organization (ROOT only)"""
    if current_user['role'] != 'ROOT':
        return jsonify({'error': 'Unauthorized'}), 403
        
    data = request.get_json()
    org_id = data.get('org_id')
    name = data.get('name')
    tier = data.get('tier', 'FREE').upper()
    
    if not org_id or not name:
        return jsonify({'error': 'Missing org_id or name'}), 400

    def slugify(text):
        text = text.lower().strip()
        text = re.sub(r'[^\w\s-]', '', text)
        text = re.sub(r'[\s_-]+', '-', text)
        text = re.sub(r'^-+|-+$', '', text)
        return text

    # The incoming org_id from the frontend "System Registry" form is actually being used as a desired slug
    slug = slugify(org_id)
    
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # 1. Fetch node limit from pricing_plans
        cur.execute("SELECT node_limit FROM pricing_plans WHERE slug = %s", (tier.lower(),))
        plan = cur.fetchone()
        node_limit = plan['node_limit'] if plan else 1

        # 2. Check if slug exists
        cur.execute("SELECT 1 FROM organizations WHERE slug = %s", (slug,))
        if cur.fetchone():
            conn.close()
            return jsonify({'error': f'Organization ID/Slug "{slug}" is already taken.'}), 409
            
        # Move email/password extraction up so admin_email is available for the org INSERT
        admin_email = data.get('email', '').lower()
        admin_password = data.get('password')
        
        cur.execute(
            "INSERT INTO organizations (name, slug, tier, node_limit, contact_email) VALUES (%s, %s, %s, %s, %s) RETURNING org_id", 
            (name, slug, tier, node_limit, admin_email)
        )
        new_org = cur.fetchone()
        org_db_id = new_org['org_id']

        # 3. Create Initial Admin User (Optional)
        if admin_email and admin_password:
            admin_username = admin_email.split('@')[0]
            # Check if user exists
            cur.execute("SELECT 1 FROM users WHERE email = %s OR username = %s", (admin_email, admin_username))
            if cur.fetchone():
                conn.rollback()
                conn.close()
                return jsonify({'error': f'Admin user with email/username "{admin_email}" already exists.'}), 409
                
            password_hash = bcrypt.hashpw(admin_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            cur.execute(
                "INSERT INTO users (username, email, password_hash, role, org_id) VALUES (%s, %s, %s, %s, %s)",
                (admin_username, admin_email, password_hash, 'ADMIN', org_db_id)
            )

        conn.commit()
        cur.close()
        conn.close()
        return jsonify({
            'message': f'Organization created successfully',
            'org_id': new_org['org_id'],
            'slug': slug,
            'tier': tier,
            'node_limit': node_limit
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/units/<unit_id>/org', methods=['PUT'])
@token_required
def update_unit_org(current_user, unit_id):
    """Re-assign a unit to a different organization (ROOT only)"""
    if current_user['role'] != 'ROOT':
        return jsonify({'error': 'Unauthorized'}), 403
        
    data = request.get_json()
    new_org_id = data.get('org_id')
    
    if not new_org_id:
        return jsonify({'error': 'Missing org_id'}), 400
        
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        # Verify org exists
        cur.execute("SELECT 1 FROM organizations WHERE org_id = %s", (new_org_id,))
        if not cur.fetchone():
            return jsonify({'error': 'Organization does not exist'}), 404
            
        cur.execute("UPDATE systems SET org_id = %s WHERE system_name = %s", (new_org_id, unit_id))
        conn.commit()
        cur.close()
        conn.close()
        
        # Clear local cache if needed (though UnitStore fetches from DB usually)
        if unit_id in units:
            units[unit_id]['org_id'] = new_org_id
            
        return jsonify({'message': f'Unit {unit_id} moved to {new_org_id}'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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
    'timestamp': datetime.now(timezone.utc).isoformat()
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
                    'timestamp': datetime.now(timezone.utc).isoformat()
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


# Duplicate route removed to favor the authenticated version at line 1296


# --- FLEET MANAGEMENT APIS ---

@app.route('/api/units/<unit_id>', methods=['DELETE'])
def delete_unit(unit_id):
    """Delete a unit from the registry"""
    unit = UnitStore.get_unit(unit_id)
    if not unit:
        return jsonify({'error': 'Unit not found'}), 404
    
    UnitStore.delete_unit(unit_id)
    # Broadcast update
    sync_units_state(unit.get('org_id'))
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
    sync_units_state(unit.get('org_id'))
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
    # Use request origin/host as default server_url if nothing else provided
    default_server = PUBLIC_SERVER_URL or f"{request.scheme}://{request.host}"
    server_url = request.args.get('server', default_server) 
    
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
        org_id = data.get('org_id')
        comp_id = data.get('comp_id', 'default_comp')
        install_token = data.get('install_token')
        hostname = data.get('hostname', 'Unknown')
        os_info = data.get('os_info', 'Unknown')
        cpu_info = data.get('cpu_info', 'Unknown')
        ram_total = data.get('ram_total', 0)
        gpu_info = data.get('gpu_info', '{}')
        network_interfaces = data.get('network_interfaces', '{}')

        # Robust casting
        try:
            if org_id: org_id = int(org_id)
        except: pass

        # Check existing in PostgreSQL
        existing_unit = UnitStore.get_unit_by_org_comp(org_id, comp_id)
        if not existing_unit:
            # Try by system_id/name matching
            existing_unit = UnitStore.get_unit(system_id)

        if existing_unit:
            unit_id = existing_unit['id']
            # Update metadata and mark as ONLINE
            # IMPORTANT: We keep the original 'name' casing from the DB 
            # (which contains the full internal org/comp string like '1/TestCase')
            # to ensure the 'ON CONFLICT (system_name)' logic in save_unit works correctly.
            existing_unit.update({
                'org_id': org_id,
                'comp_id': comp_id,
                'name': existing_unit.get('name', f"{org_id or 'unknown'}/{comp_id}"),
                'hostname': hostname,
                'os_info': os_info,
                'ram_total': ram_total,
                'ip': request.remote_addr,
                'system_id': system_id,
                'status': 'online' # Heartbeat received!
            })
            # Explicitly force status to online for the database update
            existing_unit['status'] = 'online'
            UnitStore.save_unit(unit_id, existing_unit)
            
            # Broadcast update
            if org_id: sync_units_state(str(org_id))
            return jsonify({'unit_id': unit_id, 'org_id': org_id, 'comp_id': comp_id}), 200

        # --- NEW UNIT: Validate install_token (one-time use, admin-issued) ---
        if not install_token:
            return jsonify({'error': 'install_token is required for new registrations. Use an admin-generated installer.'}), 403

        # Verify token exists in DB for this org/comp
        try:
            conn = get_db_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)
            name = f"{org_id}/{comp_id}"
            cur.execute("""
                SELECT system_id, install_token FROM systems 
                WHERE LOWER(system_name) = LOWER(%s) AND org_id = %s AND install_token = %s
            """, (name, org_id, install_token))
            token_row = cur.fetchone()
            
            if not token_row:
                cur.close()
                conn.close()
                print(f"Token validation failed for {name}. Token: {install_token}")
                return jsonify({'error': 'Invalid or expired install token. Request a new installer from your admin.'}), 403
            
            # Token is valid — consume it (one-time use)
            cur.execute("UPDATE systems SET install_token = NULL WHERE system_id = %s", (token_row['system_id'],))
            conn.commit()
            cur.close()
            conn.close()
            print(f"Install token consumed for {name}")
        except Exception as e:
            print(f"Token validation error: {e}")
            return jsonify({'error': f'Token validation failed: {str(e)}'}), 500

        # New Unit registration proceeds
        unit_id = str(uuid.uuid4())[:8]
        unit = {
            'id': unit_id,
            'system_id': system_id,
            'org_id': org_id,
            'comp_id': comp_id,
            'ip': request.remote_addr,
            'name': f"{org_id or 'unknown'}/{comp_id}",
            'hostname': hostname,
            'os_info': os_info,
            'ram_total': ram_total,
            'status': 'online'
        }

        # Save or Update Unit
        UnitStore.save_unit(unit_id, unit)
        
        # Get the actual assigned ID and verify status is online
        new_unit = UnitStore.get_unit_by_org_comp(org_id, comp_id)
        if new_unit: 
            unit_id = new_unit['id']
            # Force status check if not already online
            if new_unit.get('status') != 'online':
                conn = get_db_connection()
                cur = conn.cursor()
                cur.execute("UPDATE systems SET status = 'online', last_seen = now() WHERE system_id = %s", (new_unit.get('system_id'),))
                conn.commit()
                cur.close()
                conn.close()

        print(f"Unit registered & activated: {org_id}/{comp_id} (ID: {unit_id})")
        if org_id: sync_units_state(str(org_id))

        return jsonify({'unit_id': unit_id, 'org_id': org_id, 'comp_id': comp_id}), 201

    except Exception as e:
        print(f"Error registering unit: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/deregister_unit', methods=['POST'])
def deregister_unit():
    """Called by the client uninstall script to remove a node from the server."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body required'}), 400
        
        system_id = data.get('system_id')
        org_id = data.get('org_id')
        comp_id = data.get('comp_id')
        
        if not org_id or not comp_id:
            return jsonify({'error': 'org_id and comp_id are required'}), 400
        
        name = f"{org_id}/{comp_id}"
        
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            
            # Delete metrics first (FK constraint)
            cur.execute("""
                DELETE FROM system_metrics 
                WHERE system_id IN (SELECT system_id FROM systems WHERE system_name = %s)
            """, (name,))
            
            # Delete the system
            cur.execute("DELETE FROM systems WHERE system_name = %s", (name,))
            deleted = cur.rowcount
            
            conn.commit()
            cur.close()
            conn.close()
            
            if deleted > 0:
                print(f"Unit deregistered via client uninstall: {name}")
                # Broadcast update so dashboard reflects immediately
                sync_units_state(str(org_id))
                return jsonify({'status': 'deregistered', 'name': name}), 200
            else:
                return jsonify({'status': 'not_found', 'name': name}), 404
                
        except Exception as e:
            print(f"Error deregistering unit: {e}")
            return jsonify({'error': str(e)}), 500
            
    except Exception as e:
        print(f"Error in deregister_unit: {e}")
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

    # Update metadata and last_seen via save_unit
    unit.update({
        'status': 'online',
        'last_seen': datetime.now(timezone.utc),
        'ip': request.remote_addr,
        'hostname': data.get('hostname', unit.get('hostname'))
    })
    
    # If org/comp changed in heartbeat, update it
    if 'org_id' in data and data['org_id'] != unit.get('org_id'):
        unit['org_id'] = data['org_id']
    if 'comp_id' in data and data['comp_id'] != unit.get('comp_id'):
        unit['comp_id'] = data['comp_id']
        unit['name'] = f"{unit.get('org_id', 'unknown')}/{data['comp_id']}"

    UnitStore.save_unit(unit_id, unit)
    
    # CRITICAL: Broadcast SocketIO *before* attempting DB write for usage
    # This ensures live graphs work even if the SQL historical insert fails
    socketio.emit('usage_update', {'unit_id': unit_id, 'data': data})
    if org_id:
        socketio.emit('org_usage_update', {'unit_id': unit_id, 'data': data}, room=str(org_id))

    # Now attempt to persist to SQL (non-blocking for the heartbeat response)
    try:
        UnitStore.add_usage(unit_id, data)
    except Exception as e:
        logging.error(f"Post-heartbeat usage storage failed: {e}")
            
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
        
        # 1. Resolve System ID - unit_id from frontend is usually systems.system_id (int) as string
        cur.execute("SELECT system_id FROM systems WHERE system_id::varchar = %s OR system_name = %s", (unit_id, unit_id))
        res = cur.fetchone()
        if not res:
             return jsonify({'error': f'No data found for unit {unit_id}'}), 404
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
            
            filter_start = datetime.now(timezone.utc) - timedelta(days=days)
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

# ============================================================
# INTELLIGENT REPORT ANALYSIS ENGINE
# ============================================================

def calculate_node_health(metrics_summary):
    """Calculates a health score from 0 to 100 based on metrics."""
    if not metrics_summary: return 100
    
    cpu_avg = metrics_summary.get('avg_cpu', 0)
    ram_avg = metrics_summary.get('avg_ram', 0)
    gpu_avg = metrics_summary.get('avg_gpu', 0)
    
    # Simple weighted penalty system
    score = 100
    if cpu_avg > 80: score -= 20
    elif cpu_avg > 60: score -= 10
    
    if ram_avg > 90: score -= 30
    elif ram_avg > 75: score -= 15
    
    if gpu_avg > 85: score -= 15
    
    return max(0, score)

def get_intelligent_insights(metrics_rows, sys_info):
    """Generates human-readable analysis based on telemetry data patterns."""
    insights = []
    if not metrics_rows:
        return [{
            "type": "info",
            "title": "Data Scarcity",
            "text": "Insufficient telemetry data detected for the selected period. Connect the node and allow some time for metrics to accumulate."
        }]

    cpu_vals = [r['cpu_usage'] for r in metrics_rows]
    ram_vals = [r['ram_usage'] for r in metrics_rows]
    
    avg_cpu = sum(cpu_vals) / len(cpu_vals)
    max_cpu = max(cpu_vals)
    avg_ram = sum(ram_vals) / len(ram_vals)
    max_ram = max(ram_vals)

    # 1. Resource Utilization Insights
    if avg_cpu < 5 and max_cpu < 15:
        insights.append({
            "type": "optimization",
            "title": "Severe Under-utilization",
            "text": "This node is consistently idle (Avg CPU < 5%). Consider downgrading resources or consolidating workloads to save costs."
        })
    elif avg_cpu > 70:
        insights.append({
            "type": "warning",
            "title": "High Sustained Workload",
            "text": "The CPU is under heavy load (70%+ average). This might lead to latency issues during peak operations."
        })

    if max_ram > 95:
        insights.append({
            "type": "critical",
            "title": "RAM Exhaustion Detected",
            "text": "System hit 95%+ RAM usage. This likely triggered swap-file usage, significantly slowing down performance."
        })

    # 2. Stability Analysis
    if len(cpu_vals) > 5:
        variance = sum((x - avg_cpu) ** 2 for x in cpu_vals) / len(cpu_vals)
        if variance > 400: # High swing
            insights.append({
                "type": "info",
                "title": "Unstable Load Profile",
                "text": "We detected massive swings in CPU usage. This suggests bursty workloads or frequent periodic heavy tasks."
            })

    # 3. Recommendations
    if avg_ram > 80:
        insights.append({
            "type": "recommendation",
            "title": "Memory Upgrade Advised",
            "text": f"Average RAM usage is {avg_ram:.1f}%. Increasing physical memory will provide more head-room for OS caching."
        })

    return insights

@app.route('/api/reports/node/<unit_id>', methods=['GET'])
def get_node_report(unit_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Resolve Unit
        cur.execute("SELECT * FROM systems WHERE system_id::varchar = %s OR system_name = %s", (unit_id, unit_id))
        system = cur.fetchone()
        if not system:
            return jsonify({'error': 'Node not found'}), 404
        
        sys_id = system['system_id']
        time_range = request.args.get('range', '7d')
        days = 7
        if time_range == '1d': days = 1
        elif time_range == '30d': days = 30
        elif time_range == '1y': days = 365
        
        start_date = datetime.now() - timedelta(days=days)
        
        # Decide granularity
        if days <= 7:
            # Raw data
            query = "SELECT timestamp, cpu_usage, ram_usage, gpu_usage as gpu_usage, network_rx_mb, network_tx_mb FROM system_metrics WHERE system_id = %s AND timestamp >= %s ORDER BY timestamp ASC"
            cur.execute(query, (sys_id, start_date))
        else:
            # Aggregated data
            period_type = 'hourly' if days <= 31 else 'daily'
            query = "SELECT period_start as timestamp, avg_cpu_usage as cpu_usage, avg_ram_usage as ram_usage, avg_gpu_usage as gpu_usage, total_network_rx_mb as network_rx_mb, total_network_tx_mb as network_tx_mb FROM aggregated_metrics WHERE system_id = %s AND period_start >= %s AND period_type = %s ORDER BY period_start ASC"
            cur.execute(query, (sys_id, start_date, period_type))
            
        rows = cur.fetchall()
            
        # Prepare timeline data for JSON serialization (convert datetime and decimals)
        formatted_rows = []
        for r in rows:
            row_dict = dict(r)
            if isinstance(row_dict.get('timestamp'), datetime):
                row_dict['timestamp'] = row_dict['timestamp'].isoformat()
            
            # Ensure numbers are floats
            for key in ['cpu_usage', 'ram_usage', 'gpu_usage', 'network_rx_mb', 'network_tx_mb']:
                if row_dict.get(key) is not None:
                    row_dict[key] = float(row_dict[key])
            
            formatted_rows.append(row_dict)

        # Perform Analysis
        insights = get_intelligent_insights(rows, system)

        # Basic Summary
        summary = {
            "avg_cpu": sum(float(r['cpu_usage'] or 0) for r in rows) / len(rows) if rows else 0,
            "max_cpu": max([float(r['cpu_usage'] or 0) for r in rows]) if rows else 0,
            "avg_ram": sum(float(r['ram_usage'] or 0) for r in rows) / len(rows) if rows else 0,
            "max_ram": max([float(r['ram_usage'] or 0) for r in rows]) if rows else 0,
            "total_rx": sum(float(r['network_rx_mb'] or 0) for r in rows) if rows else 0,
            "total_tx": sum(float(r['network_tx_mb'] or 0) for r in rows) if rows else 0,
        }
        
        health_score = calculate_node_health(summary)
        
        return jsonify({
            "system": {
                "name": system.get('system_name', 'Unknown'),
                "os": system.get('os', 'Unknown'),
                "ip": system.get('ip_address', 'Unknown'),
                "cpu_model": system.get('cpu_info', 'Unknown CPU'),
                "ram_gb": float(system.get('ram_gb', 0)) if system.get('ram_gb') else 0
            },
            "summary": summary,
            "health_score": health_score,
            "insights": insights,
            "timeline": formatted_rows
        })
        
    except Exception as e:
        logging.error(f"Report Error: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()
        conn.close()

@app.route('/api/reports/org/<org_id>', methods=['GET'])
def get_org_report(org_id):
    # Fleet-wide intelligence aggregation
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute("SELECT system_id, system_name FROM systems WHERE org_id::varchar = %s", (org_id,))
        systems = cur.fetchall()
        
        report_data = []
        for sys in systems:
            # Fetch summary for each node (simplified for fleet report)
            cur.execute("SELECT AVG(cpu_usage) as avg_cpu, AVG(ram_usage) as avg_ram FROM system_metrics WHERE system_id = %s AND timestamp >= NOW() - INTERVAL '7 days'", (sys['system_id'],))
            res = cur.fetchone()
            report_data.append({
                "name": sys['system_name'],
                "avg_cpu": float(res['avg_cpu'] or 0),
                "avg_ram": float(res['avg_ram'] or 0)
            })
            
        return jsonify({
            "org_id": org_id,
            "fleet_size": len(systems),
            "node_summaries": report_data,
            "insights": [
                {"type": "info", "title": "Fleet Capacity", "text": f"Your fleet currently consists of {len(systems)} active monitoring nodes."}
            ]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()
        conn.close()

@socketio.on('connect')
def handle_connect():
    # Security: Do not emit all units on connect.
    # Wait for the client to join an organization or prove ROOT status.
    print(f"Client connected: {request.sid}")

@socketio.on('join')
def handle_join(data):
    """
    Allow a client to join their specific organization room.
    The 'org_id' is passed from the client after authentication.
    """
    org_id = data.get('org_id')
    if org_id:
        join_room(org_id)
        # If the user is ROOT, they also join a special 'ROOT' room for all updates
        if data.get('role') == 'ROOT':
            join_room('ROOT')
        
        print(f"Client {request.sid} joined room: {org_id}")
        # Send initial sync for this org
        sync_units_state(org_id)

@socketio.on('join_org')
def handle_join_org(data):
    org_id = data.get('org_id')
    role = data.get('role') # Passed from frontend based on JWT
    
    from flask_socketio import join_room
    
    if role == 'ROOT':
        join_room('ROOT')
        print(f"Admin joined ROOT room: {request.sid}")
        emit('units_update', UnitStore.get_all_units())
    elif org_id:
        join_room(org_id)
        print(f"User joined Org room: {org_id} ({request.sid})")
        emit('units_update', UnitStore.get_units_by_org(org_id))
        emit('org_units_update', UnitStore.get_units_by_org(org_id))

if __name__ == '__main__':
    # Units are now managed exclusively in PostgreSQL
    socketio.run(app, host='0.0.0.0', port=5010, debug=True, allow_unsafe_werkzeug=True)
