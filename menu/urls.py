"""URL routes for the menu app."""

from django.urls import path
from django.views.generic import RedirectView

from . import views

app_name = 'menu'

urlpatterns = [
    path(
        'yemekler/',
        RedirectView.as_view(
            pattern_name='menu:list',
            permanent=False,
            query_string=True,
        ),
        name='dishes',
    ),
    path('yemek/<slug:slug>/', views.DishDetailView.as_view(),
         name='dish_detail'),
    path('', views.DishListView.as_view(), name='list'),
]
