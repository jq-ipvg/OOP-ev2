from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, UpdateView, DeleteView, TemplateView, CreateView, FormView

from .models import Bus, Asiento, Ruta, Itinerario, Transaccion
from django.db.models import Q
from .forms import BusForm, RutaForm, ItinerarioForm, PaymentForm


class BusListView(LoginRequiredMixin, TemplateView):
    template_name = 'boletos/bus_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from datetime import date
        hoy = date.today()
        salidas = []

        for bus in Bus.objects.all():
            itinerarios = Itinerario.objects.filter(
                bus=bus, activo=True
            ).select_related('ruta__origen', 'ruta__destino').order_by('hora_salida')

            disponibles = []
            for it in itinerarios:
                if len(disponibles) >= 3:
                    break
                if it.esta_disponible(hoy):
                    libres = it.asientos_disponibles_para(hoy)
                    disponibles.append((it, libres))

            if disponibles:
                salidas.append((bus, disponibles))

        context['salidas'] = salidas
        context['hoy'] = hoy
        return context


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
        itinerario_id = self.request.GET.get('itinerario')
        if itinerario_id:
            context['itinerario'] = get_object_or_404(Itinerario, pk=itinerario_id, bus=self.object)
        return context


class SeatReserveView(LoginRequiredMixin, FormView):
    form_class = PaymentForm
    template_name = 'boletos/confirm_reserve.html'

    def get_asiento(self):
        pk = self.kwargs['pk']
        qs = Asiento.objects.all()
        itinerario_id = self.request.GET.get('itinerario')
        fecha_str = self.request.GET.get('fecha')
        if itinerario_id:
            import datetime
            try:
                fecha = datetime.datetime.strptime(fecha_str, '%Y-%m-%d').date() if fecha_str else None
            except (ValueError, TypeError):
                fecha = None
            filters = Q(ocupado=False)
            filters |= Q(ocupado=True, itinerario__isnull=False) & ~Q(itinerario_id=int(itinerario_id))
            if fecha:
                filters |= Q(ocupado=True, itinerario_id=int(itinerario_id), fecha_viaje__isnull=False) & ~Q(fecha_viaje=fecha)
            qs = qs.filter(filters)
        else:
            qs = qs.filter(ocupado=False, itinerario__isnull=True)
        return get_object_or_404(qs, pk=pk)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['asiento'] = self.get_asiento()
        itinerario_id = self.request.GET.get('itinerario')
        if itinerario_id:
            context['itinerario_obj'] = get_object_or_404(Itinerario, pk=itinerario_id)
        context['fecha'] = self.request.GET.get('fecha', '')
        return context

    def get_initial(self):
        initial = super().get_initial()
        user = self.request.user
        initial['nombre_titular'] = user.get_full_name() or user.username
        return initial

    def form_valid(self, form):
        asiento = self.get_asiento()
        itinerario_id = self.request.GET.get('itinerario')
        itinerario = None
        if itinerario_id:
            try:
                itinerario = Itinerario.objects.get(pk=itinerario_id)
            except Itinerario.DoesNotExist:
                pass
        fecha_str = self.request.GET.get('fecha')
        import datetime
        asiento.ocupado = True
        asiento.usuario = self.request.user
        asiento.fecha_reserva = datetime.datetime.now()
        asiento.itinerario = itinerario
        if fecha_str:
            try:
                asiento.fecha_viaje = datetime.datetime.strptime(fecha_str, '%Y-%m-%d').date()
            except (ValueError, TypeError):
                pass
        asiento.save()
        transaccion = Transaccion.objects.create(
            usuario=self.request.user,
            itinerario=itinerario,
            monto_total=5000,
            cantidad=1,
            ultimos_digitos='0000',
        )
        transaccion.asientos.add(asiento)
        return redirect('boletos:reserva_confirmada', pk=transaccion.pk)

    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data(form=form))


class MisReservasView(LoginRequiredMixin, TemplateView):
    template_name = 'boletos/mis_reservas.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['reservas'] = Asiento.objects.filter(
            usuario=self.request.user
        ).exclude(ocupado=False, cancelado=False).select_related(
            'bus', 'itinerario__ruta__origen', 'itinerario__ruta__destino'
        ).order_by('-fecha_reserva')
        return context


class CancelReserveView(LoginRequiredMixin, UpdateView):
    model = Asiento
    fields = []
    template_name = 'boletos/cancel_confirm.html'
    pk_url_kwarg = 'pk'

    def get_queryset(self):
        return Asiento.objects.filter(usuario=self.request.user, ocupado=True)

    def form_valid(self, form):
        if form.instance.esta_completada:
            messages.error(self.request, "No puedes cancelar una reserva de un viaje ya completado.")
            return redirect(self.get_success_url())
        form.instance.cancelado = True
        form.instance.ocupado = False
        form.instance.fecha_viaje = None
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
        context['total_rutas'] = Ruta.objects.filter(empresa=user).count()
        context['total_itinerarios'] = Itinerario.objects.filter(bus__empresa=user).count()
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
        messages.success(self.request, "Bus eliminado.")
        return super().form_valid(form)


class CompanyRutaListView(LoginRequiredMixin, CompanyRequiredMixin, ListView):
    model = Ruta
    template_name = 'boletos/empresa/ruta_list.html'
    context_object_name = 'rutas'

    def get_queryset(self):
        return Ruta.objects.filter(empresa=self.request.user).select_related('origen', 'destino')


class CompanyRutaCreateView(LoginRequiredMixin, CompanyRequiredMixin, CreateView):
    model = Ruta
    form_class = RutaForm
    template_name = 'boletos/empresa/ruta_form.html'
    success_url = reverse_lazy('boletos:empresa_ruta_list')

    def form_valid(self, form):
        form.instance.empresa = self.request.user
        messages.success(self.request, "Ruta creada correctamente.")
        return super().form_valid(form)


