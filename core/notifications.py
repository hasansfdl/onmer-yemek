"""Shared helpers for outbound mail to the brand inbox."""

from __future__ import annotations

import logging

from django.conf import settings
from django.core.mail import EmailMultiAlternatives

from .models import SiteSetting

logger = logging.getLogger(__name__)


def get_brand_inbox() -> str | None:
    """Return the inbox that should receive site notifications."""
    site = SiteSetting.load()
    candidates = [
        (site.email or '').strip(),
        getattr(settings, 'NOTIFICATION_EMAIL', '').strip(),
        getattr(settings, 'SITE_EMAIL', '').strip(),
        (settings.EMAIL_HOST_USER or '').strip(),
    ]
    for address in candidates:
        if address:
            return address
    from_email = (settings.DEFAULT_FROM_EMAIL or '').strip()
    if '<' in from_email and '>' in from_email:
        return from_email.split('<', 1)[1].split('>', 1)[0].strip()
    return from_email or None


def smtp_configured() -> bool:
    backend = (settings.EMAIL_BACKEND or '').lower()
    return 'smtp' in backend and bool(settings.EMAIL_HOST_USER and settings.EMAIL_HOST_PASSWORD)


def send_brand_mail(
    *,
    subject: str,
    text_body: str,
    html_body: str,
    reply_to: list[str] | None = None,
) -> str:
    """Send HTML + plain-text mail to the configured brand inbox."""
    recipient = get_brand_inbox()
    if not recipient:
        raise ValueError('Bildirim alıcı e-postası yapılandırılmamış.')

    email = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[recipient],
        reply_to=reply_to or None,
    )
    email.attach_alternative(html_body, 'text/html')
    email.send(fail_silently=False)
    logger.info('Brand notification sent to %s — %s', recipient, subject)
    return recipient
