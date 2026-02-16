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
from flask import Flask, jsonify, request, make_response
from flask_cors import CORS
from flask_socketio import SocketIO, emit
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
DATA_DIR = 'unit_data'
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

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
    def get_unique_orgs():
        """Get a list of all unique organization IDs"""
        all_units = UnitStore.get_all_units()
        orgs = set()
        for unit in all_units:
            if unit.get('org_id'):
                orgs.add(unit.get('org_id'))
        return sorted(list(orgs))

    @staticmethod
    def get_units_by_org(org_id):
        """Get all units for a specific organization"""
        all_units = UnitStore.get_all_units()
        return [unit for unit in all_units if unit.get('org_id') == org_id]

    @staticmethod
    def add_usage(unit_id, usage_data):
        # Persist to disk for history
        try:
            log_file = os.path.join(DATA_DIR, f'{unit_id}.jsonl')
            with open(log_file, 'a') as f:
                f.write(json.dumps(usage_data) + '\n')
        except Exception as e:
            print(f"Failed to log usage to disk: {e}")

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
        """
        Get latest usage for all online units grouped by org.
        Returns: { 'Org1': [ {unit1_usage}, {unit2_usage} ], 'Org2': ... }
        """
        all_units = UnitStore.get_all_units()
        online_units = [u for u in all_units if u.get('status') == 'online']
        
        result = {}
        for unit in online_units:
            org = unit.get('org_id', 'Unknown')
            usage = UnitStore.get_usage(unit['id'], limit=1)
            if usage:
                if org not in result:
                    result[org] = []
                # Enrich usage with unit name
                latest_usage = usage[0]
                latest_usage['unit_name'] = unit.get('comp_id', unit['name'])
                latest_usage['unit_id'] = unit['id']
                result[org].append(latest_usage)
        return result

CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# --- Routes ---

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'ok', 'timestamp': datetime.now().isoformat()}), 200

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
    data = UnitStore.get_usage(unit_id, limit=100) # Get last 100 points
    return jsonify(data)

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

@app.route('/api/report_usage', methods=['POST'])
def report_usage():
    """Receive usage data from client unit"""
    try:
        data = request.get_json()
        if not data or 'unit_id' not in data:
            return jsonify({'error': 'unit_id required'}), 400

        unit_id = data['unit_id']
        org_id = data.get('org_id')

        # Verify unit exists
        unit = UnitStore.get_unit(unit_id)
        if not unit:
            return jsonify({'error': 'Unit not registered'}), 404

        # Update unit status
        unit['last_seen'] = datetime.now().isoformat()
        unit['status'] = 'online'
        UnitStore.save_unit(unit_id, unit)
        
        # Add usage
        UnitStore.add_usage(unit_id, data)

        # Check for alerts (Simple threshold logic)
        if data.get('cpu', 0) > 90:
            alert = {
                'id': str(uuid.uuid4())[:8],
                'unit_id': unit_id,
                'type': 'cpu',
                'message': f"High CPU usage: {data['cpu']}%",
                'severity': 'high',
                'timestamp': datetime.now().isoformat(),
                'acknowledged': False
            }
            alerts.append(alert)
            if unit.get('alerts') is None: unit['alerts'] = []
            unit['alerts'].append(alert)
            UnitStore.save_unit(unit_id, unit)
            socketio.emit('new_alert', alert)

        # Broadcast usage update to global listeners and org-specific rooms
        socketio.emit('usage_update', {'unit_id': unit_id, 'data': data})
        if org_id:
             socketio.emit('org_usage_update', {'unit_id': unit_id, 'data': data}, room=org_id)

        return jsonify({'status': 'received'}), 200

    except Exception as e:
        print(f"Error reporting usage: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/units/<unit_id>/export', methods=['GET'])
def export_unit_data(unit_id):
    """Export unit usage data as CSV for a specific timeframe"""
    try:
        time_range = request.args.get('range', '1d')
        days = 1
        if time_range == '5d': days = 5
        elif time_range == '10d': days = 10
        elif time_range == 'all': days = 9999
        
        # Calculate start date (naive, but fine for now)
        start_date = datetime.now() - timedelta(days=days)
        log_file = os.path.join(DATA_DIR, f'{unit_id}.jsonl')
        
        if not os.path.exists(log_file):
            return jsonify({'error': 'No data found for this unit'}), 404

        # Generate CSV in memory
        si = io.StringIO()
        cw = csv.writer(si)
        cw.writerow(['Timestamp', 'CPU (%)', 'RAM (%)', 'GPU Load (%)'])
        
        with open(log_file, 'r') as f:
            for line in f:
                try:
                    record = json.loads(line)
                    # Parse timestamp (handle Z or no Z)
                    ts_str = record.get('timestamp', '')
                    if ts_str.endswith('Z'): ts_str = ts_str[:-1]
                    record_time = datetime.fromisoformat(ts_str)
                    
                    if record_time >= start_date:
                        cw.writerow([
                            record.get('timestamp'),
                            record.get('cpu'),
                            record.get('ram'),
                            record.get('gpu_load', 0)
                        ])
                except Exception:
                    continue

        output = make_response(si.getvalue())
        output.headers["Content-Disposition"] = f"attachment; filename={unit_id}_usage_{time_range}.csv"
        output.headers["Content-type"] = "text/csv"
        return output

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# WebSocket Events
@socketio.on('connect')
def handle_connect():
    emit('units_update', UnitStore.get_all_units())

@socketio.on('join_org')
def handle_join_org(data):
    """Client joins an organization room to receive specific updates"""
    org_id = data.get('org_id')
    if org_id:
        from flask_socketio import join_room
        join_room(org_id)
        # Send initial state for this org
        emit('org_units_update', UnitStore.get_units_by_org(org_id))

if __name__ == '__main__':
    # Start the logging thread
    # start_logging_thread() # Not using the old logging thread anymore
    
    # Run server
    # Use 0.0.0.0 to make it accessible from other machines
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, allow_unsafe_werkzeug=True)