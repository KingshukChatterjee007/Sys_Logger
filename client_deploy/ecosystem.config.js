module.exports = {
  apps: [
    {
      name: "sys-logger-client",
      script: "unit_client.py",
      interpreter: "python", // Will be overridden by venv in setup
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: "500M",
      env: {
        PYTHONUNBUFFERED: "1",
        PYTHONIOENCODING: "utf-8",
      },
      error_file: "./logs/err.log",
      out_file: "./logs/out.log",
      log_date_format: "YYYY-MM-DD HH:mm:ss Z",
    },
  ],
};
