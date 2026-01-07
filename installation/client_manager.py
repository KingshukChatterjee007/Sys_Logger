import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import json
import os
import platform
import subprocess
import zipfile
from pathlib import Path

# Constants
PROJECT_ROOT = Path(__file__).parent
CLIENT_INSTALLER_SCRIPT = PROJECT_ROOT / "client_installer.py"
SPEC_FILE = PROJECT_ROOT / "SysLogger_Client_Installer.spec"
CONFIG_FILE = PROJECT_ROOT.parent / "unit_client_config.json"
UNIT_CLIENT_SCRIPT = PROJECT_ROOT.parent / "unit_client.py"

class ClientManagerGUI(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("SysLogger Client Manager")
        self.geometry("1200x900")
        self.configure(bg="#f0f4f8")
        self.resizable(True, True)  # Make window resizable

        self.server_url = tk.StringVar(value="http://localhost:5000")
        self.server_host = tk.StringVar(value="localhost")
        self.server_port = tk.StringVar(value="5000")
        self.load_config()

        self.build_running = False
        self.server_running = False
        self.server_process = None

        self._init_style()
        self._init_ui()

    def _init_style(self):
        style = ttk.Style(self)
        style.theme_use("clam")

        # Enhanced button styling with modern gradient-like appearance
        style.configure("TButton", font=("Segoe UI", 14, "bold"), padding=(15, 10),
                        background="#4f46e5", foreground="white", relief="flat", borderwidth=0)
        style.map("TButton",
                  background=[("active", "#4338ca"), ("pressed", "#3730a3")],
                  relief=[("pressed", "sunken")])

        # Enhanced label styling with larger fonts and varied weights
        style.configure("TLabel", font=("Segoe UI", 12), background="#ffffff")
        style.configure("Title.TLabel", font=("Segoe UI", 18, "bold"), background="#ffffff")
        style.configure("Subtitle.TLabel", font=("Segoe UI", 15, "bold"), background="#ffffff")

        # Enhanced frame styling with consistent color scheme
        style.configure("Card.TFrame", background="#ffffff", relief="raised", borderwidth=2, lightcolor="#cbd5e1")

    def _init_ui(self):
        # Create elegant scrollable canvas with gradient background
        self.main_canvas = tk.Canvas(
            self,
            bg="#f8fafc",
            highlightthickness=0,
            relief="flat"
        )
        self.main_canvas.pack(side="left", fill="both", expand=True, padx=2, pady=2)

        # Create elegant scrollbar with custom styling
        scrollbar_style = ttk.Style()
        scrollbar_style.configure(
            "Elegant.Vertical.TScrollbar",
            background="#e2e8f0",
            troughcolor="#f1f5f9",
            borderwidth=0,
            lightcolor="#cbd5e1",
            darkcolor="#94a3b8"
        )

        scrollbar = ttk.Scrollbar(
            self,
            orient="vertical",
            command=self.main_canvas.yview,
            style="Elegant.Vertical.TScrollbar"
        )
        scrollbar.pack(side="right", fill="y", padx=(0,2), pady=2)

        self.main_canvas.configure(yscrollcommand=scrollbar.set)

        # Create elegant inner frame with padding
        main_frame = tk.Frame(
            self.main_canvas,
            bg="#ffffff",
            relief="flat"
        )
        self.main_canvas.create_window((0,0), window=main_frame, anchor="nw")

        # Add subtle shadow effect to the main frame
        main_frame.config(highlightbackground="#e2e8f0", highlightthickness=1)

        # Bind mousewheel to canvas with smooth scrolling
        def _on_mousewheel(event):
            self.main_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        self.main_canvas.bind_all("<MouseWheel>", _on_mousewheel)

        # Configure canvas to update scrollregion when frame changes
        def update_scrollregion(event=None):
            self.main_canvas.configure(scrollregion=self.main_canvas.bbox("all"))
            # Add some padding at the bottom
            bbox = self.main_canvas.bbox("all")
            if bbox:
                self.main_canvas.configure(scrollregion=(0, 0, bbox[2], bbox[3] + 50))

        main_frame.bind('<Configure>', update_scrollregion)

        # Initial update
        self.after(100, update_scrollregion)

        # Title
        title = tk.Label(main_frame, text="🛠️ SysLogger Client Manager",
                        font=("Segoe UI", 28, "bold"), bg="white", fg="#1e293b")
        title.pack(pady=25)

        # Configuration Section
        config_frame = ttk.Frame(main_frame, style="Card.TFrame")
        config_frame.pack(fill="x", padx=20, pady=10)

        config_title = tk.Label(config_frame, text="⚙️ Configuration",
                               font=("Segoe UI", 16, "bold"), bg="white", fg="#374151")
        config_title.pack(pady=10)

        # Server URL input
        url_frame = ttk.Frame(config_frame, style="Card.TFrame")
        url_frame.pack(fill="x", padx=20, pady=10)
        tk.Label(url_frame, text="Server URL:", bg="white", font=("Segoe UI", 14)).pack(side="left")
        ttk.Entry(url_frame, textvariable=self.server_url, font=("Segoe UI", 14)).pack(side="left", fill="x", expand=True, padx=(15,0))
        ttk.Button(url_frame, text="Save", command=self.save_config).pack(side="right", padx=(15,0))

        # Server Host/Port
        host_port_frame = ttk.Frame(config_frame, style="Card.TFrame")
        host_port_frame.pack(fill="x", padx=15, pady=5)
        tk.Label(host_port_frame, text="Host:", bg="white", font=("Segoe UI", 14)).grid(row=0, column=0, sticky="w")
        ttk.Entry(host_port_frame, textvariable=self.server_host, font=("Segoe UI", 14)).grid(row=0, column=1, padx=(15,5), sticky="ew")
        tk.Label(host_port_frame, text="Port:", bg="white", font=("Segoe UI", 14)).grid(row=0, column=2, padx=(15,5))
        ttk.Entry(host_port_frame, textvariable=self.server_port, font=("Segoe UI", 14)).grid(row=0, column=3, padx=(0,15), sticky="ew")
        host_port_frame.grid_columnconfigure(1, weight=1)
        host_port_frame.grid_columnconfigure(3, weight=1)

        # Server Management Section
        server_frame = ttk.Frame(main_frame, style="Card.TFrame")
        server_frame.pack(fill="x", padx=20, pady=10)

        server_title = tk.Label(server_frame, text="🖥️ Server Management",
                               font=("Segoe UI", 16, "bold"), bg="white", fg="#374151")
        server_title.pack(pady=10)

        # Server status and controls
        status_frame = ttk.Frame(server_frame, style="Card.TFrame")
        status_frame.pack(fill="x", padx=15, pady=5)

        self.server_status_label = tk.Label(status_frame, text="🔴 Server Status: Stopped",
                                           bg="white", font=("Segoe UI", 12, "bold"), fg="#dc2626")
        self.server_status_label.pack(side="left")

        control_frame = ttk.Frame(status_frame, style="Card.TFrame")
        control_frame.pack(side="right")

        self.start_server_btn = ttk.Button(control_frame, text="Start Server", command=self.start_server)
        self.start_server_btn.pack(side="left", padx=(0,10))

        self.stop_server_btn = ttk.Button(control_frame, text="Stop Server", command=self.stop_server, state="disabled")
        self.stop_server_btn.pack(side="left")

        # Package Generation Section
        package_frame = ttk.Frame(main_frame, style="Card.TFrame")
        package_frame.pack(fill="x", padx=20, pady=20)

        package_title = tk.Label(package_frame, text="📦 Package Generation",
                                font=("Segoe UI", 18, "bold"), bg="white", fg="#374151")
        package_title.pack(pady=10)

        # Buttons for Windows and Linux
        button_frame = ttk.Frame(package_frame, style="Card.TFrame")
        button_frame.pack(pady=10)

        current_platform = platform.system().lower()
        if current_platform == "windows":
            ttk.Button(button_frame, text="Generate Windows Package", command=self.generate_windows_package).pack(side="left", padx=20)
        elif current_platform == "linux":
            ttk.Button(button_frame, text="Generate Linux Package", command=self.generate_linux_package).pack(side="left", padx=20)
        else:
            tk.Label(button_frame, text="Package generation not supported on this platform", bg="white", fg="#dc2626").pack()

        # Progress Section
        progress_frame = ttk.Frame(main_frame, style="Card.TFrame")
        progress_frame.pack(fill="x", padx=20, pady=10)

        progress_title = tk.Label(progress_frame, text="📈 Progress",
                                 font=("Segoe UI", 16, "bold"), bg="white", fg="#374151")
        progress_title.pack(pady=10)

        self.progress_var = tk.IntVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, length=800)
        self.progress_bar.pack(pady=10, padx=25)

        # Log Display
        log_frame = ttk.Frame(main_frame, style="Card.TFrame")
        log_frame.pack(fill="both", expand=True, padx=20, pady=10)

        log_title = tk.Label(log_frame, text="📋 Activity Log",
                            font=("Segoe UI", 14, "bold"), bg="white", fg="#374151")
        log_title.pack(pady=10)

        text_frame = ttk.Frame(log_frame)
        text_frame.pack(fill="both", expand=True, padx=15, pady=(0,15))

        self.log_text = tk.Text(text_frame, bg="#f8fafc", fg="#1e293b", font=("Consolas", 10),
                               height=15, relief="sunken", borderwidth=2)
        self.log_text.pack(side="left", fill="both", expand=True)

        log_scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=self.log_text.yview)
        log_scrollbar.pack(side="right", fill="y")

        self.log_text.config(yscrollcommand=log_scrollbar.set)

        # Footer
        footer = tk.Label(main_frame, text="Product of NIELIT Bhubaneswar - Made by Krishi Sahayogi Team",
                         bg="white", fg="#64748b", font=("Segoe UI", 10, "italic"))
        footer.pack(pady=10)

        # Start server status monitoring
        self.after(1000, self.check_server_status)



    def save_config(self):
        try:
            config = {
                "server_url": self.server_url.get(),
                "server_host": self.server_host.get(),
                "server_port": self.server_port.get()
            }
            with open(CONFIG_FILE, 'w') as f:
                json.dump(config, f, indent=4)
            self.log("Configuration saved successfully")
            messagebox.showinfo("Success", "Configuration saved!")
        except Exception as e:
            self.log(f"Error saving config: {e}")
            messagebox.showerror("Error", f"Failed to save config: {e}")

    def load_config(self):
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, 'r') as f:
                    config = json.load(f)
                    self.server_url.set(config.get("server_url", "http://localhost:5000"))
                    self.server_host.set(config.get("server_host", "localhost"))
                    self.server_port.set(config.get("server_port", "5000"))
            except Exception as e:
                self.log(f"Warning: Could not load config: {e}")

    def log(self, message):
        self.log_text.insert("end", message + "\n")
        self.log_text.see("end")
        self.update_idletasks()

    def generate_windows_package(self):
        if self.build_running:
            messagebox.showwarning("Warning", "Build already running!")
            return
        threading.Thread(target=self.build_and_zip, args=("windows",), daemon=True).start()

    def generate_linux_package(self):
        if self.build_running:
            messagebox.showwarning("Warning", "Build already running!")
            return
        threading.Thread(target=self.build_and_zip, args=("linux",), daemon=True).start()

    def build_and_zip(self, target_platform):
        self.build_running = True
        try:
            self.progress_var.set(0)
            self.log(f"Starting {target_platform} package generation...")

            # Step 1: Check prerequisites
            self.check_prerequisites()
            self.progress_var.set(20)

            # Step 2: Build executable with PyInstaller
            self.build_executable(target_platform)
            self.progress_var.set(60)

            # Step 3: Create zip package
            self.create_zip_package(target_platform)
            self.progress_var.set(100)

            self.log(f"✓ {target_platform.capitalize()} package generated successfully!")
            messagebox.showinfo("Success", f"{target_platform.capitalize()} package generated!")

        except Exception as e:
            self.log(f"❌ Error: {str(e)}")
            messagebox.showerror("Error", f"Package generation failed: {str(e)}")
        finally:
            self.build_running = False





    def check_prerequisites(self):
        self.log("Checking prerequisites...")

        # Check if PyInstaller is available
        try:
            subprocess.run(["pyinstaller", "--version"], check=True, capture_output=True)
            self.log("✓ PyInstaller available")
        except subprocess.CalledProcessError:
            raise Exception("PyInstaller not installed. Please install with: pip install pyinstaller")

        # Check if spec file exists
        if not SPEC_FILE.exists():
            raise Exception(f"Spec file not found: {SPEC_FILE}")

        # Check if client installer script exists
        if not CLIENT_INSTALLER_SCRIPT.exists():
            raise Exception(f"Client installer script not found: {CLIENT_INSTALLER_SCRIPT}")

        self.log("Prerequisites check passed")

    def build_executable(self, target_platform):
        self.log(f"Building executable for {target_platform}...")

        # Run PyInstaller with the spec file
        cmd = ["pyinstaller", "--clean", str(SPEC_FILE)]
        try:
            result = subprocess.run(cmd, cwd=PROJECT_ROOT, capture_output=True, text=True, check=True)
            self.log("✓ Executable built successfully")
        except subprocess.CalledProcessError as e:
            raise Exception(f"PyInstaller build failed: {e.stderr}")

    def create_zip_package(self, target_platform):
        self.log(f"Creating zip package for {target_platform}...")

        # Determine output directory
        dist_dir = PROJECT_ROOT / "dist"
        exe_name = f"SysLogger_Client_Installer{'.exe' if target_platform == 'windows' else ''}"
        exe_path = dist_dir / exe_name

        if not exe_path.exists():
            # Try to find the executable in dist directory
            if dist_dir.exists():
                possible_executables = list(dist_dir.glob("SysLogger_Client_Installer*"))
                if possible_executables:
                    exe_path = possible_executables[0]  # Take the first match
                    exe_name = exe_path.name
                    self.log(f"Found executable: {exe_name}")
                else:
                    # List available files in dist directory for debugging
                    available_files = list(dist_dir.glob("*"))
                    self.log(f"Available files in dist directory: {[f.name for f in available_files]}")
                    raise Exception(f"No executable found in {dist_dir}")
            else:
                raise Exception(f"Dist directory not found: {dist_dir}")

        # Create zip file
        zip_name = f"SysLogger_Client_{target_platform.capitalize()}_Package.zip"
        zip_path = PROJECT_ROOT / zip_name

        try:
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Add executable
                zipf.write(exe_path, exe_name)
                self.log(f"✓ Added executable: {exe_name}")

                # Add config file
                if CONFIG_FILE.exists():
                    zipf.write(CONFIG_FILE, "unit_client_config.json")
                    self.log("✓ Added config file")
                else:
                    self.log("⚠ Config file not found")

                # Add unit client script
                if UNIT_CLIENT_SCRIPT.exists():
                    zipf.write(UNIT_CLIENT_SCRIPT, "unit_client.py")
                    self.log("✓ Added unit client script")
                else:
                    self.log("⚠ Unit client script not found")

                # Add other components as needed (watchdog.sh, etc.)
                watchdog_script = PROJECT_ROOT.parent / "watchdog.sh"
                if watchdog_script.exists():
                    zipf.write(watchdog_script, "watchdog.sh")
                    self.log("✓ Added watchdog script")

            self.log(f"✓ Zip package created: {zip_path}")

        except Exception as e:
            raise Exception(f"Failed to create zip package: {e}")

    def start_server(self):
        if self.server_running:
            messagebox.showwarning("Warning", "Server is already running!")
            return

        try:
            import sys
            sys.path.insert(0, str(PROJECT_ROOT.parent / "backend"))
            from sys_logger import app, socketio

            # Update server configuration
            import os
            os.environ['HOST'] = self.server_host.get()
            os.environ['PORT'] = self.server_port.get()

            # Start server in separate thread
            def run_server():
                socketio.run(app, host=self.server_host.get(), port=int(self.server_port.get()), debug=False)

            import threading
            server_thread = threading.Thread(target=run_server, daemon=True)
            server_thread.start()

            self.server_running = True
            self.server_status_label.config(text="🟢 Server Status: Running", fg="#16a34a")
            self.start_server_btn.config(state="disabled")
            self.stop_server_btn.config(state="normal")
            self.log("Server started successfully")

        except Exception as e:
            self.log(f"Failed to start server: {str(e)}")
            messagebox.showerror("Error", f"Failed to start server: {str(e)}")

    def stop_server(self):
        if not self.server_running:
            messagebox.showwarning("Warning", "Server is not running!")
            return

        try:
            # Note: Gracefully stopping Flask-SocketIO server requires more complex implementation
            # For now, we'll just update the UI state
            self.server_running = False
            self.server_status_label.config(text="🔴 Server Status: Stopped", fg="#dc2626")
            self.start_server_btn.config(state="normal")
            self.stop_server_btn.config(state="disabled")
            self.log("Server stopped")

        except Exception as e:
            self.log(f"Error stopping server: {str(e)}")

    def check_server_status(self):
        """Check server status periodically"""
        try:
            import requests
            url = f"http://{self.server_host.get()}:{self.server_port.get()}/api/health"
            response = requests.get(url, timeout=2)
            if response.status_code == 200:
                if not self.server_running:
                    self.server_running = True
                    self.server_status_label.config(text="🟢 Server Status: Running", fg="#16a34a")
                    self.start_server_btn.config(state="disabled")
                    self.stop_server_btn.config(state="normal")
            else:
                if self.server_running:
                    self.server_running = False
                    self.server_status_label.config(text="🔴 Server Status: Stopped", fg="#dc2626")
                    self.start_server_btn.config(state="normal")
                    self.stop_server_btn.config(state="disabled")
        except:
            if self.server_running:
                self.server_running = False
                self.server_status_label.config(text="🔴 Server Status: Stopped", fg="#dc2626")
                self.start_server_btn.config(state="normal")
                self.stop_server_btn.config(state="disabled")

        # Check again in 5 seconds
        self.after(5000, self.check_server_status)


if __name__ == "__main__":
    app = ClientManagerGUI()
    app.mainloop()
