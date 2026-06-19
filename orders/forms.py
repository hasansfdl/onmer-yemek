"""Public-facing forms for the orders app."""

import re
from datetime import date
from decimal import Decimal

from django import forms

from menu.models import Dish

from .models import Order


class OrderForm(forms.ModelForm):
    """Bulk catering order request form.

    The dish selection grid is rendered manually in the template (each dish
    has a name="qty_<dish_id>" number input). When `request.POST` is bound to
    this form we parse those values into a `cleaned_dish_quantities` dict and
    fail validation if no dish has been selected. The view then turns that
    dict into OrderItem rows.
    """

    class Meta:
        model = Order
        fields = [
            'full_name', 'company', 'email', 'phone',
            'organization_type', 'guest_count',
            'event_date', 'event_time', 'event_address',
            'notes',
        ]
        widgets = {
            'full_name': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'Ad Soyad',
            }),
            'company': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'Firma (opsiyonel)',
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'ornek@firma.com',
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': '+90 555 123 45 67',
            }),
            'organization_type': forms.Select(attrs={
                'class': 'form-select form-select-lg',
            }),
            'guest_count': forms.NumberInput(attrs={
                'class': 'form-control form-control-lg',
                'min': 10,
                'placeholder': 'Örn: 250',
            }),
            'event_date': forms.DateInput(attrs={
                'class': 'form-control form-control-lg',
                'type': 'date',
            }),
            'event_time': forms.TimeInput(attrs={
                'class': 'form-control form-control-lg',
                'type': 'time',
            }),
            'event_address': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'Etkinlik adresi',
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Özel istekler, alerjenler, menü tercihleri...',
            }),
        }

    def clean_guest_count(self):
        value = self.cleaned_data['guest_count']
        if value < 10:
            raise forms.ValidationError(
                'Toplu sipariş için minimum kişi sayısı 10 olmalıdır.'
            )
        return value

    def clean_event_date(self):
        value = self.cleaned_data['event_date']
        if value < date.today():
            raise forms.ValidationError('Etkinlik tarihi geçmiş olamaz.')
        return value

    # ---------- Dish selection (parsed from raw POST) ----------

    def clean(self):
        """Parse `qty_<id>` POST values into `cleaned_dish_quantities`."""
        cleaned = super().clean()

        # Bind requires a `data` mapping (request.POST); when unbound we skip.
        if not self.is_bound:
            return cleaned

        active_dishes = {d.id: d for d in Dish.objects.filter(is_active=True)}
        selections: dict[Dish, tuple[int, Decimal]] = {}

        for dish_id, dish in active_dishes.items():
            raw = self.data.get(f'qty_{dish_id}', '0') or '0'
            try:
                qty = int(raw)
            except (TypeError, ValueError):
                qty = 0
            if qty < 0:
                qty = 0
            if qty > 0:
                selections[dish] = (qty, dish.price)

        if not selections:
            raise forms.ValidationError(
                'Lütfen en az bir yemek seçip adetini belirtin.',
                code='no_dish_selected',
            )

        # Stash for the view's form_valid() to materialise as OrderItem rows.
        self.cleaned_dish_quantities = selections
        return cleaned


class OrderPaymentForm(forms.Form):
    """Card checkout form — data is validated then discarded (not stored).

    Production sites should replace the view logic with a PCI-compliant
    gateway (iyzico, Stripe, PayTR, bank 3D Secure iframe, etc.).
    """

    card_holder = forms.CharField(
        label='Kart Üzerindeki İsim',
        max_length=80,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg text-uppercase',
            'placeholder': 'AD SOYAD',
            'autocomplete': 'cc-name',
        }),
    )
    card_number = forms.CharField(
        label='Kart Numarası',
        max_length=32,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg js-card-number',
            'placeholder': '0000 0000 0000 0000',
            'autocomplete': 'cc-number',
            'inputmode': 'numeric',
        }),
    )
    expiry = forms.CharField(
        label='Son Kullanma Tarihi',
        max_length=9,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg js-card-expiry',
            'placeholder': 'AA / YY',
            'autocomplete': 'cc-exp',
            'inputmode': 'numeric',
        }),
    )
    cvv = forms.CharField(
        label='Güvenlik Kodu (CVV)',
        max_length=4,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': '•••',
            'autocomplete': 'cc-csc',
            'inputmode': 'numeric',
        }),
    )

    def clean_card_holder(self):
        name = ' '.join(self.cleaned_data['card_holder'].split())
        if len(name) < 3:
            raise forms.ValidationError('Lütfen kart üzerindeki ismi girin.')
        return name.upper()

    def clean_card_number(self):
        # Formalite: gerçek doğrulama yok; boş bırakılmasın.
        raw = (self.cleaned_data.get('card_number') or '').strip()
        if not raw:
            raise forms.ValidationError('Kart numarası girin.')
        return raw

    def clean_expiry(self):
        raw = re.sub(r'\D', '', self.cleaned_data.get('expiry', ''))
        if not re.fullmatch(r'\d{4}', raw):
            raise forms.ValidationError('Son kullanma AA/YY olarak 4 rakam girin (örn. 12 / 28).')
        mm = int(raw[:2])
        yy = int(raw[2:])
        if mm < 1 or mm > 12:
            raise forms.ValidationError('Ay 01–12 arasında olmalıdır.')
        return raw

    def clean_cvv(self):
        raw = re.sub(r'\D', '', self.cleaned_data.get('cvv', ''))
        if len(raw) not in (3, 4):
            raise forms.ValidationError('CVV 3 veya 4 haneli olmalıdır.')
        return raw
