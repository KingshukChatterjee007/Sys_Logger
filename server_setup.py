#!/usr/bin/env python3
"""
Unified Server Setup Script for Sys_Logger
- Prefer PostgreSQL (full schema with partitions + functions)
- Fallback to SQLite automatically if PostgreSQL is unavailable
"""

import os
import sys
import platform
import subprocess
import sqlite3
from pathlib import Path
import requests
import time

# Optional PostgreSQL
try:
    import psycopg2
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
    PG_AVAILABLE = True
except ImportError:
    PG_AVAILABLE = False


PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / "data"
SQLITE_DB = DATA_DIR / "sys_logger.db"

POSTGRES_DBNAME = "sys_logger"
POSTGRES_USER = "syslogger"
POSTGRES_PASS = "syslogger123"
POSTGRES_HOST = "localhost"


# -----------------------------------------------------------
# UTILITY
# -----------------------------------------------------------
def run_cmd(cmd):
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode == 0, result.stdout.strip()
    except Exception as e:
        return False, str(e)


# -----------------------------------------------------------
# CHECK POSTGRES AVAILABILITY
# -----------------------------------------------------------
def postgres_running():
    ok, _ = run_cmd(["pg_isready"])
    return ok


def connect_postgres(db=None):
    try:
        conn = psycopg2.connect(
            dbname=db or "postgres",
            user="postgres",
            password="",
            host=POSTGRES_HOST
        )
        return conn
    except:
        return None


# ---------------------------------------------------------
# CREATE POSTGRES DATABASE + USER
# ---------------------------------------------------------
def setup_postgres_database():
    print("➡ Checking PostgreSQL...")

    # must be installed + running
    
    if not postgres_running():
        print("❌ PostgreSQL is not running.")
        return False

    # connect to postgres
    conn = connect_postgres()
    if conn is None:
        print("❌ Unable to connect to PostgreSQL.")
        return False

    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()

    # create DB if missing
    cur.execute("SELECT 1 FROM pg_database WHERE datname=%s", (POSTGRES_DBNAME,))
    if not cur.fetchone():
        print("➡ Creating database sys_logger...")
        cur.execute(f"CREATE DATABASE {POSTGRES_DBNAME}")

    # create role
    cur.execute("""
    DO $$
    BEGIN
        IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname=%s) THEN
            CREATE ROLE syslogger LOGIN PASSWORD %s;
        END IF;
    END$$;
    """, (POSTGRES_USER, POSTGRES_PASS))

    conn.close()
    return True


