"""İletişim formu mesajlarına e-posta ile yanıt."""

from __future__ import annotations

import logging

from django.conf import settings
from django.core.mail import EmailMessage
from django.utils import timezone

from core.models import ContactMessage, SiteSetting

logger = logging.getLogger(__name__)


def send_contact_reply(
    message: ContactMessage,
    reply_body: str,
    *,
    staff_user=None,
) -> None:
    """Müşteriye yanıt e-postası gönderir ve kaydı günceller."""
    body = (reply_body or "").strip()
    if not body:
        raise ValueError("Yanıt metni boş olamaz.")

    site = SiteSetting.load()
    company = site.company_name or "Onmer Yemek Organizasyon"
    subject = f"Re: {message.subject}"

    text = (
        f"Merhaba {message.full_name},\n\n"
        f"{body}\n\n"
        f"---\n"
        f"{company}\n"
        f"{site.email or ''}\n"
        f"{site.phone or ''}\n"
    )

    from_email = settings.DEFAULT_FROM_EMAIL
    email = EmailMessage(
        subject=subject,
        body=text,
        from_email=from_email,
        to=[message.email],
        reply_to=[site.email] if site.email else None,
    )
    email.send(fail_silently=False)

    message.reply_text = body
    message.replied_at = timezone.now()
    message.replied_by = staff_user
    message.is_read = True
    message.save(
        update_fields=[
            "reply_text",
            "replied_at",
            "replied_by",
            "is_read",
        ]
    )
    logger.info(
        "Contact reply sent for message #%s to %s",
        message.pk,
        message.email,
    )
