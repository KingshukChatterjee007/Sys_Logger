# PowerShell script to create and install Unit Client as a Windows service
# Run this script as Administrator

param(
    [string]$ServiceName = "UnitClientService",
    [string]$DisplayName = "Sys_Logger Unit Client",
    [string]$Description = "Lightweight agent for collecting and reporting system usage data",
    [string]$PythonPath = "python",  # Change if python is not in PATH
    [string]$ScriptPath = $PSScriptRoot + "\unit_client.py"
)

# Check if running as administrator
if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "Please run this script as Administrator" -ForegroundColor Red
    exit 1
}

# Check if the script file exists
if (-not (Test-Path $ScriptPath)) {
    Write-Host "unit_client.py not found at $ScriptPath" -ForegroundColor Red
    exit 1
}

# Check if Python is available
try {
    & $PythonPath --version | Out-Null
} catch {
    Write-Host "Python not found at $PythonPath. Please specify correct Python path." -ForegroundColor Red
    exit 1
}

# Check if NSSM is available (we'll use it to create the service)
$NSSMPath = "$PSScriptRoot\nssm.exe"

if (-not (Test-Path $NSSMPath)) {
    Write-Host "NSSM not found. Downloading NSSM..." -ForegroundColor Yellow

    # Download NSSM
    $nssmUrl = "https://nssm.cc/release/nssm-2.24.zip"
    $nssmZip = "$PSScriptRoot\nssm.zip"
    $nssmExtractPath = "$PSScriptRoot\nssm-temp"

    try {
        Invoke-WebRequest -Uri $nssmUrl -OutFile $nssmZip
        Expand-Archive -Path $nssmZip -DestinationPath $nssmExtractPath

        # Copy the appropriate NSSM executable
        if ([Environment]::Is64BitOperatingSystem) {
            Copy-Item "$nssmExtractPath\nssm-2.24\win64\nssm.exe" $NSSMPath
        } else {
            Copy-Item "$nssmExtractPath\nssm-2.24\win32\nssm.exe" $NSSMPath
        }

        # Clean up
        Remove-Item $nssmZip -Force
        Remove-Item $nssmExtractPath -Recurse -Force

    } catch {
        Write-Host "Failed to download NSSM. Please download it manually from https://nssm.cc/" -ForegroundColor Red
        exit 1
    }
}

# Stop and remove existing service if it exists
$existingService = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
if ($existingService) {
    Write-Host "Stopping existing service..." -ForegroundColor Yellow
    Stop-Service -Name $ServiceName -Force -ErrorAction SilentlyContinue
    & $NSSMPath remove $ServiceName confirm
}

# Create the service
Write-Host "Creating Windows service '$ServiceName'..." -ForegroundColor Green

# Set the service parameters
& $NSSMPath install $ServiceName $PythonPath $ScriptPath --start

# Set service description
& $NSSMPath set $ServiceName Description $Description

# Set service display name
& $NSSMPath set $ServiceName DisplayName $DisplayName

# Set startup type to automatic
& $NSSMPath set $ServiceName Start SERVICE_AUTO_START

# Set restart options (restart on failure)
& $NSSMPath set $ServiceName AppExit Default Restart
& $NSSMPath set $ServiceName AppRestartDelay 5000

# Set restart count and reset time
& $NSSMPath set $ServiceName AppThrottle 60000
& $NSSMPath set $ServiceName AppStdout $PSScriptRoot\log.txt
& $NSSMPath set $ServiceName AppStderr $PSScriptRoot\error.log

# Optional: Set working directory
& $NSSMPath set $ServiceName AppDirectory $PSScriptRoot

# Start the service
Write-Host "Starting service..." -ForegroundColor Green
Start-Service -Name $ServiceName

# Verify service status
$service = Get-Service -Name $ServiceName
if ($service.Status -eq "Running") {
    Write-Host "Service '$ServiceName' created and started successfully!" -ForegroundColor Green
    Write-Host "Service details:" -ForegroundColor Cyan
    Write-Host "  Name: $ServiceName"
    Write-Host "  Display Name: $DisplayName"
    Write-Host "  Status: $($service.Status)"
    Write-Host "  Python Path: $PythonPath"
    Write-Host "  Script Path: $ScriptPath"
} else {
    Write-Host "Service created but failed to start. Status: $($service.Status)" -ForegroundColor Yellow
    Write-Host "Check the service logs for more information." -ForegroundColor Yellow
}

Write-Host "`nTo manage the service:" -ForegroundColor Cyan
Write-Host "  Start:  Start-Service -Name $ServiceName"
Write-Host "  Stop:   Stop-Service -Name $ServiceName"
Write-Host "  Status: Get-Service -Name $ServiceName"
Write-Host "  Remove: & '$NSSMPath' remove $ServiceName"

Write-Host "`nNote: The service will automatically restart on system boot and on crashes." -ForegroundColor Cyan