class CompanyItinerarioListView(LoginRequiredMixin, CompanyRequiredMixin, ListView):
    model = Itinerario
    template_name = 'boletos/empresa/itinerario_list.html'
    context_object_name = 'itinerarios'

    def get_queryset(self):
        return Itinerario.objects.filter(bus__empresa=self.request.user).select_related('bus', 'ruta__origen', 'ruta__destino')


class CompanyItinerarioCreateView(LoginRequiredMixin, CompanyRequiredMixin, CreateView):
    model = Itinerario
    form_class = ItinerarioForm
    template_name = 'boletos/empresa/itinerario_form.html'
    success_url = reverse_lazy('boletos:empresa_itinerario_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.creado_por = self.request.user
        messages.success(self.request, "Itinerario creado correctamente.")
        return super().form_valid(form)


class ItinerarioSeatGridView(LoginRequiredMixin, DetailView):
    model = Itinerario
    template_name = 'boletos/seat_grid.html'
    context_object_name = 'itinerario'
    pk_url_kwarg = 'pk'

    def get_object(self):
        it = super().get_object()
        if not it.esta_disponible():
            messages.error(self.request, "Este itinerario no está disponible.")
        return it

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        bus = self.object.bus
        context['bus'] = bus
        fecha_str = self.request.GET.get('fecha', '')
        context['fecha'] = fecha_str
        from datetime import datetime
        fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date() if fecha_str else None
        asientos = bus.asientos.all().order_by('numero')
        context['asientos'] = asientos
        pisos = []
        for piso in range(1, bus.pisos + 1):
            pisos.append(asientos.filter(piso=piso))
        context['pisos_list'] = pisos
        context['itinerario_obj'] = self.object
        if fecha:
            context['disponibles_hoy'] = self.object.asientos_disponibles_para(fecha)
        context['occupied_seat_ids'] = set(
            a.numero for a in bus.asientos.all()
            if a.ocupado and (
                a.itinerario_id is None or
                (a.itinerario_id == self.object.pk and fecha and a.fecha_viaje == fecha)
            )
        )
        return context


class ReservaConfirmadaView(LoginRequiredMixin, DetailView):
    model = Transaccion
    template_name = 'boletos/confirmacion.html'
    context_object_name = 'transaccion'
    pk_url_kwarg = 'pk'

    def get_queryset(self):
        return Transaccion.objects.filter(usuario=self.request.user)


class MisComprasView(LoginRequiredMixin, ListView):
    model = Transaccion
    template_name = 'boletos/mis_compras.html'
    context_object_name = 'compras'

    def get_queryset(self):
        return Transaccion.objects.filter(usuario=self.request.user).prefetch_related(
            'asientos__bus', 'itinerario__ruta__origen', 'itinerario__ruta__destino'
        )


class PagarView(LoginRequiredMixin, FormView):
    form_class = PaymentForm
    template_name = 'boletos/pagar.html'

    def get_asientos(self):
        ids = self.request.GET.getlist('asientos')
        itinerario_id = self.request.GET.get('itinerario')
        fecha_str = self.request.GET.get('fecha')
        qs = Asiento.objects.all()
        if itinerario_id:
            from datetime import datetime
            try:
                fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date() if fecha_str else None
            except (ValueError, TypeError):
                fecha = None
            filters = Q(ocupado=False)
            filters |= Q(ocupado=True, itinerario__isnull=False) & ~Q(itinerario_id=int(itinerario_id))
            if fecha:
                filters |= Q(ocupado=True, itinerario_id=int(itinerario_id), fecha_viaje__isnull=False) & ~Q(fecha_viaje=fecha)
            qs = qs.filter(filters)
        else:
            qs = qs.filter(ocupado=False, itinerario__isnull=True)
        return qs.filter(pk__in=ids)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        asientos = self.get_asientos()
        context['asientos'] = asientos
        context['total'] = len(asientos) * 5000
        context['cantidad'] = len(asientos)
        itinerario_id = self.request.GET.get('itinerario')
        if itinerario_id:
            context['itinerario_obj'] = get_object_or_404(Itinerario, pk=itinerario_id)
        context['fecha'] = self.request.GET.get('fecha', '')
        return context

    def get_initial(self):
        initial = super().get_initial()
        initial['nombre_titular'] = self.request.user.get_full_name() or self.request.user.username
        return initial

    def form_valid(self, form):
        asientos = self.get_asientos()
        import datetime
        itinerario_id = self.request.GET.get('itinerario')
        itinerario = None
        if itinerario_id:
            try:
                itinerario = Itinerario.objects.get(pk=itinerario_id)
            except Itinerario.DoesNotExist:
                pass
        fecha_str = self.request.GET.get('fecha')
        ahora = datetime.datetime.now()
        for asiento in asientos:
            asiento.ocupado = True
            asiento.usuario = self.request.user
            asiento.fecha_reserva = ahora
            asiento.itinerario = itinerario
            if fecha_str:
                try:
                    asiento.fecha_viaje = datetime.datetime.strptime(fecha_str, '%Y-%m-%d').date()
                except (ValueError, TypeError):
                    pass
            asiento.save()
        transaccion = Transaccion.objects.create(
            usuario=self.request.user,
            itinerario=itinerario,
            monto_total=len(asientos) * 5000,
            cantidad=len(asientos),
            ultimos_digitos='0000',
        )
        transaccion.asientos.add(*asientos)
        return redirect('boletos:reserva_confirmada', pk=transaccion.pk)

    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data(form=form))
