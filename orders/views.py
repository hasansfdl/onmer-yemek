"""Public order request views."""

import logging
import uuid

from django.conf import settings
from django.contrib import messages
from django.db import transaction
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from django.views.generic import CreateView, FormView, TemplateView

from menu.models import Dish

from .forms import OrderForm, OrderPaymentForm
from .mail import notify_brand_new_order, notify_brand_order_paid
from .models import Order, OrderItem

logger = logging.getLogger(__name__)


class OrderCreateView(CreateView):
    """Form page where visitors submit a bulk-order request."""

    model = Order
    form_class = OrderForm
    template_name = 'orders/order_form.html'

    def get_success_url(self):
        return reverse('orders:payment')

    # ---------- Context ----------

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        dishes = list(
            Dish.objects.filter(is_active=True)
            .select_related('category')
            .order_by('-is_featured', 'order', 'name')
        )

        is_post = self.request.method == 'POST'
        for d in dishes:
            qty = 0
            if is_post:
                raw = self.request.POST.get(f'qty_{d.id}', '0') or '0'
                try:
                    qty = max(0, int(raw))
                except (TypeError, ValueError):
                    qty = 0
            d.prev_qty = qty

        ctx['dishes'] = dishes
        return ctx

    # ---------- Persistence ----------

    @transaction.atomic
    def form_valid(self, form):
        response = super().form_valid(form)
        order = self.object

        items_to_create = [
            OrderItem(
                order=order,
                dish=dish,
                quantity=qty,
                unit_price=price,
            )
            for dish, (qty, price) in form.cleaned_dish_quantities.items()
        ]
        OrderItem.objects.bulk_create(items_to_create)
        order.recalculate_estimated_price()

        try:
            notify_brand_new_order(self.request, order)
        except Exception:
            logger.exception(
                'Order new-notification mail failed for order #%s',
                order.pk,
            )

        self.request.session['pending_payment_order_id'] = order.pk
        messages.success(
            self.request,
            'Siparişiniz oluşturuldu. Son adımda güvenli ödeme ekranında '
            'kart bilgilerinizi girin.',
        )
        return response

    def form_invalid(self, form):
        messages.error(
            self.request,
            'Lütfen formdaki hataları düzeltin.',
        )
        return super().form_invalid(form)


class OrderPaymentView(FormView):
    """Simulated bank card checkout after the order payload is saved."""

    template_name = 'orders/payment.html'
    form_class = OrderPaymentForm

    def dispatch(self, request, *args, **kwargs):
        oid = request.session.get('pending_payment_order_id')
        if not oid:
            messages.warning(
                request,
                'Ödeme oturumu bulunamadı. Lütfen sipariş formunu doldurun.',
            )
            return redirect('orders:create')

        order = (
            Order.objects.filter(pk=oid)
            .prefetch_related('items__dish')
            .first()
        )
        if not order:
            request.session.pop('pending_payment_order_id', None)
            messages.error(request, 'Sipariş kaydına ulaşılamadı.')
            return redirect('orders:create')

        if order.payment_status == 'paid':
            request.session.pop('pending_payment_order_id', None)
            request.session['last_order_id'] = order.pk
            messages.info(
                request,
                'Bu sipariş için ödeme zaten tamamlanmış.',
            )
            return redirect('orders:success')

        self.order = order
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['order'] = self.order
        ctx['order_items'] = list(self.order.items.all())
        ctx['order_total'] = self.order.items_total
        return ctx

    def form_valid(self, form):
        # SQLite: keep the write transaction tiny. SMTP inside atomic() held the
        # DB locked and caused "database is locked" on Windows during payment.
        with transaction.atomic():
            order = Order.objects.select_for_update().get(pk=self.order.pk)

            if order.payment_status == 'paid':
                self.request.session.pop('pending_payment_order_id', None)
                self.request.session['last_order_id'] = order.pk
                messages.info(
                    self.request,
                    'Bu sipariş için ödeme zaten tamamlanmış.',
                )
                return redirect('orders:success')

            order.payment_status = 'paid'
            order.payment_transaction_ref = f'ONMER-{uuid.uuid4().hex[:12].upper()}'
            order.payment_completed_at = timezone.now()
            order.save(update_fields=[
                'payment_status',
                'payment_transaction_ref',
                'payment_completed_at',
                'updated_at',
            ])

        mail_sent_ok = False
        try:
            notify_brand_order_paid(self.request, order)
            mail_sent_ok = True
        except Exception:
            logger.exception(
                'Order paid-notification mail failed for order #%s',
                order.pk,
            )
            messages.warning(
                self.request,
                'Sipariş kaydedildi fakat bilgilendirme e-postası gönderilemedi. '
                'SMTP ayarlarını kontrol edin veya sunucu günlüklerine bakın.',
            )

        if (
            mail_sent_ok
            and 'console' in (settings.EMAIL_BACKEND or '').lower()
        ):
            messages.info(
                self.request,
                'Not: E-posta şu an geliştirme modunda — mesaj gelen kutunuza '
                'gitmez, yalnızca uçbirime (runserver penceresine) yazdırılır. '
                'Gelen kutuya almak için sunucuyu başlatmadan önce EMAIL_HOST_USER '
                've EMAIL_HOST_PASSWORD ortam değişkenlerini ayarlayın (README).',
            )

        self.request.session.pop('pending_payment_order_id', None)
        self.request.session['last_order_id'] = order.pk
        messages.success(
            self.request,
            'Ödemeniz başarıyla alındı. Sipariş özetinizi aşağıda görebilirsiniz.',
        )
        return redirect('orders:success')

    def form_invalid(self, form):
        messages.error(
            self.request,
            'Lütfen kart bilgilerini kontrol edin.',
        )
        return super().form_invalid(form)


class OrderSuccessView(TemplateView):
    template_name = 'orders/order_success.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        order_id = self.request.session.pop('last_order_id', None)
        if order_id:
            order = (
                Order.objects.prefetch_related('items__dish')
                .filter(pk=order_id)
                .first()
            )
            ctx['order'] = order
            if order:
                ctx['order_items'] = list(order.items.all())
                ctx['order_total'] = order.items_total
        return ctx
