@echo off
REM Production startup script for System Logger Backend (Windows)

REM Load environment variables from .env file
if exist .env (
    for /f "tokens=1,* delims==" %%a in (.env) do set %%a=%%b
)

REM Create log directory if it doesn't exist
if not exist logs mkdir logs

REM Start with Gunicorn
echo Starting System Logger Backend...
gunicorn --config gunicorn_config.py sys_logger:app

pause

