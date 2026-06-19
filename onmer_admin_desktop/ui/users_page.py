"""Site kullanıcıları ve yetkililer — Django User listesi."""

from __future__ import annotations

from PyQt6.QtCore import Qt
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
    QVBoxLayout,
    QWidget,
)

from django.contrib.auth.models import User
from django.db.models import Q

from accounts.models import Profile

from onmer_admin_desktop.database import db_transaction, ensure_django


def _readonly_item(text: str) -> QTableWidgetItem:
    it = QTableWidgetItem(text)
    it.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
    return it


def _role_label(u: User) -> str:
    if u.is_superuser:
        return "Süper kullanıcı"
    if u.is_staff:
        return "Personel (panel)"
    return "Müşteri"


def _display_name(u: User) -> str:
    full = u.get_full_name().strip()
    return full or "—"


class UsersPage(QWidget):
    def __init__(self, user: User) -> None:
        ensure_django()
        super().__init__()
        self._user = user
        self._selected_id: int | None = None

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)

        title = QLabel("Kullanıcı ve yetkiler")
        title.setObjectName("Title")
        root.addWidget(title)

        hint = QLabel(
            "Sitede kayıt olan ve giriş yapan tüm hesaplar burada listelenir. "
            "<b>Personel</b> işaretli kullanıcılar web admin ve masaüstü panele girebilir."
        )
        hint.setObjectName("Muted")
        hint.setWordWrap(True)
        hint.setTextFormat(Qt.TextFormat.RichText)
        root.addWidget(hint)

        self._summary = QLabel("")
        self._summary.setObjectName("Muted")
        root.addWidget(self._summary)

        filt = QHBoxLayout()
        self._role_f = QComboBox()
        self._role_f.addItem("Tümü", "all")
        self._role_f.addItem("Müşteriler", "site")
        self._role_f.addItem("Yetkililer (personel / süper)", "staff")
        self._role_f.currentIndexChanged.connect(lambda _: self._load_table())
        self._search = QLineEdit()
        self._search.setPlaceholderText("Ad, kullanıcı adı veya e-posta ara…")
        self._search.textChanged.connect(lambda _: self._load_table())
        filt.addWidget(QLabel("Grup:"))
        filt.addWidget(self._role_f)
        filt.addWidget(self._search, 1)
        btn_r = QPushButton("Yenile")
        btn_r.clicked.connect(self.refresh)
        filt.addWidget(btn_r)
        root.addLayout(filt)

        split = QSplitter(Qt.Orientation.Horizontal)

        self._table = QTableWidget(0, 6)
        self._table.setHorizontalHeaderLabels(
            ["ID", "Ad Soyad", "Kullanıcı adı", "E-posta", "Rol", "Son giriş"]
        )
        self._table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self._table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self._table.itemSelectionChanged.connect(self._on_select)
        self._configure_table_columns()
        split.addWidget(self._table)

        detail = QGroupBox("Hesap detayı")
        dv = QVBoxLayout(detail)
        self._detail_labels: dict[str, QLabel] = {}
        form = QFormLayout()
        for key, lab in [
            ("display_name", "Ad Soyad"),
            ("username", "Kullanıcı adı"),
            ("email", "E-posta"),
            ("role", "Rol"),
            ("phone", "Telefon"),
            ("company", "Firma"),
            ("date_joined", "Kayıt tarihi"),
            ("last_login", "Son giriş"),
            ("is_active", "Hesap aktif"),
        ]:
            w = QLabel("—")
            w.setWordWrap(True)
            w.setTextInteractionFlags(
                Qt.TextInteractionFlag.TextSelectableByMouse
            )
            self._detail_labels[key] = w
            form.addRow(lab, w)
        dv.addLayout(form)

        staff_row = QHBoxLayout()
        staff_row.addWidget(QLabel("Panel yetkisi (personel):"))
        self._staff_cb = QComboBox()
        self._staff_cb.addItem("Hayır", False)
        self._staff_cb.addItem("Evet", True)
        self._staff_cb.setEnabled(self._user.is_superuser)
        self._staff_cb.currentIndexChanged.connect(self._on_staff_changed)
        staff_row.addWidget(self._staff_cb, 1)
        dv.addLayout(staff_row)

        if not self._user.is_superuser:
            dv.addWidget(
                QLabel(
                    "Personel yetkisini yalnızca süper kullanıcılar değiştirebilir."
                )
            )

        split.addWidget(detail)
        split.setStretchFactor(0, 3)
        split.setStretchFactor(1, 1)
        root.addWidget(split, 1)

        self.refresh()

    def refresh(self) -> None:
        self._load_table()

    def _configure_table_columns(self) -> None:
        hdr = self._table.horizontalHeader()
        hdr.setStretchLastSection(False)
        hdr.setMinimumSectionSize(48)
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        self._table.setHorizontalScrollMode(
            QAbstractItemView.ScrollMode.ScrollPerPixel
        )

    def _fit_table_columns(self) -> None:
        for col in (0, 2, 4, 5):
            self._table.resizeColumnToContents(col)
        # Son giriş: "Henüz giriş yok" ve tarih tam görünsün
        last_w = max(self._table.columnWidth(5), 158)
        self._table.setColumnWidth(5, last_w)
        role_w = max(self._table.columnWidth(4), 118)
        self._table.setColumnWidth(4, role_w)

    def _load_table(self) -> None:
        text = self._search.text().strip().lower()
        role = self._role_f.currentData()

        qs = User.objects.all().order_by("pk")
        if role == "site":
            qs = qs.filter(is_staff=False, is_superuser=False)
        elif role == "staff":
            qs = qs.filter(Q(is_staff=True) | Q(is_superuser=True))

        site_count = User.objects.filter(is_staff=False, is_superuser=False).count()
        staff_count = User.objects.filter(
            Q(is_staff=True) | Q(is_superuser=True)
        ).count()

        self._table.blockSignals(True)
        self._table.setRowCount(0)

        shown = 0
        for u in qs:
            if text:
                blob = " ".join(
                    filter(
                        None,
                        [
                            u.username,
                            u.email,
                            u.first_name,
                            u.last_name,
                            u.get_full_name(),
                        ],
                    )
                ).lower()
                if text not in blob:
                    continue

            row = self._table.rowCount()
            self._table.insertRow(row)
            self._table.setItem(row, 0, _readonly_item(str(u.pk)))
            self._table.setItem(row, 1, _readonly_item(_display_name(u)))
            self._table.setItem(row, 2, _readonly_item(u.username))
            self._table.setItem(row, 3, _readonly_item(u.email or "—"))
            self._table.setItem(row, 4, _readonly_item(_role_label(u)))
            last = (
                u.last_login.strftime("%d.%m.%Y %H:%M")
                if u.last_login
                else "Henüz giriş yok"
            )
            self._table.setItem(row, 5, _readonly_item(last))
            shown += 1

        self._table.blockSignals(False)
        self._summary.setText(
            f"Toplam müşteri: <b>{site_count}</b> · "
            f"Yetkili: <b>{staff_count}</b> · "
            f"Listede: <b>{shown}</b>"
        )
        self._summary.setTextFormat(Qt.TextFormat.RichText)
        self._fit_table_columns()

    def _selected_user(self) -> User | None:
        rows = self._table.selectionModel().selectedRows()
        if not rows:
            return None
        pk_item = self._table.item(rows[0].row(), 0)
        if not pk_item:
            return None
        try:
            return User.objects.get(pk=int(pk_item.text()))
        except (User.DoesNotExist, ValueError):
            return None

    def _on_select(self) -> None:
        u = self._selected_user()
        self._selected_id = u.pk if u else None
        self._staff_cb.blockSignals(True)
        if u is None:
            for w in self._detail_labels.values():
                w.setText("—")
            self._staff_cb.setCurrentIndex(0)
        else:
            self._detail_labels["display_name"].setText(_display_name(u))
            self._detail_labels["username"].setText(u.username)
            self._detail_labels["email"].setText(u.email or "—")
            self._detail_labels["role"].setText(_role_label(u))
            profile = Profile.objects.filter(user=u).first()
            self._detail_labels["phone"].setText(
                profile.phone if profile and profile.phone else "—"
            )
            self._detail_labels["company"].setText(
                profile.company if profile and profile.company else "—"
            )
            self._detail_labels["date_joined"].setText(
                u.date_joined.strftime("%d.%m.%Y %H:%M")
            )
            self._detail_labels["last_login"].setText(
                u.last_login.strftime("%d.%m.%Y %H:%M")
                if u.last_login
                else "Henüz giriş yok"
            )
            self._detail_labels["is_active"].setText(
                "Evet" if u.is_active else "Hayır"
            )
            self._staff_cb.setCurrentIndex(1 if u.is_staff else 0)
            self._staff_cb.setEnabled(
                self._user.is_superuser and not u.is_superuser
            )
        self._staff_cb.blockSignals(False)

    def _on_staff_changed(self) -> None:
        u = self._selected_user()
        if u is None or not self._user.is_superuser:
            return
        if u.is_superuser:
            QMessageBox.information(
                self,
                "Yetki",
                "Süper kullanıcıların personel durumu buradan değiştirilmez.",
            )
            self._on_select()
            return
        if u.pk == self._user.pk:
            QMessageBox.warning(
                self,
                "Yetki",
                "Kendi hesabınızın personel yetkisini buradan kaldıramazsınız.",
            )
            self._on_select()
            return

        want_staff = bool(self._staff_cb.currentData())
        if want_staff == u.is_staff:
            return

        try:
            with db_transaction():
                User.objects.filter(pk=u.pk).update(is_staff=want_staff)
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))
            self._on_select()
            return

        self._load_table()
        self._on_select()
