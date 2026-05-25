from django.db import models
from django.conf import settings


class Bus(models.Model):
    nombre = models.CharField(max_length=100)
    placa = models.CharField(max_length=10)
    capacidad = models.IntegerField(default=20)

    def save(self, *args, **kwargs):
        nuevo_bus = not self.pk
        super().save(*args, **kwargs)
        if nuevo_bus:
            for i in range(1, self.capacidad + 1):
                Asiento.objects.create(bus=self, numero=i)

    def asientos_disponibles(self):
        return self.asientos.filter(ocupado=False).count()

    def asientos_ocupados(self):
        return self.asientos.filter(ocupado=True).count()

    def __str__(self):
        return f"{self.nombre} [{self.placa}]"


class Asiento(models.Model):
    bus = models.ForeignKey(Bus, on_delete=models.CASCADE, related_name='asientos')
    numero = models.IntegerField()
    ocupado = models.BooleanField(default=False)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    fecha_reserva = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Asiento {self.numero} - {self.bus.nombre}"
