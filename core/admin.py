"""Admin customisations for site-wide content models."""

from django.contrib import admin

from .models import (
    ContactMessage,
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
    change_list_template = 'admin/core/statistic/change_list.html'

    def changelist_view(self, request, extra_context=None):
        from orders.models import Order
        from orders.profit import aggregate_profit_stats

        active_orders = Order.objects.exclude(status='cancelled')
        all_orders = Order.objects.order_by('-created_at')
        extra_context = {
            **(extra_context or {}),
            'order_profit_summary': aggregate_profit_stats(active_orders),
            'order_profit_rows': all_orders,
        }
        return super().changelist_view(request, extra_context=extra_context)

    def has_add_permission(self, request):
        return False


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
