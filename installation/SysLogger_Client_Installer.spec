# -*- mode: python ; coding: utf-8 -*-

import sys
import os
from pathlib import Path

# Paths
spec_dir = os.path.dirname(os.path.abspath(SPEC))
project_root = Path(spec_dir).parent
client_installer = Path(spec_dir) / 'client_installer.py'

a = Analysis(
    [str(client_installer)],
    pathex=[str(project_root), str(spec_dir)],
    binaries=[],

    datas=[
        (str(project_root / 'unit_client.py'), '.'),
        (str(project_root / 'client_watchdog.sh'), '.')
            if (project_root / 'client_watchdog.sh').exists() else (),
        (str(project_root / 'domain_updater.py'), '.')
            if (project_root / 'domain_updater.py').exists() else (),
        (str(project_root / 'README.txt'), '.')
            if (project_root / 'README.txt').exists() else (),
    ],

    # NO PyQt6 imports because GUI is now Tkinter
    hiddenimports=[
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
        "tkinter",
        "tkinter.ttk",
        "tkinter.messagebox",
    ],

    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "PyQt6",
        "PySide6",
        "qtpy",
        "sip",
        "PyQt5",
        "matplotlib",  # Exclude matplotlib if not needed
        "numpy",  # Exclude numpy if not needed
        "pandas",  # Exclude pandas if not needed
        "scipy",  # Exclude scipy if not needed
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
    name='SysLogger_Client_Installer',
    debug=False,
    upx=True,
    console=False,
    icon=None,
)
