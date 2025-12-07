#!/usr/bin/env python3
"""
Unified Server Setup GUI for Sys_Logger
- GUI with options for PostgreSQL or SQLite setup
- Prefer PostgreSQL (full schema with partitions + functions)
- Fallback to SQLite
"""

import os
import sys
import platform
import subprocess
import sqlite3
from pathlib import Path
import requests
import time
import threading
import tkinter as tk
from tkinter import ttk, messagebox
import zipfile
import tempfile
import urllib.request
import urllib.error
import tarfile
import shutil

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

# Ngrok configuration
NGROK_AUTH_TOKEN = ""
NGROK_PORT = 8000  # Default port for the server
NGROK_EXE_PATH = PROJECT_ROOT / "ngrok"  # Path to ngrok executable

FOOTER_TEXT = "Product of NIELIT Bhubaneswar - Made by Krishi Sahayogi Team"

ASCII_ART = """
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║                    SysLogger Server Setup                    ║
║                                                              ║
║                 🖥️ Database Configuration Tool               ║
║                                                              ║
║  Choose your database:                                       ║
║  • PostgreSQL (Full-featured, recommended)                   ║
║  • SQLite (Simple, no installation required)                 ║
║                                                              ║
║  Optional: Enable ngrok for remote access                    ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
"""

# -----------------------------------------------------------
# NGROK UTILITIES
# -----------------------------------------------------------


def check_ngrok_installed():
    """Check if ngrok is installed and accessible."""
    try:
        result = subprocess.run([str(NGROK_EXE_PATH), "version"], capture_output=True, text=True)
        return result.returncode == 0
    except (FileNotFoundError, subprocess.SubprocessError):
        return False


def download_ngrok():
    """Download and install ngrok binary for the current platform."""
    system = platform.system().lower()
    machine = platform.machine().lower()

    # Determine ngrok download URL based on platform
    if system == "windows":
        if "64" in machine or "amd64" in machine:
            ngrok_url = "https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-windows-amd64.zip"
        else:
            ngrok_url = "https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-windows-386.zip"
        exe_name = "ngrok.exe"
    elif system == "linux":
        if "arm64" in machine or "aarch64" in machine:
            ngrok_url = "https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-arm64.tgz"
        elif "64" in machine or "amd64" in machine:
            ngrok_url = "https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.tgz"
        else:
            ngrok_url = "https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-386.tgz"
        exe_name = "ngrok"
    elif system == "darwin":  # macOS
        if "arm64" in machine:
            ngrok_url = "https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-darwin-arm64.zip"
        else:
            ngrok_url = "https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-darwin-amd64.zip"
        exe_name = "ngrok"
    else:
        raise Exception(f"Unsupported platform: {system} {machine}")

    try:
        print(f"📥 Downloading ngrok from {ngrok_url}...")
        response = requests.get(ngrok_url, stream=True)
        response.raise_for_status()

        # Create temporary file for download
        with tempfile.NamedTemporaryFile(delete=False, suffix=".zip" if ngrok_url.endswith(".zip") else ".tgz") as temp_file:
            for chunk in response.iter_content(chunk_size=8192):
                temp_file.write(chunk)
            temp_path = temp_file.name

        # Extract the archive
        print("📦 Extracting ngrok...")
        if ngrok_url.endswith(".zip"):
            with zipfile.ZipFile(temp_path, 'r') as zip_ref:
                zip_ref.extractall(PROJECT_ROOT)
        else:  # .tgz
            import tarfile
            with tarfile.open(temp_path, 'r:gz') as tar_ref:
                tar_ref.extractall(PROJECT_ROOT)

        # Move the executable to the expected location
        extracted_exe = PROJECT_ROOT / exe_name
        if extracted_exe.exists():
            extracted_exe.replace(NGROK_EXE_PATH)
        else:
            # Look for it in subdirectories
            for file in PROJECT_ROOT.rglob(exe_name):
                file.replace(NGROK_EXE_PATH)
                break

        # Make executable on Unix systems
        if system != "windows":
            NGROK_EXE_PATH.chmod(0o755)

        # Clean up temp file
        Path(temp_path).unlink(missing_ok=True)

        print(f"✅ Ngrok installed successfully at {NGROK_EXE_PATH}")
        return True

    except Exception as e:
        print(f"❌ Failed to download/install ngrok: {e}")
        return False


