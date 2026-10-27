"""
Migracion de datos: a los animales que ya tenian publicacion les asignamos
como dueño al rescatista de esa publicacion.
"""

from django.db import migrations


def asignar_rescatista(apps, schema_editor):
    Publicaciones = apps.get_model('adopciones', 'Publicaciones')
    for publicacion in Publicaciones.objects.select_related('animal'):
        animal = publicacion.animal
        animal.rescatista_id = publicacion.rescatista_id
        animal.save(update_fields=['rescatista'])


class Migration(migrations.Migration):

    dependencies = [
        ('adopciones', '0010_rescatista_animales'),
    ]

    operations = [
        # Al deshacerla no hay nada que revertir: la columna la borra la 0010.
        migrations.RunPython(asignar_rescatista, migrations.RunPython.noop),
    ]
