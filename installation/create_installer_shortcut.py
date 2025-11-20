#!/usr/bin/env python3
"""
Create desktop shortcut for Sys_Logger Server Installer
"""

import os
import sys
from pathlib import Path

def create_installer_shortcut():
    """Create desktop shortcut for the installer"""
    try:
        from win32com.client import Dispatch

        # Get current script directory (installer location)
        installer_dir = Path(__file__).parent
        installer_path = installer_dir / "server_installer.py"

        # Desktop path
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        shortcut_path = os.path.join(desktop, "Sys_Logger Server Installer.lnk")

        shell = Dispatch('WScript.Shell')
        shortcut = shell.CreateShortCut(shortcut_path)
        shortcut.Targetpath = str(installer_path)
        shortcut.WorkingDirectory = str(installer_dir)
        shortcut.Description = "Install Sys_Logger Server"
        shortcut.save()

        print("✓ Created installer shortcut on desktop")

    except ImportError:
        print("Warning: pywin32 not available, cannot create shortcut")
    except Exception as e:
        print(f"Warning: Could not create installer shortcut: {e}")

if __name__ == "__main__":
    create_installer_shortcut()