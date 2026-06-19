"""Django `auth.User` ile giriş — web admin ile aynı kullanıcılar."""

from __future__ import annotations

from typing import Any

from django.contrib.auth import authenticate
from django.contrib.auth.models import User

from onmer_admin_desktop.database import ensure_django


def try_login(username: str, password: str) -> User | None:
    """
    Başarılıysa User nesnesi, aksi halde None.
    Sadece is_staff veya is_superuser olanların panele girmesine izin verilir.
    """
    ensure_django()
    u = authenticate(
        None,
        username=username.strip(),
        password=password,
    )
    if u is None:
        return None
    if not u.is_active:
        return None
    if not (u.is_staff or u.is_superuser):
        return None
    return u


def explain_login_failure(username: str, password: str) -> str:
    """
    try_login None döndüyse masaüstü arayüzde gösterilecek Türkçe neden.
    Her zaman açıklayıcı bir metin döner (genel 'giriş başarısız' tuzağı olmasın).
    """
    ensure_django()
    name = (username or "").strip()
    if not name:
        return "Kullanıcı adı boş olamaz."
    try:
        u = User.objects.filter(username=name).first()
    except Exception as exc:
        return f"Veritabanı okunamadı: {exc}"

    if u is None:
        return (
            "Bu kullanıcı adı bu veritabanında yok. "
            "Kurulu .exe eski olabilir veya yanlış veritabanına bağlanıyorsunuz: "
            "Önce build_windows.ps1, sonra Inno ile yeniden kurun; "
            "onmer_database.env içinde POSTGRES_* doğru mu kontrol edin; "
            "Windows ortam değişkeninde USE_SQLITE=1 kaldıysa kaldırın."
        )
    if not u.check_password(password):
        return "Şifre hatalı. (manage.py changepassword ile sıfırlayın.)"
    if not u.is_active:
        return "Bu hesap pasif."
    if not (u.is_staff or u.is_superuser):
        return (
            "Bu hesabın yönetim paneli yetkisi yok (Django admin’de personel / süper kullanıcı işaretleyin)."
        )
    auth_u = authenticate(None, username=name, password=password)
    if auth_u is None:
        return (
            "Django kimlik doğrulaması başarısız (hash / arka uç uyumsuzluğu). "
            "changepassword ile şifreyi yeniden kaydedin veya yeni süper kullanıcı oluşturun."
        )
    return (
        "Beklenmeyen giriş reddi. Uygulamayı kaynak koddan "
        "`python -m onmer_admin_desktop.main` ile deneyin; sorun sürerse proje kökünden yeniden derleyin."
    )


def user_display(u: User) -> str:
    return u.get_full_name() or u.username
