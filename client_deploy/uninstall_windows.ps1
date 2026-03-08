# =====================================
# Sys_Logger Client - Windows Uninstaller
# Removes the client service, PM2 process,
# Task Scheduler entry, and optionally the files.
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

# Step 0: Kill running client processes
Write-Host "[0/4] Stopping active client processes..."
Get-Process pythonw -ErrorAction SilentlyContinue | Where-Object { $_.Path -like "*$deployDir*" } | Stop-Process -Force -ErrorAction SilentlyContinue
Write-Host "  OK  Background processes terminated."

# Step 1: Stop PM2 process
Write-Host "[1/4] Stopping PM2 client process..."
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

# Step 2: Remove Scheduled Task
Write-Host ""
Write-Host "[2/4] Removing auto-start task..."
try {
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction Stop
    Write-Host "  OK  Scheduled task '$taskName' removed."
} catch {
    Write-Host "  SKIP Task not found or already removed."
}

# Step 3: Remove config (revokes identity)
Write-Host ""
Write-Host "[3/4] Removing client configuration..."
$configFile = Join-Path $deployDir "unit_client_config.json"
if (Test-Path $configFile) {
    Remove-Item $configFile -Force
    Write-Host "  OK  Config file deleted."
} else {
    Write-Host "  SKIP Config file not found."
}

# Step 4: Optional - delete all files
Write-Host ""
Write-Host "[4/4] Remove all Sys_Logger files?"
$choice = Read-Host "  Delete '$deployDir' completely? (y/N)"
if ($choice -eq 'y' -or $choice -eq 'Y') {
    Set-Location $env:USERPROFILE  # Move away from the folder before deleting
    Remove-Item $deployDir -Recurse -Force
    Write-Host "  OK  All files deleted."
} else {
    Write-Host "  SKIP File deletion skipped. You can manually delete: $deployDir"
}

Write-Host ""
Write-Host "======================================"
Write-Host "  Uninstall Complete!                 "
Write-Host "======================================"
Write-Host ""
Write-Host "  The Sys_Logger monitoring agent has been completely removed."
Write-Host "  It will no longer appear in logs or run on boot."
Write-Host ""
