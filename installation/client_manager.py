import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, simpledialog
import threading
import time
import json
import requests
import socket
import datetime
import webbrowser

# Constants
FOOTER_TEXT = "Product of NIELIT Bhubaneswar - Made by Krishi Sahayogi Team"
DEFAULT_SERVER_URL = "http://localhost:5000"

class ClientManagerGUI(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("SysLogger Client Manager")
        self.geometry("1200x800")
        self.configure(bg="#f8fafc")

        # Server connection
        self.server_url = DEFAULT_SERVER_URL
        self.units = []
        self.selected_unit = None

        # UI components
        self.tree = None
        self.details_text = None
        self.status_label = None

        self._init_style()
        self._init_ui()
        self._init_updates()

        # Load initial data
        self.refresh_units()

    def _init_style(self):
        style = ttk.Style(self)
        style.theme_use("clam")

        style.configure(
            "TButton",
            font=("Segoe UI", 11, "bold"),
            padding=8,
            background="#3b82f6",
            foreground="white"
        )

        style.map("TButton",
                  background=[("active", "#2563eb")])

        style.configure("Card.TFrame", background="white", relief="groove", borderwidth=2)

        # Treeview styling
        style.configure("Treeview",
                       background="white",
                       foreground="#1f2937",
                       rowheight=25,
                       fieldbackground="white",
                       font=("Segoe UI", 10))
        style.configure("Treeview.Heading",
                       background="#f1f5f9",
                       foreground="#374151",
                       font=("Segoe UI", 11, "bold"))
        style.map("Treeview",
                 background=[("selected", "#dbeafe")],
                 foreground=[("selected", "#1e40af")])

    def _init_ui(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Top toolbar
        toolbar = ttk.Frame(self, style="Card.TFrame")
        toolbar.grid(row=0, column=0, columnspan=2, sticky="ew", padx=15, pady=15)

        ttk.Label(toolbar, text=f"Server: {self.server_url}",
                 font=("Segoe UI", 12, "bold")).pack(side="left", padx=10)

        ttk.Button(toolbar, text="🔄 Refresh",
                  command=self.refresh_units).pack(side="right", padx=5)
        ttk.Button(toolbar, text="⚙️ Settings",
                  command=self.show_settings).pack(side="right", padx=5)

        # Main content area
        content = ttk.Frame(self)
        content.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=15, pady=15)
        content.grid_columnconfigure(0, weight=1)
        content.grid_rowconfigure(0, weight=1)

        # Left panel - Units list
        left_panel = ttk.Frame(content, style="Card.TFrame")
        left_panel.grid(row=0, column=0, sticky="nsew", padx=(0,10))

        ttk.Label(left_panel, text="📋 Registered Clients",
                 font=("Segoe UI", 16, "bold")).pack(pady=10, padx=10, anchor="w")

        # Search frame
        search_frame = ttk.Frame(left_panel, style="Card.TFrame")
        search_frame.pack(fill="x", padx=10, pady=(0,10))

        ttk.Label(search_frame, text="🔍").pack(side="left", padx=5)
        self.search_var = tk.StringVar()
        self.search_var.trace("w", self.filter_units)
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var,
                                font=("Segoe UI", 10))
        search_entry.pack(side="left", fill="x", expand=True, padx=(0,5))
        ttk.Button(search_frame, text="Clear",
                  command=lambda: self.search_var.set("")).pack(side="right")

        # Treeview for units
        tree_frame = ttk.Frame(left_panel)
        tree_frame.pack(fill="both", expand=True, padx=10, pady=(0,10))

        columns = ("Name", "Status", "Last Seen", "OS", "CPU Usage", "RAM Usage")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=20)

        for col in columns:
            self.tree.heading(col, text=col, command=lambda c=col: self.sort_by_column(c))
            self.tree.column(col, width=120, minwidth=80)

        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.tree.bind("<<TreeviewSelect>>", self.on_unit_select)

        # Action buttons
        btn_frame = ttk.Frame(left_panel, style="Card.TFrame")
        btn_frame.pack(fill="x", padx=10, pady=10)

        ttk.Button(btn_frame, text="➕ Add Client",
                  command=self.add_unit).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="✏️ Edit",
                  command=self.edit_unit).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="🗑️ Delete",
                  command=self.delete_unit).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="🔌 Toggle Monitoring",
                  command=self.toggle_monitoring).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="🔄 Restart",
                  command=self.restart_unit).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="🛠️ Uninstall",
                  command=self.uninstall_unit).pack(side="right", padx=2)

        # Right panel - Details
        right_panel = ttk.Frame(content, style="Card.TFrame")
        right_panel.grid(row=0, column=1, sticky="nsew")

        ttk.Label(right_panel, text="📊 Client Details",
                 font=("Segoe UI", 16, "bold")).pack(pady=10, padx=10, anchor="w")

        self.details_text = scrolledtext.ScrolledText(right_panel,
                                                    font=("Consolas", 10),
                                                    bg="#f8fafc", fg="#1f2937",
                                                    height=25, relief="flat", borderwidth=1)
        self.details_text.pack(fill="both", expand=True, padx=10, pady=(0,10))

        # Status bar
        status_frame = ttk.Frame(self, style="Card.TFrame")
        status_frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=15, pady=(0,15))

        self.status_label = ttk.Label(status_frame, text="Ready",
                                     font=("Segoe UI", 10))
        self.status_label.pack(side="left", padx=10)

        ttk.Label(status_frame, text=FOOTER_TEXT,
                 font=("Segoe UI", 9), foreground="#6b7280").pack(side="right", padx=10)

    def _init_updates(self):
        """Initialize real-time updates"""
        self.update_thread = threading.Thread(target=self.auto_refresh, daemon=True)
        self.update_thread.start()

    def auto_refresh(self):
        """Auto-refresh units every 30 seconds"""
        while True:
            time.sleep(30)
            try:
                self.refresh_units()
            except:
                pass  # Silently fail auto-refresh

    def refresh_units(self):
        """Refresh the units list from server"""
        try:
            self.status_label.config(text="🔄 Connecting to server...")
            response = requests.get(f"{self.server_url}/api/units", timeout=10)

            if response.status_code == 200:
                self.units = response.json()
                self.populate_tree()
                self.status_label.config(text=f"✅ Loaded {len(self.units)} clients")
            else:
                self.status_label.config(text=f"❌ Server error: {response.status_code}")
                messagebox.showerror("Connection Error",
                                   f"Failed to connect to server: {response.status_code}")

        except requests.exceptions.RequestException as e:
            self.status_label.config(text="❌ Connection failed")
            messagebox.showerror("Connection Error",
                               f"Cannot connect to server: {str(e)}")

    def populate_tree(self):
        """Populate the treeview with units"""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Add units
        for unit in self.units:
            last_seen = self.format_last_seen(unit.get('last_seen'))
            status = unit.get('status', 'unknown')
            monitoring = "🟢" if unit.get('monitoring_enabled', True) else "🔴"

            values = (
                unit.get('name', unit.get('id', 'Unknown')),
                f"{monitoring} {status.title()}",
                last_seen,
                unit.get('os_info', 'Unknown'),
                f"{unit.get('cpu_usage', 0):.1f}%" if 'cpu_usage' in unit else "N/A",
                f"{unit.get('ram_usage', 0):.1f}%" if 'ram_usage' in unit else "N/A"
            )

            item_id = self.tree.insert("", "end", values=values)
            self.tree.item(item_id, tags=(unit.get('id'),))

    def format_last_seen(self, last_seen_str):
        """Format last seen timestamp"""
        if not last_seen_str:
            return "Never"

        try:
            dt = datetime.datetime.fromisoformat(last_seen_str.replace('Z', '+00:00'))
            now = datetime.datetime.now(datetime.timezone.utc)
            diff = now - dt

            if diff.days > 0:
                return f"{diff.days}d ago"
            elif diff.seconds > 3600:
                return f"{diff.seconds // 3600}h ago"
            elif diff.seconds > 60:
                return f"{diff.seconds // 60}m ago"
            else:
                return "Just now"
        except:
            return "Unknown"

    def filter_units(self, *args):
        """Filter units based on search"""
        search_term = self.search_var.get().lower()

        for item in self.tree.get_children():
            values = self.tree.item(item, "values")
            name = str(values[0]).lower()

            if search_term in name:
                self.tree.reattach(item, "", "end")
            else:
                self.tree.detach(item)

    def sort_by_column(self, col):
        """Sort treeview by column"""
        items = [(self.tree.set(item, col), item) for item in self.tree.get_children()]

        try:
            items.sort(reverse=getattr(self, 'sort_reverse', False))
        except:
            items.sort(key=lambda x: x[0].lower(), reverse=getattr(self, 'sort_reverse', False))

        self.sort_reverse = not getattr(self, 'sort_reverse', False)

        for index, (_, item) in enumerate(items):
            self.tree.move(item, "", index)

    def on_unit_select(self, event):
        """Handle unit selection"""
        selection = self.tree.selection()
        if selection:
            item = selection[0]
            unit_id = self.tree.item(item, "tags")[0]

            # Find unit details
            for unit in self.units:
                if unit.get('id') == unit_id:
                    self.selected_unit = unit
                    self.show_unit_details(unit)
                    break

    def show_unit_details(self, unit):
        """Show detailed information about selected unit"""
        details = f"""CLIENT DETAILS
================

ID: {unit.get('id', 'N/A')}
Name: {unit.get('name', 'N/A')}
System ID: {unit.get('system_id', 'N/A')[:8]}...
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

        self.details_text.delete(1.0, tk.END)
        self.details_text.insert(tk.END, details)

    def show_settings(self):
        """Show server settings dialog"""
        dialog = tk.Toplevel(self)
        dialog.title("Server Settings")
        dialog.geometry("400x200")
        dialog.transient(self)
        dialog.grab_set()

        ttk.Label(dialog, text="Server URL:",
                 font=("Segoe UI", 11)).pack(pady=10)

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

        ttk.Button(dialog, text="Save & Test",
                  command=save_settings).pack(pady=20)

    def add_unit(self):
        """Add a new unit manually"""
        dialog = tk.Toplevel(self)
        dialog.title("Add New Client")
        dialog.geometry("500x400")
        dialog.transient(self)
        dialog.grab_set()

        # Form fields
        fields = {}
        ttk.Label(dialog, text="Client Name:",
                 font=("Segoe UI", 11)).pack(pady=5, anchor="w", padx=20)
        fields['name'] = ttk.Entry(dialog, font=("Segoe UI", 10))
        fields['name'].pack(fill="x", padx=20)

        ttk.Label(dialog, text="System ID:",
                 font=("Segoe UI", 11)).pack(pady=5, anchor="w", padx=20)
        fields['system_id'] = ttk.Entry(dialog, font=("Segoe UI", 10))
        fields['system_id'].pack(fill="x", padx=20)

        ttk.Label(dialog, text="Hostname:",
                 font=("Segoe UI", 11)).pack(pady=5, anchor="w", padx=20)
        fields['hostname'] = ttk.Entry(dialog, font=("Segoe UI", 10))
        fields['hostname'].pack(fill="x", padx=20)

        ttk.Label(dialog, text="OS Info:",
                 font=("Segoe UI", 11)).pack(pady=5, anchor="w", padx=20)
        fields['os_info'] = ttk.Entry(dialog, font=("Segoe UI", 10))
        fields['os_info'].pack(fill="x", padx=20)

        def save_unit():
            data = {k: v.get().strip() for k, v in fields.items() if v.get().strip()}

            if not data.get('system_id'):
                messagebox.showerror("Error", "System ID is required")
                return

            try:
                response = requests.post(f"{self.server_url}/api/register_unit",
                                       json=data, timeout=10)

                if response.status_code in [200, 201]:
                    messagebox.showinfo("Success", "Client added successfully")
                    dialog.destroy()
                    self.refresh_units()
                else:
                    messagebox.showerror("Error",
                                       f"Failed to add client: {response.status_code}")

            except requests.exceptions.RequestException as e:
                messagebox.showerror("Connection Error", f"Cannot connect: {str(e)}")

        ttk.Button(dialog, text="Add Client",
                  command=save_unit).pack(pady=20)

    def edit_unit(self):
        """Edit selected unit"""
        if not self.selected_unit:
            messagebox.showwarning("Warning", "Please select a client first")
            return

        dialog = tk.Toplevel(self)
        dialog.title("Edit Client")
        dialog.geometry("400x200")
        dialog.transient(self)
        dialog.grab_set()

        ttk.Label(dialog, text="Client Name:",
                 font=("Segoe UI", 11)).pack(pady=10, anchor="w", padx=20)

        name_var = tk.StringVar(value=self.selected_unit.get('name', ''))
        name_entry = ttk.Entry(dialog, textvariable=name_var, font=("Segoe UI", 10))
        name_entry.pack(fill="x", padx=20)

        def save_changes():
            new_name = name_var.get().strip()
            if not new_name:
                messagebox.showerror("Error", "Name cannot be empty")
                return

            try:
                response = requests.put(f"{self.server_url}/api/units/{self.selected_unit['id']}",
                                      json={'name': new_name}, timeout=10)

                if response.status_code == 200:
                    messagebox.showinfo("Success", "Client updated successfully")
                    dialog.destroy()
                    self.refresh_units()
                else:
                    messagebox.showerror("Error",
                                       f"Failed to update client: {response.status_code}")

            except requests.exceptions.RequestException as e:
                messagebox.showerror("Connection Error", f"Cannot connect: {str(e)}")

        ttk.Button(dialog, text="Save Changes",
                  command=save_changes).pack(pady=20)

    def delete_unit(self):
        """Delete selected unit"""
        if not self.selected_unit:
            messagebox.showwarning("Warning", "Please select a client first")
            return

        if messagebox.askyesno("Confirm Delete",
                              f"Are you sure you want to delete client '{self.selected_unit.get('name', 'Unknown')}'?"):
            try:
                response = requests.delete(f"{self.server_url}/api/units/{self.selected_unit['id']}",
                                         timeout=10)

                if response.status_code == 200:
                    messagebox.showinfo("Success", "Client deleted successfully")
                    self.refresh_units()
                else:
                    messagebox.showerror("Error",
                                       f"Failed to delete client: {response.status_code}")

            except requests.exceptions.RequestException as e:
                messagebox.showerror("Connection Error", f"Cannot connect: {str(e)}")

    def toggle_monitoring(self):
        """Toggle monitoring for selected unit"""
        if not self.selected_unit:
            messagebox.showwarning("Warning", "Please select a client first")
            return

        current_state = self.selected_unit.get('monitoring_enabled', True)
        new_state = not current_state

        action = "enable" if new_state else "disable"

        if messagebox.askyesno("Confirm",
                              f"Are you sure you want to {action} monitoring for '{self.selected_unit.get('name', 'Unknown')}'?"):
            try:
                response = requests.patch(f"{self.server_url}/api/units/{self.selected_unit['id']}/status",
                                        json={'monitoring_enabled': new_state}, timeout=10)

                if response.status_code == 200:
                    messagebox.showinfo("Success", f"Monitoring {action}d successfully")
                    self.refresh_units()
                else:
                    messagebox.showerror("Error",
                                       f"Failed to {action} monitoring: {response.status_code}")

            except requests.exceptions.RequestException as e:
                messagebox.showerror("Connection Error", f"Cannot connect: {str(e)}")

    def restart_unit(self):
        """Attempt to restart monitoring on selected unit"""
        if not self.selected_unit:
            messagebox.showwarning("Warning", "Please select a client first")
            return

        messagebox.showinfo("Restart", "Restart functionality requires remote access to client machines.\n\nPlease manually restart the client application on the target machine.")

    def uninstall_unit(self):
        """Show uninstall instructions for selected unit"""
        if not self.selected_unit:
            messagebox.showwarning("Warning", "Please select a client first")
            return

        unit_name = self.selected_unit.get('name', 'Unknown')

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
        dialog.geometry("700x500")
        dialog.transient(self)
        dialog.grab_set()

        text = scrolledtext.ScrolledText(dialog, font=("Consolas", 10),
                                       bg="#f8fafc", fg="#1f2937")
        text.pack(fill="both", expand=True, padx=10, pady=10)
        text.insert(tk.END, instructions)
        text.config(state="disabled")

        ttk.Button(dialog, text="Copy to Clipboard",
                  command=lambda: self.clipboard_append(instructions)).pack(pady=10)

if __name__ == "__main__":
    app = ClientManagerGUI()
    app.mainloop()