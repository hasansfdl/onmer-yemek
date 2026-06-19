"""Forms for the core app (contact form)."""

from django import forms

from .models import ContactMessage


class ContactForm(forms.ModelForm):
    """Bootstrap-styled contact form."""

    class Meta:
        model = ContactMessage
        fields = ['full_name', 'email', 'phone', 'subject', 'message']
        widgets = {
            'full_name': forms.TextInput(attrs={
                'class': 'form-control form-control-lg bg-dark border-0 text-white',
                'placeholder': 'Ad Soyad',
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control form-control-lg bg-dark border-0 text-white',
                'placeholder': 'E-posta',
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control form-control-lg bg-dark border-0 text-white',
                'placeholder': 'Telefon (opsiyonel)',
            }),
            'subject': forms.TextInput(attrs={
                'class': 'form-control form-control-lg bg-dark border-0 text-white',
                'placeholder': 'Konu',
            }),
            'message': forms.Textarea(attrs={
                'class': 'form-control bg-dark border-0 text-white',
                'placeholder': 'Mesajınız...',
                'rows': 5,
            }),
        }

    def clean_full_name(self):
        value = self.cleaned_data['full_name'].strip()
        if len(value) < 3:
            raise forms.ValidationError('Lütfen geçerli bir ad soyad giriniz.')
        return value
