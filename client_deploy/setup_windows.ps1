# =====================================
# Sys_Logger Client - Windows Setup Script
# Run this ONCE to set up your background deployment
# =====================================

Write-Host "🚀 Sys_Logger Client - Windows Setup" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""

# 1. Check/Install PM2
Write-Host "📦 Step 1: Checking Environment..." -ForegroundColor Yellow
if (!(Get-Command node -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Node.js not found. Please install from https://nodejs.org" -ForegroundColor Red
    exit
}

if (!(Get-Command pm2 -ErrorAction SilentlyContinue)) {
    Write-Host "📥 Installing PM2..."
    npm install -g pm2
} else {
    Write-Host "✅ PM2 installed" -ForegroundColor Green
}

# 2. Setup Python Environment
Write-Host "🐍 Step 2: Setting up Python..." -ForegroundColor Yellow
if (!(Test-Path "venv\Scripts\python.exe")) {
    Write-Host "Creating virtual environment..."
    python -m venv venv
}
Write-Host "Installing dependencies..."
& "venv\Scripts\activate.ps1"
pip install -r requirements.txt

# 3. Configure & Start
Write-Host "🚀 Step 3: Starting Service..." -ForegroundColor Yellow
pm2 delete sys-logger-client 2>$null
pm2 start ecosystem.config.js --interpreter venv\Scripts\python.exe

pm2 save
pm2 startup

Write-Host ""
Write-Host "✅ Setup Complete! Client is running in background." -ForegroundColor Green
Write-Host "To monitor: pm2 monit" -ForegroundColor Cyan
Write-Host "To logs: pm2 logs sys-logger-client" -ForegroundColor Cyan
