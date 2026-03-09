
import psycopg2
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASS = os.getenv('DB_PASS', 'postgres')
DB_NAME = os.getenv('DB_NAME', 'sys_logger')

def migrate():
    try:
        conn = psycopg2.connect(host=DB_HOST, user=DB_USER, password=DB_PASS, dbname=DB_NAME)
        conn.autocommit = True
        cur = conn.cursor()
        
        print(f"Modifying 'hostname' column in 'systems' table to allow NULL...")
        cur.execute("ALTER TABLE systems ALTER COLUMN hostname DROP NOT NULL;")
        
        print("Schema update complete.")
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Error during migration: {e}")
        return False

if __name__ == "__main__":
    migrate()
