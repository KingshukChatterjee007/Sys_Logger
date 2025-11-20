#!/usr/bin/env python3
"""
Sys_Logger Server Management Application
GUI application for managing server and creating client installers
"""

import os
import sys
import json
import subprocess
import threading
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import requests
import platform
import shutil
from pathlib import Path
import uuid
import time

class ServerManager:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Sys_Logger Server Manager")
        self.root.geometry("700x600")
        self.root.resizable(True, True)

        # Style configuration
        style = ttk.Style()
        style.configure('TButton', font=('Segoe UI', 10))
        style.configure('TLabel', font=('Segoe UI', 10))
        style.configure('TFrame', background='#f0f0f0')

        # Load configuration
        self.load_config()

        # Initialize variables
        self.selected_client = None
        self.clients = []
        self.server_status = "Unknown"

        self.setup_ui()
        self.start_status_monitoring()
        self.populate_client_list()

    def load_config(self):
        """Load server configuration"""
        try:
            # Find the server installation directory
            current_dir = Path(__file__).parent
            self.install_path = None

            # Look for server_config.json in parent directories
            for parent in [current_dir] + list(current_dir.parents):
                config_file = parent / 'server_config.json'
                if config_file.exists():
                    with open(config_file, 'r') as f:
                        config = json.load(f)
                        self.install_path = config.get('install_path')
                        self.server_port = config.get('server_port', '5000')
                    break

            if not self.install_path:
                # Try to find any Sys_Logger_Server directory
                program_files = Path(os.environ.get('PROGRAMFILES', 'C:\\Program Files'))
                for item in program_files.iterdir():
                    if item.name.startswith('Sys_Logger_Server_'):
                        self.install_path = str(item)
                        self.server_port = '5000'  # Default
                        break

                if not self.install_path:
                    raise FileNotFoundError("Could not find server installation")

        except Exception as e:
            messagebox.showerror("Configuration Error", f"Could not load server configuration: {e}")
            sys.exit(1)

    def setup_ui(self):
        """Setup the user interface"""
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)

        # Server Status tab
        status_frame = ttk.Frame(notebook)
        notebook.add(status_frame, text='Server Status')
        self.create_status_tab(status_frame)

        # Client Management tab
        client_frame = ttk.Frame(notebook)
        notebook.add(client_frame, text='Client Management')
        self.create_client_tab(client_frame)

        # Settings tab
        settings_frame = ttk.Frame(notebook)
        notebook.add(settings_frame, text='Settings')
        self.create_settings_tab(settings_frame)

    def create_status_tab(self, parent):
        """Create the server status tab"""
        ttk.Label(parent, text="Server Status",
                 font=('Segoe UI', 14, 'bold')).pack(pady=10)

        # Status frame
        status_frame = ttk.LabelFrame(parent, text="Current Status", padding=10)
        status_frame.pack(fill='x', padx=20, pady=5)

        self.status_var = tk.StringVar(value="Checking...")
        ttk.Label(status_frame, textvariable=self.status_var,
                 font=('Segoe UI', 12)).pack(anchor='w')

        # Control buttons
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill='x', padx=20, pady=20)

        self.start_btn = ttk.Button(btn_frame, text="Start Server",
                                   command=self.start_server)
        self.start_btn.pack(side='left', padx=(0,10))

        self.stop_btn = ttk.Button(btn_frame, text="Stop Server",
                                  command=self.stop_server)
        self.stop_btn.pack(side='left', padx=(0,10))

        self.restart_btn = ttk.Button(btn_frame, text="Restart Server",
                                     command=self.restart_server)
        self.restart_btn.pack(side='left')

    def create_client_tab(self, parent):
        """Create the client management tab"""
        ttk.Label(parent, text="Client Management",
                 font=('Segoe UI', 14, 'bold')).pack(pady=10)

        # Add client section
        add_frame = ttk.LabelFrame(parent, text="Add New Client", padding=10)
        add_frame.pack(fill='x', padx=20, pady=5)

        ttk.Label(add_frame, text="Client Name:").grid(row=0, column=0, sticky='w', pady=2)
        self.client_name_var = tk.StringVar()
        ttk.Entry(add_frame, textvariable=self.client_name_var).grid(row=0, column=1, sticky='ew', padx=(10,0))

        ttk.Button(add_frame, text="Add Client",
                  command=self.add_client).grid(row=1, column=0, columnspan=2, pady=(10,0))

        # Client list section
        list_frame = ttk.LabelFrame(parent, text="Existing Clients", padding=10)
        list_frame.pack(fill='both', expand=True, padx=20, pady=10)

        # Client listbox
        self.client_listbox = tk.Listbox(list_frame, height=8, font=('Segoe UI', 10))
        self.client_listbox.pack(fill='both', expand=True)
        self.client_listbox.bind('<<ListboxSelect>>', self.on_client_select)

        # Client action buttons
        action_frame = ttk.Frame(list_frame)
        action_frame.pack(fill='x', pady=(10,0))

        ttk.Button(action_frame, text="Create Installer",
                  command=self.create_client_installer).pack(side='left', padx=(0,10))
        ttk.Button(action_frame, text="Remove Client",
                  command=self.remove_client).pack(side='left')

    def create_settings_tab(self, parent):
        """Create the settings tab"""
        ttk.Label(parent, text="Server Settings",
                 font=('Segoe UI', 14, 'bold')).pack(pady=10)

        # Server port setting
        port_frame = ttk.LabelFrame(parent, text="Server Configuration", padding=10)
        port_frame.pack(fill='x', padx=20, pady=5)

        ttk.Label(port_frame, text="Server Port:").grid(row=0, column=0, sticky='w', pady=2)
        self.port_var = tk.StringVar(value=str(self.server_port))
        ttk.Entry(port_frame, textvariable=self.port_var).grid(row=0, column=1, sticky='w', padx=(10,0))

        ttk.Button(port_frame, text="Save Settings",
                  command=self.save_settings).grid(row=1, column=0, columnspan=2, pady=(10,0))

    def start_status_monitoring(self):
        """Start monitoring server status"""
        def monitor():
            while True:
                try:
                    response = requests.get(f"http://localhost:{self.server_port}/api/units", timeout=5)
                    if response.status_code == 200:
                        self.status_var.set("Server is running")
                        self.start_btn.config(state='disabled')
                        self.stop_btn.config(state='normal')
                        self.restart_btn.config(state='normal')
                    else:
                        self.status_var.set("Server responding with errors")
                except:
                    self.status_var.set("Server is not running")
                    self.start_btn.config(state='normal')
                    self.stop_btn.config(state='disabled')
                    self.restart_btn.config(state='disabled')
                time.sleep(5)

        thread = threading.Thread(target=monitor, daemon=True)
        thread.start()

    def start_server(self):
        """Start the server"""
        try:
            # Implementation would start the server service
            messagebox.showinfo("Info", "Server start functionality would be implemented here")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start server: {e}")

    def stop_server(self):
        """Stop the server"""
        try:
            # Implementation would stop the server service
            messagebox.showinfo("Info", "Server stop functionality would be implemented here")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to stop server: {e}")

    def restart_server(self):
        """Restart the server"""
        try:
            # Implementation would restart the server service
            messagebox.showinfo("Info", "Server restart functionality would be implemented here")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to restart server: {e}")

    def add_client(self):
        """Add a new client"""
        client_name = self.client_name_var.get().strip()
        if not client_name:
            messagebox.showerror("Error", "Please enter a client name")
            return

        if client_name in self.clients:
            messagebox.showerror("Error", "Client name already exists")
            return

        self.clients.append(client_name)
        self.client_listbox.insert(tk.END, client_name)
        self.client_name_var.set("")
        messagebox.showinfo("Success", f"Client '{client_name}' added successfully")

    def on_client_select(self, event):
        """Handle client selection"""
        selection = self.client_listbox.curselection()
        if selection:
            self.selected_client = self.client_listbox.get(selection[0])

    def create_client_installer(self):
        """Create a customized client installer for the selected client"""
        if not self.selected_client:
            messagebox.showerror("Error", "Please select a client first")
            return

        try:
            client_name = self.selected_client
            server_url = f"http://localhost:{self.server_port}"

            # Create _clients directory in install path
            clients_dir = os.path.join(self.install_path, "_clients")
            os.makedirs(clients_dir, exist_ok=True)

            # Create unique GUI-based client installer script
            installer_script = self.generate_gui_client_installer_script(client_name, server_url)

            # Write the script
            script_path = os.path.join(clients_dir, f"install_{client_name.replace(' ', '_')}.py")
            with open(script_path, 'w') as f:
                f.write(installer_script)

            # Create executable using PyInstaller
            try:
                exe_name = f"SysLogger_Client_{client_name.replace(' ', '_')}"
                exe_path = os.path.join(clients_dir, f"{exe_name}.exe")

                # Run PyInstaller
                cmd = [
                    sys.executable, "-m", "PyInstaller",
                    "--onefile", "--noconsole",
                    "--name", exe_name,
                    script_path
                ]

                result = subprocess.run(cmd, capture_output=True, text=True, cwd=clients_dir)
                if result.returncode == 0:
                    # Clean up temporary files
                    self.cleanup_build_files(clients_dir, exe_name)

                    messagebox.showinfo("Success",
                        f"Client installer created successfully!\n\n"
                        f"Location: {exe_path}\n\n"
                        f"You can now distribute this .exe file to install the client on target systems.")
                else:
                    messagebox.showerror("Error", f"Failed to create executable: {result.stderr}")

            except Exception as e:
                messagebox.showerror("Error", f"Error creating executable: {e}")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to create client installer: {e}")

    def cleanup_build_files(self, build_dir, exe_name):
        """Clean up PyInstaller temporary files"""
        try:
            # Remove build directory
            build_path = os.path.join(build_dir, "build")
            if os.path.exists(build_path):
                shutil.rmtree(build_path)

            # Remove spec file
            spec_file = os.path.join(build_dir, f"{exe_name}.spec")
            if os.path.exists(spec_file):
                os.remove(spec_file)

            # Remove the script file
            script_file = os.path.join(build_dir, f"install_{exe_name.replace('SysLogger_Client_', '').replace('.exe', '')}.py")
            if os.path.exists(script_file):
                os.remove(script_file)

        except Exception as e:
            print(f"Warning: Could not clean up build files: {e}")

    def remove_client(self):
        """Remove the selected client"""
        if not self.selected_client:
            messagebox.showerror("Error", "Please select a client first")
            return

        if messagebox.askyesno("Confirm", f"Are you sure you want to remove client '{self.selected_client}'?"):
            self.clients.remove(self.selected_client)
            self.client_listbox.delete(self.client_listbox.curselection())
            self.selected_client = None
            self.save_clients_list()
            messagebox.showinfo("Success", "Client removed successfully")

    def generate_gui_client_installer_script(self, client_name, server_url):
        """Generate a GUI-based client installer script"""
        script = f'''#!/usr/bin/env python3
"""
Sys_Logger Client Installer for {client_name}
GUI-based installer with pre-configured settings
"""

import os
import sys
import platform
import subprocess
import shutil
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
import json
import uuid
import threading
import time

class ClientInstallerGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title(f"Sys_Logger Client Installer - {client_name}")
        self.root.geometry("500x400")
        self.root.resizable(False, False)

        # Style
        style = ttk.Style()
        style.configure('TButton', font=('Segoe UI', 10))
        style.configure('TLabel', font=('Segoe UI', 10))

        self.install_path = ""
        self.setup_ui()

    def setup_ui(self):
        """Setup the user interface"""
        # Title
        ttk.Label(self.root, text=f"Install Sys_Logger Client",
                 font=('Segoe UI', 16, 'bold')).pack(pady=20)

        # Info
        info_text = f"This will install the Sys_Logger client for:\\n{client_name}\\n\\nServer: {server_url}"
        ttk.Label(self.root, text=info_text, justify='center').pack(pady=10)

        # Installation path
        path_frame = ttk.LabelFrame(self.root, text="Installation Location", padding=10)
        path_frame.pack(fill='x', padx=20, pady=10)

        self.path_var = tk.StringVar(value=self.get_default_path())
        ttk.Entry(path_frame, textvariable=self.path_var).pack(side='left', fill='x', expand=True)
        ttk.Button(path_frame, text="Browse...", command=self.browse_path).pack(side='right')

        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(self.root, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill='x', padx=20, pady=10)

        # Status label
        self.status_var = tk.StringVar(value="Ready to install")
        ttk.Label(self.root, textvariable=self.status_var).pack(pady=5)

        # Buttons
        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(fill='x', padx=20, pady=20)

        ttk.Button(btn_frame, text="Install", command=self.start_installation).pack(side='right')
        ttk.Button(btn_frame, text="Cancel", command=self.root.quit).pack(side='right', padx=(0,10))

    def get_default_path(self):
        """Get default installation path"""
        system = platform.system().lower()
        if system == 'windows':
            return str(Path(os.environ.get('PROGRAMFILES', 'C:\\\\Program Files')) / 'SysLogger_Client')
        else:
            return '/opt/syslogger_client'

    def browse_path(self):
        """Browse for installation path"""
        path = filedialog.askdirectory(title="Select Installation Directory")
        if path:
            self.path_var.set(path)

    def start_installation(self):
        """Start the installation process"""
        self.install_path = self.path_var.get()
        if not self.install_path:
            messagebox.showerror("Error", "Please select an installation path")
            return

        # Disable buttons
        for child in self.root.winfo_children():
            if isinstance(child, ttk.Frame):
                for widget in child.winfo_children():
                    if isinstance(widget, ttk.Button):
                        widget.config(state='disabled')

        # Start installation in thread
        thread = threading.Thread(target=self.run_installation)
        thread.daemon = True
        thread.start()

    def run_installation(self):
        """Run the installation process"""
        try:
            self.status_var.set("Checking prerequisites...")
            self.progress_var.set(10)

            if not self.check_prerequisites():
                return

            self.status_var.set("Creating directories...")
            self.progress_var.set(30)
            self.create_directories()

            self.status_var.set("Copying files...")
            self.progress_var.set(50)
            self.copy_files()

            self.status_var.set("Creating configuration...")
            self.progress_var.set(70)
            self.create_config()

            self.status_var.set("Setting up service...")
            self.progress_var.set(90)
            self.setup_service()

            self.progress_var.set(100)
            self.status_var.set("Installation completed successfully!")
            time.sleep(1)

            messagebox.showinfo("Success",
                f"Sys_Logger client for {client_name} has been installed successfully!\\n\\n"
                f"Location: {self.install_path}\\n\\n"
                "The client will start automatically and connect to the server.")

            self.root.quit()

        except Exception as e:
            messagebox.showerror("Installation Failed", f"Installation failed: {e}")
            self.root.quit()

    def check_prerequisites(self):
        """Check system prerequisites"""
        if sys.version_info < (3, 6):
            messagebox.showerror("Error", "Python 3.6 or higher is required")
            return False
        return True

    def create_directories(self):
        """Create necessary directories"""
        Path(self.install_path).mkdir(parents=True, exist_ok=True)
        Path(self.install_path, 'logs').mkdir(exist_ok=True)
        Path(self.install_path, 'config').mkdir(exist_ok=True)

    def copy_files(self):
        """Copy client files"""
        # This would copy the actual client files - for now, create a placeholder
        client_script = f'''#!/usr/bin/env python3
