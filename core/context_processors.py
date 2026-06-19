"""Inject brand-wide variables into every template render.

Reading from the database for every request would be wasteful, so we cache
the SiteSetting singleton on the request object and gracefully fall back to
the values defined in `settings.py` when migrations have not been run yet
(e.g. immediately after `startproject`).
"""

from django.conf import settings


def site_settings(request):
    """Return brand info & navigation primitives for templates."""

    # Lazy import — the `core` app might not yet be migrated when this module
    # is first imported (for example during `migrate`).
    from .models import SiteSetting

    try:
        site = SiteSetting.load()
    except Exception:  # pragma: no cover - DB might not be ready
        site = None

    if site is None:
        # Fallback dictionary so templates always have a value to render.
        ctx = {
            'company_name': settings.SITE_NAME,
            'tagline': settings.SITE_TAGLINE,
            'phone': settings.SITE_PHONE,
            'whatsapp': settings.SITE_WHATSAPP,
            'email': settings.SITE_EMAIL,
            'address': settings.SITE_ADDRESS,
            'social': settings.SITE_SOCIAL,
            'site': None,
        }
    else:
        ctx = {
            'company_name': site.company_name,
            'tagline': site.tagline,
            'phone': site.phone,
            'whatsapp': site.whatsapp,
            'email': site.email,
            'address': site.address,
            'social': {
                'instagram': site.instagram,
                'facebook': site.facebook,
                'twitter': site.twitter,
                'youtube': site.youtube,
            },
            'site': site,
        }

    # Top-level navbar links used by base.html.
    ctx['main_nav'] = [
        {'name': 'Ana Sayfa', 'url': 'core:home'},
        {'name': 'Hakkımızda', 'url': 'core:about'},
        {'name': 'Menü', 'url': 'menu:list'},
        {'name': 'Galeri', 'url': 'portfolio:list'},
        {'name': 'İletişim', 'url': 'core:contact'},
    ]
    return ctx
