"""Admin customisations for the accounts app."""

from django.contrib import admin
from django.contrib.auth.models import Group

from .models import Profile

admin.site.unregister(Group)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'company', 'phone')
    search_fields = ('user__username', 'user__email', 'phone', 'company')