# -----------------------------------------------------------
# APPLY FULL POSTGRES SCHEMA
# -----------------------------------------------------------
FULL_POSTGRES_SCHEMA = """
-- SYSTEMS TABLE
CREATE TABLE IF NOT EXISTS systems (
    system_id SERIAL PRIMARY KEY,
    system_name VARCHAR(255) NOT NULL UNIQUE,
    hostname VARCHAR(255) NOT NULL,
    ip_address INET,
    os VARCHAR(100),
    os_version VARCHAR(50),
    cpu_model VARCHAR(255),
    ram_gb DECIMAL(10,2),
    gpu_model VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_seen TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_systems_hostname ON systems(hostname);
CREATE INDEX IF NOT EXISTS idx_systems_active_last_seen ON systems(is_active, last_seen);

-- SYSTEM METRICS PARTITIONED TABLE
CREATE TABLE IF NOT EXISTS system_metrics (
    metric_id BIGSERIAL,
    system_id INTEGER NOT NULL REFERENCES systems(system_id),
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    cpu_usage DECIMAL(5,2) CHECK (cpu_usage >= 0 AND cpu_usage <= 100),
    ram_usage DECIMAL(5,2) CHECK (ram_usage >= 0 AND ram_usage <= 100),
    gpu_usage DECIMAL(5,2) CHECK (gpu_usage >= 0 AND gpu_usage <= 100),
    temperature DECIMAL(5,2),
    network_rx_mb DECIMAL(12,2),
    network_tx_mb DECIMAL(12,2),
    PRIMARY KEY (metric_id, timestamp)
) PARTITION BY RANGE (timestamp);

-- FUNCTION: Monthly partition creation
CREATE OR REPLACE FUNCTION create_system_metrics_partition(target_date DATE)
RETURNS VOID AS $$
DECLARE
    p_name TEXT;
    start_date DATE;
    end_date DATE;
BEGIN
    start_date := DATE_TRUNC('month', target_date);
    end_date := start_date + INTERVAL '1 month';

    p_name := 'system_metrics_y' || EXTRACT(YEAR FROM start_date)
           || 'm' || LPAD(EXTRACT(MONTH FROM start_date)::TEXT, 2, '0');

    EXECUTE FORMAT(
        'CREATE TABLE IF NOT EXISTS %I PARTITION OF system_metrics FOR VALUES FROM (%L) TO (%L)',
        p_name, start_date, end_date
    );
END;
$$ LANGUAGE plpgsql;

SELECT create_system_metrics_partition(CURRENT_DATE);

-- Indexes for partitioned table
CREATE INDEX IF NOT EXISTS idx_system_metrics_system_timestamp ON system_metrics(system_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_system_metrics_timestamp ON system_metrics(timestamp);

-- AGGREGATED METRICS
CREATE TABLE IF NOT EXISTS aggregated_metrics (
    agg_id BIGSERIAL PRIMARY KEY,
    system_id INTEGER NOT NULL REFERENCES systems(system_id),
    period_start TIMESTAMP WITH TIME ZONE NOT NULL,
    period_end TIMESTAMP WITH TIME ZONE NOT NULL,
    period_type VARCHAR(10) CHECK (period_type IN ('hourly', 'daily')),
    avg_cpu_usage DECIMAL(5,2),
    avg_ram_usage DECIMAL(5,2),
    avg_gpu_usage DECIMAL(5,2),
    avg_temperature DECIMAL(5,2),
    total_network_rx_mb DECIMAL(12,2),
    total_network_tx_mb DECIMAL(12,2),
    data_points INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_aggregated_metrics_unique
ON aggregated_metrics(system_id, period_start, period_type);

CREATE INDEX IF NOT EXISTS idx_aggregated_metrics_system_period
ON aggregated_metrics(system_id, period_type, period_start DESC);

-- DAILY AGGREGATION
CREATE OR REPLACE FUNCTION aggregate_daily_metrics(target_date DATE DEFAULT CURRENT_DATE - INTERVAL '1 day')
RETURNS VOID AS $$
BEGIN
    -- HOURLY
    INSERT INTO aggregated_metrics (
        system_id, period_start, period_end, period_type,
        avg_cpu_usage, avg_ram_usage, avg_gpu_usage, avg_temperature,
        total_network_rx_mb, total_network_tx_mb, data_points
    )
    SELECT system_id,
           DATE_TRUNC('hour', timestamp),
           DATE_TRUNC('hour', timestamp) + INTERVAL '1 hour',
           'hourly',
           AVG(cpu_usage), AVG(ram_usage), AVG(gpu_usage), AVG(temperature),
           SUM(network_rx_mb), SUM(network_tx_mb), COUNT(*)
    FROM system_metrics
    WHERE DATE(timestamp) = target_date
    GROUP BY system_id, DATE_TRUNC('hour', timestamp)
    ON CONFLICT (system_id, period_start, period_type)
    DO UPDATE SET
        avg_cpu_usage = EXCLUDED.avg_cpu_usage,
        avg_ram_usage = EXCLUDED.avg_ram_usage,
        avg_gpu_usage = EXCLUDED.avg_gpu_usage,
        avg_temperature = EXCLUDED.avg_temperature,
        total_network_rx_mb = EXCLUDED.total_network_rx_mb,
        total_network_tx_mb = EXCLUDED.total_network_tx_mb,
        data_points = EXCLUDED.data_points;

    -- DAILY
    INSERT INTO aggregated_metrics (
        system_id, period_start, period_end, period_type,
        avg_cpu_usage, avg_ram_usage, avg_gpu_usage, avg_temperature,
        total_network_rx_mb, total_network_tx_mb, data_points
    )
    SELECT system_id,
           DATE_TRUNC('day', timestamp),
           DATE_TRUNC('day', timestamp) + INTERVAL '1 day',
           'daily',
           AVG(cpu_usage), AVG(ram_usage), AVG(gpu_usage), AVG(temperature),
           SUM(network_rx_mb), SUM(network_tx_mb), COUNT(*)
    FROM system_metrics
    WHERE DATE(timestamp) = target_date
    GROUP BY system_id, DATE_TRUNC('day', timestamp)
    ON CONFLICT (system_id, period_start, period_type)
    DO UPDATE SET
        avg_cpu_usage = EXCLUDED.avg_cpu_usage,
        avg_ram_usage = EXCLUDED.avg_ram_usage,
        avg_gpu_usage = EXCLUDED.avg_gpu_usage,
        avg_temperature = EXCLUDED.avg_temperature,
        total_network_rx_mb = EXCLUDED.total_network_rx_mb,
        total_network_tx_mb = EXCLUDED.total_network_tx_mb,
        data_points = EXCLUDED.data_points;
END;
$$ LANGUAGE plpgsql;

-- CLEANUP OLD PARTITIONS (> 30 DAYS)
CREATE OR REPLACE FUNCTION cleanup_old_partitions()
RETURNS VOID AS $$
DECLARE
    cutoff DATE := CURRENT_DATE - INTERVAL '30 days';
    rec RECORD;
BEGIN
    FOR rec IN
        SELECT tablename FROM pg_tables
        WHERE tablename LIKE 'system_metrics_y%m__'
    LOOP
        EXECUTE FORMAT('DROP TABLE IF EXISTS %I', rec.tablename);
    END LOOP;
END;
$$ LANGUAGE plpgsql;
"""


