"""Menu app views — dish catalogue on /menu/ and dish detail pages."""

from django.views.generic import DetailView, ListView

from .models import Dish, MenuCategory


class DishListView(ListView):
    """All dishes (active + inactive); inactive cards show a status pill on site."""

    model = Dish
    template_name = 'menu/menu_list.html'
    context_object_name = 'dishes'
    paginate_by = 12

    def get_queryset(self):
        qs = Dish.objects.select_related('category').order_by(
            '-is_active', 'order', 'name'
        )
        category_slug = self.request.GET.get('category')
        if category_slug and category_slug != 'all':
            qs = qs.filter(category__slug=category_slug)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['categories'] = MenuCategory.objects.filter(is_active=True)
        ctx['active_category'] = self.request.GET.get('category', 'all')
        return ctx


class DishDetailView(DetailView):
    """Standalone dish detail page."""

    model = Dish
    template_name = 'menu/dish_detail.html'
    context_object_name = 'dish'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['similar'] = Dish.objects.filter(
            category=self.object.category,
        ).exclude(pk=self.object.pk).order_by('-is_active', 'order', 'name')[:4]
        return ctx
