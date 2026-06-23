"""
Onmer Stok & Finans — bağımsız masaüstü uygulaması.

Web sitesiyle bağlantısı yoktur. Veriler yerel SQLite dosyasında tutulur.

Çalıştırma (geliştirme):
    pip install -r onmer_stok_desktop/requirements.txt
    python -m onmer_stok_desktop.main

Exe derleme:
    .\\packaging\\build_stok_windows.ps1
"""

from __future__ import annotations

import sys


def main() -> int:
    from PyQt6.QtWidgets import QApplication, QDialog

    from onmer_stok_desktop.services import ensure_ready
    from onmer_stok_desktop.ui.main_window import MainWindow
    from onmer_stok_desktop.ui.theme import apply_theme

    ensure_ready()

    app = QApplication(sys.argv)
    apply_theme(app)

    from onmer_stok_desktop.ui.login_window import LoginDialog

    while True:
        login = LoginDialog()
        if login.exec() != QDialog.DialogCode.Accepted or not login.user:
            return 0

        window = MainWindow(login.user)
        window.show()
        app.exec()

        if not window.relogin_requested:
            break

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
