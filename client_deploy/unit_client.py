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
import queue
from datetime import datetime, timedelta
try:
    import GPUtil
    NVIDIA_AVAILABLE = True
except ImportError:
    NVIDIA_AVAILABLE = False

# Configuration
CONFIG_FILE = 'unit_client_config.json'
CACHE_FILE = 'cached_usage.json'
DEFAULT_SERVER_URL = 'http://203.193.145.59:5010'  # Change this to your central server URL
COLLECTION_INTERVAL = 1  # seconds - updated for 1-second updates
RECONNECT_INTERVAL = 300  # seconds (5 minutes)
MAX_RETRIES = 3
RETRY_DELAY = 10  # seconds
MAX_CACHE_SIZE = 1000  # Max records to cache offline
SYNC_BATCH_SIZE = 10   # Number of records to sync at once

def prompt_server_url():
    """Prompt user for server URL/IP and validate connection"""
    print("Sys_Logger Unit Client - Server Configuration")
    print("=" * 50)

    while True:
        server_url = input("Enter server URL or IP (default: http://203.193.145.59:5010): ").strip()
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

def prompt_org_info(silent=False):
    """Prompt user for Organization ID and Computer ID or use defaults"""
    if silent:
        return "default_org", socket.gethostname()
        
    print("\nSys_Logger Unit Client - Unit Identification")
    print("-" * 50)
    
    org_id = input("Enter Organization ID (e.g., org1): ").strip() or "default_org"
    comp_id = input("Enter Computer ID (e.g., comp1): ").strip() or socket.gethostname()
    
    return org_id, comp_id

