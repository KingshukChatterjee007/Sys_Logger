#!/usr/bin/env python3
"""
Sys_Logger Server Installer
GUI-based installer for the Sys_Logger server component
"""

import os
import sys
import subprocess
import json
import shutil
import platform
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import threading
import time
import winreg as reg
import ctypes
from pathlib import Path
import tempfile
import datetime

# Try to import PIL for enhanced UI features
try:
    from PIL import Image, ImageTk
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


class ServerInstaller:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Sys_Logger Server Installer v2.0")
        self.root.geometry("650x550")
        self.root.resizable(True, True)

        # Professional styling
        self.style = ttk.Style()
        self.style.configure('TFrame', background='#f0f0f0')
        self.style.configure('TLabel', background='#f0f0f0', font=('Segoe UI', 9))
        self.style.configure('TButton', font=('Segoe UI', 9), padding=6)
        self.style.configure('Header.TLabel', font=('Segoe UI', 14, 'bold'), foreground='#2c3e50')
        self.style.configure('Title.TLabel', font=('Segoe UI', 16, 'bold'), foreground='#1a252f')
        self.style.configure('Accent.TButton', background='#3498db', foreground='white', font=('Segoe UI', 10, 'bold'))

        # Set window icon and branding
        self.logo_image = None
        if HAS_PIL:
            try:
                # Try to load logo - you would need to provide logo.png in the installation directory
                logo_path = os.path.join(os.path.dirname(__file__), "logo.png")
                if os.path.exists(logo_path):
                    self.logo_image = ImageTk.PhotoImage(Image.open(logo_path).resize((64, 64)))
                    self.root.iconphoto(True, self.logo_image)
                else:
                    # Fallback to default icon
                    self.root.iconbitmap(default="")
            except:
                pass

        self.root.configure(bg='#f0f0f0')

        # Generate unique installation path with timestamp
        self.default_path = f"C:\\Program Files\\Sys_Logger_Server"

        self.install_path = ""
        self.server_port = "5000"
        self.database_choice = "postgresql"  # sqlite or postgresql
        self.github_token = ""
        self.create_service = True

        # Installation state tracking
        self.installation_started = False
        self.install_btn = None
        self.start_install_btn = None

        # Prerequisite checking state
        self.prereqs_checked = False
        self.choco_available = False
        self.python_installed = False
        self.docker_installed = False

        self.setup_ui()
        self.check_admin_rights()

    def check_admin_rights(self):
        """Check if running with administrator privileges"""
        try:
            is_admin = ctypes.windll.shell32.IsUserAnAdmin()
            if not is_admin:
                messagebox.showwarning(
                    "Administrator Rights Required",
                    "This installer requires administrator privileges to create Windows services.\n\n"
                    "Please run as administrator and try again."
                )
                sys.exit(1)
        except:
            pass  # Non-Windows system

    def setup_ui(self):
        """Setup the user interface"""
        # Create notebook for tabs
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)
        self.notebook = notebook

        # Prerequisites tab
        prereq_frame = ttk.Frame(notebook, style='TFrame')
        notebook.add(prereq_frame, text='🔧 Prerequisites')
        self.create_prerequisites_tab(prereq_frame)

        # Welcome tab
        welcome_frame = ttk.Frame(notebook)
        notebook.add(welcome_frame, text='Welcome')
        self.create_welcome_tab(welcome_frame)

        # Installation tab
        install_frame = ttk.Frame(notebook)
        notebook.add(install_frame, text='Installation')
        self.create_installation_tab(install_frame)

        # Configuration tab
        config_frame = ttk.Frame(notebook)
        notebook.add(config_frame, text='Configuration')
        self.create_configuration_tab(config_frame)

        # Progress tab
        progress_frame = ttk.Frame(notebook)
        notebook.add(progress_frame, text='Progress')
        self.create_progress_tab(progress_frame)

        # Finish tab
        finish_frame = ttk.Frame(notebook)
        notebook.add(finish_frame, text='Finish')
        self.create_finish_tab(finish_frame)

        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready to install")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def create_prerequisites_tab(self, parent):
        """Create the prerequisites installation tab"""
        ttk.Label(parent, text="Prerequisites Installation",
                  style='Title.TLabel').pack(pady=20)

        # Prerequisites description
        desc_text = """
This installer will automatically check and install required software components:

• Chocolatey (Windows Package Manager)
• Python 3.8+ (Programming language)
• Docker Desktop (Container platform for PostgreSQL)

All components will be installed using Chocolatey for seamless automation.
        """

        desc_label = tk.Text(parent, wrap=tk.WORD, height=6, font=('Segoe UI', 10),
                           bg='#f0f0f0', relief='flat', bd=0)
        desc_label.insert(tk.END, desc_text.strip())
        desc_label.config(state=tk.DISABLED)
        desc_label.pack(padx=20, pady=5, fill=tk.X)

        # Prerequisites checklist frame
        check_frame = ttk.LabelFrame(parent, text="Prerequisites Status", padding=10)
        check_frame.pack(fill=tk.X, padx=20, pady=10)

        # Create checklist items
        self.prereq_vars = {}
        self.prereq_labels = {}

        prereqs = [
            ("choco", "Chocolatey Package Manager", "Optional - enables automated installations"),
            ("python", "Python 3.8+", "Programming language runtime"),
            ("docker", "Docker Desktop", "Container platform for databases")
        ]

        for i, (key, name, desc) in enumerate(prereqs):
            frame = ttk.Frame(check_frame)
            frame.pack(fill=tk.X, pady=2)

            self.prereq_vars[key] = tk.BooleanVar(value=False)
            cb = ttk.Checkbutton(frame, variable=self.prereq_vars[key], state='disabled')
            cb.pack(side=tk.LEFT)

            text_frame = ttk.Frame(frame)
            text_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10,0))

            ttk.Label(text_frame, text=name, font=('Segoe UI', 9, 'bold')).pack(anchor=tk.W)
            ttk.Label(text_frame, text=desc, font=('Segoe UI', 8), foreground='#666').pack(anchor=tk.W)

            self.prereq_labels[key] = ttk.Label(frame, text="Checking...",
                                              font=('Segoe UI', 8), foreground='#ffa500')
            self.prereq_labels[key].pack(side=tk.RIGHT)

        # Control buttons
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill=tk.X, padx=20, pady=20)

        self.check_prereqs_btn = ttk.Button(btn_frame, text="🔍 Check Prerequisites",
                                          command=self.check_all_prerequisites)
        self.check_prereqs_btn.pack(side=tk.LEFT)

        self.install_prereqs_btn = ttk.Button(btn_frame, text="📦 Install Missing Prerequisites",
                                            command=self.install_missing_prerequisites, state='disabled')
        self.install_prereqs_btn.pack(side=tk.LEFT, padx=(10,0))

        self.next_to_welcome_btn = ttk.Button(btn_frame, text="Next →", command=lambda: self.notebook.select(1))
        self.next_to_welcome_btn.pack(side=tk.RIGHT)

    def check_all_prerequisites(self):
        """Check all prerequisites and update UI"""
        self.check_prereqs_btn.config(state='disabled')
        self.install_prereqs_btn.config(state='disabled')
        self.next_to_welcome_btn.config(state='disabled')

        # Reset status
        for key in self.prereq_labels:
            self.prereq_labels[key].config(text="Checking...", foreground='#ffa500')
            self.prereq_vars[key].set(False)

        def check_thread():
            try:
                # Check Chocolatey
                self.root.after(0, lambda: self.prereq_labels['choco'].config(text="Checking...", foreground='#ffa500'))
                self.choco_available = self.check_choco_available()
                if self.choco_available:
                    self.root.after(0, lambda: self.prereq_labels['choco'].config(text="✓ Installed", foreground='#008000'))
                    self.root.after(0, lambda: self.prereq_vars['choco'].set(True))
                else:
                    self.root.after(0, lambda: self.prereq_labels['choco'].config(text="✗ Not found (Optional)", foreground='#ffa500'))
                    self.root.after(0, lambda: self.prereq_vars['choco'].set(True))  # Mark as satisfied since optional

                # Check Python
                self.root.after(0, lambda: self.prereq_labels['python'].config(text="Checking...", foreground='#ffa500'))
                self.python_installed = self.check_python_installed()
                if self.python_installed:
                    self.root.after(0, lambda: self.prereq_labels['python'].config(text="✓ Installed", foreground='#008000'))
                    self.root.after(0, lambda: self.prereq_vars['python'].set(True))
                else:
                    self.root.after(0, lambda: self.prereq_labels['python'].config(text="✗ Not found", foreground='#ff0000'))

                # Check Docker
                self.root.after(0, lambda: self.prereq_labels['docker'].config(text="Checking...", foreground='#ffa500'))
                self.docker_installed = self.check_docker_installed()
                if self.docker_installed:
                    self.root.after(0, lambda: self.prereq_labels['docker'].config(text="✓ Installed", foreground='#008000'))
                    self.root.after(0, lambda: self.prereq_vars['docker'].set(True))
                else:
                    self.root.after(0, lambda: self.prereq_labels['docker'].config(text="✗ Not found", foreground='#ff0000'))

                # Update buttons
                missing_count = sum(not self.prereq_vars[key].get() for key in self.prereq_vars)
                self.prereqs_checked = (missing_count == 0)

                if missing_count > 0:
                    self.root.after(0, lambda: self.install_prereqs_btn.config(state='normal'))
                    self.root.after(0, lambda: self.next_to_welcome_btn.config(state='disabled'))
                else:
                    self.root.after(0, lambda: self.next_to_welcome_btn.config(state='normal'))

                self.root.after(0, lambda: self.check_prereqs_btn.config(state='normal'))

            except Exception as e:
                self.log_progress(f"Error checking prerequisites: {e}")
                self.root.after(0, lambda: self.check_prereqs_btn.config(state='normal'))

        thread = threading.Thread(target=check_thread, daemon=True)
        thread.start()

    def install_missing_prerequisites(self):
        """Install missing prerequisites using Chocolatey"""
        missing = []
        if not self.choco_available:
            missing.append("choco")
        if not self.python_installed:
            missing.append("python")
        if not self.docker_installed:
            missing.append("docker")

        if not missing:
            messagebox.showinfo("All Prerequisites Installed",
                              "All prerequisites are already installed!")
            return

        # Filter out optional prerequisites
        required_missing = [item for item in missing if item not in ['choco']]

        if required_missing:
            if not messagebox.askyesno("Install Prerequisites",
                                     f"The following REQUIRED prerequisites will be installed: {', '.join(required_missing)}\n\n"
                                     "This requires administrator privileges and internet connection.\n\n"
                                     "Continue?"):
                return
        elif 'choco' in missing:
            if not messagebox.askyesno("Install Optional Prerequisite",
                                     "Chocolatey package manager is not installed.\n"
                                     "This enables automated installation of other components.\n\n"
                                     "Install Chocolatey? (You can proceed without it)"):
                # User chose not to install Chocolatey, but we can continue if other prereqs are OK
                pass
            # If they said yes, proceed with installation

        self.install_prereqs_btn.config(state='disabled')
        self.check_prereqs_btn.config(state='disabled')
        self.next_to_welcome_btn.config(state='disabled')

        def install_thread():
            try:
                # Install Chocolatey first if needed
                if not self.choco_available:
                    self.root.after(0, lambda: self.prereq_labels['choco'].config(text="Installing...", foreground='#ffa500'))
                    if self.install_choco():
                        self.choco_available = True
                        self.root.after(0, lambda: self.prereq_labels['choco'].config(text="✓ Installed", foreground='#008000'))
                        self.root.after(0, lambda: self.prereq_vars['choco'].set(True))
                    else:
                        self.root.after(0, lambda: self.prereq_labels['choco'].config(text="✗ Failed", foreground='#ff0000'))

                # Install Python if needed
                if not self.python_installed:
                    self.root.after(0, lambda: self.prereq_labels['python'].config(text="Installing...", foreground='#ffa500'))
                    if self.install_python():
                        self.python_installed = True
                        self.root.after(0, lambda: self.prereq_labels['python'].config(text="✓ Installed", foreground='#008000'))
                        self.root.after(0, lambda: self.prereq_vars['python'].set(True))
                    else:
                        self.root.after(0, lambda: self.prereq_labels['python'].config(text="✗ Failed", foreground='#ff0000'))

                # Install Docker if needed
                if not self.docker_installed:
                    self.root.after(0, lambda: self.prereq_labels['docker'].config(text="Installing...", foreground='#ffa500'))
                    if self.install_docker():
                        self.docker_installed = True
                        self.root.after(0, lambda: self.prereq_labels['docker'].config(text="✓ Installed", foreground='#008000'))
                        self.root.after(0, lambda: self.prereq_vars['docker'].set(True))
                    else:
                        self.root.after(0, lambda: self.prereq_labels['docker'].config(text="✗ Failed", foreground='#ff0000'))

                # Update state
                self.prereqs_checked = all(self.prereq_vars[key].get() for key in self.prereq_vars)
                if self.prereqs_checked:
                    self.root.after(0, lambda: self.next_to_welcome_btn.config(state='normal'))

                self.root.after(0, lambda: self.install_prereqs_btn.config(state='normal'))
                self.root.after(0, lambda: self.check_prereqs_btn.config(state='normal'))

                if self.prereqs_checked:
                    messagebox.showinfo("Prerequisites Installed",
                                      "All prerequisites have been successfully installed!")
                else:
                    messagebox.showwarning("Installation Incomplete",
                                         "Some prerequisites could not be installed. Please check the status above.")

            except Exception as e:
                messagebox.showerror("Installation Error", f"Failed to install prerequisites: {e}")
                self.root.after(0, lambda: self.install_prereqs_btn.config(state='normal'))
                self.root.after(0, lambda: self.check_prereqs_btn.config(state='normal'))

        thread = threading.Thread(target=install_thread, daemon=True)
        thread.start()

    def check_choco_available(self):
        """Check if Chocolatey is available"""
        try:
            result = subprocess.run(["choco", "--version"], capture_output=True, text=True, shell=True)
            return result.returncode == 0
        except:
            return False

    def check_python_installed(self):
        """Check if Python 3.8+ is installed"""
        try:
            result = subprocess.run(["python", "--version"], capture_output=True, text=True, shell=True)
            if result.returncode == 0:
                version_str = result.stdout.strip()
                if "Python" in version_str:
                    version = version_str.split()[1]
                    major, minor = map(int, version.split('.')[:2])
                    return major >= 3 and minor >= 8
            return False
        except:
            return False

    def check_docker_installed(self):
        """Check if Docker is installed and running"""
        try:
            result = subprocess.run(["docker", "--version"], capture_output=True, text=True, shell=True)
            return result.returncode == 0
        except:
            return False

    def install_choco(self):
        """Install Chocolatey with improved error handling"""
        try:
            self.log_progress("Installing Chocolatey package manager...\n")

            # Create temporary PowerShell script for installation
            temp_dir = tempfile.gettempdir()
            script_path = os.path.join(temp_dir, "install_choco.ps1")

            script_content = '''
Set-ExecutionPolicy Bypass -Scope Process -Force
[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
try {
    Invoke-Expression ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Chocolatey installed successfully"
        exit 0
    } else {
        Write-Host "Chocolatey installation failed"
        exit 1
    }
} catch {
    Write-Host "Error installing Chocolatey: $_"
    exit 1
}
'''

            with open(script_path, 'w') as f:
                f.write(script_content)

            # Run the installation script
            install_cmd = [
                "powershell.exe",
                "-NoProfile",
                "-ExecutionPolicy", "Bypass",
                "-File", script_path
            ]

            result = subprocess.run(install_cmd, capture_output=True, text=True, timeout=300)  # 5 minute timeout

            # Cleanup
            try:
                os.remove(script_path)
            except:
                pass

            if result.returncode == 0:
                self.log_progress("Chocolatey installation completed.\n")
                # Refresh environment and verify
                import os
                choco_path = r"C:\ProgramData\chocolatey\bin"
                if choco_path not in os.environ['PATH']:
                    os.environ['PATH'] = os.environ['PATH'] + ";" + choco_path
                return self.check_choco_available()
            else:
                self.log_progress(f"Chocolatey installation failed:\n{result.stderr}\n")
                return False

        except subprocess.TimeoutExpired:
            self.log_progress("Chocolatey installation timed out. Please try again.\n")
            return False
        except Exception as e:
            self.log_progress(f"Chocolatey installation error: {e}\n")
            return False

    def install_python(self):
        """Install Python using Chocolatey"""
        try:
            # Install Python 3.9 (latest stable)
            result = subprocess.run([
                "choco", "install", "python", "--version=3.9.13", "-y"
            ], capture_output=True, text=True, shell=True)

            if result.returncode == 0:
                # Refresh environment and verify
                return self.check_python_installed()
            return False
        except Exception as e:
            self.log_progress(f"Python installation error: {e}")
            return False

    def install_docker(self):
        """Install Docker Desktop using Chocolatey with improved error handling"""
        try:
            self.log_progress("Installing Docker Desktop via Chocolatey...\n")
            self.log_progress("Note: Docker installation may take several minutes.\n")

            # Install Docker Desktop
            result = subprocess.run([
                "choco", "install", "docker-desktop", "-y", "--no-progress"
            ], capture_output=True, text=True, shell=True, timeout=1200)  # 20 minute timeout

            if result.returncode == 0:
                self.log_progress("Docker Desktop installation completed.\n")
                # Note: Docker requires restart to complete installation
                messagebox.showinfo("Docker Installation Complete",
                                  "Docker Desktop has been installed successfully!\n\n"
                                  "Important Notes:\n"
                                  "• You may need to restart your computer for Docker to work properly\n"
                                  "• Start Docker Desktop manually after restart\n"
                                  "• The installer will verify Docker functionality")
                return self.check_docker_installed()
            else:
                self.log_progress(f"Docker installation failed:\n{result.stderr}\n")
                return False

        except subprocess.TimeoutExpired:
            self.log_progress("Docker installation timed out. Installation may still be running in background.\n")
            messagebox.showwarning("Docker Installation",
                                 "Docker installation timed out but may still be running.\n"
                                 "Please wait a few minutes, then restart your computer and try again.")
            return False
        except Exception as e:
            self.log_progress(f"Docker installation error: {e}\n")
            return False

    def create_welcome_tab(self, parent):
        """Create the welcome tab"""
        # Add logo if available
        if self.logo_image and HAS_PIL:
            logo_label = ttk.Label(parent, image=self.logo_image, background='#f0f0f0')
            logo_label.pack(pady=(20,10))

        ttk.Label(parent, text="Sys_Logger Server Installation",
                  style='Title.TLabel').pack(pady=10)

        welcome_text = """
Welcome to the Sys_Logger Server Installer!

This professional installer will:
• Install Python, Docker, and all required dependencies
• Set up PostgreSQL database with Docker (auto-configured)
• Configure the Sys_Logger server with your settings
• Create Windows services for automatic startup
• Set up web dashboard with optional domain/SSL support
• Configure firewall and network settings
• Create desktop shortcuts and uninstaller

The installer requires administrator privileges and internet connection.
Please ensure you have at least 2GB free disk space.
        """

        text_widget = tk.Text(parent, wrap=tk.WORD, height=15, font=('Arial', 10))
        text_widget.insert(tk.END, welcome_text.strip())
        text_widget.config(state=tk.DISABLED)
        text_widget.pack(padx=20, pady=10, fill=tk.BOTH, expand=True)

        ttk.Button(parent, text="Next →", command=lambda: self.notebook.select(1)).pack(pady=20)

    def create_installation_tab(self, parent):
        """Create the installation options tab"""
        ttk.Label(parent, text="Installation Options",
                 font=('Arial', 14, 'bold')).pack(pady=10)

        # Installation path
        path_frame = ttk.LabelFrame(parent, text="Installation Path", padding=10)
        path_frame.pack(fill=tk.X, padx=20, pady=5)

        self.path_var = tk.StringVar(value=self.default_path)
        ttk.Entry(path_frame, textvariable=self.path_var).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(path_frame, text="Browse...", command=self.browse_install_path).pack(side=tk.RIGHT, padx=(5,0))

        # Database choice
        db_frame = ttk.LabelFrame(parent, text="Database Configuration", padding=10)
        db_frame.pack(fill=tk.X, padx=20, pady=5)

        ttk.Label(db_frame, text="Database Type:").pack(anchor=tk.W)
        self.db_var = tk.StringVar(value="postgresql")
        ttk.Radiobutton(db_frame, text="SQLite (Simple - No additional setup)",
                       variable=self.db_var, value="sqlite").pack(anchor=tk.W, padx=20)
        ttk.Radiobutton(db_frame, text="PostgreSQL with Docker (Recommended - Auto-setup)",
                       variable=self.db_var, value="postgresql").pack(anchor=tk.W, padx=20)

        # PostgreSQL settings
        postgres_frame = ttk.Frame(db_frame)
        postgres_frame.pack(fill=tk.X, padx=20, pady=5)

        ttk.Label(postgres_frame, text="PostgreSQL Port:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.pg_port_var = tk.StringVar(value="5432")
        ttk.Entry(postgres_frame, textvariable=self.pg_port_var, width=10).grid(row=0, column=1, padx=(10,0))

        ttk.Label(postgres_frame, text="Database Name:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.pg_db_var = tk.StringVar(value="syslogger")
        ttk.Entry(postgres_frame, textvariable=self.pg_db_var, width=15).grid(row=1, column=1, padx=(10,0))

        ttk.Label(postgres_frame, text="Username:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.pg_user_var = tk.StringVar(value="syslogger")
        ttk.Entry(postgres_frame, textvariable=self.pg_user_var, width=15).grid(row=2, column=1, padx=(10,0))

        ttk.Label(postgres_frame, text="Password:").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.pg_pass_var = tk.StringVar(value="syslogger123")
        ttk.Entry(postgres_frame, textvariable=self.pg_pass_var, width=15, show="*").grid(row=3, column=1, padx=(10,0))

        # Service options
        service_frame = ttk.LabelFrame(parent, text="Service Options", padding=10)
        service_frame.pack(fill=tk.X, padx=20, pady=5)

        self.service_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(service_frame, text="Install as Windows service (auto-startup)",
                       variable=self.service_var).pack(anchor=tk.W)

        # Note about client management
        client_frame = ttk.LabelFrame(parent, text="Client Management", padding=10)
        client_frame.pack(fill=tk.X, padx=20, pady=5)

        ttk.Label(client_frame, text="Note: Client executables are now created through the Server Management Application", font=('Segoe UI', 9), foreground='#666').pack(anchor=tk.W, pady=(0,5))
        ttk.Label(client_frame, text="After installation, use the 'Sys_Logger Server Manager' shortcut to add clients.", font=('Segoe UI', 9), foreground='#666').pack(anchor=tk.W)

        # Navigation buttons
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill=tk.X, padx=20, pady=20)

        ttk.Button(btn_frame, text="← Back", command=lambda: self.notebook.select(1)).pack(side=tk.LEFT)
        ttk.Button(btn_frame, text="Next →", command=lambda: self.notebook.select(3)).pack(side=tk.RIGHT)

    def create_configuration_tab(self, parent):
        """Create the configuration tab"""
        ttk.Label(parent, text="Server Configuration",
                 font=('Arial', 14, 'bold')).pack(pady=10)

        # Server port
        port_frame = ttk.LabelFrame(parent, text="Server Settings", padding=10)
        port_frame.pack(fill=tk.X, padx=20, pady=5)

        ttk.Label(port_frame, text="Server Port:").pack(anchor=tk.W)
        self.port_var = tk.StringVar(value="5000")
        ttk.Entry(port_frame, textvariable=self.port_var).pack(fill=tk.X, pady=(0,10))

        # Domain/Network configuration
        network_frame = ttk.LabelFrame(parent, text="Network Configuration", padding=10)
        network_frame.pack(fill=tk.X, padx=20, pady=5)

        ttk.Label(network_frame, text="Do you have a domain name for external access?").pack(anchor=tk.W, pady=(0,10))

        self.domain_var = tk.StringVar(value="no")
        ttk.Radiobutton(network_frame, text="No - Local access only (recommended for most users)",
                       variable=self.domain_var, value="no").pack(anchor=tk.W, padx=20)
        ttk.Radiobutton(network_frame, text="Yes - Configure for external domain access",
                       variable=self.domain_var, value="yes").pack(anchor=tk.W, padx=20)

        # Domain settings frame
        self.domain_config_frame = ttk.Frame(network_frame)
        self.domain_config_frame.pack(fill=tk.X, padx=40, pady=5)

        ttk.Label(self.domain_config_frame, text="Domain Name:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.domain_name_var = tk.StringVar()
        ttk.Entry(self.domain_config_frame, textvariable=self.domain_name_var).grid(row=0, column=1, padx=(10,0), sticky=tk.EW)

        ttk.Label(self.domain_config_frame, text="SSL Certificate:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.ssl_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(self.domain_config_frame, text="Enable HTTPS (requires SSL certificate)",
                        variable=self.ssl_var).grid(row=1, column=1, sticky=tk.W, padx=(10,0))

        # Hide domain config initially
        self.domain_config_frame.grid_remove()

        # Show/hide domain config based on selection
        def on_domain_change(*args):
            if self.domain_var.get() == "yes":
                self.domain_config_frame.grid()
            else:
                self.domain_config_frame.grid_remove()

        self.domain_var.trace_add("write", on_domain_change)

        # Optional settings
        optional_frame = ttk.LabelFrame(parent, text="Optional Settings", padding=10)
        optional_frame.pack(fill=tk.X, padx=20, pady=5)

        ttk.Label(optional_frame, text="GitHub Token (for log uploads):").pack(anchor=tk.W)
        self.token_var = tk.StringVar()
        ttk.Entry(optional_frame, textvariable=self.token_var, show="*").pack(fill=tk.X, pady=(0,5))

        ttk.Label(optional_frame, text="Leave empty to disable GitHub log uploads", font=('Arial', 8)).pack(anchor=tk.W)

        # Navigation buttons
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill=tk.X, padx=20, pady=20)

        ttk.Button(btn_frame, text="← Back", command=lambda: self.notebook.select(1)).pack(side=tk.LEFT)
        self.install_btn = ttk.Button(btn_frame, text="Install", command=self.start_installation)
        self.install_btn.pack(side=tk.RIGHT)

    def create_progress_tab(self, parent):
        """Create the progress tab"""
        ttk.Label(parent, text="Installation Progress",
                 font=('Arial', 14, 'bold')).pack(pady=10)

        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(parent, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill=tk.X, padx=20, pady=10)

        # Progress text
        self.progress_text = scrolledtext.ScrolledText(parent, height=15, wrap=tk.WORD)
        self.progress_text.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # Control buttons
        self.control_frame = ttk.Frame(parent)
        self.control_frame.pack(fill=tk.X, padx=20, pady=10)

        self.start_install_btn = ttk.Button(self.control_frame, text="Start Installation", command=self.start_installation)
        self.start_install_btn.pack(side=tk.RIGHT)

    def create_finish_tab(self, parent):
        """Create the finish tab"""
        ttk.Label(parent, text="Installation Complete!",
                 font=('Arial', 16, 'bold')).pack(pady=20)

        self.finish_text = tk.Text(parent, wrap=tk.WORD, height=10, font=('Arial', 10))
        self.finish_text.pack(padx=20, pady=10, fill=tk.BOTH, expand=True)
        self.finish_text.config(state=tk.DISABLED)

        ttk.Button(parent, text="Finish", command=self.finish_installation).pack(pady=20)

    def browse_install_path(self):
        """Browse for installation path"""
        path = filedialog.askdirectory(title="Select Installation Directory")
        if path:
            self.path_var.set(path)

    def start_installation(self):
        """Start the installation process"""
        # Prevent multiple installations
        if self.installation_started:
            messagebox.showwarning("Installation Already Started", "Installation is already in progress. Please wait for it to complete.")
            return

        # Get configuration values
        self.install_path = self.path_var.get()
        self.server_port = self.port_var.get()
        self.database_choice = self.db_var.get()
        self.github_token = self.token_var.get()
        self.create_service = self.service_var.get()
        # Client creation removed from installer - handled by management app

        # Mark installation as started and disable buttons
        self.installation_started = True
        if self.install_btn:
            self.install_btn.config(state='disabled')
        if self.start_install_btn:
            self.start_install_btn.config(state='disabled')

        # Switch to progress tab
        self.notebook.select(4)

        # Start installation in separate thread
        install_thread = threading.Thread(target=self.run_installation)
        install_thread.daemon = True
        install_thread.start()

    def run_installation(self):
        """Run the installation process"""
        try:
            self.log_progress("Starting Sys_Logger Server installation...\n")

            # Step 1: Check prerequisites (system and external software)
            self.progress_var.set(5)
            self.check_prerequisites()

            # Step 1.5: Verify external prerequisites are installed
            if not self.prereqs_checked:
                self.log_progress("Prerequisites not verified. Please complete the Prerequisites tab first.\n")
                messagebox.showerror("Prerequisites Required",
                                   "Please check and install prerequisites in the Prerequisites tab before proceeding.")
                return

            # Check if required software is available
            missing_prereqs = []
            if not self.python_installed:
                missing_prereqs.append("Python")
            if not self.docker_installed:
                missing_prereqs.append("Docker")

            if missing_prereqs:
                self.log_progress(f"Missing prerequisites: {', '.join(missing_prereqs)}\n")
                messagebox.showerror("Missing Prerequisites",
                                   f"The following prerequisites are not installed: {', '.join(missing_prereqs)}\n\n"
                                   "Please install them in the Prerequisites tab before proceeding.")
                return

            # Step 2: Create installation directory
            self.progress_var.set(10)
            self.create_install_directory()

            # Step 3: Install Python dependencies
            self.progress_var.set(20)
            self.install_python_dependencies()

            # Step 4: Copy application files
            self.progress_var.set(40)
            self.copy_application_files()

            # Step 5: Setup database
            self.progress_var.set(60)
            self.setup_database()

            # Step 6: Create configuration
            self.progress_var.set(75)
            self.create_configuration()

            # Step 7: Install Windows service
            if self.create_service:
                self.progress_var.set(85)
                self.install_windows_service()
                self.start_windows_service()

            # Step 9: Create uninstaller
            self.progress_var.set(90)
            self.create_uninstaller()

            # Step 10: Create executable files
            self.progress_var.set(97)
            self.create_executables()

            # Complete
            self.progress_var.set(100)
            self.log_progress("Installation completed successfully!\n")
            self.show_completion_message()

        except Exception as e:
            error_msg = f"Installation failed: {str(e)}\n"
            self.log_progress(error_msg)
            messagebox.showerror("Installation Failed", error_msg)
            # Re-enable buttons on failure to allow retry
            self.installation_started = False
            if self.install_btn:
                self.install_btn.config(state='normal')
            if self.start_install_btn:
                self.start_install_btn.config(state='normal')

    def check_prerequisites(self):
        """Check system prerequisites"""
        self.log_progress("Checking prerequisites...\n")

        # Check Python version
        python_version = platform.python_version()
        self.log_progress(f"Python version: {python_version}\n")

        if tuple(map(int, python_version.split('.'))) < (3, 8):
            raise Exception("Python 3.8 or higher is required")

        # Check if running on Windows
        if platform.system() != "Windows":
            raise Exception("This installer is designed for Windows systems")

        self.log_progress("Prerequisites check passed.\n")

    def create_install_directory(self):
        """Create the installation directory"""
        self.log_progress(f"Creating installation directory: {self.install_path}\n")

        try:
            os.makedirs(self.install_path, exist_ok=True)
            self.log_progress("Installation directory created.\n")
        except Exception as e:
            raise Exception(f"Failed to create installation directory: {e}")

    def install_python_dependencies(self):
        """Install Python dependencies"""
        self.log_progress("Installing Python dependencies...\n")

        requirements = [
            "flask",
            "flask-cors",
            "flask-socketio",
            "psutil",
            "python-dotenv",
            "requests",
            "pillow",
            "GPUtil"
        ]

        if self.database_choice == "postgresql":
            requirements.extend(["psycopg2-binary", "sqlalchemy"])

        # Create requirements.txt
        req_file = os.path.join(self.install_path, "requirements.txt")
        with open(req_file, 'w') as f:
            f.write('\n'.join(requirements))

        # Install using pip - use correct python executable
        try:
            python_exe = self.find_python_executable()
            result = subprocess.run([
                python_exe, "-m", "pip", "install", "-r", req_file
            ], capture_output=True, text=True, cwd=self.install_path)

            if result.returncode != 0:
                self.log_progress(f"Warning: Some dependencies may not have installed correctly.\n")
                self.log_progress(f"Error: {result.stderr}\n")

            self.log_progress("Python dependencies installation completed.\n")

        except Exception as e:
            raise Exception(f"Failed to install Python dependencies: {e}")

    def copy_application_files(self):
        """Copy application files to installation directory"""
        self.log_progress("Copying application files...\n")

        # Get the source directory (where the installer executable is located)
        if getattr(sys, 'frozen', False):
            # Running as compiled executable - files are bundled in _MEIPASS
            source_dir = sys._MEIPASS
        else:
            # Running as script - find the project root (parent of installation directory)
            current_script_dir = os.path.dirname(os.path.abspath(__file__))
            source_dir = os.path.dirname(current_script_dir)  # Go up one level from installation/

        # Files to copy from the bundled executable (exclude installer executable)
        files_to_copy = [
            ("backend", "backend/"),
            ("frontend", "frontend/"),
            ("database_schema.md", "database_schema.md"),
            ("README.md", "README.md"),
            ("unit_client.py", "unit_client.py"),
            ("unit_client.service", "unit_client.service"),
            ("create_service.ps1", "create_service.ps1"),
            ("setup.py", "setup.py"),
            ("server_setup.py", "server_setup.py"),
            ("multi_unit_simulation.py", "multi_unit_simulation.py"),
            ("TESTING_GUIDE.md", "TESTING_GUIDE.md"),
            ("server_manager.py", "server_manager.py"),
            ("uninstall.py", "uninstall.py")
        ]

        # Get the installer executable name to exclude it from copying
        installer_exe_name = "SysLogger_Server_Installer.exe"
        if getattr(sys, 'frozen', False):
            # When running as frozen executable, get the exe name
            installer_exe_name = os.path.basename(sys.executable)

        for src_name, dst_name in files_to_copy:
            src = os.path.join(source_dir, src_name)
            dst = os.path.join(self.install_path, dst_name)

            try:
                # Create destination directory if it doesn't exist
                dst_dir = os.path.dirname(dst)
                os.makedirs(dst_dir, exist_ok=True)

                if os.path.exists(src):
                    if os.path.isdir(src):
                        # For directories, use copytree with dirs_exist_ok=True for Python 3.8+
                        if hasattr(shutil, 'copytree') and 'dirs_exist_ok' in shutil.copytree.__code__.co_varnames:
                            shutil.copytree(src, dst, dirs_exist_ok=True)
                        else:
                            # Fallback for older Python versions
                            if os.path.exists(dst):
                                shutil.rmtree(dst)
                            shutil.copytree(src, dst)
                    else:
                        shutil.copy2(src, dst)
                    self.log_progress(f"Copied: {src_name}\n")
                else:
                    # File doesn't exist - this is expected when some files aren't bundled
                    # But we should only warn for development/script mode, not for frozen executables
                    if not getattr(sys, 'frozen', False):
                        if src_name not in ["docker-compose.yml"]:  # Skip warning for optional files
                            self.log_progress(f"Warning: Source file not found: {src_name} (src: {src})\n")

            except Exception as e:
                self.log_progress(f"Warning: Failed to copy {src_name}: {e}\n")

        self.log_progress("Application files copied.\n")

    def setup_database(self):
        """Setup the database"""
        self.log_progress("Setting up database...\n")

        if self.database_choice == "sqlite":
            # SQLite setup is minimal - just ensure the directory exists
            db_dir = os.path.join(self.install_path, "data")
            os.makedirs(db_dir, exist_ok=True)
            self.log_progress("SQLite database setup completed.\n")
        else:
            # PostgreSQL setup using Docker Compose
            try:
                self.setup_postgresql_with_docker()
            except AttributeError:
                self.log_progress("Warning: PostgreSQL setup method not found. Using fallback setup.\n")
                # Fallback: just create the directory and log the issue
                db_dir = os.path.join(self.install_path, "data")
                os.makedirs(db_dir, exist_ok=True)
                self.log_progress("Database directory created. Please configure PostgreSQL manually.\n")

    def create_configuration(self):
        """Create configuration files"""
        self.log_progress("Creating configuration files...\n")

        # Create .env file
        env_content = f"""# Sys_Logger Server Configuration
FLASK_DEBUG=false
PORT={self.server_port}
HOST=0.0.0.0
LOG_FOLDER=C:\\\\Usage_Logs
LOG_RETENTION_DAYS=2
LOG_INTERVAL=1
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
"""

        if self.github_token:
            env_content += f"GITHUB_TOKEN={self.github_token}\n"

        env_file = os.path.join(self.install_path, ".env")
        with open(env_file, 'w') as f:
            f.write(env_content)

        # Create config.json for the service
        config = {
            "install_path": self.install_path,
            "server_port": self.server_port,
            "database_type": self.database_choice,
            "service_name": "SysLoggerServer",
            "display_name": "Sys_Logger Server",
            "description": "Real-time system monitoring server"
        }

        config_file = os.path.join(self.install_path, "server_config.json")
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=4)

        self.log_progress("Configuration files created.\n")

    def install_windows_service(self):
        """Install Windows service"""
        self.log_progress("Installing Windows service...\n")

        try:
            # Determine the correct Python executable to use
            # When frozen (compiled), sys.executable is the exe itself, not python.exe
            if getattr(sys, 'frozen', False):
                # For frozen executable, we need to find python.exe
                # PyInstaller typically bundles python.exe or we need to find system python
                python_exe = self.find_python_executable()
            else:
                python_exe = sys.executable

            # Create service batch file
            service_script = f'''@echo off
cd /d "{self.install_path}"
"{python_exe}" sys_logger.py --service
'''

            service_file = os.path.join(self.install_path, "run_service.bat")
            with open(service_file, 'w') as f:
                f.write(service_script)

            # Use NSSM (Non-Sucking Service Manager) or Windows sc command
            # For now, we'll create the service configuration
            service_config = {
                "name": "SysLoggerServer",
                "display_name": "Sys_Logger Server",
                "description": "Real-time system monitoring server",
                "executable": sys.executable,
                "script": os.path.join(self.install_path, "sys_logger.py"),
                "arguments": ["--service"],
                "working_directory": self.install_path
            }

            service_config_file = os.path.join(self.install_path, "service_config.json")
            with open(service_config_file, 'w') as f:
                json.dump(service_config, f, indent=4)

            # Try to create service using sc command
            try:
                service_cmd = [
                    "sc", "create", "SysLoggerServer",
                    f"binPath= \"{python_exe}\" \"{os.path.join(self.install_path, 'sys_logger.py')}\" --service",
                    "start=", "auto",
                    "displayName=", "Sys_Logger Server",
                    "depend=", "Tcpip",
                    "obj=", "LocalSystem"
                ]

                result = subprocess.run(service_cmd, capture_output=True, text=True)
                if result.returncode == 0:
                    self.log_progress("Windows service created successfully.\n")
                else:
                    self.log_progress(f"Warning: Failed to create service: {result.stderr}\n")

            except Exception as e:
                self.log_progress(f"Warning: Service creation failed: {e}\n")

        except Exception as e:
            raise Exception(f"Failed to install Windows service: {e}")

    def find_python_executable(self):
        """Find the correct python executable, especially when frozen"""
        if getattr(sys, 'frozen', False):
            # When frozen, sys.executable is the .exe, we need python.exe
            exe_dir = os.path.dirname(sys.executable)
            python_exe = os.path.join(exe_dir, 'python.exe')
            if os.path.exists(python_exe):
                return python_exe

            # Fallback: try to find python in PATH
            try:
                result = subprocess.run(['where', 'python'], capture_output=True, text=True, shell=True)
                if result.returncode == 0:
                    return result.stdout.strip().split('\n')[0]
            except:
                pass

            # Last resort: assume python.exe is in PATH
            return 'python.exe'
        else:
            return sys.executable

    def start_windows_service(self):
        """Start the Windows service after installation"""
        self.log_progress("Starting Windows service...\n")

        try:
            # Start the service
            start_cmd = ["sc", "start", "SysLoggerServer"]
            result = subprocess.run(start_cmd, capture_output=True, text=True)

            if result.returncode == 0:
                self.log_progress("Windows service started successfully.\n")
            else:
                self.log_progress(f"Warning: Failed to start service: {result.stderr}\n")

        except Exception as e:
            self.log_progress(f"Warning: Could not start service: {e}\n")


    def generate_client_installer_script(self, client_name, server_url):
        """Generate customized client installer script"""
        script = f'''#!/usr/bin/env python3
"""
Sys_Logger Client Installer for {client_name}
Auto-generated client installer with pre-configured settings
"""

import os
import sys
import platform
import subprocess
import shutil
from pathlib import Path
import json
import uuid

def run_command(command, shell=False):
    """Run a command and return success status"""
    try:
        result = subprocess.run(command, shell=shell, check=True, capture_output=True, text=True)
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        return False, e.stderr

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 6):
        print("Error: Python 3.6 or higher is required")
        return False
    return True

def check_dependencies():
    """Check and install required Python packages"""
    required_packages = ['psutil', 'requests']

    print("Checking Python dependencies...")
    for package in required_packages:
        try:
            __import__(package)
            print(f"✓ {{package}} is available")
        except ImportError:
            print(f"Installing {{package}}...")
            success, output = run_command([sys.executable, '-m', 'pip', 'install', package])
            if not success:
                print(f"Failed to install {{package}}: {{output}}")
                return False
            print(f"✓ {{package}} installed")

    # Optional GPU package
    try:
        import GPUtil
        print("✓ GPUtil is available (NVIDIA GPU support)")
    except ImportError:
        print("GPUtil not available - NVIDIA GPU monitoring will be limited")

    return True

def get_install_path():
    """Get installation path based on OS"""
    system = platform.system().lower()
    if system == 'windows':
        return Path(os.environ.get('PROGRAMFILES', 'C:\\\\Program Files')) / 'UnitClient'
    else:
        return Path('/opt/unit_client')

def create_directories(install_path):
    """Create necessary directories"""
    dirs = [
        install_path,
        install_path / 'logs',
        install_path / 'config'
    ]

    for dir_path in dirs:
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {{dir_path}}")

def copy_files(install_path):
    """Copy client files to install path"""
    # Get the directory where this script is located
    current_dir = Path(__file__).parent

    # Look for unit_client.py in parent directories
    unit_client_path = None
    for parent in [current_dir] + list(current_dir.parents):
        candidate = parent / 'unit_client.py'
        if candidate.exists():
            unit_client_path = candidate
            break

    if unit_client_path:
        shutil.copy2(unit_client_path, install_path / 'unit_client.py')
        print(f"Copied unit_client.py to {{install_path}}")

        # Also copy unit_client.service if it exists (for Linux)
        service_file = unit_client_path.parent / 'unit_client.service'
        if service_file.exists():
            shutil.copy2(service_file, install_path / 'unit_client.service')
            print(f"Copied unit_client.service to {{install_path}}")
    else:
        print("Warning: unit_client.py not found")

def setup_linux_service(install_path):
    """Setup systemd service on Linux"""
    if platform.system().lower() != 'linux':
        return

    print("Setting up systemd service...")

    # Create unitclient user if it doesn't exist
    success, output = run_command(['id', 'unitclient'])
    if not success:
        print("Creating unitclient user...")
        success, output = run_command(['sudo', 'useradd', '--system', '--shell', '/bin/false', 'unitclient'])
        if not success:
            print(f"Warning: Failed to create unitclient user: {{output}}")

    # Set permissions
    success, output = run_command(['sudo', 'chown', '-R', 'unitclient:unitclient', str(install_path)])
    if not success:
        print(f"Warning: Failed to set permissions: {{output}}")

    # Copy service file
    service_file = install_path / 'unit_client.service'
    if service_file.exists():
        success, output = run_command(['sudo', 'cp', str(service_file), '/etc/systemd/system/'])
        if not success:
            print(f"Failed to copy service file: {{output}}")
            return False

        # Reload systemd and enable service
        run_command(['sudo', 'systemctl', 'daemon-reload'])
        run_command(['sudo', 'systemctl', 'enable', 'unit_client.service'])
        run_command(['sudo', 'systemctl', 'start', 'unit_client.service'])

        print("✓ Systemd service installed and started")
        print("To check status: sudo systemctl status unit_client")
        print("To view logs: sudo journalctl -u unit_client -f")
    else:
        print("Warning: unit_client.service file not found")

    return True

def setup_windows_service(install_path):
    """Setup Windows service"""
    if platform.system().lower() != 'windows':
        return

    print("Setting up Windows service...")

    # Look for create_service.ps1 in parent directories
    current_dir = Path(__file__).parent
    script_path = None
    for parent in [current_dir] + list(current_dir.parents):
        candidate = parent / 'create_service.ps1'
        if candidate.exists():
            script_path = candidate
            break

    if script_path:
        print("Running PowerShell service creation script...")
        # Run PowerShell script as administrator
        command = [
            'powershell.exe',
            '-ExecutionPolicy', 'Bypass',
            '-File', str(script_path)
        ]

        try:
            result = subprocess.run(command, check=True)
            print("✓ Windows service setup completed")
        except subprocess.CalledProcessError as e:
            print(f"Failed to setup Windows service: {{e}}")
            return False
    else:
        print("Warning: create_service.ps1 not found")

    return True

def create_config_file(install_path):
    """Create config file with pre-configured settings"""
    import uuid
    import json

    config_file = install_path / 'unit_client_config.json'
    if not config_file.exists():
        # Generate system ID
        system_id = str(uuid.uuid4())

        # Use pre-configured server URL and system name
        server_url = "{server_url}"
        system_name = "{client_name}"

        default_config = {{
            'system_id': system_id,
            'server_url': server_url,
            'system_name': system_name
        }}

        with open(config_file, 'w') as f:
            json.dump(default_config, f, indent=4)

        print(f"✓ Created config file: {{config_file}}")
        print(f"  System ID: {{system_id}}")
        print(f"  System Name: {{system_name}}")
        print(f"  Server URL: {{server_url}}")
    else:
        print(f"Config file already exists: {{config_file}}")

def main():
    print("Sys_Logger Unit Client Setup for {client_name}")
    print("=" * 50)

    # Check Python version
    if not check_python_version():
        sys.exit(1)

    # Check and install dependencies
    if not check_dependencies():
        sys.exit(1)

    # Determine install path
    install_path = get_install_path()
    print(f"Install path: {{install_path}}")

    # Create directories
    create_directories(install_path)

    # Copy files
    copy_files(install_path)

    # Create config with pre-configured settings
    create_config_file(install_path)

    # Setup service based on OS
    system = platform.system().lower()
    if system == 'linux':
        setup_linux_service(install_path)
    elif system == 'windows':
        setup_windows_service(install_path)
    else:
        print(f"Unsupported OS: {{system}}")
        print("Manual service setup required")

    print("\\nSetup completed for {client_name}!")
    print(f"Installation directory: {{install_path}}")
    print("\\nTo run manually:")
    print(f"  cd {{install_path}}")
    print("  python unit_client.py --foreground  # For testing")
    print("  python unit_client.py --start        # As background service")

    if system == 'linux':
        print("\\nService management:")
        print("  sudo systemctl start unit_client")
        print("  sudo systemctl stop unit_client")
        print("  sudo systemctl status unit_client")
        print("  sudo journalctl -u unit_client -f")

    input("\\nPress Enter to exit...")

if __name__ == "__main__":
    main()
'''
        return script

    def create_uninstaller(self):
        """Create uninstaller script"""
        self.log_progress("Creating uninstaller...\n")

        uninstaller_script = f'''#!/usr/bin/env python3
"""
Sys_Logger Server Uninstaller
"""

import os
import sys
import subprocess
import json
import shutil
import tkinter as tk
from tkinter import messagebox

def uninstall():
    """Uninstall Sys_Logger Server"""
    try:
        # Load configuration
        config_file = r"{os.path.join(self.install_path, 'server_config.json')}"
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                config = json.load(f)

            # Stop and remove service
            try:
                subprocess.run(["sc", "stop", "SysLoggerServer"], capture_output=True)
                subprocess.run(["sc", "delete", "SysLoggerServer"], capture_output=True)
                print("Service stopped and removed.")
            except:
                pass

            # Remove installation directory
            install_path = config["install_path"]
            if os.path.exists(install_path):
                try:
                    shutil.rmtree(install_path)
                    print(f"Installation directory removed: {{install_path}}")
                except:
                    print("Warning: Could not remove installation directory completely.")

        # Remove from registry
        try:
            import winreg as reg
            key_path = r"SOFTWARE\\SysLogger"
            reg.DeleteKey(reg.HKEY_LOCAL_MACHINE, key_path)
        except:
            pass

        messagebox.showinfo("Success", "Sys_Logger Server has been uninstalled successfully!")
        sys.exit(0)

    except Exception as e:
        messagebox.showerror("Error", f"Uninstallation failed: {{e}}")

if __name__ == "__main__":
    if messagebox.askyesno("Confirm Uninstall", "Are you sure you want to uninstall Sys_Logger Server?"):
        uninstall()
'''

        uninstaller_file = os.path.join(self.install_path, "uninstall.py")
        with open(uninstaller_file, 'w') as f:
            f.write(uninstaller_script)

        # Create desktop shortcut for uninstaller
        self.create_desktop_shortcut("Uninstall Sys_Logger Server", uninstaller_file)

        self.log_progress("Uninstaller created.\n")

    def create_executables(self):
        """Create batch files for server manager and uninstaller"""
        self.log_progress("Creating application launchers...\n")

        try:
            # Create server manager batch file using pythonw for GUI apps
            manager_script = os.path.join(self.install_path, "server_manager.py")
            manager_bat = os.path.join(self.install_path, "SysLogger_Server_Manager.bat")

            if os.path.exists(manager_script):
                pythonw_exe = sys.executable.replace('python.exe', 'pythonw.exe')
                if not os.path.exists(pythonw_exe):
                    pythonw_exe = sys.executable  # fallback to regular python

                with open(manager_bat, 'w') as f:
                    f.write(f'@echo off\ncd /d "{self.install_path}"\nstart "" "{pythonw_exe}" server_manager.py\n')
                self.log_progress("Server manager launcher created.\n")

                # Create desktop shortcut
                self.create_desktop_shortcut_simple("Sys_Logger Server Manager", manager_bat)
            else:
                self.log_progress("Warning: Server manager script not found.\n")

            # Create uninstaller batch file using pythonw for GUI apps
            uninstaller_script = os.path.join(self.install_path, "uninstall.py")
            uninstaller_bat = os.path.join(self.install_path, "SysLogger_Server_Uninstaller.bat")

            if os.path.exists(uninstaller_script):
                pythonw_exe = sys.executable.replace('python.exe', 'pythonw.exe')
                if not os.path.exists(pythonw_exe):
                    pythonw_exe = sys.executable  # fallback to regular python

                with open(uninstaller_bat, 'w') as f:
                    f.write(f'@echo off\ncd /d "{self.install_path}"\nstart "" "{pythonw_exe}" uninstall.py\n')
                self.log_progress("Uninstaller launcher created.\n")

                # Create desktop shortcut
                self.create_desktop_shortcut_simple("Uninstall Sys_Logger Server", uninstaller_bat)
            else:
                self.log_progress("Warning: Uninstaller script not found.\n")

        except Exception as e:
            self.log_progress(f"Warning: Could not create launchers: {e}\n")

    def create_desktop_shortcut(self, name, target_path):
        """Create desktop shortcut"""
        try:
            from win32com.client import Dispatch

            desktop = os.path.join(os.path.expanduser("~"), "Desktop")
            shortcut_path = os.path.join(desktop, f"{name}.lnk")

            shell = Dispatch('WScript.Shell')
            shortcut = shell.CreateShortCut(shortcut_path)
            shortcut.Targetpath = target_path
            shortcut.WorkingDirectory = os.path.dirname(target_path)
            shortcut.save()

        except ImportError:
            # pywin32 not available, skip shortcut creation
            pass
        except Exception as e:
            self.log_progress(f"Warning: Could not create desktop shortcut: {e}\n")

    def create_desktop_shortcut_simple(self, name, target_path):
        """Create desktop shortcut (alias for create_desktop_shortcut)"""
        self.create_desktop_shortcut(name, target_path)

    def show_completion_message(self):
        """Show completion message and setup instructions"""
        completion_text = f"""
Sys_Logger Server has been successfully installed!

Installation Details:
• Location: {self.install_path}
• Server Port: {self.server_port}
• Database: {self.database_choice}
• Service: {'Installed' if self.create_service else 'Not installed'}

Next Steps:
1. Start the server service from Windows Services
2. Access the web dashboard at: http://localhost:{self.server_port}
3. Use the client installer to add monitoring units

To uninstall, run the uninstaller from the desktop shortcut.
        """

        self.finish_text.config(state=tk.NORMAL)
        self.finish_text.delete(1.0, tk.END)
        self.finish_text.insert(tk.END, completion_text.strip())
        self.finish_text.config(state=tk.DISABLED)

        # Switch to finish tab
        self.notebook.select(4)

    def finish_installation(self):
        """Finish the installation"""
        self.root.quit()

    def log_progress(self, message):
        """Log progress message"""
        self.progress_text.insert(tk.END, message)
        self.progress_text.see(tk.END)
        self.status_var.set(message.strip())
        self.root.update_idletasks()

    def run(self):
        """Run the installer"""
        self.root.mainloop()


if __name__ == "__main__":
    installer = ServerInstaller()
    installer.run()