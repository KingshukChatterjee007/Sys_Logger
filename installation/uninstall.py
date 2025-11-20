#!/usr/bin/env python3
"""
Sys_Logger Server Uninstaller
GUI-based uninstaller for the Sys_Logger server
"""

import os
import sys
import subprocess
import json
import shutil
import tkinter as tk
from tkinter import messagebox

class Uninstaller:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Sys_Logger Server Uninstaller")
        self.root.geometry("400x300")
        self.root.resizable(False, False)

        # Find installation path
        self.install_path = self.find_install_path()

        self.setup_ui()

    def find_install_path(self):
        """Find the server installation directory"""
        # Try to find from current directory first
        current_dir = os.path.dirname(os.path.abspath(__file__))
        if os.path.exists(os.path.join(current_dir, "server_config.json")):
            with open(os.path.join(current_dir, "server_config.json"), 'r') as f:
                config = json.load(f)
                return config.get('install_path')

        # Try to find in Program Files
        import platform
        if platform.system() == "Windows":
            program_files = os.environ.get('PROGRAMFILES', 'C:\\Program Files')
            for item in os.listdir(program_files):
                if item.startswith('Sys_Logger_Server'):
                    return os.path.join(program_files, item)

        return None

    def setup_ui(self):
        """Setup the user interface"""
        # Title
        title_label = tk.Label(self.root, text="Uninstall Sys_Logger Server",
                              font=('Arial', 16, 'bold'))
        title_label.pack(pady=20)

        # Info
        if self.install_path:
            info_text = f"This will uninstall Sys_Logger Server from:\n\n{self.install_path}"
        else:
            info_text = "Could not find Sys_Logger Server installation."

        info_label = tk.Label(self.root, text=info_text, justify='center')
        info_label.pack(pady=20)

        # Buttons
        button_frame = tk.Frame(self.root)
        button_frame.pack(side=tk.BOTTOM, pady=20)

        if self.install_path:
            uninstall_btn = tk.Button(button_frame, text="Uninstall",
                                     command=self.uninstall, width=10)
            uninstall_btn.pack(side=tk.LEFT, padx=(0,10))

        cancel_btn = tk.Button(button_frame, text="Cancel",
                              command=self.root.quit, width=10)
        cancel_btn.pack(side=tk.LEFT)

    def uninstall(self):
        """Perform the uninstallation"""
        try:
            if not self.install_path:
                messagebox.showerror("Error", "Could not find installation path")
                return

            # Confirm uninstallation
            if not messagebox.askyesno("Confirm Uninstall",
                "Are you sure you want to uninstall Sys_Logger Server?\n\n"
                "This will:\n"
                "• Stop and remove the Windows service\n"
                "• Remove all installed files\n"
                "• Remove desktop shortcuts"):
                return

            # Stop and remove service
            self.stop_service()

            # Remove installation directory
            self.remove_files()

            # Remove shortcuts
            self.remove_shortcuts()

            messagebox.showinfo("Success", "Sys_Logger Server has been successfully uninstalled!")
            self.root.quit()

        except Exception as e:
            messagebox.showerror("Error", f"Uninstallation failed: {str(e)}")

    def stop_service(self):
        """Stop and remove the Windows service"""
        try:
            # Stop service
            subprocess.run(["sc", "stop", "SysLoggerServer"],
                         capture_output=True, timeout=10)

            # Delete service
            subprocess.run(["sc", "delete", "SysLoggerServer"],
                         capture_output=True, timeout=10)

            print("Service stopped and removed")
        except Exception as e:
            print(f"Warning: Could not remove service: {e}")

    def remove_files(self):
        """Remove installation files"""
        try:
            if os.path.exists(self.install_path):
                shutil.rmtree(self.install_path)
                print(f"Removed installation directory: {self.install_path}")
        except Exception as e:
            print(f"Warning: Could not remove installation directory: {e}")

    def remove_shortcuts(self):
        """Remove desktop shortcuts"""
        try:
            desktop = os.path.join(os.path.expanduser("~"), "Desktop")

            shortcuts = [
                "Sys_Logger Server Manager.lnk",
                "Uninstall Sys_Logger Server.lnk"
            ]

            for shortcut in shortcuts:
                shortcut_path = os.path.join(desktop, shortcut)
                if os.path.exists(shortcut_path):
                    os.remove(shortcut_path)
                    print(f"Removed shortcut: {shortcut}")
        except Exception as e:
            print(f"Warning: Could not remove shortcuts: {e}")

    def run(self):
        """Run the uninstaller"""
        self.root.mainloop()

if __name__ == "__main__":
    uninstaller = Uninstaller()
    uninstaller.run()