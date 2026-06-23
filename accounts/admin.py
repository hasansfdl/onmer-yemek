"""Admin customisations for the accounts app."""

from django.contrib import admin
from django.contrib.auth.models import Group

from .models import Profile

admin.site.unregister(Group)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'email',
        'company',
        'phone',
        'date_joined',
        'is_active',
    )
    list_filter = ('user__is_active',)
    search_fields = (
        'user__username',
        'user__email',
        'user__first_name',
        'user__last_name',
        'phone',
        'company',
    )
    readonly_fields = ('user', 'email', 'date_joined', 'last_login')
    fields = (
        'user',
        'email',
        'date_joined',
        'last_login',
        'company',
        'phone',
        'note',
    )
    ordering = ('-user__date_joined',)

    @admin.display(description='E-posta', ordering='user__email')
    def email(self, obj):
        return obj.user.email or '—'

    @admin.display(description='Kayıt tarihi', ordering='user__date_joined')
    def date_joined(self, obj):
        return obj.user.date_joined

    @admin.display(description='Aktif', boolean=True, ordering='user__is_active')
    def is_active(self, obj):
        return obj.user.is_active

    @admin.display(description='Son giriş')
    def last_login(self, obj):
        return obj.user.last_login or '—'

    def has_add_permission(self, request):
        """Profiller kayıt sırasında otomatik oluşturulur."""
        return False
