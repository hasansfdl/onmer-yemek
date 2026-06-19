from django.apps import AppConfig


class MenuConfig(AppConfig):
    """Menu app: dish catalog + daily/weekly menu management."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'menu'
    verbose_name = 'Menü Yönetimi'
