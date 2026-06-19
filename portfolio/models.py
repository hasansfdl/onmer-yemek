"""Portfolio domain models — past organisation gallery items."""

from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _


class PortfolioItem(models.Model):
    """An entry in the portfolio gallery (with optional cover image)."""

    CATEGORY_CHOICES = [
        ('wedding', 'Düğün'),
        ('engagement', 'Nişan'),
        ('corporate', 'Kurumsal'),
        ('bulk', 'Toplu Yemek'),
        ('catering', 'Catering'),
        ('other', 'Diğer'),
    ]

    title = models.CharField(_('Başlık'), max_length=160)
    slug = models.SlugField(_('URL'), unique=True, blank=True)
    category = models.CharField(
        _('Kategori'), max_length=20, choices=CATEGORY_CHOICES,
        default='other',
    )
    description = models.TextField(_('Açıklama'), blank=True)
    location = models.CharField(_('Konum'), max_length=160, blank=True)
    event_date = models.DateField(_('Etkinlik Tarihi'), null=True, blank=True)
    cover = models.ImageField(_('Kapak Görseli'), upload_to='portfolio/covers/')
    is_published = models.BooleanField(_('Yayında'), default=True)
    order = models.PositiveSmallIntegerField(_('Sıra'), default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('Portfolyo Öğesi')
        verbose_name_plural = _('Portfolyo Öğeleri')
        ordering = ['order', '-event_date', '-created_at']

    def __str__(self) -> str:
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title, allow_unicode=False)
        super().save(*args, **kwargs)


class PortfolioImage(models.Model):
    """Additional gallery images attached to a portfolio item."""

    item = models.ForeignKey(
        PortfolioItem,
        on_delete=models.CASCADE,
        related_name='images',
        verbose_name=_('Portfolyo Öğesi'),
    )
    image = models.ImageField(_('Görsel'), upload_to='portfolio/images/')
    caption = models.CharField(_('Başlık / Alt Metin'),
                               max_length=200, blank=True)
    order = models.PositiveSmallIntegerField(_('Sıra'), default=0)

    class Meta:
        verbose_name = _('Galeri Görseli')
        verbose_name_plural = _('Galeri Görselleri')
        ordering = ['order', 'pk']

    def __str__(self) -> str:
        return self.caption or f'Görsel #{self.pk}'
