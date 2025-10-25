# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('template.png', '.'),
        ('begentemplate.png', '.'),
        ('begenmedyatemplate.png', '.'),
        ('begenfilmtemplate.png', '.'),
        ('begentvtemplate.png', '.'),
        ('logo.png', '.'),
        ('BEGEN HABER.png', '.'),
        ('BEGEN MEDYA.png', '.'),
        ('BEGEN FILM.png', '.'),
        ('BEGEN TV.png', '.'),
        ('Montserrat-Bold.ttf', '.'),
        ('Montserrat-Regular.ttf', '.'),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='GorselOlusturucu_Son',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='logo.png'
)
