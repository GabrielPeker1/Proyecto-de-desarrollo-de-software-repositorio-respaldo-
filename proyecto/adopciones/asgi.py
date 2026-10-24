"""
asgi serviria si mas adelante quisieramos usar WebSockets para el chat en vivo.
"""

import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'adopciones.settings')

application = get_asgi_application()
