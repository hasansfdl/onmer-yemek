"""Yerel SQLite veritabanı — internet veya web sitesi bağlantısı yok."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Iterator

from .config import DATA_DIR, DB_PATH, migrate_legacy_database

_SCHEMA = """
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    unit TEXT NOT NULL DEFAULT 'adet',
    quantity REAL NOT NULL DEFAULT 0,
    unit_cost REAL NOT NULL DEFAULT 0,
    category TEXT NOT NULL DEFAULT '',
    notes TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS stock_movements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    movement_type TEXT NOT NULL CHECK (movement_type IN ('in', 'out', 'adjust')),
    quantity REAL NOT NULL,
    unit_cost REAL NOT NULL DEFAULT 0,
    unit_price REAL NOT NULL DEFAULT 0,
    movement_date TEXT NOT NULL,
    note TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS finance_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entry_type TEXT NOT NULL CHECK (entry_type IN ('income', 'expense')),
    amount REAL NOT NULL,
    category TEXT NOT NULL DEFAULT '',
    description TEXT NOT NULL DEFAULT '',
    invoice_note TEXT NOT NULL DEFAULT '',
    entry_date TEXT NOT NULL,
    employee_payment_id INTEGER,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS employees (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT '',
    monthly_salary REAL NOT NULL DEFAULT 0,
    phone TEXT NOT NULL DEFAULT '',
    birth_date TEXT,
    hire_date TEXT,
    notes TEXT NOT NULL DEFAULT '',
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    category_type TEXT NOT NULL CHECK (category_type IN ('income', 'expense', 'product')),
    created_at TEXT NOT NULL,
    UNIQUE(name, category_type)
);

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE COLLATE NOCASE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('admin', 'stock', 'finance', 'viewer')),
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS employee_payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id INTEGER NOT NULL,
    payment_type TEXT NOT NULL CHECK (
        payment_type IN ('salary', 'advance', 'bonus', 'deduction')
    ),
    amount REAL NOT NULL,
    payment_date TEXT NOT NULL,
    invoice_note TEXT NOT NULL DEFAULT '',
    notes TEXT NOT NULL DEFAULT '',
    finance_entry_id INTEGER,
    created_at TEXT NOT NULL,
    FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE,
    FOREIGN KEY (finance_entry_id) REFERENCES finance_entries(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_stock_movements_date ON stock_movements(movement_date);
CREATE INDEX IF NOT EXISTS idx_finance_entries_date ON finance_entries(entry_date);
CREATE INDEX IF NOT EXISTS idx_employees_active ON employees(is_active);
CREATE INDEX IF NOT EXISTS idx_employee_payments_date ON employee_payments(payment_date);
CREATE INDEX IF NOT EXISTS idx_categories_type ON categories(category_type);
"""


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _table_columns(conn: sqlite3.Connection, table: str) -> set[str]:
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return {row[1] for row in rows}


def _migrate(conn: sqlite3.Connection) -> None:
    product_cols = _table_columns(conn, "products")
    if "category" not in product_cols:
        conn.execute(
            "ALTER TABLE products ADD COLUMN category TEXT NOT NULL DEFAULT ''"
        )

    finance_cols = _table_columns(conn, "finance_entries")
    if "invoice_note" not in finance_cols:
        conn.execute(
            "ALTER TABLE finance_entries ADD COLUMN invoice_note TEXT NOT NULL DEFAULT ''"
        )
    if "employee_payment_id" not in finance_cols:
        conn.execute(
            "ALTER TABLE finance_entries ADD COLUMN employee_payment_id INTEGER"
        )

    employee_cols = _table_columns(conn, "employees")
    if "birth_date" not in employee_cols:
        conn.execute("ALTER TABLE employees ADD COLUMN birth_date TEXT")


def init_db() -> None:
    migrate_legacy_database()
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with connect() as conn:
        conn.executescript(_SCHEMA)
        _migrate(conn)
        conn.commit()


@contextmanager
def connect() -> Iterator[sqlite3.Connection]:
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
    finally:
        conn.close()


def row_to_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    if row is None:
        return None
    return dict(row)
