# Sys_Logger Server Installer - Build Instructions

## Prerequisites

1. **Python 3.8+** installed
2. **PyInstaller** installed: `pip install pyinstaller`
3. **All required dependencies** installed (see requirements.txt)
4. **Windows OS** (for building Windows executables)

## Building the Installer

### Option 1: Using Python Script (Recommended)

```bash
cd installation
python build_installer.py
```

### Option 2: Using Batch File

```bash
cd installation
build_installer.bat
```

### Option 3: Manual PyInstaller Command

```bash
cd installation
pyinstaller SysLogger_Server_Installer.spec
```

## Output

The build process will create:
- `dist/SysLogger_Server_Installer.exe` - The main installer executable
- `dist/` directory containing all bundled files

## Files Included in the Installer

The executable bundles:
- Server installer GUI (`server_installer.py`)
- Server management application (`server_manager.py`)
- All backend files (Flask server, etc.)
- Frontend React application
- Client files (unit_client.py, service files, etc.)
- Database schema and documentation
- Setup and utility scripts

## Distribution

The `SysLogger_Server_Installer.exe` file in the `dist/` folder is ready for distribution. Users can run it directly without needing Python installed on their systems.

## Troubleshooting

1. **PyInstaller not found**: Install with `pip install pyinstaller`
2. **Missing dependencies**: Ensure all packages in requirements.txt are installed
3. **Build fails**: Check that all source files exist in the expected locations
4. **Large file size**: The executable includes all dependencies - this is normal for standalone apps

## Icon

If you have an `installer_icon.ico` file in the installation directory, it will be used as the executable icon. Otherwise, a default icon will be used.