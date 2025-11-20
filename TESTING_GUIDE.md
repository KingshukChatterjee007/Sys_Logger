# Sys_Logger Installation Testing Guide

## Prerequisites
- Windows 10/11 system
- Administrator privileges
- At least 5GB free disk space
- Internet connection for downloading dependencies

## Test Environment Setup
Create a test directory structure:
```
C:\SysLogger_Test\
├── Server_Test\
└── Client_Test_1\
```

## Testing Steps

### 1. Server Installer Test

**Location**: `dist/SysLogger_Server_Installer.exe`

**Steps**:
1. Run `SysLogger_Server_Installer.exe` as Administrator
2. Follow the installation wizard:
   - Welcome → Next
   - Installation Path: `C:\SysLogger_Test\Server_Test`
   - Database: Choose "SQLite (Simple)"
   - Client Executables: Set count to "2"
   - Client Names (one per line):
     ```
     Test_PC_1
     Test_PC_2
     ```
   - Server Port: `5001` (to avoid conflicts)
   - Domain: "No - Local access only"
   - Optional: Leave GitHub token empty
   - Service: Check "Install as Windows service"
3. Click "Install" and wait for completion
4. Check the installation directory for generated files

**Expected Results**:
- Server installed in `C:\SysLogger_Test\Server_Test`
- Windows service "SysLoggerServer" created
- Client executables generated in `C:\SysLogger_Test\Server_Test\clients\`
- Desktop shortcut for uninstaller created

### 2. Client Executable Test

**Location**: Generated in server installation `clients/` folder

**Steps**:
1. Locate the generated client executables:
   - `C:\SysLogger_Test\Server_Test\clients\SysLogger_Client_Test_PC_1.exe`
   - `C:\SysLogger_Client_Test_PC_2.exe`

2. Test Client 1 Installation:
   - Run `SysLogger_Client_Test_PC_1.exe`
   - Installation should complete automatically
   - Check installation in default location: `C:\Program Files\UnitClient`
   - Verify config file: `C:\Program Files\UnitClient\unit_client_config.json`
   - Verify system name is "Test_PC_1"

3. Test Client 2 Installation:
   - Run `SysLogger_Client_Test_PC_2.exe`
   - Installation should complete automatically
   - Verify system name is "Test_PC_2"

**Expected Results**:
- Clients install silently with pre-configured settings
- No user interaction required except running the .exe
- Services created and started automatically
- Config files contain correct server URL (`http://localhost:5001`) and system names

### 3. Functional Testing

**Server Test**:
1. Check Windows Services (services.msc) - SysLoggerServer should be running
2. Open browser to `http://localhost:5001` - should show web dashboard
3. Check server logs in installation directory

**Client Test**:
1. Check Windows Services - unit_client service should be running
2. Monitor server dashboard for client connections
3. Check client logs in `C:\Program Files\UnitClient\logs\`

### 4. Manual Client Creation Test

**Purpose**: Test the server's ability to generate additional clients

**Steps**:
1. Create a new client executable from the server (conceptual test):
   - The server installer creates clients during installation
   - In production, server operators can request new client executables

### 5. Cleanup Test

**Steps**:
1. Use desktop shortcut "Uninstall Sys_Logger Server"
2. Confirm server uninstallation
3. Manually uninstall client services if needed
4. Verify all files removed

## Troubleshooting

### Common Issues:
- **Permission Denied**: Run as Administrator
- **Port Conflicts**: Change server port in configuration
- **Service Creation Failed**: Check Windows Event Viewer
- **PyInstaller Errors**: Ensure all dependencies are available

### Logs to Check:
- Server logs: `C:\SysLogger_Test\Server_Test\logs\`
- Client logs: `C:\Program Files\UnitClient\logs\`
- Windows Event Viewer: System and Application logs

## Verification Checklist

- [ ] Server installer runs without errors
- [ ] Server service installs and starts
- [ ] Web dashboard accessible at configured port
- [ ] Client executables generated with correct names
- [ ] Client executables install silently
- [ ] Client services install and start
- [ ] Clients connect to server automatically
- [ ] System names appear correctly in dashboard
- [ ] Uninstallation removes all components

## Quick Test Commands

```batch
# Test server startup
sc query SysLoggerServer

# Test client service
sc query unit_client

# Check server port
netstat -ano | findstr :5001

# View server logs
type "C:\SysLogger_Test\Server_Test\logs\server.log"