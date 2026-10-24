"""
wsgi.py es el archivo que usa un servidor de verdad (Apache, Gunicorn) para
levantar el proyecto cuando se despliega. Mientras desarrollamos no lo tocamos.
"""

import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'adopciones.settings')

application = get_wsgi_application()
