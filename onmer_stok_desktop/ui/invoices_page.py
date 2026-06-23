"""Faturalar — personel ödemeleri ve gelir/gider fişleri."""

from __future__ import annotations

from datetime import date

from PyQt6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from onmer_stok_desktop import services
from onmer_stok_desktop.services import PAYMENT_TYPE_LABELS


def _money(value: float) -> str:
    return f"₺{float(value):,.2f}"


class _FilterBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._date_from = QDateEdit()
        self._date_from.setCalendarPopup(True)
        self._date_from.setDate(date(date.today().year, 1, 1))
        self._date_to = QDateEdit()
        self._date_to.setCalendarPopup(True)
        self._date_to.setDate(date.today())
        self._invoice_search = QLineEdit()
        self._invoice_search.setPlaceholderText("Örn. 5 veya 0005")
        self._btn_search = QPushButton("Fiş Ara")
        self._btn_search.setObjectName("Primary")
        self._btn_clear = QPushButton("Temizle")
        self._btn_refresh = QPushButton("Yenile")

    def date_from(self) -> str | None:
        return self._date_from.date().toString("yyyy-MM-dd")

    def date_to(self) -> str | None:
        return self._date_to.date().toString("yyyy-MM-dd")

    def invoice_search(self) -> str:
        return self._invoice_search.text().strip()

    def _add_date_rows(self, layout: QHBoxLayout) -> None:
        layout.addWidget(QLabel("Başlangıç"))
        layout.addWidget(self._date_from)
        layout.addWidget(QLabel("Bitiş"))
        layout.addWidget(self._date_to)

    def _add_invoice_row(self, layout: QHBoxLayout) -> None:
        layout.addWidget(QLabel("Fiş No"))
        layout.addWidget(self._invoice_search)
        layout.addWidget(self._btn_search)
        layout.addWidget(self._btn_clear)
        layout.addWidget(self._btn_refresh)
        layout.addStretch()


class _PaymentInvoicesTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._filter = _FilterBar()

        self._ptype = QComboBox()
        self._ptype.addItem("Tümü", "")
        for key, label in PAYMENT_TYPE_LABELS.items():
            self._ptype.addItem(label, key)
        self._employee = QLineEdit()
        self._employee.setPlaceholderText("Personel adı")

        filter_row = QHBoxLayout()
        self._filter._add_date_rows(filter_row)
        filter_row.addWidget(QLabel("Ödeme türü"))
        filter_row.addWidget(self._ptype)
        filter_row.addWidget(QLabel("Personel"))
        filter_row.addWidget(self._employee)

        filter_row2 = QHBoxLayout()
        self._filter._add_invoice_row(filter_row2)

        self._table = QTableWidget()
        self._table.setColumnCount(7)
        self._table.setHorizontalHeaderLabels(
            ["ID", "Fiş No", "Tarih", "Personel", "Tür", "Tutar", "Not"]
        )
        self._table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.hideColumn(0)

        layout = QVBoxLayout(self)
        layout.addLayout(filter_row)
        layout.addLayout(filter_row2)
        layout.addWidget(self._table)

        self._filter._btn_search.clicked.connect(self.refresh)
        self._filter._btn_clear.clicked.connect(self._clear_filters)
        self._filter._btn_refresh.clicked.connect(self.refresh)
        self._filter._invoice_search.returnPressed.connect(self.refresh)
        self._filter._date_from.dateChanged.connect(lambda _: self.refresh())
        self._filter._date_to.dateChanged.connect(lambda _: self.refresh())
        self._ptype.currentIndexChanged.connect(lambda _: self.refresh())
        self._employee.returnPressed.connect(self.refresh)
        self._employee.editingFinished.connect(self.refresh)

    def _clear_filters(self) -> None:
        self._filter._date_from.setDate(date(date.today().year, 1, 1))
        self._filter._date_to.setDate(date.today())
        self._ptype.setCurrentIndex(0)
        self._employee.clear()
        self._filter._invoice_search.clear()
        self.refresh()

    def refresh(self) -> None:
        rows = services.list_payment_invoices(
            payment_type=self._ptype.currentData() or None,
            date_from=self._filter.date_from(),
            date_to=self._filter.date_to(),
            invoice_search=self._filter.invoice_search(),
            employee_name=self._employee.text(),
        )
        self._table.setRowCount(len(rows))
        for row, p in enumerate(rows):
            ptype = PAYMENT_TYPE_LABELS.get(p["payment_type"], p["payment_type"])
            self._table.setItem(row, 0, QTableWidgetItem(str(p["id"])))
            self._table.setItem(row, 1, QTableWidgetItem(p.get("invoice_note") or ""))
            self._table.setItem(row, 2, QTableWidgetItem(p["payment_date"]))
            self._table.setItem(row, 3, QTableWidgetItem(p.get("employee_name") or ""))
            self._table.setItem(row, 4, QTableWidgetItem(ptype))
            self._table.setItem(row, 5, QTableWidgetItem(_money(p["amount"])))
            self._table.setItem(row, 6, QTableWidgetItem(p.get("notes") or ""))


