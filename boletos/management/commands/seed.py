from datetime import time, date, timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from boletos.models import Bus, Asiento, Profile, Terminal, Ruta, Itinerario, Transaccion


class Command(BaseCommand):
    help = 'Puebla la base de datos con datos de ejemplo para una demo rápida'

    def handle(self, *args, **options):
        self.stdout.write("Poblando base de datos...")

        for user in User.objects.all():
            Profile.objects.get_or_create(user=user)

        if not User.objects.filter(username='cliente').exists():
            cliente = User.objects.create_user('cliente', email='cliente@mail.cl',
                                                first_name='María', last_name='González',
                                                password='cliente123')
            cliente.profile.tipo = 'cliente'
            cliente.profile.save()
            self.stdout.write("  + Usuario 'cliente' creado (pass: cliente123)")
        else:
            cliente = User.objects.get(username='cliente')
            self.stdout.write("  ~ Usuario 'cliente' ya existe")

        if not User.objects.filter(username='empresa').exists():
            empresa = User.objects.create_user('empresa', email='empresa@buses.cl',
                                                first_name='Carlos', last_name='Muñoz',
                                                password='empresa123')
            empresa.profile.tipo = 'empresa'
            empresa.profile.empresa_nombre = 'BusSur Ltda.'
            empresa.profile.save()
            self.stdout.write("  + Usuario 'empresa' creado (pass: empresa123)")
        else:
            empresa = User.objects.get(username='empresa')
            self.stdout.write("  ~ Usuario 'empresa' ya existe")

        # Limpiar datos huerfanos
        Asiento.objects.filter(usuario=cliente, ocupado=True).update(
            ocupado=False, usuario=None, fecha_reserva=None, itinerario=None, fecha_viaje=None)
        Transaccion.objects.filter(usuario=cliente).delete()
        Itinerario.objects.all().delete()
        Bus.objects.all().delete()
        Ruta.objects.filter(empresa=empresa).delete()

        # Terminales
        Terminal.objects.get_or_create(nombre='Terminal San Borja', ciudad='Santiago')
        Terminal.objects.get_or_create(nombre='Terminal Valparaíso', ciudad='Valparaíso')
        Terminal.objects.get_or_create(nombre='Terminal Viña del Mar', ciudad='Viña del Mar')
        Terminal.objects.get_or_create(nombre='Terminal Collao', ciudad='Concepción')
        self.stdout.write("  + Terminales listas")

        t = {t.ciudad: t for t in Terminal.objects.all()}

        # Rutas
        ruta1 = Ruta.objects.create(origen=t['Santiago'], destino=t['Valparaíso'], duracion_minutos=120, empresa=empresa)
        ruta2 = Ruta.objects.create(origen=t['Santiago'], destino=t['Viña del Mar'], duracion_minutos=110, empresa=empresa)
        ruta3 = Ruta.objects.create(origen=t['Valparaíso'], destino=t['Santiago'], duracion_minutos=120, empresa=empresa)
        ruta4 = Ruta.objects.create(origen=t['Viña del Mar'], destino=t['Santiago'], duracion_minutos=110, empresa=empresa)
        rutas = [ruta1, ruta2, ruta3, ruta4]
        self.stdout.write("  + Rutas creadas")

        # Buses
        bus1 = Bus.objects.create(nombre='Buses Sur 01', placa='BS-1010', pisos=1, asientos_piso_1=40, asientos_piso_2=0, empresa=empresa)
        bus2 = Bus.objects.create(nombre='Buses Sur 02', placa='BS-2020', pisos=2, asientos_piso_1=20, asientos_piso_2=20, empresa=empresa)
        bus3 = Bus.objects.create(nombre='Buses Sur 03', placa='BS-3030', pisos=1, asientos_piso_1=30, asientos_piso_2=0, empresa=empresa)
        buses = [bus1, bus2, bus3]
        self.stdout.write("  + Buses creados")

        # Itinerarios diarios (incluye 21:00 para que siempre haya salidas disponibles)
        Itinerario.objects.create(bus=buses[0], ruta=rutas[0], hora_salida=time(8, 0), tipo='diario', creado_por=empresa)
        Itinerario.objects.create(bus=buses[0], ruta=rutas[0], hora_salida=time(14, 0), tipo='diario', creado_por=empresa)
        Itinerario.objects.create(bus=buses[0], ruta=rutas[0], hora_salida=time(21, 0), tipo='diario', creado_por=empresa)
        Itinerario.objects.create(bus=buses[1], ruta=rutas[1], hora_salida=time(9, 30), tipo='diario', creado_por=empresa)
        Itinerario.objects.create(bus=buses[1], ruta=rutas[2], hora_salida=time(11, 0), tipo='diario', creado_por=empresa)
        Itinerario.objects.create(bus=buses[2], ruta=rutas[3], hora_salida=time(16, 0), tipo='diario', creado_por=empresa)
        # Itinerario unico futuro
        Itinerario.objects.create(bus=buses[0], ruta=rutas[0], hora_salida=time(6, 0), tipo='unico',
                                   fecha_especifica=date.today() + timedelta(days=3), creado_por=empresa)
        self.stdout.write("  + Itinerarios creados")

        # Reserva activa (hoy)
        from django.utils import timezone
        it_activo = Itinerario.objects.filter(bus=bus1, tipo='diario').first()
        asiento_activo = bus1.asientos.filter(ocupado=False).first()
        if asiento_activo and it_activo:
            asiento_activo.ocupado = True
            asiento_activo.usuario = cliente
            asiento_activo.itinerario = it_activo
            asiento_activo.fecha_viaje = date.today()
            asiento_activo.fecha_reserva = timezone.now()
            asiento_activo.save()
            self.stdout.write(f"  + Reserva activa (Asiento {asiento_activo.numero})")

            t_activa = Transaccion.objects.create(
                usuario=cliente, itinerario=it_activo, monto_total=5000, cantidad=1, ultimos_digitos='0000')
            t_activa.asientos.add(asiento_activo)

        # Itinerario pasado para reserva completada
        it_pasado = Itinerario.objects.create(
            bus=bus1, ruta=rutas[0], hora_salida=time(10, 0),
            tipo='unico', fecha_especifica=date.today() - timedelta(days=1),
            creado_por=empresa)
        asiento_completado = bus1.asientos.filter(ocupado=False).first()
        if asiento_completado:
            asiento_completado.ocupado = True
            asiento_completado.usuario = cliente
            asiento_completado.itinerario = it_pasado
            asiento_completado.fecha_viaje = date.today() - timedelta(days=1)
            asiento_completado.fecha_reserva = timezone.now() - timedelta(days=2)
            asiento_completado.save()
            self.stdout.write(f"  + Reserva completada (Asiento {asiento_completado.numero})")

            t_completada = Transaccion.objects.create(
                usuario=cliente, itinerario=it_pasado, monto_total=5000, cantidad=1, ultimos_digitos='0000')
            t_completada.asientos.add(asiento_completado)

        self.stdout.write("  + Transacciones creadas")
        self.stdout.write(self.style.SUCCESS("¡Base de datos poblada!"))
