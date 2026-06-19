"""Portfolyo ve galeri — sitedeki `PortfolioItem` / `PortfolioImage` kayıtları."""

from __future__ import annotations

import os

from PyQt6.QtCore import QDate, Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QDateEdit,
    QFileDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QGroupBox,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from django.contrib.auth.models import User
from django.core.files import File
from django.db import IntegrityError
from django.db.models import Max
from django.utils.text import slugify

from portfolio.models import PortfolioImage, PortfolioItem

from onmer_admin_desktop.database import db_transaction, ensure_django


def _abs_media_path(field_file) -> str | None:
    if not field_file:
        return None
    try:
        p = field_file.path
        if p and os.path.isfile(p):
            return p
    except Exception:  # ValueError / NotImplementedError ortam farkları
        pass
    return None


def _pixmap(path: str | None, mw: int, mh: int) -> QPixmap | None:
    if not path:
        return None
    pm = QPixmap(path)
    if pm.isNull():
        return None
    return pm.scaled(
        mw,
        mh,
        Qt.AspectRatioMode.KeepAspectRatio,
        Qt.TransformationMode.SmoothTransformation,
    )


def _unique_slug_from_title(title: str, exclude_pk: int | None = None) -> str:
    """Başlıktan slug; başka kayıtla çakışırsa `-2`, `-3` … ekler."""
    base = slugify(title, allow_unicode=False) or "portfolyo"
    candidate = base
    n = 2
    while True:
        qs = PortfolioItem.objects.filter(slug=candidate)
        if exclude_pk is not None:
            qs = qs.exclude(pk=exclude_pk)
        if not qs.exists():
            return candidate
        candidate = f"{base}-{n}"
        n += 1


def _centered_cell_widget(widget: QWidget) -> QWidget:
    wrap = QWidget()
    lay = QHBoxLayout(wrap)
    lay.setContentsMargins(4, 0, 4, 0)
    lay.setSpacing(0)
    lay.addStretch()
    lay.addWidget(widget)
    lay.addStretch()
    return wrap


def _published_combo(
    published: bool,
    pk: int,
    on_change,
) -> QWidget:
    cb = QComboBox()
    cb.addItem("Evet", True)
    cb.addItem("Hayır", False)
    cb.setFixedWidth(96)
    cb.setFixedHeight(28)
    cb.blockSignals(True)
    cb.setCurrentIndex(0 if published else 1)
    cb.blockSignals(False)
    cb.currentIndexChanged.connect(
        lambda _idx, p=pk, c=cb: on_change(p, c)
    )
    return _centered_cell_widget(cb)


