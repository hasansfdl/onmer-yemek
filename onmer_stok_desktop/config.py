"""Uygulama yolları — exe güncellemelerinde veriler korunur."""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

APP_NAME = "Onmer Stok & Finans"
APP_DATA_FOLDER = "OnmerStokFinans"


def app_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def _legacy_data_dir() -> Path:
    """Eski sürümlerde veritabanının tutulduğu klasör (exe yanında)."""
    return app_root() / "data"


def user_data_dir() -> Path:
    """Kalıcı veri klasörü — derleme/güncelleme sırasında silinmez."""
    if getattr(sys, "frozen", False):
        local = os.environ.get("LOCALAPPDATA")
        if local:
            return Path(local) / APP_DATA_FOLDER
        return Path.home() / APP_DATA_FOLDER
    return app_root() / "data"


DATA_DIR = user_data_dir()
DB_PATH = DATA_DIR / "onmer_stok.db"

ASSETS_DIR = Path(__file__).resolve().parent / "assets"


def migrate_legacy_database() -> None:
    """Eski exe yanındaki veritabanını kalıcı klasöre taşır (bir kez)."""
    if DB_PATH.is_file():
        return

    legacy_db = _legacy_data_dir() / "onmer_stok.db"
    if not legacy_db.is_file():
        return

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(legacy_db, DB_PATH)


def database_location_hint() -> str:
    if getattr(sys, "frozen", False):
        return str(DB_PATH)
    return str(DB_PATH.relative_to(app_root()))


def _resolve_logo() -> Path:
    for path in (
        ASSETS_DIR / "onmer-logo-transparent.png",
        app_root() / "onmer_stok_desktop" / "assets" / "onmer-logo-transparent.png",
        app_root() / "static" / "images" / "onmer-logo-transparent.png",
    ):
        if path.is_file():
            return path
    return ASSETS_DIR / "onmer-logo-transparent.png"


LOGO_PATH = _resolve_logo()
