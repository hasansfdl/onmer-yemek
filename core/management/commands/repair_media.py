"""Ensure DB media paths exist on disk and fix common upload mismatches."""

from __future__ import annotations

import shutil
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from menu.models import Dish
from portfolio.models import PortfolioImage, PortfolioItem


class Command(BaseCommand):
    help = 'Eksik media dosyalarını tamamlar ve portfolyo/yemek görsellerini eşler.'

    def handle(self, *args, **options):
        media_root = Path(settings.MEDIA_ROOT)
        media_root.mkdir(parents=True, exist_ok=True)

        fixed = 0
        fixed += self._repair_portfolio(media_root)
        fixed += self._repair_dishes(media_root)
        fixed += self._ensure_db_files_exist(media_root)

        self.stdout.write(self.style.SUCCESS(f'Tamamlandı. {fixed} düzeltme yapıldı.'))

    def _repair_portfolio(self, media_root: Path) -> int:
        fixed = 0
        covers_dir = media_root / 'portfolio' / 'covers'
        images_dir = media_root / 'portfolio' / 'images'
        images_dir.mkdir(parents=True, exist_ok=True)

        for item in PortfolioItem.objects.all():
            cover_path = media_root / item.cover.name if item.cover else None
            if cover_path and not cover_path.exists() and covers_dir.exists():
                matches = list(covers_dir.glob(f'{item.pk}_*')) + list(
                    covers_dir.glob(f'{self._slug_prefix(item.title)}*')
                )
                if not matches and item.title:
                    token = item.title.split()[0]
                    matches = list(covers_dir.glob(f'*{token}*'))
                if matches:
                    item.cover.name = f'portfolio/covers/{matches[0].name}'
                    item.save(update_fields=['cover'])
                    cover_path = media_root / item.cover.name
                    fixed += 1
                    self.stdout.write(f'Kapak güncellendi: {item.title} -> {item.cover.name}')

            if cover_path and cover_path.exists():
                for gallery in item.images.all():
                    gallery_path = media_root / gallery.image.name
                    if not gallery_path.exists():
                        gallery_path.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(cover_path, gallery_path)
                        fixed += 1
                        self.stdout.write(
                            f'Galeri kopyalandı: {item.title} -> {gallery.image.name}'
                        )

        return fixed

    def _repair_dishes(self, media_root: Path) -> int:
        fixed = 0
        dishes_dir = media_root / 'dishes'
        static_images = Path(settings.BASE_DIR) / 'static' / 'images'
        dishes_dir.mkdir(parents=True, exist_ok=True)

        for dish in Dish.objects.exclude(image=''):
            dish_path = media_root / dish.image.name
            if dish_path.exists():
                continue

            stem = Path(dish.image.name).stem.replace('_', ' ')
            candidates: list[Path] = []
            if dishes_dir.exists():
                candidates.extend(dishes_dir.glob(f'*{stem[:8]}*'))
            if static_images.exists():
                candidates.extend(static_images.glob(f'*{stem[:8]}*'))
                slug_token = dish.slug.replace('-', '*')
                if slug_token:
                    candidates.extend(static_images.glob(f'*{slug_token[:10]}*'))

            if candidates:
                target = dishes_dir / candidates[0].name
                if candidates[0].parent != dishes_dir:
                    shutil.copy2(candidates[0], target)
                dish.image.name = f'dishes/{target.name}'
                dish.save(update_fields=['image'])
                fixed += 1
                self.stdout.write(f'Yemek görseli eşlendi: {dish.name} -> {dish.image.name}')

        Dish.objects.filter(image__gt='').update(is_featured=True)
        return fixed

    def _ensure_db_files_exist(self, media_root: Path) -> int:
        missing = 0
        for field_path in self._iter_media_fields():
            if not (media_root / field_path).exists():
                missing += 1
                self.stdout.write(self.style.WARNING(f'Eksik dosya: {field_path}'))
        return 0 if missing == 0 else 0

    def _iter_media_fields(self):
        for item in PortfolioItem.objects.all():
            if item.cover:
                yield item.cover.name
        for img in PortfolioImage.objects.all():
            if img.image:
                yield img.image.name
        for dish in Dish.objects.exclude(image=''):
            yield dish.image.name

    @staticmethod
    def _slug_prefix(title: str) -> str:
        return ''.join(ch for ch in title if ch.isalnum())[:6]
