"""Stok ve ürün yönetimi."""

from __future__ import annotations

from datetime import date

from PyQt6.QtCore import Qt
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
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from onmer_stok_desktop import services


class _ProductDialog(QDialog):
    def __init__(self, parent=None, product: dict | None = None):
        super().__init__(parent)
        self.setWindowTitle("Ürün" if product else "Yeni Ürün")
        self.setMinimumWidth(400)
        self._product = product

        self._name = QLineEdit()
        self._unit = QComboBox()
        self._unit.setEditable(True)
        self._unit.addItems(["adet", "kg", "lt", "paket", "koli"])
        self._qty = QDoubleSpinBox()
        self._qty.setRange(0.01, 999999)
        self._qty.setDecimals(2)
        self._qty.setValue(1)
        self._cost = QDoubleSpinBox()
        self._cost.setRange(0, 9999999)
        self._cost.setDecimals(2)
        self._cost.setPrefix("₺ ")
        self._notes = QTextEdit()
        self._notes.setMaximumHeight(80)

        if product:
            self._name.setText(product["name"])
            self._unit.setCurrentText(product["unit"])
            self._cost.setValue(float(product["unit_cost"]))
            self._notes.setPlainText(product.get("notes") or "")

        form = QFormLayout()
        form.addRow("Ürün adı *", self._name)
        form.addRow("Birim", self._unit)
        if not product:
            form.addRow("Stok miktarı *", self._qty)
        form.addRow("Birim maliyet", self._cost)
        form.addRow("Not", self._notes)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)

    def data(self) -> dict:
        payload = {
            "name": self._name.text().strip(),
            "unit": self._unit.currentText().strip(),
            "category": "",
            "unit_cost": self._cost.value(),
            "notes": self._notes.toPlainText().strip(),
        }
        if not self._product:
            payload["quantity"] = self._qty.value()
        return payload


class _MovementDialog(QDialog):
    def __init__(self, parent, products: list[dict], movement_type: str):
        super().__init__(parent)
        titles = {"in": "Stok Girişi", "out": "Stok Çıkışı / Satış"}
        self.setWindowTitle(titles.get(movement_type, "Hareket"))
        self._movement_type = movement_type
        self._products_by_id = {p["id"]: p for p in products}

        self._product = QComboBox()
        for p in products:
            self._product.addItem(
                f"{p['name']} ({p['quantity']} {p['unit']})", p["id"]
            )
        self._qty = QDoubleSpinBox()
        self._qty.setRange(0.01, 999999)
        self._qty.setDecimals(2)
        self._cost = QDoubleSpinBox()
        self._cost.setRange(0, 9999999)
        self._cost.setDecimals(2)
        self._cost.setPrefix("₺ ")
        self._date = QDateEdit()
        self._date.setCalendarPopup(True)
        self._date.setDate(date.today())
        self._note = QLineEdit()

        form = QFormLayout()
        form.addRow("Ürün *", self._product)
        form.addRow("Miktar *", self._qty)
        if movement_type == "in":
            form.addRow("Alış birim fiyatı", self._cost)
            self._product.currentIndexChanged.connect(self._sync_cost_from_product)
            self._sync_cost_from_product()
        form.addRow("Tarih", self._date)
        form.addRow("Not", self._note)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)

    def _sync_cost_from_product(self) -> None:
        product = self._products_by_id.get(self._product.currentData())
        if product:
            self._cost.setValue(float(product["unit_cost"]))

    def payload(self) -> dict:
        return {
            "product_id": self._product.currentData(),
            "movement_type": self._movement_type,
            "quantity": self._qty.value(),
            "unit_cost": self._cost.value() if self._movement_type == "in" else 0,
            "unit_price": 0,
            "movement_date": self._date.date().toString("yyyy-MM-dd"),
            "note": self._note.text().strip(),
        }


class StockPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._read_only = False
        self._add_delete_only = False
        title = QLabel("Stok Takibi")
        title.setObjectName("PageTitle")

        btn_row = QHBoxLayout()
        self._btn_add = QPushButton("Yeni Ürün")
        self._btn_add.setObjectName("Primary")
        self._btn_edit = QPushButton("Düzenle")
        self._btn_in = QPushButton("Stok Girişi")
        self._btn_out = QPushButton("Satış / Çıkış")
        self._btn_del = QPushButton("Sil")
        self._btn_del.setObjectName("Danger")
        self._btn_refresh = QPushButton("Yenile")
        for b in (
            self._btn_add, self._btn_edit, self._btn_in,
            self._btn_out, self._btn_del, self._btn_refresh,
        ):
            btn_row.addWidget(b)
        btn_row.addStretch()

        splitter = QSplitter(Qt.Orientation.Vertical)
        self._products = QTableWidget()
        self._products.setColumnCount(5)
        self._products.setHorizontalHeaderLabels(
            ["ID", "Ürün", "Stok", "Birim Maliyet", "Not"]
        )
        self._products.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self._products.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._products.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._products.hideColumn(0)

        self._movements = QTableWidget()
        self._movements.setColumnCount(6)
        self._movements.setHorizontalHeaderLabels(
            ["Tarih", "Ürün", "Tür", "Miktar", "Tutar", "Not"]
        )
        self._movements.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self._movements.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        self._movement_wrap = QWidget()
        movement_layout = QVBoxLayout(self._movement_wrap)
        movement_layout.setContentsMargins(0, 0, 0, 0)
        movement_layout.addWidget(QLabel("Stok Hareketleri"))
        movement_layout.addWidget(self._movements)

        splitter.addWidget(self._products)
        splitter.addWidget(self._movement_wrap)

        layout = QVBoxLayout(self)
        layout.addWidget(title)
        layout.addLayout(btn_row)
        layout.addWidget(splitter)

        self._btn_add.clicked.connect(self._add_product)
        self._btn_edit.clicked.connect(self._edit_product)
        self._btn_in.clicked.connect(lambda: self._movement("in"))
        self._btn_out.clicked.connect(lambda: self._movement("out"))
        self._btn_del.clicked.connect(self._delete_product)
        self._btn_refresh.clicked.connect(self.refresh)

    def set_read_only(self, read_only: bool) -> None:
        self._read_only = read_only
        self._apply_button_state()

    def set_add_delete_only(self, enabled: bool) -> None:
        self._add_delete_only = enabled
        limited_buttons = (
            self._btn_edit, self._btn_in, self._btn_out,
        )
        for btn in limited_buttons:
            btn.setVisible(not enabled)
        self._movement_wrap.setVisible(not enabled)
        self._apply_button_state()

    def _apply_button_state(self) -> None:
        if self._add_delete_only:
            self._btn_add.setEnabled(not self._read_only)
            self._btn_del.setEnabled(not self._read_only)
            return
        for btn in (
            self._btn_add, self._btn_edit, self._btn_in,
            self._btn_out, self._btn_del,
        ):
            btn.setEnabled(not self._read_only)

    def _selected_id(self) -> int | None:
        rows = self._products.selectionModel().selectedRows()
        if not rows:
            return None
        return int(self._products.item(rows[0].row(), 0).text())

    def refresh(self) -> None:
        products = services.list_products()
        self._products.setRowCount(len(products))
        for row, p in enumerate(products):
            self._products.setItem(row, 0, QTableWidgetItem(str(p["id"])))
            self._products.setItem(row, 1, QTableWidgetItem(p["name"]))
            self._products.setItem(
                row, 2, QTableWidgetItem(f"{p['quantity']} {p['unit']}")
            )
            self._products.setItem(
                row, 3, QTableWidgetItem(f"₺{float(p['unit_cost']):,.2f}")
            )
            self._products.setItem(row, 4, QTableWidgetItem(p.get("notes") or ""))

        moves = services.list_stock_movements()
        type_labels = {"in": "Giriş", "out": "Çıkış", "adjust": "Düzeltme"}
        self._movements.setRowCount(len(moves))
        for row, m in enumerate(moves):
            if m["movement_type"] == "out":
                unit = float(m["unit_price"]) if float(m["unit_price"]) > 0 else float(m["unit_cost"])
                amount = m["quantity"] * unit
            elif m["movement_type"] == "in":
                amount = m["quantity"] * m["unit_cost"]
            else:
                amount = 0
            self._movements.setItem(row, 0, QTableWidgetItem(m["movement_date"]))
            self._movements.setItem(row, 1, QTableWidgetItem(m["product_name"]))
            self._movements.setItem(
                row, 2, QTableWidgetItem(type_labels.get(m["movement_type"], m["movement_type"]))
            )
            self._movements.setItem(
                row, 3, QTableWidgetItem(f"{m['quantity']} {m['product_unit']}")
            )
            self._movements.setItem(row, 4, QTableWidgetItem(f"₺{amount:,.2f}"))
            self._movements.setItem(row, 5, QTableWidgetItem(m.get("note") or ""))

    def _add_product(self) -> None:
        dlg = _ProductDialog(self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        try:
            services.add_product(**dlg.data())
            self.refresh()
        except Exception as e:
            QMessageBox.warning(self, "Hata", str(e))

    def _edit_product(self) -> None:
        pid = self._selected_id()
        if not pid:
            QMessageBox.information(self, "Seçim", "Düzenlemek için ürün seçin.")
            return
        product = services.get_product(pid)
        dlg = _ProductDialog(self, product)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        d = dlg.data()
        try:
            services.update_product(
                pid, name=d["name"], unit=d["unit"],
                unit_cost=d["unit_cost"], category=d["category"], notes=d["notes"],
            )
            self.refresh()
        except Exception as e:
            QMessageBox.warning(self, "Hata", str(e))

    def _movement(self, movement_type: str) -> None:
        products = services.list_products()
        if not products:
            QMessageBox.information(self, "Ürün yok", "Önce ürün ekleyin.")
            return
        dlg = _MovementDialog(self, products, movement_type)
        if self._selected_id():
            idx = dlg._product.findData(self._selected_id())
            if idx >= 0:
                dlg._product.setCurrentIndex(idx)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        p = dlg.payload()
        try:
            services.add_stock_movement(
                p["product_id"], p["movement_type"], p["quantity"],
                unit_cost=p["unit_cost"], unit_price=p["unit_price"],
                movement_date=p["movement_date"], note=p["note"],
            )
            self.refresh()
        except Exception as e:
            QMessageBox.warning(self, "Hata", str(e))

    def _delete_product(self) -> None:
        pid = self._selected_id()
        if not pid:
            QMessageBox.information(self, "Seçim", "Silmek için ürün seçin.")
            return
        if QMessageBox.question(
            self, "Sil", "Ürün ve hareket geçmişi silinsin mi?"
        ) != QMessageBox.StandardButton.Yes:
            return
        try:
            services.delete_product(pid)
            self.refresh()
        except Exception as e:
            QMessageBox.warning(self, "Hata", str(e))
