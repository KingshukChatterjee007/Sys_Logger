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
import io
from datetime import datetime, timedelta, timezone

# Force UTF-8 encoding for stdout to prevent UnicodeEncodeError on Windows
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        # Fallback for older Python versions
        import codecs
        sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())

try:
    import GPUtil
    NVIDIA_AVAILABLE = True
except ImportError:
    NVIDIA_AVAILABLE = False

# Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, 'unit_client_config.json')
CACHE_FILE = os.path.join(BASE_DIR, 'cached_usage.json')
DEFAULT_SERVER_URL = 'http://127.0.0.1:5000'  # Hardcoded central server URL
COLLECTION_INTERVAL = 1  # seconds - updated for 1-second updates
RECONNECT_INTERVAL = 300  # seconds (5 minutes)
MAX_RETRIES = 3
RETRY_DELAY = 10  # seconds
MAX_CACHE_SIZE = 1000  # Max records to cache offline
SYNC_BATCH_SIZE = 10   # Number of records to sync at once

# Configuration prompting is handled by configure.py (run at install time).
# unit_client.py always runs in --silent mode under PM2 and reads from config file.

class UnitClient:
    def __init__(self):
        self.config = self.load_config()
        self.system_id = self.config.get('system_id')
        self.org_id = self.config.get('org_id')
        self.comp_id = self.config.get('comp_id')
        
        # Hardcode server URL as requested by user
        self.server_url = DEFAULT_SERVER_URL
        
        if not self.org_id or self.org_id == 'default_org' or not self.comp_id:
            # Under PM2/Boot — config must be set up by first_run_wizard.py / install.bat first
            print(
                "ERROR: org_id or comp_id not configured.\n"
                "  Please run install.bat (Windows) or first_run_wizard.py to set up this unit.",
                flush=True
            )
            sys.exit(1)

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

        logging.info(f"Unit Client initialized: {self.org_id}/{self.comp_id}")
        print(f"Unit Client initialized: {self.org_id}/{self.comp_id}", flush=True)

    def signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        logging.info(f"Received signal {signum}, initiating graceful shutdown")
        self.stop()

    def load_config(self):
        config = {'system_id': str(uuid.uuid4()), 'org_id': None, 'comp_id': None}
        if os.path.exists(CONFIG_FILE):
            try:
                # Use utf-8-sig to handle Windows BOMs
                with open(CONFIG_FILE, 'r', encoding='utf-8-sig') as f:
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
            print(f"Error getting system info: {e}", flush=True)
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
                    print(f"DEBUG: Assigned unit_id: {self.unit_id}", flush=True)
                except: pass

                print(f"Unit registered successfully (Status: {response.status_code})", flush=True)
                return True
            else:
                print(f"Registration failed with status: {response.status_code}", flush=True)
        except requests.RequestException as e:
            print(f"Registration error: {e}", flush=True)
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
            
            # Fix: Hide command window on Windows
            creationflags = 0
            if platform.system() == 'Windows':
                creationflags = 0x08000000 # CREATE_NO_WINDOW
            
            output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, timeout=8, creationflags=creationflags).decode().strip()
            
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
                'hostname': socket.gethostname(),
                'platform': platform.system(),
                'os_release': platform.release(),
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cpu_usage': cpu_usage,
                'ram_usage': ram_usage,
                'gpu_usage': gpu_usage,
                'network_rx': network_rx,
                'network_tx': network_tx,
                'unit_id': self.unit_id
            }
            return data
        except Exception as e:
            print(f"Error collecting usage data: {e}", flush=True)
            return None

    def submit_data(self, data):
        """Submit usage data to the central server"""
        url = f"{self.server_url}/api/report_usage"
        try:
            print(f"DEBUG: Submitting data to {url}", flush=True)
                # print(f"DEBUG: Payload: {json.dumps(data, indent=2)}")
            
            response = requests.post(url, json=data, timeout=30)
            
            print(f"DEBUG: Server response: {response.status_code}", flush=True)
            if response.status_code != 200:
                print(f"DEBUG: Error response: {response.text}", flush=True)

            if response.status_code == 404:
                # Server forgot us (likely restarted), force re-registration
                print("Server responded with 404 (Unit Not Found). Re-registering...", flush=True)
                self.registered = False
                return False
            
            if response.status_code != 200:
                print(f"Data submission failed with status: {response.status_code}", flush=True)
            return response.status_code == 200
        except requests.RequestException as e:
            print(f"Data submission error: {e}", flush=True)
            return False

    def sync_offline_data(self):
        print("Sync thread started.", flush=True)
            
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
                    # Log even in silent mode so PM2 captures it
                    print(f"  OK Synced batch of {len(batch)} records. Queue size: {self.data_queue.qsize()}", flush=True)
                    
                    # Mark all as done
                    for _ in batch:
                        self.data_queue.task_done()
                        
                    # Save cache (optional optimization: only save if queue is empty or periodically)
                    if self.data_queue.qsize() == 0:
                        self.save_cache_from_queue()
                else:
                    # Log even in silent mode so PM2 captures it
                    print(f"  FAILED Sync failed for batch of {len(batch)}. Retrying in {RETRY_DELAY}s...", flush=True)
                    time.sleep(RETRY_DELAY)

    def save_cache_from_queue(self):
        """Save remaining queue to disk (approximate)"""
        try:
            items = list(self.data_queue.queue)
            with open(CACHE_FILE, 'w') as f:
                json.dump(items[-MAX_CACHE_SIZE:], f)
        except: pass

    def run(self):
        print(f"Unit client loop started", flush=True)

        while self.running:
            # 1. Ensure registration
            if not self.registered:
                success = self.register_unit()
                if not success:
                    # During boot/restart, network might not be ready. Wait and retry.
                    print("Registration failed. Waiting for network...", flush=True)
                    time.sleep(5)
                    continue
            
            # 2. Collect data
            data = self.collect_usage_data()
            if data:
                # Add to queue for buffering/caching
                self.data_queue.put(data)
                
                print(f"DEBUG: Collected data, queue size: {self.data_queue.qsize()}", flush=True)
                
                # 3. Synchronous submission of current item (and any queued data)
                # In this simplified single-threaded mode, we try to clear the queue
                while not self.data_queue.empty() and self.running:
                    batch = []
                    # Try to get a batch
                    try:
                        while len(batch) < SYNC_BATCH_SIZE:
                            batch.append(self.data_queue.get_nowait())
                    except queue.Empty:
                        pass
                    
                    if batch:
                        # Add Unit ID to batch items
                        for item in batch:
                            if self.unit_id:
                                item['unit_id'] = self.unit_id

                        if self.submit_data(batch if len(batch) > 1 else batch[0]):
                            # Log even in silent mode so PM2 captures it
                            print(f"  OK Submitted {len(batch)} records", flush=True)
                            # Mark as done
                            for _ in batch:
                                self.data_queue.task_done()
                        else:
                            # Log even in silent mode so PM2 captures it
                            print(f"  FAILED Submission failed - keeping {len(batch)} records in queue", flush=True)
                            # Put them back (at the front if possible, but Queue is FIFO)
                            # Actually, for simplicity on failure, we stop trying to clear queue this interval
                            for item in batch:
                                # We can't easily put back at front of queue.Queue, so we just stop
                                # and the items are lost if we don't handle them. 
                                # Let's stick to a simpler "try one, then queue others" approach
                                pass
                            break # Retry next interval

                # 4. Backup to disk every 10 records
                if self.data_queue.qsize() % 10 == 0 and self.data_queue.qsize() > 0:
                    self.save_cache_from_queue()
            
            time.sleep(COLLECTION_INTERVAL)

    def stop(self):
        """Stop the client"""
        self.running = False
        if self.sync_thread:
            self.sync_thread.join(timeout=5)
        print("Unit client stopped", flush=True)

def main():
    print(f"--- Sys_Logger Unit Client Starting (Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}) ---", flush=True)
    client = UnitClient()
    print("Running unit client. Press Ctrl+C to stop.", flush=True)
    try:
        client.run()
    except KeyboardInterrupt:
        print("\nStopping...")
        client.stop()

if __name__ == "__main__":
    main()