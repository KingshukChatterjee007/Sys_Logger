import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import threading
import time
import json
import requests
import datetime
import subprocess
import tempfile
import shutil
import zipfile
import uuid
import sys
import os
from pathlib import Path

# Constants
FOOTER_TEXT = "Product of NIELIT Bhubaneswar - Made by Krishi Sahayogi Team"
DEFAULT_SERVER_URL = "http://localhost:5000"
PRIMARY_COLOR = "#2563eb"   # Enterprise blue
PRIMARY_DARK = "#1d4ed8"
BG_APP = "#f3f4f6"           # Light gray background
CARD_BG = "#ffffff"          # Card/Panel background
BORDER_COLOR = "#d1d5db"
TEXT_MAIN = "#111827"
TEXT_MUTED = "#6b7280"


class ClientManagerGUI(tk.Tk):
    """Enterprise-style SysLogger Client Manager GUI"""

    def __init__(self):
        super().__init__()

        self.title("SysLogger Client Manager")
        self.geometry("1200x800")
        self.configure(bg=BG_APP)

        # Server connection
        self.server_url = DEFAULT_SERVER_URL
        self.public_server_url = DEFAULT_SERVER_URL
        self.units = []
        self.selected_unit = None

        # UI components
        self.tree = None
        self.details_text = None
        self.status_label = None

        # Fetch public IP and update server URL
        self._update_server_url_with_public_ip()

        self._init_style()
        self._init_ui()
        self._init_updates()

        # Load initial data
        self.refresh_units()

    # ------------------------------------------------------------------
    #  STYLE
    # ------------------------------------------------------------------
    def _init_style(self):
        style = ttk.Style(self)
        style.theme_use("clam")

        style.configure(
            "App.TFrame",
            background=BG_APP,
        )

        # Card / panel frames
        style.configure(
            "Card.TFrame",
            background=CARD_BG,
            relief="solid",
            borderwidth=1,
        )

        style.configure(
            "Toolbar.TFrame",
            background=CARD_BG,
            relief="solid",
            borderwidth=0,
        )

        style.configure(
            "Status.TFrame",
            background=CARD_BG,
            relief="solid",
            borderwidth=1,
        )

        # Labels
        style.configure(
            "Title.TLabel",
            background=CARD_BG,
            foreground=TEXT_MAIN,
            font=("Segoe UI", 16, "bold"),
        )

        style.configure(
            "Toolbar.TLabel",
            background=CARD_BG,
            foreground=TEXT_MAIN,
            font=("Segoe UI", 11, "bold"),
        )

        style.configure(
            "Muted.TLabel",
            background=CARD_BG,
            foreground=TEXT_MUTED,
            font=("Segoe UI", 9),
        )

        # Buttons
        style.configure(
            "Primary.TButton",
            font=("Segoe UI", 10, "bold"),
            padding=(10, 6),
            background=PRIMARY_COLOR,
            foreground="white",
            borderwidth=0,
        )
        style.map(
            "Primary.TButton",
            background=[("active", PRIMARY_DARK)],
            foreground=[("disabled", "#9ca3af")],
        )

        style.configure(
            "Secondary.TButton",
            font=("Segoe UI", 10),
            padding=(10, 6),
            background="#e5e7eb",
            foreground=TEXT_MAIN,
            borderwidth=0,
        )
        style.map(
            "Secondary.TButton",
            background=[("active", "#d1d5db")],
        )

        style.configure(
            "Danger.TButton",
            font=("Segoe UI", 10, "bold"),
            padding=(10, 6),
            background="#dc2626",
            foreground="white",
            borderwidth=0,
        )
        style.map(
            "Danger.TButton",
            background=[("active", "#b91c1c")],
        )

        # Treeview styling
        style.configure(
            "Treeview",
            background="white",
            foreground=TEXT_MAIN,
            rowheight=24,
            fieldbackground="white",
            font=("Segoe UI", 10),
        )
        style.configure(
            "Treeview.Heading",
            background="#f3f4f6",
            foreground=TEXT_MAIN,
            font=("Segoe UI", 10, "bold"),
        )
        style.map(
            "Treeview",
            background=[("selected", "#dbeafe")],
            foreground=[("selected", "#1e40af")],
        )

    # ------------------------------------------------------------------
    #  UI LAYOUT
    # ------------------------------------------------------------------
    def _init_ui(self):
        # Root grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # -------------------- Toolbar --------------------
        toolbar = ttk.Frame(self, style="Toolbar.TFrame")
        toolbar.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 0))
        toolbar.grid_columnconfigure(0, weight=1)

        server_label = ttk.Label(
            toolbar,
            text=f"Server: {self.server_url}",
            style="Toolbar.TLabel",
        )
        server_label.grid(row=0, column=0, sticky="w", padx=12, pady=8)

        btn_settings = ttk.Button(
            toolbar,
            text="Settings",
            style="Secondary.TButton",
            command=self.show_settings,
        )
        btn_settings.grid(row=0, column=1, padx=(0, 6), pady=6)

        btn_refresh = ttk.Button(
            toolbar,
            text="Refresh",
            style="Primary.TButton",
            command=self.refresh_units,
        )
        btn_refresh.grid(row=0, column=2, padx=(0, 12), pady=6)

        # -------------------- Main content --------------------
        content = ttk.Frame(self, style="App.TFrame")
        content.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        content.grid_columnconfigure(0, weight=2)
        content.grid_columnconfigure(1, weight=3)
        content.grid_rowconfigure(0, weight=1)

        # ===== Left panel: Clients list =====
        left_panel = ttk.Frame(content, style="Card.TFrame")
        left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        left_panel.grid_columnconfigure(0, weight=1)
        left_panel.grid_rowconfigure(2, weight=1)  # tree expands

        # Title
        title_label = ttk.Label(left_panel, text="Registered Clients", style="Title.TLabel")
        title_label.grid(row=0, column=0, sticky="w", padx=16, pady=(12, 4))

        # Search row
        search_frame = ttk.Frame(left_panel, style="Card.TFrame")
        search_frame.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 8))
        search_frame.grid_columnconfigure(1, weight=1)

        ttk.Label(search_frame, text="Search", background=CARD_BG, foreground=TEXT_MUTED,
                  font=("Segoe UI", 9, "bold")).grid(row=0, column=0, padx=(0, 8), pady=6)

        self.search_var = tk.StringVar()
        self.search_var.trace("w", self.filter_units)
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, font=("Segoe UI", 10))
        search_entry.grid(row=0, column=1, sticky="ew", pady=6)

        clear_btn = ttk.Button(
            search_frame,
            text="Clear",
            style="Secondary.TButton",
            command=lambda: self.search_var.set(""),
        )
        clear_btn.grid(row=0, column=2, padx=(8, 0), pady=4)

        # Treeview area
        tree_frame = ttk.Frame(left_panel, style="Card.TFrame")
        tree_frame.grid(row=2, column=0, sticky="nsew", padx=16, pady=(0, 8))
        tree_frame.grid_columnconfigure(0, weight=1)
        tree_frame.grid_rowconfigure(0, weight=1)

        columns = ("Name", "Status", "Last Seen", "OS", "CPU Usage", "RAM Usage")

        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", selectmode="browse")
        self.tree.grid(row=0, column=0, sticky="nsew")

        # Headings
        for col in columns:
            self.tree.heading(col, text=col, command=lambda c=col: self.sort_by_column(c))

        # Column widths
        self.tree.column("Name", width=160, anchor="w")
        self.tree.column("Status", width=110, anchor="center")
        self.tree.column("Last Seen", width=110, anchor="center")
        self.tree.column("OS", width=130, anchor="w")
        self.tree.column("CPU Usage", width=90, anchor="center")
        self.tree.column("RAM Usage", width=90, anchor="center")

        # Vertical scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.bind("<<TreeviewSelect>>", self.on_unit_select)

        # Action buttons row
        actions_frame = ttk.Frame(left_panel, style="Card.TFrame")
        actions_frame.grid(row=3, column=0, sticky="ew", padx=16, pady=(4, 12))
        actions_frame.grid_columnconfigure((0, 1, 2, 3, 4, 5), weight=1)

        ttk.Label(actions_frame, text="Actions", background=CARD_BG,
                  foreground=TEXT_MUTED, font=("Segoe UI", 9, "bold")).grid(
            row=0, column=0, columnspan=6, sticky="w", pady=(4, 6)
        )

        ttk.Button(
            actions_frame,
            text="Add Client",
            style="Primary.TButton",
            command=self.add_unit,
        ).grid(row=1, column=0, padx=3, pady=4, sticky="ew")

        ttk.Button(
            actions_frame,
            text="Generate Package",
            style="Secondary.TButton",
            command=self.generate_client_package,
        ).grid(row=1, column=1, padx=3, pady=4, sticky="ew")

        ttk.Button(
            actions_frame,
            text="Edit",
            style="Secondary.TButton",
            command=self.edit_unit,
        ).grid(row=1, column=2, padx=3, pady=4, sticky="ew")

        ttk.Button(
            actions_frame,
            text="Delete",
            style="Danger.TButton",
            command=self.delete_unit,
        ).grid(row=1, column=3, padx=3, pady=4, sticky="ew")

        ttk.Button(
            actions_frame,
            text="Toggle Monitoring",
            style="Secondary.TButton",
            command=self.toggle_monitoring,
        ).grid(row=1, column=4, padx=3, pady=4, sticky="ew")

        ttk.Button(
            actions_frame,
            text="Uninstall",
            style="Secondary.TButton",
            command=self.uninstall_unit,
        ).grid(row=1, column=5, padx=3, pady=4, sticky="ew")

        # ===== Right panel: Details =====
        right_panel = ttk.Frame(content, style="Card.TFrame")
        right_panel.grid(row=0, column=1, sticky="nsew", padx=(6, 0))
        right_panel.grid_columnconfigure(0, weight=1)
        right_panel.grid_rowconfigure(1, weight=1)

        details_title = ttk.Label(right_panel, text="Client Details", style="Title.TLabel")
        details_title.grid(row=0, column=0, sticky="w", padx=16, pady=(12, 4))

        self.details_text = scrolledtext.ScrolledText(
            right_panel,
            font=("Consolas", 10),
            bg="#f9fafb",
            fg=TEXT_MAIN,
            relief="flat",
            borderwidth=1,
            highlightthickness=1,
            highlightbackground=BORDER_COLOR,
        )
        self.details_text.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 16))

        # -------------------- Status bar --------------------
        status_frame = ttk.Frame(self, style="Status.TFrame")
        status_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 10))
        status_frame.grid_columnconfigure(0, weight=1)

        self.status_label = ttk.Label(
            status_frame,
            text="Ready",
            background=CARD_BG,
            foreground=TEXT_MAIN,
            font=("Segoe UI", 9),
        )
        self.status_label.grid(row=0, column=0, sticky="w", padx=12, pady=4)

        footer = ttk.Label(
            status_frame,
            text=FOOTER_TEXT,
            style="Muted.TLabel",
        )
        footer.grid(row=0, column=1, sticky="e", padx=12, pady=4)

    # ------------------------------------------------------------------
    #  BACKGROUND UPDATES
    # ------------------------------------------------------------------
    def _init_updates(self):
        self.update_thread = threading.Thread(target=self.auto_refresh, daemon=True)
        self.update_thread.start()

    def _get_public_ip(self):
        """Fetch the public IP address"""
        try:
            response = requests.get("https://api.ipify.org", timeout=5)
            if response.status_code == 200:
                return response.text.strip()
        except Exception:
            pass
        return None

    def _update_server_url_with_public_ip(self):
        """Update server URL with public IP and port forwarding"""
        # First get public IP for client packages
        public_ip = self._get_public_ip()
        if public_ip:
            self.public_server_url = f"http://{public_ip}:5000"

        # For manager connection, first try localhost
        try:
            response = requests.get("http://localhost:5000/api/config", timeout=5)
            if response.status_code == 200:
                config = response.json()
                port = config.get('port', 5000)
                self.server_url = f"http://localhost:{port}"
                return
        except:
            pass

        # If localhost doesn't work, try public IP for manager connection too
        if public_ip:
            # Try to get server config from public IP
            try:
                response = requests.get(f"http://{public_ip}:5000/api/config", timeout=5)
                if response.status_code == 200:
                    config = response.json()
                    port = config.get('port', 5000)
                    self.server_url = f"http://{public_ip}:{port}"
                    return
            except:
                pass
            # Fallback to public IP with default port
            self.server_url = f"http://{public_ip}:5000"
        # If all fails, fallback to DEFAULT_SERVER_URL (localhost:5000)

    def auto_refresh(self):
        while True:
            time.sleep(30)
            try:
                self.refresh_units()
            except Exception:
                # Don't crash the GUI on background errors
                pass

    # ------------------------------------------------------------------
    #  SERVER / DATA HANDLING
    # ------------------------------------------------------------------
    def refresh_units(self):
        """Refresh the units list from server"""
        try:
            self.status_label.config(text="Connecting to server...")
            response = requests.get(f"{self.server_url}/api/units", timeout=10)

            if response.status_code == 200:
                self.units = response.json()
                self.populate_tree()
                self.status_label.config(text=f"Loaded {len(self.units)} clients")
            else:
                self.status_label.config(text=f"Server error: {response.status_code}")
                messagebox.showerror(
                    "Connection Error",
                    f"Failed to connect to server: {response.status_code}",
                )
        except requests.exceptions.RequestException as e:
            self.status_label.config(text="Connection failed")
            messagebox.showerror("Connection Error", f"Cannot connect to server: {e}")

    def populate_tree(self):
        """Populate the treeview with units"""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)

        for unit in self.units:
            last_seen = self.format_last_seen(unit.get("last_seen"))
            status = unit.get("status", "unknown")
            monitoring = "ON" if unit.get("monitoring_enabled", True) else "OFF"

            values = (
                unit.get("name", unit.get("id", "Unknown")),
                f"{status.title()} ({monitoring})",
                last_seen,
                unit.get("os_info", "Unknown"),
                f"{unit.get('cpu_usage', 0):.1f}%" if "cpu_usage" in unit else "N/A",
                f"{unit.get('ram_usage', 0):.1f}%" if "ram_usage" in unit else "N/A",
            )

            item_id = self.tree.insert("", "end", values=values)
            self.tree.item(item_id, tags=(unit.get("id"),))

    @staticmethod
    def format_last_seen(last_seen_str):
        if not last_seen_str:
            return "Never"
        try:
            dt = datetime.datetime.fromisoformat(last_seen_str.replace("Z", "+00:00"))
            now = datetime.datetime.now(datetime.timezone.utc)
            diff = now - dt

            if diff.days > 0:
                return f"{diff.days}d ago"
            if diff.seconds > 3600:
                return f"{diff.seconds // 3600}h ago"
            if diff.seconds > 60:
                return f"{diff.seconds // 60}m ago"
            return "Just now"
        except Exception:
            return "Unknown"

    def filter_units(self, *args):
        search_term = self.search_var.get().lower()
        for item in self.tree.get_children():
            values = self.tree.item(item, "values")
            name = str(values[0]).lower() if values else ""
            if search_term in name:
                self.tree.reattach(item, "", "end")
            else:
                self.tree.detach(item)

    def sort_by_column(self, col):
        items = [(self.tree.set(item, col), item) for item in self.tree.get_children("")]
        try:
            items.sort(reverse=getattr(self, "_sort_reverse", False))
        except Exception:
            items.sort(key=lambda x: str(x[0]).lower(), reverse=getattr(self, "_sort_reverse", False))

        self._sort_reverse = not getattr(self, "_sort_reverse", False)

        for index, (_, item) in enumerate(items):
            self.tree.move(item, "", index)

    # ------------------------------------------------------------------
    #  SELECTION & DETAILS
    # ------------------------------------------------------------------
    def on_unit_select(self, event):
        selection = self.tree.selection()
        if not selection:
            return
        item = selection[0]
        tags = self.tree.item(item, "tags")
        if not tags:
            return
        unit_id = tags[0]

        for unit in self.units:
            if unit.get("id") == unit_id:
                self.selected_unit = unit
                self.show_unit_details(unit)
                break

    def show_unit_details(self, unit):
        details = f"""CLIENT DETAILS
================

ID: {unit.get('id', 'N/A')}
Name: {unit.get('name', 'N/A')}
System ID: {str(unit.get('system_id', 'N/A'))[:8]}...
Status: {unit.get('status', 'unknown').title()}
Monitoring: {'Enabled' if unit.get('monitoring_enabled', True) else 'Disabled'}

SYSTEM INFORMATION
==================

Hostname: {unit.get('hostname', 'N/A')}
OS: {unit.get('os_info', 'N/A')}
CPU: {unit.get('cpu_info', 'N/A')}
RAM Total: {unit.get('ram_total', 0):.1f} GB
GPU Info: {unit.get('gpu_info', 'N/A')}

LAST SEEN
=========

{self.format_last_seen(unit.get('last_seen'))}
Timestamp: {unit.get('last_seen', 'N/A')}

NETWORK INFO
============

{unit.get('network_interfaces', 'N/A')}

ALERTS
======

{len(unit.get('alerts', []))} active alerts"""

        self.details_text.delete("1.0", tk.END)
        self.details_text.insert(tk.END, details)

    # ------------------------------------------------------------------
    #  SETTINGS & CRUD ACTIONS
    # ------------------------------------------------------------------
    def show_settings(self):
        dialog = tk.Toplevel(self)
        dialog.title("Server Settings")
        dialog.geometry("420x200")
        dialog.transient(self)
        dialog.grab_set()

        ttk.Label(dialog, text="Server URL:", font=("Segoe UI", 10, "bold")).pack(pady=(16, 4), anchor="w", padx=20)

        url_var = tk.StringVar(value=self.server_url)
        url_entry = ttk.Entry(dialog, textvariable=url_var, font=("Segoe UI", 10))
        url_entry.pack(fill="x", padx=20)

        def save_settings():
            new_url = url_var.get().strip()
            if new_url:
                self.server_url = new_url
                self.refresh_units()
                dialog.destroy()
            else:
                messagebox.showerror("Error", "Server URL cannot be empty")

        ttk.Button(
            dialog,
            text="Save & Test",
            style="Primary.TButton",
            command=save_settings,
        ).pack(pady=20)

    def add_unit(self):
        dialog = tk.Toplevel(self)
        dialog.title("Add New Client")
        dialog.geometry("480x360")
        dialog.transient(self)
        dialog.grab_set()

        fields = {}

        def add_field(label_text, key):
            ttk.Label(dialog, text=label_text, font=("Segoe UI", 10, "bold")).pack(pady=(8, 2), anchor="w", padx=20)
            entry = ttk.Entry(dialog, font=("Segoe UI", 10))
            entry.pack(fill="x", padx=20)
            fields[key] = entry

        add_field("Client Name", "name")
        add_field("System ID", "system_id")
        add_field("Hostname", "hostname")
        add_field("OS Info", "os_info")

        def save_unit():
            data = {k: v.get().strip() for k, v in fields.items() if v.get().strip()}
            if not data.get("system_id"):
                messagebox.showerror("Error", "System ID is required")
                return
            try:
                response = requests.post(f"{self.server_url}/api/register_unit", json=data, timeout=10)
                if response.status_code in (200, 201):
                    messagebox.showinfo("Success", "Client added successfully")
                    dialog.destroy()
                    self.refresh_units()
                else:
                    messagebox.showerror("Error", f"Failed to add client: {response.status_code}")
            except requests.exceptions.RequestException as e:
                messagebox.showerror("Connection Error", f"Cannot connect: {e}")

        ttk.Button(dialog, text="Add Client", style="Primary.TButton", command=save_unit).pack(pady=18)

    def edit_unit(self):
        if not self.selected_unit:
            messagebox.showwarning("Warning", "Please select a client first")
            return

        dialog = tk.Toplevel(self)
        dialog.title("Edit Client")
        dialog.geometry("420x220")
        dialog.transient(self)
        dialog.grab_set()

        ttk.Label(dialog, text="Client Name:", font=("Segoe UI", 10, "bold")).pack(pady=(16, 4), anchor="w", padx=20)

        name_var = tk.StringVar(value=self.selected_unit.get("name", ""))
        ttk.Entry(dialog, textvariable=name_var, font=("Segoe UI", 10)).pack(fill="x", padx=20)

        def save_changes():
            new_name = name_var.get().strip()
            if not new_name:
                messagebox.showerror("Error", "Name cannot be empty")
                return
            try:
                response = requests.put(
                    f"{self.server_url}/api/units/{self.selected_unit['id']}",
                    json={"name": new_name},
                    timeout=10,
                )
                if response.status_code == 200:
                    messagebox.showinfo("Success", "Client updated successfully")
                    dialog.destroy()
                    self.refresh_units()
                else:
                    messagebox.showerror("Error", f"Failed to update client: {response.status_code}")
            except requests.exceptions.RequestException as e:
                messagebox.showerror("Connection Error", f"Cannot connect: {e}")

        ttk.Button(dialog, text="Save Changes", style="Primary.TButton", command=save_changes).pack(pady=20)

    def delete_unit(self):
        if not self.selected_unit:
            messagebox.showwarning("Warning", "Please select a client first")
            return

        if not messagebox.askyesno(
            "Confirm Delete", f"Are you sure you want to delete client '{self.selected_unit.get('name', 'Unknown')}'?",
        ):
            return

        try:
            response = requests.delete(f"{self.server_url}/api/units/{self.selected_unit['id']}", timeout=10)
            if response.status_code == 200:
                messagebox.showinfo("Success", "Client deleted successfully")
                self.refresh_units()
            else:
                messagebox.showerror("Error", f"Failed to delete client: {response.status_code}")
        except requests.exceptions.RequestException as e:
            messagebox.showerror("Connection Error", f"Cannot connect: {e}")

    def toggle_monitoring(self):
        if not self.selected_unit:
            messagebox.showwarning("Warning", "Please select a client first")
            return

        current_state = self.selected_unit.get("monitoring_enabled", True)
        new_state = not current_state
        action = "enable" if new_state else "disable"

        if not messagebox.askyesno(
            "Confirm",
            f"Are you sure you want to {action} monitoring for '{self.selected_unit.get('name', 'Unknown')}'?",
        ):
            return

        try:
            response = requests.patch(
                f"{self.server_url}/api/units/{self.selected_unit['id']}/status",
                json={"monitoring_enabled": new_state},
                timeout=10,
            )
            if response.status_code == 200:
                messagebox.showinfo("Success", f"Monitoring {action}d successfully")
                self.refresh_units()
            else:
                messagebox.showerror("Error", f"Failed to {action} monitoring: {response.status_code}")
        except requests.exceptions.RequestException as e:
            messagebox.showerror("Connection Error", f"Cannot connect: {e}")

    def uninstall_unit(self):
        if not self.selected_unit:
            messagebox.showwarning("Warning", "Please select a client first")
            return

        unit_name = self.selected_unit.get("name", "Unknown")

        instructions = f"""UNINSTALL INSTRUCTIONS for {unit_name}
==========================================

Remote uninstall is not currently available. Please follow these manual steps:

WINDOWS:
1. Open Task Manager (Ctrl+Shift+Esc)
2. Go to Services tab
3. Find "SysLoggerClient" or "SysLoggerClientProtected"
4. Stop the service
5. Open Command Prompt as Administrator
6. Run: sc delete "SysLoggerClient"
7. Delete the client installation folder

LINUX:
1. Open terminal
2. Run: sudo systemctl stop syslogger
3. Run: sudo systemctl disable syslogger
4. Run: sudo rm /etc/systemd/system/syslogger.service
5. Delete the client installation folder

MACOS:
1. Open Terminal
2. Run: sudo launchctl unload ~/Library/LaunchAgents/syslogger.client.plist
3. Run: sudo launchctl unload /Library/LaunchDaemons/com.syslogger.client.protected.plist
4. Delete plist files and installation folder

After uninstallation, the client will be removed from this list on next refresh."""

        dialog = tk.Toplevel(self)
        dialog.title(f"Uninstall {unit_name}")
        dialog.geometry("720x520")
        dialog.transient(self)
        dialog.grab_set()

        text = scrolledtext.ScrolledText(dialog, font=("Consolas", 10), bg="#f9fafb", fg=TEXT_MAIN)
        text.pack(fill="both", expand=True, padx=12, pady=12)
        text.insert(tk.END, instructions)
        text.config(state="disabled")

        def copy_to_clipboard():
            self.clipboard_clear()
            self.clipboard_append(instructions)
            messagebox.showinfo("Copied", "Instructions copied to clipboard")

        ttk.Button(dialog, text="Copy to Clipboard", style="Secondary.TButton", command=copy_to_clipboard).pack(pady=(0, 12))

    # ------------------------------------------------------------------
    #  PACKAGE GENERATION
    # ------------------------------------------------------------------
    def generate_client_package(self):
        dialog = tk.Toplevel(self)
        dialog.title("Generate Client Package")
        dialog.geometry("520x420")
        dialog.transient(self)
        dialog.grab_set()

        ttk.Label(dialog, text="Package Name", font=("Segoe UI", 10, "bold")).pack(pady=(14, 2), anchor="w", padx=20)
        name_var = tk.StringVar(value="SysLogger_Client_Package")
        ttk.Entry(dialog, textvariable=name_var, font=("Segoe UI", 10)).pack(fill="x", padx=20)

        ttk.Label(dialog, text="Client Name", font=("Segoe UI", 10, "bold")).pack(pady=(10, 2), anchor="w", padx=20)
        client_name_var = tk.StringVar(value="")
        ttk.Entry(dialog, textvariable=client_name_var, font=("Segoe UI", 10)).pack(fill="x", padx=20)

        ttk.Label(dialog, text="Server URL", font=("Segoe UI", 10, "bold")).pack(pady=(10, 2), anchor="w", padx=20)
        ttk.Label(dialog, text="(For remote deployment: use IP address or domain name - NOT localhost)",
                  font=("Segoe UI", 9), foreground="#dc2626").pack(anchor="w", padx=20)
        server_url_var = tk.StringVar(value=self.public_server_url if self.public_server_url != DEFAULT_SERVER_URL else self._get_public_ip() or self.server_url)
        ttk.Entry(dialog, textvariable=server_url_var, font=("Segoe UI", 10)).pack(fill="x", padx=20)

        ttk.Label(dialog, text="Output Directory", font=("Segoe UI", 10, "bold")).pack(pady=(10, 2), anchor="w", padx=20)
        output_var = tk.StringVar()

        output_frame = ttk.Frame(dialog)
        output_frame.pack(fill="x", padx=20)
        ttk.Entry(output_frame, textvariable=output_var, font=("Segoe UI", 10)).pack(side="left", fill="x", expand=True)

        def browse():
            directory = filedialog.askdirectory()
            if directory:
                output_var.set(directory)

        ttk.Button(output_frame, text="Browse...", style="Secondary.TButton", command=browse).pack(side="left", padx=(8, 0))

        def create_package():
            package_name = name_var.get().strip()
            client_name = client_name_var.get().strip()
            server_url = server_url_var.get().strip()
            output_dir = output_var.get().strip()

            if not package_name:
                messagebox.showerror("Error", "Package name is required")
                return
            if not server_url:
                messagebox.showerror("Error", "Server URL is required")
                return
            if not output_dir:
                messagebox.showerror("Error", "Output directory is required")
                return

            threading.Thread(
                target=self._create_client_package,
                args=(package_name, client_name, server_url, output_dir, dialog),
                daemon=True,
            ).start()

        ttk.Button(dialog, text="Generate Package", style="Primary.TButton", command=create_package).pack(pady=24)

    def _create_client_package(self, package_name, client_name, server_url, output_dir, dialog):
        try:
            self.status_label.config(text="Generating client package...")

            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                package_dir = temp_path / package_name
                package_dir.mkdir()

                project_root = Path(".")

                files_to_copy = [
                    ("installation/client_installer.py", "client_installer.py"),
                    ("unit_client.py", "unit_client.py"),
                    ("watchdog.sh", "client_watchdog_template.sh"),
                    ("installation/SysLogger_Client_Installer.spec", "SysLogger_Client_Installer.spec"),
                ]

                for src_rel, dst_name in files_to_copy:
                    src = project_root / src_rel
                    if src.exists():
                        shutil.copy2(src, package_dir / dst_name)
                    else:
                        print(f"Warning: {src_rel} not found")

                config_data = {
                    "system_id": str(uuid.uuid4()),
                    "server_url": server_url,
                    "client_name": client_name,
                    "auto_register": True,
                    "collection_interval": 60,
                    "reconnect_interval": 300,
                }
                config_file = package_dir / "unit_client_config.json"
                json.dump(config_data, config_file.open("w"), indent=4)

                python_exe = sys.executable
                self._create_watchdog_script(package_dir, python_exe)
                self._create_domain_updater(package_dir)

                install_instructions = f"""SYSLOGGER CLIENT INSTALLATION INSTRUCTIONS
==============================================

1. Extract this ZIP file to a folder on the target machine
2. Run the installer executable: {package_name.replace(' ', '_')}_Installer.exe
3. The installer will automatically:
   - Check system requirements
   - Configure the client with server: {server_url}
   - Set up auto-startup services
   - Start monitoring

FILES INCLUDED:
- Installer executable
- Client monitoring software
- Configuration files
- Watchdog and updater scripts

For manual installation (if executable fails):
1. Ensure Python 3.6+ is installed
2. Install dependencies: pip install psutil requests GPUtil
3. Run: python client_installer.py

Client Name: {client_name}
Server URL: {server_url}
System ID: {config_data['system_id'][:8]}...

For support, contact your system administrator.
"""
                readme_file = package_dir / "README.txt"
                readme_file.write_text(install_instructions)

                spec_file = package_dir / "SysLogger_Client_Installer.spec"
                if spec_file.exists():
                    self.status_label.config(text="Building executable (PyInstaller)...")
                    result = subprocess.run([
                        "pyinstaller",
                        "--clean",
                        "--noconfirm",
                        str(spec_file),
                    ], cwd=package_dir, capture_output=True, text=True)

                    if result.returncode != 0:
                        raise Exception(f"PyInstaller failed: {result.stderr}")

                    dist_dir = package_dir / "dist"
                    if dist_dir.exists():
                        exe_files = list(dist_dir.glob("*"))
                        if exe_files:
                            exe_file = exe_files[0]
                            exe_name = exe_file.name
                            if exe_name.startswith("SysLogger_Client_Installer"):
                                new_name = f"{package_name.replace(' ', '_')}_Installer{exe_file.suffix}"
                            else:
                                new_name = exe_name
                            shutil.move(str(exe_file), str(package_dir / new_name))

                for dir_to_remove in (package_dir / "build", package_dir / "dist"):
                    if dir_to_remove.exists():
                        shutil.rmtree(dir_to_remove)
                if spec_file.exists():
                    spec_file.unlink()

                self.status_label.config(text="Creating ZIP package...")
                zip_path = Path(output_dir) / f"{package_name}.zip"
                with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                    for file_path in package_dir.rglob("*"):
                        if file_path.is_file() and not file_path.name.endswith(".spec"):
                            arcname = file_path.relative_to(package_dir)
                            zipf.write(file_path, arcname)

                self.status_label.config(text=f"Package created: {zip_path}")
                messagebox.showinfo(
                    "Success",
                    f"Client package '{package_name}' created successfully!\n\n"
                    f"Location: {zip_path}\n\n"
                    f"Deploy this ZIP file to remote machines for installation.",
                )
        except Exception as e:
            self.status_label.config(text="Package generation failed")
            messagebox.showerror("Package Generation Failed", f"Error: {e}")
        finally:
            dialog.destroy()

    # ------------------------------------------------------------------
    #  SUPPORT SCRIPTS FOR PACKAGE
    # ------------------------------------------------------------------
    @staticmethod
    def _create_watchdog_script(package_dir: Path, python_exe: str):
        watchdog_script = f"""#!/usr/bin/env bash
# SysLogger Client Watchdog
CLIENT_COMMAND=\"{python_exe} unit_client.py --start\"

while true; do
    if ! pgrep -f \"$CLIENT_COMMAND\" > /dev/null; then
        echo \"$(date): SysLogger client not running, restarting...\"
        nohup {python_exe} unit_client.py --start &
    fi
    sleep 30
done
"""
        watchdog_path = package_dir / "client_watchdog.sh"
        watchdog_path.write_text(watchdog_script)
        os.chmod(watchdog_path, 0o755)

    @staticmethod
    def _create_domain_updater(package_dir: Path):
        updater_script = """#!/usr/bin/env python3
import time, json, requests
from pathlib import Path

CONFIG_FILE = Path(__file__).parent / "unit_client_config.json"

while True:
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r") as f:
                cfg = json.load(f)
            url = cfg.get("server_url")
            if url:
                try:
                    r = requests.get(f"{url}/api/domain_config", timeout=10)
                    if r.status_code == 200:
                        cfg.update(r.json())
                        with open(CONFIG_FILE, "w") as f:
                            json.dump(cfg, f, indent=4)
                except Exception as e:
                    print(f"Domain update failed: {e}")
        except Exception as e:
            print(f"Config read error: {e}")
    time.sleep(3600)
"""
        updater_path = package_dir / "domain_updater.py"
        updater_path.write_text(updater_script)
        os.chmod(updater_path, 0o755)


if __name__ == "__main__":
    app = ClientManagerGUI()
    app.mainloop()
