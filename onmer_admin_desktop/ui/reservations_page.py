"""İletişim mesajları — siteden gelen talepler ve e-posta yanıtı."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QFormLayout,
    QGroupBox,
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

from django.contrib.auth.models import User

from core.contact_reply import send_contact_reply
from core.models import ContactMessage

from onmer_admin_desktop.database import db_transaction, ensure_django


def _readonly_item(text: str) -> QTableWidgetItem:
    it = QTableWidgetItem(text)
    it.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
    return it


def _status_label(msg: ContactMessage) -> str:
    if msg.is_replied:
        return "Yanıtlandı"
    if msg.is_read:
        return "Okundu"
    return "Yeni"


class ReservationsPage(QWidget):
    """Sol menüde «İletişim» — site iletişim formu mesajları."""

    def __init__(self, user: User) -> None:
        ensure_django()
        super().__init__()
        self._user = user
        self._current_id: int | None = None

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)

        title = QLabel("İletişim Mesajları")
        title.setObjectName("Title")
        root.addWidget(title)

        hint = QLabel(
            "Web sitesindeki iletişim formundan gelen mesajlar burada listelenir. "
            "Seçili mesaja e-posta ile yanıt gönderebilirsiniz."
        )
        hint.setObjectName("Muted")
        hint.setWordWrap(True)
        root.addWidget(hint)

        self._summary = QLabel("")
        self._summary.setObjectName("Muted")
        root.addWidget(self._summary)

        filt = QHBoxLayout()
        self._filter = QComboBox()
        self._filter.addItem("Tümü", "all")
        self._filter.addItem("Yanıt bekleyen", "pending")
        self._filter.addItem("Yanıtlandı", "replied")
        self._filter.currentIndexChanged.connect(lambda _: self._load_table())
        self._search = QLineEdit()
        self._search.setPlaceholderText("Ad, e-posta, konu veya mesaj ara…")
        self._search.textChanged.connect(lambda _: self._load_table())
        filt.addWidget(QLabel("Filtre:"))
        filt.addWidget(self._filter)
        filt.addWidget(self._search, 1)
        btn_r = QPushButton("Yenile")
        btn_r.clicked.connect(self.refresh)
        filt.addWidget(btn_r)
        root.addLayout(filt)

        split = QSplitter(Qt.Orientation.Horizontal)

        self._table = QTableWidget(0, 6)
        self._table.setHorizontalHeaderLabels(
            ["#", "Tarih", "Ad Soyad", "E-posta", "Konu", "Durum"]
        )
        self._table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self._table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self._table.itemSelectionChanged.connect(self._on_select)
        hdr = self._table.horizontalHeader()
        hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        hdr.setStretchLastSection(False)
        split.addWidget(self._table)

        box = QGroupBox("Mesaj detayı")
        dv = QVBoxLayout(box)
        form = QFormLayout()
        self._d_name = QLabel("—")
        self._d_email = QLabel("—")
        self._d_phone = QLabel("—")
        self._d_subject = QLabel("—")
        self._d_date = QLabel("—")
        self._d_status = QLabel("—")
        self._d_message = QTextEdit()
        self._d_message.setReadOnly(True)
        self._d_message.setMaximumHeight(120)
        self._d_prev_reply = QTextEdit()
        self._d_prev_reply.setReadOnly(True)
        self._d_prev_reply.setMaximumHeight(100)
        self._d_prev_reply.setPlaceholderText("Henüz yanıt yok.")
        self._reply = QTextEdit()
        self._reply.setPlaceholderText("Müşteriye gönderilecek yanıt metnini yazın…")
        self._reply.setMaximumHeight(120)

        for key, lab, w in [
            ("name", "Ad Soyad", self._d_name),
            ("email", "E-posta", self._d_email),
            ("phone", "Telefon", self._d_phone),
            ("subject", "Konu", self._d_subject),
            ("date", "Gönderim", self._d_date),
            ("status", "Durum", self._d_status),
        ]:
            w.setTextInteractionFlags(
                Qt.TextInteractionFlag.TextSelectableByMouse
            )
            w.setWordWrap(True)
            form.addRow(lab, w)
        form.addRow("Mesaj", self._d_message)
        form.addRow("Önceki yanıt", self._d_prev_reply)
        form.addRow("Yanıtınız", self._reply)
        dv.addLayout(form)

        row = QHBoxLayout()
        row.addStretch()
        btn_send = QPushButton("E-posta ile yanıtla")
        btn_send.setObjectName("Primary")
        btn_send.clicked.connect(self._send_reply)
        btn_del = QPushButton("Sil")
        btn_del.setObjectName("Danger")
        btn_del.clicked.connect(self._delete)
        row.addWidget(btn_send)
        row.addWidget(btn_del)
        dv.addLayout(row)
        split.addWidget(box)
        split.setStretchFactor(0, 3)
        split.setStretchFactor(1, 1)
        root.addWidget(split, 1)

        self.refresh()

    def refresh(self) -> None:
        self._load_table()

    def _load_table(self) -> None:
        keep_id = self._current_id
        text = self._search.text().strip().lower()
        flt = self._filter.currentData()

        qs = ContactMessage.objects.all().order_by("-created_at")
        if flt == "pending":
            qs = qs.filter(reply_text="")
        elif flt == "replied":
            qs = qs.exclude(reply_text="")

        self._table.blockSignals(True)
        self._table.setRowCount(0)
        shown = 0

        for m in qs:
            if text:
                blob = (
                    f"{m.full_name} {m.email} {m.phone} {m.subject} {m.message}"
                ).lower()
                if text not in blob:
                    continue

            row = self._table.rowCount()
            self._table.insertRow(row)
            self._table.setItem(row, 0, _readonly_item(str(m.pk)))
            when = m.created_at.strftime("%d.%m.%Y %H:%M") if m.created_at else "—"
            self._table.setItem(row, 1, _readonly_item(when))
            self._table.setItem(row, 2, _readonly_item(m.full_name))
            self._table.setItem(row, 3, _readonly_item(m.email))
            self._table.setItem(row, 4, _readonly_item(m.subject))
            st = _status_label(m)
            st_item = _readonly_item(st)
            if st == "Yeni":
                st_item.setForeground(QColor("#e8a838"))
            elif st == "Yanıtlandı":
                st_item.setForeground(QColor("#5cb85c"))
            self._table.setItem(row, 5, st_item)
            self._table.item(row, 0).setData(Qt.ItemDataRole.UserRole, m.pk)
            shown += 1

        self._table.blockSignals(False)

        total = ContactMessage.objects.count()
        pending = ContactMessage.objects.filter(reply_text="").count()
        self._summary.setText(
            f"Toplam mesaj: <b>{total}</b> · "
            f"Yanıt bekleyen: <b>{pending}</b> · "
            f"Listede: <b>{shown}</b>"
        )
        self._summary.setTextFormat(Qt.TextFormat.RichText)

        for col in (0, 1, 3, 5):
            self._table.resizeColumnToContents(col)

        if keep_id:
            self._select_row_by_id(keep_id)
        else:
            self._clear_form()

    def _select_row_by_id(self, pk: int) -> None:
        for row in range(self._table.rowCount()):
            it = self._table.item(row, 0)
            if it and it.data(Qt.ItemDataRole.UserRole) == pk:
                self._table.selectRow(row)
                self._load_detail(pk)
                return
        self._clear_form()

    def _clear_form(self) -> None:
        self._current_id = None
        for w in (
            self._d_name,
            self._d_email,
            self._d_phone,
            self._d_subject,
            self._d_date,
            self._d_status,
        ):
            w.setText("—")
        self._d_message.clear()
        self._d_prev_reply.clear()
        self._reply.clear()

    def _on_select(self) -> None:
        rows = self._table.selectionModel().selectedRows()
        if not rows:
            self._clear_form()
            return
        it = self._table.item(rows[0].row(), 0)
        if not it:
            return
        pk = it.data(Qt.ItemDataRole.UserRole)
        if not pk:
            return
        self._load_detail(int(pk))

    def _load_detail(self, pk: int) -> None:
        try:
            m = ContactMessage.objects.get(pk=pk)
        except ContactMessage.DoesNotExist:
            self._clear_form()
            return

        if not m.is_read:
            ContactMessage.objects.filter(pk=pk).update(is_read=True)
            m.is_read = True

        self._current_id = pk
        self._d_name.setText(m.full_name)
        self._d_email.setText(m.email)
        self._d_phone.setText(m.phone or "—")
        self._d_subject.setText(m.subject)
        self._d_date.setText(
            m.created_at.strftime("%d.%m.%Y %H:%M") if m.created_at else "—"
        )
        self._d_status.setText(_status_label(m))
        self._d_message.setPlainText(m.message)
        if m.reply_text.strip():
            replied = m.reply_text
            if m.replied_at:
                replied += f"\n\n— {m.replied_at.strftime('%d.%m.%Y %H:%M')}"
            self._d_prev_reply.setPlainText(replied)
        else:
            self._d_prev_reply.clear()
        self._reply.clear()

    def _send_reply(self) -> None:
        if not self._current_id:
            QMessageBox.warning(self, "Seçim", "Önce listeden bir mesaj seçin.")
            return
        body = self._reply.toPlainText().strip()
        if not body:
            QMessageBox.warning(self, "Yanıt", "Yanıt metni yazın.")
            return

        try:
            with db_transaction():
                m = ContactMessage.objects.get(pk=self._current_id)
                send_contact_reply(m, body, staff_user=self._user)
        except ContactMessage.DoesNotExist:
            QMessageBox.warning(self, "Mesaj", "Kayıt bulunamadı.")
            self.refresh()
            return
        except Exception as e:
            QMessageBox.critical(
                self,
                "E-posta",
                f"Yanıt gönderilemedi.\n\n{e}\n\n"
                "E-posta ayarlarını (SMTP / Gmail) kontrol edin.",
            )
            return

        QMessageBox.information(
            self,
            "Tamam",
            "Yanıt e-posta ile gönderildi ve kaydedildi.",
        )
        self.refresh()

    def _delete(self) -> None:
        if not self._current_id:
            return
        if (
            QMessageBox.question(
                self,
                "Sil",
                f"Mesaj #{self._current_id} silinsin mi?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            != QMessageBox.StandardButton.Yes
        ):
            return
        ContactMessage.objects.filter(pk=self._current_id).delete()
        self._current_id = None
        self.refresh()
