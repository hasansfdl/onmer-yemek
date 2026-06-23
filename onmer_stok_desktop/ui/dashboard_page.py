"""Özet panel — ciro, kar, stok değeri."""

from __future__ import annotations

from datetime import date

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDateEdit,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from onmer_stok_desktop import services


def _money(value: float) -> str:
    return f"₺{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _money_whole(value: float) -> str:
    return f"₺{value:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")


class DashboardPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._cards: dict[str, QLabel] = {}

        title = QLabel("Özet Panel")
        title.setObjectName("PageTitle")

        filter_row = QHBoxLayout()
        self._from = QDateEdit()
        self._from.setCalendarPopup(True)
        self._from.setDate(date(date.today().year, date.today().month, 1))
        self._to = QDateEdit()
        self._to.setCalendarPopup(True)
        self._to.setDate(date.today())
        btn = QPushButton("Yenile")
        btn.setObjectName("Primary")
        btn.clicked.connect(self.refresh)
        filter_row.addWidget(QLabel("Dönem:"))
        filter_row.addWidget(self._from)
        filter_row.addWidget(QLabel("—"))
        filter_row.addWidget(self._to)
        filter_row.addWidget(btn)
        filter_row.addStretch()

        grid = QGridLayout()
        grid.setSpacing(16)
        labels = [
            ("ciro", "Ciro"),
            ("kar", "Kar / Zarar"),
            ("gider", "Giderler"),
            ("stok_degeri", "Stok Değeri"),
            ("aylik_maas_toplam", "Aylık Maaş Toplamı"),
            ("personel_sayisi", "Aktif Personel"),
            ("urun_sayisi", "Ürün Sayısı"),
            ("dusuk_stok", "Düşük Stok (≤5)"),
        ]
        for i, (key, label) in enumerate(labels):
            frame = self._make_card(label)
            grid.addWidget(frame, i // 3, i % 3)

        layout = QVBoxLayout(self)
        layout.addWidget(title)
        layout.addLayout(filter_row)
        layout.addLayout(grid)
        layout.addStretch()

    def _make_card(self, title: str) -> QFrame:
        frame = QFrame()
        frame.setStyleSheet(
            "QFrame { background: #1a2332; border: 1px solid #3d4f66; border-radius: 12px; }"
        )
        v = QVBoxLayout(frame)
        t = QLabel(title.upper())
        t.setObjectName("CardTitle")
        val = QLabel("—")
        val.setObjectName("CardValue")
        v.addWidget(t)
        v.addWidget(val)
        self._cards[title] = val
        return frame

    def refresh(self) -> None:
        d_from = self._from.date().toString("yyyy-MM-dd")
        d_to = self._to.date().toString("yyyy-MM-dd")
        s = services.dashboard_summary(d_from, d_to)

        mapping = {
            "Ciro": _money(s["ciro"]),
            "Kar / Zarar": _money(s["kar"]),
            "Giderler": _money(s["gider"]),
            "Stok Değeri": _money(s["stok_degeri"]),
            "Aylık Maaş Toplamı": _money_whole(s["aylik_maas_toplam"]),
            "Aktif Personel": str(int(s["personel_sayisi"])),
            "Ürün Sayısı": str(int(s["urun_sayisi"])),
            "Düşük Stok (≤5)": str(int(s["dusuk_stok"])),
        }
        for title, text in mapping.items():
            lbl = self._cards.get(title)
            if lbl:
                lbl.setText(text)
                if title == "Kar / Zarar":
                    color = "#4ade80" if s["kar"] >= 0 else "#f87171"
                    lbl.setStyleSheet(f"font-size: 22px; font-weight: 700; color: {color};")
