"""Ana pencere."""

from __future__ import annotations

from typing import Any

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QStatusBar,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from onmer_stok_desktop import auth
from onmer_stok_desktop.config import APP_NAME, LOGO_PATH
from onmer_stok_desktop.ui.charts_page import ChartsPage
from onmer_stok_desktop.ui.dashboard_page import DashboardPage
from onmer_stok_desktop.ui.employees_page import EmployeesPage
from onmer_stok_desktop.ui.finance_page import FinancePage
from onmer_stok_desktop.ui.invoices_page import InvoicesPage
from onmer_stok_desktop.ui.stock_page import StockPage
from onmer_stok_desktop.ui.users_page import UsersPage


class MainWindow(QMainWindow):
    def __init__(self, user: dict[str, Any]):
        super().__init__()
        self._user = user
        self.relogin_requested = False
        self.setWindowTitle(APP_NAME)
        self.setMinimumSize(1100, 700)
        self.resize(1280, 800)

        if LOGO_PATH.is_file():
            self.setWindowIcon(QIcon(str(LOGO_PATH)))

        logo = QLabel()
        if LOGO_PATH.is_file():
            logo.setPixmap(
                QPixmap(str(LOGO_PATH)).scaled(
                    200,
                    52,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
        else:
            logo.setText(APP_NAME)
            logo.setObjectName("PageTitle")

        user_label = QLabel(f"{user['username']} — {user['role_label']}")
        user_label.setStyleSheet("color: #8b9cb3; margin-right: 12px;")

        btn_logout = QPushButton("Çıkış Yap")
        btn_logout.setObjectName("Danger")
        btn_logout.clicked.connect(self._logout)

        header_row = QHBoxLayout()
        header_row.setContentsMargins(20, 16, 20, 0)
        header_row.addWidget(logo)
        header_row.addStretch()
        header_row.addWidget(user_label)
        header_row.addWidget(btn_logout)

        self._tabs = QTabWidget()
        self._pages: dict[str, QWidget] = {}
        role = user["role"]

        self._dashboard = DashboardPage()
        self._pages["Özet"] = self._dashboard

        self._stock = StockPage()
        self._stock.set_read_only(not auth.can_edit_stock(role))
        self._stock.set_add_delete_only(auth.is_stock_add_delete_only(role))
        self._pages["Stok"] = self._stock

        self._finance = FinancePage()
        self._finance.set_read_only(not auth.can_edit_finance(role))
        self._pages["Gelir / Gider"] = self._finance

        self._employees = EmployeesPage()
        self._employees.set_permissions(
            can_edit_employees=auth.can_edit_employees(role),
            can_manage_payments=auth.can_manage_employee_payments(role),
        )
        self._pages["Personel"] = self._employees

        self._invoices = InvoicesPage()
        self._pages["Faturalar"] = self._invoices

        self._charts = ChartsPage()
        self._pages["Grafikler"] = self._charts

        self._users = UsersPage()
        self._pages["Kullanıcılar"] = self._users

        for tab_name in auth.ROLE_TABS.get(role, []):
            self._tabs.addTab(self._pages[tab_name], tab_name)

        self._tabs.currentChanged.connect(self._on_tab_changed)

        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setContentsMargins(12, 0, 12, 12)
        layout.addLayout(header_row)
        layout.addWidget(self._tabs)
        self.setCentralWidget(central)

        status = QStatusBar()
        self.setStatusBar(status)

        self.refresh_all()

    def _logout(self) -> None:
        self.relogin_requested = True
        self.close()

    def _on_tab_changed(self, _index: int) -> None:
        self.refresh_all()

    def refresh_all(self) -> None:
        tab = self._tabs.tabText(self._tabs.currentIndex())
        if tab == "Özet":
            self._dashboard.refresh()
        elif tab == "Stok":
            self._stock.refresh()
        elif tab == "Gelir / Gider":
            self._finance.refresh()
        elif tab == "Personel":
            self._employees.refresh()
        elif tab == "Faturalar":
            self._invoices.refresh()
        elif tab == "Grafikler":
            self._charts.refresh()
        elif tab == "Kullanıcılar":
            self._users.refresh()
