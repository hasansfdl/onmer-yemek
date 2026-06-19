"""Yeniden başlatmada giriş penceresini atlamak için tek kullanımlık imzalı jeton."""

from __future__ import annotations

import hashlib
import hmac
import json
import tempfile
import time
from pathlib import Path

from django.contrib.auth.models import User

from onmer_admin_desktop.database import ensure_django

_TOKEN_NAME = "onmer_admin_relaunch.session"
_TOKEN_TTL_SEC = 120


def _token_path() -> Path:
    return Path(tempfile.gettempdir()) / _TOKEN_NAME


def write_relaunch_token(user_pk: int) -> None:
    """Yeni süreç `consume_relaunch_user` ile aynı kullanıcıyla açılabilsin."""
    ensure_django()
    from django.conf import settings

    exp = int(time.time()) + _TOKEN_TTL_SEC
    msg = f"{user_pk}|{exp}".encode("utf-8")
    key = settings.SECRET_KEY.encode("utf-8")
    sig = hmac.new(key, msg, hashlib.sha256).hexdigest()
    payload = {"user_pk": user_pk, "exp": exp, "sig": sig}
    _token_path().write_text(json.dumps(payload), encoding="utf-8")


def consume_relaunch_user() -> User | None:
    """
    Geçerli jeton varsa dosyayı siler ve kullanıcıyı döndürür; yoksa None.
    `ensure_django()` çağrılmış olmalıdır.
    """
    path = _token_path()
    if not path.is_file():
        return None

    raw: str | None = None
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError:
        pass
    try:
        path.unlink(missing_ok=True)
    except OSError:
        pass
    if raw is None:
        return None

    from django.conf import settings

    try:
        data = json.loads(raw)
        user_pk = int(data["user_pk"])
        exp = int(data["exp"])
        sig = str(data["sig"])
    except (KeyError, TypeError, ValueError, json.JSONDecodeError):
        return None

    if int(time.time()) > exp:
        return None

    msg = f"{user_pk}|{exp}".encode("utf-8")
    key = settings.SECRET_KEY.encode("utf-8")
    expected = hmac.new(key, msg, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, sig):
        return None

    try:
        u = User.objects.get(pk=user_pk, is_active=True)
    except User.DoesNotExist:
        return None
    if not (u.is_staff or u.is_superuser):
        return None
    return u
