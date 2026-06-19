"""URL routes for the accounts app."""

from django.urls import path

from . import views

app_name = 'accounts'

urlpatterns = [
    path('giris/', views.CustomLoginView.as_view(), name='login'),
    path('cikis/', views.CustomLogoutView.as_view(), name='logout'),
    path('kayit/', views.RegisterView.as_view(), name='register'),
]
