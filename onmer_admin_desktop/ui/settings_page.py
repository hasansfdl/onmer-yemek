"""Site genel ayarları — SiteSetting özet düzenleme."""

from __future__ import annotations

from PyQt6.QtWidgets import (
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from django.contrib.auth.models import User

from core.models import SiteSetting

from onmer_admin_desktop.database import db_transaction, ensure_django


class SettingsPage(QWidget):
    def __init__(self, user: User) -> None:
        ensure_django()
        super().__init__()
        self._user = user

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        t = QLabel("Site ayarları")
        t.setObjectName("Title")
        root.addWidget(t)

        box = QGroupBox("İletişim ve firma (SiteSetting)")
        form = QFormLayout()
        self._company = QLineEdit()
        self._phone = QLineEdit()
        self._whatsapp = QLineEdit()
        self._email = QLineEdit()
        self._address = QLineEdit()
        self._instagram = QLineEdit()
        self._facebook = QLineEdit()
        form.addRow("Firma adı", self._company)
        form.addRow("Telefon", self._phone)
        form.addRow("WhatsApp", self._whatsapp)
        form.addRow("E-posta", self._email)
        form.addRow("Adres (yazılı)", self._address)
        self._maps_embed = QPlainTextEdit()
        self._maps_embed.setPlaceholderText(
            "Google Maps iframe src veya harita bağlantısı (Lokasyon sayfası)"
        )
        self._maps_embed.setMaximumHeight(100)
        form.addRow("Google Maps URL", self._maps_embed)
        form.addRow("Instagram URL", self._instagram)
        form.addRow("Facebook URL", self._facebook)
        bv = QVBoxLayout(box)
        bv.addLayout(form)
        row = QHBoxLayout()
        row.addStretch()
        btn = QPushButton("Kaydet")
        btn.setObjectName("Primary")
        btn.clicked.connect(self._save)
        row.addWidget(btn)
        bv.addLayout(row)
        root.addWidget(box)
        root.addStretch()

        self.refresh()

    def refresh(self) -> None:
        s = SiteSetting.load()
        self._company.setText(s.company_name)
        self._phone.setText(s.phone)
        self._whatsapp.setText(s.whatsapp)
        self._email.setText(s.email)
        self._address.setText(s.address)
        self._maps_embed.setPlainText(s.google_maps_embed or "")
        self._instagram.setText(s.instagram or "")
        self._facebook.setText(s.facebook or "")

    def _save(self) -> None:
        try:
            with db_transaction():
                s = SiteSetting.load()
                s.company_name = self._company.text().strip() or s.company_name
                s.phone = self._phone.text().strip()
                s.whatsapp = self._whatsapp.text().strip()
                s.email = self._email.text().strip()
                s.address = self._address.text().strip()
                s.google_maps_embed = self._maps_embed.toPlainText().strip()
                s.instagram = self._instagram.text().strip()
                s.facebook = self._facebook.text().strip()
                s.save()
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))
            return
        QMessageBox.information(self, "Tamam", "Site ayarları güncellendi.")
