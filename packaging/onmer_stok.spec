# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec — Onmer Stok & Finans (PyQt6 + SQLite)."""

from pathlib import Path

block_cipher = None
_spec_dir = Path(SPECPATH).resolve().parent if Path(SPECPATH).suffix.lower() == ".spec" else Path(SPECPATH).resolve()
ROOT = _spec_dir.parent

from PyInstaller.utils.hooks import collect_all

datas = []
binaries = []
hiddenimports = []

for pkg in ("PyQt6", "PyQt6-Charts"):
    try:
        d, b, h = collect_all(pkg)
        datas += d
        binaries += b
        hiddenimports += h
    except Exception:
        pass

assets = ROOT / "onmer_stok_desktop" / "assets"
if assets.is_dir():
    datas.append((str(assets), "onmer_stok_desktop/assets"))

a = Analysis(
    [str(ROOT / "onmer_stok_desktop" / "main.py")],
    pathex=[str(ROOT)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
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
    name="OnmerStokFinans",
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
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="OnmerStokFinans",
)
