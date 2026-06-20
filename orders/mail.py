"""Outbound e-mail notifications for the orders app."""

import logging

from django.template.loader import render_to_string

from core.models import SiteSetting
from core.notifications import send_brand_mail

from .models import Order

logger = logging.getLogger(__name__)


def _order_mail_context(request, order: Order) -> dict:
    site = SiteSetting.load()
    items = list(order.items.select_related('dish').all())
    return {
        'order': order,
        'order_items': items,
        'order_total': order.items_total,
        'site': site,
        'company_name': site.company_name,
        'admin_url': request.build_absolute_uri(
            f'/admin/orders/order/{order.pk}/change/',
        ),
    }


def notify_brand_new_order(request, order: Order) -> None:
    """Site ayarlarındaki e-posta adresine yeni sipariş bildirimi gönder."""
    ctx = _order_mail_context(request, order)
    subject = (
        f'[{ctx["company_name"]}] Yeni sipariş talebi '
        f'#ONMER-{order.pk:05d}'
    )
    send_brand_mail(
        subject=subject,
        text_body=render_to_string('orders/emails/order_new_notify.txt', ctx),
        html_body=render_to_string('orders/emails/order_new_notify.html', ctx),
        reply_to=[order.email],
    )
    logger.info('Order #%s new-order mail sent', order.pk)


def notify_brand_order_paid(request, order: Order) -> None:
    """Ödeme tamamlandığında site ayarlarındaki e-posta adresine bildirim gönder."""
    ctx = _order_mail_context(request, order)
    subject = (
        f'[{ctx["company_name"]}] Sipariş ödeme onayı '
        f'#ONMER-{order.pk:05d}'
    )
    send_brand_mail(
        subject=subject,
        text_body=render_to_string('orders/emails/order_paid_notify.txt', ctx),
        html_body=render_to_string('orders/emails/order_paid_notify.html', ctx),
        reply_to=[order.email],
    )
    logger.info('Order #%s paid-notification mail sent', order.pk)
