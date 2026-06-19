from django.apps import AppConfig


class AccountsConfig(AppConfig):
    """Accounts app: customer login / registration / profile."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'
    verbose_name = 'Kullanıcı Hesapları'
