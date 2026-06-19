"""Sipariş gelir, maliyet ve kar/zarar raporları."""

from __future__ import annotations

import os
from datetime import timedelta
from decimal import Decimal, InvalidOperation

from django.contrib.auth.models import User
from django.utils import timezone

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from orders.models import Order

from onmer_admin_desktop.database import ensure_django


def _money(v) -> str:
    if v is None:
        return "0,00 ₺"
    if not isinstance(v, Decimal):
        v = Decimal(str(v))
    return f"{v:.2f} ₺"


def _pct(v: Decimal) -> str:
    return f"{v:.1f}%"


def _cost_ratio() -> Decimal:
    """Tahmini maliyet oranı (gelirin yüzdesi). Ortam: ONMER_COST_RATIO=0.55"""
    raw = os.environ.get("ONMER_COST_RATIO", "0.55")
    try:
        r = Decimal(raw)
        if r < 0 or r >= 1:
            raise InvalidOperation
        return r
    except (InvalidOperation, ValueError):
        return Decimal("0.55")


def _order_revenue(order: Order) -> Decimal:
    """İptal hariç tüm siparişler için tahmini gelir; iptal = 0."""
    if order.status == "cancelled":
        return Decimal("0")
    if order.estimated_price is not None:
        return order.estimated_price
    return order.items_total


def _finance_color(order: Order) -> QColor:
    if order.status == "completed":
        return QColor("#5cb85c")
    if order.status == "cancelled":
        return QColor("#c94c4c")
    return QColor("#e8a838")


def _finance_item(text: str, order: Order) -> QTableWidgetItem:
    it = _readonly_item(text)
    it.setForeground(_finance_color(order))
    return it


def _readonly_item(text: str) -> QTableWidgetItem:
    it = QTableWidgetItem(text)
    it.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
    return it


