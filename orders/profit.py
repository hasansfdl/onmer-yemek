"""Sipariş kar / maliyet hesapları (%45 kar marjı)."""

from __future__ import annotations

from decimal import Decimal

PROFIT_MARGIN_RATE = Decimal('0.45')
PROFIT_MARGIN_PERCENT = 45


def quantize_money(value: Decimal) -> Decimal:
    return value.quantize(Decimal('0.01'))


def revenue_for_order(order) -> Decimal:
    return order.estimated_price or Decimal('0')


def profit_for_order(order) -> Decimal:
    return quantize_money(revenue_for_order(order) * PROFIT_MARGIN_RATE)


def cost_for_order(order) -> Decimal:
    return quantize_money(revenue_for_order(order) - profit_for_order(order))


def aggregate_profit_stats(queryset) -> dict:
    revenue = Decimal('0')
    count = 0
    for order in queryset.iterator():
        revenue += revenue_for_order(order)
        count += 1
    profit = quantize_money(revenue * PROFIT_MARGIN_RATE)
    cost = quantize_money(revenue - profit)
    return {
        'order_count': count,
        'revenue': revenue,
        'profit': profit,
        'cost': cost,
        'margin_percent': PROFIT_MARGIN_PERCENT,
    }
