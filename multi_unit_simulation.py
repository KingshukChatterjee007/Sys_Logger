import threading
import time
import random
import requests
import uuid
from datetime import datetime

# Configuration
SERVER_URL = 'http://localhost:5000'
NUM_UNITS = 5
SUBMISSION_INTERVAL = 10  # seconds

# Unit profiles with different usage patterns
UNIT_PROFILES = [
    {
        'name': 'Workstation',
        'cpu_base': 15,
        'cpu_var': 10,
        'ram_base': 60,
        'ram_var': 15,
        'gpu_base': 5,
        'gpu_var': 5,
        'temp_base': 45,
        'temp_var': 5,
        'hostname': 'WS-001'
    },
    {
        'name': 'GamingPC',
        'cpu_base': 25,
        'cpu_var': 20,
        'ram_base': 70,
        'ram_var': 20,
        'gpu_base': 80,
        'gpu_var': 15,
        'temp_base': 60,
        'temp_var': 10,
        'hostname': 'GAMING-001'
    },
    {
        'name': 'Server',
        'cpu_base': 30,
        'cpu_var': 25,
        'ram_base': 80,
        'ram_var': 10,
        'gpu_base': 10,
        'gpu_var': 5,
        'temp_base': 50,
        'temp_var': 8,
        'hostname': 'SRV-001'
    },
    {
        'name': 'Laptop',
        'cpu_base': 10,
        'cpu_var': 15,
        'ram_base': 50,
        'ram_var': 20,
        'gpu_base': 0,
        'gpu_var': 2,
        'temp_base': 40,
        'temp_var': 6,
        'hostname': 'LT-001'
    },
    {
        'name': 'DevMachine',
        'cpu_base': 20,
        'cpu_var': 25,
        'ram_base': 65,
        'ram_var': 25,
        'gpu_base': 15,
        'gpu_var': 10,
        'temp_base': 48,
        'temp_var': 7,
        'hostname': 'DEV-001'
    }
]

class SimulatedUnit:
    def __init__(self, profile):
        self.system_id = str(uuid.uuid4())
        self.profile = profile
        self.unit_id = None
        self.registered = False
        self.running = True

    def register(self):
        """Register this unit with the server"""
        if self.registered:
            return True

        registration_data = {
            'system_id': self.system_id,
            'hostname': self.profile['hostname'],
            'os_info': f"Windows 11 {self.profile['name']}",
            'cpu_info': f"Intel Core i7-12700K ({self.profile['name']})",
            'ram_total': 16.0 + random.uniform(-2, 2),  # 14-18 GB
            'gpu_info': '{"count": 1, "details": [{"name": "NVIDIA RTX 3060", "memory": 12288}]}' if self.profile['gpu_base'] > 0 else '{"count": 0, "details": []}',
            'network_interfaces': '{"Ethernet": ["192.168.1.100"], "WiFi": ["192.168.1.101"]}'
        }

        try:
            response = requests.post(f"{SERVER_URL}/api/register_unit", json=registration_data, timeout=10)
            if response.status_code in [200, 201]:
                data = response.json()
                self.unit_id = data.get('unit_id')
                self.registered = True
                print(f"✓ {self.profile['name']} registered successfully as unit {self.unit_id}")
                return True
            else:
                print(f"✗ {self.profile['name']} registration failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"✗ {self.profile['name']} registration error: {e}")
            return False

    def generate_usage_data(self):
        """Generate realistic usage data based on profile"""
        cpu = max(0, min(100, self.profile['cpu_base'] + random.uniform(-self.profile['cpu_var'], self.profile['cpu_var'])))
        ram = max(0, min(100, self.profile['ram_base'] + random.uniform(-self.profile['ram_var'], self.profile['ram_var'])))
        gpu = max(0, min(100, self.profile['gpu_base'] + random.uniform(-self.profile['gpu_var'], self.profile['gpu_var'])))
        temp = max(30, min(90, self.profile['temp_base'] + random.uniform(-self.profile['temp_var'], self.profile['temp_var'])))

        # Add some spikes for realism
        if random.random() < 0.1:  # 10% chance of CPU spike
            cpu = min(100, cpu + random.uniform(10, 30))
        if random.random() < 0.05:  # 5% chance of RAM spike
            ram = min(100, ram + random.uniform(15, 25))

        return {
            'system_id': self.system_id,
            'timestamp': datetime.utcnow().isoformat(),
            'cpu_usage': round(cpu, 1),
            'ram_usage': round(ram, 1),
            'gpu_usage': round(gpu, 1),
            'temperature': round(temp, 1) if temp > 35 else None,
            'network_rx': random.uniform(100, 1000),  # KB/s
            'network_tx': random.uniform(50, 500)    # KB/s
        }

    def submit_data(self):
        """Submit usage data to server"""
        if not self.registered:
            if not self.register():
                return

        data = self.generate_usage_data()

        try:
            response = requests.post(f"{SERVER_URL}/api/submit_usage", json=data, timeout=10)
            if response.status_code == 200:
                print(f"✓ {self.profile['name']} ({self.unit_id}): CPU={data['cpu_usage']}%, RAM={data['ram_usage']}%, GPU={data['gpu_usage']}%")
            else:
                print(f"✗ {self.profile['name']} data submission failed: {response.status_code}")
        except Exception as e:
            print(f"✗ {self.profile['name']} submission error: {e}")

    def run(self):
        """Main loop for this unit"""
        print(f"Starting {self.profile['name']} simulation...")

        while self.running:
            self.submit_data()
            time.sleep(SUBMISSION_INTERVAL)

def main():
    print(f"🚀 Starting Sys_Logger Multi-Unit Simulation")
    print(f"📊 Simulating {NUM_UNITS} units with {SUBMISSION_INTERVAL}s intervals")
    print(f"🌐 Server: {SERVER_URL}")
    print("=" * 60)

    # Create and start unit threads
    units = []
    threads = []

    for i, profile in enumerate(UNIT_PROFILES[:NUM_UNITS]):
        unit = SimulatedUnit(profile)
        units.append(unit)

        thread = threading.Thread(target=unit.run, daemon=True)
        threads.append(thread)
        thread.start()

        # Stagger startup slightly
        time.sleep(0.5)

    print(f"\n✅ All {len(units)} units started successfully!")
    print("📈 Monitoring server logs and data submissions...\n")

    try:
        # Keep main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Stopping simulation...")
        for unit in units:
            unit.running = False

        for thread in threads:
            thread.join(timeout=2)

        print("✅ Simulation stopped.")

if __name__ == "__main__":
    main()