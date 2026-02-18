module.exports = {
  apps: [
    {
      name: "SysLoggerBackend",
      script: "/Users/ayushranjan/Sys_Logger/backend/sys_logger.py",
      cwd: "/Users/ayushranjan/Sys_Logger/backend",
      interpreter: "/Users/ayushranjan/Sys_Logger/backend/venv/bin/python3",
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: "500M",
      env: {
        PYTHONUNBUFFERED: "1",
        PORT: "5001"
      },
      error_file: "./backend_err.log",
      out_file: "./backend_out.log",
      log_date_format: "YYYY-MM-DD HH:mm:ss Z",
    },
  ],
};
