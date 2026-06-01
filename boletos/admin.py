from django.contrib import admin
from .models import Bus, Asiento, Profile


class AsientoAdmin(admin.ModelAdmin):
    list_display = ['numero', 'bus', 'ocupado', 'usuario', 'fecha_reserva']


class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'tipo', 'empresa_nombre']


admin.site.register(Bus)
admin.site.register(Asiento, AsientoAdmin)
admin.site.register(Profile, ProfileAdmin)