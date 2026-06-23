"""Otomatik profil oluşturma — site kaydı ve mevcut kullanıcılar."""

from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Profile


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def ensure_user_profile(sender, instance, created, **kwargs):
    """Her kullanıcı için bir profil kaydı tut."""
    profile, was_created = Profile.objects.get_or_create(user=instance)
    if was_created and (instance.is_superuser or instance.is_staff):
        if instance.is_superuser:
            profile.role = Profile.ROLE_ADMIN
        else:
            profile.role = Profile.ROLE_STAFF
        profile.save(update_fields=['role'])


@receiver(post_save, sender=Profile)
def sync_profile_role_to_user(sender, instance, **kwargs):
    """Profilde seçilen yetkiyi kullanıcı hesabına uygula."""
    instance.apply_role_to_user()
