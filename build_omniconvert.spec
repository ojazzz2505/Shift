# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['src/ui/main_window.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('src/assets', 'src/assets'), 
        # ('bin', 'bin') # Do NOT bundle bin/ffmpeg.exe to comply with LGPL strict mode if you want to be extra safe
        # actually user said "must check for external ffmpeg in ./bin". 
        # So we expect ./bin to be ALONGSIDE the exe, not inside it (one-file mode unpacks to temp).
        # So we don't bundle it.
    ],
    hiddenimports=['PIL._tkinter_finder', 'customtkinter', 'tkinterdnd2', 'magic', 'fitz'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    name='OmniConvert',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False, # Windowed mode
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='OmniConvert',
)
