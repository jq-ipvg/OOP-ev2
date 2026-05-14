from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, UpdateView

from .models import Bus, Asiento


class BusListView(LoginRequiredMixin, ListView):
    model = Bus
    template_name = 'boletos/bus_list.html'
    context_object_name = 'buses'


class SeatGridView(LoginRequiredMixin, DetailView):
    model = Bus
    template_name = 'boletos/seat_grid.html'
    context_object_name = 'bus'
    pk_url_kwarg = 'pk'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['asientos'] = self.object.asientos.all().order_by('numero')
        return context


class SeatReserveView(LoginRequiredMixin, UpdateView):
    model = Asiento
    fields = []
    template_name = 'boletos/confirm_reserve.html'
    pk_url_kwarg = 'pk'

    def get_queryset(self):
        return Asiento.objects.filter(ocupado=False)

    def form_valid(self, form):
        form.instance.ocupado = True
        form.instance.usuario = self.request.user
        import datetime
        form.instance.fecha_reserva = datetime.datetime.now()
        messages.success(self.request, f"Asiento {form.instance.numero} reservado correctamente.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('boletos:seat_grid', kwargs={'pk': self.object.bus.pk})
