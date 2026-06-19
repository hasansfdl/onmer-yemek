"""Reservation views — booking page + AJAX slot lookup."""

from datetime import datetime

from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.views.generic import CreateView, TemplateView

from .forms import TIME_SLOTS, ReservationForm
from .models import Reservation


class ReservationCreateView(CreateView):
    """Public reservation booking page."""

    model = Reservation
    form_class = ReservationForm
    template_name = 'reservations/reservation_form.html'
    success_url = reverse_lazy('reservations:success')

    def form_valid(self, form):
        response = super().form_valid(form)
        self.request.session['last_reservation_id'] = self.object.pk
        messages.success(
            self.request,
            'Randevunuz oluşturuldu! Onay için sizi arayacağız.',
        )
        return response

    def form_invalid(self, form):
        messages.error(
            self.request,
            'Randevu oluşturulamadı. Lütfen formu kontrol edin.',
        )
        return super().form_invalid(form)


class ReservationSuccessView(TemplateView):
    template_name = 'reservations/reservation_success.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        rid = self.request.session.pop('last_reservation_id', None)
        if rid:
            ctx['reservation'] = Reservation.objects.filter(pk=rid).first()
        return ctx


def available_slots(request):
    """Return free time slots for a specific date as JSON.

    Used by the booking form's date picker to live-update the time
    dropdown without a page reload.
    """
    raw = request.GET.get('date', '')
    try:
        day = datetime.strptime(raw, '%Y-%m-%d').date()
    except ValueError:
        return JsonResponse({'slots': [s[0] for s in TIME_SLOTS]})

    taken = set(
        Reservation.objects
        .filter(date=day)
        .filter(~Q(status='cancelled'))
        .values_list('time', flat=True)
    )
    taken_str = {t.strftime('%H:%M') for t in taken}
    free = [s[0] for s in TIME_SLOTS if s[0] not in taken_str]
    return JsonResponse({'slots': free, 'taken': sorted(taken_str)})
