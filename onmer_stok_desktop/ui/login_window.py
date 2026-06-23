"""Admin giriş penceresi."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QDialog,
    QFormLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from onmer_stok_desktop import auth
from onmer_stok_desktop.config import APP_NAME, LOGO_PATH


class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.user: dict | None = None
        self.setWindowTitle(f"{APP_NAME} — Giriş")
        self.setModal(True)
        self.setFixedSize(420, 520)

        logo = QLabel()
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if LOGO_PATH.is_file():
            pix = QPixmap(str(LOGO_PATH))
            logo.setPixmap(
                pix.scaled(
                    280, 120,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
        else:
            logo.setText("ONMER")
            logo.setStyleSheet("font-size: 28px; font-weight: 700; color: #d4af37;")

        subtitle = QLabel("Stok & Finans Yönetim Paneli")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color: #8b9cb3; margin-bottom: 8px;")

        self._username = QLineEdit()
        self._username.setPlaceholderText("Kullanıcı adı")
        self._password = QLineEdit()
        self._password.setPlaceholderText("Şifre")
        self._password.setEchoMode(QLineEdit.EchoMode.Password)

        form = QFormLayout()
        form.addRow("Kullanıcı adı", self._username)
        form.addRow("Şifre", self._password)

        self._btn_login = QPushButton("Giriş Yap")
        self._btn_login.setObjectName("Primary")
        self._btn_login.setDefault(True)
        self._btn_login.clicked.connect(self._try_login)
        self._password.returnPressed.connect(self._try_login)
        self._username.returnPressed.connect(self._password.setFocus)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(12)
        layout.addWidget(logo)
        layout.addWidget(subtitle)
        layout.addSpacing(8)
        layout.addLayout(form)
        layout.addWidget(self._btn_login)

    def _try_login(self) -> None:
        user = auth.verify_login(self._username.text(), self._password.text())
        if user:
            self.user = user
            self.accept()
            return
        QMessageBox.warning(
            self,
            "Giriş başarısız",
            "Kullanıcı adı veya şifre hatalı.",
        )
        self._password.clear()
        self._password.setFocus()
