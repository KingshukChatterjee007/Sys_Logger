# -*- mode: python ; coding: utf-8 -*-

import sys
import os
import subprocess
import platform
import logging
import json
import re
from pathlib import Path
import threading

import tkinter as tk
from tkinter import ttk, messagebox

# Optional imports
try:
    import psycopg2
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
    PSYCOPG_AVAILABLE = True
except ImportError:
    PSYCOPG_AVAILABLE = False

# Constants
FOOTER_TEXT = "Product of NIELIT Bhubaneswar - Made by Krishi Sahayogi Team"
REQUIRED_PYTHON_VERSION = (3, 8)
REQUIRED_NODE_VERSION = (16, 0)

# Handle bundled executable path resolution
if hasattr(sys, '_MEIPASS'):
    # Running from PyInstaller bundle
    PROJECT_ROOT = Path(sys._MEIPASS)
else:
    # Running from source
    PROJECT_ROOT = Path(__file__).parent.parent

SERVER_SETUP_FILE = PROJECT_ROOT / "server_setup.py"


# ============================================================================
# WORKER THREAD (Tkinter-safe)
# ============================================================================
class Worker(threading.Thread):
    def __init__(self, app, operation, *args):
        super().__init__(daemon=True)
        self.app = app
        self.operation = operation
        self.args = args

    def run(self):
        try:
            fn = getattr(self.app, f"op_{self.operation}")
            fn(*self.args)
        except Exception as e:
            # Show error in main thread via app helper
            self.app.log(f"ERROR: {e}")
            self.app.show_error(str(e))
        finally:
            self.app.progress(100, "Operation finished.")


