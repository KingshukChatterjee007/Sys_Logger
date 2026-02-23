# =====================================
# Sys_Logger Client - Windows Setup Script
# Installs dependencies, starts the client hidden,
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
# Step 1: Check Python
# ==========================================
Write-Host "[Step 1/4] Checking Python..." -ForegroundColor Yellow

if (!(Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "  ERROR: Python not found!" -ForegroundColor Red
    Write-Host "  Download from: https://python.org/" -ForegroundColor Yellow
    exit 1
}
Write-Host "  OK Python found: $(python --version)" -ForegroundColor Green

# ==========================================
# Step 2: Setup Python Virtual Environment
# ==========================================
Write-Host ""
Write-Host "[Step 2/4] Setting up Python venv..." -ForegroundColor Yellow

$venvPath     = Join-Path $deployDir "venv"
$venvPython   = Join-Path $venvPath "Scripts\python.exe"
$venvPythonW  = Join-Path $venvPath "Scripts\pythonw.exe"   # No console window

if (!(Test-Path $venvPython)) {
    Write-Host "  Creating virtual environment..." -ForegroundColor Yellow
    python -m venv $venvPath
}

$reqFile = Join-Path $deployDir "requirements.txt"
Write-Host "  Installing dependencies..." -ForegroundColor Yellow
& $venvPython -m pip install -r $reqFile --quiet
Write-Host "  OK Python venv ready" -ForegroundColor Green

# ==========================================
# Step 3: Create logs directory
# ==========================================
Write-Host ""
Write-Host "[Step 3/4] Preparing log directory..." -ForegroundColor Yellow
$logsDir = Join-Path $deployDir "logs"
if (!(Test-Path $logsDir)) { New-Item -ItemType Directory -Path $logsDir | Out-Null }
Write-Host "  OK Logs folder: $logsDir" -ForegroundColor Green

# ==========================================
# Step 4: Register a Hidden Boot Task
#
# Uses pythonw.exe so NO console window ever appears.
# Task Scheduler handles:
#   - Start on every boot (AtStartup)
#   - Restart on crash (RestartOnFailure, every 60s, unlimited)
#   - Never time out (ExecutionTimeLimit = PT0S)
# ==========================================
Write-Host ""
Write-Host "[Step 4/4] Registering hidden auto-start service..." -ForegroundColor Yellow

$taskName  = "SysLoggerClient"
$scriptPath = Join-Path $deployDir "unit_client.py"

# Verify pythonw.exe exists (it's always next to python.exe in a venv)
if (!(Test-Path $venvPythonW)) {
    # Fallback: pythonw.exe lives beside the system python.exe too
    $sysPythonDir = Split-Path (Get-Command python).Source
    $venvPythonW  = Join-Path $sysPythonDir "pythonw.exe"
}

try {
    # Remove any previous version of this task
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue

    # Action  — pythonw.exe = fully windowless Python
    $action = New-ScheduledTaskAction `
        -Execute    $venvPythonW `
        -Argument   "`"$scriptPath`" --silent" `
        -WorkingDirectory $deployDir

    # Trigger — fire on every system startup
    $trigger = New-ScheduledTaskTrigger -AtStartup

    # Settings — no timeout, restart on failure (every 60s, up to 99 times)
    $settings = New-ScheduledTaskSettingsSet `
        -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries `
        -StartWhenAvailable `
        -ExecutionTimeLimit (New-TimeSpan -Seconds 0) `
        -RestartOnIdle:$false

    # Principal — run as the current logged-in user, highest privileges
    $currentUser = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
    $principal = New-ScheduledTaskPrincipal `
        -UserId   $currentUser `
        -LogonType Interactive `
        -RunLevel Highest

    # Register the task
    $task = Register-ScheduledTask `
        -TaskName   $taskName `
        -Action     $action `
        -Trigger    $trigger `
        -Settings   $settings `
        -Principal  $principal `
        -Description "Sys_Logger unit client — runs hidden on boot, restarts on crash"

    # Add restart-on-failure behaviour (not exposed directly by cmdlets)
    # We patch the XML definition after registration
    $taskXml   = (Export-ScheduledTask -TaskName $taskName)
    $xmlDoc    = [xml]$taskXml
    $ns        = "http://schemas.microsoft.com/windows/2004/02/mit/task"
    $settingsNode = $xmlDoc.Task.Settings

    # RestartOnFailure element
    $restartNode = $xmlDoc.CreateElement("RestartOnFailure", $ns)
    $intervalEl  = $xmlDoc.CreateElement("Interval", $ns);  $intervalEl.InnerText  = "PT1M"   # 1 minute
    $countEl     = $xmlDoc.CreateElement("Count", $ns);     $countEl.InnerText     = "99"
    $restartNode.AppendChild($intervalEl) | Out-Null
    $restartNode.AppendChild($countEl)    | Out-Null
    $settingsNode.AppendChild($restartNode) | Out-Null

    # Re-register with patched XML
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue
    Register-ScheduledTask -TaskName $taskName -Xml $xmlDoc.OuterXml -Force | Out-Null

    Write-Host "  OK Task '$taskName' registered — hidden, boot-persistent, auto-restart" -ForegroundColor Green
}
catch {
    Write-Host "  WARNING: Could not register auto-start task: $($_.Exception.Message)" -ForegroundColor Yellow
    Write-Host "  You can register it manually in Task Scheduler (taskschd.msc):" -ForegroundColor Yellow
    Write-Host "    Execute : $venvPythonW" -ForegroundColor White
    Write-Host "    Argument: `"$scriptPath`" --silent" -ForegroundColor White
    Write-Host "    Trigger : At startup" -ForegroundColor White
}

# ==========================================
# Start the client NOW (hidden, immediately)
# ==========================================
Write-Host ""
Write-Host "Starting client now (hidden)..." -ForegroundColor Yellow

# Kill any already-running instance first
Get-Process -Name "python","pythonw" -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -like "*unit_client.py*" } |
    Stop-Process -Force -ErrorAction SilentlyContinue

Start-Process `
    -FilePath         $venvPythonW `
    -ArgumentList     "`"$scriptPath`" --silent" `
    -WorkingDirectory $deployDir `
    -WindowStyle      Hidden

Write-Host "  OK Client is running in the background" -ForegroundColor Green

# ==========================================
# Done!
# ==========================================
Write-Host ""
Write-Host "======================================" -ForegroundColor Green
Write-Host "  Setup Complete!                     " -ForegroundColor Green
Write-Host "======================================" -ForegroundColor Green
Write-Host ""
Write-Host "  The client runs silently with NO visible window." -ForegroundColor White
Write-Host "  It will auto-start after every reboot and restart" -ForegroundColor White
Write-Host "  automatically if it crashes." -ForegroundColor White
Write-Host ""
Write-Host "  To check it's running:" -ForegroundColor Cyan
Write-Host "    Task Manager -> Details -> look for pythonw.exe" -ForegroundColor White
Write-Host "  Logs:"  -ForegroundColor Cyan
Write-Host "    $logsDir" -ForegroundColor White
Write-Host "  To stop:" -ForegroundColor Cyan
Write-Host "    schtasks /End /TN SysLoggerClient" -ForegroundColor White
Write-Host "  To uninstall:" -ForegroundColor Cyan
Write-Host "    schtasks /Delete /TN SysLoggerClient /F" -ForegroundColor White
Write-Host ""


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
