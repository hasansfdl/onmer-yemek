"""Personel, maaş ve ödeme geçmişi."""

from __future__ import annotations

import re
from datetime import date

from PyQt6.QtCore import QRegularExpression, Qt
from PyQt6.QtGui import QRegularExpressionValidator
from PyQt6.QtWidgets import (
    QCheckBox,
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
from onmer_stok_desktop.services import PAYMENT_TYPE_LABELS

EMPLOYEE_ROLES = ["Muhasebe", "Depo", "Aşçı", "Çalışan", "Şoför"]
_DATE_MIN = date(1940, 1, 1)


def _money(value: float) -> str:
    return f"₺{value:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _normalize_phone(value: str) -> str:
    return re.sub(r"\D", "", value.strip())


def _validate_employee_fields(
    full_name: str,
    phone: str,
    birth_date: str,
    role: str,
    monthly_salary: float,
    hire_date: str,
) -> str | None:
    full_name = full_name.strip()
    if not full_name:
        return "Ad soyad boş olamaz."
    if re.search(r"\d", full_name):
        return "Ad soyad alanına rakam girilemez."
    if not re.fullmatch(r"[A-Za-zÇçĞğİıÖöŞşÜü\s'\-]+", full_name):
        return "Ad soyad yalnızca harf içerebilir."

    if not role.strip():
        return "Görev / pozisyon seçilmelidir."

    if monthly_salary <= 0:
        return "Aylık maaş girilmelidir."

    digits = _normalize_phone(phone)
    if not digits:
        return "Telefon numarası girilmelidir."
    if len(digits) != 11:
        return "Telefon numarası 11 haneli olmalıdır."

    birth_date = birth_date.strip()
    if not birth_date:
        return "Doğum tarihi seçilmelidir."
    try:
        birth = date.fromisoformat(birth_date)
    except ValueError:
        return "Geçerli bir doğum tarihi girin."
    if birth > date.today():
        return "Doğum tarihi gelecekte olamaz."
    age = date.today().year - birth.year
    if (date.today().month, date.today().day) < (birth.month, birth.day):
        age -= 1
    if age < 18:
        return "Personel 18 yaşından küçüktür."

    hire_date = hire_date.strip()
    if not hire_date:
        return "İşe başlama tarihi seçilmelidir."
    try:
        hire = date.fromisoformat(hire_date)
    except ValueError:
        return "Geçerli bir işe başlama tarihi girin."
    if hire > date.today():
        return "İşe başlama tarihi gelecekte olamaz."
    if hire < birth:
        return "İşe başlama tarihi doğum tarihinden önce olamaz."

    return None


class _EmployeeDialog(QDialog):
    def __init__(self, parent=None, employee: dict | None = None):
        super().__init__(parent)
        self.setWindowTitle("Personel Düzenle" if employee else "Yeni Personel")
        self.setMinimumWidth(440)

        self._name = QLineEdit()
        self._name.setValidator(
            QRegularExpressionValidator(
                QRegularExpression(r"^[A-Za-zÇçĞğİıÖöŞşÜü\s'\-]*$")
            )
        )
        self._role = QComboBox()
        self._role.addItem("— Görev seçin —", "")
        for role_name in EMPLOYEE_ROLES:
            self._role.addItem(role_name, role_name)
        self._salary = QDoubleSpinBox()
        self._salary.setRange(0, 99_999_999)
        self._salary.setDecimals(0)
        self._salary.setPrefix("₺ ")
        self._salary.setGroupSeparatorShown(True)
        self._phone = QLineEdit()
        self._phone.setPlaceholderText("05xxxxxxxxx")
        self._phone.setMaxLength(11)
        self._phone.setValidator(
            QRegularExpressionValidator(QRegularExpression(r"^\d{0,11}$"))
        )
        self._birth = QDateEdit()
        self._birth.setCalendarPopup(True)
        self._birth.setDisplayFormat("dd.MM.yyyy")
        self._birth.setMaximumDate(date.today())
        self._birth.setMinimumDate(_DATE_MIN)
        self._hire = QDateEdit()
        self._hire.setCalendarPopup(True)
        self._hire.setDisplayFormat("dd.MM.yyyy")
        self._hire.setMaximumDate(date.today())
        self._hire.setMinimumDate(_DATE_MIN)
        self._notes = QTextEdit()
        self._notes.setMaximumHeight(70)
        self._active = QCheckBox("Aktif personel")
        self._active.setChecked(True)

        if employee:
            self._name.setText(employee["full_name"])
            saved_role = employee.get("role") or ""
            idx = self._role.findData(saved_role)
            if idx >= 0:
                self._role.setCurrentIndex(idx)
            elif saved_role:
                self._role.addItem(saved_role, saved_role)
                self._role.setCurrentIndex(self._role.count() - 1)
            self._salary.setValue(float(employee["monthly_salary"]))
            self._phone.setText(employee.get("phone") or "")
            if employee.get("birth_date"):
                parts = employee["birth_date"].split("-")
                if len(parts) == 3:
                    self._birth.setDate(date(int(parts[0]), int(parts[1]), int(parts[2])))
            else:
                self._birth.setDate(date.today().replace(year=date.today().year - 25))
            if employee.get("hire_date"):
                parts = employee["hire_date"].split("-")
                if len(parts) == 3:
                    self._hire.setDate(date(int(parts[0]), int(parts[1]), int(parts[2])))
            else:
                self._hire.setDate(date.today())
            self._notes.setPlainText(employee.get("notes") or "")
            self._active.setChecked(bool(employee.get("is_active")))
        else:
            self._birth.setDate(date.today().replace(year=date.today().year - 25))
            self._hire.setDate(date.today())

        form = QFormLayout()
        form.addRow("Ad Soyad *", self._name)
        form.addRow("Görev / Pozisyon *", self._role)
        form.addRow("Aylık maaş *", self._salary)
        form.addRow("Telefon *", self._phone)
        form.addRow("Doğum tarihi *", self._birth)
        form.addRow("İşe başlama *", self._hire)
        form.addRow("Not (isteğe bağlı)", self._notes)
        form.addRow("", self._active)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._try_accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)

    def _salary_value(self) -> float:
        return float(self._salary.value())

    def _date_value(self, widget: QDateEdit) -> str:
        return widget.date().toString("yyyy-MM-dd")

    def _try_accept(self) -> None:
        birth_date = self._date_value(self._birth)
        hire_date = self._date_value(self._hire)
        role = (self._role.currentData() or self._role.currentText()).strip()
        error = _validate_employee_fields(
            self._name.text(),
            self._phone.text(),
            birth_date,
            role,
            self._salary_value(),
            hire_date,
        )
        if error:
            QMessageBox.warning(self, "Geçersiz bilgi", error)
            return
        self.accept()

    def data(self) -> dict:
        return {
            "full_name": self._name.text().strip(),
            "role": (self._role.currentData() or self._role.currentText()).strip(),
            "monthly_salary": self._salary_value(),
            "phone": _normalize_phone(self._phone.text()),
            "birth_date": self._date_value(self._birth),
            "hire_date": self._date_value(self._hire),
            "notes": self._notes.toPlainText().strip(),
            "is_active": self._active.isChecked(),
        }


