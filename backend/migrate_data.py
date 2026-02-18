
import os
import json
import psycopg2
from datetime import datetime

# DB Config
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASS = os.getenv('DB_PASS', 'postgres')
DB_NAME = 'sys_logger'

DATA_DIR = 'unit_data'

def migrate():
    print("Starting JSONL -> Postgres Migration...")
    
    try:
        conn = psycopg2.connect(host=DB_HOST, user=DB_USER, password=DB_PASS, dbname=DB_NAME)
        cur = conn.cursor()
    except Exception as e:
        print(f"Failed to connect to DB: {e}")
        return

    # iterate over all jsonl files
    if not os.path.exists(DATA_DIR):
        print("No unit_data directory found.")
        return
        
    # CLEAR EXISTING DATA to avoid Duplicates/Bad Data
    print("Clearing old DB data...")
    cur.execute("TRUNCATE systems, system_metrics RESTART IDENTITY CASCADE;")
    conn.commit()

    files = [f for f in os.listdir(DATA_DIR) if f.endswith('.jsonl')]
    print(f"Found {len(files)} log files.")

    total_records = 0
    
    for filename in files:
        unit_id = filename.replace('.jsonl', '')
        filepath = os.path.join(DATA_DIR, filename)
        
        print(f"Processing {unit_id}...")
        
        batch = []
        with open(filepath, 'r') as f:
            for line in f:
                try:
                    record = json.loads(line)
                    
                    sys_id_uuid = record.get('system_id')
                    timestamp = record.get('timestamp')
                    if timestamp.endswith('Z'): timestamp = timestamp[:-1]
                    
                    # 2. Insert Metric
                    # Use unit_id from filename as system_name to match backend logic
                    system_name = unit_id
                    hostname = "legacy_import"
                    
                    cur.execute("""
                        INSERT INTO systems (system_name, hostname, last_seen)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (system_name) DO UPDATE SET last_seen = EXCLUDED.last_seen
                        RETURNING system_id
                    """, (system_name, hostname, timestamp))
                    
                    sys_int_id = cur.fetchone()[0]
                    
                    # Prepare Metric Data
                    cpu = record.get('cpu', record.get('cpu_usage', 0))
                    ram = record.get('ram', record.get('ram_usage', 0))
                    gpu = 0
                    if record.get('gpu_load') is not None: gpu = record.get('gpu_load')
                    elif record.get('gpu_usage') is not None: gpu = record.get('gpu_usage')
                    
                    net_rx = record.get('network_rx', 0)
                    net_tx = record.get('network_tx', 0)
                    
                    cur.execute("""
                        INSERT INTO system_metrics 
                        (system_id, timestamp, cpu_usage, ram_usage, gpu_usage, network_rx_mb, network_tx_mb)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT DO NOTHING
                    """, (sys_int_id, timestamp, cpu, ram, gpu, net_rx, net_tx))
                    
                    total_records += 1
                    
                except Exception as e:
                    # print(f"Skipping bad line: {e}")
                    pass
        
        conn.commit()
        print(f"  > Imported logs for {unit_id}")

    print(f"Migration Complete. Imported {total_records} records.")
    cur.close()
    conn.close()

if __name__ == "__main__":
    migrate()
