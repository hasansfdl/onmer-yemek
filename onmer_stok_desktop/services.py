"""Stok ve finans iş mantığı — yalnızca yerel SQLite."""

from __future__ import annotations

import calendar
import re
from datetime import date, datetime
from typing import Any

from .auth import ensure_default_admin, hash_password
from .database import connect, init_db, row_to_dict

INCOME_CATEGORIES = [
    "Yemek satışı",
    "Catering / toplu yemek",
    "Organizasyon",
    "Sözleşmeli gelir",
    "Diğer gelir",
]

EXPENSE_CATEGORIES = [
    "Malzeme",
    "Ambalaj",
    "Kira",
    "Elektrik/su/doğalgaz",
    "Yakıt",
    "Diğer gider",
]

DEFAULT_CATEGORIES = {
    "income": INCOME_CATEGORIES,
    "expense": EXPENSE_CATEGORIES,
    "product": ["Sebze", "Et", "Ambalaj", "İçecek", "Diğer"],
}

PAYMENT_TYPE_LABELS = {
    "salary": "Maaş",
    "advance": "Avans",
    "bonus": "Prim",
    "deduction": "Kesinti",
}


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _today() -> str:
    return date.today().isoformat()


def _normalize_phone(value: str) -> str:
    return re.sub(r"\D", "", value.strip())


def _parse_iso_date(value: str) -> date:
    return date.fromisoformat(value.strip())


def _age_on(birth: date, on: date | None = None) -> int:
    on = on or date.today()
    age = on.year - birth.year
    if (on.month, on.day) < (birth.month, birth.day):
        age -= 1
    return age


def _validate_birth_date(birth_date: str) -> date:
    birth_date = (birth_date or "").strip()
    if not birth_date:
        raise ValueError("Doğum tarihi girilmelidir.")
    try:
        birth = _parse_iso_date(birth_date)
    except ValueError:
        raise ValueError("Geçerli bir doğum tarihi girin.") from None
    if birth > date.today():
        raise ValueError("Doğum tarihi gelecekte olamaz.")
    if _age_on(birth) < 18:
        raise ValueError("Personel 18 yaşından küçüktür.")
    return birth


def _validate_employee_identity(full_name: str, phone: str, birth_date: str) -> date:
    full_name = full_name.strip()
    if not full_name:
        raise ValueError("Ad soyad boş olamaz.")
    if re.search(r"\d", full_name):
        raise ValueError("Ad soyad alanına rakam girilemez.")
    if not re.fullmatch(r"[A-Za-zÇçĞğİıÖöŞşÜü\s'\-]+", full_name):
        raise ValueError("Ad soyad yalnızca harf içerebilir.")

    digits = _normalize_phone(phone)
    if not digits:
        raise ValueError("Telefon numarası girilmelidir.")
    if len(digits) != 11:
        raise ValueError("Telefon numarası 11 haneli olmalıdır.")
    return _validate_birth_date(birth_date)


def _validate_employee_record(
    full_name: str,
    phone: str,
    birth_date: str,
    role: str,
    monthly_salary: float,
    hire_date: str | None,
) -> tuple[date, date]:
    birth = _validate_employee_identity(full_name, phone, birth_date)

    role = role.strip()
    if not role:
        raise ValueError("Görev / pozisyon seçilmelidir.")
    if monthly_salary <= 0:
        raise ValueError("Aylık maaş girilmelidir.")

    hire_date = (hire_date or "").strip()
    if not hire_date:
        raise ValueError("İşe başlama tarihi seçilmelidir.")
    try:
        hire = _parse_iso_date(hire_date)
    except ValueError:
        raise ValueError("Geçerli bir işe başlama tarihi girin.") from None
    if hire > date.today():
        raise ValueError("İşe başlama tarihi gelecekte olamaz.")
    if hire < birth:
        raise ValueError("İşe başlama tarihi doğum tarihinden önce olamaz.")

    return birth, hire


def _month_range(year: int, month: int) -> tuple[str, str]:
    last_day = calendar.monthrange(year, month)[1]
    return f"{year}-{month:02d}-01", f"{year}-{month:02d}-{last_day:02d}"


# ---------------------------------------------------------------------------
# Categories
# ---------------------------------------------------------------------------

