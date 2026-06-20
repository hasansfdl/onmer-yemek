"""Public marketing views (home, about, contact, location)."""

import logging

from django.contrib import messages
from django.shortcuts import render
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.views.generic import CreateView, TemplateView

from core.notifications import send_brand_mail

from menu.models import Dish, MenuCategory
from portfolio.models import PortfolioItem

from .forms import ContactForm
from .models import (
    FleetVehicle,
    Service,
    ServiceArea,
    SiteSetting,
    Statistic,
)

logger = logging.getLogger(__name__)


class HomeView(TemplateView):
    """Landing page with hero, services, featured dishes & gallery teaser."""

    template_name = 'core/home.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update({
            'services': Service.objects.filter(is_active=True),
            'featured_dishes': Dish.objects.filter(
                is_featured=True,
            ).select_related('category').order_by('-is_active', 'order', 'name')[:6],
            'categories': MenuCategory.objects.filter(is_active=True)[:5],
            'gallery_preview': PortfolioItem.objects.filter(
                is_published=True,
            )[:8],
        })
        return ctx


class AboutView(TemplateView):
    """Hakkımızda page — company story, mission/vision, statistics."""

    template_name = 'core/about.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update({
            'statistics': Statistic.objects.all(),
            'services': Service.objects.filter(is_active=True),
        })
        return ctx


class LocationView(TemplateView):
    """Location & logistics page (map + service areas + fleet)."""

    template_name = 'core/location.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update({
            'service_areas': ServiceArea.objects.filter(is_active=True),
            'fleet': FleetVehicle.objects.filter(is_active=True),
        })
        return ctx


class ContactView(CreateView):
    """Contact form view — saves the message, e-mails the brand inbox, redirects."""

    form_class = ContactForm
    template_name = 'core/contact.html'
    success_url = reverse_lazy('core:contact')

    def form_valid(self, form):
        response = super().form_valid(form)
        # Try to deliver the mail asynchronously-ish: even if the SMTP server
        # is misconfigured, we never want the user-facing flow to fail.
        try:
            self._notify_brand_inbox(self.object)
        except Exception:
            logger.exception(
                'Contact mail delivery failed for message #%s', self.object.pk,
            )
        messages.success(
            self.request,
            'Mesajınız başarıyla iletildi. En kısa sürede size dönüş yapacağız.',
        )
        return response

    def form_invalid(self, form):
        messages.error(
            self.request,
            'Form gönderilemedi. Lütfen alanları kontrol ediniz.',
        )
        return super().form_invalid(form)

    # ------------------------------------------------------------------
    # E-mail helpers
    # ------------------------------------------------------------------
    def _notify_brand_inbox(self, message):
        """Send the contact message to the e-mail saved on SiteSetting."""

        site = SiteSetting.load()
        ctx = {
            'msg': message,
            'site': site,
            'company_name': site.company_name,
            'admin_url': self.request.build_absolute_uri(
                f'/admin/core/contactmessage/{message.pk}/change/'
            ),
        }
        subject = (
            f'[{site.company_name}] Yeni iletişim mesajı: {message.subject}'
        )
        send_brand_mail(
            subject=subject,
            text_body=render_to_string('core/emails/contact_message.txt', ctx),
            html_body=render_to_string('core/emails/contact_message.html', ctx),
            reply_to=[message.email],
        )
        logger.info('Contact message #%s delivered', message.pk)


def custom_404(request, exception):  # pragma: no cover - simple error page
    return render(request, 'core/404.html', status=404)
