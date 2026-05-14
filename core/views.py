from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.views.generic import TemplateView, CreateView
from django.urls import reverse_lazy


class HomeView(TemplateView):
    template_name = 'core/home.html'


class RegisterView(CreateView):
    form_class = UserCreationForm
    template_name = 'core/register.html'
    success_url = reverse_lazy('login')

    def form_valid(self, form):
        messages.success(self.request, "Cuenta creada correctamente. Ahora puedes iniciar sesión.")
        return super().form_valid(form)
