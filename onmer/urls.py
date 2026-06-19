"""Project-level URL configuration for Onmer Yemek Organizasyon."""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

# Customize the admin titles to give it a premium-feeling brand identity.
admin.site.site_header = 'Onmer Yönetim Paneli'
admin.site.site_title = 'Onmer Admin'
admin.site.index_title = 'Onmer Yemek Organizasyon · Kontrol Paneli'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include(('core.urls', 'core'), namespace='core')),
    path('hesap/', include(('accounts.urls', 'accounts'), namespace='accounts')),
    path('menu/', include(('menu.urls', 'menu'), namespace='menu')),
    path('siparis/', include(('orders.urls', 'orders'), namespace='orders')),
    path('randevu/', include(('reservations.urls', 'reservations'), namespace='reservations')),
    path('galeri/', include(('portfolio.urls', 'portfolio'), namespace='portfolio')),
]

# Serve uploaded media + static during development.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Custom error handlers
handler404 = 'core.views.custom_404'