class _FinanceInvoicesTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._filter = _FilterBar()

        self._etype = QComboBox()
        self._etype.addItem("Tümü", "")
        self._etype.addItem("Gelir", "income")
        self._etype.addItem("Gider", "expense")
        self._category = QLineEdit()
        self._category.setPlaceholderText("Kategori")

        filter_row = QHBoxLayout()
        self._filter._add_date_rows(filter_row)
        filter_row.addWidget(QLabel("Tür"))
        filter_row.addWidget(self._etype)
        filter_row.addWidget(QLabel("Kategori"))
        filter_row.addWidget(self._category)

        filter_row2 = QHBoxLayout()
        self._filter._add_invoice_row(filter_row2)

        self._table = QTableWidget()
        self._table.setColumnCount(7)
        self._table.setHorizontalHeaderLabels(
            ["ID", "Fiş No", "Tarih", "Tür", "Kategori", "Tutar", "Açıklama"]
        )
        self._table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.hideColumn(0)

        layout = QVBoxLayout(self)
        layout.addLayout(filter_row)
        layout.addLayout(filter_row2)
        layout.addWidget(self._table)

        self._filter._btn_search.clicked.connect(self.refresh)
        self._filter._btn_clear.clicked.connect(self._clear_filters)
        self._filter._btn_refresh.clicked.connect(self.refresh)
        self._filter._invoice_search.returnPressed.connect(self.refresh)
        self._filter._date_from.dateChanged.connect(lambda _: self.refresh())
        self._filter._date_to.dateChanged.connect(lambda _: self.refresh())
        self._etype.currentIndexChanged.connect(lambda _: self.refresh())
        self._category.returnPressed.connect(self.refresh)
        self._category.editingFinished.connect(self.refresh)

    def _clear_filters(self) -> None:
        self._filter._date_from.setDate(date(date.today().year, 1, 1))
        self._filter._date_to.setDate(date.today())
        self._etype.setCurrentIndex(0)
        self._category.clear()
        self._filter._invoice_search.clear()
        self.refresh()

    def refresh(self) -> None:
        labels = {"income": "Gelir", "expense": "Gider"}
        rows = services.list_finance_invoices(
            entry_type=self._etype.currentData() or None,
            category=self._category.text(),
            date_from=self._filter.date_from(),
            date_to=self._filter.date_to(),
            invoice_search=self._filter.invoice_search(),
        )
        self._table.setRowCount(len(rows))
        for row, e in enumerate(rows):
            self._table.setItem(row, 0, QTableWidgetItem(str(e["id"])))
            self._table.setItem(row, 1, QTableWidgetItem(e.get("invoice_note") or ""))
            self._table.setItem(row, 2, QTableWidgetItem(e["entry_date"]))
            self._table.setItem(
                row, 3, QTableWidgetItem(labels.get(e["entry_type"], e["entry_type"]))
            )
            self._table.setItem(row, 4, QTableWidgetItem(e.get("category") or ""))
            self._table.setItem(row, 5, QTableWidgetItem(_money(e["amount"])))
            self._table.setItem(row, 6, QTableWidgetItem(e.get("description") or ""))


class InvoicesPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        title = QLabel("Faturalar")
        title.setObjectName("PageTitle")

        hint = QLabel(
            f"Personel ödemeleri: {services.next_payment_invoice_note()} · "
            f"Gelir/Gider: {services.next_finance_invoice_note()}"
        )
        hint.setStyleSheet("color: #8b9cb3; margin-bottom: 4px;")
        self._hint = hint

        self._tabs = QTabWidget()
        self._payments_tab = _PaymentInvoicesTab()
        self._finance_tab = _FinanceInvoicesTab()
        self._tabs.addTab(self._payments_tab, "Maaş Ödemesi")
        self._tabs.addTab(self._finance_tab, "Gelir / Gider")
        self._tabs.currentChanged.connect(self._on_sub_tab_changed)

        layout = QVBoxLayout(self)
        layout.addWidget(title)
        layout.addWidget(hint)
        layout.addWidget(self._tabs)

    def _on_sub_tab_changed(self, _index: int) -> None:
        self.refresh()

    def refresh(self) -> None:
        self._hint.setText(
            f"Personel ödemeleri: {services.next_payment_invoice_note()} · "
            f"Gelir/Gider: {services.next_finance_invoice_note()}"
        )
        if self._tabs.currentIndex() == 0:
            self._payments_tab.refresh()
        else:
            self._finance_tab.refresh()
