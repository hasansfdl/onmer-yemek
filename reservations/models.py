"""Reservation domain models — calendar-style appointment booking."""

from django.db import models
from django.utils.translation import gettext_lazy as _


class Reservation(models.Model):
    """A consultation / tasting appointment booked from the website."""

    STATUS_CHOICES = [
        ('pending', 'Bekliyor'),
        ('confirmed', 'Onaylandı'),
        ('cancelled', 'İptal'),
        ('done', 'Tamamlandı'),
    ]

    full_name = models.CharField(_('Ad Soyad'), max_length=120)
    email = models.EmailField(_('E-posta'))
    phone = models.CharField(_('Telefon'), max_length=30)

    date = models.DateField(_('Tarih'))
    time = models.TimeField(_('Saat'))
    topic = models.CharField(
        _('Görüşme Konusu'),
        max_length=160,
        blank=True,
        help_text=_('Düğün, kurumsal etkinlik, catering vs.'),
    )
    note = models.TextField(_('Not'), blank=True)

    status = models.CharField(_('Durum'), max_length=20,
                              choices=STATUS_CHOICES, default='pending')

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('Randevu')
        verbose_name_plural = _('Randevular')
        ordering = ['-date', '-time']
        # Aynı tarih + saate iki onaylı/bekleyen randevu engelleniyor.
        constraints = [
            models.UniqueConstraint(
                fields=['date', 'time'],
                condition=~models.Q(status='cancelled'),
                name='unique_active_reservation_slot',
            ),
        ]

    def __str__(self) -> str:
        return f'{self.full_name} – {self.date} {self.time}'
