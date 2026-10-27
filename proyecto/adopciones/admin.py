"""
registramos las clases para poder verlas y cargarlas a mano desde
http://localhost:8000/admin/.
"""

from django.contrib import admin
from .models import (
    TiposUsuario,
    Ubicaciones,
    Usuarios,
    Animales,
    FotosAnimal,
    Publicaciones,
    SolicitudesAdopcion,
    Chats,
    Mensajes,
    Reportes,
    Alertas,
    Bloqueos,
)

# Con esto cada tabla aparece en el panel de administracion de Django.
admin.site.register(TiposUsuario)
admin.site.register(Ubicaciones)
admin.site.register(Usuarios)
admin.site.register(Animales)
admin.site.register(FotosAnimal)
admin.site.register(Publicaciones)
admin.site.register(SolicitudesAdopcion)
admin.site.register(Chats)
admin.site.register(Mensajes)
admin.site.register(Reportes)
admin.site.register(Alertas)
admin.site.register(Bloqueos)

# Titulos del panel para que quede prolijo
admin.site.site_header = 'Administración - Sistema de Adopciones'
admin.site.site_title = 'Adopciones DDS 2026 - Grupo 15'
admin.site.index_title = 'Gestión de datos'
