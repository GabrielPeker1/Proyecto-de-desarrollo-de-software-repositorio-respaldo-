#!/usr/bin/env python
"""Este archivo es el "control remoto" de Django.
Todo lo que corramos por consola (runserver, migrate, createsuperuser, etc.)
pasa por aca. Lo genera solo Django cuando hacemos startproject, no hay que tocarlo.
"""
import os
import sys


def main():
    # Le avisamos a Django donde esta el archivo de configuracion del proyecto
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'adopciones.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "No se encontró Django. ¿Activaste el entorno virtual y corriste "
            "'pip install -r requirements.txt'?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
