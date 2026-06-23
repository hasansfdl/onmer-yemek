"""Kullanıcı yönetimi — yalnızca admin."""

from __future__ import annotations

from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
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

from onmer_stok_desktop import auth, services


class _UserDialog(QDialog):
    def __init__(self, parent=None, user: dict | None = None):
        super().__init__(parent)
        self._user = user
        self.setWindowTitle("Kullanıcı Düzenle" if user else "Yeni Kullanıcı")
        self.setMinimumWidth(380)

        self._username = QLineEdit()
        self._password = QLineEdit()
        self._password.setEchoMode(QLineEdit.EchoMode.Password)
        self._password.setPlaceholderText("En az 4 karakter")
        self._role = QComboBox()
        for key, label in auth.ASSIGNABLE_USER_ROLES.items():
            self._role.addItem(label, key)
        self._active = QCheckBox("Aktif")
        self._active.setChecked(True)

        if user:
            self._username.setText(user["username"])
            self._username.setReadOnly(True)
            idx = self._role.findData(user["role"])
            if idx >= 0:
                self._role.setCurrentIndex(idx)
            elif user["role"] in auth.ROLE_LABELS:
                self._role.addItem(auth.ROLE_LABELS[user["role"]], user["role"])
                self._role.setCurrentIndex(self._role.count() - 1)
            self._active.setChecked(bool(user["is_active"]))
            self._password.setPlaceholderText("Değiştirmek için yeni şifre girin")

        form = QFormLayout()
        form.addRow("Kullanıcı adı *", self._username)
        form.addRow("Şifre" + ("" if user else " *"), self._password)
        form.addRow("Rol", self._role)
        form.addRow("", self._active)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)

    def data(self) -> dict:
        return {
            "username": self._username.text().strip(),
            "password": self._password.text(),
            "role": self._role.currentData(),
            "is_active": self._active.isChecked(),
        }


class UsersPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        title = QLabel("Kullanıcılar")
        title.setObjectName("PageTitle")

        hint = QLabel(
            "Roller: Admin (tam erişim), Depo (stok), "
            "Muhasebe (gelir/gider + personel ödemeleri)"
        )
        hint.setStyleSheet("color: #8b9cb3; margin-bottom: 4px;")
        hint.setWordWrap(True)

        btn_row = QHBoxLayout()
        self._btn_add = QPushButton("Kullanıcı Ekle")
        self._btn_add.setObjectName("Primary")
        self._btn_edit = QPushButton("Düzenle")
        self._btn_del = QPushButton("Sil")
        self._btn_del.setObjectName("Danger")
        self._btn_refresh = QPushButton("Yenile")
        for b in (self._btn_add, self._btn_edit, self._btn_del, self._btn_refresh):
            btn_row.addWidget(b)
        btn_row.addStretch()

        self._table = QTableWidget()
        self._table.setColumnCount(5)
        self._table.setHorizontalHeaderLabels(
            ["ID", "Kullanıcı", "Rol", "Durum", "Oluşturulma"]
        )
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.hideColumn(0)

        layout = QVBoxLayout(self)
        layout.addWidget(title)
        layout.addWidget(hint)
        layout.addLayout(btn_row)
        layout.addWidget(self._table)

        self._btn_add.clicked.connect(self._add)
        self._btn_edit.clicked.connect(self._edit)
        self._btn_del.clicked.connect(self._delete)
        self._btn_refresh.clicked.connect(self.refresh)

    def _selected_id(self) -> int | None:
        rows = self._table.selectionModel().selectedRows()
        if not rows:
            return None
        return int(self._table.item(rows[0].row(), 0).text())

    def refresh(self) -> None:
        users = services.list_users()
        self._table.setRowCount(len(users))
        for row, user in enumerate(users):
            self._table.setItem(row, 0, QTableWidgetItem(str(user["id"])))
            self._table.setItem(row, 1, QTableWidgetItem(user["username"]))
            self._table.setItem(
                row, 2,
                QTableWidgetItem(auth.ROLE_LABELS.get(user["role"], user["role"])),
            )
            self._table.setItem(
                row, 3, QTableWidgetItem("Aktif" if user["is_active"] else "Pasif")
            )
            self._table.setItem(row, 4, QTableWidgetItem(user["created_at"]))

    def _add(self) -> None:
        dlg = _UserDialog(self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        d = dlg.data()
        if not d["password"]:
            QMessageBox.warning(self, "Hata", "Yeni kullanıcı için şifre gerekli.")
            return
        try:
            services.add_user(d["username"], d["password"], d["role"])
            self.refresh()
        except Exception as exc:
            QMessageBox.warning(self, "Hata", str(exc))

    def _edit(self) -> None:
        uid = self._selected_id()
        if not uid:
            QMessageBox.information(self, "Seçim", "Düzenlemek için kullanıcı seçin.")
            return
        users = {u["id"]: u for u in services.list_users()}
        user = users.get(uid)
        dlg = _UserDialog(self, user)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        d = dlg.data()
        try:
            services.update_user(
                uid,
                role=d["role"],
                is_active=d["is_active"],
                new_password=d["password"] or None,
            )
            self.refresh()
        except Exception as exc:
            QMessageBox.warning(self, "Hata", str(exc))

    def _delete(self) -> None:
        uid = self._selected_id()
        if not uid:
            QMessageBox.information(self, "Seçim", "Silmek için kullanıcı seçin.")
            return
        if QMessageBox.question(
            self, "Sil", "Kullanıcı silinsin mi?"
        ) != QMessageBox.StandardButton.Yes:
            return
        try:
            services.delete_user(uid)
            self.refresh()
        except Exception as exc:
            QMessageBox.warning(self, "Hata", str(exc))
