"""URL routes for the orders app."""

from django.urls import path

from . import views

app_name = 'orders'

urlpatterns = [
    path('', views.OrderCreateView.as_view(), name='create'),
    path('odeme/', views.OrderPaymentView.as_view(), name='payment'),
    path('basarili/', views.OrderSuccessView.as_view(), name='success'),
]
