from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from boletos.models import Bus, Asiento, Profile


class Command(BaseCommand):
    help = 'Puebla la base de datos con datos de ejemplo para una demo rápida'

    def handle(self, *args, **options):
        self.stdout.write("Poblando base de datos...")

        # Crear perfiles para usuarios existentes
        for user in User.objects.all():
            Profile.objects.get_or_create(user=user)

        # Cliente de prueba
        if not User.objects.filter(username='cliente').exists():
            cliente = User.objects.create_user('cliente', email='cliente@mail.cl',
                                                first_name='María', last_name='González',
                                                password='cliente123')
            cliente.profile.tipo = 'cliente'
            cliente.profile.save()
            self.stdout.write("  + Usuario 'cliente' creado (pass: cliente123)")
        else:
            self.stdout.write("  ~ Usuario 'cliente' ya existe")

        # Empresa de prueba
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

        # Buses de la empresa
        if not Bus.objects.filter(empresa=empresa).exists():
            bus1 = Bus.objects.create(
                nombre='Buses Sur 01',
                placa='BS-1010',
                pisos=1,
                asientos_piso_1=40,
                asientos_piso_2=0,
                empresa=empresa,
            )
            self.stdout.write(f"  + Bus '{bus1.nombre}' creado ({bus1.capacidad} asientos)")

            bus2 = Bus.objects.create(
                nombre='Buses Sur 02',
                placa='BS-2020',
                pisos=2,
                asientos_piso_1=20,
                asientos_piso_2=20,
                empresa=empresa,
            )
            self.stdout.write(f"  + Bus '{bus2.nombre}' creado ({bus2.capacidad} asientos, 2 pisos)")

            bus3 = Bus.objects.create(
                nombre='Buses Sur 03',
                placa='BS-3030',
                pisos=1,
                asientos_piso_1=30,
                asientos_piso_2=0,
                empresa=empresa,
            )
            self.stdout.write(f"  + Bus '{bus3.nombre}' creado ({bus3.capacidad} asientos)")
        else:
            self.stdout.write("  ~ La empresa ya tiene buses")

        self.stdout.write(self.style.SUCCESS("¡Base de datos poblada!"))
