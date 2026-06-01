from django.db import migrations


def migrar_capacidad(apps, schema_editor):
    Bus = apps.get_model('boletos', 'Bus')
    for bus in Bus.objects.all():
        old_cap = getattr(bus, 'capacidad', 20)
        if bus.pisos == 1:
            bus.asientos_piso_1 = old_cap
            bus.asientos_piso_2 = 0
        else:
            mitad = old_cap // 2
            bus.asientos_piso_1 = mitad
            bus.asientos_piso_2 = old_cap - mitad
        bus.save(update_fields=['asientos_piso_1', 'asientos_piso_2'])


class Migration(migrations.Migration):

    dependencies = [
        ('boletos', '0004_remove_bus_capacidad_bus_asientos_piso_1_and_more'),
    ]

    operations = [
        migrations.RunPython(migrar_capacidad),
    ]
