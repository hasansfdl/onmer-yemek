"""Yemek listesi — fiyat düzenleme ve aktif/pasif durumu tek sayfada."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from django.contrib.auth.models import User

from menu.models import Dish, MenuCategory

from onmer_admin_desktop.database import db_transaction, ensure_django


def _readonly_item(text: str) -> QTableWidgetItem:
    it = QTableWidgetItem(text)
    it.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
    return it


def _centered_cell_widget(widget: QWidget) -> QWidget:
    """Tablo hücresinde widget'ı dikey/yatay ortalar."""
    wrap = QWidget()
    lay = QHBoxLayout(wrap)
    lay.setContentsMargins(6, 0, 6, 0)
    lay.setSpacing(0)
    lay.addStretch()
    lay.addWidget(widget)
    lay.addStretch()
    return wrap


def _active_combo(active: bool, pk: int, on_change) -> QWidget:
    cb = QComboBox()
    cb.addItem("Evet", True)
    cb.addItem("Hayır", False)
    cb.setFixedWidth(96)
    cb.setFixedHeight(28)
    cb.blockSignals(True)
    cb.setCurrentIndex(0 if active else 1)
    cb.blockSignals(False)
    cb.currentIndexChanged.connect(
        lambda _idx, p=pk, c=cb: on_change(p, c)
    )
    return _centered_cell_widget(cb)


class FoodsPage(QWidget):
    def __init__(self, user: User) -> None:
        ensure_django()
        super().__init__()
        self._user = user
        v = QVBoxLayout(self)
        v.setContentsMargins(20, 20, 20, 20)

        t = QLabel("Yemekler & Fiyatlar")
        t.setObjectName("Title")
        v.addWidget(t)

        hint = QLabel(
            "Kişi başı fiyatları tabloda düzenleyip <b>Değişiklikleri kaydet</b> ile "
            "güncelleyin. <b>Aktif</b> sütunu anında kaydedilir: Evet olanlar toplu "
            "siparişe açıktır; Hayır olanlar sitede menüde görünür ancak "
            "<b>Şu an aktif değil</b> etiketiyle listelenir."
        )
        hint.setObjectName("Muted")
        hint.setWordWrap(True)
        hint.setTextFormat(Qt.TextFormat.RichText)
        v.addWidget(hint)

        filt = QHBoxLayout()
        filt.addWidget(QLabel("Kategori:"))
        self._cat = QComboBox()
        self._cat.addItem("Tümü", None)
        for c in MenuCategory.objects.order_by("order", "name"):
            self._cat.addItem(c.name, c.pk)
        self._cat.currentIndexChanged.connect(lambda _: self.refresh())
        filt.addWidget(self._cat)
        filt.addStretch()
        btn_save = QPushButton("Değişiklikleri kaydet")
        btn_save.setObjectName("Primary")
        btn_save.clicked.connect(self._save_prices)
        filt.addWidget(btn_save)
        v.addLayout(filt)

        self._tbl = QTableWidget(0, 5)
        self._tbl.setHorizontalHeaderLabels(
            ["ID", "Yemek", "Kategori", "Kişi başı ₺", "Aktif"]
        )
        self._tbl.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self._tbl.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._tbl.verticalHeader().setDefaultSectionSize(44)
        self._tbl.verticalHeader().setVisible(False)
        hdr = self._tbl.horizontalHeader()
        for col in range(4):
            hdr.setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self._tbl.setColumnWidth(4, 128)
        v.addWidget(self._tbl, 1)
        self.refresh()

    def refresh(self) -> None:
        cat_id = self._cat.currentData()
        qs = Dish.objects.select_related("category").order_by(
            "category__order", "category__name", "order", "name"
        )
        if cat_id:
            qs = qs.filter(category_id=cat_id)

        self._tbl.setRowCount(0)
        for d in qs:
            row = self._tbl.rowCount()
            self._tbl.insertRow(row)
            self._tbl.setItem(row, 0, _readonly_item(str(d.pk)))
            self._tbl.setItem(row, 1, _readonly_item(d.name))
            cat = d.category.name if d.category else "—"
            self._tbl.setItem(row, 2, _readonly_item(cat))

            pr = QTableWidgetItem(
                f"{d.price:.2f}" if d.price is not None else "0.00"
            )
            pr.setFlags(
                Qt.ItemFlag.ItemIsSelectable
                | Qt.ItemFlag.ItemIsEnabled
                | Qt.ItemFlag.ItemIsEditable
            )
            self._tbl.setItem(row, 3, pr)

            self._tbl.setCellWidget(
                row,
                4,
                _active_combo(d.is_active, d.pk, self._on_active_changed),
            )
            self._tbl.setRowHeight(row, 44)

        hdr = self._tbl.horizontalHeader()
        for c in (0, 2, 3):
            self._tbl.resizeColumnToContents(c)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self._tbl.setColumnWidth(4, 128)

    def _save_prices(self) -> None:
        rows: list[tuple[int, Decimal]] = []
        for r in range(self._tbl.rowCount()):
            pk_item = self._tbl.item(r, 0)
            pr_item = self._tbl.item(r, 3)
            if not pk_item or not pr_item:
                continue
            try:
                pk = int(pk_item.text())
                raw = pr_item.text().strip().replace(",", ".")
                val = Decimal(raw)
            except (ValueError, InvalidOperation):
                QMessageBox.warning(
                    self,
                    "Geçersiz fiyat",
                    f"Satır {r + 1} için sayısal fiyat girin.",
                )
                return
            if val < 0 or val > Decimal("999999.99"):
                QMessageBox.warning(self, "Aralık", "0–999999.99 arası girin.")
                return
            rows.append((pk, val))
        if not rows:
            return
        try:
            with db_transaction():
                for pk, val in rows:
                    Dish.objects.filter(pk=pk).update(price=val)
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))
            return
        QMessageBox.information(self, "Tamam", f"{len(rows)} fiyat güncellendi.")
        self.refresh()

    def _on_active_changed(self, pk: int, combo: QComboBox) -> None:
        raw = combo.currentData()
        if raw is None:
            return
        active = bool(raw)
        try:
            with db_transaction():
                Dish.objects.filter(pk=pk).update(is_active=active)
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))
            self.refresh()
