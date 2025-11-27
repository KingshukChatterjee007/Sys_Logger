#!/usr/bin/env python3
"""
Cross-platform service installer for SysLogger backend server.
Supports Windows (Windows Service), Linux (systemd), and macOS (launchd).
"""

import os
import sys
import platform
import subprocess
import shutil
from pathlib import Path
import argparse

class ServiceInstaller:
    def __init__(self, service_name="SysLoggerBackend", display_name="SysLogger Backend Server"):
        self.service_name = service_name
        self.display_name = display_name
        self.system = platform.system().lower()
        self.script_dir = Path(__file__).parent
        self.python_executable = sys.executable

    def install_service(self):
        """Install the service based on the operating system."""
        print(f"Installing {self.display_name} service...")

        if self.system == "windows":
            return self._install_windows_service()
        elif self.system == "linux":
            return self._install_linux_service()
        elif self.system == "darwin":  # macOS
            return self._install_macos_service()
        else:
            print(f"Unsupported operating system: {self.system}")
            return False

    def uninstall_service(self):
        """Uninstall the service based on the operating system."""
        print(f"Uninstalling {self.display_name} service...")

        if self.system == "windows":
            return self._uninstall_windows_service()
        elif self.system == "linux":
            return self._uninstall_linux_service()
        elif self.system == "darwin":  # macOS
            return self._uninstall_macos_service()
        else:
            print(f"Unsupported operating system: {self.system}")
            return False

    def _install_windows_service(self):
        """Install as Windows service using sc.exe"""
        try:
            # Path to the main script
            script_path = self.script_dir / "sys_logger.py"

            # Create service command
            cmd = [
                "sc.exe", "create", self.service_name,
                f"binPath= \"{self.python_executable} \\\"{script_path}\\\" --service\"",
                f"displayName= \"{self.display_name}\"",
                "start= auto"
            ]

            print(f"Running: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                print("Service created successfully. Starting service...")
                # Start the service
                start_cmd = ["sc.exe", "start", self.service_name]
                start_result = subprocess.run(start_cmd, capture_output=True, text=True)
                if start_result.returncode == 0:
                    print("Service started successfully.")
                    return True
                else:
                    print(f"Failed to start service: {start_result.stderr}")
                    return False
            else:
                print(f"Failed to create service: {result.stderr}")
                return False

        except Exception as e:
            print(f"Error installing Windows service: {e}")
            return False

    def _uninstall_windows_service(self):
        """Uninstall Windows service"""
        try:
            # Stop service first
            stop_cmd = ["sc.exe", "stop", self.service_name]
            subprocess.run(stop_cmd, capture_output=True)

            # Delete service
            delete_cmd = ["sc.exe", "delete", self.service_name]
            result = subprocess.run(delete_cmd, capture_output=True, text=True)

            if result.returncode == 0:
                print("Service uninstalled successfully.")
                return True
            else:
                print(f"Failed to uninstall service: {result.stderr}")
                return False

        except Exception as e:
            print(f"Error uninstalling Windows service: {e}")
            return False

    def _install_linux_service(self):
        """Install as systemd service on Linux"""
        try:
            service_file = f"""
[Unit]
Description={self.display_name}
After=network.target

[Service]
Type=simple
User={os.getenv('USER', 'root')}
ExecStart={self.python_executable} {self.script_dir / "sys_logger.py"} --service
Restart=always
RestartSec=5
Environment=PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
WorkingDirectory={self.script_dir}

[Install]
WantedBy=multi-user.target
"""

            service_path = Path("/etc/systemd/system") / f"{self.service_name}.service"

            # Write service file
            with open(service_path, 'w') as f:
                f.write(service_file.strip())

            # Reload systemd, enable and start service
            commands = [
                ["systemctl", "daemon-reload"],
                ["systemctl", "enable", f"{self.service_name}.service"],
                ["systemctl", "start", f"{self.service_name}.service"]
            ]

            for cmd in commands:
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    print(f"Command failed: {' '.join(cmd)}")
                    print(f"Error: {result.stderr}")
                    return False

            print("Linux service installed and started successfully.")
            return True

        except Exception as e:
            print(f"Error installing Linux service: {e}")
            return False

    def _uninstall_linux_service(self):
        """Uninstall systemd service on Linux"""
        try:
            commands = [
                ["systemctl", "stop", f"{self.service_name}.service"],
                ["systemctl", "disable", f"{self.service_name}.service"]
            ]

            for cmd in commands:
                subprocess.run(cmd, capture_output=True)

            # Remove service file
            service_path = Path("/etc/systemd/system") / f"{self.service_name}.service"
            if service_path.exists():
                service_path.unlink()

            # Reload systemd
            subprocess.run(["systemctl", "daemon-reload"], capture_output=True)

            print("Linux service uninstalled successfully.")
            return True

        except Exception as e:
            print(f"Error uninstalling Linux service: {e}")
            return False

    def _install_macos_service(self):
        """Install as launchd service on macOS"""
        try:
            plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>{self.service_name}</string>
    <key>ProgramArguments</key>
    <array>
        <string>{self.python_executable}</string>
        <string>{self.script_dir / "sys_logger.py"}</string>
        <string>--service</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>WorkingDirectory</key>
    <string>{self.script_dir}</string>
    <key>StandardOutPath</key>
    <string>{self.script_dir / "service.log"}</string>
    <key>StandardErrorPath</key>
    <string>{self.script_dir / "service_error.log"}</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
    </dict>
</dict>
</plist>
"""

            plist_path = Path.home() / "Library" / "LaunchAgents" / f"{self.service_name}.plist"

            # Create LaunchAgents directory if it doesn't exist
            plist_path.parent.mkdir(parents=True, exist_ok=True)

            # Write plist file
            with open(plist_path, 'w') as f:
                f.write(plist_content)

            # Load and start service
            commands = [
                ["launchctl", "load", str(plist_path)],
                ["launchctl", "start", self.service_name]
            ]

            for cmd in commands:
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    print(f"Command failed: {' '.join(cmd)}")
                    print(f"Error: {result.stderr}")
                    return False

            print("macOS service installed and started successfully.")
            return True

        except Exception as e:
            print(f"Error installing macOS service: {e}")
            return False

    def _uninstall_macos_service(self):
        """Uninstall launchd service on macOS"""
        try:
            plist_path = Path.home() / "Library" / "LaunchAgents" / f"{self.service_name}.plist"

            # Stop and unload service
            commands = [
                ["launchctl", "stop", self.service_name],
                ["launchctl", "unload", str(plist_path)]
            ]

            for cmd in commands:
                subprocess.run(cmd, capture_output=True)

            # Remove plist file
            if plist_path.exists():
                plist_path.unlink()

            print("macOS service uninstalled successfully.")
            return True

        except Exception as e:
            print(f"Error uninstalling macOS service: {e}")
            return False

def main():
    parser = argparse.ArgumentParser(description="SysLogger Backend Service Installer")
    parser.add_argument("action", choices=["install", "uninstall"], help="Action to perform")
    parser.add_argument("--name", default="SysLoggerBackend", help="Service name")
    parser.add_argument("--display-name", default="SysLogger Backend Server", help="Display name")

    args = parser.parse_args()

    installer = ServiceInstaller(args.name, args.display_name)

    if args.action == "install":
        success = installer.install_service()
    else:  # uninstall
        success = installer.uninstall_service()

    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()