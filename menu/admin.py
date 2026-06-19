"""Admin customisations for the menu domain."""

from django.contrib import admin
from django.utils.html import format_html

from .models import Dish, MenuCategory


@admin.register(MenuCategory)
class MenuCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'kind', 'icon', 'order', 'is_active')
    list_editable = ('order', 'is_active')
    list_filter = ('kind', 'is_active')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Dish)
class DishAdmin(admin.ModelAdmin):
    list_display = ('thumb', 'name', 'category', 'price', 'calories',
                    'is_featured', 'is_active', 'order')
    list_display_links = ('name',)
    list_editable = ('price', 'is_featured', 'is_active', 'order')
    list_filter = ('category', 'is_featured', 'is_active')
    search_fields = ('name', 'description', 'ingredients')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('thumb', 'created_at')
    fieldsets = (
        ('Genel', {
            'fields': ('category', 'name', 'slug', 'description',
                       'ingredients'),
        }),
        ('Detaylar', {
            'fields': ('calories', 'serving_size', 'price', 'image', 'thumb'),
        }),
        ('Durum', {
            'fields': ('is_featured', 'is_active', 'order', 'created_at'),
        }),
    )

    @admin.display(description='Önizleme')
    def thumb(self, obj):
        if obj and obj.image:
            return format_html(
                '<img src="{}" style="width:60px;height:60px;'
                'object-fit:cover;border-radius:8px;border:2px solid '
                '#d4af37;" />', obj.image.url)
        return '—'
