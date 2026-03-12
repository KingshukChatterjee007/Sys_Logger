import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def list_orgs():
    try:
        conn = psycopg2.connect(
            dbname=os.getenv('DB_NAME', 'sys_logger'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASS', 'postgres'),
            host=os.getenv('DB_HOST', 'localhost'),
            port=os.getenv('DB_PORT', '5432')
        )
        cur = conn.cursor()
        cur.execute("SELECT org_id, name, slug, tier FROM organizations ORDER BY org_id")
        rows = cur.fetchall()
        
        print(f"TOTAL ORGS: {len(rows)}")
        for r in rows:
            print(f"#{r[0]} | {r[1]} | {r[2]} | {r[3]}")
            
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    list_orgs()
