@echo off
echo Building SysLogger Installers...

REM Move to the directory where this script is located
cd /d "%~dp0"

REM Build client installer
echo Building Client Installer...
pyinstaller installation\SysLogger_Client_Installer.spec

IF %errorlevel% NEQ 0 (
    echo Client installer build failed!
    exit /b 1
)

REM Build server installer
echo Building Server Installer...
pyinstaller installation\SysLogger_Server_Installer.spec

IF %errorlevel% NEQ 0 (
    echo Server installer build failed!
    exit /b 1
)

echo.
echo ============================================
echo Installers built successfully!
echo Output directory:
echo   %~dp0dist
echo ============================================
echo.
echo Built EXE files:
dir dist\*.exe
echo.
pause
