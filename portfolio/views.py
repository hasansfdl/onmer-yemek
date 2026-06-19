"""Portfolio app views."""

from django.views.generic import DetailView, ListView

from .models import PortfolioItem


class PortfolioListView(ListView):
    """Masonry gallery of all published portfolio items."""

    model = PortfolioItem
    template_name = 'portfolio/list.html'
    context_object_name = 'items'

    def get_queryset(self):
        qs = PortfolioItem.objects.filter(is_published=True)
        category = self.request.GET.get('category')
        if category and category != 'all':
            qs = qs.filter(category=category)
        return qs.prefetch_related('images')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['categories'] = PortfolioItem.CATEGORY_CHOICES
        ctx['active_category'] = self.request.GET.get('category', 'all')
        return ctx


class PortfolioDetailView(DetailView):
    """Detail page for a single portfolio entry."""

    model = PortfolioItem
    template_name = 'portfolio/detail.html'
    context_object_name = 'item'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
