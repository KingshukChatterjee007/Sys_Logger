import psutil
import requests
import uuid
import json
import os
import sys
import time
import threading
import socket
import platform
import subprocess
import signal
import logging
from datetime import datetime, timedelta
try:
    import GPUtil
    NVIDIA_AVAILABLE = True
except ImportError:
    NVIDIA_AVAILABLE = False

# Configuration
CONFIG_FILE = 'unit_client_config.json'
DEFAULT_SERVER_URL = 'http://localhost:5000'  # Change this to your central server URL
COLLECTION_INTERVAL = 1  # seconds - updated for 1-second updates
RECONNECT_INTERVAL = 300  # seconds (5 minutes)
MAX_RETRIES = 3
RETRY_DELAY = 10  # seconds

def prompt_server_url():
    """Prompt user for server URL/IP and validate connection"""
    print("Sys_Logger Unit Client - Server Configuration")
    print("=" * 50)

    while True:
        server_url = input("Enter server URL or IP (default: http://localhost:5000): ").strip()
        if not server_url:
            server_url = DEFAULT_SERVER_URL
            print(f"Using default server URL: {server_url}")

        # Validate URL format
        if not server_url.startswith(('http://', 'https://')):
            server_url = f"http://{server_url}"

        # Try to connect to server
        print(f"Testing connection to {server_url}...")
        try:
            response = requests.get(f"{server_url}/api/health", timeout=10)
            if response.status_code == 200:
                print("✓ Server connection successful!")
                return server_url
            else:
                print(f"⚠ Server responded with status {response.status_code}")
                retry = input("Continue anyway? (y/n): ").lower().strip()
                if retry == 'y':
                    return server_url
        except requests.RequestException as e:
            print(f"ERROR: Cannot connect to server: {e}")

        retry = input("Try different server URL? (y/n): ").lower().strip()
        if retry != 'y':
            print("Using default server URL...")
            return DEFAULT_SERVER_URL

