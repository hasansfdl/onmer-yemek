"""Django ORM başlatma ve güvenli veritabanı yardımcıları.

Masaüstü uygulaması, web sitesiyle aynı SQLite dosyasını (`db.sqlite3`)
Django ORM üzerinden kullanır; şema uyumu korunur.
"""

from __future__ import annotations

import os
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Callable, TypeVar

from django.db import connection, transaction

from onmer_admin_desktop import config

T = TypeVar("T")

_django_ready: bool = False


def ensure_django() -> None:
    """Sys.path ve Django ayarlarını bir kez yükle."""
    global _django_ready
    if _django_ready:
        return

    root = str(config.PROJECT_ROOT.resolve())
    if root not in sys.path:
        sys.path.insert(0, root)

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", config.SETTINGS_MODULE)

    import django

    django.setup()
    _django_ready = True


def db_path() -> Path:
    """Aktif SQLite dosyası (settings’te tanımlı)."""
    ensure_django()
    from django.conf import settings

    name = settings.DATABASES["default"]["NAME"]
    return Path(name)


@contextmanager
def db_transaction():
    """Atomik yazma işlemleri için."""
    ensure_django()
    with transaction.atomic():
        yield


def run_with_db(fn: Callable[[], T]) -> T:
    """Yardımcı: Django kurulduktan sonra fonksiyon çalıştır."""
    ensure_django()
    return fn()


def check_connection() -> bool:
    """Veritabanına basit bağlantı testi."""
    try:
        ensure_django()
        connection.ensure_connection()
        return True
    except Exception:
        return False