def seed_default_categories() -> None:
    now = _now()
    with connect() as conn:
        for category_type, names in DEFAULT_CATEGORIES.items():
            for name in names:
                conn.execute(
                    """
                    INSERT OR IGNORE INTO categories (name, category_type, created_at)
                    VALUES (?, ?, ?)
                    """,
                    (name, category_type, now),
                )
        conn.commit()


def list_categories(category_type: str) -> list[str]:
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT name FROM categories
            WHERE category_type = ?
            ORDER BY name COLLATE NOCASE
            """,
            (category_type,),
        ).fetchall()
    return [row["name"] for row in rows]


def add_category(name: str, category_type: str) -> None:
    name = name.strip()
    if not name:
        raise ValueError("Kategori adı boş olamaz.")
    if category_type not in ("income", "expense", "product"):
        raise ValueError("Geçersiz kategori türü.")
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO categories (name, category_type, created_at)
            VALUES (?, ?, ?)
            """,
            (name, category_type, _now()),
        )
        conn.commit()


def delete_category(name: str, category_type: str) -> None:
    with connect() as conn:
        conn.execute(
            "DELETE FROM categories WHERE name = ? AND category_type = ?",
            (name.strip(), category_type),
        )
        conn.commit()


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------

def list_users() -> list[dict[str, Any]]:
    with connect() as conn:
        rows = conn.execute(
            "SELECT id, username, role, is_active, created_at FROM users ORDER BY username"
        ).fetchall()
    return [dict(r) for r in rows]


