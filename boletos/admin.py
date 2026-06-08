from django.contrib import admin
from .models import Bus, Asiento, Profile, Terminal, Ruta, Itinerario, Transaccion


class AsientoAdmin(admin.ModelAdmin):
    list_display = ['numero', 'bus', 'ocupado', 'usuario', 'fecha_reserva', 'itinerario']


class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'tipo', 'empresa_nombre']


class ItinerarioAdmin(admin.ModelAdmin):
    list_display = ['bus', 'ruta', 'hora_salida', 'tipo', 'fecha_especifica', 'activo']


class TransaccionAdmin(admin.ModelAdmin):
    list_display = ['id', 'usuario', 'fecha_compra', 'monto_total', 'cantidad']


admin.site.register(Bus)
admin.site.register(Asiento, AsientoAdmin)
admin.site.register(Profile, ProfileAdmin)
admin.site.register(Terminal)
admin.site.register(Ruta)
admin.site.register(Itinerario, ItinerarioAdmin)
admin.site.register(Transaccion, TransaccionAdmin)