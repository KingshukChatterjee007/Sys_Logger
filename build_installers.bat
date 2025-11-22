@echo off
echo Building SysLogger Installers...

REM Move to the directory where this script is located
cd /d "%~dp0"

REM Clean previous builds
echo Cleaning previous builds...

REM Kill any running SysLogger executables and wait
taskkill /f /im SysLogger_Client_Installer.exe >nul 2>&1
taskkill /f /im SysLogger_Server_Installer.exe >nul 2>&1
taskkill /f /im SysLogger_Client_Manager.exe >nul 2>&1
timeout /t 3 /nobreak >nul

REM Force remove directories with multiple attempts
if exist dist (
    echo Removing dist directory...
    rmdir /s /q dist 2>nul
    if exist dist (
        echo Force removing dist...
        for /d %%i in (dist) do rd /s /q "%%i" 2>nul
    )
    timeout /t 2 /nobreak >nul
)
if exist build (
    echo Removing build directory...
    rmdir /s /q build 2>nul
    if exist build (
        echo Force removing build...
        for /d %%i in (build) do rd /s /q "%%i" 2>nul
    )
    timeout /t 1 /nobreak >nul
)

REM Final check
if exist dist echo Warning: dist directory still exists
if exist build echo Warning: build directory still exists

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

REM Build client manager
echo Building Client Manager...
pyinstaller installation\SysLogger_Client_Manager.spec

IF %errorlevel% NEQ 0 (
    echo Client manager build failed!
    exit /b 1
)

echo.
echo ============================================
echo All installers built successfully!
echo Output directory:
echo   %~dp0dist
echo ============================================
echo.
echo Built EXE files:
dir dist\*.exe
echo.
pause
