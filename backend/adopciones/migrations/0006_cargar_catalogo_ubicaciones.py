"""
Migracion de datos: carga las provincias, departamentos y localidades de
Argentina desde data/georef_argentina.json (datos oficiales de la API Georef).
Se ejecuta sola con "python manage.py migrate", no hace falta internet.
"""

import json
from pathlib import Path

from django.db import migrations

ARCHIVO = Path(__file__).resolve().parent.parent / 'data' / 'georef_argentina.json'


def cargar_catalogo(apps, schema_editor):
    Provincias = apps.get_model('adopciones', 'Provincias')
    Departamentos = apps.get_model('adopciones', 'Departamentos')
    Localidades = apps.get_model('adopciones', 'Localidades')

    with open(ARCHIVO, encoding='utf-8') as archivo:
        datos = json.load(archivo)

    # bulk_create inserta todo de a muchos registros juntos, mucho mas rapido
    # que hacer un .create() por cada una de las ~4000 localidades.
    Provincias.objects.bulk_create(
        [Provincias(id_provincia=id, nombre=nombre) for id, nombre in datos['provincias']]
    )
    Departamentos.objects.bulk_create(
        [Departamentos(id_departamento=id, provincia_id=provincia_id, nombre=nombre)
         for id, provincia_id, nombre in datos['departamentos']]
    )
    Localidades.objects.bulk_create(
        [Localidades(id_localidad=id, departamento_id=departamento_id, nombre=nombre)
         for id, departamento_id, nombre in datos['localidades']],
        batch_size=1000
    )


def borrar_catalogo(apps, schema_editor):
    # Si se deshace la migracion, vaciamos las tablas (las localidades y
    # departamentos se borran en cascada).
    apps.get_model('adopciones', 'Provincias').objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('adopciones', '0005_catalogo_ubicaciones'),
    ]

    operations = [
        migrations.RunPython(cargar_catalogo, borrar_catalogo),
    ]
