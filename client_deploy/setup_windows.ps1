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

$venvPath    = Join-Path $deployDir "venv"
$venvPython  = Join-Path $venvPath "Scripts\python.exe"
$venvPythonW = Join-Path $venvPath "Scripts\pythonw.exe"   # No console window

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
#   - Restart on crash (every 60s, up to 99 times)
#   - Never time out (ExecutionTimeLimit = PT0S)
# ==========================================
Write-Host ""
Write-Host "[Step 4/4] Registering hidden auto-start service..." -ForegroundColor Yellow

$taskName   = "SysLoggerClient"
$scriptPath = Join-Path $deployDir "unit_client.py"

# Verify pythonw.exe exists — it is always beside python.exe in a venv
if (!(Test-Path $venvPythonW)) {
    $sysPythonDir = Split-Path (Get-Command python).Source
    $venvPythonW  = Join-Path $sysPythonDir "pythonw.exe"
}

try {
    # Remove any previous version of this task
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue

    # Action — pythonw.exe = fully windowless Python
    $action = New-ScheduledTaskAction `
        -Execute          $venvPythonW `
        -Argument         "`"$scriptPath`" --silent" `
        -WorkingDirectory $deployDir

    # Trigger — fire on every system startup
    $trigger = New-ScheduledTaskTrigger -AtStartup

    # Settings — no timeout, start when available
    $settings = New-ScheduledTaskSettingsSet `
        -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries `
        -StartWhenAvailable `
        -ExecutionTimeLimit (New-TimeSpan -Seconds 0)

    # Principal — current logged-in user, elevated
    $currentUser = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
    $principal = New-ScheduledTaskPrincipal `
        -UserId    $currentUser `
        -LogonType Interactive `
        -RunLevel  Highest

    # Register initial task
    Register-ScheduledTask `
        -TaskName   $taskName `
        -Action     $action `
        -Trigger    $trigger `
        -Settings   $settings `
        -Principal  $principal `
        -Description "Sys_Logger unit client — runs hidden on boot, restarts on crash" | Out-Null

    # Patch XML to add RestartOnFailure (not exposed via cmdlets)
    $taskXml      = Export-ScheduledTask -TaskName $taskName
    $xmlDoc       = [xml]$taskXml
    $ns           = "http://schemas.microsoft.com/windows/2004/02/mit/task"
    $settingsNode = $xmlDoc.Task.Settings

    $restartNode = $xmlDoc.CreateElement("RestartOnFailure", $ns)
    $intervalEl  = $xmlDoc.CreateElement("Interval", $ns); $intervalEl.InnerText = "PT1M"
    $countEl     = $xmlDoc.CreateElement("Count",    $ns); $countEl.InnerText    = "99"
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
    Write-Host "  Register manually in Task Scheduler (taskschd.msc):" -ForegroundColor Yellow
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
Write-Host "  It auto-starts after every reboot and restarts" -ForegroundColor White
Write-Host "  automatically if it crashes." -ForegroundColor White
Write-Host ""
Write-Host "  To check it is running:" -ForegroundColor Cyan
Write-Host "    Task Manager -> Details -> look for pythonw.exe" -ForegroundColor White
Write-Host "  Logs:" -ForegroundColor Cyan
Write-Host "    $logsDir" -ForegroundColor White
Write-Host "  To stop:" -ForegroundColor Cyan
Write-Host "    schtasks /End /TN SysLoggerClient" -ForegroundColor White
Write-Host "  To uninstall:" -ForegroundColor Cyan
Write-Host "    schtasks /Delete /TN SysLoggerClient /F" -ForegroundColor White
Write-Host ""
