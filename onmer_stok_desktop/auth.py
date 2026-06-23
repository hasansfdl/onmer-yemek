"""Yerel kullanıcı girişi ve rol yönetimi."""

from __future__ import annotations

import hashlib
import secrets
from typing import Any

from .database import connect, row_to_dict

ROLE_LABELS = {
    "admin": "Admin",
    "stock": "Depo",
    "finance": "Muhasebe",
    "viewer": "İzleyici",
}

ASSIGNABLE_USER_ROLES = {
    key: label for key, label in ROLE_LABELS.items() if key != "viewer"
}

ROLE_TABS = {
    "admin": ["Özet", "Stok", "Gelir / Gider", "Personel", "Faturalar", "Grafikler", "Kullanıcılar"],
    "stock": ["Stok"],
    "finance": ["Özet", "Stok", "Gelir / Gider", "Personel", "Faturalar", "Grafikler"],
    "viewer": ["Özet", "Grafikler", "Faturalar"],
}

DEFAULT_ADMIN_USERNAME = "admin"
DEFAULT_ADMIN_PASSWORD = "onmer1905"


def hash_password(password: str, salt: str | None = None) -> str:
    if salt is None:
        salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), 100_000
    )
    return f"{salt}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        salt, hex_digest = stored.split("$", 1)
    except ValueError:
        return False
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), 100_000
    )
    return secrets.compare_digest(digest.hex(), hex_digest)


def ensure_default_admin() -> None:
    from datetime import datetime

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with connect() as conn:
        count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        if count == 0:
            conn.execute(
                """
                INSERT INTO users (username, password_hash, role, is_active, created_at)
                VALUES (?, ?, 'admin', 1, ?)
                """,
                (
                    DEFAULT_ADMIN_USERNAME,
                    hash_password(DEFAULT_ADMIN_PASSWORD),
                    now,
                ),
            )
            conn.commit()


def verify_login(username: str, password: str) -> dict[str, Any] | None:
    username = username.strip()
    if not username or not password:
        return None
    with connect() as conn:
        row = conn.execute(
            """
            SELECT * FROM users
            WHERE username = ? COLLATE NOCASE AND is_active = 1
            """,
            (username,),
        ).fetchone()
    user = row_to_dict(row)
    if not user or not verify_password(password, user["password_hash"]):
        return None
    return {
        "id": user["id"],
        "username": user["username"],
        "role": user["role"],
        "role_label": ROLE_LABELS.get(user["role"], user["role"]),
    }


def can_access_tab(role: str, tab_name: str) -> bool:
    return tab_name in ROLE_TABS.get(role, [])


def can_manage_users(role: str) -> bool:
    return role == "admin"


def can_edit_data(role: str) -> bool:
    return role in ("admin", "stock", "finance")


def can_edit_finance(role: str) -> bool:
    return role in ("admin", "finance")


def can_edit_stock(role: str) -> bool:
    return role in ("admin", "stock")


def is_stock_add_delete_only(role: str) -> bool:
    """Depo: stok sekmesinde tam düzenleme (giriş, çıkış, düzenleme)."""
    return False


def can_edit_employees(role: str) -> bool:
    return role == "admin"


def can_manage_employee_payments(role: str) -> bool:
    return role in ("admin", "finance")
