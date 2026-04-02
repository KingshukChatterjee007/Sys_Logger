@echo off
REM ==========================================
REM Sys_Logger Client - One-Click Uninstaller
REM Run as Administrator to remove service
REM ==========================================

echo.
echo ==========================================
echo   Sys_Logger Client - Uninstaller
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

REM Run the PowerShell uninstall script
echo Starting uninstallation...
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0src\uninstall_windows.ps1"

echo.
echo ==========================================
echo   Uninstallation Complete!
echo ==========================================
echo.
pause
