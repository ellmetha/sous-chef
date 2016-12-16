# coding: utf-8

from django.contrib.auth.views import login
from django.http import HttpResponseRedirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.urlresolvers import reverse_lazy
from django.views.generic import TemplateView
from member.models import Client
from order.models import Order
from datetime import datetime


class HomeView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    permission_required = 'sous_chef.read'
    template_name = 'pages/home.html'

    def get_context_data(self, **kwargs):
        context = super(HomeView, self).get_context_data(**kwargs)

        today = datetime.today()
        active_clients = Client.active.all().count()
        pending_clients = Client.pending.all().count()
        clients = Client.contact.get_birthday_boys_and_girls()
        billable_orders = Order.objects.get_billable_orders(
            today.year, today.month
        ).count()
        billable_orders_year = Order.objects.filter(
            status='D',
            delivery_date__year=datetime.today().year).count()
        context['active_clients'] = active_clients
        context['pending_clients'] = pending_clients
        context['birthday'] = clients
        context['billable_orders_month'] = billable_orders,
        context['billable_orders_year'] = billable_orders_year

        return context


def custom_login(request):
    if request.user.is_authenticated():
        # Redirect to home if already logged in.
        return HttpResponseRedirect(reverse_lazy("page:home"))
    else:
        return login(request)
