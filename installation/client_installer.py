import sys
import os
import subprocess
import platform
import logging
import socket
import threading
import time
import json
import uuid
from pathlib import Path

import tkinter as tk
from tkinter import ttk, messagebox

# Optional deps
try:
    import psutil
    PSUTIL_AVAILABLE = True
except:
    PSUTIL_AVAILABLE = False

try:
    import requests
    REQUESTS_AVAILABLE = True
except:
    REQUESTS_AVAILABLE = False

try:
    import GPUtil
    GPUUTIL_AVAILABLE = True
except:
    GPUUTIL_AVAILABLE = False


# --------------------------
# CONSTANTS
# --------------------------
FOOTER_TEXT = "Product of NIELIT Bhubaneswar - Made by Krishi Sahayogi Team"
REQUIRED_PYTHON_VERSION = (3, 6)

PROJECT_ROOT = Path(__file__).parent
UNIT_CLIENT_SCRIPT = PROJECT_ROOT / "unit_client.py"
CLIENT_CONFIG_FILE = PROJECT_ROOT / "unit_client_config.json"


# ===================================================================
#                       TKINTER WORKER THREAD
# ===================================================================
class Worker(threading.Thread):
    def __init__(self, app, operation):
        super().__init__()
        self.app = app
        self.operation = operation

    def run(self):
        try:
            func = getattr(self.app, f"op_{self.operation}")
            func()
            # On success, update status
            if self.operation in self.app.step_labels:
                self.app.step_labels[self.operation].config(text="✅ Success", fg="#16a34a")
                self.app.step_statuses[self.operation] = "✅ Success"
                self.app.log(f"✓ Step '{self.operation}' completed successfully.")
        except Exception as e:
            self.app.log(f"❌ ERROR: {str(e)}")
            if self.operation in self.app.step_labels:
                self.app.step_labels[self.operation].config(text="❌ Failed", fg="#dc2626")
                self.app.step_statuses[self.operation] = "❌ Failed"
            messagebox.showerror("Installation Error", f"Step '{self.operation}' failed:\n\n{str(e)}\n\nPlease resolve the issue and try again.")
        finally:
            self.app.progress(100, "Step completed.")


