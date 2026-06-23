"""Accounts app — user profile extension."""

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class Profile(models.Model):
    """Optional profile extension attached one-to-one to the auth user."""

    ROLE_MEMBER = 'member'
    ROLE_STAFF = 'staff'
    ROLE_ADMIN = 'admin'

    ROLE_CHOICES = [
        (ROLE_MEMBER, _('Üye')),
        (ROLE_STAFF, _('Yönetim Paneli')),
        (ROLE_ADMIN, _('Tam Yetki')),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name=_('Kullanıcı'),
    )
    role = models.CharField(
        _('Yetki'),
        max_length=20,
        choices=ROLE_CHOICES,
        default=ROLE_MEMBER,
        help_text=_('Yönetim paneli ve tam yetki yalnızca güvenilir hesaplara verilmelidir.'),
    )
    phone = models.CharField(_('Telefon'), max_length=30, blank=True)
    company = models.CharField(_('Firma'), max_length=120, blank=True)
    note = models.TextField(_('Not'), blank=True)

    class Meta:
        verbose_name = _('Kullanıcı')
        verbose_name_plural = _('Kullanıcılar')

    def __str__(self) -> str:
        label = self.user.get_full_name() or self.user.username
        if self.user.email:
            return f'{label} ({self.user.email})'
        return label

    def apply_role_to_user(self, save_user: bool = True) -> None:
        """Profildeki yetkiyi Django kullanıcı bayraklarına yansıt."""
        user = self.user
        if self.role == self.ROLE_ADMIN:
            user.is_staff = True
            user.is_superuser = True
        elif self.role == self.ROLE_STAFF:
            user.is_staff = True
            user.is_superuser = False
        else:
            user.is_staff = False
            user.is_superuser = False
        if save_user:
            user.save(update_fields=['is_staff', 'is_superuser'])