class _PaymentDialog(QDialog):
    def __init__(self, parent=None, employee: dict | None = None):
        super().__init__(parent)
        self.setWindowTitle("Ödeme Kaydı")
        self.setMinimumWidth(400)

        self._employee = QComboBox()
        for emp in services.list_employees():
            self._employee.addItem(emp["full_name"], emp["id"])
        if employee:
            idx = self._employee.findData(employee["id"])
            if idx >= 0:
                self._employee.setCurrentIndex(idx)

        self._ptype = QComboBox()
        for key, label in PAYMENT_TYPE_LABELS.items():
            self._ptype.addItem(label, key)
        self._amount = QDoubleSpinBox()
        self._amount.setRange(0, 99_999_999)
        self._amount.setDecimals(0)
        self._amount.setPrefix("₺ ")
        self._date = QDateEdit()
        self._date.setCalendarPopup(True)
        self._date.setDate(date.today())
        self._invoice = QLineEdit()
        self._invoice.setReadOnly(True)
        self._invoice.setText(services.next_payment_invoice_note())
        self._notes = QLineEdit()

        self._ptype.currentIndexChanged.connect(self._on_type_changed)
        self._employee.currentIndexChanged.connect(self._on_employee_changed)
        self._on_type_changed()
        self._on_employee_changed()

        form = QFormLayout()
        form.addRow("Personel *", self._employee)
        form.addRow("Ödeme türü", self._ptype)
        form.addRow("Tutar *", self._amount)
        form.addRow("Tarih", self._date)
        form.addRow("Fatura / Fiş (otomatik)", self._invoice)
        form.addRow("Not", self._notes)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)

    def _on_type_changed(self) -> None:
        is_salary = self._ptype.currentData() == "salary"
        self._amount.setEnabled(not is_salary)
        if is_salary:
            self._on_employee_changed()

    def _on_employee_changed(self) -> None:
        if self._ptype.currentData() != "salary":
            return
        emp_id = self._employee.currentData()
        employee = services.get_employee(emp_id) if emp_id else None
        if employee:
            self._amount.setValue(float(employee["monthly_salary"]))

    def data(self) -> dict:
        return {
            "employee_id": self._employee.currentData(),
            "payment_type": self._ptype.currentData(),
            "amount": self._amount.value(),
            "payment_date": self._date.date().toString("yyyy-MM-dd"),
            "invoice_note": "",
            "notes": self._notes.text().strip(),
        }


