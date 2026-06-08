import uuid
from datetime import date, datetime, timedelta
from django.db import models
from django.db.models import Q
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


class Terminal(models.Model):
    nombre = models.CharField(max_length=100)
    ciudad = models.CharField(max_length=100)

    class Meta:
        ordering = ['ciudad', 'nombre']

    def __str__(self):
        return f"{self.nombre}, {self.ciudad}"


class Ruta(models.Model):
    origen = models.ForeignKey(Terminal, on_delete=models.CASCADE, related_name='rutas_origen')
    destino = models.ForeignKey(Terminal, on_delete=models.CASCADE, related_name='rutas_destino')
    duracion_minutos = models.IntegerField()
    empresa = models.ForeignKey(User, on_delete=models.CASCADE, related_name='rutas')

    class Meta:
        unique_together = ['origen', 'destino', 'empresa']
        ordering = ['origen__ciudad', 'destino__ciudad']

    def __str__(self):
        return f"{self.origen} → {self.destino}"


class Itinerario(models.Model):
    TIPO_CHOICES = [
        ('diario', 'Diario'),
        ('unico', 'Único'),
    ]
    bus = models.ForeignKey(Bus, on_delete=models.CASCADE, related_name='itinerarios')
    ruta = models.ForeignKey(Ruta, on_delete=models.CASCADE, related_name='itinerarios')
    hora_salida = models.TimeField()
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES, default='diario')
    fecha_especifica = models.DateField(null=True, blank=True)
    activo = models.BooleanField(default=True)
    creado_por = models.ForeignKey(User, on_delete=models.CASCADE, null=True)

    class Meta:
        ordering = ['hora_salida']

    def hora_llegada(self):
        dt = datetime.combine(date.today(), self.hora_salida)
        dt += timedelta(minutes=self.ruta.duracion_minutos)
        return dt.time()

    def esta_disponible(self, fecha=None):
        if not self.activo:
            return False
        if fecha is None:
            fecha = date.today()

        if self.tipo == 'unico':
            if not self.fecha_especifica or self.fecha_especifica != fecha:
                return False

        ahora = datetime.now()
        if fecha == date.today():
            salida = datetime.combine(fecha, self.hora_salida)
            return salida > ahora
        return fecha > date.today()

    def asientos_disponibles(self):
        return self.asientos_disponibles_para(date.today())

    def asientos_disponibles_para(self, fecha):
        ocupados = self.bus.asientos.filter(
            Q(ocupado=True, itinerario__isnull=True) |
            Q(itinerario=self, fecha_viaje=fecha)
        ).count()
        return self.bus.capacidad - ocupados

    @property
    def ya_partio(self):
        ahora = datetime.now()
        if self.tipo == 'unico' and self.fecha_especifica:
            salida = datetime.combine(self.fecha_especifica, self.hora_salida)
            return salida + timedelta(minutes=self.ruta.duracion_minutos) < ahora
        if self.tipo == 'diario':
            salida = datetime.combine(date.today(), self.hora_salida)
            return salida + timedelta(minutes=self.ruta.duracion_minutos) < ahora
        return False

    def __str__(self):
        base = f"{self.bus.nombre} - {self.ruta} - {self.hora_salida}"
        if self.tipo == 'unico':
            base += f" ({self.fecha_especifica})"
        return base


class Asiento(models.Model):
    bus = models.ForeignKey(Bus, on_delete=models.CASCADE, related_name='asientos')
    numero = models.IntegerField()
    piso = models.IntegerField(default=1)
    ocupado = models.BooleanField(default=False)
    cancelado = models.BooleanField(default=False)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    fecha_reserva = models.DateTimeField(null=True, blank=True)
    fecha_viaje = models.DateField(null=True, blank=True)
    itinerario = models.ForeignKey(Itinerario, on_delete=models.SET_NULL, null=True, blank=True)

    @property
    def esta_completada(self):
        if not self.itinerario:
            return False
        viaje_date = self.fecha_viaje or date.today()
        salida = datetime.combine(viaje_date, self.itinerario.hora_salida)
        salida += timedelta(minutes=self.itinerario.ruta.duracion_minutos)
        return datetime.now() > salida

    def __str__(self):
        return f"Asiento {self.numero} - {self.bus.nombre}"


class Transaccion(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='transacciones')
    asientos = models.ManyToManyField(Asiento, related_name='transacciones')
    itinerario = models.ForeignKey(Itinerario, on_delete=models.SET_NULL, null=True, blank=True)
    monto_total = models.IntegerField(default=5000)
    cantidad = models.IntegerField(default=1)
    fecha_compra = models.DateTimeField(auto_now_add=True)
    ultimos_digitos = models.CharField(max_length=4, default='0000')

    class Meta:
        ordering = ['-fecha_compra']

    def __str__(self):
        return f"#{self.id}"
