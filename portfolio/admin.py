"""Admin customisations for the portfolio app."""

from django.contrib import admin
from django.utils.html import format_html

from .models import PortfolioImage, PortfolioItem


class PortfolioImageInline(admin.TabularInline):
    model = PortfolioImage
    extra = 1
    fields = ('image', 'caption', 'order')


@admin.register(PortfolioItem)
class PortfolioItemAdmin(admin.ModelAdmin):
    list_display = ('thumb', 'title', 'category', 'event_date',
                    'is_published', 'order')
    list_display_links = ('title',)
    list_editable = ('is_published', 'order')
    list_filter = ('category', 'is_published')
    search_fields = ('title', 'description', 'location')
    prepopulated_fields = {'slug': ('title',)}
    inlines = [PortfolioImageInline]

    @admin.display(description='Önizleme')
    def thumb(self, obj):
        if obj and obj.cover:
            return format_html(
                '<img src="{}" style="width:60px;height:60px;'
                'object-fit:cover;border-radius:8px;border:2px solid '
                '#d4af37;" />', obj.cover.url)
        return '—'
