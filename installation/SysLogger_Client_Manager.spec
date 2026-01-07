# -*- mode: python ; coding: utf-8 -*-

import sys
import os
from pathlib import Path

# Paths
spec_dir = os.path.dirname(os.path.abspath(SPEC))
project_root = Path(spec_dir).parent
client_manager = Path(spec_dir) / 'client_manager.py'

a = Analysis(
    [str(client_manager)],
    pathex=[str(project_root), str(spec_dir)],
    binaries=[],
    datas=[
        (str(project_root / 'unit_client.py'), '.'),
        (str(project_root / 'unit_client_config.json'), '.'),
        (str(spec_dir / 'SysLogger_Client_Installer.spec'), '.'),
        (str(spec_dir / 'client_installer.py'), '.'),
    ],
    hiddenimports=[
        "tkinter",
        "tkinter.ttk",
        "tkinter.messagebox",
        "tkinter.scrolledtext",
        "tkinter.simpledialog",
        "threading",
        "time",
        "json",
        "requests",
        "socket",
        "datetime",
        "webbrowser",
        "pathlib",
        "typing",
        "logging",
        "uuid",
        "platform",
        "subprocess",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
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
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='SysLogger_Client_Manager',
    debug=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)