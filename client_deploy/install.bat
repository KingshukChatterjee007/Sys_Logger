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

REM Run the PowerShell setup script
echo Starting setup...
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0src\setup_windows.ps1"

echo.
echo ==========================================
echo   Installation Complete!
echo ==========================================
echo.
echo   The client is now running and will
echo   auto-start on every system boot.
echo.
pause
