from django.contrib import admin
from .models import Bus, Asiento


class AsientoAdmin(admin.ModelAdmin):
    list_display = ['numero', 'bus', 'ocupado', 'usuario', 'fecha_reserva']


admin.site.register(Bus)
admin.site.register(Asiento, AsientoAdmin)