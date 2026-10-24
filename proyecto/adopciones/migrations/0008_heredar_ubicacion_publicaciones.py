"""
Migracion de datos: a las publicaciones que ya existian les copiamos la
ubicacion actual de su rescatista (las nuevas la heredan al crearse).
"""

from django.db import migrations


def heredar_ubicacion(apps, schema_editor):
    Publicaciones = apps.get_model('adopciones', 'Publicaciones')
    for publicacion in Publicaciones.objects.select_related('rescatista__ubicacion'):
        ubicacion = publicacion.rescatista.ubicacion
        publicacion.provincia = ubicacion.provincia
        publicacion.departamento = ubicacion.departamento
        publicacion.localidad = ubicacion.ciudad
        publicacion.save(update_fields=['provincia', 'departamento', 'localidad'])


class Migration(migrations.Migration):

    dependencies = [
        ('adopciones', '0007_ubicacion_publicaciones'),
    ]

    operations = [
        # Al deshacerla no hay nada que revertir: las columnas las borra la 0007.
        migrations.RunPython(heredar_ubicacion, migrations.RunPython.noop),
    ]
