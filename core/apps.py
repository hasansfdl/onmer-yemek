from django.apps import AppConfig


class CoreConfig(AppConfig):
    """Core app: shared site content (home, about, contact, services)."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    verbose_name = 'Site Geneli'

    def ready(self):
        from .admin_dashboard import patch_admin_index

        patch_admin_index()
