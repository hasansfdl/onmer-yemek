"""Admin giriş penceresi — Django `User` (staff/superuser)."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QVBoxLayout,
)

from onmer_admin_desktop import config
from onmer_admin_desktop.auth import explain_login_failure, try_login
from onmer_admin_desktop.database import ensure_django
from onmer_admin_desktop.ui.branding import brand_icon, brand_pixmap_scaled


class LoginDialog(QDialog):
    """Kullanıcı adı / şifre; başarıda `authenticated_user` dolu."""

    def __init__(self) -> None:
        ensure_django()
        super().__init__()
        self.authenticated_user = None
        self.setWindowTitle(config.APP_TITLE + " — Giriş")
        self.setFixedWidth(420)
        self.setModal(True)
        _ico = brand_icon()
        if not _ico.isNull():
            self.setWindowIcon(_ico)

        layout = QVBoxLayout(self)
        pm = brand_pixmap_scaled(max_width=280)
        if pm is not None:
            logo = QLabel()
            logo.setPixmap(pm)
            logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(logo)
            layout.addSpacing(8)

        title = QLabel(config.ORG_NAME)
        title.setObjectName("Title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        subtitle = QLabel("Yönetim paneline giriş")
        subtitle.setObjectName("Muted")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._user = QLineEdit()
        self._user.setPlaceholderText("Kullanıcı adı")
        self._pw = QLineEdit()
        self._pw.setPlaceholderText("Şifre")
        self._pw.setEchoMode(QLineEdit.EchoMode.Password)

        self._err = QLabel("")
        self._err.setObjectName("Muted")
        self._err.setStyleSheet("color: #c94c4c;")
        self._err.setWordWrap(True)

        form = QFormLayout()
        form.addRow("Kullanıcı adı", self._user)
        form.addRow("Şifre", self._pw)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        ok_btn = buttons.button(QDialogButtonBox.StandardButton.Ok)
        if ok_btn:
            ok_btn.setObjectName("Primary")
            ok_btn.setText("Giriş")

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(16)
        layout.addLayout(form)
        layout.addWidget(self._err)
        layout.addWidget(buttons)

    def _on_accept(self) -> None:
        self._err.setText("")
        u = self._user.text().strip()
        p = self._pw.text()
        if not u or not p:
            self._err.setText("Kullanıcı adı ve şifre zorunludur.")
            return
        user = try_login(u, p)
        if user is None:
            self._err.setText(explain_login_failure(u, p))
            return
        self.authenticated_user = user
        self.accept()