def apply_postgres_schema():
    print("➡ Applying PostgreSQL schema...")

    try:
        conn = psycopg2.connect(
            dbname=POSTGRES_DBNAME,
            user=POSTGRES_USER,
            password=POSTGRES_PASS,
            host=POSTGRES_HOST,
        )
        cur = conn.cursor()
        cur.execute(FULL_POSTGRES_SCHEMA)
        conn.commit()
        conn.close()
        print("✅ PostgreSQL schema applied successfully")
        return True

    except Exception as e:
        print(f"❌ PostgreSQL schema failed: {e}")
        return False


# -----------------------------------------------------------
# SQLITE FALLBACK
# -----------------------------------------------------------
SQLITE_SCHEMA = """
CREATE TABLE IF NOT EXISTS systems (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    system_name TEXT UNIQUE,
    hostname TEXT NOT NULL,
    ip_address TEXT,
    os TEXT,
    os_version TEXT,
    cpu_model TEXT,
    ram_gb REAL,
    gpu_model TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    last_seen TEXT DEFAULT CURRENT_TIMESTAMP,
    is_active INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS system_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    system_id INTEGER,
    timestamp TEXT,
    cpu_usage REAL,
    ram_usage REAL,
    gpu_usage REAL,
    temperature REAL,
    network_rx_mb REAL,
    network_tx_mb REAL,
    FOREIGN KEY(system_id) REFERENCES systems(id)
);

CREATE TABLE IF NOT EXISTS aggregated_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    system_id INTEGER,
    period_start TEXT,
    period_end TEXT,
    period_type TEXT,
    avg_cpu_usage REAL,
    avg_ram_usage REAL,
    avg_gpu_usage REAL,
    avg_temperature REAL,
    total_network_rx_mb REAL,
    total_network_tx_mb REAL,
    data_points INTEGER,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(system_id) REFERENCES systems(id)
);
"""

def setup_sqlite():
    print("➡ Using SQLite fallback...")
    DATA_DIR.mkdir(exist_ok=True)

    conn = sqlite3.connect(SQLITE_DB)
    cur = conn.cursor()
    cur.executescript(SQLITE_SCHEMA)
    conn.commit()
    conn.close()

    print(f"✅ SQLite database ready: {SQLITE_DB}")


