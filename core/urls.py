from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views

from . import views

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path("login/", auth_views.LoginView.as_view(), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("password_change/", auth_views.PasswordChangeView.as_view(template_name='core/password_change.html', success_url=reverse_lazy('profile')), name="password_change"),
    path("registro/", views.ClienteRegisterView.as_view(), name="register"),
    path("registro/empresa/", views.EmpresaRegisterView.as_view(), name="register_empresa"),
    path("perfil/", views.ProfileUpdateView.as_view(), name="profile"),
]