def add_user(username: str, password: str, role: str) -> int:
    username = username.strip()
    if not username:
        raise ValueError("Kullanıcı adı boş olamaz.")
    if len(password) < 4:
        raise ValueError("Şifre en az 4 karakter olmalıdır.")
    if role not in ("admin", "stock", "finance"):
        raise ValueError("Geçersiz rol.")
    with connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO users (username, password_hash, role, is_active, created_at)
            VALUES (?, ?, ?, 1, ?)
            """,
            (username, hash_password(password), role, _now()),
        )
        conn.commit()
        return int(cur.lastrowid)


def update_user(
    user_id: int,
    *,
    role: str,
    is_active: bool,
    new_password: str | None = None,
) -> None:
    if role not in ("admin", "stock", "finance", "viewer"):
        raise ValueError("Geçersiz rol.")
    with connect() as conn:
        if new_password:
            if len(new_password) < 4:
                raise ValueError("Şifre en az 4 karakter olmalıdır.")
            conn.execute(
                """
                UPDATE users SET role = ?, is_active = ?, password_hash = ?
                WHERE id = ?
                """,
                (role, 1 if is_active else 0, hash_password(new_password), user_id),
            )
        else:
            conn.execute(
                "UPDATE users SET role = ?, is_active = ? WHERE id = ?",
                (role, 1 if is_active else 0, user_id),
            )
        conn.commit()


def delete_user(user_id: int) -> None:
    with connect() as conn:
        admin_count = conn.execute(
            "SELECT COUNT(*) FROM users WHERE role = 'admin' AND is_active = 1"
        ).fetchone()[0]
        user = conn.execute(
            "SELECT role, is_active FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        if user and user["role"] == "admin" and user["is_active"] and admin_count <= 1:
            raise ValueError("Son aktif admin kullanıcı silinemez.")
        conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()


# ---------------------------------------------------------------------------
# Products
# ---------------------------------------------------------------------------

def list_products() -> list[dict[str, Any]]:
    with connect() as conn:
        rows = conn.execute(
            "SELECT * FROM products ORDER BY name COLLATE NOCASE"
        ).fetchall()
    return [dict(r) for r in rows]


def get_product(product_id: int) -> dict[str, Any] | None:
    with connect() as conn:
        row = conn.execute(
            "SELECT * FROM products WHERE id = ?", (product_id,)
        ).fetchone()
    return row_to_dict(row)


def add_product(
    name: str,
    unit: str = "adet",
    quantity: float = 0,
    unit_cost: float = 0,
    category: str = "",
    notes: str = "",
) -> int:
    name = name.strip()
    if not name:
        raise ValueError("Ürün adı boş olamaz.")
    if quantity < 0:
        raise ValueError("Stok miktarı negatif olamaz.")
    now = _now()
    entry_date = _today()
    with connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO products
            (name, unit, quantity, unit_cost, category, notes, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                name, unit.strip() or "adet", quantity, unit_cost,
                category.strip(), notes.strip(), now, now,
            ),
        )
        product_id = int(cur.lastrowid)
        if quantity > 0:
            conn.execute(
                """
                INSERT INTO stock_movements
                (product_id, movement_type, quantity, unit_cost, unit_price,
                 movement_date, note, created_at)
                VALUES (?, 'in', ?, ?, 0, ?, ?, ?)
                """,
                (product_id, quantity, unit_cost, entry_date, "İlk stok", now),
            )
        conn.commit()
        return product_id


def update_product(
    product_id: int,
    *,
    name: str,
    unit: str,
    unit_cost: float,
    category: str,
    notes: str,
) -> None:
    name = name.strip()
    if not name:
        raise ValueError("Ürün adı boş olamaz.")
    with connect() as conn:
        conn.execute(
            """
            UPDATE products
            SET name = ?, unit = ?, unit_cost = ?, category = ?, notes = ?, updated_at = ?
            WHERE id = ?
            """,
            (
                name, unit.strip() or "adet", unit_cost,
                category.strip(), notes.strip(), _now(), product_id,
            ),
        )
        conn.commit()


def delete_product(product_id: int) -> None:
    with connect() as conn:
        conn.execute("DELETE FROM products WHERE id = ?", (product_id,))
        conn.commit()


# ---------------------------------------------------------------------------
# Stock movements
# ---------------------------------------------------------------------------

def add_stock_movement(
    product_id: int,
    movement_type: str,
    quantity: float,
    *,
    unit_cost: float = 0,
    unit_price: float = 0,
    movement_date: str | None = None,
    note: str = "",
) -> None:
    if movement_type not in ("in", "out", "adjust"):
        raise ValueError("Geçersiz hareket türü.")
    if quantity <= 0 and movement_type != "adjust":
        raise ValueError("Miktar sıfırdan büyük olmalıdır.")
    movement_date = movement_date or _today()
    now = _now()

    with connect() as conn:
        product = conn.execute(
            "SELECT * FROM products WHERE id = ?", (product_id,)
        ).fetchone()
        if not product:
            raise ValueError("Ürün bulunamadı.")

        current_qty = float(product["quantity"])
        if movement_type == "in":
            new_qty = current_qty + quantity
            cost = unit_cost if unit_cost > 0 else float(product["unit_cost"])
        elif movement_type == "out":
            if quantity > current_qty:
                raise ValueError(
                    f"Yetersiz stok. Mevcut: {current_qty} {product['unit']}"
                )
            new_qty = current_qty - quantity
            cost = float(product["unit_cost"])
        else:
            new_qty = quantity
            cost = unit_cost if unit_cost > 0 else float(product["unit_cost"])

        conn.execute(
            """
            INSERT INTO stock_movements
            (product_id, movement_type, quantity, unit_cost, unit_price,
             movement_date, note, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                product_id, movement_type, quantity, cost, unit_price,
                movement_date, note.strip(), now,
            ),
        )
        conn.execute(
            "UPDATE products SET quantity = ?, unit_cost = ?, updated_at = ? WHERE id = ?",
            (new_qty, cost if movement_type == "in" else float(product["unit_cost"]), now, product_id),
        )
        if movement_type == "in" and unit_cost > 0:
            conn.execute(
                "UPDATE products SET unit_cost = ? WHERE id = ?",
                (unit_cost, product_id),
            )
        conn.commit()


def list_stock_movements(limit: int = 200) -> list[dict[str, Any]]:
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT m.*, p.name AS product_name, p.unit AS product_unit
            FROM stock_movements m
            JOIN products p ON p.id = m.product_id
            ORDER BY m.movement_date DESC, m.id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Finance entries
# ---------------------------------------------------------------------------