# -----------------------------------------------------------
# MAIN LOGIC
# -----------------------------------------------------------

def setup_windows_service():
    """Install Sys_Logger Server as a Windows Service using NSSM"""
    print("\n➡ Installing Windows Service...")
    
    if platform.system() != 'Windows':
        print("❌ Service installation is only supported on Windows.")
        return

    # Check for Admin privileges
    try:
        is_admin = os.getuid() == 0
    except AttributeError:
        import ctypes
        is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0

    if not is_admin:
        print("❌ Admin privileges required. Please run this script as Administrator.")
        return

    # Helper Paths
    nssm_path = PROJECT_ROOT / "nssm.exe"
    python_exe = sys.executable
    server_script = PROJECT_ROOT / "backend" / "sys_logger.py"
    service_name = "Sys_Logger_Server"

    # Download NSSM if missing
    if not nssm_path.exists():
        print("⬇ Downloading NSSM (Service Manager)...")
        # Reuse logic from create_service.ps1 but in Python or just rely on powershell
        # For simplicity, let's use a PowerShell one-liner to download/extract if needed
        # Or better, just instruct user or bundling it. 
        # Actually, let's use the explicit powershell command to download it blindly if missing
        ps_download = f"""
        $Url = "https://nssm.cc/release/nssm-2.24.zip"
        $Zip = "{PROJECT_ROOT}\\nssm.zip"
        $Dest = "{PROJECT_ROOT}\\nssm-temp"
        Invoke-WebRequest -Uri $Url -OutFile $Zip
        Expand-Archive -Path $Zip -DestinationPath $Dest
        Copy-Item "$Dest\\nssm-2.24\\win64\\nssm.exe" "{nssm_path}"
        Remove-Item $Zip
        Remove-Item $Dest -Recurse
        """
        try:
            subprocess.run(["powershell", "-Command", ps_download], check=True)
        except Exception as e:
            print(f"❌ Failed to download NSSM: {e}")
            return

    print(f"➡ Registering Service: {service_name}...")
    
    # NSSM Commands
    commands = [
        f'{nssm_path} install {service_name} "{python_exe}" "{server_script}"',
        f'{nssm_path} set {service_name} AppDirectory "{PROJECT_ROOT}"',
        f'{nssm_path} set {service_name} Description "Sys_Logger Backend Server"',
        f'{nssm_path} set {service_name} DisplayName "Sys_Logger Server"',
        f'{nssm_path} set {service_name} Start SERVICE_AUTO_START',
        f'{nssm_path} set {service_name} AppExit Default Restart',
        f'{nssm_path} set {service_name} AppRestartDelay 5000',
        f'{nssm_path} set {service_name} AppStdout "{PROJECT_ROOT}\\server_log.txt"',
        f'{nssm_path} set {service_name} AppStderr "{PROJECT_ROOT}\\server_error.log"'
    ]

    for cmd in commands:
        try:
            subprocess.run(cmd, check=True, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except subprocess.CalledProcessError:
            print(f"⚠ Warning: specific NSSM command failed or service already exists. Continuing...")

    print("➡ Starting Service...")
    subprocess.run(f'{nssm_path} start {service_name}', shell=True)
    
    print(f"✅ Service '{service_name}' installed and started!")
    print("   Run 'services.msc' to verify.")


def main():
    print("\n=== Sys_Logger Server Setup ===\n")

    # 1. Database Setup
    if PG_AVAILABLE and postgres_running() and setup_postgres_database():
        if apply_postgres_schema():
            print("🎉 Database: PostgreSQL")
        else:
            print("⚠ Database: SQLite (PostgreSQL schema failed)")
            setup_sqlite()
    else:
        print("⚠ Database: SQLite (PostgreSQL unavailable)")
        setup_sqlite()

    # 2. Service Installation Prompt
    print("\n--- Production Setup ---")
    ask = input("Install as persistent Windows Service? (y/n): ").lower().strip()
    if ask == 'y':
        setup_windows_service()

    print("\nSetup complete.\n")


if __name__ == "__main__":
    main()