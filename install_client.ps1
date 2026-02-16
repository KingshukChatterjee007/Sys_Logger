# Sys_Logger Client Installation Script

# 1. Check for Python
if (!(Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: Python is not installed or not in PATH." -ForegroundColor Red
    Write-Host "Please install Python 3.10+ from python.org"
    exit
}

# 2. Install dependencies
Write-Host "Installing dependencies..." -ForegroundColor Cyan
python -m pip install -r requirements_client.txt

# 3. Install Background Service
Write-Host "Registering background service..." -ForegroundColor Cyan
python unit_client.py --install-service

Write-Host "`n✓ Client installation complete!" -ForegroundColor Green
Write-Host "The client will now run automatically on startup."
Write-Host "You can manually start it now using: python unit_client.py"