def add_finance_entry(
    entry_type: str,
    amount: float,
    *,
    category: str = "",
    description: str = "",
    invoice_note: str = "",
    entry_date: str | None = None,
    employee_payment_id: int | None = None,
) -> int:
    if entry_type not in ("income", "expense"):
        raise ValueError("Gelir veya gider seçin.")
    if amount <= 0:
        raise ValueError("Tutar sıfırdan büyük olmalıdır.")
    description = description.strip()
    category = category.strip()
    if entry_type == "income" and not employee_payment_id:
        if category not in INCOME_CATEGORIES:
            raise ValueError("Gelir kategorisi seçilmelidir.")
    if entry_type == "expense" and not employee_payment_id:
        if category not in EXPENSE_CATEGORIES:
            raise ValueError("Gider kategorisi seçilmelidir.")
    entry_date = entry_date or _today()
    now = _now()
    with connect() as conn:
        invoice_note = invoice_note.strip()
        if not invoice_note and not employee_payment_id:
            invoice_note = _format_finance_invoice_note(
                _max_finance_invoice_sequence(conn) + 1
            )
        cur = conn.execute(
            """
            INSERT INTO finance_entries
            (entry_type, amount, category, description, invoice_note,
             entry_date, employee_payment_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                entry_type, amount, category.strip(), description,
                invoice_note, entry_date, employee_payment_id, now,
            ),
        )
        conn.commit()
        return int(cur.lastrowid)


def list_finance_entries(limit: int = 200) -> list[dict[str, Any]]:
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT * FROM finance_entries
            WHERE employee_payment_id IS NULL
            ORDER BY entry_date DESC, id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [dict(r) for r in rows]


def get_finance_entry(entry_id: int) -> dict[str, Any] | None:
    with connect() as conn:
        row = conn.execute(
            "SELECT * FROM finance_entries WHERE id = ?", (entry_id,)
        ).fetchone()
    return row_to_dict(row)


def update_finance_entry(
    entry_id: int,
    *,
    amount: float,
    description: str,
    entry_date: str | None = None,
    category: str = "",
) -> None:
    if amount <= 0:
        raise ValueError("Tutar sıfırdan büyük olmalıdır.")
    description = description.strip()
    entry_date = entry_date or _today()
    category = category.strip()
    with connect() as conn:
        row = conn.execute(
            "SELECT * FROM finance_entries WHERE id = ?", (entry_id,)
        ).fetchone()
        if not row:
            raise ValueError("Kayıt bulunamadı.")
        if row["employee_payment_id"]:
            raise ValueError("Personel ödemeleri bu ekrandan düzenlenemez.")
        if row["entry_type"] == "income" and category not in INCOME_CATEGORIES:
            raise ValueError("Gelir kategorisi seçilmelidir.")
        if row["entry_type"] == "expense" and category not in EXPENSE_CATEGORIES:
            raise ValueError("Gider kategorisi seçilmelidir.")
        conn.execute(
            """
            UPDATE finance_entries
            SET amount = ?, description = ?, entry_date = ?, category = ?
            WHERE id = ?
            """,
            (amount, description, entry_date, category, entry_id),
        )
        conn.commit()


def delete_finance_entry(entry_id: int) -> None:
    with connect() as conn:
        row = conn.execute(
            "SELECT employee_payment_id FROM finance_entries WHERE id = ?", (entry_id,)
        ).fetchone()
        if row and row["employee_payment_id"]:
            conn.execute(
                "DELETE FROM employee_payments WHERE id = ?",
                (row["employee_payment_id"],),
            )
        conn.execute("DELETE FROM finance_entries WHERE id = ?", (entry_id,))
        conn.commit()


# ---------------------------------------------------------------------------
# Employees
# ---------------------------------------------------------------------------

def list_employees(active_only: bool = False) -> list[dict[str, Any]]:
    with connect() as conn:
        sql = "SELECT * FROM employees"
        if active_only:
            sql += " WHERE is_active = 1"
        sql += " ORDER BY full_name COLLATE NOCASE"
        rows = conn.execute(sql).fetchall()
    return [dict(r) for r in rows]


def get_employee(employee_id: int) -> dict[str, Any] | None:
    with connect() as conn:
        row = conn.execute(
            "SELECT * FROM employees WHERE id = ?", (employee_id,)
        ).fetchone()
    return row_to_dict(row)


def add_employee(
    full_name: str,
    *,
    role: str = "",
    monthly_salary: float = 0,
    phone: str = "",
    birth_date: str = "",
    hire_date: str | None = None,
    notes: str = "",
    is_active: bool = True,
) -> int:
    full_name = full_name.strip()
    birth, hire = _validate_employee_record(
        full_name, phone, birth_date, role, monthly_salary, hire_date,
    )
    phone = _normalize_phone(phone)
    birth_date = birth.isoformat()
    hire_date = hire.isoformat()
    now = _now()
    with connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO employees
            (full_name, role, monthly_salary, phone, birth_date, hire_date, notes,
             is_active, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                full_name, role.strip(), monthly_salary, phone, birth_date,
                hire_date, notes.strip(), 1 if is_active else 0,
                now, now,
            ),
        )
        conn.commit()
        return int(cur.lastrowid)


def update_employee(
    employee_id: int,
    *,
    full_name: str,
    role: str,
    monthly_salary: float,
    phone: str,
    birth_date: str,
    hire_date: str | None,
    notes: str,
    is_active: bool,
) -> None:
    full_name = full_name.strip()
    birth, hire = _validate_employee_record(
        full_name, phone, birth_date, role, monthly_salary, hire_date,
    )
    phone = _normalize_phone(phone)
    birth_date = birth.isoformat()
    hire_date = hire.isoformat()
    with connect() as conn:
        conn.execute(
            """
            UPDATE employees
            SET full_name = ?, role = ?, monthly_salary = ?, phone = ?,
                birth_date = ?, hire_date = ?, notes = ?, is_active = ?, updated_at = ?
            WHERE id = ?
            """,
            (
                full_name, role.strip(), monthly_salary, phone, birth_date,
                hire_date, notes.strip(), 1 if is_active else 0,
                _now(), employee_id,
            ),
        )
        conn.commit()


def delete_employee(employee_id: int) -> None:
    with connect() as conn:
        conn.execute("DELETE FROM employees WHERE id = ?", (employee_id,))
        conn.commit()


def payroll_summary() -> dict[str, float]:
    with connect() as conn:
        row = conn.execute(
            """
            SELECT
                COUNT(*) AS total,
                COALESCE(SUM(CASE WHEN is_active = 1 THEN 1 ELSE 0 END), 0) AS active,
                COALESCE(SUM(CASE WHEN is_active = 1 THEN monthly_salary ELSE 0 END), 0) AS payroll
            FROM employees
            """
        ).fetchone()
    return {
        "personel_sayisi": float(row["total"]),
        "aktif_personel": float(row["active"]),
        "aylik_maas_toplam": float(row["payroll"]),
    }


# ---------------------------------------------------------------------------
# Employee payments
# ---------------------------------------------------------------------------

def _invoice_sequence_number(note: str) -> int | None:
    note = (note or "").strip()
    if not note:
        return None
    if note.isdigit():
        return int(note)
    match = re.search(r"(\d+)$", note)
    if match:
        return int(match.group(1))
    return None


def _format_payment_invoice_note(number: int) -> str:
    return f"FIS-{number:04d}"


def _format_finance_invoice_note(number: int) -> str:
    return f"FTR-{number:04d}"


def _max_payment_invoice_sequence(conn) -> int:
    max_num = 0
    rows = conn.execute(
        "SELECT invoice_note FROM employee_payments WHERE invoice_note != ''"
    ).fetchall()
    for row in rows:
        seq = _invoice_sequence_number(row["invoice_note"])
        if seq is not None and seq > max_num:
            max_num = seq
    return max_num


def _max_finance_invoice_sequence(conn) -> int:
    max_num = 0
    rows = conn.execute(
        """
        SELECT invoice_note FROM finance_entries
        WHERE invoice_note != '' AND employee_payment_id IS NULL
        """
    ).fetchall()
    for row in rows:
        seq = _invoice_sequence_number(row["invoice_note"])
        if seq is not None and seq > max_num:
            max_num = seq
    return max_num


def next_payment_invoice_note() -> str:
    """Bir sonraki personel fiş numarası (önizleme)."""
    with connect() as conn:
        return _format_payment_invoice_note(_max_payment_invoice_sequence(conn) + 1)


def next_finance_invoice_note() -> str:
    """Bir sonraki gelir/gider fiş numarası (önizleme)."""
    with connect() as conn:
        return _format_finance_invoice_note(_max_finance_invoice_sequence(conn) + 1)


def _invoice_matches_search(invoice_note: str, search: str) -> bool:
    search = search.strip()
    if not search:
        return True
    note = (invoice_note or "").strip()
    if not note:
        return False
    if search.isdigit():
        seq = _invoice_sequence_number(note)
        if seq is None:
            return False
        if seq == int(search):
            return True
        padded = f"{seq:04d}"
        return padded.endswith(search) or search in padded
    return search.lower() in note.lower()


def _salary_paid_in_month(conn, employee_id: int, year_month: str) -> bool:
    row = conn.execute(
        """
        SELECT 1 FROM employee_payments
        WHERE employee_id = ? AND payment_type = 'salary'
          AND substr(payment_date, 1, 7) = ?
        LIMIT 1
        """,
        (employee_id, year_month),
    ).fetchone()
    return row is not None


def record_employee_payment(
    employee_id: int,
    payment_type: str,
    amount: float,
    *,
    payment_date: str | None = None,
    invoice_note: str = "",
    notes: str = "",
    skip_expense: bool = False,
) -> int:
    if payment_type not in PAYMENT_TYPE_LABELS:
        raise ValueError("Geçersiz ödeme türü.")
    if amount <= 0:
        raise ValueError("Tutar sıfırdan büyük olmalıdır.")
    payment_date = payment_date or _today()
    now = _now()

    with connect() as conn:
        employee = conn.execute(
            "SELECT * FROM employees WHERE id = ?", (employee_id,)
        ).fetchone()
        if not employee:
            raise ValueError("Personel bulunamadı.")

        year_month = payment_date[:7]
        if payment_type == "salary" and _salary_paid_in_month(conn, employee_id, year_month):
            raise ValueError(
                f"{employee['full_name']} için {year_month} ayında maaş zaten kayıtlı."
            )

        invoice_note = invoice_note.strip()
        if not invoice_note:
            invoice_note = _format_payment_invoice_note(
                _max_payment_invoice_sequence(conn) + 1
            )

        finance_entry_id = None
        if not skip_expense and payment_type in ("salary", "advance", "bonus"):
            label = PAYMENT_TYPE_LABELS[payment_type]
            desc = f"{label} — {employee['full_name']}"
            cur = conn.execute(
                """
                INSERT INTO finance_entries
                (entry_type, amount, category, description, invoice_note,
                 entry_date, employee_payment_id, created_at)
                VALUES ('expense', ?, 'Personel', ?, ?, ?, NULL, ?)
                """,
                (amount, desc, invoice_note, payment_date, now),
            )
            finance_entry_id = int(cur.lastrowid)
        elif not skip_expense and payment_type == "deduction":
            label = PAYMENT_TYPE_LABELS[payment_type]
            desc = f"{label} — {employee['full_name']}"
            cur = conn.execute(
                """
                INSERT INTO finance_entries
                (entry_type, amount, category, description, invoice_note,
                 entry_date, employee_payment_id, created_at)
                VALUES ('income', ?, 'Personel', ?, ?, ?, NULL, ?)
                """,
                (amount, desc, invoice_note, payment_date, now),
            )
            finance_entry_id = int(cur.lastrowid)

        cur = conn.execute(
            """
            INSERT INTO employee_payments
            (employee_id, payment_type, amount, payment_date,
             invoice_note, notes, finance_entry_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                employee_id, payment_type, amount, payment_date,
                invoice_note.strip(), notes.strip(), finance_entry_id, now,
            ),
        )
        payment_id = int(cur.lastrowid)

        if finance_entry_id:
            conn.execute(
                "UPDATE finance_entries SET employee_payment_id = ? WHERE id = ?",
                (payment_id, finance_entry_id),
            )

        conn.commit()
        return payment_id


