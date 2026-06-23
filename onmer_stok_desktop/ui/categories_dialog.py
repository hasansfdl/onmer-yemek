"""Kategori yönetimi diyalogu."""

from __future__ import annotations

from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QInputDialog,
    QListWidget,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from onmer_stok_desktop import services

_TYPE_LABELS = {
    "income": "Gelir",
    "expense": "Gider",
    "product": "Ürün",
}


class CategoriesDialog(QDialog):
    def __init__(self, parent=None, *, initial_tab: str = "expense"):
        super().__init__(parent)
        self.setWindowTitle("Kategoriler")
        self.setMinimumSize(420, 360)

        self._lists: dict[str, QListWidget] = {}
        tabs = QTabWidget()
        for key, label in _TYPE_LABELS.items():
            widget = self._build_tab(key)
            tabs.addTab(widget, label)
            if key == initial_tab:
                tabs.setCurrentWidget(widget)

        close_btn = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        close_btn.rejected.connect(self.reject)
        close_btn.accepted.connect(self.accept)

        layout = QVBoxLayout(self)
        layout.addWidget(tabs)
        layout.addWidget(close_btn)

        self._reload_all()

    def _build_tab(self, category_type: str) -> QWidget:
        lst = QListWidget()
        self._lists[category_type] = lst

        btn_add = QPushButton("Ekle")
        btn_add.setObjectName("Primary")
        btn_del = QPushButton("Sil")
        btn_del.setObjectName("Danger")
        btn_add.clicked.connect(lambda: self._add(category_type))
        btn_del.clicked.connect(lambda: self._delete(category_type))

        row = QHBoxLayout()
        row.addWidget(btn_add)
        row.addWidget(btn_del)
        row.addStretch()

        layout = QVBoxLayout()
        layout.addWidget(lst)
        layout.addLayout(row)

        w = QWidget()
        w.setLayout(layout)
        return w

    def _reload_all(self) -> None:
        for category_type, lst in self._lists.items():
            lst.clear()
            for name in services.list_categories(category_type):
                lst.addItem(name)

    def _add(self, category_type: str) -> None:
        name, ok = QInputDialog.getText(self, "Kategori Ekle", "Kategori adı:")
        if not ok:
            return
        try:
            services.add_category(name, category_type)
            self._reload_all()
        except Exception as exc:
            QMessageBox.warning(self, "Hata", str(exc))

    def _delete(self, category_type: str) -> None:
        lst = self._lists[category_type]
        item = lst.currentItem()
        if not item:
            QMessageBox.information(self, "Seçim", "Silmek için kategori seçin.")
            return
        if QMessageBox.question(
            self, "Sil", f"'{item.text()}' silinsin mi?"
        ) != QMessageBox.StandardButton.Yes:
            return
        services.delete_category(item.text(), category_type)
        self._reload_all()
