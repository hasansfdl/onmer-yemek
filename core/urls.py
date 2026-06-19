"""URL routes for the core (marketing) app."""

from django.urls import path

from . import views

app_name = 'core'

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('hakkimizda/', views.AboutView.as_view(), name='about'),
    path('iletisim/', views.ContactView.as_view(), name='contact'),
    path('lokasyon/', views.LocationView.as_view(), name='location'),
]
