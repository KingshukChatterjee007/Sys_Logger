# =====================================
# Sys_Logger Client - Windows Setup Script
# Run this ONCE to set up your background deployment
# =====================================

Write-Host "🚀 Sys_Logger Client - Windows Setup" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""

<<<<<<< HEAD
# 1. Setup Python Environment
Write-Host "🐍 Step 1: Setting up Python..." -ForegroundColor Yellow
if (!(Test-Path "venv\Scripts\python.exe")) {
    Write-Host "Creating virtual environment..."
    python -m venv venv
=======
# 0. Set working directory to script location
Set-Location $PSScriptRoot

# Reset PM2 daemon to fix "EPERM //.pipe/rpc.sock" errors
Write-Host "Resetting PM2 daemon..." -ForegroundColor Gray
pm2 kill 2>$null

# 1. Check/Install PM2
Write-Host "Step 1: Checking Environment..." -ForegroundColor Yellow
if (!(Get-Command node -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: Node.js not found. Please install from https://nodejs.org" -ForegroundColor Red
    exit
}

if (!(Get-Command pm2 -ErrorAction SilentlyContinue)) {
    Write-Host "Installing PM2..."
    npm install -g pm2
} else {
    Write-Host "PM2 installed" -ForegroundColor Green
}

# 2. Setup Python Environment
Write-Host "Step 2: Setting up Python..." -ForegroundColor Yellow
# Force recreate venv to fix "Fatal error in launcher" issues
if (Test-Path "venv") {
    Write-Host "Removing existing virtual environment to fix path issues..." -ForegroundColor Gray
    Remove-Item -Path "venv" -Recurse -Force -ErrorAction SilentlyContinue
>>>>>>> 94571205259c2bf6c077a807c402a192098f910c
}

<<<<<<< HEAD
# 2. Configure & Install Service (Task Scheduler)
Write-Host "🚀 Step 2: Installing Background Service..." -ForegroundColor Yellow

# Use the python executable from the venv to run the install command
& "venv\Scripts\python.exe" unit_client.py --install-service

Write-Host ""
Write-Host "✅ Setup Complete! Client is scheduled to run at startup." -ForegroundColor Green
Write-Host "It has also been started immediately." -ForegroundColor Green
=======
Write-Host "Creating virtual environment..."
python -m venv venv

Write-Host "Installing dependencies..."
& "venv\Scripts\python.exe" -m pip install --upgrade pip
& "venv\Scripts\python.exe" -m pip install -r requirements.txt

# 3. Interactive Configuration
Write-Host "Step 3: Configuration..." -ForegroundColor Yellow
$configPath = Join-Path $PSScriptRoot "unit_client_config.json"
Write-Host "Config file will be saved to: $configPath" -ForegroundColor Gray

$currentConfig = if (Test-Path $configPath) { Get-Content $configPath | ConvertFrom-Json } else { @{} }

# Server URL is hardcoded as per user request
$serverUrl = "http://203.193.145.59:5010"

$currentOrg = if ($currentConfig.org_id) { $currentConfig.org_id } else { "default_org" }
$orgId = Read-Host "Enter Organization ID (Press Enter to keep '$currentOrg')"
if ([string]::IsNullOrWhiteSpace($orgId)) { $orgId = $currentOrg }

$currentComp = if ($currentConfig.comp_id) { $currentConfig.comp_id } else { $env:COMPUTERNAME }
$compId = Read-Host "Enter Computer ID (Press Enter to keep '$currentComp')"
if ([string]::IsNullOrWhiteSpace($compId)) { $compId = $currentComp }

$newConfig = @{
    system_id = if ($currentConfig.system_id) { $currentConfig.system_id } else { [guid]::NewGuid().ToString() }
    server_url = $serverUrl
    org_id = $orgId
    comp_id = $compId
}

$json = $newConfig | ConvertTo-Json
[System.IO.File]::WriteAllText($configPath, $json)
Write-Host "Configuration saved." -ForegroundColor Green

# 4. Configure & Start
Write-Host "Step 4: Starting Service..." -ForegroundColor Yellow
pm2 delete sys-logger-client 2>$null
pm2 start ecosystem.config.js --interpreter venv\Scripts\python.exe

pm2 save
pm2 save

Write-Host "Configuring Auto-Startup..." -ForegroundColor Yellow
# Install pm2-windows-startup to handle boot persistence
try {
    if (!(Get-Command pm2-startup -ErrorAction SilentlyContinue)) {
        Write-Host "Installing pm2-windows-startup..."
        npm install -g pm2-windows-startup
    }
    
    # Install the registry entry (Safe to run multiple times)
    Write-Host "Registering Startup Service..."
    pm2-startup install
    pm2 save
    Write-Host "Auto-Startup Configured Successfully!" -ForegroundColor Green
} catch {
    Write-Host "Warning: Failed to configure auto-startup. You may need to run this script as Administrator." -ForegroundColor Red
}

Write-Host ""
Write-Host "Setup Complete! Client is running in background." -ForegroundColor Green
Write-Host "To monitor type: pm2 monit"
Write-Host "To see logs type: pm2 logs sys-logger-client"
>>>>>>> 94571205259c2bf6c077a807c402a192098f910c
