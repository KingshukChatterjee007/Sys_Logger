# =====================================
# Sys_Logger Client - Windows Setup Script
# Run this ONCE to set up your background deployment
# =====================================

Write-Host "🚀 Sys_Logger Client - Windows Setup" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""

# 1. Setup Python Environment
Write-Host "🐍 Step 1: Setting up Python..." -ForegroundColor Yellow
if (!(Test-Path "venv\Scripts\python.exe")) {
    Write-Host "Creating virtual environment..."
    python -m venv venv
}

# 2. Configure & Install Service (Task Scheduler)
Write-Host "🚀 Step 2: Installing Background Service..." -ForegroundColor Yellow

# Use the python executable from the venv to run the install command
& "venv\Scripts\python.exe" unit_client.py --install-service

Write-Host ""
Write-Host "✅ Setup Complete! Client is scheduled to run at startup." -ForegroundColor Green
Write-Host "It has also been started immediately." -ForegroundColor Green