# ============================================================================
# MAIN UI WINDOW (Tkinter)
# ============================================================================
class ServerInstallerApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Server Installer - Krishi Sahayogi")
        self.geometry("950x700")
        self.configure(bg="#f8f9fa")
        self.prereq_passed = False
        self.buttons = {}

        self._init_style()
        self._init_logging()
        self._init_ui()

    # ----------------------------------------------------------------------
    # Styles & logging
    # ----------------------------------------------------------------------
    def _init_style(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TButton", font=("Segoe UI", 11), padding=6)
        style.configure("Card.TLabelframe",
                        background="white",
                        borderwidth=2,
                        relief="groove")
        style.configure("Card.TLabelframe.Label",
                        font=("Segoe UI", 11, "bold"))

    def _init_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(message)s"
        )
        self.logger = logging.getLogger("server_installer")

    # ----------------------------------------------------------------------
    # UI Layout
    # ----------------------------------------------------------------------
    def _init_ui(self):
        # Root grid config
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)

        # Top title
        title = tk.Label(
            self,
            text="Krishi Sahayogi Server Installer",
            font=("Segoe UI", 20, "bold"),
            bg="#eef1f7"
        )
        title.grid(row=0, column=0, pady=(10, 5))

        # Main frame
        main = tk.Frame(self, bg="#eef1f7")
        main.grid(row=1, column=0, sticky="nsew", padx=15, pady=10)
        main.grid_columnconfigure(0, weight=1)
        main.grid_columnconfigure(1, weight=1)
        main.grid_rowconfigure(1, weight=1)

        # Left column (actions)
        left = tk.Frame(main, bg="#eef1f7")
        left.grid(row=0, column=0, sticky="nwe", padx=(0, 10))
        left.grid_columnconfigure(0, weight=1)

        # Right column (progress + log)
        right = tk.Frame(main, bg="#eef1f7")
        right.grid(row=0, column=1, sticky="nsew")
        right.grid_rowconfigure(1, weight=1)
        right.grid_columnconfigure(0, weight=1)

        # ----------------- Groups on LEFT -----------------

        # Prerequisites
        prereq_frame = ttk.Labelframe(
            left, text="Prerequisites", style="Card.TLabelframe")
        prereq_frame.grid(row=0, column=0, sticky="we", pady=5)
        self.buttons['prereq'] = ttk.Button(
            prereq_frame,
            text="🔍 Check Prerequisites",
            command=self.run_prereq_check
        )
        self.buttons['prereq'].pack(fill="x", padx=10, pady=10)

        # PostgreSQL Setup
        pg_frame = ttk.Labelframe(
            left, text="PostgreSQL Setup", style="Card.TLabelframe")
        pg_frame.grid(row=1, column=0, sticky="we", pady=5)
        ttk.Button(
            pg_frame,
            text="Setup PostgreSQL",
            command=self.run_postgres_setup
        ).pack(fill="x", padx=10, pady=10)

        # Domain configuration
        dom_frame = ttk.Labelframe(
            left, text="Domain Configuration", style="Card.TLabelframe")
        dom_frame.grid(row=2, column=0, sticky="we", pady=5)

        tk.Label(dom_frame, text="Backend Domain:", bg="white").pack(
            anchor="w", padx=10, pady=(8, 0))
        self.backend_domain = tk.Entry(dom_frame)
        self.backend_domain.insert(0, "http://localhost:8000")
        self.backend_domain.pack(fill="x", padx=10, pady=2)

        tk.Label(dom_frame, text="Frontend Domain:", bg="white").pack(
            anchor="w", padx=10, pady=(8, 0))
        self.frontend_domain = tk.Entry(dom_frame)
        self.frontend_domain.insert(0, "http://localhost:3000")
        self.frontend_domain.pack(fill="x", padx=10, pady=2)

        self.buttons['domain'] = ttk.Button(
            dom_frame,
            text="🔗 Apply Domain Config",
            command=self.run_domain_config,
            state="disabled"
        )
        self.buttons['domain'].pack(fill="x", padx=10, pady=10)

        # Startup configuration
        startup_frame = ttk.Labelframe(
            left, text="Startup Configuration", style="Card.TLabelframe")
        startup_frame.grid(row=3, column=0, sticky="we", pady=5)
        ttk.Button(
            startup_frame,
            text="Configure Startup",
            command=self.run_startup_config
        ).pack(fill="x", padx=10, pady=10)

        # Protection
        prot_frame = ttk.Labelframe(
            left, text="Protection", style="Card.TLabelframe")
        prot_frame.grid(row=4, column=0, sticky="we", pady=5)
        ttk.Button(
            prot_frame,
            text="Setup Protection",
            command=self.run_protection_setup
        ).pack(fill="x", padx=10, pady=10)

        # Run server_setup.py
        run_frame = ttk.Labelframe(
            left, text="Server Setup Script", style="Card.TLabelframe")
        run_frame.grid(row=5, column=0, sticky="we", pady=5)
        ttk.Button(
            run_frame,
            text="Run server_setup.py",
            command=self.run_server_setup
        ).pack(fill="x", padx=10, pady=10)

        # Start Server
        start_frame = ttk.Labelframe(
            left, text="Start Server", style="Card.TLabelframe")
        start_frame.grid(row=6, column=0, sticky="we", pady=5)
        ttk.Button(
            start_frame,
            text="Start Server (Service Mode)",
            command=self.run_start_server
        ).pack(fill="x", padx=10, pady=10)

        # ----------------- RIGHT: Progress + Log -----------------

        self.progress_var = tk.IntVar()
        self.progress_bar = ttk.Progressbar(
            right, variable=self.progress_var, maximum=100)
        self.progress_bar.grid(row=0, column=0, sticky="we", padx=5, pady=(5, 10))

        self.log_widget = tk.Text(right, bg="#f5f5f5", wrap="word")
        self.log_widget.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

        footer = tk.Label(
            right,
            text=FOOTER_TEXT,
            bg="#eef1f7",
            fg="gray",
            font=("Segoe UI", 9)
        )
        footer.grid(row=2, column=0, pady=(5, 0))

    # ----------------------------------------------------------------------
    # Helper UI methods
    # ----------------------------------------------------------------------
    def log(self, msg: str):
        print(msg)
        self.logger.info(msg)

    def progress(self, value: int, msg: str):
        # schedule UI updates on main thread
        def _update():
            self.progress_var.set(value)
            self.log(msg)
        self.after(0, _update)

    def show_error(self, msg: str):
        def _show():
            messagebox.showerror("Error", msg)
        self.after(0, _show)

    # ----------------------------------------------------------------------
    # Worker start helpers
    # ----------------------------------------------------------------------
    def start_worker(self, operation: str, *args):
        worker = Worker(self, operation, *args)
        worker.start()

    # Button handlers
    def run_prereq_check(self):
        self.start_worker("prereq_check")

    def run_postgres_setup(self):
        self.start_worker("postgres_setup")

    def run_domain_config(self):
        backend = self.backend_domain.get().strip()
        frontend = self.frontend_domain.get().strip()
        self.start_worker("domain_config", backend, frontend)

    def run_startup_config(self):
        self.start_worker("startup_config")

    def run_protection_setup(self):
        self.start_worker("protection_setup")

    def run_server_setup(self):
        self.start_worker("run_server_setup")

    def run_start_server(self):
        self.start_worker("start_server")

    # =========================================================================
    # BACKEND OPERATIONS (PyQt → Tkinter refactor)
    # =========================================================================

    # ---------------------- run_server_setup.py ----------------------
    def op_run_server_setup(self):
        self.progress(10, "Running server_setup.py...")

        if not SERVER_SETUP_FILE.exists():
            raise Exception("server_setup.py not found")

        result = subprocess.run(
            [sys.executable, str(SERVER_SETUP_FILE)],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            raise Exception(result.stderr or "server_setup.py failed")

        self.progress(100, "server_setup.py completed successfully")

    # ---------------------- start_server ----------------------
    def op_start_server(self):
        self.progress(10, "Starting server in service mode...")

        sys_logger_path = PROJECT_ROOT / "backend" / "sys_logger.py"
        if not sys_logger_path.exists():
            raise Exception("sys_logger.py not found")

        result = subprocess.run(
            [sys.executable, str(sys_logger_path), "--service"],
            cwd=PROJECT_ROOT,
            capture_output=False,
            text=True
        )

        # Note: In service mode, the server runs indefinitely, so we don't check returncode
        self.progress(100, "Server started in service mode")

    # ---------------------- Prerequisite checks ----------------------
    def op_prereq_check(self):
        checks = [
            ("Python", self._check_python),
            ("Node.js", self._check_node),
            ("Docker", self._check_docker),
            ("Chocolatey (optional)", self._check_choco),
        ]

        for i, (name, fn) in enumerate(checks):
            pct = int((i / len(checks)) * 100)
            self.progress(pct, f"Checking {name}...")
            if not fn():
                raise Exception(f"{name} check failed")
            self.log(f"✓ {name} OK")

        self.progress(100, "All prerequisites OK")
        self.buttons['domain'].config(state="normal")

    def _check_python(self):
        try:
            version = tuple(map(int, platform.python_version_tuple()[:2]))
            return version >= REQUIRED_PYTHON_VERSION
        except:
            return False

    def _check_node(self):
        try:
            result = subprocess.run(["node", "--version"],
                                    capture_output=True, text=True)
            version = result.stdout.strip().lstrip("v")
            major, minor = map(int, version.split(".")[:2])
            return major >= REQUIRED_NODE_VERSION[0]
        except:
            return False

    def _check_docker(self):
        try:
            subprocess.run(["docker", "--version"],
                           capture_output=True, check=True)
            return True
        except:
            return False

    def _check_choco(self):
        try:
            subprocess.run(["choco", "--version"],
                           capture_output=True, check=True)
            return True
        except:
            return False

    # ---------------------- PostgreSQL setup ----------------------
    def op_postgres_setup(self):
        if not PSYCOPG_AVAILABLE:
            raise Exception("psycopg2 is not installed")

        self.progress(10, "Checking PostgreSQL installation...")

        try:
            subprocess.run(
                ["psql", "--version"],
                check=True,
                capture_output=True
            )
        except:
            raise Exception("PostgreSQL not installed. Please install manually.")

        # Start service
        system = platform.system()
        self.progress(20, "Starting PostgreSQL service...")

        if system == "Windows":
            subprocess.run(["net", "start", "postgresql"], check=False)
        elif system == "Linux":
            subprocess.run(["sudo", "systemctl", "start", "postgresql"])
        elif system == "Darwin":
            subprocess.run(["brew", "services", "start", "postgresql"])

        # Create DB, user, schema
        self.progress(40, "Creating database and user...")

        conn = psycopg2.connect("user=postgres host=localhost")
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()

        # Create DB if not exists
        cur.execute("SELECT 1 FROM pg_database WHERE datname='sys_logger'")
        if not cur.fetchone():
            cur.execute("CREATE DATABASE sys_logger")

        # Create role if not exists
        cur.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname='syslogger') THEN
                CREATE ROLE syslogger LOGIN PASSWORD 'syslogger123';
            END IF;
        END$$;
        """)
        conn.close()

        # Apply schema
        self.progress(60, "Applying SQL schema...")

        conn = psycopg2.connect(
            "dbname=sys_logger user=syslogger password=syslogger123 host=localhost")
        cur = conn.cursor()

        schema_path = PROJECT_ROOT / "database_schema.sql"
        if not schema_path.exists():
            conn.close()
            raise Exception("database_schema.sql missing")

        with open(schema_path, "r") as f:
            sql = f.read()
            cur.execute(sql)

        conn.commit()
        conn.close()

        self.progress(100, "PostgreSQL setup completed successfully")

    # ---------------------- Domain configuration ----------------------
    def op_domain_config(self, backend_domain, frontend_domain):
        self.progress(20, "Updating backend .env...")

        backend_env = PROJECT_ROOT / "backend" / ".env"
        backend_env.parent.mkdir(exist_ok=True)

        with open(backend_env, "w") as f:
            f.write(
                "FLASK_ENV=production\n"
                "PORT=8000\n"
                f"CORS_ORIGINS={frontend_domain}\n"
            )

        self.progress(60, "Updating frontend .env.local...")

        frontend_env = PROJECT_ROOT / "frontend" / ".env.local"
        frontend_env.parent.mkdir(exist_ok=True)

        with open(frontend_env, "w") as f:
            f.write(
                "NODE_ENV=production\n"
                f"NEXT_PUBLIC_API_URL={backend_domain}\n"
            )

        self.progress(100, "Domain configuration updated")

    # ---------------------- Startup configuration ----------------------
    def op_startup_config(self):
        system = platform.system()
        self.progress(20, f"Configuring startup for {system}...")

        if system == "Windows":
            task_name = "SysLoggerServer"
            cmd = (
                f'cmd /c "cd /d {PROJECT_ROOT} && '
                f'"{sys.executable}" server_setup.py"'
            )

            subprocess.run(
                [
                    "schtasks", "/create", "/tn", task_name,
                    "/tr", cmd, "/sc", "onlogon",
                    "/rl", "highest", "/f"
                ],
                check=True
            )

        elif system == "Linux":
            service = f"""[Unit]