class PortfolioPage(QWidget):
    def __init__(self, user: User) -> None:
        ensure_django()
        super().__init__()
        self._user = user
        self._current_id: int | None = None
        self._is_new: bool = False
        self._pending_cover: str | None = None  # Geçici yerel dosya (kapak değişimi)

        rootv = QVBoxLayout(self)
        rootv.setContentsMargins(20, 20, 20, 20)

        title = QLabel("Portfolyo ve galeri")
        title.setObjectName("Title")
        rootv.addWidget(title)
        hint = QLabel(
            "Web sitesindeki portfolyo öğelerini buradan yönetirsiniz. "
            "Kapak ve galeri görselleri media/portfolio/ altına kaydedilir."
        )
        hint.setObjectName("Muted")
        hint.setWordWrap(True)
        rootv.addWidget(hint)

        split = QSplitter(Qt.Orientation.Horizontal)
        rootv.addWidget(split, 1)

        # —— Sol: liste ——
        left = QWidget()
        left.setMinimumWidth(300)
        lv = QVBoxLayout(left)
        lv.setContentsMargins(0, 0, 8, 0)
        lv.setSpacing(8)
        bar = QHBoxLayout()
        bar.addWidget(QLabel("Kategori:"))
        self._filt_cat = QComboBox()
        self._filt_cat.addItem("Tümü", "")
        for val, lab in PortfolioItem.CATEGORY_CHOICES:
            self._filt_cat.addItem(lab, val)
        self._filt_cat.currentIndexChanged.connect(lambda _=0: self._load_items())
        bar.addWidget(self._filt_cat)
        bar.addStretch()
        btn_new = QPushButton("Yeni öğe")
        btn_new.setObjectName("Primary")
        btn_new.clicked.connect(self._new_item)
        bar.addWidget(btn_new)
        btn_ref = QPushButton("Yenile")
        btn_ref.clicked.connect(self.refresh)
        bar.addWidget(btn_ref)
        lv.addLayout(bar)

        self._items_tbl = QTableWidget(0, 5)
        self._items_tbl.setHorizontalHeaderLabels(
            ["ID", "Başlık", "Kategori", "Yayında", "Sıra"]
        )
        self._items_tbl.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self._items_tbl.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self._items_tbl.itemSelectionChanged.connect(self._on_item_selected)
        items_hdr = self._items_tbl.horizontalHeader()
        items_hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        items_hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        items_hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        items_hdr.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        items_hdr.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self._items_tbl.setColumnWidth(3, 120)
        self._items_tbl.verticalHeader().setVisible(False)
        lv.addWidget(self._items_tbl, 1)
        btn_del_item = QPushButton("Seçili öğeyi sil")
        btn_del_item.setObjectName("Danger")
        btn_del_item.clicked.connect(self._delete_item)
        lv.addWidget(btn_del_item)
        split.addWidget(left)

        # —— Sağ: detay (kaydırılabilir) ——
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        right = QWidget()
        right.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )
        rv = QVBoxLayout(right)
        rv.setContentsMargins(8, 0, 0, 0)
        rv.setSpacing(12)

        self._detail_box = QGroupBox("Öğe detayı")
        detail_outer = QVBoxLayout(self._detail_box)
        detail_outer.setSpacing(10)

        form = QFormLayout()
        form.setFieldGrowthPolicy(
            QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow
        )
        form.setLabelAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )
        form.setFormAlignment(Qt.AlignmentFlag.AlignTop)
        form.setHorizontalSpacing(12)
        form.setVerticalSpacing(10)

        self._f_title = QLineEdit()
        self._f_cat = QComboBox()
        for val, lab in PortfolioItem.CATEGORY_CHOICES:
            self._f_cat.addItem(lab, val)
        self._f_desc = QTextEdit()
        self._f_desc.setMinimumHeight(72)
        self._f_desc.setMaximumHeight(100)
        self._f_loc = QLineEdit()
        self._f_event_use = QCheckBox("Etkinlik tarihi var")
        self._f_event = QDateEdit()
        self._f_event.setCalendarPopup(True)
        self._f_event_use.toggled.connect(self._f_event.setEnabled)
        self._f_pub = QComboBox()
        self._f_pub.addItem("Evet", True)
        self._f_pub.addItem("Hayır", False)
        self._f_order = QSpinBox()
        self._f_order.setRange(0, 32767)

        event_row = QWidget()
        event_lay = QHBoxLayout(event_row)
        event_lay.setContentsMargins(0, 0, 0, 0)
        event_lay.setSpacing(8)
        event_lay.addWidget(self._f_event_use)
        event_lay.addWidget(self._f_event)
        event_lay.addStretch()

        form.addRow("Başlık", self._f_title)
        form.addRow("Kategori", self._f_cat)
        form.addRow("Açıklama", self._f_desc)
        form.addRow("Konum", self._f_loc)
        form.addRow("Etkinlik", event_row)
        form.addRow("Yayında", self._f_pub)
        form.addRow("Sıra", self._f_order)

        cover_wrap = QWidget()
        cov_row = QHBoxLayout(cover_wrap)
        cov_row.setContentsMargins(0, 0, 0, 0)
        cov_row.setSpacing(12)
        self._cover_preview = QLabel("Kapak önizleme")
        self._cover_preview.setFixedSize(180, 100)
        self._cover_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._cover_preview.setStyleSheet(
            "border: 1px solid #2a2a2a; border-radius: 8px; background: #121212;"
        )
        btn_cov = QPushButton("Kapak görseli seç…")
        btn_cov.clicked.connect(self._pick_cover)
        self._cover_path_lbl = QLabel("—")
        self._cover_path_lbl.setObjectName("Muted")
        self._cover_path_lbl.setWordWrap(True)
        self._cover_path_lbl.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )
        cov_l = QVBoxLayout()
        cov_l.setContentsMargins(0, 0, 0, 0)
        cov_l.setSpacing(6)
        cov_l.addWidget(btn_cov)
        cov_l.addWidget(self._cover_path_lbl)
        cov_l.addStretch()
        cov_row.addWidget(self._cover_preview, 0, Qt.AlignmentFlag.AlignTop)
        cov_row.addLayout(cov_l, 1)
        form.addRow("Kapak", cover_wrap)

        detail_outer.addLayout(form)

        detail_actions = QHBoxLayout()
        detail_actions.setContentsMargins(0, 4, 0, 0)
        detail_actions.addStretch()
        btn_save_item = QPushButton("Öğeyi kaydet")
        btn_save_item.setObjectName("Primary")
        btn_save_item.setMinimumWidth(160)
        btn_save_item.clicked.connect(self._save_item)
        detail_actions.addWidget(btn_save_item)
        detail_outer.addLayout(detail_actions)

        rv.addWidget(self._detail_box)

        # Galeri
        self._gal_box = QGroupBox("Galeri görselleri (ek fotoğraflar)")
        gv = QVBoxLayout(self._gal_box)
        gv.setSpacing(8)
        gal_bar = QHBoxLayout()
        btn_add_img = QPushButton("Galeriye fotoğraf ekle…")
        btn_add_img.clicked.connect(self._add_gallery_image)
        gal_bar.addWidget(btn_add_img)
        gal_bar.addStretch()
        btn_save_gal = QPushButton("Galeri başlık / sıra kaydet")
        btn_save_gal.clicked.connect(self._save_gallery_meta)
        gal_bar.addWidget(btn_save_gal)
        gv.addLayout(gal_bar)

        self._gal_tbl = QTableWidget(0, 4)
        self._gal_tbl.setHorizontalHeaderLabels(
            ["Öniz.", "ID", "Başlık / alt metin", "Sıra"]
        )
        gal_hdr = self._gal_tbl.horizontalHeader()
        gal_hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        gal_hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        gal_hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        gal_hdr.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self._gal_tbl.setColumnWidth(0, 110)
        self._gal_tbl.verticalHeader().setVisible(False)
        self._gal_tbl.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self._gal_tbl.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        gv.addWidget(self._gal_tbl, 1)
        btn_rm_img = QPushButton("Seçili galeri görselini sil")
        btn_rm_img.setObjectName("Danger")
        btn_rm_img.clicked.connect(self._remove_gallery_image)
        gv.addWidget(btn_rm_img)

        rv.addWidget(self._gal_box, 1)
        scroll.setWidget(right)
        split.addWidget(scroll)
        split.setStretchFactor(0, 2)
        split.setStretchFactor(1, 3)
        split.setSizes([360, 640])

        self._set_form_enabled(False)
        self.refresh()

    def refresh(self) -> None:
        keep = self._current_id
        self._load_items()
        if keep:
            self._select_row_by_pk(keep)
        if not keep and not self._is_new:
            self._clear_form()

    def _set_form_enabled(self, on: bool) -> None:
        self._detail_box.setEnabled(on)
        self._gal_box.setEnabled(on and not self._is_new)

    def _load_items(self) -> None:
        cat = self._filt_cat.currentData()
        qs = PortfolioItem.objects.all().order_by("order", "-event_date", "-pk")
        if cat:
            qs = qs.filter(category=cat)
        self._items_tbl.blockSignals(True)
        self._items_tbl.setRowCount(0)
        for it in qs:
            r = self._items_tbl.rowCount()
            self._items_tbl.insertRow(r)
            c0 = QTableWidgetItem(str(it.pk))
            c0.setData(Qt.ItemDataRole.UserRole, it.pk)
            self._items_tbl.setItem(r, 0, c0)
            self._items_tbl.setItem(r, 1, QTableWidgetItem(it.title))
            self._items_tbl.setItem(
                r, 2, QTableWidgetItem(it.get_category_display())
            )
            self._items_tbl.setCellWidget(
                r,
                3,
                _published_combo(it.is_published, it.pk, self._on_published_changed),
            )
            self._items_tbl.setItem(r, 4, QTableWidgetItem(str(it.order)))
            self._items_tbl.setRowHeight(r, 44)
        self._items_tbl.blockSignals(False)

    def _on_published_changed(self, pk: int, combo: QComboBox) -> None:
        raw = combo.currentData()
        if raw is None:
            return
        published = bool(raw)
        try:
            with db_transaction():
                PortfolioItem.objects.filter(pk=pk).update(is_published=published)
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))
            self._load_items()
            return
        if self._current_id == pk and not self._is_new:
            self._f_pub.blockSignals(True)
            self._f_pub.setCurrentIndex(0 if published else 1)
            self._f_pub.blockSignals(False)

    def _select_row_by_pk(self, pk: int) -> None:
        for r in range(self._items_tbl.rowCount()):
            it = self._items_tbl.item(r, 0)
            if it and it.data(Qt.ItemDataRole.UserRole) == pk:
                self._items_tbl.selectRow(r)
                return

    def _on_item_selected(self) -> None:
        sel = self._items_tbl.selectedItems()
        if not sel:
            if not self._is_new:
                self._current_id = None
                self._set_form_enabled(False)
                self._clear_form(keep_new_state=False)
            return
        row = sel[0].row()
        it = self._items_tbl.item(row, 0)
        if not it:
            return
        pk = it.data(Qt.ItemDataRole.UserRole)
        if not pk:
            return
        self._is_new = False
        self._current_id = int(pk)
        self._pending_cover = None
        self._set_form_enabled(True)
        self._load_item_form(self._current_id)

    def _clear_form(self, keep_new_state: bool = False) -> None:
        if not keep_new_state:
            self._is_new = False
            self._current_id = None
        self._pending_cover = None
        self._f_title.clear()
        self._f_cat.setCurrentIndex(0)
        self._f_desc.clear()
        self._f_loc.clear()
        self._f_event_use.setChecked(False)
        self._f_event.setEnabled(False)
        self._f_pub.setCurrentIndex(0)
        self._f_order.setValue(0)
        self._cover_path_lbl.setText("—")
        self._cover_preview.setPixmap(QPixmap())
        self._cover_preview.setText("Kapak yok")
        self._gal_tbl.setRowCount(0)

    def _set_cover_preview_path(self, path: str | None) -> None:
        pm = _pixmap(path, 170, 90)
        if pm is not None:
            self._cover_preview.setPixmap(pm)
            self._cover_preview.setText("")
        else:
            self._cover_preview.setPixmap(QPixmap())
            self._cover_preview.setText("Kapak yok")

    def _new_item(self) -> None:
        self._items_tbl.clearSelection()
        self._is_new = True
        self._current_id = None
        self._pending_cover = None
        self._set_form_enabled(True)
        self._gal_box.setEnabled(False)
        self._clear_form(keep_new_state=True)

    def _pick_cover(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Kapak görseli",
            "",
            "Görseller (*.png *.jpg *.jpeg *.webp *.gif);;Tüm dosyalar (*.*)",
        )
        if not path:
            return
        self._pending_cover = path
        self._cover_path_lbl.setText(os.path.basename(path))
        self._set_cover_preview_path(path)

    def _load_item_form(self, pk: int) -> None:
        try:
            it = PortfolioItem.objects.get(pk=pk)
        except PortfolioItem.DoesNotExist:
            self._clear_form()
            return
        self._f_title.setText(it.title)
        idx = self._f_cat.findData(it.category)
        if idx >= 0:
            self._f_cat.setCurrentIndex(idx)
        self._f_desc.setPlainText(it.description or "")
        self._f_loc.setText(it.location or "")
        if it.event_date:
            self._f_event_use.setChecked(True)
            self._f_event.setEnabled(True)
            d = it.event_date
            self._f_event.setDate(QDate(d.year, d.month, d.day))
        else:
            self._f_event_use.setChecked(False)
            self._f_event.setEnabled(False)

        self._f_pub.setCurrentIndex(0 if it.is_published else 1)
        self._f_order.setValue(it.order)
        cover_p = _abs_media_path(it.cover)
        self._cover_path_lbl.setText(
            os.path.basename(cover_p) if cover_p else "(dosya yok)"
        )
        self._set_cover_preview_path(cover_p)

        self._load_gallery(pk)

    def _load_gallery(self, item_pk: int) -> None:
        self._gal_tbl.blockSignals(True)
        self._gal_tbl.setRowCount(0)
        imgs = PortfolioImage.objects.filter(item_id=item_pk).order_by(
            "order", "pk"
        )
        for im in imgs:
            r = self._gal_tbl.rowCount()
            self._gal_tbl.insertRow(r)
            ph = QLabel()
            ph.setAlignment(Qt.AlignmentFlag.AlignCenter)
            ph.setFixedSize(100, 72)
            p = _abs_media_path(im.image)
            pm = _pixmap(p, 96, 68)
            if pm:
                ph.setPixmap(pm)
            else:
                ph.setText("?")
            self._gal_tbl.setCellWidget(r, 0, ph)
            id_it = QTableWidgetItem(str(im.pk))
            id_it.setData(Qt.ItemDataRole.UserRole, im.pk)
            id_it.setFlags(
                Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled
            )
            self._gal_tbl.setItem(r, 1, id_it)
            cap = QLineEdit(im.caption)
            cap.setMinimumHeight(30)
            self._gal_tbl.setCellWidget(r, 2, cap)
            ord_spin = QSpinBox()
            ord_spin.setRange(0, 32767)
            ord_spin.setValue(im.order)
            ord_spin.setMinimumWidth(72)
            self._gal_tbl.setCellWidget(r, 3, ord_spin)
            self._gal_tbl.setRowHeight(r, 78)
        self._gal_tbl.blockSignals(False)

    def _save_item(self) -> None:
        title = self._f_title.text().strip()
        if not title:
            QMessageBox.warning(self, "Eksik", "Başlık zorunludur.")
            return

        exclude = None if self._is_new else self._current_id
        slug = _unique_slug_from_title(title, exclude)

        ev_date = None
        if self._f_event_use.isChecked():
            ev_date = self._f_event.date().toPyDate()

        if self._is_new:
            if not self._pending_cover:
                QMessageBox.warning(
                    self,
                    "Kapak",
                    "Yeni portfolyo öğesi için kapak görseli seçmelisiniz.",
                )
                return
        else:
            if not self._current_id:
                return

        try:
            with db_transaction():
                if self._is_new:
                    item = PortfolioItem(
                        title=title,
                        slug=slug,
                        category=self._f_cat.currentData(),
                        description=self._f_desc.toPlainText().strip(),
                        location=self._f_loc.text().strip(),
                        event_date=ev_date,
                        is_published=bool(self._f_pub.currentData()),
                        order=self._f_order.value(),
                    )
                    with open(self._pending_cover, "rb") as f:
                        item.cover.save(
                            os.path.basename(self._pending_cover),
                            File(f),
                            save=True,
                        )
                    self._is_new = False
                    self._current_id = item.pk
                    self._pending_cover = None
                    self._gal_box.setEnabled(True)
                else:
                    item = PortfolioItem.objects.select_for_update().get(
                        pk=self._current_id
                    )
                    item.title = title
                    item.slug = slug
                    item.category = self._f_cat.currentData()
                    item.description = self._f_desc.toPlainText().strip()
                    item.location = self._f_loc.text().strip()
                    item.event_date = ev_date
                    item.is_published = bool(self._f_pub.currentData())
                    item.order = self._f_order.value()
                    item.save()
                    if self._pending_cover:
                        with open(self._pending_cover, "rb") as f:
                            item.cover.save(
                                os.path.basename(self._pending_cover),
                                File(f),
                                save=True,
                            )
                        self._pending_cover = None
        except IntegrityError as e:
            QMessageBox.critical(self, "Veritabanı", str(e))
            return
        except OSError as e:
            QMessageBox.critical(self, "Dosya", str(e))
            return

        QMessageBox.information(self, "Tamam", "Portfolyo öğesi kaydedildi.")
        self.refresh()
        if self._current_id:
            self._select_row_by_pk(self._current_id)

    def _delete_item(self) -> None:
        if self._is_new:
            self._clear_form()
            self._set_form_enabled(False)
            return
        if not self._current_id:
            return
        if (
            QMessageBox.question(
                self,
                "Sil",
                f"“{self._f_title.text()}” ve tüm galeri görselleri silinsin mi?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            != QMessageBox.StandardButton.Yes
        ):
            return
        PortfolioItem.objects.filter(pk=self._current_id).delete()
        self._current_id = None
        self._clear_form()
        self._set_form_enabled(False)
        self.refresh()

    def _add_gallery_image(self) -> None:
        if not self._current_id or self._is_new:
            return
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Galeri görseli",
            "",
            "Görseller (*.png *.jpg *.jpeg *.webp *.gif);;Tüm dosyalar (*.*)",
        )
        if not path:
            return
        try:
            with db_transaction():
                top = PortfolioImage.objects.filter(
                    item_id=self._current_id
                ).aggregate(m=Max("order"))["m"]
                next_order = (top or 0) + 1
                pi = PortfolioImage(item_id=self._current_id, order=next_order)
                with open(path, "rb") as f:
                    pi.image.save(os.path.basename(path), File(f), save=True)
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))
            return
        self._load_gallery(self._current_id)

    def _save_gallery_meta(self) -> None:
        if not self._current_id or self._is_new:
            return
        try:
            with db_transaction():
                for r in range(self._gal_tbl.rowCount()):
                    id_it = self._gal_tbl.item(r, 1)
                    if not id_it:
                        continue
                    pk = id_it.data(Qt.ItemDataRole.UserRole)
                    if not pk:
                        continue
                    cap_w = self._gal_tbl.cellWidget(r, 2)
                    ord_w = self._gal_tbl.cellWidget(r, 3)
                    if not isinstance(cap_w, QLineEdit) or not isinstance(
                        ord_w, QSpinBox
                    ):
                        continue
                    PortfolioImage.objects.filter(pk=int(pk)).update(
                        caption=cap_w.text().strip(),
                        order=ord_w.value(),
                    )
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))
            return
        QMessageBox.information(self, "Tamam", "Galeri bilgileri güncellendi.")
        self._load_gallery(self._current_id)

    def _remove_gallery_image(self) -> None:
        if not self._current_id or self._is_new:
            return
        r = self._gal_tbl.currentRow()
        if r < 0:
            QMessageBox.warning(self, "Seçim", "Silinecek galeri satırını seçin.")
            return
        id_it = self._gal_tbl.item(r, 1)
        if not id_it:
            return
        pk = id_it.data(Qt.ItemDataRole.UserRole)
        if not pk:
            return
        if (
            QMessageBox.question(
                self,
                "Sil",
                "Bu galeri görseli silinsin mi?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            != QMessageBox.StandardButton.Yes
        ):
            return
        try:
            PortfolioImage.objects.filter(pk=int(pk)).delete()
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))
            return
        self._load_gallery(self._current_id)