def set_ngrok_auth_token(token):
    """Set ngrok authentication token."""
    global NGROK_AUTH_TOKEN
    NGROK_AUTH_TOKEN = token
    try:
        result = subprocess.run([str(NGROK_EXE_PATH), "config", "add-authtoken", token],
                               capture_output=True, text=True)
        return result.returncode == 0
    except subprocess.SubprocessError:
        return False


def start_ngrok_tunnel(port=8000):
    """Start ngrok tunnel for the specified port."""
    try:
        # Start ngrok in background
        cmd = [str(NGROK_EXE_PATH), "http", str(port)]
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        time.sleep(3)  # Wait for tunnel to establish

        # Get tunnel URL
        result = subprocess.run([str(NGROK_EXE_PATH), "api", "tunnels"], capture_output=True, text=True)
        if result.returncode == 0:
            import json
            tunnels = json.loads(result.stdout)
            if tunnels.get("tunnels"):
                tunnel_url = tunnels["tunnels"][0]["public_url"]
                return process, tunnel_url

        return process, None
    except Exception:
        return None, None


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


# -----------------------------------------------------------
# CREATE POSTGRES DATABASE + USER
# -----------------------------------------------------------
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
# GUI CLASS
# -----------------------------------------------------------
class ServerSetupGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("SysLogger Server Setup")
        self.geometry("900x700")
        self.configure(bg="#e0f2fe")

        # Database selection
        self.db_choice = tk.StringVar(value="postgresql")

        # PostgreSQL config
        self.pg_host = tk.StringVar(value=POSTGRES_HOST)
        self.pg_dbname = tk.StringVar(value=POSTGRES_DBNAME)
        self.pg_user = tk.StringVar(value=POSTGRES_USER)
        self.pg_pass = tk.StringVar(value=POSTGRES_PASS)

        # Ngrok config
        self.enable_ngrok = tk.BooleanVar(value=False)
        self.ngrok_token = tk.StringVar(value="")

        # Setup thread
        self.setup_thread = None

        self._init_style()
        self._init_ui()

    def _init_style(self):
        style = ttk.Style(self)
        style.theme_use("clam")

        # Enhanced button styling with modern look
        style.configure("TButton", font=("Segoe UI", 14, "bold"),
                        padding=(15, 10), background="#4f46e5", foreground="white",
                        relief="flat", borderwidth=2, borderradius=8)
        style.map("TButton",
                  background=[("active", "#4338ca"), ("pressed", "#3730a3")],
                  relief=[("pressed", "sunken")])

        # Enhanced frame styling with subtle shadows
        style.configure("Card.TFrame", background="#ffffff", relief="raised",
                        lightcolor="#e2e8f0", darkcolor="#f1f5f9", borderwidth=2)

        # Enhanced label styling with better fonts
        style.configure("TLabel", font=("Segoe UI", 12), background="#ffffff")
        style.configure("Title.TLabel", font=("Segoe UI", 20, "bold"), background="#ffffff")

        # Enhanced entry styling with rounded corners effect
        style.configure("TEntry", font=("Segoe UI", 12), relief="flat", borderwidth=2,
                        fieldbackground="#f8fafc")

    def _init_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Create scrollable canvas
        self.main_canvas = tk.Canvas(self, bg="#f8fafc", highlightthickness=0)
        self.main_canvas.grid(row=0, column=0, sticky="nsew")

        # Add scrollbar
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.main_canvas.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")

        self.main_canvas.configure(yscrollcommand=scrollbar.set)

        # Create main frame inside canvas
        main_frame = ttk.Frame(self.main_canvas, style="Card.TFrame")
        self.main_canvas.create_window((0, 0), window=main_frame, anchor="nw")

        # Configure scrolling
        main_frame.bind('<Configure>', lambda e: self.main_canvas.configure(scrollregion=self.main_canvas.bbox("all")))

        # Enable mouse wheel scrolling
        def _on_mousewheel(event):
            self.main_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        self.main_canvas.bind_all("<MouseWheel>", _on_mousewheel)

        main_frame.grid_columnconfigure(0, weight=1)

        # ASCII Art Header with better styling
        art_frame = ttk.Frame(main_frame, style="Card.TFrame")
        art_frame.pack(fill="x", padx=20, pady=30)
        art_label = tk.Label(art_frame, text=ASCII_ART, font=("Courier New", 9, "bold"),
                            bg="white", fg="#1e40af", justify="center", relief="flat")
        art_label.pack(pady=15)

        title = tk.Label(main_frame, text="🛠️ Server Setup Configuration",
                        font=("Segoe UI", 24, "bold"), bg="white", fg="#0f172a")
        title.pack(pady=20)

        # Database Selection
        db_frame = ttk.Frame(main_frame, style="Card.TFrame")
        db_frame.pack(fill="x", padx=20, pady=10)

        ttk.Label(db_frame, text="Database Type:", font=("Segoe UI", 14, "bold"),
                 background="white").grid(row=0, column=0, sticky="w", padx=15, pady=10)

        pg_radio = ttk.Radiobutton(db_frame, text="PostgreSQL (Recommended)", variable=self.db_choice,
                                  value="postgresql", command=self._toggle_db_config)
        pg_radio.grid(row=1, column=0, sticky="w", padx=35, pady=5)

        sqlite_radio = ttk.Radiobutton(db_frame, text="SQLite (Fallback)", variable=self.db_choice,
                                      value="sqlite", command=self._toggle_db_config)
        sqlite_radio.grid(row=2, column=0, sticky="w", padx=35, pady=5)

        # PostgreSQL Config Frame
        self.pg_config_frame = ttk.Frame(db_frame, style="Card.TFrame")
        self.pg_config_frame.grid(row=3, column=0, columnspan=2, sticky="ew", padx=30, pady=10)

        ttk.Label(self.pg_config_frame, text="PostgreSQL Configuration:",
                 font=("Segoe UI", 11, "bold"), background="white").grid(row=0, column=0, columnspan=2, pady=5)

        ttk.Label(self.pg_config_frame, text="Host:", background="white").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        ttk.Entry(self.pg_config_frame, textvariable=self.pg_host, width=30).grid(row=1, column=1, padx=5, pady=2)

        ttk.Label(self.pg_config_frame, text="Database:", background="white").grid(row=2, column=0, sticky="w", padx=5, pady=2)
        ttk.Entry(self.pg_config_frame, textvariable=self.pg_dbname, width=30).grid(row=2, column=1, padx=5, pady=2)

        ttk.Label(self.pg_config_frame, text="Username:", background="white").grid(row=3, column=0, sticky="w", padx=5, pady=2)
        ttk.Entry(self.pg_config_frame, textvariable=self.pg_user, width=30).grid(row=3, column=1, padx=5, pady=2)

        ttk.Label(self.pg_config_frame, text="Password:", background="white").grid(row=4, column=0, sticky="w", padx=5, pady=2)
        ttk.Entry(self.pg_config_frame, textvariable=self.pg_pass, show="*", width=30).grid(row=4, column=1, padx=5, pady=2)

        # Port Forwarding (Ngrok) Section
        ngrok_frame = ttk.Frame(main_frame, style="Card.TFrame")
        ngrok_frame.pack(fill="x", padx=20, pady=10)

        ttk.Label(ngrok_frame, text="Port Forwarding (Ngrok):", font=("Segoe UI", 14, "bold"),
                 background="white").grid(row=0, column=0, sticky="w", padx=15, pady=10)

        self.ngrok_checkbox = ttk.Checkbutton(ngrok_frame, text="Enable ngrok tunnel for remote access",
                                             variable=self.enable_ngrok, command=self._toggle_ngrok_config)
        self.ngrok_checkbox.grid(row=1, column=0, sticky="w", padx=35, pady=10)

        # Ngrok Config Frame
        self.ngrok_config_frame = ttk.Frame(ngrok_frame, style="Card.TFrame")
        self.ngrok_config_frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=30, pady=10)

        ttk.Label(self.ngrok_config_frame, text="Ngrok Configuration:",
                 font=("Segoe UI", 11, "bold"), background="white").grid(row=0, column=0, columnspan=2, pady=5)

        ttk.Label(self.ngrok_config_frame, text="Auth Token:", background="white").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        ttk.Entry(self.ngrok_config_frame, textvariable=self.ngrok_token, show="*", width=50).grid(row=1, column=1, padx=5, pady=2)

        ttk.Label(self.ngrok_config_frame, text="(Get token from https://dashboard.ngrok.com/get-started/your-authtoken)",
                 font=("Segoe UI", 8), background="white").grid(row=2, column=0, columnspan=2, sticky="w", padx=5, pady=2)

        # Progress and Log Area
        progress_frame = ttk.Frame(main_frame, style="Card.TFrame")
        progress_frame.pack(fill="both", expand=True, padx=20, pady=10)

        ttk.Label(progress_frame, text="📈 Setup Progress", font=("Segoe UI", 16, "bold"),
                 background="white").pack(pady=10)

        self.progress_var = tk.IntVar()
        ttk.Progressbar(progress_frame, variable=self.progress_var, length=700).pack(pady=5)

        log_label = ttk.Label(progress_frame, text="📋 Activity Log", font=("Segoe UI", 14, "bold"), background="white")
        log_label.pack(pady=5)

        log_frame = ttk.Frame(progress_frame)
        log_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.log_text = tk.Text(log_frame, bg="#f8fafc", fg="#1e293b", font=("Consolas", 9),
                               height=15, wrap=tk.WORD, relief="sunken", borderwidth=2)
        scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)

        self.log_text.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Buttons
        button_frame = ttk.Frame(main_frame, style="Card.TFrame")
        button_frame.pack(fill="x", padx=20, pady=20)

        ttk.Button(button_frame, text="🚀 Start Setup", command=self.start_setup).pack(side="left", padx=10)
        ttk.Button(button_frame, text="❌ Exit", command=self.quit).pack(side="right", padx=10)

        # Footer
        footer = tk.Label(main_frame, text=FOOTER_TEXT, bg="white", fg="#64748b",
                         font=("Segoe UI", 9, "italic"))
        footer.pack(pady=10)

        # Initialize UI state
        self._toggle_db_config()
        self._toggle_ngrok_config()

    def _toggle_db_config(self):
        if self.db_choice.get() == "postgresql":
            self.pg_config_frame.grid()
        else:
            self.pg_config_frame.grid_remove()

    def _toggle_ngrok_config(self):
        if self.enable_ngrok.get():
            self.ngrok_config_frame.grid()
        else:
            self.ngrok_config_frame.grid_remove()

    def log(self, msg, color="#1e293b"):
        self.log_text.insert("end", msg + "\n", ("tag_" + color))
        self.log_text.tag_config("tag_" + color, foreground=color)
        self.log_text.see("end")

    def start_setup(self):
        if self.setup_thread and self.setup_thread.is_alive():
            messagebox.showwarning("Warning", "Setup is already running!")
            return

        self.progress_var.set(0)
        self.log_text.delete(1.0, "end")

        self.setup_thread = threading.Thread(target=self._run_setup)
        self.setup_thread.start()

    def _run_setup(self):
        try:
            if self.db_choice.get() == "postgresql":
                self.log("🔍 Checking PostgreSQL availability...", "#2563eb")
                self.progress_var.set(10)

                if not PG_AVAILABLE:
                    raise Exception("psycopg2 not installed")

                if not postgres_running():
                    raise Exception("PostgreSQL server is not running")

                global POSTGRES_HOST, POSTGRES_DBNAME, POSTGRES_USER, POSTGRES_PASS
                POSTGRES_HOST = self.pg_host.get()
                POSTGRES_DBNAME = self.pg_dbname.get()
                POSTGRES_USER = self.pg_user.get()
                POSTGRES_PASS = self.pg_pass.get()

                self.log("✅ PostgreSQL detected. Setting up database...", "#16a34a")
                self.progress_var.set(30)

                if setup_postgres_database():
                    self.log("✅ Database and user created", "#16a34a")
                    self.progress_var.set(60)

                    if apply_postgres_schema():
                        self.log("✅ PostgreSQL schema applied successfully!", "#16a34a")
                        self.progress_var.set(70)

                        # Handle ngrok setup if enabled
                        if self.enable_ngrok.get():
                            self.log("🔧 Setting up ngrok for port forwarding...", "#2563eb")
                            self.progress_var.set(80)

                            if not check_ngrok_installed():
                                self.log("📥 Installing ngrok...", "#2563eb")
                                if not download_ngrok():
                                    raise Exception("Failed to install ngrok")

                            token = self.ngrok_token.get().strip()
                            if not token:
                                raise Exception("Ngrok auth token is required")

                            if not set_ngrok_auth_token(token):
                                raise Exception("Failed to set ngrok auth token")

                            self.log("✅ Ngrok configured successfully!", "#16a34a")
                            self.log(f"🚀 Starting ngrok tunnel on port {NGROK_PORT}...", "#2563eb")

                            process, tunnel_url = start_ngrok_tunnel(NGROK_PORT)
                            if process and tunnel_url:
                                self.log(f"✅ Ngrok tunnel active: {tunnel_url}", "#16a34a")
                                self.log("💡 Save this URL for remote access", "#16a34a")
                            else:
                                raise Exception("Failed to start ngrok tunnel")

                        self.progress_var.set(100)
                        messagebox.showinfo("Success", "PostgreSQL setup completed successfully!")

                    else:
                        raise Exception("Failed to apply PostgreSQL schema")
                else:
                    raise Exception("Failed to setup PostgreSQL database")

            else:
                self.log("🔄 Using SQLite fallback...", "#2563eb")
                self.progress_var.set(50)

                setup_sqlite()
                self.log("✅ SQLite database ready", "#16a34a")
                self.progress_var.set(70)

                # Handle ngrok setup if enabled
                if self.enable_ngrok.get():
                    self.log("🔧 Setting up ngrok for port forwarding...", "#2563eb")
                    self.progress_var.set(80)

                    if not check_ngrok_installed():
                        self.log("📥 Installing ngrok...", "#2563eb")
                        if not download_ngrok():
                            raise Exception("Failed to install ngrok")

                    token = self.ngrok_token.get().strip()
                    if not token:
                        raise Exception("Ngrok auth token is required")

                    if not set_ngrok_auth_token(token):
                        raise Exception("Failed to set ngrok auth token")

                    self.log("✅ Ngrok configured successfully!", "#16a34a")
                    self.log(f"🚀 Starting ngrok tunnel on port {NGROK_PORT}...", "#2563eb")

                    process, tunnel_url = start_ngrok_tunnel(NGROK_PORT)
                    if process and tunnel_url:
                        self.log(f"✅ Ngrok tunnel active: {tunnel_url}", "#16a34a")
                        self.log("💡 Save this URL for remote access", "#16a34a")
                    else:
                        raise Exception("Failed to start ngrok tunnel")

                self.progress_var.set(100)
                messagebox.showinfo("Success", "SQLite setup completed successfully!")

        except Exception as e:
            self.log(f"❌ ERROR: {str(e)}", "#dc2626")
            self.progress_var.set(0)
            messagebox.showerror("Setup Failed", f"Setup failed: {str(e)}")


# -----------------------------------------------------------
# MAIN LOGIC
# -----------------------------------------------------------
def main():
    # Check if GUI mode or console mode
    if len(sys.argv) > 1 and sys.argv[1] == "--console":
        print("\n=== Sys_Logger Server Setup (Console Mode) ===\n")

        # Prefer PostgreSQL
        if PG_AVAILABLE and postgres_running() and setup_postgres_database():
            if apply_postgres_schema():
                print("🎉 Using PostgreSQL mode")
            else:
                print("⚠ PostgreSQL schema failed → switching to SQLite")
                setup_sqlite()
        else:
            print("⚠ PostgreSQL not available → using SQLite")
            setup_sqlite()

        print("\nSetup complete.\n")
    else:
        # GUI mode
        app = ServerSetupGUI()
        app.mainloop()


if __name__ == "__main__":
    main()