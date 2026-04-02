@echo off
setlocal
cd /d "%~dp0"
set LOGFILE=startup_debug.log

echo [%date% %time%] Startup sequence initiated > %LOGFILE%

:: Phase 1: Wait for network
echo [%date% %time%] Phase 1: Waiting for network... >> %LOGFILE%
:retry_net
ping -n 1 8.8.8.8 >nul
if errorlevel 1 (
    echo [%date% %time%] No network yet. Sleeping 10s... >> %LOGFILE%
    timeout /t 10 /nobreak >nul
    goto retry_net
)
echo [%date% %time%] Network detected. >> %LOGFILE%

:: Phase 2: Start PM2
:: Note: The absolute path to PM2 will be injected here by the setup script
:: or we can rely on it being in the PATH since we are running in the user context
echo [%date% %time%] Phase 2: Starting PM2 services... >> %LOGFILE%

:: Attempt to start the client
pm2 start ecosystem.config.js >> %LOGFILE% 2>&1

if errorlevel 1 (
    echo [%date% %time%] pm2 start failed. Attempting resurrect... >> %LOGFILE%
    pm2 resurrect >> %LOGFILE% 2>&1
)

echo [%date% %time%] Startup sequence complete. >> %LOGFILE%
endlocal
