"""Yönetim paneli ana sayfasına sipariş özeti ekler."""

from __future__ import annotations

from functools import wraps


def patch_admin_index() -> None:
    from django.contrib import admin

    if getattr(admin.site, '_onmer_orders_patched', False):
        return

    original_index = admin.site.index

    @wraps(original_index)
    def index_with_orders(request, extra_context=None):
        from orders.models import Order
        from orders.profit import aggregate_profit_stats

        active_orders = Order.objects.exclude(status='cancelled')
        profit_summary = aggregate_profit_stats(active_orders)
        context = {
            'orders_stats': {
                'new': Order.objects.filter(status='new').count(),
                'total': Order.objects.count(),
                'pending_payment': Order.objects.filter(
                    payment_status='pending',
                ).count(),
                'total_profit': profit_summary['profit'],
            },
            'recent_orders': (
                Order.objects.order_by('-created_at')
                .prefetch_related('items')[:20]
            ),
            'orders_changelist_url': 'admin:orders_order_changelist',
        }
        if extra_context:
            context.update(extra_context)
        return original_index(request, context)

    admin.site.index = index_with_orders
    admin.site.index_template = 'admin/onmer_index.html'
    admin.site._onmer_orders_patched = True
