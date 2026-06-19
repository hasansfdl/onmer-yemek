"""Proje kökündeki onmer_database.env dosyasını Django başlamadan önce yükler."""

from __future__ import annotations

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent


def _env_file_path() -> Path:
    import sys

    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent / "onmer_database.env"
    return PROJECT_ROOT / "onmer_database.env"


def load_env_file(path: Path | None = None) -> None:
    """PostgreSQL, SQLite ve e-posta ayarlarını ortam değişkenlerine yazar."""
    if path is None:
        path = _env_file_path()
    if not path.is_file():
        return
    try:
        raw = path.read_text(encoding="utf-8-sig")
    except OSError:
        return

    set_keys: list[str] = []
    saw_use_sqlite_key = False
    for line in raw.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        if not key:
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        os.environ[key] = value
        set_keys.append(key)
        if key.upper() == "USE_SQLITE":
            saw_use_sqlite_key = True

    if any(k.upper().startswith("POSTGRES_") for k in set_keys) and not saw_use_sqlite_key:
        os.environ.pop("USE_SQLITE", None)


def bootstrap() -> None:
    load_env_file()
