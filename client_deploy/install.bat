@echo off
REM ==========================================
REM Sys_Logger Client - One-Click Installer
REM Run as Administrator for auto-start setup
REM ==========================================

echo.
echo ==========================================
echo   Sys_Logger Client - Installer
echo ==========================================
echo.

REM Check if running as Admin
net session >nul 2>&1
if %errorLevel% == 0 (
    echo Running with Administrator privileges...
) else (
    echo Requesting Administrator privileges...
    powershell -Command "Start-Process '%~dpnx0' -Verb RunAs"
    exit /b
)

REM ==========================================
REM Step 1: Collect org_id and comp_id
REM (uses system Python - runs before venv)
REM ==========================================
echo.
echo Collecting unit configuration...
echo.
python "%~dp0first_run_wizard.py"
if %errorLevel% neq 0 (
    echo.
    echo ERROR: Configuration wizard failed.
    echo Make sure Python is installed and on PATH.
    pause
    exit /b 1
)

REM ==========================================
REM Step 2: Install dependencies and register
REM         service (hidden, auto-start, etc.)
REM ==========================================
echo.
echo Registering background service...
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup_windows.ps1"

echo.
echo ==========================================
echo   Installation Complete!
echo ==========================================
echo.
echo   The client is now running silently in
echo   the background and will auto-start on
echo   every system boot.
echo.
pause
