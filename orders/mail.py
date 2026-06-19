"""Outbound e-mail notifications for the orders app."""

import logging

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

from core.models import SiteSetting

from .models import Order

logger = logging.getLogger(__name__)


def notify_brand_order_paid(request, order: Order) -> None:
    """Send the site inbox (SiteSetting.email) a notice that payment completed.

    Card data is never included. Mirrors the contact form recipient logic.
    """
    site = SiteSetting.load()
    recipient = (
        site.email
        or getattr(settings, 'SITE_EMAIL', None)
        or settings.DEFAULT_FROM_EMAIL
    )
    if not recipient:
        logger.warning('No order-notification recipient configured; skipping mail.')
        return

    items = list(order.items.select_related('dish').all())
    ctx = {
        'order': order,
        'order_items': items,
        'order_total': order.items_total,
        'site': site,
        'company_name': site.company_name,
        'admin_url': request.build_absolute_uri(
            f'/admin/orders/order/{order.pk}/change/',
        ),
    }
    subject = (
        f'[{site.company_name}] Yeni sipariş — ödeme onayı '
        f'#ONMER-{order.pk:05d}'
    )
    text_body = render_to_string('orders/emails/order_paid_notify.txt', ctx)
    html_body = render_to_string('orders/emails/order_paid_notify.html', ctx)

    email = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[recipient],
        reply_to=[order.email],
    )
    email.attach_alternative(html_body, 'text/html')
    email.send(fail_silently=False)
    logger.info('Order #%s paid-notification mail sent to %s', order.pk, recipient)
