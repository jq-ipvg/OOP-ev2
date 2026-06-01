from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('boletos', '0003_asiento_piso_bus_pisos'),
    ]

    operations = [
        migrations.AddField(
            model_name='bus',
            name='asientos_piso_1',
            field=models.IntegerField(default=20),
        ),
        migrations.AddField(
            model_name='bus',
            name='asientos_piso_2',
            field=models.IntegerField(default=0),
        ),
    ]
