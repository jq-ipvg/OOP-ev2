from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import TemplateView, CreateView, UpdateView

from .forms import ClienteRegisterForm, EmpresaRegisterForm, ProfileUpdateForm
from boletos.models import Terminal, Itinerario


def mi_error_404(request, exception=None):
    return render(request, '404.html', status=404)


class HomeView(TemplateView):
    template_name = 'core/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['terminales'] = Terminal.objects.all()
        context['itinerarios_resultados'] = []
        return context

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        origen_id = request.POST.get('origen')
        destino_id = request.POST.get('destino')
        fecha_str = request.POST.get('fecha')

        from datetime import date, datetime
        try:
            fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date() if fecha_str else date.today()
        except (ValueError, TypeError):
            fecha = date.today()

        context['origen_id'] = int(origen_id) if origen_id else None
        context['destino_id'] = int(destino_id) if destino_id else None
        context['fecha'] = fecha

        if origen_id and destino_id and fecha:
            resultados = Itinerario.objects.filter(
                ruta__origen_id=origen_id,
                ruta__destino_id=destino_id,
                activo=True,
            ).select_related('bus', 'ruta__origen', 'ruta__destino')

            disponibles = []
            for it in resultados:
                if it.esta_disponible(fecha):
                    libres = it.asientos_disponibles_para(fecha)
                    if libres > 0:
                        disponibles.append((it, libres))
            context['itinerarios_resultados'] = disponibles

        return self.render_to_response(context)


class ClienteRegisterView(CreateView):
    form_class = ClienteRegisterForm
    template_name = 'core/register.html'
    success_url = reverse_lazy('login')

    def form_valid(self, form):
        messages.success(self.request, "Cuenta creada correctamente. Ahora puedes iniciar sesión.")
        return super().form_valid(form)


class EmpresaRegisterView(CreateView):
    form_class = EmpresaRegisterForm
    template_name = 'core/register_empresa.html'
    success_url = reverse_lazy('login')

    def form_valid(self, form):
        messages.success(self.request, "Cuenta empresarial creada correctamente. Ahora puedes iniciar sesión.")
        return super().form_valid(form)


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    form_class = ProfileUpdateForm
    template_name = 'core/profile.html'
    success_url = reverse_lazy('profile')

    def get_object(self):
        return self.request.user

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['profile'] = self.request.user.profile
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, "Datos actualizados correctamente.")
        return super().form_valid(form)