def pay_employee_salary(
    employee_id: int,
    *,
    payment_date: str | None = None,
    invoice_note: str = "",
    notes: str = "",
) -> int:
    employee = get_employee(employee_id)
    if not employee:
        raise ValueError("Personel bulunamadı.")
    amount = float(employee["monthly_salary"])
    if amount <= 0:
        raise ValueError("Personelin aylık maaşı tanımlı değil.")
    return record_employee_payment(
        employee_id, "salary", amount,
        payment_date=payment_date, invoice_note=invoice_note, notes=notes,
    )


def pay_all_salaries(
    *,
    payment_date: str | None = None,
    invoice_note: str = "",
) -> tuple[int, list[str]]:
    payment_date = payment_date or _today()
    year_month = payment_date[:7]
    paid = 0
    errors: list[str] = []
    for employee in list_employees(active_only=True):
        if float(employee["monthly_salary"]) <= 0:
            continue
        try:
            pay_employee_salary(
                employee["id"],
                payment_date=payment_date,
                invoice_note=invoice_note,
            )
            paid += 1
        except ValueError as exc:
            if "zaten kayıtlı" in str(exc):
                errors.append(str(exc))
            else:
                errors.append(f"{employee['full_name']}: {exc}")
    if paid == 0 and not errors:
        raise ValueError("Ödenecek aktif personel bulunamadı.")
    return paid, errors


