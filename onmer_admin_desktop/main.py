"""
Onmer Admin Panel — masaüstü giriş noktası.

Çalıştırmadan önce proje kökünde (`onmer_yemekcilik`) bir sanal ortam
açıp `pip install -r onmer_admin_desktop/requirements.txt` ile bağımlılıkları
yükleyin.

Önerilen komut (proje kökünden)::

    python -m onmer_admin_desktop.main

Windows’ta doğrudan::

    py -m onmer_admin_desktop.main
"""

from __future__ import annotations

import sys
from pathlib import Path


def _ensure_project_root_on_path() -> None:
    """`onmer` Django paketini ve uygulama paketlerini bulmak için."""
    from onmer_admin_desktop import config

    s = str(config.PROJECT_ROOT.resolve())
    if s not in sys.path:
        sys.path.insert(0, s)


def main() -> int:
    _ensure_project_root_on_path()
    from load_env import bootstrap

    bootstrap()

    from PyQt6.QtWidgets import QApplication, QDialog, QMessageBox

    from onmer_admin_desktop.database import check_connection, ensure_django
    from onmer_admin_desktop.ui.branding import brand_icon
    from onmer_admin_desktop.ui.theme import apply_theme

    app = QApplication(sys.argv)
    app.setApplicationDisplayName("Onmer Admin Panel")
    _ico = brand_icon()
    if not _ico.isNull():
        app.setWindowIcon(_ico)
    apply_theme(app)

    ensure_django()
    if getattr(sys, "frozen", False):
        from django.conf import settings
        from django.core.management import call_command

        if "sqlite" in settings.DATABASES["default"]["ENGINE"]:
            try:
                call_command("migrate", interactive=False, verbosity=0)
            except Exception as exc:
                QMessageBox.critical(
                    None,
                    "Veritabanı",
                    "Şema güncellenemedi (migrate).\n\n"
                    f"Ayrıntı: {exc}",
                )
                return 1

    if not check_connection():
        extra = ""
        if getattr(sys, "frozen", False):
            exe_dir = Path(sys.executable).resolve().parent
            try:
                from django.conf import settings

                db = settings.DATABASES["default"]
                engine = db.get("ENGINE", "")
                if "sqlite" in engine:
                    db_shown = str(db.get("NAME", ""))
                    extra = (
                        f"\nUygulama klasörü: {exe_dir}\n"
                        f"SQLite dosyası: {db_shown}\n"
                        "SQLite kullanmak için USE_SQLITE=1 ve gerekirse onmer_database.env "
                        "dosyasına yazın."
                    )
                else:
                    extra = (
                        f"\nUygulama klasörü: {exe_dir}\n"
                        "PostgreSQL: Sunucunun çalıştığından ve POSTGRES_* değişkenlerinin "
                        "doğru olduğundan emin olun.\n"
                        f"İsteğe bağlı: bu klasöre onmer_database.env koyun (ör. POSTGRES_HOST=…).\n"
                        "Örnek satırlar: USE_SQLITE=0 veya hiç yazmayın, POSTGRES_DB, POSTGRES_USER, "
                        "POSTGRES_PASSWORD, POSTGRES_HOST, POSTGRES_PORT."
                    )
            except Exception:
                extra = (
                    f"\nUygulama klasörü: {exe_dir}\n"
                    "onmer_database.env ile veritabanı ayarlarını kontrol edin."
                )
        QMessageBox.critical(
            None,
            "Veritabanı",
            "Veritabanına bağlanılamadı.\n\n"
            "Geliştirme ortamında komutu proje kökünde çalıştırdığınızdan emin olun. "
            "SQLite için USE_SQLITE=1; PostgreSQL için POSTGRES_* ortam değişkenleri gerekir."
            + extra,
        )
        return 1

    from onmer_admin_desktop.relaunch import consume_relaunch_user
    from onmer_admin_desktop.ui.login_window import LoginDialog
    from onmer_admin_desktop.ui.main_window import MainWindow

    user = consume_relaunch_user()
    if user is None:
        dlg = LoginDialog()
        if (
            dlg.exec() != QDialog.DialogCode.Accepted
            or dlg.authenticated_user is None
        ):
            return 0
        user = dlg.authenticated_user

    try:
        win = MainWindow(user)
    except Exception as exc:
        QMessageBox.critical(
            None,
            "Uygulama",
            "Ana pencere açılamadı.\n\n"
            f"Ayrıntı: {exc}",
        )
        return 1
    win.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