Description=SysLogger Server
After=network.target postgresql.service

[Service]
User={os.getlogin()}
WorkingDirectory={PROJECT_ROOT}
ExecStart={sys.executable} {SERVER_SETUP_FILE}
Restart=always

[Install]
WantedBy=multi-user.target
"""
            svc_file = Path("/etc/systemd/system/syslogger.service")
            with open(svc_file, "w") as f:
                f.write(service)

            subprocess.run(["sudo", "systemctl", "daemon-reload"])
            subprocess.run(["sudo", "systemctl", "enable", "syslogger.service"])

        elif system == "Darwin":
            plist_path = Path("/Library/LaunchDaemons/com.syslogger.server.plist")
            plist = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
"http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
    <key>Label</key><string>com.syslogger.server</string>
    <key>ProgramArguments</key>
    <array>
        <string>{sys.executable}</string>
        <string>{SERVER_SETUP_FILE}</string>
    </array>
    <key>RunAtLoad</key><true/>
</dict></plist>
"""
            with open(plist_path, "w") as f:
                f.write(plist)
            subprocess.run(["sudo", "launchctl", "load", str(plist_path)])

        self.progress(100, "Startup configuration complete")

    # ---------------------- Protection setup ----------------------
    def op_protection_setup(self):
        system = platform.system()
        self.progress(20, f"Configuring service protection for {system}...")

        try:
            if system == "Windows":
                subprocess.run([
                    "sc.exe", "failure", "SysLoggerServer",
                    "reset=", "86400",
                    "actions=", "restart/5000/restart/5000/restart/5000"
                ])

            elif system == "Linux":
                subprocess.run(["sudo", "systemctl", "restart", "syslogger.service"])

            elif system == "Darwin":
                subprocess.run([
                    "sudo", "launchctl", "kickstart",
                    "-k", "system/com.syslogger.server"
                ])
        except Exception as e:
            raise Exception(f"Failed to configure protection: {e}")

        self.progress(100, "Protection configured successfully")


# ============================================================================
# MAIN
# ============================================================================
if __name__ == "__main__":
    app = ServerInstallerApp()
    app.mainloop()
