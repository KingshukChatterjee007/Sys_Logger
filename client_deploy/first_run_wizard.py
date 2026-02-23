"""
Sys_Logger Client - First Run Wizard
Collects org_id and comp_id from the user, saves to unit_client_config.json.
Uses the hardcoded server URL (no prompt needed).
Run with: python first_run_wizard.py
"""

import json
import os
import socket
import uuid

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'unit_client_config.json')
DEFAULT_SERVER_URL = 'http://203.193.145.59:5010'

def load_existing_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8-sig') as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def main():
    print("")
    print("=" * 50)
    print("  Sys_Logger Client - First-Time Setup")
    print("=" * 50)
    print("")

    existing = load_existing_config()
    system_id = existing.get('system_id', str(uuid.uuid4()))

    # --- Org ID ---
    existing_org = existing.get('org_id', '')
    if existing_org and existing_org != 'default_org':
        prompt_org = f"Enter Organisation ID [{existing_org}]: "
    else:
        prompt_org = "Enter Organisation ID (e.g. org1): "

    org_id = input(prompt_org).strip()
    if not org_id:
        org_id = existing_org if existing_org else 'default_org'

    # --- Computer / Unit ID ---
    hostname = socket.gethostname()
    existing_comp = existing.get('comp_id', '')
    default_comp = existing_comp if existing_comp else hostname
    comp_id = input(f"Enter Computer / Unit ID [{default_comp}]: ").strip()
    if not comp_id:
        comp_id = default_comp

    # --- Save ---
    config = {
        'system_id': system_id,
        'server_url': DEFAULT_SERVER_URL,
        'org_id': org_id,
        'comp_id': comp_id,
    }

    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4)

    print("")
    print("  Configuration saved:")
    print(f"    Organisation ID : {org_id}")
    print(f"    Computer ID     : {comp_id}")
    print("")
    print("  Setup complete! The installer will now register")
    print("  this machine as a background service.")
    print("")

if __name__ == '__main__':
    main()
