"""
urls.py es el indice de la API.
Aca decimos que direccion ejecuta que vista.

Regla que usamos en todas:
  /api/recurso/         -> GET (lista) y POST (crear)
  /api/recurso/<id>/    -> GET (uno), PATCH (modificar) y DELETE (borrar)
"""

from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path

from .views import (
    TiposUsuarioView,
    UbicacionesView,
    DepartamentosView,
    LocalidadesView,
    UsuariosView,
    LoginView,
    CambiarPasswordView,
    DarDeBajaUsuarioView,
    PerfilPublicoView,
    AnimalesView,
    FotosAnimalView,
    SubirFotosAnimalView,
    PublicacionesView,
    DepartamentosPublicacionesView,
    LocalidadesPublicacionesView,
    SolicitudesAdopcionView,
    AceptarSolicitudView,
    RechazarSolicitudView,
    ChatsView,
    MensajesView,
    ReportesView,
    GestionarReporteView,
    BloqueosView,
)

urlpatterns = [
    # Panel de administracion de Django
    path('admin/', admin.site.urls),

    # Tipos de usuario (Adoptante / Rescatista / Moderador)
    path('api/tipos-usuario/', TiposUsuarioView.as_view()),
    path('api/tipos-usuario/<int:id>/', TiposUsuarioView.as_view()),

    # Ubicaciones
    path('api/ubicaciones/', UbicacionesView.as_view()),
    path('api/ubicaciones/<int:id>/', UbicacionesView.as_view()),
    path('api/departamentos/', DepartamentosView.as_view()),
    path('api/localidades/', LocalidadesView.as_view()),

    # Usuarios + login + baja por parte del moderador
    path('api/usuarios/', UsuariosView.as_view()),
    path('api/usuarios/<int:id>/', UsuariosView.as_view()),
    path('api/usuarios/<int:id>/baja/', DarDeBajaUsuarioView.as_view()),
    path('api/usuarios/<int:id>/perfil-publico/', PerfilPublicoView.as_view()),
    path('api/usuarios/<int:id>/cambiar-password/', CambiarPasswordView.as_view()),
    path('api/login/', LoginView.as_view()),

    # Animales y sus fotos
    path('api/animales/', AnimalesView.as_view()),
    path('api/animales/<int:id>/', AnimalesView.as_view()),
    path('api/animales/<int:id>/fotos/', SubirFotosAnimalView.as_view()),
    path('api/fotos-animal/', FotosAnimalView.as_view()),
    path('api/fotos-animal/<int:id>/', FotosAnimalView.as_view()),

    # Publicaciones (el catalogo con filtros)
    path('api/publicaciones/', PublicacionesView.as_view()),
    path('api/publicaciones/departamentos/', DepartamentosPublicacionesView.as_view()),
    path('api/publicaciones/localidades/', LocalidadesPublicacionesView.as_view()),
    path('api/publicaciones/<int:id>/', PublicacionesView.as_view()),

    # Solicitudes de adopcion
    path('api/solicitudes/', SolicitudesAdopcionView.as_view()),
    path('api/solicitudes/<int:id>/', SolicitudesAdopcionView.as_view()),
    path('api/solicitudes/<int:id>/aceptar/', AceptarSolicitudView.as_view()),
    path('api/solicitudes/<int:id>/rechazar/', RechazarSolicitudView.as_view()),

    # Chats y mensajes
    path('api/chats/', ChatsView.as_view()),
    path('api/chats/<int:id>/', ChatsView.as_view()),
    path('api/mensajes/', MensajesView.as_view()),
    path('api/mensajes/<int:id>/', MensajesView.as_view()),

    # Reportes. La ultima recibe la acción (revisar/aceptar/rechazar) en la URL.
    path('api/reportes/', ReportesView.as_view()),
    path('api/reportes/<int:id>/', ReportesView.as_view()),
    path('api/reportes/<int:id>/<str:accion>/', GestionarReporteView.as_view()),

    # Bloqueos
    path('api/bloqueos/', BloqueosView.as_view()),
    path('api/bloqueos/<int:id>/', BloqueosView.as_view()),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
