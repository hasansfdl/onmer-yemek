"""URL routes for the reservations app."""

from django.urls import path

from . import views

app_name = 'reservations'

urlpatterns = [
    path('', views.ReservationCreateView.as_view(), name='create'),
    path('basarili/', views.ReservationSuccessView.as_view(), name='success'),
    path('uygun-saatler/', views.available_slots, name='available_slots'),
]
