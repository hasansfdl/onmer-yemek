"""Gelir ve gider kayıtları."""

from __future__ import annotations

from datetime import date

from PyQt6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from onmer_stok_desktop import services
from onmer_stok_desktop.services import EXPENSE_CATEGORIES, INCOME_CATEGORIES

_FINANCE_CATEGORIES = {
    "income": INCOME_CATEGORIES,
    "expense": EXPENSE_CATEGORIES,
}


class _FinanceDialog(QDialog):
    def __init__(
        self,
        parent=None,
        entry_type: str = "income",
        entry: dict | None = None,
    ):
        super().__init__(parent)
        self._entry = entry
        if entry:
            entry_type = entry["entry_type"]
            self.setWindowTitle(
                "Gelir Düzenle" if entry_type == "income" else "Gider Düzenle"
            )
        else:
            self.setWindowTitle(
                "Gelir Ekle" if entry_type == "income" else "Gider Ekle"
            )

        self._amount = QDoubleSpinBox()
        self._amount.setRange(0.01, 99999999)
        self._amount.setDecimals(2)
        self._amount.setPrefix("₺ ")
        self._desc = QLineEdit()
        self._category = QComboBox()
        self._invoice = QLineEdit()
        self._invoice.setReadOnly(True)
        self._date = QDateEdit()
        self._date.setCalendarPopup(True)
        self._entry_type = entry_type

        if entry:
            self._amount.setValue(float(entry["amount"]))
            self._desc.setText(entry.get("description") or "")
            self._invoice.setText(entry.get("invoice_note") or "")
            parts = entry["entry_date"].split("-")
            if len(parts) == 3:
                self._date.setDate(
                    date(int(parts[0]), int(parts[1]), int(parts[2]))
                )
            else:
                self._date.setDate(date.today())
        else:
            self._invoice.setText(services.next_finance_invoice_note())
            self._date.setDate(date.today())

        form = QFormLayout()
        form.addRow("Tutar *", self._amount)
        if entry_type in _FINANCE_CATEGORIES:
            self._category.addItem("— Kategori seçin —", "")
            for name in _FINANCE_CATEGORIES[entry_type]:
                self._category.addItem(name, name)
            if entry and entry.get("category"):
                idx = self._category.findData(entry["category"])
                if idx >= 0:
                    self._category.setCurrentIndex(idx)
            form.addRow("Kategori *", self._category)
        form.addRow("Açıklama", self._desc)
        form.addRow("Fatura / Fiş (otomatik)", self._invoice)
        form.addRow("Tarih", self._date)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._try_accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)

    def _try_accept(self) -> None:
        if self._entry_type in _FINANCE_CATEGORIES and not self._category.currentData():
            label = "Gelir" if self._entry_type == "income" else "Gider"
            QMessageBox.warning(
                self, "Geçersiz bilgi", f"{label} kategorisi seçilmelidir."
            )
            return
        self.accept()

    def payload(self) -> dict:
        category = ""
        if self._entry_type in _FINANCE_CATEGORIES:
            category = self._category.currentData() or ""
        return {
            "entry_type": self._entry_type,
            "amount": self._amount.value(),
            "category": category,
            "description": self._desc.text().strip(),
            "invoice_note": "",
            "entry_date": self._date.date().toString("yyyy-MM-dd"),
        }


class FinancePage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._read_only = False
        title = QLabel("Gelir & Gider")
        title.setObjectName("PageTitle")

        btn_row = QHBoxLayout()
        self._btn_income = QPushButton("Gelir Ekle")
        self._btn_income.setObjectName("Primary")
        self._btn_expense = QPushButton("Gider Ekle")
        self._btn_edit = QPushButton("Düzenle")
        self._btn_del = QPushButton("Sil")
        self._btn_del.setObjectName("Danger")
        self._btn_refresh = QPushButton("Yenile")
        for b in (
            self._btn_income, self._btn_expense, self._btn_edit,
            self._btn_del, self._btn_refresh,
        ):
            btn_row.addWidget(b)
        btn_row.addStretch()

        self._table = QTableWidget()
        self._table.setColumnCount(7)
        self._table.setHorizontalHeaderLabels(
            ["ID", "Tarih", "Tür", "Kategori", "Tutar", "Fatura / Fiş", "Açıklama"]
        )
        self._table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.hideColumn(0)

        layout = QVBoxLayout(self)
        layout.addWidget(title)
        layout.addLayout(btn_row)
        layout.addWidget(self._table)

        self._btn_income.clicked.connect(lambda: self._add("income"))
        self._btn_expense.clicked.connect(lambda: self._add("expense"))
        self._btn_edit.clicked.connect(self._edit)
        self._btn_del.clicked.connect(self._delete)
        self._btn_refresh.clicked.connect(self.refresh)

    def set_read_only(self, read_only: bool) -> None:
        self._read_only = read_only
        for btn in (self._btn_income, self._btn_expense, self._btn_edit, self._btn_del):
            btn.setEnabled(not read_only)

    def _selected_id(self) -> int | None:
        rows = self._table.selectionModel().selectedRows()
        if not rows:
            return None
        return int(self._table.item(rows[0].row(), 0).text())

    def refresh(self) -> None:
        entries = services.list_finance_entries()
        labels = {"income": "Gelir", "expense": "Gider"}
        self._table.setRowCount(len(entries))
        for row, e in enumerate(entries):
            self._table.setItem(row, 0, QTableWidgetItem(str(e["id"])))
            self._table.setItem(row, 1, QTableWidgetItem(e["entry_date"]))
            self._table.setItem(row, 2, QTableWidgetItem(labels.get(e["entry_type"], e["entry_type"])))
            self._table.setItem(row, 3, QTableWidgetItem(e.get("category") or ""))
            self._table.setItem(row, 4, QTableWidgetItem(f"₺{float(e['amount']):,.2f}"))
            self._table.setItem(row, 5, QTableWidgetItem(e.get("invoice_note") or ""))
            self._table.setItem(row, 6, QTableWidgetItem(e.get("description") or ""))

    def _add(self, entry_type: str) -> None:
        dlg = _FinanceDialog(self, entry_type)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        p = dlg.payload()
        try:
            services.add_finance_entry(
                p["entry_type"], p["amount"],
                category=p["category"], description=p["description"],
                invoice_note=p["invoice_note"], entry_date=p["entry_date"],
            )
            self.refresh()
        except Exception as e:
            QMessageBox.warning(self, "Hata", str(e))

    def _edit(self) -> None:
        eid = self._selected_id()
        if not eid:
            QMessageBox.information(self, "Seçim", "Düzenlemek için kayıt seçin.")
            return
        entry = services.get_finance_entry(eid)
        if not entry or entry.get("employee_payment_id"):
            QMessageBox.warning(self, "Hata", "Kayıt düzenlenemez.")
            return
        dlg = _FinanceDialog(self, entry=entry)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        p = dlg.payload()
        try:
            services.update_finance_entry(
                eid,
                amount=p["amount"],
                description=p["description"],
                entry_date=p["entry_date"],
                category=p["category"],
            )
            self.refresh()
        except Exception as e:
            QMessageBox.warning(self, "Hata", str(e))

    def _delete(self) -> None:
        eid = self._selected_id()
        if not eid:
            QMessageBox.information(self, "Seçim", "Silmek için kayıt seçin.")
            return
        if QMessageBox.question(self, "Sil", "Kayıt silinsin mi?") != QMessageBox.StandardButton.Yes:
            return
        services.delete_finance_entry(eid)
        self.refresh()
