// Sys_Logger Client - PM2 Ecosystem Config
// This file tells PM2 how to manage the unit_client.py process.
// Paths are resolved dynamically by the setup scripts.

const path = require('path');
const os = require('os');

// Resolve the correct Python path based on OS
const isWindows = os.platform() === 'win32';
const venvPython = isWindows
  ? path.join(__dirname, 'venv', 'Scripts', 'python.exe')
  : path.join(__dirname, 'venv', 'bin', 'python');

module.exports = {
  apps: [
    {
      name: "sys-logger-client",
      script: "unit_client.py",
      args: "--silent",
      interpreter: venvPython,
      cwd: __dirname,
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: "500M",
      min_uptime: "10s",
      max_restarts: 10,
      env: {
        PYTHONUNBUFFERED: "1",
        PYTHONIOENCODING: "utf-8",
      },
      error_file: path.join(__dirname, "logs", "err.log"),
      out_file: path.join(__dirname, "logs", "out.log"),
      log_date_format: "YYYY-MM-DD HH:mm:ss Z",
      merge_logs: true,
    },
  ],
};
