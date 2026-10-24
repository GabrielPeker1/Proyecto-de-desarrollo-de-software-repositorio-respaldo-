from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('adopciones', '0003_add_animal_profile_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='animales',
            name='compatible_ninos',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='animales',
            name='compatible_otros_animales',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='animales',
            name='desparasitado',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='animales',
            name='tiene_microchip',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='animales',
            name='entrenamiento_basico',
            field=models.BooleanField(default=False),
        ),
    ]
