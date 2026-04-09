import os
import sys
import subprocess
import time
import requests
import json

BASE_DIR = os.getcwd()
BACKEND_DIR = os.path.join(BASE_DIR, "backend")

def run_sql(sql):
    subprocess.call(["psql", "-U", "postgres", "-d", "sys_logger", "-c", sql])

def verify():
    # 1. Setup
    print("Step 1: Cleaning up and seeding DB...")
    run_sql("DELETE FROM systems WHERE LOWER(system_name) = '1/testcase'")
    run_sql("INSERT INTO systems (system_name, org_id, install_token, status) VALUES ('1/TestCase', 1, 'verified-token', 'pending')")

    # 2. Start Backend
    print("\nStep 2: Starting Backend...")
    proc = subprocess.Popen(["./venv/bin/python3", "sys_logger.py"], 
                            cwd=BACKEND_DIR,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT,
                            text=True)
    time.sleep(5)

    try:
        # 3. Register via API
        print("\nStep 3: Registering via API with Uppercase Mismatch (TESTCASE)...")
        payload = {
            "system_id": "test-verify-uuid",
            "org_id": "1",
            "comp_id": "TESTCASE",
            "install_token": "verified-token",
            "hostname": "Verify-Host"
        }
        resp = requests.post("http://127.0.0.1:5010/api/register_unit", json=payload, timeout=10)
        print(f"Server Response ({resp.status_code}): {json.dumps(resp.json(), indent=2)}")

        # Print some backend output
        print("\nBackend Debug Output:")
        time.sleep(3)
        while proc.poll() is None:
            # Non-blocking read
            import os, fcntl
            fd = proc.stdout.fileno()
            fl = fcntl.fcntl(fd, fcntl.F_GETFL)
            fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)
            try:
                out = proc.stdout.read()
                if out: print(out)
                else: break
            except: break

        # 4. Verify DB
        print("\nStep 4: Checking DB status...")
        subprocess.call(["psql", "-U", "postgres", "-d", "sys_logger", "-c", "SELECT system_name, status, last_seen FROM systems WHERE LOWER(system_name) = '1/testcase'"])

    finally:
        print("\nStep 5: Cleaning up...")
        proc.terminate()
        run_sql("DELETE FROM systems WHERE LOWER(system_name) = '1/testcase'")

if __name__ == "__main__":
    verify()