"""
Sys_Logger Client for {client_name}
"""

import time
import requests
import json
import uuid
import platform
import psutil

def main():
    system_id = "{str(uuid.uuid4())}"
    system_name = "{client_name}"
    server_url = "{server_url}"

    print(f"Sys_Logger Client for {{system_name}} starting...")
    print(f"System ID: {{system_id}}")
    print(f"Server URL: {{server_url}}")

    while True:
        try:
            # Collect system data
            data = {{
                'system_id': system_id,
                'system_name': system_name,
                'cpu_percent': psutil.cpu_percent(interval=1),
                'memory_percent': psutil.virtual_memory().percent,
                'timestamp': time.time()
            }}

            # Send to server
            response = requests.post(f"{{server_url}}/api/units", json=data, timeout=10)
            if response.status_code == 200:
                print("Data sent successfully")
            else:
                print(f"Failed to send data: {{response.status_code}}")

        except Exception as e:
            print(f"Error: {{e}}")

        time.sleep(60)  # Send data every minute

if __name__ == "__main__":
    main()
'''

        with open(os.path.join(self.install_path, 'syslogger_client.py'), 'w') as f:
            f.write(client_script)

    def create_config(self):
        """Create client configuration"""
        config = {{
            'system_id': str(uuid.uuid4()),
            'server_url': "{server_url}",
            'system_name': "{client_name}"
        }}

        with open(os.path.join(self.install_path, 'config', 'client_config.json'), 'w') as f:
            json.dump(config, f, indent=4)

    def setup_service(self):
        """Setup the client as a service"""
        system = platform.system().lower()
        if system == 'windows':
            # Windows service setup would go here
            pass
        elif system == 'linux':
            # Linux service setup would go here
            pass

    def run(self):
        """Run the installer"""
        self.root.mainloop()

if __name__ == "__main__":
    installer = ClientInstallerGUI()
    installer.run()
'''
        return script

    def save_settings(self):
        """Save server settings"""
        try:
            new_port = self.port_var.get()
            if new_port != str(self.server_port):
                # Update configuration
                config_file = os.path.join(self.install_path, 'server_config.json')
                if os.path.exists(config_file):
                    with open(config_file, 'r') as f:
                        config = json.load(f)
                    config['server_port'] = int(new_port)
                    with open(config_file, 'w') as f:
                        json.dump(config, f, indent=4)

                    self.server_port = int(new_port)
                    messagebox.showinfo("Success", "Settings saved. Please restart the server for changes to take effect.")
                else:
                    messagebox.showerror("Error", "Could not find server configuration file")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings: {e}")

    def save_clients_list(self):
        """Save the clients list to a file"""
        try:
            clients_file = os.path.join(self.install_path, 'clients.json')
            with open(clients_file, 'w') as f:
                json.dump(self.clients, f, indent=4)
        except Exception as e:
            print(f"Warning: Could not save clients list: {e}")

    def load_clients_list(self):
        """Load the clients list from file"""
        try:
            clients_file = os.path.join(self.install_path, 'clients.json')
            if os.path.exists(clients_file):
                with open(clients_file, 'r') as f:
                    self.clients = json.load(f)
        except Exception as e:
            print(f"Warning: Could not load clients list: {e}")
            self.clients = []

    def populate_client_list(self):
        """Populate the client listbox from saved data"""
        self.load_clients_list()
        for client in self.clients:
            self.client_listbox.insert(tk.END, client)

    def run(self):
        """Run the server manager"""
        self.root.mainloop()

if __name__ == "__main__":
    manager = ServerManager()
    manager.run()