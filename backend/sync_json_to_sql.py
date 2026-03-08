import json
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASS = os.getenv('DB_PASS', 'postgres')
DB_NAME = 'sys_logger'

UNITS_DB_FILE = '../units_db.json'

def get_db_connection():
    return psycopg2.connect(host=DB_HOST, user=DB_USER, password=DB_PASS, dbname=DB_NAME)

def migrate():
    if not os.path.exists(UNITS_DB_FILE):
        print(f"No {UNITS_DB_FILE} found. Skipping migration.")
        return

    with open(UNITS_DB_FILE, 'r') as f:
        units = json.load(f)

    conn = get_db_connection()
    cur = conn.cursor()

    print(f"Migrating {len(units)} units...")

    for unit_id, unit in units.items():
        # Ensure org exists
        org_id = unit.get('org_id', 'TEST')
        cur.execute("INSERT INTO organizations (org_id, name) VALUES (%s, %s) ON CONFLICT (org_id) DO NOTHING", (org_id, org_id))

        # Validate UUID
        sys_uuid = unit.get('system_id')
        import uuid
        try:
            uuid.UUID(sys_uuid)
        except (ValueError, TypeError):
            sys_uuid = None # Skip if not a valid UUID for the UUID column

        # Insert or update system
        cur.execute("""
            INSERT INTO systems 
            (system_name, system_uuid, hostname, ip_address, os, ram_gb, org_id, last_seen)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (system_name) DO UPDATE SET
                system_uuid = COALESCE(EXCLUDED.system_uuid, systems.system_uuid),
                hostname = EXCLUDED.hostname,
                ip_address = EXCLUDED.ip_address,
                os = EXCLUDED.os,
                ram_gb = EXCLUDED.ram_gb,
                org_id = EXCLUDED.org_id,
                last_seen = EXCLUDED.last_seen
        """, (
            unit.get('name', f"{org_id}/{unit.get('comp_id', unit_id)}"),
            sys_uuid,
            unit.get('hostname', 'Unknown'),
            unit.get('ip'),
            unit.get('os_info'),
            unit.get('ram_total'),
            org_id,
            unit.get('last_seen')
        ))

    conn.commit()
    cur.close()
    conn.close()
    print("Migration complete!")

if __name__ == "__main__":
    migrate()
