# =====================================
# Sys_Logger Client - Windows Setup Script
# Installs PM2, sets up Python venv, runs the configuration
# wizard, starts the client, and registers auto-start on boot.
#
# MUST be run as Administrator!
# =====================================

Write-Host ""
Write-Host "======================================" -ForegroundColor Cyan
Write-Host "  Sys_Logger Client - Windows Setup   " -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

# --- Check Administrator ---
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "ERROR: This script requires Administrator privileges!" -ForegroundColor Red
    Write-Host "  Right-click PowerShell and select 'Run as Administrator'" -ForegroundColor Yellow
    exit 1
}

$deployDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# ==========================================
# Step 1: Check Prerequisites (Node.js, PM2)
# ==========================================
Write-Host "[Step 1/6] Checking prerequisites..." -ForegroundColor Yellow

# Check Node.js
if (!(Get-Command node -ErrorAction SilentlyContinue)) {
    Write-Host "  ERROR: Node.js not found!" -ForegroundColor Red
    Write-Host "  Download from: https://nodejs.org/" -ForegroundColor Yellow
    Write-Host "  Install Node.js LTS, then re-run this script." -ForegroundColor Yellow
    exit 1
}
Write-Host "  OK Node.js found: $(node -v)" -ForegroundColor Green

# Check/Install PM2
if (!(Get-Command pm2 -ErrorAction SilentlyContinue)) {
    Write-Host "  Installing PM2..." -ForegroundColor Yellow
    npm install -g pm2
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  ERROR: Failed to install PM2." -ForegroundColor Red
        exit 1
    }
}
Write-Host "  OK PM2 found" -ForegroundColor Green

# ==========================================
# Step 2: Setup Python Virtual Environment
# ==========================================
Write-Host ""
Write-Host "[Step 2/6] Setting up Python..." -ForegroundColor Yellow

if (!(Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "  ERROR: Python not found!" -ForegroundColor Red
    Write-Host "  Download from: https://python.org/" -ForegroundColor Yellow
    exit 1
}

$venvPath = Join-Path $deployDir "venv"
$venvPython = Join-Path $venvPath "Scripts\python.exe"

if (!(Test-Path $venvPython)) {
    Write-Host "  Creating virtual environment..." -ForegroundColor Yellow
    python -m venv $venvPath
}
Write-Host "  OK Python venv ready" -ForegroundColor Green

# ==========================================
# Step 3: Install Dependencies
# ==========================================
Write-Host ""
Write-Host "[Step 3/6] Installing dependencies..." -ForegroundColor Yellow

$reqFile = Join-Path $deployDir "requirements.txt"
& $venvPython -m pip install -r $reqFile --quiet
Write-Host "  OK Dependencies installed" -ForegroundColor Green

# ==========================================
# Step 4: Configure Unit Identity
# ==========================================
Write-Host ""
Write-Host "[Step 4/6] Configuring unit identity..." -ForegroundColor Yellow
Write-Host "  You will be asked for your Organization ID and Computer ID." -ForegroundColor White
Write-Host "  These are saved once and used every time the client runs." -ForegroundColor White
Write-Host ""

& $venvPython "$deployDir\configure.py"

if ($LASTEXITCODE -ne 0) {
    Write-Host "  ERROR: Configuration wizard failed. Cannot continue." -ForegroundColor Red
    exit 1
}
Write-Host "  OK Unit identity configured" -ForegroundColor Green

# ==========================================
# Step 5: Start Client via PM2
# ==========================================
Write-Host ""
Write-Host "[Step 5/6] Starting client via PM2..." -ForegroundColor Yellow

# Create logs directory
$logsDir = Join-Path $deployDir "logs"
if (!(Test-Path $logsDir)) { New-Item -ItemType Directory -Path $logsDir | Out-Null }

# Stop any existing instance
pm2 delete sys-logger-client 2>$null

# Start with ecosystem config (windowsHide:true keeps it background)
Set-Location $deployDir
pm2 start ecosystem.config.js

# Save the process list (needed for pm2 resurrect on boot)
pm2 save --force

Write-Host "  OK Client is running (hidden background process)" -ForegroundColor Green

# ==========================================
# Step 6: Register Auto-Start on Boot
# ==========================================
Write-Host ""
Write-Host "[Step 6/6] Registering auto-start on boot..." -ForegroundColor Yellow

$pm2Path = (Get-Command pm2 -ErrorAction SilentlyContinue).Source
$currentUser = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
$taskName = "PM2-AutoStart-SysLogger"

try {
    # Remove existing task if present
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue

    # S4U logon: runs on boot even before user logs in, no password stored
    $action   = New-ScheduledTaskAction -Execute $pm2Path -Argument "resurrect" -WorkingDirectory $env:USERPROFILE
    $trigger  = New-ScheduledTaskTrigger -AtStartup
    $settings = New-ScheduledTaskSettingsSet `
        -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries `
        -StartWhenAvailable `
        -ExecutionTimeLimit 0
    $principal = New-ScheduledTaskPrincipal -UserId $currentUser -LogonType S4U -RunLevel Highest

    Register-ScheduledTask `
        -TaskName $taskName `
        -Action $action `
        -Trigger $trigger `
        -Settings $settings `
        -Principal $principal `
        -Description "Auto-start Sys_Logger client on Windows boot via PM2"

    Write-Host "  OK Auto-start registered! (runs on boot, no login required)" -ForegroundColor Green
}
catch {
    Write-Host "  WARNING: Could not register auto-start: $($_.Exception.Message)" -ForegroundColor Yellow
    Write-Host "  Manual setup — open Task Scheduler (taskschd.msc):" -ForegroundColor Yellow
    Write-Host "    Action:  $pm2Path resurrect" -ForegroundColor White
    Write-Host "    Trigger: At system startup" -ForegroundColor White
}

# ==========================================
# Verify & Done
# ==========================================
Write-Host ""
Write-Host "Verifying PM2 status..." -ForegroundColor Yellow
Start-Sleep -Seconds 3
pm2 status
Write-Host ""

Write-Host "======================================" -ForegroundColor Green
Write-Host "  Setup Complete!                     " -ForegroundColor Green
Write-Host "======================================" -ForegroundColor Green
Write-Host ""
Write-Host "  Status:     pm2 status"                         -ForegroundColor White
Write-Host "  Logs:       pm2 logs sys-logger-client"         -ForegroundColor White
Write-Host "  Monitor:    pm2 monit"                          -ForegroundColor White
Write-Host "  Stop:       pm2 stop sys-logger-client"         -ForegroundColor White
Write-Host "  Restart:    pm2 restart sys-logger-client"      -ForegroundColor White
Write-Host "  Uninstall:  pm2 delete sys-logger-client"       -ForegroundColor White
Write-Host ""
Write-Host "  Runs silently in the background on every boot." -ForegroundColor Cyan
Write-Host "  No console window will appear."                  -ForegroundColor Cyan
Write-Host ""
