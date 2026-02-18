
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Default Credentials
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASS = os.getenv('DB_PASS', 'postgres')
DB_NAME = os.getenv('DB_NAME', 'sys_logger')

def create_database():
    try:
        # Connect to default 'postgres' db to create new db
        conn = psycopg2.connect(host=DB_HOST, user=DB_USER, password=DB_PASS, dbname='postgres')
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        
        # Check if exists
        cur.execute(f"SELECT 1 FROM pg_catalog.pg_database WHERE datname = '{DB_NAME}'")
        exists = cur.fetchone()
        
        if not exists:
            print(f"DTO creating database {DB_NAME}...")
            cur.execute(f"CREATE DATABASE {DB_NAME}")
            print("Database created successfully.")
        else:
            print(f"Database {DB_NAME} already exists.")
            
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Error creating database: {e}")
        return False

def apply_schema():
    try:
        conn = psycopg2.connect(host=DB_HOST, user=DB_USER, password=DB_PASS, dbname=DB_NAME)
        conn.autocommit = True
        cur = conn.cursor()
        
        with open('database_schema.sql', 'r') as f:
            schema_sql = f.read()
            
        print("Applying schema...")
        cur.execute(schema_sql)
        print("Schema applied successfully.")
        
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Error applying schema: {e}")
        return False

if __name__ == "__main__":
    if create_database():
        apply_schema()
