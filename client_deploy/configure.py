#!/usr/bin/env python3
"""
Sys_Logger Client - First-Run Configuration Wizard
---------------------------------------------------
Run ONCE at install time (by setup_windows.ps1) to collect:
  - Organization ID
  - Computer/Unit ID

Writes the result to unit_client_config.json so that unit_client.py
can run silently under PM2 without ever needing interactive prompts.
"""

import json
import os
import sys
import uuid
import socket
import requests

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, 'unit_client_config.json')
DEFAULT_SERVER_URL = 'http://203.193.145.59:5010'


def load_existing_config():
    """Load existing config if present."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8-sig') as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def is_config_complete(config):
    """Return True if org_id and comp_id are already set to non-default values."""
    org_id = config.get('org_id', '')
    comp_id = config.get('comp_id', '')
    return (
        org_id and org_id != 'default_org' and
        comp_id and comp_id != socket.gethostname() and comp_id != ''
    )


def test_server(url):
    """Try to reach the server health endpoint. Returns True on success."""
    try:
        r = requests.get(f"{url}/api/health", timeout=10)
        return r.status_code == 200
    except requests.RequestException:
        return False


def prompt_configuration(existing_config):
    """Interactively ask user for org_id, comp_id. Returns updated config dict."""
    print()
    print("=" * 55)
    print("  Sys_Logger — Unit Identity Configuration")
    print("=" * 55)
    print()

    existing_org = existing_config.get('org_id', '')
    existing_comp = existing_config.get('comp_id', socket.gethostname())

    # --- Org ID ---
    if existing_org and existing_org != 'default_org':
        print(f"  Current Org ID : {existing_org}")
        change = input("  Keep this Org ID? (y/n) [y]: ").strip().lower()
        if change != 'n':
            org_id = existing_org
        else:
            org_id = ''
    else:
        org_id = ''

    while not org_id:
        val = input("  Enter Organization ID (e.g., org1): ").strip()
        if val:
            org_id = val
        else:
            print("  Organization ID cannot be blank.")

    # --- Comp ID ---
    if existing_comp and existing_comp != 'default_comp':
        print(f"  Current Computer ID : {existing_comp}")
        change = input(f"  Keep this Computer ID? (y/n) [y]: ").strip().lower()
        if change != 'n':
            comp_id = existing_comp
        else:
            comp_id = ''
    else:
        comp_id = ''

    if not comp_id:
        default_comp = socket.gethostname()
        val = input(f"  Enter Computer/Unit ID (default: {default_comp}): ").strip()
        comp_id = val if val else default_comp

    print()
    print(f"  Org ID      : {org_id}")
    print(f"  Computer ID : {comp_id}")
    print()

    return org_id, comp_id


def main():
    print()
    print("Checking existing configuration...")

    config = load_existing_config()

    # If config is already complete, ask if user wants to reconfigure
    if is_config_complete(config):
        print(f"  Found existing config:")
        print(f"    Org ID      : {config.get('org_id')}")
        print(f"    Computer ID : {config.get('comp_id')}")
        print()
        reconfigure = input("  Reconfigure? (y/n) [n]: ").strip().lower()
        if reconfigure != 'y':
            print("  Keeping existing configuration. Done!")
            sys.exit(0)

    # Run the wizard
    org_id, comp_id = prompt_configuration(config)

    # Preserve or generate system_id
    system_id = config.get('system_id') or str(uuid.uuid4())

    # Build updated config
    new_config = {
        'system_id': system_id,
        'server_url': DEFAULT_SERVER_URL,
        'org_id': org_id,
        'comp_id': comp_id,
    }

    # Write config
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(new_config, f, indent=4)
        print(f"  Configuration saved to: {CONFIG_FILE}")
        print()
        print("  Setup will now continue and start the background service.")
        print()
    except OSError as e:
        print(f"  ERROR: Could not write config file: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
