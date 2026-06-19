from django.apps import AppConfig


class ReservationsConfig(AppConfig):
    """Reservations app: appointment / consultation booking system."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'reservations'
    verbose_name = 'Randevu Sistemi'
