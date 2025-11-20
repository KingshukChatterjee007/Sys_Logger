#!/bin/bash
# SysLogger Watchdog Script
# Monitors and restarts the server if it crashes

SERVER_PROCESS="C:\Users\piyus\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.11_qbz5n2kfra8p0\python.exe E:\PROJECTS\Sys_Logger/server_setup.py"
LOG_FILE="/var/log/syslogger_watchdog.log"

while true; do
    # Check if server is running
    if ! pgrep -f "$SERVER_PROCESS" > /dev/null; then
        echo "$(date): Server not running, restarting..." >> $LOG_FILE
        cd E:\PROJECTS\Sys_Logger
        nohup $SERVER_PROCESS >> /var/log/syslogger.log 2>&1 &
    fi
    sleep 30
done
