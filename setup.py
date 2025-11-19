#!/usr/bin/env python3
"""
Setup script for Sys_Logger Unit Client
This script handles installation and configuration of the unit client.
"""

import os
import sys
import platform
import subprocess
import shutil
from pathlib import Path

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
            print(f"✓ {package} is available")
        except ImportError:
            print(f"Installing {package}...")
            success, output = run_command([sys.executable, '-m', 'pip', 'install', package])
            if not success:
                print(f"Failed to install {package}: {output}")
                return False
            print(f"✓ {package} installed")

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
        return Path(os.environ.get('PROGRAMFILES', 'C:\\Program Files')) / 'UnitClient'
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
        print(f"Created directory: {dir_path}")

def copy_files(install_path):
    """Copy client files to install path"""
    current_dir = Path(__file__).parent

    files_to_copy = [
        'unit_client.py',
        'unit_client_config.json'  # Will be created if doesn't exist
    ]

    for file in files_to_copy:
        src = current_dir / file
        if src.exists():
            dst = install_path / file
            shutil.copy2(src, dst)
            print(f"Copied {file} to {dst}")

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
            print(f"Warning: Failed to create unitclient user: {output}")

    # Set permissions
    success, output = run_command(['sudo', 'chown', '-R', 'unitclient:unitclient', str(install_path)])
    if not success:
        print(f"Warning: Failed to set permissions: {output}")

    # Copy service file
    service_file = Path(__file__).parent / 'unit_client.service'
    if service_file.exists():
        success, output = run_command(['sudo', 'cp', str(service_file), '/etc/systemd/system/'])
        if not success:
            print(f"Failed to copy service file: {output}")
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

    script_path = Path(__file__).parent / 'create_service.ps1'
    if script_path.exists():
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
            print(f"Failed to setup Windows service: {e}")
            return False
    else:
        print("Warning: create_service.ps1 not found")

    return True

def create_config_file(install_path):
    """Create default config file if it doesn't exist"""
    import uuid
    import json

    config_file = install_path / 'unit_client_config.json'
    if not config_file.exists():
        # Generate system ID
        system_id = str(uuid.uuid4())

        # Prompt for server URL during setup
        print("\n--- Server Configuration ---")
        print("Please enter the server URL where this unit should connect.")

        # Import the prompt function from unit_client if available
        try:
            from unit_client import prompt_server_url
            server_url = prompt_server_url()
        except ImportError:
            # Fallback if unit_client module not available
            server_url = input("Enter server URL (default: http://localhost:5000): ").strip()
            if not server_url:
                server_url = 'http://localhost:5000'

        default_config = {
            'system_id': system_id,
            'server_url': server_url
        }

        with open(config_file, 'w') as f:
            json.dump(default_config, f, indent=4)

        print(f"✓ Created config file: {config_file}")
        print(f"  System ID: {system_id}")
        print(f"  Server URL: {server_url}")
    else:
        print(f"Config file already exists: {config_file}")

def main():
    print("Sys_Logger Unit Client Setup")
    print("=" * 30)

    # Check Python version
    if not check_python_version():
        sys.exit(1)

    # Check and install dependencies
    if not check_dependencies():
        sys.exit(1)

    # Determine install path
    install_path = get_install_path()
    print(f"Install path: {install_path}")

    # Create directories
    create_directories(install_path)

    # Copy files
    copy_files(install_path)

    # Create config
    create_config_file(install_path)

    # Setup service based on OS
    system = platform.system().lower()
    if system == 'linux':
        setup_linux_service(install_path)
    elif system == 'windows':
        setup_windows_service(install_path)
    else:
        print(f"Unsupported OS: {system}")
        print("Manual service setup required")

    print("\nSetup completed!")
    print(f"Installation directory: {install_path}")
    print("\nTo run manually:")
    print(f"  cd {install_path}")
    print("  python unit_client.py --foreground  # For testing")
    print("  python unit_client.py --start        # As background service")

    if system == 'linux':
        print("\nService management:")
        print("  sudo systemctl start unit_client")
        print("  sudo systemctl stop unit_client")
        print("  sudo systemctl status unit_client")
        print("  sudo journalctl -u unit_client -f")

if __name__ == "__main__":
    main()