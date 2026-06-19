"""Navbar ile aynı marka görseli — Django `static` altındaki logo dosyası."""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QPixmap

from onmer_admin_desktop import config


def brand_logo_path() -> Path:
    return config.BRAND_LOGO_PATH


def brand_icon() -> QIcon:
    """Pencere / görev çubuğu ikonu."""
    p = brand_logo_path()
    if p.is_file():
        return QIcon(str(p))
    return QIcon()


def brand_pixmap_scaled(
    max_width: int | None = None,
    max_height: int | None = None,
) -> QPixmap | None:
    """Arayüzde kullanılmak üzere oranı koruyarak ölçeklenmiş pixmap."""
    p = brand_logo_path()
    if not p.is_file():
        return None
    pm = QPixmap(str(p))
    if pm.isNull():
        return None
    if max_width and max_height:
        return pm.scaled(
            max_width,
            max_height,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
    if max_width is not None:
        return pm.scaledToWidth(max_width, Qt.TransformationMode.SmoothTransformation)
    if max_height is not None:
        return pm.scaledToHeight(max_height, Qt.TransformationMode.SmoothTransformation)
    return pm