class ReportsPage(QWidget):
    def __init__(self, user: User) -> None:
        ensure_django()
        super().__init__()
        self._user = user
        self._cost_ratio = _cost_ratio()

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)

        title = QLabel("Raporlama")
        title.setObjectName("Title")
        root.addWidget(title)

        pct = int(self._cost_ratio * 100)
        hint = QLabel(
            f"Tüm siparişlerin gelir, maliyet ve kar marjı gösterilir. "
            f"Maliyet tahmini gelirin <b>%{pct}</b>’idir. "
            f"<span style='color:#5cb85c'>■</span> Tamamlandı · "
            f"<span style='color:#e8a838'>■</span> Bekleyen · "
            f"<span style='color:#c94c4c'>■</span> İptal"
        )
        hint.setObjectName("Muted")
        hint.setWordWrap(True)
        hint.setTextFormat(Qt.TextFormat.RichText)
        root.addWidget(hint)

        filt = QHBoxLayout()
        self._period = QComboBox()
        self._period.addItem("Son 7 gün", "7d")
        self._period.addItem("Son 30 gün", "30d")
        self._period.addItem("Bu ay", "month")
        self._period.addItem("Tüm zamanlar", "all")
        self._period.currentIndexChanged.connect(lambda _: self.refresh())
        idx_all = self._period.findData("all")
        if idx_all >= 0:
            self._period.blockSignals(True)
            self._period.setCurrentIndex(idx_all)
            self._period.blockSignals(False)
        self._status = QComboBox()
        self._status.addItem("Tüm siparişler", "")
        for val, lab in Order.STATUS_CHOICES:
            self._status.addItem(lab, val)
        self._status.currentIndexChanged.connect(lambda _: self.refresh())
        filt.addWidget(QLabel("Dönem:"))
        filt.addWidget(self._period)
        filt.addWidget(QLabel("Durum:"))
        filt.addWidget(self._status)
        filt.addStretch()
        root.addLayout(filt)

        kpi_box = QGroupBox("Özet")
        kpi_grid = QGridLayout(kpi_box)
        self._kpis: dict[str, QLabel] = {}
        for i, (key, lab) in enumerate(
            [
                ("orders", "Sipariş sayısı"),
                ("revenue", "Toplam gelir"),
                ("cost", "Tahmini maliyet"),
                ("profit", "Net kar"),
                ("margin", "Kar marjı"),
            ]
        ):
            lbl = QLabel(lab)
            lbl.setObjectName("Muted")
            val = QLabel("—")
            val.setObjectName("KpiValue")
            self._kpis[key] = val
            kpi_grid.addWidget(lbl, i // 3, (i % 3) * 2)
            kpi_grid.addWidget(val, i // 3, (i % 3) * 2 + 1)
        root.addWidget(kpi_box)

        self._table = QTableWidget(0, 9)
        self._table.setHorizontalHeaderLabels(
            [
                "#",
                "Sipariş tarihi",
                "Etkinlik tarihi",
                "Müşteri",
                "Durum",
                "Gelir",
                "Maliyet",
                "Kar",
                "Marj %",
            ]
        )
        self._table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        hdr = self._table.horizontalHeader()
        hdr.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        hdr.setStretchLastSection(False)
        root.addWidget(self._table, 1)

        self.refresh()

    def refresh(self) -> None:
        self._load_report()

    def _period_range(self):
        today = timezone.localdate()
        key = self._period.currentData()
        if key == "7d":
            return today - timedelta(days=6), today
        if key == "30d":
            return today - timedelta(days=29), today
        if key == "month":
            return today.replace(day=1), today
        return None, None

    def _load_report(self) -> None:
        start, end = self._period_range()
        status = self._status.currentData()

        qs = Order.objects.prefetch_related("items").all().order_by("created_at")
        if start and end:
            qs = qs.filter(created_at__date__gte=start, created_at__date__lte=end)
        if status:
            qs = qs.filter(status=status)

        orders = list(qs)
        ratio = self._cost_ratio

        total_rev = Decimal("0")
        total_cost = Decimal("0")
        total_profit = Decimal("0")
        completed_rev = Decimal("0")
        completed_profit = Decimal("0")

        self._table.setRowCount(0)
        for o in orders:
            rev = _order_revenue(o)
            cost = (rev * ratio).quantize(Decimal("0.01")) if rev else Decimal("0")
            profit = rev - cost
            if rev:
                margin = (profit / rev * Decimal("100")).quantize(Decimal("0.1"))
            else:
                margin = Decimal("0")

            total_rev += rev
            total_cost += cost
            total_profit += profit
            if o.status == "completed":
                completed_rev += rev
                completed_profit += profit

            row = self._table.rowCount()
            self._table.insertRow(row)
            self._table.setItem(row, 0, _readonly_item(str(o.pk)))
            self._table.setItem(
                row,
                1,
                _readonly_item(o.created_at.strftime("%d.%m.%Y")),
            )
            self._table.setItem(
                row,
                2,
                _readonly_item(o.event_date.strftime("%d.%m.%Y")),
            )
            self._table.setItem(row, 3, _readonly_item(o.full_name))
            self._table.setItem(
                row, 4, _readonly_item(str(o.get_status_display()))
            )
            self._table.setItem(row, 5, _readonly_item(_money(rev)))
            self._table.setItem(row, 6, _readonly_item(_money(cost)))
            self._table.setItem(row, 7, _finance_item(_money(profit), o))
            self._table.setItem(row, 8, _finance_item(_pct(margin), o))

        if completed_rev > 0:
            overall_margin = (
                completed_profit / completed_rev * Decimal("100")
            ).quantize(Decimal("0.1"))
        elif total_rev > 0:
            overall_margin = (total_profit / total_rev * Decimal("100")).quantize(
                Decimal("0.1")
            )
        else:
            overall_margin = Decimal("0")

        self._kpis["orders"].setText(str(len(orders)))
        self._kpis["revenue"].setText(_money(total_rev))
        self._kpis["cost"].setText(_money(total_cost))
        self._kpis["profit"].setText(_money(total_profit))
        self._kpis["margin"].setText(_pct(overall_margin))

        for col in range(self._table.columnCount()):
            self._table.resizeColumnToContents(col)
        hdr = self._table.horizontalHeader()
        hdr.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
