"""Koyu tema stilleri."""

from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtWidgets import QApplication


def apply_theme(app: QApplication) -> None:
    app.setStyle("Fusion")
    palette = QPalette()
    bg = QColor("#0f1419")
    card = QColor("#1a2332")
    text = QColor("#e8edf4")
    muted = QColor("#8b9cb3")
    brand = QColor("#d4af37")
    palette.setColor(QPalette.ColorRole.Window, bg)
    palette.setColor(QPalette.ColorRole.WindowText, text)
    palette.setColor(QPalette.ColorRole.Base, card)
    palette.setColor(QPalette.ColorRole.AlternateBase, bg)
    palette.setColor(QPalette.ColorRole.Text, text)
    palette.setColor(QPalette.ColorRole.Button, card)
    palette.setColor(QPalette.ColorRole.ButtonText, text)
    palette.setColor(QPalette.ColorRole.Highlight, brand)
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#0f1419"))
    palette.setColor(QPalette.ColorRole.PlaceholderText, muted)
    app.setPalette(palette)

    app.setStyleSheet("""
        QMainWindow, QWidget { font-family: 'Segoe UI', sans-serif; font-size: 13px; }
        QPushButton {
            background: #243044; border: 1px solid #3d4f66; border-radius: 8px;
            padding: 8px 16px; color: #e8edf4;
        }
        QPushButton:hover { background: #2d3d54; border-color: #d4af37; }
        QPushButton#Primary {
            background: #d4af37; color: #0f1419; border: none; font-weight: 600;
        }
        QPushButton#Primary:hover { background: #e0c04a; }
        QPushButton#Danger { background: #5c2a2a; border-color: #8b3a3a; }
        QLineEdit, QTextEdit, QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit {
            background: #1a2332; border: 1px solid #3d4f66; border-radius: 8px;
            padding: 8px 10px; color: #e8edf4;
        }
        QTableWidget {
            background: #1a2332; border: 1px solid #3d4f66; border-radius: 8px;
            gridline-color: #2d3d54;
        }
        QHeaderView::section {
            background: #243044; color: #d4af37; padding: 8px; border: none;
            font-weight: 600;
        }
        QTabWidget::pane { border: 1px solid #3d4f66; border-radius: 8px; }
        QTabBar::tab {
            background: #1a2332; padding: 10px 20px; margin-right: 4px;
            border-top-left-radius: 8px; border-top-right-radius: 8px;
        }
        QTabBar::tab:selected { background: #243044; color: #d4af37; }
        QLabel#CardTitle { font-size: 11px; color: #8b9cb3; letter-spacing: 1px; }
        QLabel#CardValue { font-size: 22px; font-weight: 700; color: #d4af37; }
        QLabel#PageTitle { font-size: 20px; font-weight: 700; color: #fff; }
    """)
