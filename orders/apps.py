from django.apps import AppConfig


class OrdersConfig(AppConfig):
    """Orders app: bulk catering order requests."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'orders'
    verbose_name = 'Siparişler'
