"""Ana pencere: üst bar, sol sidebar, sayfa yığını."""

from __future__ import annotations

import subprocess
import sys

from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
    QApplication,
)

from django.contrib.auth.models import User

from onmer_admin_desktop import config
from onmer_admin_desktop.auth import user_display
from onmer_admin_desktop.ui.branding import brand_icon, brand_pixmap_scaled
from onmer_admin_desktop.ui.dashboard_window import DashboardPage
from onmer_admin_desktop.ui.foods_page import FoodsPage
from onmer_admin_desktop.ui.orders_page import OrdersPage
from onmer_admin_desktop.ui.portfolio_page import PortfolioPage
from onmer_admin_desktop.ui.reports_page import ReportsPage
from onmer_admin_desktop.ui.reservations_page import ReservationsPage
from onmer_admin_desktop.ui.settings_page import SettingsPage
from onmer_admin_desktop.ui.users_page import UsersPage


class MainWindow(QMainWindow):
    def __init__(self, user: User) -> None:
        super().__init__()
        self._user = user
        self.setWindowTitle(config.APP_TITLE)
        _ico = brand_icon()
        if not _ico.isNull():
            self.setWindowIcon(_ico)
        self.resize(1200, 780)
        self.setMinimumSize(960, 600)

        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self._nav = QListWidget()
        self._nav.setFixedWidth(240)
        self._nav.setSpacing(2)
        entries = [
            ("Genel Bakış", DashboardPage),
            ("Siparişler", OrdersPage),
            ("İletişim", ReservationsPage),
            ("Yemekler", FoodsPage),
            ("Portfolyo", PortfolioPage),
            ("Kullanıcılar", UsersPage),
            ("Raporlar", ReportsPage),
            ("Ayarlar", SettingsPage),
        ]
        for label, _ in entries:
            QListWidgetItem(label, self._nav)

        self._stack = QStackedWidget()
        for _, cls in entries:
            page = cls(self._user)
            self._stack.addWidget(page)

        self._nav.currentRowChanged.connect(self._on_nav)
        self._nav.setCurrentRow(0)

        right_wrap = QWidget()
        rv = QVBoxLayout(right_wrap)
        rv.setContentsMargins(0, 0, 0, 0)
        rv.setSpacing(0)

        top = QWidget()
        top.setStyleSheet(
            "background-color: #161616; border-bottom: 1px solid #2a2a2a;"
        )
        th = QHBoxLayout(top)
        th.setContentsMargins(16, 12, 16, 12)
        pm = brand_pixmap_scaled(max_height=36)
        if pm is not None:
            logo_lbl = QLabel()
            logo_lbl.setPixmap(pm)
            th.addWidget(logo_lbl)
            th.addSpacing(10)
        brand = QLabel(
            f'<span style="color:#c9a227;font-weight:700">{config.APP_TITLE}</span>'
        )
        th.addWidget(brand)
        th.addStretch()
        btn_refresh = QPushButton("Yenile")
        btn_refresh.setToolTip(
            "Uygulamayı kapatıp aynı kullanıcıyla yeniden başlatır (şifre sormaz). "
            "Python kodu veya arayüz (.py) dosyalarındaki değişiklikler böylece yüklenir."
        )
        btn_refresh.clicked.connect(self._restart_application)
        th.addWidget(btn_refresh)
        lbl = QLabel(f"Giriş: <b>{user_display(user)}</b>")
        lbl.setObjectName("Muted")
        th.addWidget(lbl)
        btn_out = QPushButton("Çıkış")
        btn_out.clicked.connect(self._logout)
        th.addWidget(btn_out)

        rv.addWidget(top)
        rv.addWidget(self._stack, 1)

        root.addWidget(self._nav)
        root.addWidget(right_wrap, 1)

        self.statusBar().showMessage("Hazır.")

    def _restart_application(self) -> None:
        """
        Yeni süreç olarak uygulamayı başlatır ve bu süreci kapatır.

        PyQt ve import edilmiş Python modülleri bellekte kalır; kaynak kod
        değişince değişikliğin görülmesi için sürecin yeniden başlaması gerekir.
        """
        reply = QMessageBox.question(
            self,
            "Uygulamayı yenile",
            "Uygulama kapatılıp yeniden açılacak. Kaydedilmemiş formlar sıfırlanır.\n\n"
            "Bu işlem, düzenlediğiniz .py dosyalarındaki değişikliklerin "
            "yüklenmesi içindir.\n\n"
            "Aynı oturumla devam edersiniz; tekrar şifre istenmez.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        from onmer_admin_desktop.relaunch import write_relaunch_token

        try:
            write_relaunch_token(self._user.pk)
        except OSError as e:
            QMessageBox.critical(
                self,
                "Oturum",
                f"Yeniden başlatma jetonu yazılamadı:\n{e}",
            )
            return

        root = str(config.PROJECT_ROOT)
        cmd = [sys.executable, "-m", "onmer_admin_desktop.main"]
        popen_kw: dict = {
            "cwd": root,
            "stdin": subprocess.DEVNULL,
            "stdout": subprocess.DEVNULL,
            "stderr": subprocess.DEVNULL,
        }
        if sys.platform == "win32":
            popen_kw["creationflags"] = subprocess.CREATE_NO_WINDOW
        else:
            popen_kw["start_new_session"] = True

        try:
            subprocess.Popen(cmd, **popen_kw)
        except OSError as e:
            QMessageBox.critical(
                self,
                "Yeniden başlatılamadı",
                f"Yeni süreç başlatılamadı:\n{e}\n\n"
                f"Komut: {' '.join(cmd)}\nÇalışma dizini: {root}",
            )
            return

        QApplication.quit()

    def _on_nav(self, row: int) -> None:
        if row < 0:
            return
        self._stack.setCurrentIndex(row)
        w = self._stack.currentWidget()
        if hasattr(w, "refresh"):
            w.refresh()

    def _logout(self) -> None:
        reply = QMessageBox.question(
            self,
            "Çıkış",
            "Oturumu kapatmak istiyor musunuz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            QApplication.quit()
