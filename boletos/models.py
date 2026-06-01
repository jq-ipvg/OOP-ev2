from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class Profile(models.Model):
    TIPO_CHOICES = [
        ('cliente', 'Cliente'),
        ('empresa', 'Empresa'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES, default='cliente')
    empresa_nombre = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"{self.user.username} ({self.tipo})"


@receiver(post_save, sender=User)
def crear_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


class Bus(models.Model):
    PISOS_CHOICES = [
        (1, '1 Piso'),
        (2, '2 Pisos'),
    ]
    nombre = models.CharField(max_length=100)
    placa = models.CharField(max_length=10)
    pisos = models.IntegerField(choices=PISOS_CHOICES, default=1)
    asientos_piso_1 = models.IntegerField(default=20)
    asientos_piso_2 = models.IntegerField(default=0)
    empresa = models.ForeignKey(User, on_delete=models.CASCADE, related_name='buses', null=True, blank=True)

    @property
    def capacidad(self):
        return self.asientos_piso_1 + self.asientos_piso_2

    def save(self, *args, **kwargs):
        nuevo_bus = not self.pk
        super().save(*args, **kwargs)
        if nuevo_bus:
            for i in range(1, self.asientos_piso_1 + 1):
                Asiento.objects.create(bus=self, numero=i, piso=1)
            for i in range(1, self.asientos_piso_2 + 1):
                Asiento.objects.create(bus=self, numero=self.asientos_piso_1 + i, piso=2)

    def asientos_disponibles(self):
        return self.asientos.filter(ocupado=False).count()

    def asientos_ocupados(self):
        return self.asientos.filter(ocupado=True).count()

    def __str__(self):
        return f"{self.nombre} [{self.placa}]"


class Asiento(models.Model):
    bus = models.ForeignKey(Bus, on_delete=models.CASCADE, related_name='asientos')
    numero = models.IntegerField()
    piso = models.IntegerField(default=1)
    ocupado = models.BooleanField(default=False)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    fecha_reserva = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Asiento {self.numero} - {self.bus.nombre}"