class UnitClient:
    def __init__(self, silent=False):
        self.silent = silent
        self.config = self.load_config()
        self.system_id = self.config.get('system_id')
        self.org_id = self.config.get('org_id')
        self.comp_id = self.config.get('comp_id')
        self.server_url = self.config.get('server_url', DEFAULT_SERVER_URL)
        
        if not self.org_id or not self.comp_id:
            self.org_id, self.comp_id = prompt_org_info(silent)
            self.save_config()

        self.unit_id = None
        self.registered = False
        self.running = True
        self.last_network_counters = None
        self.data_queue = queue.Queue()
        
        # Load existing cache into queue
        cached_data = self.load_cache()
        for item in cached_data:
            self.data_queue.put(item)
            
        self.sync_thread = None
        
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

        if not silent:
            logging.info(f"Unit Client initialized: {self.org_id}/{self.comp_id}")
            print(f"Unit Client initialized: {self.org_id}/{self.comp_id}")

    def signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        logging.info(f"Received signal {signum}, initiating graceful shutdown")
        self.stop()

    def load_config(self):
        config = {'system_id': str(uuid.uuid4()), 'server_url': DEFAULT_SERVER_URL, 'org_id': None, 'comp_id': None}
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    config.update(json.load(f))
            except (json.JSONDecodeError, KeyError):
                pass
        return config

    def save_config(self):
        """Save current configuration to file"""
        config = {
            'system_id': self.system_id,
            'server_url': self.server_url,
            'org_id': self.org_id,
            'comp_id': self.comp_id
        }
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=4)

    def load_cache(self):
        if os.path.exists(CACHE_FILE):
            try:
                with open(CACHE_FILE, 'r') as f:
                    return json.load(f)
            except: pass
        return []

    def save_cache(self):
        try:
            with open(CACHE_FILE, 'w') as f:
                json.dump(self.cache[-MAX_CACHE_SIZE:], f)
        except: pass

    def update_server_url(self, new_url):
        """Update server URL in config"""
        self.server_url = new_url
        self.save_config()

    def get_system_info(self):
        """Collect system information for registration"""
        try:
            hostname = socket.gethostname()
            os_info = f"{platform.system()} {platform.release()}"
            cpu_info = platform.processor() or "Unknown CPU"
            ram_total = round(psutil.virtual_memory().total / (1024**3), 2)  # GB

            return {
                'system_id': self.system_id,
                'org_id': self.org_id,
                'comp_id': self.comp_id,
                'hostname': hostname,
                'os_info': os_info,
                'cpu_info': cpu_info,
                'ram_total': ram_total,
                'gpu_info': json.dumps({'nvidia': NVIDIA_AVAILABLE}),
                'network_interfaces': json.dumps({})
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
        try:
            response = requests.post(url, json=info, timeout=30)
            if response.status_code in [200, 201, 409]:
                self.registered = True
                try:
                    self.unit_id = response.json().get('unit_id')
                except: pass

                if not self.silent:
                    print(f"Unit registered successfully (Status: {response.status_code})")
                return True
            else:
                if not self.silent:
                    print(f"Registration failed with status: {response.status_code}")
        except requests.RequestException as e:
            if not self.silent:
                print(f"Registration error: {e}")
        return False

    def get_gpu_usage(self):
        """Get GPU usage (NVIDIA via GPUtil, or AMD/Generic via PowerShell)"""
        usage = 0.0
        try:
            # 1. Try NVIDIA first
            if NVIDIA_AVAILABLE:
                gpus = GPUtil.getGPUs()
                if gpus:
                    usage = max(gpu.load * 100 for gpu in gpus)
                    if usage > 0:
                        return usage
        except Exception as e:
            logging.debug(f"Failed to get NVIDIA GPU usage: {e}")
            pass

        # 2. Try Windows Performance Counters (for AMD / Intel / any Windows GPU)
        if platform.system() == 'Windows':
            usage = self.get_windows_gpu_usage()
            
        return usage

    def get_windows_gpu_usage(self):
        """Robust GPU usage detection for Windows (AMD/NVIDIA/Intel)"""
        try:
            # Ultra-simple PowerShell to avoid any parser/quoting issues
            cmd = [
                "powershell",
                "-Command",
                "(Get-Counter '\\GPU Engine(*)\\Utilization Percentage' -ErrorAction SilentlyContinue).CounterSamples.CookedValue | Measure-Object -Max | Select-Object -ExpandProperty Maximum"
            ]
            
            output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, timeout=8).decode().strip()
            
            if output:
                import re
                # Match any float or integer
                match = re.search(r"(\d+[\.,]\d+|\d+)", output)
                if match:
                    val = match.group(1).replace(',', '.')
                    usage = round(float(val), 2)
                    # Cap at 100% just in case of counter oddities
                    return min(100.0, usage)
        except Exception as e:
            if not self.silent:
                logging.debug(f"Failed to get Windows GPU usage: {e}")
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
            network_rx, network_tx = self.get_network_io()

            data = {
                'system_id': self.system_id,
                'org_id': self.org_id,
                'comp_id': self.comp_id,
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'cpu_usage': cpu_usage,
                'ram_usage': ram_usage,
                'gpu_usage': gpu_usage,
                'network_rx': network_rx,
                'network_tx': network_tx,
                'unit_id': self.unit_id
            }
            return data
        except Exception as e:
            print(f"Error collecting usage data: {e}")
            return None

    def submit_data(self, data):
        """Submit usage data to the central server"""
        url = f"{self.server_url}/api/report_usage"
        try:
            # if not self.silent:
            #     print(f"DEBUG: Submitting data with timestamp: {data.get('timestamp')}")
            response = requests.post(url, json=data, timeout=30)
            if response.status_code == 404:
                # Server forgot us (likely restarted), force re-registration
                if not self.silent:
                    print("Server responded with 404 (Unit Not Found). Re-registering...")
                self.registered = False
                return False
            
            if response.status_code != 200:
                 if not self.silent:
                    print(f"Data submission failed with status: {response.status_code}")
            return response.status_code == 200
        except requests.RequestException as e:
            if not self.silent:
                print(f"Data submission error: {e}")
            return False

    def sync_offline_data(self):
        if not self.silent:
            print("Sync thread started.")
            
        while self.running:
            # 1. Build a batch
            batch = []
            try:
                # Block for the first item
                item = self.data_queue.get(timeout=1)
                batch.append(item)
                
                # Opportunistically grab more items up to batch size
                while len(batch) < SYNC_BATCH_SIZE:
                    try:
                        item = self.data_queue.get_nowait()
                        batch.append(item)
                    except queue.Empty:
                        break
            except queue.Empty:
                continue

            if not batch:
                continue

            # 2. Add Unit ID check for all items in batch
            for item in batch:
                if self.unit_id:
                    item['unit_id'] = self.unit_id

            # 3. Retry Loop (Infinite until success or stop)
            sent = False
            while not sent and self.running:
                # Check registration before sending
                if not self.registered:
                    if not self.register_unit():
                         # If we can't register, wait and retry loop
                        time.sleep(RETRY_DELAY)
                        continue
                        
                # Attempt Send
                if self.submit_data(batch):
                    sent = True
                    if not self.silent:
                         print(f"✓ Synced batch of {len(batch)} records. Queue size: {self.data_queue.qsize()}")
                    
                    # Mark all as done
                    for _ in batch:
                        self.data_queue.task_done()
                        
                    # Save cache (optional optimization: only save if queue is empty or periodically)
                    if self.data_queue.qsize() == 0:
                        self.save_cache_from_queue()
                else:
                    if not self.silent:
                        print(f"⚠ Sync failed for batch of {len(batch)}. Retrying in {RETRY_DELAY}s...")
                    time.sleep(RETRY_DELAY)

    def save_cache_from_queue(self):
        """Save remaining queue to disk (approximate)"""
        try:
            items = list(self.data_queue.queue)
            with open(CACHE_FILE, 'w') as f:
                json.dump(items[-MAX_CACHE_SIZE:], f)
        except: pass

    def run(self):
        # Start sync thread
        self.sync_thread = threading.Thread(target=self.sync_offline_data, daemon=True)
        self.sync_thread.start()

        while self.running:
            data = self.collect_usage_data()
            if data:
                self.data_queue.put(data)
                # Backup to disk every 10 records
                if self.data_queue.qsize() % 10 == 0:
                    self.save_cache_from_queue()
            
            if not self.registered:
                self.register_unit()
                
            time.sleep(COLLECTION_INTERVAL)

    def stop(self):
        """Stop the client"""
        self.running = False
        if self.sync_thread:
            self.sync_thread.join(timeout=5)
        if not self.silent:
            print("Unit client stopped")

