"""Forms for the reservation booking system."""

from datetime import date, time

from django import forms
from django.db.models import Q

from .models import Reservation


# Allowed booking time slots: 30-minute increments, 09:00–18:00.
TIME_SLOTS = [
    ('09:00', '09:00'),
    ('09:30', '09:30'),
    ('10:00', '10:00'),
    ('10:30', '10:30'),
    ('11:00', '11:00'),
    ('11:30', '11:30'),
    ('12:00', '12:00'),
    ('13:00', '13:00'),
    ('13:30', '13:30'),
    ('14:00', '14:00'),
    ('14:30', '14:30'),
    ('15:00', '15:00'),
    ('15:30', '15:30'),
    ('16:00', '16:00'),
    ('16:30', '16:30'),
    ('17:00', '17:00'),
    ('17:30', '17:30'),
]


class ReservationForm(forms.ModelForm):
    """Booking form with conflict-detection on (date, time)."""

    time = forms.ChoiceField(
        label='Saat',
        choices=TIME_SLOTS,
        widget=forms.Select(attrs={'class': 'form-select form-select-lg'}),
    )

    class Meta:
        model = Reservation
        fields = ['full_name', 'email', 'phone', 'date', 'time',
                  'topic', 'note']
        widgets = {
            'full_name': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'Ad Soyad',
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'E-posta',
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'Telefon',
            }),
            'date': forms.DateInput(attrs={
                'class': 'form-control form-control-lg',
                'type': 'date',
            }),
            'topic': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'Görüşmek istediğiniz konu',
            }),
            'note': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Eklemek istediğiniz notlar...',
            }),
        }

    def clean_date(self):
        value = self.cleaned_data['date']
        if value < date.today():
            raise forms.ValidationError('Geçmiş bir tarih seçilemez.')
        return value

    def clean(self):
        cleaned = super().clean()
        d = cleaned.get('date')
        t = cleaned.get('time')
        if d and t:
            # Convert "HH:MM" -> time object
            try:
                hh, mm = t.split(':')
                t_obj = time(int(hh), int(mm))
            except (ValueError, AttributeError):
                self.add_error('time', 'Geçersiz saat formatı.')
                return cleaned
            cleaned['time'] = t_obj

            # Block double-booking for the same active slot.
            conflict = (
                Reservation.objects
                .filter(date=d, time=t_obj)
                .filter(~Q(status='cancelled'))
                .exists()
            )
            if conflict:
                raise forms.ValidationError(
                    'Seçtiğiniz tarih ve saat dolu görünüyor. '
                    'Lütfen başka bir saat deneyiniz.'
                )
        return cleaned
