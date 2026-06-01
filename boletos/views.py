from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, UpdateView, DeleteView, TemplateView, CreateView

from .models import Bus, Asiento
from .forms import BusForm


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
        asientos = self.object.asientos.all().order_by('numero')
        context['asientos'] = asientos
        pisos = []
        for piso in range(1, self.object.pisos + 1):
            pisos.append(asientos.filter(piso=piso))
        context['pisos_list'] = pisos
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


class MisReservasView(LoginRequiredMixin, TemplateView):
    template_name = 'boletos/mis_reservas.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['reservas'] = Asiento.objects.filter(
            usuario=self.request.user, ocupado=True
        ).select_related('bus').order_by('-fecha_reserva')
        return context


class CancelReserveView(LoginRequiredMixin, UpdateView):
    model = Asiento
    fields = []
    template_name = 'boletos/cancel_confirm.html'
    pk_url_kwarg = 'pk'

    def get_queryset(self):
        return Asiento.objects.filter(usuario=self.request.user, ocupado=True)

    def form_valid(self, form):
        form.instance.ocupado = False
        form.instance.usuario = None
        form.instance.fecha_reserva = None
        messages.success(self.request, f"Reserva del asiento {form.instance.numero} cancelada.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('boletos:mis_reservas')


class CompanyRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return hasattr(self.request.user, 'profile') and self.request.user.profile.tipo == 'empresa'


class CompanyDashboardView(LoginRequiredMixin, CompanyRequiredMixin, TemplateView):
    template_name = 'boletos/empresa/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context['total_buses'] = Bus.objects.filter(empresa=user).count()
        context['total_reservas'] = Asiento.objects.filter(
            bus__empresa=user, ocupado=True
        ).count()
        context['buses'] = Bus.objects.filter(empresa=user)
        return context


class CompanyBusListView(LoginRequiredMixin, CompanyRequiredMixin, ListView):
    model = Bus
    template_name = 'boletos/empresa/bus_list.html'
    context_object_name = 'buses'

    def get_queryset(self):
        return Bus.objects.filter(empresa=self.request.user)


class CompanyBusCreateView(LoginRequiredMixin, CompanyRequiredMixin, CreateView):
    model = Bus
    form_class = BusForm
    template_name = 'boletos/empresa/bus_form.html'
    success_url = reverse_lazy('boletos:empresa_bus_list')

    def form_valid(self, form):
        form.instance.empresa = self.request.user
        messages.success(self.request, f"Bus {form.instance.nombre} creado correctamente.")
        return super().form_valid(form)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if self.object:
            kwargs['instance'] = self.object
        return kwargs


class CompanyBusDetailView(LoginRequiredMixin, CompanyRequiredMixin, DetailView):
    model = Bus
    template_name = 'boletos/empresa/bus_detail.html'
    context_object_name = 'bus'
    pk_url_kwarg = 'pk'

    def get_queryset(self):
        return Bus.objects.filter(empresa=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['reservas'] = self.object.asientos.filter(ocupado=True).select_related('usuario').order_by('-fecha_reserva')
        context['asientos_disponibles'] = self.object.asientos_disponibles()
        return context


class CompanyBusUpdateView(LoginRequiredMixin, CompanyRequiredMixin, UpdateView):
    model = Bus
    fields = ['nombre', 'placa']
    template_name = 'boletos/empresa/bus_form.html'
    pk_url_kwarg = 'pk'
    success_url = reverse_lazy('boletos:empresa_bus_list')

    def get_queryset(self):
        return Bus.objects.filter(empresa=self.request.user)

    def form_valid(self, form):
        messages.success(self.request, f"Bus {form.instance.nombre} actualizado.")
        return super().form_valid(form)


class CompanyBusDeleteView(LoginRequiredMixin, CompanyRequiredMixin, DeleteView):
    model = Bus
    template_name = 'boletos/empresa/bus_confirm_delete.html'
    pk_url_kwarg = 'pk'
    success_url = reverse_lazy('boletos:empresa_bus_list')

    def get_queryset(self):
        return Bus.objects.filter(empresa=self.request.user)

    def form_valid(self, form):
        messages.success(self.request, f"Bus eliminado.")
        return super().form_valid(form)
