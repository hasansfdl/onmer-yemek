"""Accounts app — user profile extension."""

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class Profile(models.Model):
    """Optional profile extension attached one-to-one to the auth user."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name=_('Kullanıcı'),
    )
    phone = models.CharField(_('Telefon'), max_length=30, blank=True)
    company = models.CharField(_('Firma'), max_length=120, blank=True)
    note = models.TextField(_('Not'), blank=True)

    class Meta:
        verbose_name = _('Profil')
        verbose_name_plural = _('Profiller')

    def __str__(self) -> str:
        return f'Profil: {self.user.username}'
