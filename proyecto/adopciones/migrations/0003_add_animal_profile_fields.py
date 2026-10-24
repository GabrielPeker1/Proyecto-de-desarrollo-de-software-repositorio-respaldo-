from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('adopciones', '0002_alter_publicaciones_animal'),
    ]

    operations = [
        migrations.AddField(
            model_name='animales',
            name='especie',
            field=models.CharField(default='Perro', max_length=50),
        ),
        migrations.AddField(
            model_name='animales',
            name='raza',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='animales',
            name='sexo',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.AddField(
            model_name='animales',
            name='peso',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=6, null=True),
        ),
    ]