def install_service():
    """Install the client as a Windows background task"""
    if platform.system() != 'Windows':
        print("Service installation is only supported on Windows.")
        return

    script_path = os.path.abspath(__file__)
    python_exe = sys.executable
    task_name = "Sys_Logger_Client"
    
    # PowerShell command to create a scheduled task that runs on startup
    command = f'Register-ScheduledTask -TaskName "{task_name}" -Action (New-ScheduledTaskAction -Execute "{python_exe}" -Argument "{script_path} --silent") -Trigger (New-ScheduledTaskTrigger -AtStartup) -Settings (New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit 0) -User "SYSTEM" -RunLevel Highest -Force'
    
    try:
        subprocess.check_call(["powershell", "-Command", command])
        print(f"✓ Background service '{task_name}' installed successfully.")
        print("It will now start automatically with Windows.")
    except subprocess.CalledProcessError as e:
        print(f"FAILED to install service: {e}")
        print("Try running this command in an Administrator terminal.")

def main():
    is_silent = "--silent" in sys.argv
    if "--install-service" in sys.argv:
        install_service()
    else:
        client = UnitClient(silent=is_silent)
        print("Running unit client. Press Ctrl+C to stop.")
        try:
            client.run()
        except KeyboardInterrupt:
            print("\nStopping...")
            client.stop()

if __name__ == "__main__":
    main()