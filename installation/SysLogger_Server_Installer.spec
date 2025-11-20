# -*- mode: python ; coding: utf-8 -*-

import sys
import os
from pathlib import Path

# Resolve directories
spec_dir = os.path.dirname(os.path.abspath(SPEC))
project_root = Path(spec_dir).parent
installer_file = project_root / "installation" / "server_installer.py"

a = Analysis(
    [str(installer_file)],
    pathex=[str(project_root), str(spec_dir)],
    binaries=[],

    datas=[
        # Include database schema if present
        (str(project_root / "database_schema.sql"), "."),
        (str(project_root / "server_setup.py"), ".") 
            if (project_root / "server_setup.py").exists() else (),
    ],

    hiddenimports=[
        "tkinter",
        "tkinter.ttk",
        "tkinter.messagebox",

        "psutil",
        "requests",
        "GPUtil",

        "uuid",
        "json",
        "socket",
        "platform",
        "subprocess",
        "threading",
        "time",
        "logging",
        "pathlib",
        "typing",
        "datetime",
        "signal",

        # psycopg2 binary distribution
        "psycopg2",
        "psycopg2.extensions",
        "psycopg2.extras",
    ],

    # No Qt, no PyQt, no PySide
    excludes=[
        "PyQt6",
        "PyQt6.QtWidgets",
        "PyQt6.QtCore",
        "PyQt6.QtGui",
        "PySide6",
        "PyQt5",
        "qtpy",
        "sip",
    ],

    runtime_hooks=[],
    hookspath=[],
    hooksconfig={},

    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="SysLogger_Server_Installer",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
)
