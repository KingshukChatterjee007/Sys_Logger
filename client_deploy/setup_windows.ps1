# =====================================
# Sys_Logger Client - Windows Setup Script
# Installs PM2, sets up Python venv, starts the client,
# and configures auto-start on system boot.
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
Write-Host "[Step 1/5] Checking prerequisites..." -ForegroundColor Yellow

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
Write-Host "[Step 2/5] Setting up Python..." -ForegroundColor Yellow

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
Write-Host "[Step 3/5] Installing dependencies..." -ForegroundColor Yellow

$reqFile = Join-Path $deployDir "requirements.txt"
& $venvPython -m pip install -r $reqFile --quiet
Write-Host "  OK Dependencies installed" -ForegroundColor Green

# ==========================================
# Step 4: Start Client via PM2
# ==========================================
Write-Host ""
Write-Host "[Step 4/5] Starting client via PM2..." -ForegroundColor Yellow

# Create logs directory
$logsDir = Join-Path $deployDir "logs"
if (!(Test-Path $logsDir)) { New-Item -ItemType Directory -Path $logsDir | Out-Null }

# Stop any existing instance
pm2 delete sys-logger-client 2>$null

# Start with ecosystem config
Set-Location $deployDir
pm2 start ecosystem.config.js

# Save the process list (so pm2 resurrect can restore it)
pm2 save --force

Write-Host "  OK Client is running" -ForegroundColor Green

# ==========================================
# Step 5: Register Auto-Start on Boot
# ==========================================
Write-Host ""
Write-Host "[Step 5/5] Registering auto-start on boot..." -ForegroundColor Yellow

$pm2Path = (Get-Command pm2 -ErrorAction SilentlyContinue).Source
$currentUser = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
$taskName = "PM2-AutoStart-SysLogger"

try {
    # Remove existing task if present
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue

    # Create Task Scheduler entry: run "pm2 resurrect" at system startup
    $action = New-ScheduledTaskAction -Execute $pm2Path -Argument "resurrect" -WorkingDirectory $env:USERPROFILE
    $trigger = New-ScheduledTaskTrigger -AtStartup
    $settings = New-ScheduledTaskSettingsSet `
        -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries `
        -StartWhenAvailable
    $principal = New-ScheduledTaskPrincipal -UserId $currentUser -LogonType Interactive -RunLevel Highest

    Register-ScheduledTask `
        -TaskName $taskName `
        -Action $action `
        -Trigger $trigger `
        -Settings $settings `
        -Principal $principal `
        -Description "Auto-start Sys_Logger client on Windows boot via PM2"

    Write-Host "  OK Auto-start registered!" -ForegroundColor Green
}
catch {
    Write-Host "  WARNING: Could not register auto-start: $($_.Exception.Message)" -ForegroundColor Yellow
    Write-Host "  You can manually set it up in Task Scheduler (taskschd.msc):" -ForegroundColor Yellow
    Write-Host "    Action: $pm2Path resurrect" -ForegroundColor White
    Write-Host "    Trigger: At system startup" -ForegroundColor White
}

# ==========================================
# Done!
# ==========================================
Write-Host ""
Write-Host "======================================" -ForegroundColor Green
Write-Host "  Setup Complete!                     " -ForegroundColor Green
Write-Host "======================================" -ForegroundColor Green
Write-Host ""
Write-Host "  Status:     pm2 status" -ForegroundColor White
Write-Host "  Logs:       pm2 logs sys-logger-client" -ForegroundColor White
Write-Host "  Monitor:    pm2 monit" -ForegroundColor White
Write-Host "  Stop:       pm2 stop sys-logger-client" -ForegroundColor White
Write-Host "  Uninstall:  pm2 delete sys-logger-client" -ForegroundColor White
Write-Host ""
Write-Host "  The client will auto-start on every system boot." -ForegroundColor Cyan
Write-Host ""