class _BulkSalaryDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Tüm Maaşları Öde")
        self._date = QDateEdit()
        self._date.setCalendarPopup(True)
        self._date.setDate(date.today())

        info2 = QLabel(
            f"Fiş numaraları otomatik verilir (sıradaki: {services.next_payment_invoice_note()})."
        )
        info2.setWordWrap(True)
        info2.setStyleSheet("color: #8b9cb3;")

        form = QFormLayout()
        form.addRow("Ödeme tarihi", self._date)

        info = QLabel(
            "Aktif personellerin aylık maaşları gider olarak kaydedilir. "
            "Aynı ay için daha önce maaş ödenmiş personeller atlanır."
        )
        info.setWordWrap(True)
        info.setStyleSheet("color: #8b9cb3;")

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(info)
        layout.addWidget(info2)
        layout.addLayout(form)
        layout.addWidget(buttons)

    def data(self) -> dict:
        return {
            "payment_date": self._date.date().toString("yyyy-MM-dd"),
            "invoice_note": "",
        }


class EmployeesPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        title = QLabel("Personel")
        title.setObjectName("PageTitle")

        self._summary = QLabel()
        self._summary.setStyleSheet("color: #8b9cb3; margin-bottom: 4px;")

        btn_row = QHBoxLayout()
        self._btn_add = QPushButton("Personel Ekle")
        self._btn_add.setObjectName("Primary")
        self._btn_edit = QPushButton("Düzenle")
        self._btn_pay = QPushButton("Ödeme Ekle")
        self._btn_pay_all = QPushButton("Tüm Maaşları Öde")
        self._btn_del_pay = QPushButton("Ödeme Sil")
        self._btn_del_pay.setObjectName("Danger")
        self._btn_del = QPushButton("Personel Sil")
        self._btn_del.setObjectName("Danger")
        self._btn_refresh = QPushButton("Yenile")
        for b in (
            self._btn_add, self._btn_edit, self._btn_pay, self._btn_pay_all,
            self._btn_del_pay, self._btn_del, self._btn_refresh,
        ):
            btn_row.addWidget(b)
        btn_row.addStretch()

        splitter = QSplitter(Qt.Orientation.Vertical)

        self._table = QTableWidget()
        self._table.setColumnCount(8)
        self._table.setHorizontalHeaderLabels(
            ["ID", "Ad Soyad", "Görev", "Aylık Maaş", "Telefon", "Doğum Tarihi", "Başlama", "Durum"]
        )
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.hideColumn(0)

        self._payments = QTableWidget()
        self._payments.setColumnCount(7)
        self._payments.setHorizontalHeaderLabels(
            ["ID", "Tarih", "Personel", "Tür", "Tutar", "Fatura / Fiş", "Not"]
        )
        self._payments.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self._payments.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._payments.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._payments.hideColumn(0)

        emp_wrap = QWidget()
        emp_layout = QVBoxLayout(emp_wrap)
        emp_layout.setContentsMargins(0, 0, 0, 0)
        emp_layout.addWidget(QLabel("Personel Listesi"))
        emp_layout.addWidget(self._table)

        pay_wrap = QWidget()
        pay_layout = QVBoxLayout(pay_wrap)
        pay_layout.setContentsMargins(0, 0, 0, 0)
        pay_layout.addWidget(QLabel("Ödeme Geçmişi"))
        pay_layout.addWidget(self._payments)

        splitter.addWidget(emp_wrap)
        splitter.addWidget(pay_wrap)

        layout = QVBoxLayout(self)
        layout.addWidget(title)
        layout.addWidget(self._summary)
        layout.addLayout(btn_row)
        layout.addWidget(splitter)

        self._btn_add.clicked.connect(self._add)
        self._btn_edit.clicked.connect(self._edit)
        self._btn_pay.clicked.connect(self._add_payment)
        self._btn_pay_all.clicked.connect(self._pay_all)
        self._btn_del_pay.clicked.connect(self._delete_payment)
        self._btn_del.clicked.connect(self._delete)
        self._btn_refresh.clicked.connect(self.refresh)
        self._table.itemSelectionChanged.connect(self._filter_payments)

    def set_permissions(
        self,
        *,
        can_edit_employees: bool = False,
        can_manage_payments: bool = False,
    ) -> None:
        for btn in (self._btn_add, self._btn_edit, self._btn_del):
            btn.setEnabled(can_edit_employees)
        for btn in (self._btn_pay, self._btn_pay_all, self._btn_del_pay):
            btn.setEnabled(can_manage_payments)

    def _selected_id(self) -> int | None:
        rows = self._table.selectionModel().selectedRows()
        if not rows:
            return None
        return int(self._table.item(rows[0].row(), 0).text())

    def _selected_payment_id(self) -> int | None:
        rows = self._payments.selectionModel().selectedRows()
        if not rows:
            return None
        return int(self._payments.item(rows[0].row(), 0).text())

    def refresh(self) -> None:
        employees = services.list_employees()
        summary = services.payroll_summary()
        self._summary.setText(
            f"Aktif personel: {int(summary['aktif_personel'])}  |  "
            f"Aylık toplam maaş: {_money(summary['aylik_maas_toplam'])}"
        )

        self._table.setRowCount(len(employees))
        for row, e in enumerate(employees):
            status = "Aktif" if e.get("is_active") else "Pasif"
            self._table.setItem(row, 0, QTableWidgetItem(str(e["id"])))
            self._table.setItem(row, 1, QTableWidgetItem(e["full_name"]))
            self._table.setItem(row, 2, QTableWidgetItem(e.get("role") or "—"))
            self._table.setItem(
                row, 3, QTableWidgetItem(_money(float(e["monthly_salary"])))
            )
            self._table.setItem(row, 4, QTableWidgetItem(e.get("phone") or "—"))
            self._table.setItem(row, 5, QTableWidgetItem(e.get("birth_date") or "—"))
            self._table.setItem(row, 6, QTableWidgetItem(e.get("hire_date") or "—"))
            item_status = QTableWidgetItem(status)
            if not e.get("is_active"):
                item_status.setForeground(Qt.GlobalColor.gray)
            self._table.setItem(row, 7, item_status)

        self._load_payments()

    def _filter_payments(self) -> None:
        self._load_payments(self._selected_id())

    def _load_payments(self, employee_id: int | None = None) -> None:
        payments = services.list_employee_payments(employee_id=employee_id)
        self._payments.setRowCount(len(payments))
        for row, p in enumerate(payments):
            self._payments.setItem(row, 0, QTableWidgetItem(str(p["id"])))
            self._payments.setItem(row, 1, QTableWidgetItem(p["payment_date"]))
            self._payments.setItem(row, 2, QTableWidgetItem(p["employee_name"]))
            self._payments.setItem(
                row, 3,
                QTableWidgetItem(PAYMENT_TYPE_LABELS.get(p["payment_type"], p["payment_type"])),
            )
            self._payments.setItem(row, 4, QTableWidgetItem(_money(float(p["amount"]))))
            self._payments.setItem(row, 5, QTableWidgetItem(p.get("invoice_note") or ""))
            self._payments.setItem(row, 6, QTableWidgetItem(p.get("notes") or ""))

    def _add(self) -> None:
        dlg = _EmployeeDialog(self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        d = dlg.data()
        try:
            services.add_employee(
                d["full_name"],
                role=d["role"],
                monthly_salary=d["monthly_salary"],
                phone=d["phone"],
                birth_date=d["birth_date"],
                hire_date=d["hire_date"],
                notes=d["notes"],
                is_active=d["is_active"],
            )
            self.refresh()
        except Exception as e:
            QMessageBox.warning(self, "Hata", str(e))

    def _edit(self) -> None:
        eid = self._selected_id()
        if not eid:
            QMessageBox.information(self, "Seçim", "Düzenlemek için personel seçin.")
            return
        employee = services.get_employee(eid)
        dlg = _EmployeeDialog(self, employee)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        d = dlg.data()
        try:
            services.update_employee(
                eid,
                full_name=d["full_name"],
                role=d["role"],
                monthly_salary=d["monthly_salary"],
                phone=d["phone"],
                birth_date=d["birth_date"],
                hire_date=d["hire_date"],
                notes=d["notes"],
                is_active=d["is_active"],
            )
            self.refresh()
        except Exception as e:
            QMessageBox.warning(self, "Hata", str(e))

    def _add_payment(self) -> None:
        employee = None
        eid = self._selected_id()
        if eid:
            employee = services.get_employee(eid)
        dlg = _PaymentDialog(self, employee)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        d = dlg.data()
        try:
            services.record_employee_payment(
                d["employee_id"], d["payment_type"], d["amount"],
                payment_date=d["payment_date"],
                invoice_note=d["invoice_note"], notes=d["notes"],
            )
            self.refresh()
        except Exception as e:
            QMessageBox.warning(self, "Hata", str(e))

    def _pay_all(self) -> None:
        dlg = _BulkSalaryDialog(self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        d = dlg.data()
        try:
            paid, errors = services.pay_all_salaries(
                payment_date=d["payment_date"],
                invoice_note=d["invoice_note"],
            )
            msg = f"{paid} personel için maaş gideri kaydedildi."
            if errors:
                msg += "\n\nAtlananlar:\n" + "\n".join(errors[:10])
            QMessageBox.information(self, "Tamamlandı", msg)
            self.refresh()
        except Exception as e:
            QMessageBox.warning(self, "Hata", str(e))

    def _delete_payment(self) -> None:
        pid = self._selected_payment_id()
        if not pid:
            QMessageBox.information(self, "Seçim", "Silmek için ödeme seçin.")
            return
        if QMessageBox.question(
            self, "Sil", "Ödeme ve bağlı gider kaydı silinsin mi?"
        ) != QMessageBox.StandardButton.Yes:
            return
        services.delete_employee_payment(pid)
        self.refresh()

    def _delete(self) -> None:
        eid = self._selected_id()
        if not eid:
            QMessageBox.information(self, "Seçim", "Silmek için personel seçin.")
            return
        if QMessageBox.question(
            self, "Sil", "Bu personel kaydı silinsin mi?"
        ) != QMessageBox.StandardButton.Yes:
            return
        services.delete_employee(employee_id=eid)
        self.refresh()
