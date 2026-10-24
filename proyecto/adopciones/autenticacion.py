"""
Autenticacion de la API con token.

Cuando el usuario inicia sesion, LoginView le devuelve un token. El front lo
manda en cada pedido en el header:
    Authorization: Bearer <token>
y con eso sabemos quien esta haciendo el pedido (request.user).

El token es el id del usuario firmado con la SECRET_KEY de Django
(django.core.signing). Si alguien lo modifica, la firma deja de coincidir y se
rechaza, asi que no se puede falsificar. Vence a los 7 dias.
"""

from django.core import signing
from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework.exceptions import AuthenticationFailed

from .models import Usuarios

SALT = 'adopciones.token'
DURACION_SEGUNDOS = 7 * 24 * 60 * 60


def generar_token(usuario):
    return signing.dumps({'id_usuario': usuario.id_usuario}, salt=SALT)


class TokenAutenticacion(BaseAuthentication):
    """Le dice a Django REST Framework como reconocer al usuario del pedido."""

    def authenticate(self, request):
        header = get_authorization_header(request).split()
        if not header or header[0].lower() != b'bearer':
            # Sin token: el pedido sigue como anonimo. Cada vista decide si lo deja pasar.
            return None
        if len(header) != 2:
            raise AuthenticationFailed('Token mal formado')

        try:
            datos = signing.loads(header[1].decode(), salt=SALT, max_age=DURACION_SEGUNDOS)
        except signing.SignatureExpired:
            raise AuthenticationFailed('La sesión venció. Iniciá sesión de nuevo.')
        except signing.BadSignature:
            raise AuthenticationFailed('Token inválido')

        usuario = Usuarios.objects.select_related('tipo_usuario').filter(
            id_usuario=datos.get('id_usuario')
        ).first()
        if usuario is None:
            raise AuthenticationFailed('El usuario ya no existe')
        if usuario.estado == Usuarios.BAJA:
            raise AuthenticationFailed('El usuario está dado de baja')
        return (usuario, header[1].decode())

    def authenticate_header(self, request):
        # Hace que los pedidos sin token valido respondan 401 (no 403).
        return 'Bearer'
