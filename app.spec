# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import copy_metadata, collect_all

datas = [('Bak.xlsx', '.'), ('Mag_1_.xlsx', '.'), ('app.py', '.')]
binaries = []
hiddenimports = []

packages_needing_metadata = [
    'streamlit', 'pandas', 'numpy', 'plotly', 'altair', 'pydeck',
    'jinja2', 'markupsafe', 'pillow', 'packaging', 'openpyxl',
    'click', 'tornado', 'toml', 'validators', 'watchdog',
    'gitpython', 'pyarrow', 'protobuf', 'tenacity', 'rich',
    'blinker', 'cachetools',
]

for pkg in packages_needing_metadata:
    try:
        datas += copy_metadata(pkg)
    except Exception as e:
        print(f"Skip metadata for {pkg}: {e}")

tmp_ret = collect_all('streamlit')
datas += tmp_ret[0]
binaries += tmp_ret[1]
hiddenimports += tmp_ret[2]

a = Analysis(
    ['run_app.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
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
    name='app',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='app.ico',
)