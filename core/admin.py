"""Admin customisations for site-wide content models."""

from django.contrib import admin

from .models import (
    ContactMessage,
    Service,
    SiteSetting,
    Statistic,
)


@admin.register(SiteSetting)
class SiteSettingAdmin(admin.ModelAdmin):
    """Singleton admin – disallow add/delete, force in-place editing."""

    fieldsets = (
        ('Marka & Slogan', {
            'fields': ('company_name', 'tagline', 'hero_title', 'hero_subtitle'),
        }),
        ('İletişim', {
            'fields': ('phone', 'whatsapp', 'email', 'address'),
        }),
        ('Sosyal Medya', {
            'fields': ('instagram', 'facebook', 'twitter', 'youtube'),
        }),
        ('Kurumsal', {
            'fields': ('about_short', 'about_long', 'mission', 'vision'),
        }),
        ('Harita', {
            'fields': ('google_maps_embed',),
        }),
    )

    def has_add_permission(self, request):
        return not SiteSetting.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Statistic)
class StatisticAdmin(admin.ModelAdmin):
    list_display = ('label', 'value', 'suffix', 'icon', 'order')
    list_editable = ('value', 'suffix', 'order')
    ordering = ('order',)


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('title', 'icon', 'order', 'is_active')
    list_editable = ('order', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('title', 'short_description')


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = (
        'full_name',
        'email',
        'subject',
        'is_read',
        'replied_at',
        'created_at',
    )
    list_filter = ('is_read', 'created_at', 'replied_at')
    search_fields = ('full_name', 'email', 'subject', 'message', 'reply_text')
    readonly_fields = (
        'full_name',
        'email',
        'phone',
        'subject',
        'message',
        'created_at',
        'replied_at',
        'replied_by',
    )
    fields = (
        'full_name',
        'email',
        'phone',
        'subject',
        'message',
        'is_read',
        'reply_text',
        'replied_at',
        'replied_by',
        'created_at',
    )
    list_editable = ('is_read',)
    date_hierarchy = 'created_at'

    def has_add_permission(self, request):
        return False
