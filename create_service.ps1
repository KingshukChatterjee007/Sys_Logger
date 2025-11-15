param(
    [string]$ServiceName = "SysLoggerService",
    [string]$ServicePath = "C:\Usage_Logs\sys_logger.exe"
)

# Check if running as administrator
$currentPrincipal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
if (-not $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "Please run this script as Administrator to create Windows services."
    exit 1
}

# Check if service already exists
$existingService = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
if ($existingService) {
    Write-Host "Service '$ServiceName' already exists. Removing it first..."
    Stop-Service -Name $ServiceName -ErrorAction SilentlyContinue
    sc.exe delete $ServiceName
    Start-Sleep -Seconds 5
}

# Create the service
Write-Host "Creating service '$ServiceName'..."
$result = sc.exe create $ServiceName binPath= "$ServicePath" start= auto DisplayName= "System Logger Service"
if ($LASTEXITCODE -eq 0) {
    Write-Host "Service created successfully."

    # Start the service
    Write-Host "Starting service..."
    Start-Service -Name $ServiceName

    if ((Get-Service -Name $ServiceName).Status -eq "Running") {
        Write-Host "Service started successfully."
    } else {
        Write-Host "Service created but failed to start. Check the service logs."
    }
} else {
    Write-Host "Failed to create service. Error code: $LASTEXITCODE"
}