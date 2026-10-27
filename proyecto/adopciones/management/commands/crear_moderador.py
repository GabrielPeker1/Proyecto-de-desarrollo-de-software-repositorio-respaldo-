"""
Crea una cuenta de moderador desde la consola:

    python manage.py crear_moderador --email mod@adoptme.com --nombre "Moderador 1"

La contraseña se pide por teclado (no se ve al escribirla) y se guarda con el
mismo hash que usa el registro. Asi no queda escrita en ningun archivo, ni en el
historial de la consola, ni en texto plano en la base.
Desde el registro de la app no se pueden crear moderadores (ver UsuariosView.post).
"""

from getpass import getpass

from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from adopciones.models import TiposUsuario, Ubicaciones, Usuarios

LARGO_MINIMO = 8


class Command(BaseCommand):
    help = 'Crea una cuenta de moderador (la contraseña se pide por teclado).'

    def add_arguments(self, parser):
        parser.add_argument('--email', required=True)
        parser.add_argument('--nombre', required=True, help='Nombre que se muestra en el panel')

    def handle(self, *args, **options):
        email = options['email'].strip().lower()
        nombre = options['nombre'].strip()
        if Usuarios.objects.filter(email__iexact=email).exists():
            raise CommandError('Ya existe un usuario con el email ' + email)

        password = getpass('Contraseña: ')
        if len(password) < LARGO_MINIMO:
            raise CommandError('La contraseña tiene que tener al menos ' + str(LARGO_MINIMO) + ' caracteres')
        if getpass('Repetí la contraseña: ') != password:
            raise CommandError('Las contraseñas no coinciden')

        with transaction.atomic():
            tipo = TiposUsuario.objects.filter(nombre__iexact='Moderador').first()
            if tipo is None:
                tipo = TiposUsuario.objects.create(nombre='Moderador')
            # usuarios.id_ubicacion es obligatorio, pero el moderador no publica ni
            # adopta: le dejamos una ubicacion vacia que no se muestra en ningun lado.
            ubicacion = Ubicaciones.objects.create(
                provincia='-', ciudad='-', direccion_completa='-', zona_aproximada='-'
            )
            Usuarios.objects.create(
                email=email,
                nombre_completo=nombre,
                password_encriptada=make_password(password),
                tipo_usuario=tipo,
                ubicacion=ubicacion,
            )

        self.stdout.write(self.style.SUCCESS(
            'Moderador creado. Entrá por /moderacion con ' + email
        ))
