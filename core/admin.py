"""Admin customisations for site-wide content models."""

from django.contrib import admin
from django.utils.html import format_html

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
    list_display = ('label', 'value', 'suffix', 'order')
    list_editable = ('value', 'suffix', 'order')
    fields = ('label', 'value', 'suffix', 'order')
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
        'message_preview',
        'is_read',
        'replied_at',
        'created_at',
    )
    list_display_links = ('full_name', 'subject')
    list_filter = ('is_read', 'created_at', 'replied_at')
    search_fields = ('full_name', 'email', 'subject', 'message', 'reply_text')
    readonly_fields = (
        'full_name',
        'email',
        'phone',
        'subject',
        'message_display',
        'created_at',
        'replied_at',
        'replied_by',
    )
    fieldsets = (
        ('Gönderen', {
            'fields': ('full_name', 'email', 'phone', 'created_at'),
        }),
        ('Mesaj', {
            'fields': ('subject', 'message_display'),
            'description': 'Mesajın tam metni aşağıdadır.',
        }),
        ('Yanıt ve durum', {
            'fields': ('is_read', 'reply_text', 'replied_at', 'replied_by'),
        }),
    )
    list_editable = ('is_read',)
    date_hierarchy = 'created_at'

    @admin.display(description='Mesaj özeti')
    def message_preview(self, obj):
        text = (obj.message or '').strip()
        if not text:
            return '—'
        preview = text.replace('\n', ' ')
        if len(preview) > 100:
            preview = f'{preview[:100]}…'
        return preview

    @admin.display(description='Mesaj içeriği')
    def message_display(self, obj):
        text = (obj.message or '').strip()
        if not text:
            return '—'
        return format_html(
            '<div style="white-space: pre-wrap; line-height: 1.5; max-width: 760px; '
            'padding: 14px 16px; background: #f8f9fa; border: 1px solid #ced4da; '
            'border-radius: 8px; font-size: 14px;">{}</div>',
            text,
        )

    def has_add_permission(self, request):
        return False
