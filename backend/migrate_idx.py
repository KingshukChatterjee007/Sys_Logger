import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def migrate():
    try:
        conn = psycopg2.connect(
            dbname=os.getenv('DB_NAME', 'sys_logger'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASS', 'postgres'),
            host=os.getenv('DB_HOST', 'localhost'),
            port=os.getenv('DB_PORT', '5432')
        )
        cur = conn.cursor()
        
        print("Dropping unique index idx_systems_hostname...")
        cur.execute("DROP INDEX IF EXISTS idx_systems_hostname;")
        
        conn.commit()
        print("✓ Migration successful.")
        
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Migration failed: {e}")

if __name__ == "__main__":
    migrate()
