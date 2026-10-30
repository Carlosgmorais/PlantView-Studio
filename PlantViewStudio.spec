# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path
import sys

block_cipher = None

ROOT = Path.cwd()

datas = [
    (str(ROOT / 'engine' / 'plantview-dwg.exe'), 'engine'),
    (str(ROOT / 'examples'), 'examples'),
    (str(ROOT / 'resources'), 'resources'),
]

hiddenimports = [
    'pyvistaqt',
    'pyvista',
    'vtk',
    'vtkmodules',
    'vtkmodules.all',
    'vtkmodules.vtkRenderingOpenGL2',
    'vtkmodules.vtkInteractionStyle',
    'vtkmodules.vtkRenderingFreeType',
    'PySide6',
    'PySide6.QtCore',
    'PySide6.QtGui',
    'PySide6.QtWidgets',
    'ifcopenshell',
    'ezdxf',
    'unittest',
]

a = Analysis(
    ['run.py'],
    pathex=[str(ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='PlantView Studio',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(ROOT / 'resources' / 'plantview.ico'),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='PlantView Studio',
)