def list_employee_payments(
    employee_id: int | None = None,
    limit: int = 300,
) -> list[dict[str, Any]]:
    with connect() as conn:
        sql = """
            SELECT p.*, e.full_name AS employee_name
            FROM employee_payments p
            JOIN employees e ON e.id = p.employee_id
        """
        params: list[Any] = []
        if employee_id:
            sql += " WHERE p.employee_id = ?"
            params.append(employee_id)
        sql += " ORDER BY p.payment_date DESC, p.id DESC LIMIT ?"
        params.append(limit)
        rows = conn.execute(sql, params).fetchall()
    return [dict(r) for r in rows]


def delete_employee_payment(payment_id: int) -> None:
    with connect() as conn:
        row = conn.execute(
            "SELECT finance_entry_id FROM employee_payments WHERE id = ?",
            (payment_id,),
        ).fetchone()
        if row and row["finance_entry_id"]:
            conn.execute(
                "DELETE FROM finance_entries WHERE id = ?",
                (row["finance_entry_id"],),
            )
        conn.execute("DELETE FROM employee_payments WHERE id = ?", (payment_id,))
        conn.commit()


def list_payment_invoices(
    *,
    payment_type: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    invoice_search: str = "",
    employee_name: str = "",
    limit: int = 500,
) -> list[dict[str, Any]]:
    with connect() as conn:
        sql = """
            SELECT p.*, e.full_name AS employee_name
            FROM employee_payments p
            JOIN employees e ON e.id = p.employee_id
            WHERE 1=1
        """
        params: list[Any] = []
        if payment_type:
            sql += " AND p.payment_type = ?"
            params.append(payment_type)
        if date_from:
            sql += " AND p.payment_date >= ?"
            params.append(date_from)
        if date_to:
            sql += " AND p.payment_date <= ?"
            params.append(date_to)
        if employee_name.strip():
            sql += " AND e.full_name LIKE ?"
            params.append(f"%{employee_name.strip()}%")
        sql += " ORDER BY p.payment_date DESC, p.id DESC LIMIT ?"
        params.append(limit)
        rows = conn.execute(sql, params).fetchall()

    results = [dict(r) for r in rows]
    if invoice_search.strip():
        results = [
            r for r in results
            if _invoice_matches_search(r.get("invoice_note", ""), invoice_search)
        ]
    return results


