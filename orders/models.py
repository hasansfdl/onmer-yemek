"""Models for inbound bulk catering orders."""

from decimal import Decimal

from django.db import models
from django.utils.translation import gettext_lazy as _


class Order(models.Model):
    """A request submitted via the public bulk-order form."""

    ORGANIZATION_TYPES = [
        ('wedding', 'Düğün'),
        ('engagement', 'Nişan'),
        ('corporate', 'Şirket Organizasyonu'),
        ('bulk', 'Toplu Yemek'),
        ('catering', 'Catering'),
        ('other', 'Diğer'),
    ]

    STATUS_CHOICES = [
        ('new', 'Yeni'),
        ('contacted', 'İletişime Geçildi'),
        ('confirmed', 'Onaylandı'),
        ('completed', 'Tamamlandı'),
        ('cancelled', 'İptal Edildi'),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('pending', _('Ödeme Bekleniyor')),
        ('paid', _('Ödeme Alındı')),
        ('failed', _('Ödeme Başarısız')),
    ]

    full_name = models.CharField(_('Ad Soyad'), max_length=120)
    company = models.CharField(_('Firma'), max_length=120, blank=True)
    email = models.EmailField(_('E-posta'))
    phone = models.CharField(_('Telefon'), max_length=30)

    organization_type = models.CharField(
        _('Organizasyon Türü'), max_length=20, choices=ORGANIZATION_TYPES,
        default='catering',
    )
    guest_count = models.PositiveIntegerField(_('Kişi Sayısı'))
    event_date = models.DateField(_('Etkinlik Tarihi'))
    event_time = models.TimeField(_('Etkinlik Saati'), null=True, blank=True)
    event_address = models.CharField(_('Etkinlik Adresi'), max_length=255,
                                     blank=True)

    notes = models.TextField(_('Özel Notlar'), blank=True)

    status = models.CharField(_('Durum'), max_length=20,
                              choices=STATUS_CHOICES, default='new')
    estimated_price = models.DecimalField(
        _('Tahmini Fiyat (₺)'), max_digits=10, decimal_places=2,
        null=True, blank=True,
    )

    payment_status = models.CharField(
        _('Ödeme Durumu'),
        max_length=16,
        choices=PAYMENT_STATUS_CHOICES,
        default='pending',
    )
    payment_transaction_ref = models.CharField(
        _('Ödeme Referansı'),
        max_length=64,
        blank=True,
        help_text=_('Ödeme sağlayıcısından dönen veya simüle edilen işlem no.'),
    )
    payment_completed_at = models.DateTimeField(
        _('Ödeme Tarihi'),
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(_('Oluşturma Tarihi'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Güncelleme'), auto_now=True)

    class Meta:
        verbose_name = _('Sipariş Talebi')
        verbose_name_plural = _('Sipariş Talepleri')
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f'#{self.pk} – {self.full_name} ({self.guest_count} kişi)'

    @property
    def is_actionable(self) -> bool:
        return self.status in {'new', 'contacted'}

    @property
    def items_total(self) -> Decimal:
        """Sum of all OrderItem subtotals (qty × unit_price × guest_count)."""
        total = Decimal('0')
        for item in self.items.all():
            total += item.line_total
        return total

    def recalculate_estimated_price(self, save: bool = True) -> Decimal:
        """Refresh estimated_price from current items_total. Returns the value."""
        total = self.items_total
        self.estimated_price = total
        if save:
            self.save(update_fields=['estimated_price', 'updated_at'])
        return total


class OrderItem(models.Model):
    """A single dish line on a bulk order (snapshot price at submit time)."""

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name=_('Sipariş'),
    )
    dish = models.ForeignKey(
        'menu.Dish',
        on_delete=models.PROTECT,
        related_name='order_items',
        verbose_name=_('Yemek'),
    )
    quantity = models.PositiveIntegerField(_('Adet (kişi)'), default=1)
    unit_price = models.DecimalField(
        _('Birim Fiyat (₺)'),
        max_digits=8, decimal_places=2,
        default=0,
        help_text=_('Sipariş gönderildiği andaki kişi başı fiyat.'),
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('Sipariş Kalemi')
        verbose_name_plural = _('Sipariş Kalemleri')
        ordering = ['id']
        constraints = [
            models.UniqueConstraint(
                fields=['order', 'dish'],
                name='orders_orderitem_unique_dish_per_order',
            ),
        ]

    def __str__(self) -> str:
        return f'{self.dish.name} × {self.quantity}'

    @property
    def line_total(self) -> Decimal:
        return Decimal(self.quantity) * (self.unit_price or Decimal('0'))
