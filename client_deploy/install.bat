@echo off
REM ==========================================
REM Sys_Logger One-Click Installer
REM Wraps PowerShell setup script to run silently
REM ==========================================

echo Starting Sys_Logger Setup...

REM Check if running as Admin
net session >nul 2>&1
if %errorLevel% == 0 (
    echo Running with Administrator privileges...
) else (
    echo Requesting Administrator privileges...
    powershell -Command "Start-Process '%~dpnx0' -Verb RunAs"
    exit /b
)

REM Run setup script bypassing execution policy
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup_windows.ps1"

echo.
echo Installation process completed.
echo You can close this window.
pause
