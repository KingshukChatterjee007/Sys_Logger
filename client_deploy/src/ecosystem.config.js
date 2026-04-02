// Sys_Logger Client - PM2 Ecosystem Config
// This file tells PM2 how to manage the unit_client.py process.
// Paths are resolved dynamically by the setup scripts.

const path = require('path');
const os = require('os');

// Resolve the correct Python path based on OS
const isWindows = os.platform() === 'win32';
const venvPython = isWindows
  ? path.join(__dirname, 'venv', 'Scripts', 'pythonw.exe')
  : path.join(__dirname, 'venv', 'bin', 'python');

module.exports = {
  apps: [
    {
      name: "sys-logger-client",
      script: "unit_client.py",
      args: "",
      interpreter: venvPython,
      cwd: __dirname,
      instances: 1,

      // --- Crash Recovery ---
      autorestart: true,
      max_restarts: 0,           // 0 = unlimited restarts (never give up)
      restart_delay: 3000,       // wait 3s before restarting on crash
      exp_backoff_restart_delay: 100, // exponential back-off: 100ms → 200 → 400... cap at ~15s
      min_uptime: "10s",         // must run 10s to count as "stable"
      max_memory_restart: "500M",

      // --- Background / Hidden Window ---
      windowsHide: true,         // suppress console window on Windows
      watch: false,

      env: {
        PYTHONUNBUFFERED: "1",
        PYTHONIOENCODING: "utf-8",
      },

      error_file: path.join(__dirname, "logs", "err.log"),
      log_date_format: "YYYY-MM-DD HH:mm:ss Z",
      merge_logs: true,
    },
  ],
};
