import psycopg2
import os
from dotenv import load_dotenv

def migrate():
    load_dotenv()
    
    # Defaults based on sys_logger.py
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_USER = os.getenv('DB_USER', 'postgres')
    DB_PASS = os.getenv('DB_PASS', 'postgres')
    DB_NAME = os.getenv('DB_NAME', 'sys_logger')
    DATABASE_URL = os.getenv('DATABASE_URL')

    try:
        if DATABASE_URL:
            conn = psycopg2.connect(DATABASE_URL)
        else:
            conn = psycopg2.connect(host=DB_HOST, user=DB_USER, password=DB_PASS, dbname=DB_NAME)
        
        conn.autocommit = True
        cur = conn.cursor()
        
        print(f"Connecting to {DB_NAME}...")
        
        # Check if column exists
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='systems' AND column_name='install_token';
        """)
        
        if not cur.fetchone():
            print("Adding 'install_token' column to 'systems' table...")
            cur.execute("ALTER TABLE systems ADD COLUMN install_token VARCHAR(64);")
            print("Successfully added 'install_token'.")
        else:
            print("Column 'install_token' already exists.")
            
        cur.close()
        conn.close()
        print("Migration complete.")
    except Exception as e:
        print(f"Error during migration: {e}")
        exit(1)

if __name__ == "__main__":
    migrate()
