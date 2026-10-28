"""
Migracion de datos: crea las cuentas de prueba para poder entrar apenas se
corre "python manage.py migrate", sin registrarse a mano:

    adoptante1@mail.com   / 123456   (Adoptante)
    rescatista1@mail.com  / 123456   (Rescatista)
    mod1@adoptme.com      / 123456   (Moderador)

Si alguna de esas cuentas ya existe la deja como esta
"""

from django.contrib.auth.hashers import make_password
from django.db import migrations 

PASSWORD = '123456'

# email, nombre, tipo de usuario
USUARIOS = [
    ('adoptante1@mail.com', 'Adoptante 1', 'Adoptante'),
    ('rescatista1@mail.com', 'Rescatista 1', 'Rescatista'),
    ('mod1@adoptme.com', 'Moderador 1', 'Moderador'),
]


def crear_usuarios(apps, schema_editor):
    TiposUsuario = apps.get_model('adopciones', 'TiposUsuario')
    Ubicaciones = apps.get_model('adopciones', 'Ubicaciones')
    Usuarios = apps.get_model('adopciones', 'Usuarios')

    for email, nombre, tipo_nombre in USUARIOS:
        if Usuarios.objects.filter(email__iexact=email).exists():
            continue

        # Los tipos los carga el fixture datos_iniciales.json, pero puede que
        # todavia no se haya cargado: si falta lo creamos.
        tipo = TiposUsuario.objects.filter(nombre__iexact=tipo_nombre).first()
        if tipo is None:
            tipo = TiposUsuario.objects.create(nombre=tipo_nombre)

        if tipo_nombre == 'Moderador':
            # Igual que en crear_moderador: el moderador no publica ni adopta,
            # le dejamos una ubicacion vacia que no se muestra en ningun lado.
            ubicacion = Ubicaciones.objects.create(
                provincia='-', ciudad='-', direccion_completa='-', zona_aproximada='-'
            )
        else:
            ubicacion = Ubicaciones.objects.create(
                provincia='Santa Fe', departamento='Rosario', ciudad='Rosario',
                calle='Cordoba', numero='1000',
                direccion_completa='Cordoba 1000', zona_aproximada='Rosario'
            )

        Usuarios.objects.create(
            email=email,
            nombre_completo=nombre,
            password_encriptada=make_password(PASSWORD),
            tipo_usuario=tipo,
            ubicacion=ubicacion,
        )


def borrar_usuarios(apps, schema_editor):
    Usuarios = apps.get_model('adopciones', 'Usuarios')
    for usuario in Usuarios.objects.filter(email__in=[u[0] for u in USUARIOS]):
        ubicacion = usuario.ubicacion
        usuario.delete()
        ubicacion.delete()


class Migration(migrations.Migration):

    dependencies = [
        ('adopciones', '0018_bloqueo_reportes_hasta'),
    ]

    operations = [
        migrations.RunPython(crear_usuarios, borrar_usuarios),
    ]
