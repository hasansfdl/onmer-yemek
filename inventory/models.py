"""Mutfak / depo stok kalemleri ve hareket geçmişi."""

from __future__ import annotations

from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils.translation import gettext_lazy as _


class StockItem(models.Model):
    """Tek bir stok kalemi (malzeme, ürün)."""

    UNIT_CHOICES = [
        ('kg', _('Kilogram')),
        ('g', _('Gram')),
        ('lt', _('Litre')),
        ('ml', _('Mililitre')),
        ('adet', _('Adet')),
        ('paket', _('Paket')),
        ('kutu', _('Kutu')),
    ]

    name = models.CharField(_('Ürün adı'), max_length=120, unique=True)
    unit = models.CharField(
        _('Birim'),
        max_length=10,
        choices=UNIT_CHOICES,
        default='kg',
    )
    quantity = models.DecimalField(
        _('Mevcut miktar'),
        max_digits=12,
        decimal_places=3,
        default=Decimal('0'),
    )
    min_quantity = models.DecimalField(
        _('Minimum stok'),
        max_digits=12,
        decimal_places=3,
        default=Decimal('0'),
        help_text=_('Bu seviyenin altında uyarı gösterilir.'),
    )
    notes = models.TextField(_('Not'), blank=True)
    is_active = models.BooleanField(_('Aktif'), default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Stok kalemi')
        verbose_name_plural = _('Stok kalemleri')
        ordering = ['name']

    def __str__(self) -> str:
        return self.name

    @property
    def is_low(self) -> bool:
        return self.quantity <= self.min_quantity

    def apply_movement(
        self,
        movement_type: str,
        amount: Decimal,
        *,
        note: str = '',
        user=None,
    ) -> 'StockMovement':
        """Stok giriş/çıkış/düzeltme; miktarı günceller ve hareket kaydı oluşturur."""
        if amount <= 0:
            raise ValidationError(_('Miktar sıfırdan büyük olmalıdır.'))

        with transaction.atomic():
            item = StockItem.objects.select_for_update().get(pk=self.pk)
            if movement_type == StockMovement.TYPE_IN:
                new_qty = item.quantity + amount
            elif movement_type == StockMovement.TYPE_OUT:
                if item.quantity < amount:
                    raise ValidationError(
                        _('Yetersiz stok. Mevcut: %(qty)s %(unit)s') % {
                            'qty': item.quantity,
                            'unit': item.get_unit_display(),
                        }
                    )
                new_qty = item.quantity - amount
            elif movement_type == StockMovement.TYPE_ADJUST:
                new_qty = amount
            else:
                raise ValidationError(_('Geçersiz hareket türü.'))

            item.quantity = new_qty
            item.save(update_fields=['quantity', 'updated_at'])

            return StockMovement.objects.create(
                stock_item=item,
                movement_type=movement_type,
                amount=amount,
                balance_after=new_qty,
                note=note.strip(),
                created_by=user,
            )


class StockMovement(models.Model):
    """Stok giriş, çıkış veya sayım düzeltmesi."""

    TYPE_IN = 'in'
    TYPE_OUT = 'out'
    TYPE_ADJUST = 'adjust'

    TYPE_CHOICES = [
        (TYPE_IN, _('Giriş')),
        (TYPE_OUT, _('Çıkış')),
        (TYPE_ADJUST, _('Düzeltme')),
    ]

    stock_item = models.ForeignKey(
        StockItem,
        on_delete=models.CASCADE,
        related_name='movements',
        verbose_name=_('Stok kalemi'),
    )
    movement_type = models.CharField(
        _('Tür'),
        max_length=10,
        choices=TYPE_CHOICES,
    )
    amount = models.DecimalField(
        _('Miktar'),
        max_digits=12,
        decimal_places=3,
    )
    balance_after = models.DecimalField(
        _('İşlem sonrası bakiye'),
        max_digits=12,
        decimal_places=3,
    )
    note = models.CharField(_('Açıklama'), max_length=255, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='stock_movements',
        verbose_name=_('İşlemi yapan'),
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('Stok hareketi')
        verbose_name_plural = _('Stok hareketleri')
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f'{self.stock_item.name} — {self.get_movement_type_display()}'
