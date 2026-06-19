"""Toplu sipariş yönetimi — liste, detay, durum, silme."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
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
    QFormLayout,
    QGroupBox,
)

from django.contrib.auth.models import User

from orders.models import Order

from onmer_admin_desktop.database import ensure_django, db_transaction


class OrdersPage(QWidget):
    def __init__(self, user: User) -> None:
        ensure_django()
        super().__init__()
        self._user = user
        self._current_id: int | None = None

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)

        title = QLabel("Sipariş Yönetimi")
        title.setObjectName("Title")
        root.addWidget(title)

        filt = QHBoxLayout()
        self._search = QLineEdit()
        self._search.setPlaceholderText("Ad, telefon veya e-posta ara…")
        self._search.textChanged.connect(lambda _: self._load_table())
        self._status_f = QComboBox()
        self._status_f.addItem("Tüm durumlar", "")
        for val, lab in Order.STATUS_CHOICES:
            self._status_f.addItem(lab, val)
        self._status_f.currentIndexChanged.connect(lambda _: self._load_table())
        filt.addWidget(QLabel("Durum:"))
        filt.addWidget(self._status_f)
        filt.addWidget(self._search, 1)
        btn_r = QPushButton("Yenile")
        btn_r.clicked.connect(self.refresh)
        filt.addWidget(btn_r)
        root.addLayout(filt)

        split = QSplitter(Qt.Orientation.Horizontal)
        self._table = QTableWidget(0, 6)
        self._table.setHorizontalHeaderLabels(
            ["#", "Müşteri", "Kişi", "Etkinlik", "Durum", "Tahmini ₺"]
        )
        self._table.itemSelectionChanged.connect(self._on_select)
        split.addWidget(self._table)

        detail = QGroupBox("Sipariş detayı")
        dv = QVBoxLayout(detail)
        self._detail_labels: dict[str, QLabel] = {}
        form = QFormLayout()
        for key, lab in [
            ("full_name", "Ad Soyad"),
            ("phone", "Telefon"),
            ("email", "E-posta"),
            ("organization_type", "Organizasyon"),
            ("guest_count", "Kişi sayısı"),
            ("created_at", "Sipariş tarihi"),
            ("event_date", "Etkinlik tarihi"),
            ("event_address", "Adres"),
            ("estimated_price", "Tahmini fiyat"),
            ("payment_status", "Ödeme"),
        ]:
            w = QLabel("—")
            w.setTextInteractionFlags(
                Qt.TextInteractionFlag.TextSelectableByMouse
            )
            self._detail_labels[key] = w
            form.addRow(lab, w)
        dv.addLayout(form)

        self._notes = QTextEdit()
        self._notes.setReadOnly(False)
        self._notes.setPlaceholderText("Özel notlar")
        dv.addWidget(QLabel("Özel notlar"))
        dv.addWidget(self._notes)

        self._status_edit = QComboBox()
        for val, lab in Order.STATUS_CHOICES:
            self._status_edit.addItem(lab, val)
        row_st = QHBoxLayout()
        row_st.addWidget(QLabel("Durum"))
        row_st.addWidget(self._status_edit, 1)

        btn_save = QPushButton("Kaydet")
        btn_save.setObjectName("Primary")
        btn_save.clicked.connect(self._save_order)
        btn_del = QPushButton("Sil")
        btn_del.setObjectName("Danger")
        btn_del.clicked.connect(self._delete_order)
        row_btn = QHBoxLayout()
        row_btn.addStretch()
        row_btn.addWidget(btn_save)
        row_btn.addWidget(btn_del)

        dv.addLayout(row_st)
        dv.addLayout(row_btn)
        split.addWidget(detail)
        split.setStretchFactor(0, 2)
        split.setStretchFactor(1, 1)
        root.addWidget(split, 1)

        self.refresh()

    def refresh(self) -> None:
        self._load_table()

    def _load_table(self) -> None:
        self._table.blockSignals(True)
        self._table.setRowCount(0)
        text = self._search.text().strip().lower()
        st = self._status_f.currentData()
        qs = Order.objects.all().order_by("-created_at")
        if st:
            qs = qs.filter(status=st)
        for o in qs:
            if text:
                blob = f"{o.full_name} {o.phone} {o.email}".lower()
                if text not in blob:
                    continue
            row = self._table.rowCount()
            self._table.insertRow(row)
            self._table.setItem(row, 0, QTableWidgetItem(str(o.pk)))
            self._table.setItem(row, 1, QTableWidgetItem(o.full_name))
            self._table.setItem(row, 2, QTableWidgetItem(str(o.guest_count)))
            self._table.setItem(
                row,
                3,
                QTableWidgetItem(
                    o.event_date.strftime("%d.%m.%Y") if o.event_date else ""
                ),
            )
            self._table.setItem(
                row, 4, QTableWidgetItem(o.get_status_display())
            )
            ep = o.estimated_price
            self._table.setItem(
                row,
                5,
                QTableWidgetItem(f"{ep:.2f}" if ep is not None else "—"),
            )
            self._table.item(row, 0).setData(Qt.ItemDataRole.UserRole, o.pk)
        self._table.resizeColumnsToContents()
        self._table.blockSignals(False)
        self._clear_detail()

    def _clear_detail(self) -> None:
        self._current_id = None
        for w in self._detail_labels.values():
            w.setText("—")
        self._notes.clear()

    def _on_select(self) -> None:
        items = self._table.selectedItems()
        if not items:
            self._clear_detail()
            return
        row = items[0].row()
        it = self._table.item(row, 0)
        if not it:
            return
        pk = it.data(Qt.ItemDataRole.UserRole)
        if not pk:
            return
        self._current_id = int(pk)
        self._show_order(self._current_id)

    def _show_order(self, pk: int) -> None:
        try:
            o = Order.objects.get(pk=pk)
        except Order.DoesNotExist:
            self._clear_detail()
            return
        od = Order.ORGANIZATION_TYPES
        org_map = dict(od)
        self._detail_labels["full_name"].setText(o.full_name)
        self._detail_labels["phone"].setText(o.phone)
        self._detail_labels["email"].setText(o.email)
        self._detail_labels["organization_type"].setText(
            org_map.get(o.organization_type, o.organization_type)
        )
        self._detail_labels["guest_count"].setText(str(o.guest_count))
        self._detail_labels["created_at"].setText(
            o.created_at.strftime("%d.%m.%Y %H:%M")
        )
        self._detail_labels["event_date"].setText(
            o.event_date.strftime("%d.%m.%Y") if o.event_date else "—"
        )
        if o.event_time:
            self._detail_labels["event_date"].setText(
                self._detail_labels["event_date"].text()
                + " "
                + o.event_time.strftime("%H:%M")
            )
        self._detail_labels["event_address"].setText(o.event_address or "—")
        ep = o.estimated_price
        self._detail_labels["estimated_price"].setText(
            f"{ep:.2f} ₺" if ep is not None else "—"
        )
        self._detail_labels["payment_status"].setText(
            o.get_payment_status_display()
        )
        self._notes.blockSignals(True)
        self._notes.setPlainText(o.notes or "")
        self._notes.blockSignals(False)

        idx = self._status_edit.findData(o.status)
        if idx >= 0:
            self._status_edit.setCurrentIndex(idx)

    def _save_order(self) -> None:
        if not self._current_id:
            return
        try:
            with db_transaction():
                o = Order.objects.select_for_update().get(pk=self._current_id)
                o.status = self._status_edit.currentData()
                o.notes = self._notes.toPlainText().strip()
                o.save(update_fields=["status", "notes", "updated_at"])
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))
            return
        QMessageBox.information(self, "Tamam", "Sipariş güncellendi.")
        self.refresh()
        self._show_order(self._current_id)

    def _delete_order(self) -> None:
        if not self._current_id:
            return
        if (
            QMessageBox.question(
                self,
                "Sil",
                f"Sipariş #{self._current_id} kalıcı olarak silinsin mi?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            != QMessageBox.StandardButton.Yes
        ):
            return
        try:
            Order.objects.filter(pk=self._current_id).delete()
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))
            return
        self._current_id = None
        self.refresh()
