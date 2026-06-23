"""Admin customisations for the orders app."""

from django.contrib import admin
from django.utils.html import format_html

from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    """Show / edit the dishes selected for an order inline on the Order page."""

    model = OrderItem
    extra = 0
    autocomplete_fields = ('dish',)
    fields = ('dish', 'quantity', 'unit_price', 'line_total_display')
    readonly_fields = ('line_total_display',)

    @admin.display(description='Satır Toplamı (₺)')
    def line_total_display(self, obj):
        if obj.pk:
            return f'₺{obj.line_total:,.2f}'
        return '—'


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'full_name', 'organization_type', 'guest_count',
        'item_count', 'estimated_price_display', 'cost_display',
        'profit_display', 'margin_display',
        'payment_status', 'event_date', 'status', 'created_at',
    )
    list_display_links = ('id', 'full_name')
    list_filter = ('status', 'payment_status', 'organization_type', 'event_date')
    search_fields = ('full_name', 'email', 'phone', 'company', 'notes',
                     'payment_transaction_ref')
    list_editable = ('status',)
    date_hierarchy = 'event_date'
    change_list_template = 'admin/orders/order/change_list.html'
    readonly_fields = (
        'created_at', 'updated_at', 'items_total_display',
        'profit_summary_display', 'cost_summary_display',
        'margin_summary_display',
    )

    inlines = [OrderItemInline]

    fieldsets = (
        ('Müşteri', {
            'fields': ('full_name', 'company', 'email', 'phone'),
        }),
        ('Etkinlik', {
            'fields': ('organization_type', 'guest_count',
                       'event_date', 'event_time', 'event_address'),
        }),
        ('Detay', {
            'fields': ('notes',),
        }),
        ('Ödeme', {
            'fields': ('payment_status', 'payment_transaction_ref',
                       'payment_completed_at'),
        }),
        ('İşlem', {
            'fields': (
                'status', 'estimated_price', 'items_total_display',
                'cost_summary_display', 'profit_summary_display',
                'margin_summary_display',
                'created_at', 'updated_at',
            ),
        }),
    )

    actions = ['recalculate_estimated_price']

    @admin.display(description='Yemek')
    def item_count(self, obj):
        return obj.items.count()

    @admin.display(description='Tahmini Fiyat')
    def estimated_price_display(self, obj):
        if obj.estimated_price:
            return format_html('<strong>₺{}</strong>',
                               f'{obj.estimated_price:,.2f}')
        return '—'

    @admin.display(description='Maliyet')
    def cost_display(self, obj):
        if obj.revenue_amount:
            return f'₺{obj.cost_amount:,.2f}'
        return '—'

    @admin.display(description='Kar')
    def profit_display(self, obj):
        if obj.revenue_amount:
            return format_html('<strong>₺{}</strong>', f'{obj.profit_amount:,.2f}')
        return '—'

    @admin.display(description='Kar Oranı')
    def margin_display(self, obj):
        if obj.revenue_amount:
            return f'%{obj.profit_margin_percent}'
        return '—'

    @admin.display(description='Maliyet (₺)')
    def cost_summary_display(self, obj):
        return f'₺{obj.cost_amount:,.2f}'

    @admin.display(description='Kar (₺)')
    def profit_summary_display(self, obj):
        return f'₺{obj.profit_amount:,.2f}'

    @admin.display(description='Kar Oranı')
    def margin_summary_display(self, obj):
        return f'%{obj.profit_margin_percent} (ciro üzerinden)'

    @admin.display(description='Satırlardan Hesaplanan Toplam (₺)')
    def items_total_display(self, obj):
        total = obj.items_total if obj.pk else 0
        return f'₺{total:,.2f}'

    @admin.action(description='Tahmini fiyatı yemek satırlarından yeniden hesapla')
    def recalculate_estimated_price(self, request, queryset):
        updated = 0
        for order in queryset:
            order.recalculate_estimated_price()
            updated += 1
        self.message_user(request,
                          f'{updated} sipariş için tahmini fiyat güncellendi.')

    def save_related(self, request, form, formsets, change):
        """After inline OrderItem rows are saved, refresh estimated_price."""
        super().save_related(request, form, formsets, change)
        form.instance.recalculate_estimated_price()

    def changelist_view(self, request, extra_context=None):
        from orders.profit import aggregate_profit_stats

        qs = self.get_queryset(request).exclude(status='cancelled')
        extra_context = {
            **(extra_context or {}),
            'order_list_profit_summary': aggregate_profit_stats(qs),
        }
        return super().changelist_view(request, extra_context=extra_context)

    def has_add_permission(self, request):
        """Siparişler yalnızca web sitesi formundan oluşturulur."""
        return False
