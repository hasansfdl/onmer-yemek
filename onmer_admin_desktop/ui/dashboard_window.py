"""Dashboard — özet KPI kartları ve son kayıtlar."""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.db.models import Sum
from django.utils import timezone

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from menu.models import Dish
from orders.models import Order
from core.models import ContactMessage

from onmer_admin_desktop.database import ensure_django


def _money(v) -> str:
    if v is None:
        return "—"
    if isinstance(v, Decimal):
        return f"{v:.2f} ₺"
    return f"{v:.2f} ₺"


class _NumericIdItem(QTableWidgetItem):
    """# sütununda metin değil sayısal ID ile sıralama."""

    def __init__(self, pk: int) -> None:
        super().__init__(f"#{pk}")
        self.setData(Qt.ItemDataRole.UserRole, pk)
        self.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)

    def __lt__(self, other: QTableWidgetItem) -> bool:
        if other is None:
            return False
        a = self.data(Qt.ItemDataRole.UserRole)
        b = other.data(Qt.ItemDataRole.UserRole)
        if a is not None and b is not None:
            try:
                return int(a) < int(b)
            except (TypeError, ValueError):
                pass
        return super().__lt__(other)


def _readonly_item(text: str) -> QTableWidgetItem:
    it = QTableWidgetItem(text)
    it.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
    return it


class DashboardPage(QWidget):
    def __init__(self, user: User) -> None:
        ensure_django()
        super().__init__()
        self._user = user
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel("Genel Bakış")
        title.setObjectName("Title")
        layout.addWidget(title)

        self._grid = QGridLayout()
        self._grid.setSpacing(12)
        layout.addLayout(self._grid)

        self._cards = []
        for i in range(6):
            f = QFrame()
            f.setObjectName("Card")
            v = QVBoxLayout(f)
            v.setContentsMargins(14, 14, 14, 14)
            lbl = QLabel("")
            lbl.setObjectName("KpiLabel")
            val = QLabel("—")
            val.setObjectName("KpiValue")
            v.addWidget(lbl)
            v.addWidget(val)
            self._cards.append((lbl, val))
            self._grid.addWidget(f, i // 3, i % 3)

        mid = QHBoxLayout()
        self._tbl_orders = QTableWidget(0, 4)
        self._tbl_orders.setHorizontalHeaderLabels(
            ["Sipariş", "Müşteri", "Tarih", "Durum"]
        )
        self._tbl_orders.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._tbl_orders.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self._tbl_orders.setSortingEnabled(True)
        self._tbl_res = QTableWidget(0, 4)
        self._tbl_res.setHorizontalHeaderLabels(
            ["Mesaj", "Gönderen", "Tarih", "Durum"]
        )
        self._tbl_res.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._tbl_res.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self._tbl_res.setSortingEnabled(True)
        mid.addWidget(self._label_block("Son siparişler", self._tbl_orders))
        mid.addWidget(self._label_block("Son iletişim mesajları", self._tbl_res))
        layout.addLayout(mid, 1)

        self.refresh()

    def _label_block(self, text: str, table: QTableWidget) -> QWidget:
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(0, 0, 0, 0)
        t = QLabel(text)
        t.setObjectName("Muted")
        v.addWidget(t)
        v.addWidget(table, 1)
        return w

    def refresh(self) -> None:
        today = timezone.localdate()
        week_start = today - timedelta(days=6)

        total_orders = Order.objects.count()
        pending = Order.objects.filter(status__in=("new", "contacted")).count()
        pending_msgs = ContactMessage.objects.filter(reply_text="").count()

        day_rev = (
            Order.objects.filter(
                status="completed",
                updated_at__date=today,
            ).aggregate(s=Sum("estimated_price"))["s"]
            or 0
        )
        week_rev = (
            Order.objects.filter(
                status="completed",
                updated_at__date__gte=week_start,
                updated_at__date__lte=today,
            ).aggregate(s=Sum("estimated_price"))["s"]
            or 0
        )

        dish_active = Dish.objects.filter(is_active=True).count()
        dish_total = Dish.objects.count()

        labels_vals = [
            ("Toplam sipariş", str(total_orders)),
            ("Aksiyon bekleyen sipariş", str(pending)),
            ("Yanıt bekleyen mesaj", str(pending_msgs)),
            ("Bugünkü gelir (tamamlanan)", _money(day_rev)),
            ("Son 7 gün geliri", _money(week_rev)),
            ("Aktif / toplam yemek", f"{dish_active} / {dish_total}"),
        ]
        for i, (lb, val) in enumerate(labels_vals):
            self._cards[i][0].setText(lb)
            self._cards[i][1].setText(val)

        self._tbl_orders.setRowCount(0)
        self._tbl_orders.setSortingEnabled(False)
        for o in Order.objects.order_by("-pk")[:12]:
            row = self._tbl_orders.rowCount()
            self._tbl_orders.insertRow(row)
            when = (
                o.created_at.strftime("%d.%m.%Y %H:%M") if o.created_at else "—"
            )
            self._tbl_orders.setItem(row, 0, _NumericIdItem(o.pk))
            self._tbl_orders.setItem(row, 1, _readonly_item(o.full_name))
            self._tbl_orders.setItem(row, 2, _readonly_item(when))
            self._tbl_orders.setItem(
                row, 3, _readonly_item(o.get_status_display())
            )
        self._tbl_orders.setSortingEnabled(True)
        self._tbl_orders.sortItems(0, Qt.SortOrder.DescendingOrder)
        self._tbl_orders.resizeColumnsToContents()

        self._tbl_res.setRowCount(0)
        self._tbl_res.setSortingEnabled(False)
        for m in ContactMessage.objects.order_by("-pk")[:12]:
            row = self._tbl_res.rowCount()
            self._tbl_res.insertRow(row)
            self._tbl_res.setItem(row, 0, _NumericIdItem(m.pk))
            self._tbl_res.setItem(row, 1, _readonly_item(m.full_name))
            when = m.created_at.strftime("%d.%m.%Y %H:%M") if m.created_at else "—"
            self._tbl_res.setItem(row, 2, _readonly_item(when))
            if m.reply_text.strip():
                status = "Yanıtlandı"
            elif m.is_read:
                status = "Okundu"
            else:
                status = "Yeni"
            self._tbl_res.setItem(row, 3, _readonly_item(status))
        self._tbl_res.setSortingEnabled(True)
        self._tbl_res.sortItems(0, Qt.SortOrder.DescendingOrder)
        self._tbl_res.resizeColumnsToContents()
