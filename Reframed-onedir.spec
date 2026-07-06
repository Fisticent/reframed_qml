# -*- mode: python ; coding: utf-8 -*-
# Build dossier dist/Reframed/ — démarrage nettement plus rapide que le onefile.

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('./logo.ico', '.'),
        ('./logo_transparent.png', '.'),
        ('./skin', 'skin'),
        ('./icons', 'icons'),
        ('./sounds', 'sounds'),
        ('./theme', 'theme'),
        ('./qml', 'qml'),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'PySide6.QtWebEngineCore', 'PySide6.QtWebEngineWidgets',
        'PySide6.Qt3DCore', 'PySide6.QtCharts', 'PySide6.QtDataVisualization',
        'PySide6.QtMultimedia', 'PySide6.QtPdf', 'PySide6.QtSql',
        'tkinter', 'customtkinter', 'PIL',
    ],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Reframed',
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
    icon=['logo.ico'],
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='Reframed',
)
