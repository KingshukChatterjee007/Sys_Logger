module.exports = {
  apps: [
    {
      name: "SysLoggerBackend",
      script: "sys_logger.py",
      cwd: "./",
      interpreter: process.platform === 'win32' ? "./venv/Scripts/python.exe" : "./venv/bin/python3",
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: "500M",
      env: {
        PYTHONUNBUFFERED: "1",
        PORT: "5010"
      },
      windowsHide: true,
      error_file: "./backend_err.log",
      out_file: "./backend_out.log",
      log_date_format: "YYYY-MM-DD HH:mm:ss Z",
    },
  ],
};
