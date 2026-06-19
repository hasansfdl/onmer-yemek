# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec — Onmer Admin Panel (PyQt6 + Django ORM).

Derleme sonrası packaging/build_windows.ps1 proje dosyalarını dist klasörüne kopyalar.
"""
from __future__ import annotations

import pathlib

block_cipher = None

# SPECPATH = spec dosyasının bulunduğu klasör (PyInstaller 6); gerekiyorsa dosya yolu da gelebilir.
_spec_ref = pathlib.Path(SPECPATH).resolve()
_spec_dir = _spec_ref.parent if _spec_ref.suffix.lower() == ".spec" else _spec_ref
ROOT = _spec_dir.parent

from PyInstaller.utils.hooks import collect_all, collect_submodules

datas: list = []
binaries: list = []
hiddenimports: list = []

for pkg in (
    "django",
    "PyQt6",
    "widget_tweaks",
    "tzdata",
):
    try:
        d, b, h = collect_all(pkg)
        datas += d
        binaries += b
        hiddenimports += h
    except Exception:
        pass

# PostgreSQL istemcisi (kurulu değilse atlanır)
for pkg in ("psycopg",):
    try:
        d, b, h = collect_all(pkg)
        datas += d
        binaries += b
        hiddenimports += h
    except Exception:
        pass

# Pillow — ImageField
try:
    d, b, h = collect_all("PIL")
    datas += d
    binaries += b
    hiddenimports += h
except Exception:
    pass

for app in (
    "onmer",
    "core",
    "accounts",
    "menu",
    "orders",
    "reservations",
    "portfolio",
    "inventory",
):
    try:
        hiddenimports += collect_submodules(app)
    except Exception:
        pass

hiddenimports = sorted(set(hiddenimports))

a = Analysis(
    [str(ROOT / "onmer_admin_desktop" / "main.py")],
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
    name="OnmerAdminPanel",
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
    name="OnmerAdminPanel",
)