# ===================================================================
#                       MAIN INSTALLER GUI (TKINTER)
# ===================================================================
class InstallerGUI(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("SysLogger Client Installer")
        self.geometry("1200x800")
        self.configure(bg="#e0f2fe")

        # Status tracking for steps
        self.step_statuses = {
            "prereq_check": "⏳ Pending",
            "generate_id": "⏳ Pending",
            "discover_server": "⏳ Pending",
            "register_client": "⏳ Pending",
            "start_monitoring": "⏳ Pending",
            "configure_startup": "⏳ Pending",
            "setup_protection": "⏳ Pending",
            "handle_domain_updates": "⏳ Pending",
        }
        self.step_labels = {}

        self.full_install_running = False
        self.full_install_step_index = 0
        self.full_install_steps = [
            "prereq_check",
            "generate_id",
            "discover_server",
            "register_client",
            "start_monitoring",
            "configure_startup",
            "setup_protection",
            "handle_domain_updates",
        ]

        self._init_style()
        self._init_ui()
        self._init_logging()

    # -------------------------------------------------------------------
    # UI STYLES
    # -------------------------------------------------------------------
    def _init_style(self):
        style = ttk.Style(self)
        style.theme_use("clam")

        # Modern button styling
        style.configure(
            "TButton",
            font=("Segoe UI", 12, "bold"),
            padding=(12, 8),
            background="#6366f1",
            foreground="white",
            relief="flat",
            borderwidth=0
        )

        style.map("TButton",
                  background=[("active", "#4f46e5"), ("pressed", "#4338ca")],
                  relief=[("pressed", "sunken")])

        # Enhanced card frames with subtle shadow effect
        style.configure("Card.TFrame", background="#ffffff", relief="raised", borderwidth=3)

    # -------------------------------------------------------------------
    # MAIN UI LAYOUT (LEFT PANEL + RIGHT PANEL)
    # -------------------------------------------------------------------
    def _init_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=2)

        # Left Panel
        left = ttk.Frame(self, style="Card.TFrame")
        left.grid(row=0, column=0, sticky="nswe", padx=15, pady=15)

        title = tk.Label(left, text="📋 Installation Steps",
                         font=("Segoe UI", 22, "bold"),
                         bg="#ffffff", fg="#1f2937")
        title.pack(pady=20)

        steps = [
            ("Check Prerequisites", "prereq_check"),
            ("Generate System ID", "generate_id"),
            ("Discover Server", "discover_server"),
            ("Register Client", "register_client"),
            ("Start Monitoring Service", "start_monitoring"),
            ("Configure Auto-Startup", "configure_startup"),
            ("Setup Protection", "setup_protection"),
            ("Configure Domain Updates", "handle_domain_updates"),
        ]

        for label, op in steps:
            frame = ttk.Frame(left, style="Card.TFrame")
            frame.pack(fill="x", padx=20, pady=5)
            btn = ttk.Button(frame, text=label,
                             command=lambda o=op: self.start_worker(o))
            btn.pack(side="left", fill="x", expand=True)
            status_label = tk.Label(frame, text=self.step_statuses[op],
                                    bg="white", fg="#6b7280", font=("Segoe UI", 9))
            status_label.pack(side="right", padx=10)
            self.step_labels[op] = status_label

        ttk.Button(left, text="Run Full Installation",
                   command=self.run_full_install).pack(fill="x", padx=20, pady=30)

        # Right Panel
        right = ttk.Frame(self, style="Card.TFrame")
        right.grid(row=0, column=1, sticky="nswe", padx=20, pady=20)

        progress_title = tk.Label(right, text="📈 Installation Progress",
                                  font=("Segoe UI", 20, "bold"),
                                  bg="white", fg="#1e293b")
        progress_title.pack(pady=15)

        self.progress_var = tk.IntVar()
        progress_frame = ttk.Frame(right, style="Card.TFrame")
        progress_frame.pack(pady=10, padx=25, fill="x")
        ttk.Progressbar(progress_frame, variable=self.progress_var, length=700,
                        style="TProgressbar").pack(pady=10, padx=25, fill="x")

        log_title = tk.Label(right, text="📋 Activity Log",
                             font=("Segoe UI", 18, "bold"),
                             bg="white", fg="#374151")
        log_title.pack(pady=5)

        self.log_box = tk.Text(right, bg="#f8fafc", fg="#1e293b", font=("Consolas", 11),
                               height=28, relief="sunken", borderwidth=2)
        self.log_box.pack(padx=25, pady=5, fill="both", expand=True)

        footer = tk.Label(right, text=FOOTER_TEXT, bg="white", fg="#64748b",
                          font=("Segoe UI", 10, "italic"))
        footer.pack(pady=15)

    # -------------------------------------------------------------------
    # Logging
    # -------------------------------------------------------------------
    def _init_logging(self):
        logging.basicConfig(level=logging.INFO,
                            format="%(asctime)s - %(message)s")
        self.logger = logging.getLogger("installer")

    def log(self, msg):
        self.log_box.insert("end", msg + "\n")
        self.log_box.see("end")
        self.logger.info(msg)

    def progress(self, val, msg):
        self.progress_var.set(val)
        self.log(msg)

    # -------------------------------------------------------------------
    # Start Worker Thread
    # -------------------------------------------------------------------
    def start_worker(self, operation):
        if operation in self.step_labels:
            self.step_labels[operation].config(text="▶️ Running", fg="#2563eb")
            self.step_statuses[operation] = "▶️ Running"
        Worker(self, operation).start()

    # -------------------------------------------------------------------
    # Full Installation Runner
    # -------------------------------------------------------------------
    def run_full_install(self):
        if self.full_install_running:
            messagebox.showwarning("Warning", "Full installation is already running.")
            return

        self.full_install_running = True
        self.full_install_step_index = 0

        # Reset all statuses to pending
        for op in self.step_statuses:
            self.step_statuses[op] = "⏳ Pending"
            self.step_labels[op].config(text="⏳ Pending", fg="#6b7280")

        self.run_next_step()

    def run_next_step(self):
        if self.full_install_step_index >= len(self.full_install_steps):
            self.full_install_running = False
            messagebox.showinfo("Success", "Full Installation Complete!")
            return

        op = self.full_install_steps[self.full_install_step_index]
        self.step_labels[op].config(text="▶️ Running", fg="#2563eb")
        self.step_statuses[op] = "▶️ Running"

        worker = Worker(self, op)
        worker.start()
        # Override worker's run to handle success/failure
        original_run = worker.run
        def patched_run():
            try:
                original_run()
                # On success, proceed to next
                self.step_labels[op].config(text="✅ Success", fg="#16a34a")
                self.step_statuses[op] = "✅ Success"
                self.log(f"Step {op} completed successfully.")
                self.full_install_step_index += 1
                self.after(500, self.run_next_step)
            except Exception as e:
                self.step_labels[op].config(text="❌ Failed", fg="#dc2626")
                self.step_statuses[op] = "❌ Failed"
                self.log(f"Step {op} failed: {str(e)}")
                messagebox.showerror("Installation Failed", f"Step '{op}' failed: {str(e)}\n\nFull installation halted. Please resolve the issue and retry.")
                self.full_install_running = False

        worker.run = patched_run

    # ===================================================================
    #                    BACKEND OPERATIONS (Converted)
    # ===================================================================

    # -------------------------
    # Requirement Check
    # -------------------------
    def op_prereq_check(self):
        checks = [
            ("Python Version", lambda: sys.version_info >= REQUIRED_PYTHON_VERSION),
            ("psutil Installed", lambda: PSUTIL_AVAILABLE),
            ("requests Installed", lambda: REQUESTS_AVAILABLE),
            ("GPUtil (Optional)", lambda: GPUUTIL_AVAILABLE),
        ]

        for idx, (name, func) in enumerate(checks):
            self.progress(int(idx / len(checks) * 100), f"Checking {name}...")
            if not func() and "Optional" not in name:
                raise Exception(f"Missing: {name}")
            self.log(f"✓ {name} OK")

        self.progress(100, "Prerequisite check complete")

    # -------------------------
    # Generate System ID
    # -------------------------
    def op_generate_id(self):
        self.progress(10, "Checking existing ID...")

        if CLIENT_CONFIG_FILE.exists():
            try:
                config = json.loads(CLIENT_CONFIG_FILE.read_text())
                sid = config.get("system_id")
                if sid:
                    self.progress(100, f"Existing ID found: {sid[:8]}...")
                    return
            except:
                pass

        self.progress(50, "Generating new ID...")
        sid = str(uuid.uuid4())
        json.dump({"system_id": sid, "server_url": "http://localhost:5000"},
                  open(CLIENT_CONFIG_FILE, "w"), indent=4)

        self.progress(100, f"Generated new ID: {sid[:8]}...")

    # -------------------------
    # Server Discovery
    # -------------------------
    def op_discover_server(self):
        self.progress(10, "Discovering server on network...")

        ports = [5000, 8000, 3000]
        found = None

        try:
            local_ip = socket.gethostbyname(socket.gethostname())
            prefix = ".".join(local_ip.split(".")[:-1])
        except:
            prefix = "192.168.1"

        for i in range(1, 255):
            ip = f"{prefix}.{i}"
            for port in ports:
                try:
                    r = requests.get(f"http://{ip}:{port}/api/health",
                                     timeout=0.3)
                    if r.status_code == 200:
                        found = f"http://{ip}:{port}"
                        break
                except:
                    pass
            if found:
                break

        if not found:
            found = "http://localhost:5000"

        cfg = self._load_cfg()
        cfg["server_url"] = found
        self._save_cfg(cfg)

        self.progress(100, f"Server detected: {found}")

    # -------------------------
    # Registration
    # -------------------------
    def op_register_client(self):
        cfg = self._load_cfg()
        sid = cfg.get("system_id")
        url = cfg.get("server_url")

        if not sid:
            raise Exception("System ID missing!")
        if not url:
            raise Exception("Server URL missing!")

        self.progress(20, "Collecting system info...")
        info = self._collect_system_info(sid)

        self.progress(60, "Registering with server...")

        resp = requests.post(f"{url}/api/register_unit",
                             json=info, timeout=30)

        if resp.status_code not in (200, 201, 409):
            raise Exception(f"Registration failed: {resp.status_code}")

        self.progress(100, "Registration successful")

    # -------------------------
    # Start Monitoring
    # -------------------------
    def op_start_monitoring(self):
        if not UNIT_CLIENT_SCRIPT.exists():
            raise Exception("unit_client.py missing!")

        self.progress(20, "Launching background monitoring...")

        subprocess.Popen([sys.executable,
                          str(UNIT_CLIENT_SCRIPT),
                          "--start"])

        self.progress(100, "Monitoring active")

    # -------------------------
    # Auto-start setup (Win/Linux/macOS)
    # -------------------------
    def op_configure_startup(self):
        system = platform.system()

        self.progress(20, f"Configuring startup on {system}...")

        python = sys.executable
        script = UNIT_CLIENT_SCRIPT

        if system == "Windows":
            subprocess.run([
                "schtasks", "/create", "/tn", "SysLoggerClient",
                "/tr", f'"{python}" "{script}" --start',
                "/sc", "ONLOGON", "/rl", "HIGHEST", "/f"
            ], check=True)

        elif system == "Linux":
            svc = f"""
[Unit]
Description=SysLogger Client
After=network.target

[Service]
ExecStart={python} {script} --start
Restart=always

[Install]
WantedBy=multi-user.target
"""
            path = Path("/etc/systemd/system/syslogger.service")
            path.write_text(svc)
            subprocess.run(["sudo", "systemctl", "enable", "syslogger"], check=True)

        elif system == "Darwin":
            plist = f"""
<?xml version="1.0"?>
<plist version="1.0">
<dict>
 <key>Label</key><string>syslogger.client</string>
 <key>ProgramArguments</key>
 <array>
   <string>{python}</string>
   <string>{script}</string>
   <string>--start</string>
 </array>
 <key>RunAtLoad</key><true/>
</dict>
</plist>
"""
            p = Path.home() / "Library/LaunchAgents/syslogger.client.plist"
            p.write_text(plist)

        self.progress(100, "Startup configured")

    # -------------------------
    # Protection Setup
    # -------------------------
    def op_setup_protection(self):
        """Setup protection mechanisms across all OS"""
        system = platform.system()
        self.progress(20, f"Setting up protection for {system}...")

        python = sys.executable
        client_script = UNIT_CLIENT_SCRIPT

        #
        # -------------------------------------------------------
        # WINDOWS PROTECTION
        # -------------------------------------------------------
        #
        if system == "Windows":
            try:
                service_name = "SysLoggerClientProtected"
                bin_path = f'"{python}" "{client_script}" --start"'

                # Create the protected service
                subprocess.run([
                    "sc.exe", "create", service_name,
                    "binPath=", bin_path,
                    "start=", "auto",
                    "DisplayName=", "SysLogger Client (Protected)",
                    "type=", "own",
                    "error=", "normal"
                ], check=True)

                # Configure automatic restart on failure
                subprocess.run([
                    "sc.exe", "failure", service_name,
                    "reset=", "86400",
                    "actions=", "restart/5000/restart/5000/restart/5000"
                ], check=True)

                self.log("✓ Windows protected service installed")

            except Exception as e:
                raise Exception(f"Failed to setup Windows service protection: {e}")

        #
        # -------------------------------------------------------
        # LINUX PROTECTION
        # -------------------------------------------------------
        #
        elif system == "Linux":
            try:
                service = f"""
    [Unit]
    Description=SysLogger Client (Protected)
    After=network.target

    [Service]
    ExecStart={python} {client_script} --start
    Restart=always
    RestartSec=10

    # ---- HARDENING ----
    NoNewPrivileges=yes
    PrivateTmp=yes
    ProtectSystem=strict
    ProtectHome=yes
    ReadWritePaths={PROJECT_ROOT}

    # High priority
    Nice=-10

    [Install]
    WantedBy=multi-user.target
    """

                service_path = Path("/etc/systemd/system/syslogger-client-protected.service")

                # Write service file
                with open(service_path, "w") as f:
                    f.write(service)

                # Enable it
                subprocess.run(["sudo", "systemctl", "daemon-reload"], check=True)
                subprocess.run(["sudo", "systemctl", "enable",
                                "syslogger-client-protected.service"], check=True)

                self.log("✓ Linux protected systemd service installed")

            except Exception as e:
                raise Exception(f"Failed to setup Linux protection: {e}")

        #
        # -------------------------------------------------------
        # MACOS PROTECTION
        # -------------------------------------------------------
        #
        elif system == "Darwin":
            try:
                plist = f"""<?xml version="1.0" encoding="UTF-8"?>
    <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" 
    "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
    <plist version="1.0">
    <dict>
        <key>Label</key>
        <string>com.syslogger.client.protected</string>

        <key>ProgramArguments</key>
        <array>
            <string>{python}</string>
            <string>{client_script}</string>
            <string>--start</string>
        </array>

        <key>RunAtLoad</key><true/>

        <key>KeepAlive</key>
        <dict>
            <key>SuccessfulExit</key><false/>
        </dict>

        <key>Nice</key><integer>-10</integer>
    </dict>
    </plist>
    """

                plist_path = Path("/Library/LaunchDaemons/com.syslogger.client.protected.plist")

                # write plist
                with open(plist_path, "w") as f:
                    f.write(plist)

                # Load it
                subprocess.run(["sudo", "launchctl", "load", str(plist_path)], check=True)

                self.log("✓ macOS protected launchd daemon installed")

            except Exception as e:
                raise Exception(f"Failed to setup macOS protected daemon: {e}")

        #
        # -------------------------------------------------------
        # WATCHDOG SCRIPT (Cross-platform)
        # -------------------------------------------------------
        #
        self.progress(60, "Creating watchdog process...")

        watchdog_script = f"""#!/usr/bin/env bash
    # SysLogger Watchdog
    CLIENT_COMMAND="{python} {client_script} --start"

    while true; do
        if ! pgrep -f "$CLIENT_COMMAND" > /dev/null; then
            echo "$(date): SysLogger client not running, restarting..."
            {python} {client_script} --start &
        fi
        sleep 30
    done
    """

        watchdog_path = PROJECT_ROOT / "client_watchdog.sh"

        try:
            watchdog_path.write_text(watchdog_script)
            os.chmod(watchdog_path, 0o755)

            # Start watchdog silently
            subprocess.Popen(
                ["nohup", str(watchdog_path)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

            self.log("✓ Watchdog installed & running")

        except Exception as e:
            raise Exception(f"Failed to install watchdog: {e}")

        #
        # Finalize
        #
        self.progress(100, "Protection configured")
        self.log("✔ Protection mechanisms fully configured")

        # -------------------------
        # Domain Update Service
        # -------------------------
    def op_handle_domain_updates(self):
        self.progress(20, "Installing domain updater...")

        updater_script = f"""
#!/usr/bin/env python3
import time, json, requests, os
CONFIG="{CLIENT_CONFIG_FILE}"

while True:
    if os.path.exists(CONFIG):
        cfg=json.load(open(CONFIG))
        url=cfg.get("server_url")
        if url:
            try:
                r=requests.get(f"{{url}}/api/domain_config",timeout=10)
                if r.status_code==200:
                    cfg.update(r.json())
                    json.dump(cfg,open(CONFIG,"w"),indent=4)
            except:
                pass
    time.sleep(3600)
"""

        path = PROJECT_ROOT / "domain_updater.py"
        path.write_text(updater_script)

        subprocess.Popen([sys.executable, str(path)])

        self.progress(100, "Domain updater active")

    # ===================================================================
    # Helpers
    # ===================================================================
    def _load_cfg(self):
        if CLIENT_CONFIG_FILE.exists():
            return json.loads(CLIENT_CONFIG_FILE.read_text())
        return {}

    def _save_cfg(self, cfg):
        json.dump(cfg, open(CLIENT_CONFIG_FILE, "w"), indent=4)

    def _check_write_permissions(self):
        try:
            test_file = PROJECT_ROOT / "test_write.tmp"
            test_file.write_text("test")
            test_file.unlink()
            return True
        except:
            return False

    def _check_network_connectivity(self):
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=5)
            return True
        except:
            return False

    def _collect_system_info(self, sid):
        hostname = socket.gethostname()
        os_info = f"{platform.system()} {platform.release()}"

        ram = psutil.virtual_memory().total / (1024 ** 3) if PSUTIL_AVAILABLE else 0
        cpu = platform.processor()

        gpu_info = {}
        if GPUUTIL_AVAILABLE:
            try:
                gpus = GPUtil.getGPUs()
                gpu_info = {
                    "count": len(gpus),
                    "details": [{"name": g.name, "memory": g.memoryTotal} for g in gpus]
                }
            except:
                gpu_info = {"count": 0, "details": []}

        return {
            "system_id": sid,
            "hostname": hostname,
            "os_info": os_info,
            "cpu_info": cpu,
            "ram_total": round(ram, 2),
            "gpu_info": json.dumps(gpu_info)
        }


# ===================================================================
# MAIN
# ===================================================================
if __name__ == "__main__":
    InstallerGUI().mainloop()

