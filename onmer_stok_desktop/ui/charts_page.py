"""Aylık ve yıllık grafikler."""

from __future__ import annotations

from datetime import date

from PyQt6.QtCharts import (
    QBarCategoryAxis,
    QBarSeries,
    QBarSet,
    QChart,
    QChartView,
    QValueAxis,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPainter
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from onmer_stok_desktop import services


def _bar_chart(title: str, labels: list[str], series_data: dict[str, list[float]]) -> QChartView:
    chart = QChart()
    chart.setTitle(title)
    chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)
    chart.legend().setAlignment(Qt.AlignmentFlag.AlignBottom)

    colors = {
        "Ciro": QColor("#4ade80"),
        "Gider": QColor("#f87171"),
        "Kar": QColor("#60a5fa"),
    }
    max_val = 1.0
    bar_series = QBarSeries()
    for name, values in series_data.items():
        bar_set = QBarSet(name)
        bar_set.setColor(colors.get(name, QColor("#d4af37")))
        for value in values:
            bar_set.append(max(value, 0))
            max_val = max(max_val, abs(value))
        bar_series.append(bar_set)

    chart.addSeries(bar_series)

    axis_x = QBarCategoryAxis()
    axis_x.append(labels)
    chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
    bar_series.attachAxis(axis_x)

    axis_y = QValueAxis()
    axis_y.setLabelFormat("₺%.0f")
    axis_y.setRange(0, max_val * 1.15)
    chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
    bar_series.attachAxis(axis_y)

    chart.setBackgroundVisible(False)
    chart.setTitleBrush(QColor("#e8edf4"))
    chart.legend().setLabelColor(QColor("#c5d0de"))
    axis_x.setLabelsColor(QColor("#8b9cb3"))
    axis_y.setLabelsColor(QColor("#8b9cb3"))

    view = QChartView(chart)
    view.setRenderHint(QPainter.RenderHint.Antialiasing)
    return view


class ChartsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        title = QLabel("Grafikler")
        title.setObjectName("PageTitle")

        self._monthly_tab = QWidget()
        self._monthly_layout = QVBoxLayout(self._monthly_tab)
        month_row = QHBoxLayout()
        month_row.addWidget(QLabel("Yıl:"))
        self._year = QSpinBox()
        self._year.setRange(2020, 2099)
        self._year.setValue(date.today().year)
        btn_month = QPushButton("Yenile")
        btn_month.setObjectName("Primary")
        btn_month.clicked.connect(self.refresh)
        month_row.addWidget(self._year)
        month_row.addWidget(btn_month)
        month_row.addStretch()
        self._monthly_layout.addLayout(month_row)

        self._yearly_tab = QWidget()
        self._yearly_layout = QVBoxLayout(self._yearly_tab)
        year_row = QHBoxLayout()
        year_row.addWidget(QLabel("Dönem:"))
        self._start_year = QSpinBox()
        self._start_year.setRange(2020, 2099)
        self._start_year.setValue(date.today().year - 4)
        self._end_year = QSpinBox()
        self._end_year.setRange(2020, 2099)
        self._end_year.setValue(date.today().year)
        btn_year = QPushButton("Yenile")
        btn_year.setObjectName("Primary")
        btn_year.clicked.connect(self.refresh)
        year_row.addWidget(self._start_year)
        year_row.addWidget(QLabel("—"))
        year_row.addWidget(self._end_year)
        year_row.addWidget(btn_year)
        year_row.addStretch()
        self._yearly_layout.addLayout(year_row)

        tabs = QTabWidget()
        tabs.addTab(self._monthly_tab, "Aylık")
        tabs.addTab(self._yearly_tab, "Yıllık")

        layout = QVBoxLayout(self)
        layout.addWidget(title)
        layout.addWidget(tabs)

        self._monthly_chart: QChartView | None = None
        self._yearly_chart: QChartView | None = None

    def refresh(self) -> None:
        year = self._year.value()
        monthly = services.monthly_chart_data(year)
        labels = [m["month_name"] for m in monthly]
        series = {
            "Ciro": [m["ciro"] for m in monthly],
            "Gider": [m["gider"] for m in monthly],
            "Kar": [m["kar"] for m in monthly],
        }
        if self._monthly_chart:
            self._monthly_layout.removeWidget(self._monthly_chart)
            self._monthly_chart.deleteLater()
        self._monthly_chart = _bar_chart(f"{year} — Aylık Özet", labels, series)
        self._monthly_layout.addWidget(self._monthly_chart)

        start = self._start_year.value()
        end = self._end_year.value()
        yearly = services.yearly_chart_data(start, end)
        y_labels = [y["label"] for y in yearly]
        y_series = {
            "Ciro": [y["ciro"] for y in yearly],
            "Gider": [y["gider"] for y in yearly],
            "Kar": [y["kar"] for y in yearly],
        }
        if self._yearly_chart:
            self._yearly_layout.removeWidget(self._yearly_chart)
            self._yearly_chart.deleteLater()
        self._yearly_chart = _bar_chart(f"{start}–{end} — Yıllık Özet", y_labels, y_series)
        self._yearly_layout.addWidget(self._yearly_chart)
