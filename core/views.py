from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import TemplateView, CreateView, UpdateView

from .forms import ClienteRegisterForm, EmpresaRegisterForm, ProfileUpdateForm


def mi_error_404(request, exception=None):
    return render(request, '404.html', status=404)


class HomeView(TemplateView):
    template_name = 'core/home.html'


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