def list_finance_invoices(
    *,
    entry_type: str | None = None,
    category: str = "",
    date_from: str | None = None,
    date_to: str | None = None,
    invoice_search: str = "",
    limit: int = 500,
) -> list[dict[str, Any]]:
    with connect() as conn:
        sql = """
            SELECT * FROM finance_entries
            WHERE employee_payment_id IS NULL
        """
        params: list[Any] = []
        if entry_type:
            sql += " AND entry_type = ?"
            params.append(entry_type)
        if category.strip():
            sql += " AND category LIKE ?"
            params.append(f"%{category.strip()}%")
        if date_from:
            sql += " AND entry_date >= ?"
            params.append(date_from)
        if date_to:
            sql += " AND entry_date <= ?"
            params.append(date_to)
        sql += " ORDER BY entry_date DESC, id DESC LIMIT ?"
        params.append(limit)
        rows = conn.execute(sql, params).fetchall()

    results = [dict(r) for r in rows]
    if invoice_search.strip():
        results = [
            r for r in results
            if _invoice_matches_search(r.get("invoice_note", ""), invoice_search)
        ]
    return results


# ---------------------------------------------------------------------------
# Dashboard / reports / charts
# ---------------------------------------------------------------------------

def dashboard_summary(
    date_from: str | None = None,
    date_to: str | None = None,
) -> dict[str, float]:
    """Ciro, maliyet, gider ve kar özeti."""
    date_from = date_from or "1970-01-01"
    date_to = date_to or "9999-12-31"

    with connect() as conn:
        stock_sales = conn.execute(
            """
            SELECT COALESCE(SUM(
                quantity * CASE WHEN unit_price > 0 THEN unit_price ELSE unit_cost END
            ), 0)
            FROM stock_movements
            WHERE movement_type = 'out'
              AND movement_date BETWEEN ? AND ?
            """,
            (date_from, date_to),
        ).fetchone()[0]

        stock_cogs = conn.execute(
            """
            SELECT COALESCE(SUM(quantity * unit_cost), 0)
            FROM stock_movements
            WHERE movement_type = 'out'
              AND movement_date BETWEEN ? AND ?
            """,
            (date_from, date_to),
        ).fetchone()[0]

        income = conn.execute(
            """
            SELECT COALESCE(SUM(amount), 0)
            FROM finance_entries
            WHERE entry_type = 'income'
              AND entry_date BETWEEN ? AND ?
            """,
            (date_from, date_to),
        ).fetchone()[0]

        legacy_deductions = conn.execute(
            """
            SELECT COALESCE(SUM(amount), 0)
            FROM employee_payments
            WHERE payment_type = 'deduction'
              AND payment_date BETWEEN ? AND ?
              AND finance_entry_id IS NULL
            """,
            (date_from, date_to),
        ).fetchone()[0]

        expense = conn.execute(
            """
            SELECT COALESCE(SUM(amount), 0)
            FROM finance_entries
            WHERE entry_type = 'expense'
              AND entry_date BETWEEN ? AND ?
            """,
            (date_from, date_to),
        ).fetchone()[0]

        stock_value = conn.execute(
            "SELECT COALESCE(SUM(quantity * unit_cost), 0) FROM products"
        ).fetchone()[0]

        product_count = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
        low_stock = conn.execute(
            "SELECT COUNT(*) FROM products WHERE quantity <= 5"
        ).fetchone()[0]

        payroll = conn.execute(
            """
            SELECT COALESCE(SUM(monthly_salary), 0)
            FROM employees WHERE is_active = 1
            """
        ).fetchone()[0]

        employee_count = conn.execute(
            "SELECT COUNT(*) FROM employees WHERE is_active = 1"
        ).fetchone()[0]

    ciro = float(stock_sales) + float(income) + float(legacy_deductions)
    maliyet = float(stock_cogs)
    gider = float(expense)
    kar = ciro - maliyet - gider

    return {
        "ciro": ciro,
        "maliyet": maliyet,
        "gider": gider,
        "kar": kar,
        "stok_degeri": float(stock_value),
        "urun_sayisi": float(product_count),
        "dusuk_stok": float(low_stock),
        "personel_sayisi": float(employee_count),
        "aylik_maas_toplam": float(payroll),
    }


def monthly_chart_data(year: int) -> list[dict[str, Any]]:
    months = []
    for month in range(1, 13):
        date_from, date_to = _month_range(year, month)
        summary = dashboard_summary(date_from, date_to)
        months.append({
            "label": f"{month:02d}",
            "month_name": [
                "Oca", "Şub", "Mar", "Nis", "May", "Haz",
                "Tem", "Ağu", "Eyl", "Eki", "Kas", "Ara",
            ][month - 1],
            "ciro": summary["ciro"],
            "gider": summary["gider"],
            "kar": summary["kar"],
        })
    return months


def yearly_chart_data(start_year: int, end_year: int) -> list[dict[str, Any]]:
    if start_year > end_year:
        start_year, end_year = end_year, start_year
    years = []
    for year in range(start_year, end_year + 1):
        summary = dashboard_summary(f"{year}-01-01", f"{year}-12-31")
        years.append({
            "label": str(year),
            "ciro": summary["ciro"],
            "gider": summary["gider"],
            "kar": summary["kar"],
        })
    return years


def ensure_ready() -> None:
    init_db()
    seed_default_categories()
    ensure_default_admin()