class UnitClient:
    def __init__(self):
        self.system_id = self.get_or_create_system_id()
        self.server_url = self.get_server_url()
        self.unit_id = None
        self.registered = False
        self.running = True
        self.thread = None
        self.last_network_counters = None
        self.restart_count = 0
        self.last_restart_time = time.time()
        self.shutdown_event = threading.Event()

        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

        logging.info(f"Unit Client initialized with System ID: {self.system_id}")
        print(f"Unit Client initialized with System ID: {self.system_id}")

    def signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        logging.info(f"Received signal {signum}, initiating graceful shutdown")
        self.stop()

    def get_or_create_system_id(self):
        """Generate and persist a unique system ID"""
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    config = json.load(f)
                    return config.get('system_id')
            except (json.JSONDecodeError, KeyError):
                pass

        system_id = str(uuid.uuid4())
        config = {'system_id': system_id, 'server_url': DEFAULT_SERVER_URL}
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=4)
        return system_id

    def get_server_url(self):
        """Get server URL from config or use default.
        
        Supports both 'server_url' field and separate 'server_host'/'server_port' fields.
        """
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    config = json.load(f)
                    # First try direct server_url
                    if 'server_url' in config and config['server_url']:
                        return config.get('server_url')
                    # Fallback: construct from server_host and server_port
                    host = config.get('server_host', 'localhost')
                    port = config.get('server_port', '5000')
                    if host:
                        return f"http://{host}:{port}"
                    return DEFAULT_SERVER_URL
            except (json.JSONDecodeError, KeyError):
                pass
        return DEFAULT_SERVER_URL

    def update_server_url(self, new_url):
        """Update server URL in config"""
        config = {'system_id': self.system_id, 'server_url': new_url}
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=4)
        self.server_url = new_url

    def get_system_info(self):
        """Collect system information for registration"""
        try:
            hostname = socket.gethostname()
            os_info = f"{platform.system()} {platform.release()}"
            cpu_info = platform.processor() or "Unknown CPU"
            ram_total = round(psutil.virtual_memory().total / (1024**3), 2)  # GB

            # GPU info
            gpu_info = {}
            try:
                if NVIDIA_AVAILABLE:
                    gpus = GPUtil.getGPUs()
                    gpu_info = {
                        'count': len(gpus),
                        'details': [{'name': gpu.name, 'memory': gpu.memoryTotal} for gpu in gpus]
                    }
            except:
                gpu_info = {'count': 0, 'details': []}

            # Network interfaces
            network_interfaces = {}
            for name, addrs in psutil.net_if_addrs().items():
                network_interfaces[name] = [addr.address for addr in addrs if addr.family == socket.AF_INET]

            return {
                'system_id': self.system_id,
                'hostname': hostname,
                'os_info': os_info,
                'cpu_info': cpu_info,
                'ram_total': ram_total,
                'gpu_info': json.dumps(gpu_info),
                'network_interfaces': json.dumps(network_interfaces)
            }
        except Exception as e:
            print(f"Error getting system info: {e}")
            return None

    def register_unit(self):
        """Register this unit with the central server"""
        if self.registered:
            return True

        info = self.get_system_info()
        if not info:
            return False

        url = f"{self.server_url}/api/register_unit"
        for attempt in range(MAX_RETRIES):
            try:
                response = requests.post(url, json=info, timeout=30)
                if response.status_code == 200 or response.status_code == 201:
                    data = response.json()
                    self.unit_id = data.get('unit_id')
                    self.registered = True
                    print("Unit registered successfully")
                    return True
                elif response.status_code == 409:  # Already registered
                    self.registered = True
                    print("Unit already registered")
                    return True
                else:
                    print(f"Registration failed: {response.status_code} - {response.text}")
            except requests.RequestException as e:
                print(f"Registration attempt {attempt + 1} failed: {e}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY)

        return False

    def get_gpu_usage(self):
        """Get GPU usage"""
        try:
            if NVIDIA_AVAILABLE:
                gpus = GPUtil.getGPUs()
                if gpus:
                    return max(gpu.load * 100 for gpu in gpus)  # Max usage %
        except:
            pass
        return 0.0

    def get_temperature(self):
        """Get system temperature"""
        try:
            temps = psutil.sensors_temperatures()
            if temps:
                # Get the highest temperature from available sensors
                max_temp = 0
                for sensor_name, sensors in temps.items():
                    for sensor in sensors:
                        if sensor.current > max_temp:
                            max_temp = sensor.current
                return max_temp
        except:
            pass
        return None

    def get_network_io(self):
        """Get network I/O rates in MB/s"""
        try:
            counters = psutil.net_io_counters()
            now = time.time()

            if self.last_network_counters is None:
                self.last_network_counters = (counters, now)
                return 0.0, 0.0

            last_counters, last_time = self.last_network_counters
            time_diff = now - last_time

            if time_diff > 0:
                rx_rate = (counters.bytes_recv - last_counters.bytes_recv) / (1024**2) / time_diff  # MB/s
                tx_rate = (counters.bytes_sent - last_counters.bytes_sent) / (1024**2) / time_diff  # MB/s
                self.last_network_counters = (counters, now)
                return rx_rate, tx_rate
        except:
            pass
        return 0.0, 0.0

    def collect_usage_data(self):
        """Collect current system usage data"""
        try:
            cpu_usage = psutil.cpu_percent(interval=1)
            ram_usage = psutil.virtual_memory().percent
            gpu_usage = self.get_gpu_usage()
            temperature = self.get_temperature()
            network_rx, network_tx = self.get_network_io()

            data = {
                'system_id': self.system_id,
                'timestamp': datetime.utcnow().isoformat(),
                'cpu_usage': cpu_usage,
                'ram_usage': ram_usage,
                'gpu_usage': gpu_usage,
                'temperature': temperature,
                'network_rx': network_rx,
                'network_tx': network_tx
            }
            return data
        except Exception as e:
            print(f"Error collecting usage data: {e}")
            return None

    def submit_usage_data(self, data):
        """Submit usage data to the central server"""
        url = f"{self.server_url}/api/submit_usage"
        for attempt in range(MAX_RETRIES):
            try:
                response = requests.post(url, json=data, timeout=30)
                if response.status_code == 200:
                    print(f"Data submitted successfully at {data['timestamp']}")
                    return True
                else:
                    print(f"Data submission failed: {response.status_code} - {response.text}")
            except requests.RequestException as e:
                print(f"Submission attempt {attempt + 1} failed: {e}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY)

        return False

    def data_collection_loop(self):
        """Main data collection and submission loop"""
        while self.running:
            try:
                # Try to register if not registered
                if not self.registered:
                    self.register_unit()
                    if not self.registered:
                        print("Failed to register, retrying in 5 minutes...")
                        time.sleep(RECONNECT_INTERVAL)
                        continue

                # Collect and submit data
                data = self.collect_usage_data()
                if data:
                    self.submit_usage_data(data)
                else:
                    print("Failed to collect usage data")

                # Wait for next collection interval
                time.sleep(COLLECTION_INTERVAL)

            except Exception as e:
                print(f"Error in data collection loop: {e}")
                time.sleep(RETRY_DELAY)  # Wait before retrying

    def start(self):
        """Start the client in a background thread"""
        if self.thread and self.thread.is_alive():
            print("Client is already running")
            return

        self.thread = threading.Thread(target=self.data_collection_loop, daemon=True)
        self.thread.start()
        print("Unit client started")

    def stop(self):
        """Stop the client"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        print("Unit client stopped")

    def run_foreground(self):
        """Run the client in foreground (for testing)"""
        print("Running unit client in foreground. Press Ctrl+C to stop.")
        try:
            self.data_collection_loop()
        except KeyboardInterrupt:
            print("\nStopping...")
            self.stop()

def main():
    client = UnitClient()

    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == '--foreground':
            client.run_foreground()
        elif command == '--start':
            client.start()
            # Keep main thread alive
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                client.stop()
        elif command == '--stop':
            client.stop()
        elif command == '--status':
            # Simple status check
            print(f"System ID: {client.system_id}")
            print(f"Server URL: {client.server_url}")
            print(f"Registered: {client.registered}")
            print(f"Running: {client.thread and client.thread.is_alive() if client.thread else False}")
        else:
            print("Usage: python unit_client.py [--foreground|--start|--stop|--status]")
    else:
        # Default: run in foreground
        client.run_foreground()

if __name__ == "__main__":
    main()