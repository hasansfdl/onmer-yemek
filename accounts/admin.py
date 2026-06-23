"""Admin customisations for the accounts app."""

from django.contrib import admin
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

from .models import Profile

User = get_user_model()

admin.site.unregister(Group)
try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'role',
        'email',
        'company',
        'phone',
        'date_joined',
        'is_active',
    )
    list_filter = ('role', 'user__is_active')
    list_editable = ('role',)
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
        'role',
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

    def get_list_editable(self, request):
        if request.user.is_superuser:
            return self.list_editable
        return ()

    def get_readonly_fields(self, request, obj=None):
        readonly = list(super().get_readonly_fields(request, obj))
        if not request.user.is_superuser:
            readonly.append('role')
        return readonly

    def save_model(self, request, obj, form, change):
        if (
            change
            and obj.user_id == request.user.id
            and obj.role != Profile.ROLE_ADMIN
            and request.user.is_superuser
        ):
            obj.role = Profile.ROLE_ADMIN
            messages.warning(
                request,
                'Kendi hesabınızın tam yetkisini kaldıramazsınız.',
            )
        super().save_model(request, obj, form, change)

    def has_add_permission(self, request):
        """Kullanıcılar site kaydı veya süper yönetici ile oluşturulur."""
        return False

    def has_delete_permission(self, request, obj=None):
        if obj and obj.user_id == request.user.id:
            return False
        return request.user.is_superuser
