# =====================================
# Sys_Logger Client - Windows Uninstaller
# Removes the client service, PM2 process,
# Task Scheduler entry, notifies the server,
# and wipes ALL local data.
#
# MUST be run as Administrator!
# =====================================

Write-Host ""
Write-Host "======================================"
Write-Host "  Sys_Logger Client - Uninstaller     "
Write-Host "======================================"
Write-Host ""

$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "ERROR: This script requires Administrator privileges!"
    Write-Host "  Right-click PowerShell and select 'Run as Administrator'"
    exit 1
}

$deployDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$taskName  = "Sys_Logger_Client_AutoStart"

# Step 0: Read config BEFORE deleting anything (needed for server notification)
Write-Host "[0/5] Reading client identity..."
$configFile = Join-Path $deployDir "unit_client_config.json"
$serverUrl = $null
$systemId = $null
$orgId = $null
$compId = $null

if (Test-Path $configFile) {
    try {
        $configData = Get-Content $configFile -Raw | ConvertFrom-Json
        $serverUrl = "http://187.127.142.58"  # Hardcoded server URL
        $systemId = $configData.system_id
        $orgId = $configData.org_id
        $compId = $configData.comp_id
        Write-Host "  OK  Identity: $orgId/$compId"
    } catch {
        Write-Host "  WARNING: Could not parse config file."
    }
} else {
    Write-Host "  SKIP Config file not found. Server will not be notified."
}

# Step 1: Kill running client processes
Write-Host ""
Write-Host "[1/5] Stopping active client processes..."
Get-Process pythonw -ErrorAction SilentlyContinue | Where-Object { $_.Path -like "*$deployDir*" } | Stop-Process -Force -ErrorAction SilentlyContinue
Get-Process python -ErrorAction SilentlyContinue | Where-Object { $_.Path -like "*$deployDir*" } | Stop-Process -Force -ErrorAction SilentlyContinue
Write-Host "  OK  Background processes terminated."

# Step 2: Stop PM2 process
Write-Host ""
Write-Host "[2/5] Stopping PM2 client process..."
try {
    if (Get-Command pm2.cmd -ErrorAction SilentlyContinue) {
        & pm2.cmd delete sys-logger-client --silent 2>$null
        & pm2.cmd save --force 2>$null
        Write-Host "  OK  Client process stopped and removed from PM2."
    } else {
        Write-Host "  SKIP PM2 not found."
    }
} catch {
    Write-Host "  WARNING: Failed to interact with PM2: $_"
}

# Step 3: Remove Scheduled Task
Write-Host ""
Write-Host "[3/5] Removing auto-start task..."
try {
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction Stop
    Write-Host "  OK  Scheduled task '$taskName' removed."
} catch {
    Write-Host "  SKIP Task not found or already removed."
}

# Step 4: Notify Server (Deregister)
Write-Host ""
Write-Host "[4/5] Notifying server of uninstallation..."
if ($serverUrl -and $orgId -and $compId) {
    try {
        $body = @{
            system_id = $systemId
            org_id = $orgId
            comp_id = $compId
        } | ConvertTo-Json

        $response = Invoke-RestMethod -Uri "$serverUrl/api/deregister_unit" -Method POST -Body $body -ContentType "application/json" -TimeoutSec 10
        Write-Host "  OK  Server notified. Node removed from dashboard."
    } catch {
        Write-Host "  WARNING: Could not reach server. Node may remain in dashboard until manually removed."
        Write-Host "           Error: $($_.Exception.Message)"
    }
} else {
    Write-Host "  SKIP No config data available. Server not notified."
}

# Step 5: Wipe ALL local data
Write-Host ""
Write-Host "[5/5] Wiping all local data..."

# Delete config
$configFile = Join-Path $deployDir "unit_client_config.json"
if (Test-Path $configFile) {
    Remove-Item $configFile -Force
    Write-Host "  OK  Config file deleted."
}

# Delete cache
$cacheFile = Join-Path $deployDir "cached_usage.json"
if (Test-Path $cacheFile) {
    Remove-Item $cacheFile -Force
    Write-Host "  OK  Cache file deleted."
}

# Delete logs directory
$logsDir = Join-Path $deployDir "logs"
if (Test-Path $logsDir) {
    Remove-Item $logsDir -Recurse -Force
    Write-Host "  OK  Logs directory deleted."
}

# Delete venv directory
$venvDir = Join-Path $deployDir "venv"
if (Test-Path $venvDir) {
    Remove-Item $venvDir -Recurse -Force
    Write-Host "  OK  Virtual environment deleted."
}

Write-Host "  OK  All local data wiped."

Write-Host ""
Write-Host "======================================"
Write-Host "  Uninstall Complete!                 "
Write-Host "======================================"
Write-Host ""
Write-Host "  The Sys_Logger monitoring agent has been completely removed."
Write-Host "  All local data (config, cache, logs, venv) has been deleted."
Write-Host "  It will no longer appear in logs or run on boot."
Write-Host ""

