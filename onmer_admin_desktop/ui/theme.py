"""Koyu tema ve altın vurgu — global QSS."""

from __future__ import annotations

# Palet: siyah, koyu gri, beyaz, altın
COLOR_BG = "#0d0d0d"
COLOR_SURFACE = "#161616"
COLOR_CARD = "#1e1e1e"
COLOR_BORDER = "#2a2a2a"
COLOR_TEXT = "#f2f2f2"
COLOR_MUTED = "#9a9a9a"
COLOR_GOLD = "#c9a227"
COLOR_GOLD_HOVER = "#e0bc3c"
COLOR_DANGER = "#c94c4c"


def app_stylesheet() -> str:
    return f"""
    QWidget {{
        background-color: {COLOR_BG};
        color: {COLOR_TEXT};
        font-family: "Segoe UI", "SF Pro Display", sans-serif;
        font-size: 13px;
    }}
    QMainWindow {{
        background-color: {COLOR_BG};
    }}
    QFrame#Card {{
        background-color: {COLOR_CARD};
        border: 1px solid {COLOR_BORDER};
        border-radius: 10px;
    }}
    QLabel#Title {{
        font-size: 18px;
        font-weight: 600;
        color: {COLOR_TEXT};
    }}
    QLabel#Muted {{
        color: {COLOR_MUTED};
        font-size: 12px;
    }}
    QLabel#KpiValue {{
        font-size: 22px;
        font-weight: 700;
        color: {COLOR_GOLD};
    }}
    QLabel#KpiLabel {{
        color: {COLOR_MUTED};
        font-size: 11px;
        text-transform: uppercase;
    }}
    QPushButton {{
        background-color: {COLOR_SURFACE};
        border: 1px solid {COLOR_BORDER};
        border-radius: 8px;
        padding: 8px 16px;
        min-height: 20px;
    }}
    QPushButton:hover {{
        border-color: {COLOR_GOLD};
        color: {COLOR_GOLD};
    }}
    QPushButton:pressed {{
        background-color: {COLOR_CARD};
    }}
    QPushButton#Primary {{
        background-color: {COLOR_GOLD};
        color: {COLOR_BG};
        border: none;
        font-weight: 600;
    }}
    QPushButton#Primary:hover {{
        background-color: {COLOR_GOLD_HOVER};
        color: {COLOR_BG};
    }}
    QPushButton#Danger {{
        background-color: transparent;
        border-color: {COLOR_DANGER};
        color: {COLOR_DANGER};
    }}
    QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox, QDateEdit, QTimeEdit, QComboBox {{
        background-color: {COLOR_SURFACE};
        border: 1px solid {COLOR_BORDER};
        border-radius: 8px;
        padding: 8px 10px;
        min-height: 22px;
        color: {COLOR_TEXT};
        selection-background-color: {COLOR_GOLD};
        selection-color: {COLOR_BG};
    }}
    QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QComboBox:focus {{
        border-color: {COLOR_GOLD};
    }}
    QComboBox QAbstractItemView {{
        background-color: {COLOR_CARD};
        color: {COLOR_TEXT};
        selection-background-color: {COLOR_GOLD};
        selection-color: {COLOR_BG};
        outline: none;
        padding: 2px;
    }}
    QComboBox QAbstractItemView::item {{
        min-height: 22px;
        padding: 6px 12px;
    }}
    QComboBox QAbstractItemView::item:selected {{
        background: {COLOR_GOLD};
        color: {COLOR_BG};
    }}
    QComboBox QAbstractItemView::item:hover {{
        background: {COLOR_SURFACE};
        color: {COLOR_GOLD};
    }}
    QComboBox::drop-down {{
        border: none;
        width: 28px;
    }}
    QListWidget {{
        background-color: {COLOR_SURFACE};
        border: 1px solid {COLOR_BORDER};
        border-radius: 10px;
        padding: 6px;
        outline: none;
    }}
    QListWidget::item {{
        padding: 10px 12px;
        border-radius: 8px;
        margin: 2px 0;
    }}
    QListWidget::item:selected {{
        background-color: {COLOR_CARD};
        border-left: 3px solid {COLOR_GOLD};
        color: {COLOR_GOLD};
    }}
    QListWidget::item:hover {{
        background-color: {COLOR_CARD};
    }}
    QTableWidget {{
        background-color: {COLOR_SURFACE};
        border: 1px solid {COLOR_BORDER};
        border-radius: 10px;
        gridline-color: {COLOR_BORDER};
        selection-background-color: #3d3510;
    }}
    QTableWidget::item {{
        padding: 6px;
    }}
    QHeaderView::section {{
        background-color: {COLOR_CARD};
        color: {COLOR_MUTED};
        padding: 8px;
        border: none;
        border-bottom: 2px solid {COLOR_GOLD};
        font-weight: 600;
    }}
    QScrollBar:vertical {{
        background: {COLOR_SURFACE};
        width: 10px;
        margin: 0;
    }}
    QScrollBar::handle:vertical {{
        background: {COLOR_BORDER};
        min-height: 24px;
        border-radius: 5px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: {COLOR_GOLD};
    }}
    QGroupBox {{
        border: 1px solid {COLOR_BORDER};
        border-radius: 10px;
        margin-top: 12px;
        padding-top: 12px;
        font-weight: 600;
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 12px;
        color: {COLOR_GOLD};
    }}
    QMessageBox {{
        background-color: {COLOR_CARD};
    }}
    """


def apply_theme(app) -> None:
    from PyQt6.QtWidgets import QApplication

    if isinstance(app, QApplication):
        app.setStyleSheet(app_stylesheet())
