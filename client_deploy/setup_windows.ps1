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
    # Check common roaming path before installing
    $roamingNpm = Join-Path $env:APPDATA "npm"
    $pm2Roaming = Join-Path $roamingNpm "pm2.cmd"
    
    if (Test-Path $pm2Roaming) {
        Write-Host "  OK PM2 found in npm roaming path: $pm2Roaming"
    } else {
        Write-Host "  Installing PM2 globally..."
        npm install -g pm2
        if ($LASTEXITCODE -ne 0) {
            Write-Host "  ERROR: Failed to install PM2 globally."
            exit 1
        }
        # Refresh PATH in current session
        $env:PATH = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
    }
}
Write-Host "  OK PM2 is available"

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

if (Test-Path $venvPython) {
    Write-Host "  Verifying virtual environment..."
    try {
        & $venvPython -c "import requests, psutil, GPUtil" -ErrorAction Stop
        Write-Host "  OK Python venv is healthy"
    } catch {
        Write-Host "  WARNING: Python venv is corrupted. Re-creating..."
        python -m venv --clear $venvPath
    }
} else {
    Write-Host "  Creating virtual environment..."
    python -m venv $venvPath
}

# ==========================================
# Step 3: Install Dependencies
# ==========================================
Write-Host ""
Write-Host "[Step 3/6] Installing dependencies..."

$reqFile = Join-Path $deployDir "requirements.txt"
& $venvPython -m pip install -r $reqFile --quiet
Write-Host "  OK Dependencies installed"

# ==========================================
# Step 4: Validate Pre-Configured Identity
# ==========================================
Write-Host ""
Write-Host "[Step 4/6] Validating unit identity..."

$configFile = Join-Path $deployDir "unit_client_config.json"
if (-not (Test-Path $configFile)) {
    # Try current directory as fallback (for ZIP extraction oddities)
    $configFile = Join-Path (Get-Location) "unit_client_config.json"
}

if (-not (Test-Path $configFile)) {
    Write-Host ""
    Write-Host "  ERROR: unit_client_config.json not found!" -ForegroundColor Red
    Write-Host "  This installer requires a pre-configured package from the admin dashboard."
    Write-Host "  Manual installation is not supported."
    Write-Host ""
    Write-Host "  To get a valid installer:"
    Write-Host "    1. Log into the Sys_Logger dashboard"
    Write-Host "    2. Go to 'Add Node' > 'Download Installer'"
    Write-Host "    3. Extract and run the downloaded package"
    exit 1
}

# Validate config contents
$configData = Get-Content $configFile -Raw | ConvertFrom-Json

if (-not $configData.org_id -or -not $configData.comp_id -or -not $configData.install_token) {
    Write-Host ""
    Write-Host "  ERROR: Invalid configuration file!" -ForegroundColor Red
    Write-Host "  The config is missing required fields (org_id, comp_id, or install_token)."
    Write-Host "  This installer may have been tampered with or already used."
    Write-Host "  Request a new installer from your admin dashboard."
    exit 1
}

Write-Host "  OK Pre-configured installer detected."
Write-Host "    Node: $($configData.comp_id)"
Write-Host "    Org : $($configData.org_id)"
Write-Host "  OK Unit identity validated"

# ==========================================
# Step 5: Start Client Invisibly
# ==========================================
Write-Host ""
Write-Host "[Step 5/6] Starting client invisibly..."

# Create logs directory
$logsDir = Join-Path $deployDir "logs"
if (!(Test-Path $logsDir)) { New-Item -ItemType Directory -Path $logsDir | Out-Null }

# Stop any existing PM2 or VBS instances
& pm2.cmd delete sys-logger-client 2>$null
Get-Process pythonw -ErrorAction SilentlyContinue | Where-Object { $_.Path -like "*$deployDir*" } | Stop-Process -Force -ErrorAction SilentlyContinue

# Start via VBS (Zero-Visibility)
$vbsPath = Join-Path $deployDir "ghost_runner.vbs"
$wscriptPath = "C:\Windows\System32\wscript.exe"
Start-Process $wscriptPath -ArgumentList "`"$vbsPath`"" -WorkingDirectory $deployDir

Write-Host "  OK Client started in the background (No window will appear)"

# ==========================================
# Step 6: Create Auto-Start Task (Silent)
# ==========================================
Write-Host ""
Write-Host "[Step 6/6] Registering auto-start..."

# Find absolute path to pm2.cmd (essential for Task Scheduler)
$pm2Path = Get-Command pm2.cmd -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source
if (!$pm2Path) { $pm2Path = "pm2" }

# Note: We rely on PM2 being in the PATH or the ecosystem config being relative.
# Absolute path injection is disabled to keep files portable for shipping.
# $batContent = Get-Content $batPath
# $batContent = $batContent -replace 'pm2 start', "`"$pm2Path`" start"
# $batContent = $batContent -replace 'pm2 resurrect', "`"$pm2Path`" resurrect"
# Set-Content -Path $batPath -Value $batContent

# === Inject pythonw.exe path (deprecated for shippable VBS) ===
# We now use relative paths in ghost_runner.vbs for better portability.
# Only verifying it exists here.
$pythonwExe = Join-Path $venvPath "Scripts\pythonw.exe"
if (Test-Path $pythonwExe) {
    Write-Host "  OK pythonw.exe verified at: $pythonwExe"
} else {
    Write-Host "  WARNING: pythonw.exe not found. Background mode may fail."
}

$vbsPath = Join-Path $deployDir "ghost_runner.vbs"
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
