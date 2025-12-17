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
import shutil

import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk

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

        self.title("Server Installer - Sys Logger")
        self.geometry("1400x850")
        self.configure(bg="#e0f2fe")
        self.prereq_passed = False
        self.buttons = {}

        self._init_style()
        self._init_icons()
        self._init_tooltips()
        self._init_logging()
        self._init_ui()

    # ----------------------------------------------------------------------
    # Styles & logging
    # ----------------------------------------------------------------------
    def _init_style(self):
        style = ttk.Style(self)
        style.theme_use("clam")

        # Purple/indigo themed buttons matching client_installer.py
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

        # Card frames with subtle shadow
        style.configure("Card.TLabelframe",
                        background="white",
                        borderwidth=3,
                        relief="raised")
        style.configure("Card.TLabelframe.Label",
                        font=("Segoe UI", 11, "bold"))

        # Wizard navigation buttons
        style.configure("Wizard.TButton",
                        font=("Segoe UI", 10, "bold"),
                        padding=(8, 4))
        style.map("Wizard.TButton",
                  background=[("active", "#e0e7ff"), ("pressed", "#c7d2fe")])

        # Loading spinner style
        style.configure("Spinner.TLabel",
                        font=("Segoe UI", 10),
                        foreground="#6366f1")

    def _init_icons(self):
        # Create simple icons using PIL (fallback if images not available)
        self.icons = {}
        try:
            # Create checkmark icon
            img = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
            self.icons['check'] = ImageTk.PhotoImage(img)

            # Create error icon
            img = Image.new('RGBA', (16, 16), (220, 38, 38, 255))
            self.icons['error'] = ImageTk.PhotoImage(img)

            # Create loading spinner frames
            self.spinner_frames = []
            for i in range(8):
                img = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
                self.spinner_frames.append(ImageTk.PhotoImage(img))

        except Exception as e:
            self.log(f"Icon creation failed: {e}")

    def _init_tooltips(self):
        # Tooltip functionality
        self.tooltip_labels = {}

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
        self.grid_rowconfigure(2, weight=0)

        # Top title
        title = tk.Label(
            self,
            text="📋 Krishi Sahayogi Server Installer",
            font=("Segoe UI", 24, "bold"),
            bg="#e0f2fe",
            fg="#1f2937"
        )
        title.grid(row=0, column=0, pady=(20, 10))

        # Main frame
        main = tk.Frame(self, bg="#e0f2fe")
        main.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        main.grid_columnconfigure(0, weight=1)
        main.grid_columnconfigure(1, weight=2)
        main.grid_rowconfigure(0, weight=1)

        # Left column (wizard steps)
        left = tk.Frame(main, bg="#ffffff", relief="raised", borderwidth=2)
        left.grid(row=0, column=0, sticky="nwe", padx=(0, 15))
        left.grid_columnconfigure(0, weight=1)

        # Right column (step content + progress + log)
        right = tk.Frame(main, bg="#e0f2fe")
        right.grid(row=0, column=1, sticky="nsew")
        right.grid_rowconfigure(2, weight=1)
        right.grid_columnconfigure(0, weight=1)

        # Wizard navigation
        nav_frame = tk.Frame(self, bg="#e0f2fe")
        nav_frame.grid(row=2, column=0, pady=(10, 20))
        nav_frame.grid_columnconfigure(1, weight=1)

        self.back_button = ttk.Button(nav_frame, text="⬅️ Back", style="Wizard.TButton",
                                    command=self.wizard_back, state="disabled")
        self.back_button.pack(side="left", padx=10)

        self.next_button = ttk.Button(nav_frame, text="Next ➡️", style="Wizard.TButton",
                                    command=self.wizard_next)
        self.next_button.pack(side="left", padx=10)

        self.finish_button = ttk.Button(nav_frame, text="✅ Finish Installation",
                                      style="Wizard.TButton", command=self.wizard_finish, state="disabled")
        self.finish_button.pack(side="right", padx=10)

        # ----------------- Groups on LEFT -----------------

        # Left panel: Step indicators
        steps_title = tk.Label(left, text="Installation Steps",
                              font=("Segoe UI", 16, "bold"), bg="white", fg="#1f2937")
        steps_title.pack(pady=20, padx=20)

        self.step_indicators = []
        step_names = [
            ("Prerequisites Check", "🔍"),
            ("Database Setup", "🐘"),
            ("Domain Configuration", "🔗"),
            ("Installation Progress", "⚙️")
        ]

        for i, (name, icon) in enumerate(step_names):
            step_frame = ttk.Frame(left, style="Card.TFrame")
            step_frame.pack(fill="x", padx=15, pady=5)
            step_frame.grid_columnconfigure(1, weight=1)

            # Step number/icon
            indicator = tk.Label(step_frame, text=f"{i+1}. {icon}", bg="white",
                               font=("Segoe UI", 12, "bold"), fg="#6366f1")
            indicator.grid(row=0, column=0, padx=(10, 5), pady=10, sticky="w")

            # Step name
            name_label = tk.Label(step_frame, text=name, bg="white",
                                font=("Segoe UI", 10), fg="#374151")
            name_label.grid(row=0, column=1, padx=(0, 10), pady=10, sticky="w")

            # Status
            status_label = tk.Label(step_frame, text="⏳ Pending", bg="white",
                                  font=("Segoe UI", 9), fg="#6b7280")
            status_label.grid(row=0, column=2, padx=10, pady=10, sticky="e")

            self.step_indicators.append((indicator, name_label, status_label))

        # Action buttons for current step
        actions_frame = ttk.Frame(left, style="Card.TFrame")
        actions_frame.pack(fill="x", padx=15, pady=20)

        self.step_action_buttons = {
            0: ttk.Button(actions_frame, text="🔍 Check Prerequisites", command=self.execute_current_step),
            1: ttk.Button(actions_frame, text="🐘 Configure Database", command=self.execute_current_step),
            2: ttk.Button(actions_frame, text="🔗 Configure Domain", command=self.execute_current_step),
            3: ttk.Button(actions_frame, text="⚙️ Start Installation", command=self.execute_current_step)
        }

        for btn in self.step_action_buttons.values():
            btn.pack(fill="x", padx=15, pady=15)
            btn.pack_forget()  # Hide all initially

        self.step_action_button = self.step_action_buttons[0]  # Default to first
        self.step_action_button.pack(fill="x", padx=15, pady=15)

        # Create step content areas on right
        self.step_content_frames = []

        # Step 0: Prerequisites
        prereq_frame = ttk.Frame(right, style="Card.TFrame")
        prereq_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        tk.Label(prereq_frame, text="Check system prerequisites before proceeding",
                font=("Segoe UI", 14, "bold"), bg="white", fg="#1f2937").pack(pady=20)
        tk.Label(prereq_frame, text="This step verifies that Python, Node.js, Docker, and other\nrequired components are installed and properly configured.",
                bg="white", fg="#6b7280", font=("Segoe UI", 10)).pack(pady=(0, 20))
        self.step_content_frames.append(prereq_frame)

        # Step 1: Database Setup
        db_frame = ttk.Frame(right, style="Card.TFrame")
        db_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        tk.Label(db_frame, text="Database Configuration",
                font=("Segoe UI", 14, "bold"), bg="white", fg="#1f2937").pack(pady=20)

        # PostgreSQL toggle
        toggle_frame = ttk.Frame(db_frame, style="Card.TFrame")
        toggle_frame.pack(fill="x", padx=20, pady=5)
        tk.Label(toggle_frame, text="Use PostgreSQL Database:", bg="white",
                font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(10, 5))

        self.use_postgres = tk.BooleanVar(value=False)
        postgres_check = ttk.Checkbutton(toggle_frame, text="Enable PostgreSQL (requires installation)",
                                         variable=self.use_postgres, command=self.toggle_db_mode)
        postgres_check.pack(anchor="w", padx=10, pady=(0, 10))

        self.db_description = tk.Label(toggle_frame, text="Using SQLite database (no additional setup required).",
                                      bg="white", fg="#6b7280", font=("Segoe UI", 10), justify="left")
        self.db_description.pack(anchor="w", padx=10, pady=(0, 10))

        self.step_content_frames.append(db_frame)

        # Step 2: Domain Configuration
        dom_frame = ttk.Frame(right, style="Card.TFrame")
        dom_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        tk.Label(dom_frame, text="Configure Domain Settings",
                font=("Segoe UI", 14, "bold"), bg="white", fg="#1f2937").pack(pady=20)

        # Backend domain
        backend_frame = ttk.Frame(dom_frame, style="Card.TFrame")
        backend_frame.pack(fill="x", padx=20, pady=5)
        tk.Label(backend_frame, text="Backend Domain:", bg="white",
                font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(10, 2))
        self.backend_domain = tk.Entry(backend_frame, font=("Segoe UI", 10))
        self.backend_domain.insert(0, "http://localhost:8000")
        self.backend_domain.pack(fill="x", padx=10, pady=(0, 10))
        self.backend_validation = tk.Label(backend_frame, text="", bg="white",
                                         fg="#dc2626", font=("Segoe UI", 9))
        self.backend_validation.pack(anchor="w", padx=10)

        # Frontend domain
        frontend_frame = ttk.Frame(dom_frame, style="Card.TFrame")
        frontend_frame.pack(fill="x", padx=20, pady=5)
        tk.Label(frontend_frame, text="Frontend Domain:", bg="white",
                font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(10, 2))
        self.frontend_domain = tk.Entry(frontend_frame, font=("Segoe UI", 10))
        self.frontend_domain.insert(0, "http://localhost:5000")
        self.frontend_domain.pack(fill="x", padx=10, pady=(0, 10))
        self.frontend_validation = tk.Label(frontend_frame, text="", bg="white",
                                          fg="#dc2626", font=("Segoe UI", 9))
        self.frontend_validation.pack(anchor="w", padx=10)

        # Server Host
        host_frame = ttk.Frame(dom_frame, style="Card.TFrame")
        host_frame.pack(fill="x", padx=20, pady=5)
        tk.Label(host_frame, text="Server Host (IP to bind to):", bg="white",
                font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(10, 2))
        self.server_host = tk.Entry(host_frame, font=("Segoe UI", 10))
        self.server_host.insert(0, "0.0.0.0")
        self.server_host.pack(fill="x", padx=10, pady=(0, 10))

        # Server Port
        port_frame = ttk.Frame(dom_frame, style="Card.TFrame")
        port_frame.pack(fill="x", padx=20, pady=5)
        tk.Label(port_frame, text="Server Port:", bg="white",
                font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(10, 2))
        self.server_port = tk.Entry(port_frame, font=("Segoe UI", 10))
        self.server_port.insert(0, "8000")
        self.server_port.pack(fill="x", padx=10, pady=(0, 10))

        # Bind validation
        self.backend_domain.bind('<FocusOut>', lambda e: self.validate_domain('backend'))
        self.frontend_domain.bind('<FocusOut>', lambda e: self.validate_domain('frontend'))

        self.step_content_frames.append(dom_frame)

        # Step 3: Installation Progress
        install_frame = ttk.Frame(right, style="Card.TFrame")
        install_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        tk.Label(install_frame, text="Installation Progress",
                font=("Segoe UI", 14, "bold"), bg="white", fg="#1f2937").pack(pady=20)
        tk.Label(install_frame, text="Execute the full installation process including database setup\n(if selected), startup configuration, protection setup,\nserver setup script, and server startup.",
                bg="white", fg="#6b7280", font=("Segoe UI", 10), justify="left").pack(pady=(0, 20))
        self.step_content_frames.append(install_frame)

        # Initialize wizard state
        self.current_step = 0
        self.steps_completed = [False] * len(self.step_content_frames)
        self.show_step(0)

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
    # Wizard navigation methods
    # ----------------------------------------------------------------------
    def show_step(self, step_index):
        # Hide all step frames
        for frame in self.step_content_frames:
            frame.grid_remove()

        # Hide all action buttons
        for btn in self.step_action_buttons.values():
            btn.pack_forget()

        # Show selected step
        if 0 <= step_index < len(self.step_content_frames):
            self.step_content_frames[step_index].grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
            self.current_step = step_index

            # Show appropriate action button
            if step_index in self.step_action_buttons:
                self.step_action_buttons[step_index].pack(fill="x", padx=15, pady=15)

        # Update navigation buttons
        self.back_button.config(state="normal" if step_index > 0 else "disabled")
        self.next_button.config(state="normal" if step_index < len(self.step_content_frames) - 1 else "disabled")
        self.finish_button.config(state="normal" if all(self.steps_completed) else "disabled")

    def wizard_back(self):
        if self.current_step > 0:
            self.show_step(self.current_step - 1)

    def wizard_next(self):
        if self.current_step < len(self.step_content_frames) - 1:
            # Validate current step before proceeding
            if self.validate_current_step():
                self.steps_completed[self.current_step] = True
                self.show_step(self.current_step + 1)
            else:
                messagebox.showwarning("Validation Error", "Please correct the errors before proceeding.")

    def wizard_finish(self):
        if all(self.steps_completed):
            messagebox.showinfo("Installation Complete", "All steps have been completed successfully!")
        else:
            messagebox.showwarning("Incomplete Installation", "Please complete all steps before finishing.")

    def validate_current_step(self):
        if self.current_step == 2:  # Domain configuration step
            return self.validate_domain('backend') and self.validate_domain('frontend')
        return True

    def execute_current_step(self):
        """Execute the action for the current step."""
        if self.current_step == 0:
            self.run_prereq_check()
        elif self.current_step == 1:
            if self.use_postgres.get():
                self.run_postgres_setup()
            else:
                self.log("Using SQLite - No configuration needed.")
                self.progress(100, "Database configuration complete")
        elif self.current_step == 2:
            self.run_domain_config()
        elif self.current_step == 3:
            backend = self.backend_domain.get().strip()
            frontend = self.frontend_domain.get().strip()
            host = self.server_host.get().strip()
            port = self.server_port.get().strip()
            use_pg = self.use_postgres.get()
            self.start_worker("full_installation", backend, frontend, use_pg, host, port)

    def toggle_db_mode(self):
        """Update description based on PostgreSQL toggle"""
        if self.use_postgres.get():
            self.db_description.config(text="Using PostgreSQL database (requires PostgreSQL installation and psycopg2).")
        else:
            self.db_description.config(text="Using SQLite database (no additional setup required).")

    def validate_domain(self, domain_type):
        domain = self.backend_domain.get().strip() if domain_type == 'backend' else self.frontend_domain.get().strip()
        validation_label = self.backend_validation if domain_type == 'backend' else self.frontend_validation

        if not domain:
            validation_label.config(text="Domain cannot be empty")
            return False

        # Basic URL validation
        if not re.match(r'^https?://', domain):
            validation_label.config(text="Must start with http:// or https://")
            return False

        # Check for localhost or valid hostname/IP
        url_part = domain[8:] if domain.startswith('https://') else domain[7:]
        if not url_part or '/' in url_part:
            validation_label.config(text="Invalid domain format")
            return False

        validation_label.config(text="")
        return True

    # ----------------------------------------------------------------------
    # Helper UI methods
    # ----------------------------------------------------------------------
    def log(self, msg: str, color=None):
        print(msg)
        self.logger.info(msg)

        # Colorize log messages
        if color:
            colored_msg = f"[{color}]{msg}[/{color}]"
        else:
            colored_msg = msg

        self.log_widget.insert("end", msg + "\n")
        self.log_widget.see("end")

    def progress(self, value: int, msg: str):
        # schedule UI updates on main thread
        def _update():
            self.progress_var.set(value)
            self.current_op_label.config(text=msg)
            if value > 0:
                self.start_spinner()
            elif value >= 100:
                self.stop_spinner()
            self.log(msg, "green" if value == 100 else "blue")
        self.after(0, _update)

    def start_spinner(self):
        if not self.is_spinning:
            self.is_spinning = True
            self.animate_spinner()

    def stop_spinner(self):
        self.is_spinning = False
        self.spinner_label.config(text="✅")

    def animate_spinner(self):
        if not self.is_spinning:
            return
        spinner_chars = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        current = getattr(self, 'spinner_index', 0)
        self.spinner_label.config(text=spinner_chars[current])
        self.spinner_index = (current + 1) % len(spinner_chars)
        self.after(100, self.animate_spinner)

    def show_error(self, msg: str):
        def _show():
            messagebox.showerror("Error", msg)
            self.stop_spinner()
        self.after(0, _show)

    def show_tooltip(self, widget, text):
        def enter(event):
            tooltip = tk.Toplevel(widget)
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")

            label = tk.Label(tooltip, text=text, bg="#ffffe0", relief="solid", borderwidth=1)
            label.pack()

            self.tooltip_labels[widget] = tooltip

        def leave(event):
            if widget in self.tooltip_labels:
                self.tooltip_labels[widget].destroy()
                del self.tooltip_labels[widget]

        widget.bind("<Enter>", enter)
        widget.bind("<Leave>", leave)

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
        host = self.server_host.get().strip()
        port = self.server_port.get().strip()
        self.start_worker("domain_config", backend, frontend, host, port)

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

        python_exe = self._get_python_executable()
        result = subprocess.run(
            [python_exe, str(SERVER_SETUP_FILE)],
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

        python_exe = self._get_python_executable()
        result = subprocess.run(
            [python_exe, str(sys_logger_path), "--service"],
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
            # Check system python version via subprocess, not internal frozen version
            python_exe = self._get_python_executable() or "python"
            result = subprocess.run([python_exe, "--version"], capture_output=True, text=True)
            # Output format: "Python 3.x.y"
            version_str = result.stdout.strip().split()[-1]
            version = tuple(map(int, version_str.split(".")[:2]))
            return version >= REQUIRED_PYTHON_VERSION
        except Exception as e:
            self.log(f"Python check failed: {e}")
            return False

    def _get_python_executable(self):
        """Resolve system python executable, handling frozen state."""
        # If frozen, we can't use sys.executable (it's the installer EXE)
        # We must find the system python.
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
             # Try standard names
             if platform.system() == "Windows":
                 return shutil.which("python") or shutil.which("py")
             else:
                 return shutil.which("python3") or shutil.which("python")
        
        # If not frozen, sys.executable is the correct python interpreter
        return sys.executable

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

    def _install_package(self, package_name):
        """Install a Python package using pip."""
        try:
            self.log(f"Installing {package_name}...")
            python_exe = self._get_python_executable()
            result = subprocess.run([python_exe, "-m", "pip", "install", package_name],
                                    capture_output=True, text=True, check=True)
            self.log(f"✓ {package_name} installed successfully")
            return True
        except subprocess.CalledProcessError as e:
            self.log(f"❌ Failed to install {package_name}: {e.stderr}")
            return False

    def _check_and_install_dep(self, package_name, optional=False):
        """Check if package is available, install if not."""
        if package_name == "psycopg2":
            if PSYCOPG_AVAILABLE:
                return True
            else:
                return self._install_package("psycopg2")

    # ---------------------- PostgreSQL setup ----------------------
    def op_postgres_setup(self):
        global PSYCOPG_AVAILABLE
        if not PSYCOPG_AVAILABLE:
            self.log("Installing psycopg2...")
            self._install_package("psycopg2")
            try:
                import psycopg2
                from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
                PSYCOPG_AVAILABLE = True
            except ImportError:
                raise Exception("Failed to install psycopg2")

        self.progress(10, "Checking PostgreSQL installation...")

        system = platform.system()
        psql_available = False

        try:
            subprocess.run(
                ["psql", "--version"],
                check=True,
                capture_output=True
            )
            psql_available = True
        except:
            self.log("PostgreSQL not found, installing automatically...")

        if not psql_available:
            # Auto-install PostgreSQL
            if system == "Windows":
                self.progress(15, "Installing PostgreSQL on Windows...")
                # Try Chocolatey first
                try:
                    subprocess.run(["choco", "install", "postgresql", "-y"], check=True)
                except:
                    # Fallback to manual download
                    self.log("Chocolatey failed, trying manual installation...")
                    self._install_postgres_windows()
            elif system == "Linux":
                self.progress(15, "Installing PostgreSQL on Linux...")
                # Try apt (Ubuntu/Debian)
                try:
                    subprocess.run(["sudo", "apt", "update"], check=True)
                    subprocess.run(["sudo", "apt", "install", "-y", "postgresql", "postgresql-contrib"], check=True)
                except:
                    # Try yum (CentOS/RHEL)
                    try:
                        subprocess.run(["sudo", "yum", "install", "-y", "postgresql-server", "postgresql-contrib"], check=True)
                        subprocess.run(["sudo", "postgresql-setup", "initdb"], check=True)
                    except:
                        raise Exception("Failed to install PostgreSQL. Please install manually.")
            elif system == "Darwin":
                self.progress(15, "Installing PostgreSQL on macOS...")
                try:
                    subprocess.run(["brew", "install", "postgresql"], check=True)
                except:
                    raise Exception("Failed to install PostgreSQL. Please install Homebrew and PostgreSQL manually.")

        # Verify installation
        try:
            subprocess.run(
                ["psql", "--version"],
                check=True,
                capture_output=True
            )
            self.log("PostgreSQL installed successfully")
        except:
            raise Exception("PostgreSQL installation failed")

        # Start service and enable on boot
        self.progress(20, "Starting PostgreSQL service...")
        self._start_postgres_service()

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

    # ---------------------- Full installation ----------------------
    def op_full_installation(self, backend_domain, frontend_domain, use_postgres, host, port):
        total_steps = 6 if use_postgres else 5  # postgres_setup adds one step
        current_step = 0

        def update_progress(step_name, step_pct):
            nonlocal current_step
            overall_pct = int((current_step * 100 + step_pct) / total_steps)
            self.progress(overall_pct, f"{step_name}: {step_pct}%")

        # Step 1: Domain configuration
        update_progress("Domain config", 10)
        
        self.op_domain_config(backend_domain, frontend_domain, host, port)
        current_step += 1

        # Step 2: Startup configuration
        update_progress("Startup config", 20)
        self.op_startup_config()
        current_step += 1

        # Step 3: Protection setup
        update_progress("Protection setup", 40)
        self.op_protection_setup()
        current_step += 1

        # Step 4: PostgreSQL setup (if selected)
        if use_postgres:
            update_progress("PostgreSQL setup", 60)
            self.op_postgres_setup()
            current_step += 1

        # Step 5: Run server setup
        update_progress("Server setup", 80)
        self.op_run_server_setup()
        current_step += 1

        # Step 6: Start server
        update_progress("Starting server", 100)
        self.op_start_server()
        current_step += 1

        self.progress(100, "Installation completed successfully!")

    # ---------------------- Domain configuration ----------------------
    def op_domain_config(self, backend_domain, frontend_domain, host, port):
        self.progress(20, "Updating backend .env...")

        backend_env = PROJECT_ROOT / "backend" / ".env"
        backend_env.parent.mkdir(exist_ok=True)

        with open(backend_env, "w") as f:
            f.write(
                "FLASK_ENV=production\n"
                f"PORT={port}\n"
                f"HOST={host}\n"
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
            # Start both backend and PostgreSQL on startup
            python_exe = self._get_python_executable()
            cmd = (
                f'cmd /c "net start postgresql && cd /d {PROJECT_ROOT} && '
                f'"{python_exe}" backend/sys_logger.py --service"'
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
