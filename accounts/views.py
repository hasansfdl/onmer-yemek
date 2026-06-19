"""Auth views: login, logout, register."""

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView

from .forms import RegisterForm, StyledLoginForm


class CustomLoginView(LoginView):
    """Branded login screen."""

    template_name = 'accounts/login.html'
    authentication_form = StyledLoginForm
    redirect_authenticated_user = True


class CustomLogoutView(LogoutView):
    next_page = reverse_lazy('core:home')


class RegisterView(CreateView):
    """Public registration page."""

    form_class = RegisterForm
    template_name = 'accounts/register.html'
    success_url = reverse_lazy('core:home')

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        messages.success(
            self.request,
            f'Hoş geldiniz, {user.username}! Hesabınız oluşturuldu.',
        )
        return redirect(self.success_url)
