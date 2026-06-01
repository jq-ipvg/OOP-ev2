from django.conf import settings
from django.contrib import admin
from django.urls import path, include, re_path

from core import views

urlpatterns = [
    path('', include('core.urls')),
    path('admin/', admin.site.urls),
    path('buses/', include('boletos.urls')),
]

handler404 = 'core.views.mi_error_404'

if settings.DEBUG:
    urlpatterns += [
        re_path(r'^.*$', views.mi_error_404),
    ]
