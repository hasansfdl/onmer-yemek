"""Auth forms for the accounts app."""

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

User = get_user_model()


_text_attrs = {'class': 'form-control form-control-lg'}


class StyledLoginForm(AuthenticationForm):
    """Bootstrap-styled login form."""

    username = forms.CharField(
        label='Kullanıcı Adı',
        widget=forms.TextInput(attrs={
            **_text_attrs,
            'placeholder': 'Kullanıcı adınız',
            'autofocus': True,
        }),
    )
    password = forms.CharField(
        label='Şifre',
        widget=forms.PasswordInput(attrs={
            **_text_attrs,
            'placeholder': '••••••••',
        }),
    )


class RegisterForm(UserCreationForm):
    """Bootstrap-styled registration form."""

    email = forms.EmailField(
        label='E-posta',
        widget=forms.EmailInput(attrs={
            **_text_attrs,
            'placeholder': 'ornek@firma.com',
        }),
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={
                **_text_attrs,
                'placeholder': 'Kullanıcı Adı',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget = forms.PasswordInput(attrs={
            **_text_attrs, 'placeholder': 'Şifre'})
        self.fields['password2'].widget = forms.PasswordInput(attrs={
            **_text_attrs, 'placeholder': 'Şifre (tekrar)'})
        for field in self.fields.values():
            field.help_text = ''
