"""Domain models for dishes, categories and the weekly/daily menu plan."""

from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _


class MenuCategory(models.Model):
    """Top-level category like Düğün, Nişan, Catering, Toplu Yemek..."""

    KIND_CHOICES = [
        ('wedding', 'Düğün'),
        ('engagement', 'Nişan'),
        ('corporate', 'Şirket Organizasyonu'),
        ('bulk', 'Toplu Yemek'),
        ('catering', 'Catering'),
        ('other', 'Diğer'),
    ]

    name = models.CharField(_('Ad'), max_length=80)
    kind = models.CharField(_('Tür'), max_length=20, choices=KIND_CHOICES,
                            default='other')
    slug = models.SlugField(_('URL'), unique=True, blank=True)
    description = models.CharField(_('Açıklama'), max_length=255, blank=True)
    icon = models.CharField(_('Bootstrap Icon'), max_length=80,
                            default='bi-egg-fried')
    is_active = models.BooleanField(_('Aktif'), default=True)
    order = models.PositiveSmallIntegerField(_('Sıra'), default=0)

    class Meta:
        verbose_name = _('Yemek Kategorisi')
        verbose_name_plural = _('Yemek Kategorileri')
        ordering = ['order', 'name']

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=False)
        super().save(*args, **kwargs)


class Dish(models.Model):
    """A single dish item shown in the dish catalog."""

    category = models.ForeignKey(
        MenuCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='dishes',
        verbose_name=_('Kategori'),
    )
    name = models.CharField(_('Yemek Adı'), max_length=120)
    slug = models.SlugField(_('URL'), unique=True, blank=True)
    description = models.TextField(_('Açıklama'))
    ingredients = models.CharField(
        _('İçindekiler'),
        max_length=255,
        blank=True,
        help_text=_('Virgülle ayırarak yazınız.'),
    )
    calories = models.PositiveIntegerField(_('Kalori (kcal)'),
                                           null=True, blank=True)
    serving_size = models.CharField(_('Porsiyon'), max_length=60, blank=True,
                                    help_text=_('Örn: 250 gr / kişi'))
    image = models.ImageField(
        _('Görsel'),
        upload_to='dishes/',
        blank=True,
        null=True,
    )
    price = models.DecimalField(
        _('Kişi Başı Fiyat (₺)'),
        max_digits=8, decimal_places=2,
        default=0,
        help_text=_('Toplu sipariş formundaki kişi başı fiyat.'),
    )
    is_featured = models.BooleanField(_('Öne Çıkan'), default=False)
    is_active = models.BooleanField(_('Aktif'), default=True)
    order = models.PositiveSmallIntegerField(_('Sıra'), default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('Yemek')
        verbose_name_plural = _('Yemekler')
        ordering = ['order', 'name']

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=False)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('menu:dish_detail', kwargs={'slug': self.slug})


class WeeklyMenu(models.Model):
    """A scheduled daily/weekly menu listing."""

    title = models.CharField(_('Başlık'), max_length=120,
                             help_text=_('Örn: 12 - 18 Mayıs Haftası Menüsü'))
    start_date = models.DateField(_('Başlangıç Tarihi'))
    end_date = models.DateField(_('Bitiş Tarihi'))
    summary = models.CharField(_('Özet'), max_length=255, blank=True)
    is_published = models.BooleanField(_('Yayında'), default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('Haftalık Menü')
        verbose_name_plural = _('Haftalık Menüler')
        ordering = ['-start_date']

    def __str__(self) -> str:
        return self.title


class WeeklyMenuItem(models.Model):
    """A single menu line: a day, dish and a price."""

    DAY_CHOICES = [
        ('mon', 'Pazartesi'),
        ('tue', 'Salı'),
        ('wed', 'Çarşamba'),
        ('thu', 'Perşembe'),
        ('fri', 'Cuma'),
        ('sat', 'Cumartesi'),
        ('sun', 'Pazar'),
    ]

    menu = models.ForeignKey(
        WeeklyMenu,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name=_('Menü'),
    )
    day = models.CharField(_('Gün'), max_length=4, choices=DAY_CHOICES)
    dish = models.ForeignKey(
        Dish,
        on_delete=models.PROTECT,
        related_name='menu_appearances',
        verbose_name=_('Yemek'),
    )
    price = models.DecimalField(_('Fiyat (₺)'), max_digits=8, decimal_places=2,
                                default=0)
    note = models.CharField(_('Not'), max_length=255, blank=True)
    order = models.PositiveSmallIntegerField(_('Sıra'), default=0)

    class Meta:
        verbose_name = _('Menü Kalemi')
        verbose_name_plural = _('Menü Kalemleri')
        ordering = ['day', 'order']

    def __str__(self) -> str:
        return f'{self.get_day_display()} – {self.dish.name}'
