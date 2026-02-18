
import psycopg2
from psycopg2.extras import RealDictCursor
import os
import json
from datetime import datetime
import uuid

# DB Config
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASS = os.getenv('DB_PASS', 'postgres')
DB_NAME = 'sys_logger'

def check_db():
    print(f"Connecting to {DB_NAME} at {DB_HOST}...")
    try:
        conn = psycopg2.connect(host=DB_HOST, user=DB_USER, password=DB_PASS, dbname=DB_NAME)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        print("✓ Connection Successful")
        
        # 1. Check Tables
        cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")
        tables = [r['table_name'] for r in cur.fetchall()]
        if 'systems' in tables and 'system_metrics' in tables:
            print("✓ Tables 'systems' and 'system_metrics' found")
        else:
            print(f"❌ Missing tables: Found {tables}")
            return

        # 2. Check UUID Column
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='systems' AND column_name='system_uuid'")
        if cur.fetchone():
            print("✓ Column 'system_uuid' found in 'systems'")
        else:
            print("❌ Column 'system_uuid' MISSING in 'systems'")
            return

        # 3. Test Write/Read with UUID
        test_uuid = str(uuid.uuid4())
        test_name = f"test_unit_{test_uuid[:8]}"
        
        print(f"Testing Write for {test_name}...")
        cur.execute("""
            INSERT INTO systems (system_name, system_uuid, hostname, last_seen)
            VALUES (%s, %s, 'test_host', NOW())
            RETURNING system_id
        """, (test_name, test_uuid))
        sys_id = cur.fetchone()['system_id']
        conn.commit()
        print(f"✓ Inserted System ID: {sys_id}")
        
        # 4. Read Back
        cur.execute("SELECT * FROM systems WHERE system_id = %s", (sys_id,))
        row = cur.fetchone()
        print(f"Read Back: {dict(row)}")
        
        if str(row['system_uuid']) == test_uuid:
             print("✓ UUID Verification Passed")
        else:
             print(f"❌ UUID Mismatch: {row['system_uuid']} != {test_uuid}")

        # Clean up
        cur.execute("DELETE FROM systems WHERE system_id = %s", (sys_id,))
        conn.commit()
        print("✓ Test Data Cleaned")

        cur.close()
        conn.close()
        
    except psycopg2.OperationalError as e:
        print(f"❌ Connection Failed: {e}")
        print("Is PostgreSQL running? Check your service.")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_db()
