# =====================================
# Sys_Logger Client - Windows Setup Script
# Installs PM2, sets up Python venv, runs the configuration
# wizard, starts the client, and registers auto-start on boot.
#
# MUST be run as Administrator!
# =====================================

Write-Host ""
Write-Host "======================================"
Write-Host "  Sys_Logger Client - Windows Setup   "
Write-Host "======================================"
Write-Host ""

# --- Check Administrator ---
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "ERROR: This script requires Administrator privileges!"
    Write-Host "  Right-click PowerShell and select 'Run as Administrator'"
    exit 1
}

$deployDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# ==========================================
# Step 1: Check Prerequisites (Node.js, PM2)
# ==========================================
Write-Host "[Step 1/6] Checking prerequisites..."

# Check Node.js
if (!(Get-Command node -ErrorAction SilentlyContinue)) {
    Write-Host "  ERROR: Node.js not found!"
    Write-Host "  Download from: https://nodejs.org/"
    Write-Host "  Install Node.js LTS, then re-run this script."
    exit 1
}
Write-Host "  OK Node.js found: $(node -v)"

# Check NPM
if (!(Get-Command npm -ErrorAction SilentlyContinue)) {
    Write-Host "  ERROR: npm not found! NPM is required to install PM2."
    Write-Host "  NPM is usually included with Node.js. Please repair your Node.js installation."
    exit 1
}
Write-Host "  OK npm found: $(npm -v)"

# Check/Install PM2
if (!(Get-Command pm2 -ErrorAction SilentlyContinue)) {
    Write-Host "  Installing PM2 globally..."
    npm install -g pm2
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  ERROR: Failed to install PM2 globally."
        exit 1
    }
    # Refresh PATH in current session
    $env:PATH = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
}
Write-Host "  OK PM2 found (Global installation confirmed)"

# ==========================================
# Step 2: Setup Python Virtual Environment
# ==========================================
Write-Host ""
Write-Host "[Step 2/6] Setting up Python..."

if (!(Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "  ERROR: Python not found!"
    Write-Host "  Download from: https://python.org/"
    exit 1
}

$venvPath = Join-Path $deployDir "venv"
$venvPython = Join-Path $venvPath "Scripts\python.exe"

if (!(Test-Path $venvPython)) {
    Write-Host "  Creating virtual environment..."
    python -m venv $venvPath
}
Write-Host "  OK Python venv ready"

# ==========================================
# Step 3: Install Dependencies
# ==========================================
Write-Host ""
Write-Host "[Step 3/6] Installing dependencies..."

$reqFile = Join-Path $deployDir "requirements.txt"
& $venvPython -m pip install -r $reqFile --quiet
Write-Host "  OK Dependencies installed"

# ==========================================
# Step 4: Configure Unit Identity
# ==========================================
Write-Host ""
Write-Host "[Step 4/6] Configuring unit identity..."
Write-Host "  You will be asked for your Organization ID and Computer ID."
Write-Host "  These are saved once and used every time the client runs."
Write-Host ""

& $venvPython "$deployDir\first_run_wizard.py"

if ($LASTEXITCODE -ne 0) {
    Write-Host "  ERROR: Configuration wizard failed. Cannot continue."
    exit 1
}
Write-Host "  OK Unit identity configured"

# ==========================================
# Step 5: Start Client via PM2
# ==========================================
Write-Host ""
Write-Host "[Step 5/6] Starting client via PM2..."

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

Write-Host "  OK Client is running (hidden background process)"

# ==========================================
# Step 6: Create Auto-Start Task (Silent)
# ==========================================
Write-Host ""
Write-Host "[Step 6/6] Registering auto-start..."

# Create the Ghost Launcher VBScript
$vbsPath = Join-Path $deployDir "launcher.vbs"
$vbsContent = @"
' Sys_Logger - Ghost Launcher
' Runs PM2 resurrect with zero console visibility
Set WshShell = CreateObject("WScript.Shell")
WshShell.Run "pm2 resurrect", 0, False
"@
Set-Content -Path $vbsPath -Value $vbsContent

$taskName = "Sys_Logger_Client_AutoStart"
$currentUser = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
$wscriptPath = "C:\Windows\System32\wscript.exe"

try {
    # Remove existing task if present
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue

    # S4U logon: runs on boot even before user logs in, no password stored
    # Use wscript.exe to run the .vbs file - this ensures ZERO console window
    $action   = New-ScheduledTaskAction -Execute $wscriptPath -Argument "`"$vbsPath`"" -WorkingDirectory $deployDir
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
        -Description "Auto-start Sys_Logger client invisibly on Windows boot via VBS Launcher"

    Write-Host "  OK Auto-start registered! (Invisible background service)"
}
catch {
    Write-Host "  WARNING: Could not register auto-start: $($_.Exception.Message)"
    Write-Host "  Manual setup - open Task Scheduler (taskschd.msc):"
    Write-Host "    Action:  $pm2Path resurrect"
}

# ==========================================
# Verify & Done
# ==========================================
Write-Host ""
Write-Host "Verifying PM2 status..."
Start-Sleep -Seconds 3
pm2 status
Write-Host ""

Write-Host "======================================"
Write-Host "  Setup Complete!                     "
Write-Host "======================================"
Write-Host ""
Write-Host "  Status:     pm2 status"
Write-Host "  Logs:       pm2 logs sys-logger-client"
Write-Host "  Monitor:    pm2 monit"
Write-Host "  Stop:       pm2 stop sys-logger-client"
Write-Host "  Restart:    pm2 restart sys-logger-client"
Write-Host "  Uninstall:  pm2 delete sys-logger-client"
Write-Host ""
Write-Host "  Runs silently in the background on every boot."
Write-Host "  No console window will appear."
Write-Host ""
