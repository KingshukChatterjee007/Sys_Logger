"""
Sys_Logger - Silent Launcher (launcher.pyw)
===========================================
This file is called by ghost_runner.vbs via pythonw.exe.
Running as .pyw means Python starts with NO console window at all.

Responsibilities:
1. Wait for network connectivity.
2. Start unit_client.py as a fully detached subprocess (no parent console).
3. Log any startup issues to logs/startup.log.
"""

import os
import sys
import time
import socket
import subprocess
import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(BASE_DIR, "logs", "startup.log")

# Ensure logs folder exists
os.makedirs(os.path.join(BASE_DIR, "logs"), exist_ok=True)


def log(msg: str):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {msg}\n")
    except:
        pass
    print(f"[{timestamp}] {msg}", flush=True)


def wait_for_network(timeout_secs=120, retry_interval=5):
    """Block until internet is reachable or timeout."""
    log("Waiting for network...")
    deadline = time.time() + timeout_secs
    while time.time() < deadline:
        try:
            socket.setdefaulttimeout(3)
            socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(("8.8.8.8", 53))
            log("Network available.")
            return True
        except OSError:
            time.sleep(retry_interval)
    log("WARNING: Network not available after timeout. Starting anyway.")
    return False


def find_python():
    """Find the venv pythonw.exe (windowless) or python.exe as fallback."""
    candidates = [
        os.path.join(BASE_DIR, "venv", "Scripts", "pythonw.exe"),  # venv Windows
        os.path.join(BASE_DIR, "venv", "Scripts", "python.exe"),   # venv Windows fallback
        os.path.join(BASE_DIR, "venv", "bin", "python"),           # venv Linux/Mac
        sys.executable,                                             # Current interpreter
    ]
    for path in candidates:
        if os.path.isfile(path):
            return path
    return "python"


def launch_client():
    """Launch unit_client.py as a fully detached process."""
    python_exe = find_python()
    client_script = os.path.join(BASE_DIR, "unit_client.py")

    if not os.path.isfile(client_script):
        log(f"ERROR: unit_client.py not found at {client_script}")
        return

    log(f"Launching: {python_exe} {client_script}")

    # DETACHED_PROCESS (0x00000008) on Windows ensures the process is
    # completely decoupled from this launcher — no console, no inherited handles.
    DETACHED_PROCESS = 0x00000008
    CREATE_NO_WINDOW = 0x08000000

    try:        
        err_f = open(os.path.join(BASE_DIR, "logs", "err.log"), "a", encoding="utf-8")
        
        proc = subprocess.Popen(
            [python_exe, client_script],
            cwd=BASE_DIR,
            stdout=subprocess.DEVNULL,
            stderr=err_f,
            stdin=subprocess.DEVNULL,
            creationflags=DETACHED_PROCESS | CREATE_NO_WINDOW,
            close_fds=True,
        )
        log(f"Client started successfully. PID: {proc.pid}")
    except Exception as e:
        log(f"CRITICAL: Failed to start client: {e}")


if __name__ == "__main__":
    log("=== Ghost Runner Launcher starting ===")
    wait_for_network()
    launch_client()
    log("=== Launcher exiting (client is detached and running) ===")
