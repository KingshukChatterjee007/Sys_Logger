
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASS = os.getenv('DB_PASS', 'postgres')
DB_NAME = os.getenv('DB_NAME', 'sys_logger')

def check_schema():
    try:
        conn = psycopg2.connect(host=DB_HOST, user=DB_USER, password=DB_PASS, dbname=DB_NAME)
        cur = conn.cursor()
        
        # Check nullability of hostname
        cur.execute("""
            SELECT column_name, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_name = 'systems' AND column_name = 'hostname';
        """)
        row = cur.fetchone()
        print(f"DEBUG: Hostname column info: {row}")
        
        # Check all columns in systems
        cur.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'systems'
            ORDER BY ordinal_position;
        """)
        columns = cur.fetchall()
        print("DEBUG: All columns in 'systems':")
        for col in columns:
            print(f"  {col}")
            
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error checking schema: {e}")

if __name__ == "__main__":
    check_schema()
