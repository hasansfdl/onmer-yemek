"""Uygulama sabitleri ve Django proje kök yolu."""

from __future__ import annotations

import sys
from pathlib import Path


def _resolve_project_root() -> Path:
    """
    Geliştirme: bu dosyanın iki üstü = repo kökü.
    PyInstaller (.exe): proje dosyaları yürütülebilir ile aynı klasörde olmalı (manage.py, onmer/, …).
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


PROJECT_ROOT: Path = _resolve_project_root()
SETTINGS_MODULE: str = "onmer.settings"
APP_TITLE: str = "Onmer Admin Panel"
APP_VERSION: str = "1.0.0"

# Login sonrası hatırlanan son kullanıcı (isteğe bağlı genişletme için)
ORG_NAME: str = "Onmer Yemek Organizasyon"

# Web sitesi navbar / footer ile aynı logo
# (`templates/partials/_navbar.html` → `static/images/onmer-logo-transparent.png`)
BRAND_LOGO_PATH: Path = PROJECT_ROOT / "static" / "images" / "onmer-logo-transparent.png"
