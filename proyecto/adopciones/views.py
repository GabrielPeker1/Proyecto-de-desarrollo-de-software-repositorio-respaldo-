"""
views.py, aca definimos quue hace la API cuando le pega un GET, POST, PATCH o DELETE.
Una clase por recurso que hereda de APIView,
con un metodo por cada verbo HTTP, y siempre devolvemos
Response({"status": "success", "data": ...}).
"""

from datetime import timedelta
from pathlib import Path
from uuid import uuid4

from django.conf import settings
from django.core.files.storage import default_storage
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from django.shortcuts import get_object_or_404
from django.contrib.auth.hashers import check_password, make_password
from django.db.models import Q
from django.db import transaction
from django.utils import timezone

from .models import (
    TiposUsuario,
    Departamentos,
    Localidades,
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
from .serializers import (
    TiposUsuarioSerializer,
    UbicacionesSerializer,
    UsuariosSerializer,
    UsuarioPublicoSerializer,
    PerfilPublicoSerializer,
    LoginSerializer,
    AnimalesSerializer,
    FotosAnimalSerializer,
    PublicacionesSerializer,
    SolicitudesAdopcionSerializer,
    ChatsSerializer,
    MensajesSerializer,
    ReportesSerializer,
    AlertasSerializer,
    BloqueosSerializer,
    CambiarPasswordSerializer,
)
from .autenticacion import generar_token, mensaje_suspension


# ===========================================================================
# Ayudas para chequear quien hace el pedido.
# request.user es el usuario del token (ver autenticacion.py) o un anonimo.
# ===========================================================================
def es_moderador(usuario):
    return usuario.is_authenticated and usuario.tipo_usuario.nombre.lower() == 'moderador'


def sin_login():
    return Response({'status': 'error', 'data': 'Iniciá sesión para continuar'},
                    status=status.HTTP_401_UNAUTHORIZED)


def sin_permiso():
    return Response({'status': 'error', 'data': 'No tenés permiso para hacer esto'},
                    status=status.HTTP_403_FORBIDDEN)


def puede_gestionar_usuario(request, id_usuario):
    """Devuelve None si el que pide es ese mismo usuario o un moderador.
    Si no, devuelve la respuesta de error para cortar la vista."""
    if not request.user.is_authenticated:
        return sin_login()
    if request.user.id_usuario != int(id_usuario) and not es_moderador(request.user):
        return sin_permiso()
    return None


def rol(usuario):
    return usuario.tipo_usuario.nombre.lower() if usuario.is_authenticated else ''


def datos_con(request, **campos):
    """Copia del body del pedido pisando algunos campos.
    La usamos para que los ids de "quien hace esto" (rescatista_id, adoptante_id,
    emisor_id...) salgan siempre del token y no de lo que mande el front."""
    datos = request.data.copy()
    for campo, valor in campos.items():
        datos[campo] = valor
    return datos


def dueno_animal(animal):
    """El rescatista dueño del animal (o None si es un animal viejo sin dueño)."""
    if animal.rescatista_id:
        return animal.rescatista_id
    publicacion = Publicaciones.objects.filter(animal=animal).first()
    return publicacion.rescatista_id if publicacion else None


def puede_editar_animal(request, animal):
    """None si el que pide es el rescatista dueño del animal; si no, el error."""
    if not request.user.is_authenticated:
        return sin_login()
    if dueno_animal(animal) != request.user.id_usuario:
        return Response({'status': 'error', 'data': 'Solo el rescatista dueño puede modificar este animal'},
                        status=status.HTTP_403_FORBIDDEN)
    return None


def participantes_chat(chat):
    return (chat.solicitud.adoptante_id, chat.solicitud.publicacion.rescatista_id)


def hay_bloqueo(id_a, id_b):
    """True si alguno de los dos bloqueo al otro (bloqueo activo)."""
    return Bloqueos.objects.filter(
        Q(usuario_bloqueador_id=id_a, usuario_bloqueado_id=id_b) |
        Q(usuario_bloqueador_id=id_b, usuario_bloqueado_id=id_a),
        estado=Bloqueos.ACTIVO
    ).exists()


# ===========================================================================
# /api/tipos-usuario/
# ===========================================================================
class TiposUsuarioView(APIView):

    def get(self, request, *args, **kwargs):
        id = kwargs.get('id', None)
        if id:
            # get_object_or_404 devuelve un 404 prolijo si el id no existe,
            # en vez de romper todo con un error 500.
            resultado = get_object_or_404(TiposUsuario, id_tipo_usuario=id)
            serializer = TiposUsuarioSerializer(resultado)
            return Response({'status': 'success', 'data': serializer.data}, status=200)

        resultado = TiposUsuario.objects.all()
        # many=True porque le estamos pasando una lista de objetos y no uno solo
        serializer = TiposUsuarioSerializer(resultado, many=True)
        return Response({'status': 'success', 'data': serializer.data}, status=200)

    # Ver los tipos es libre (el registro los necesita); crearlos o borrarlos, solo un moderador.
    def post(self, request):
        if not es_moderador(request.user):
            return sin_login() if not request.user.is_authenticated else sin_permiso()
        serializer = TiposUsuarioSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'status': 'success', 'data': serializer.data},
                            status=status.HTTP_201_CREATED)
        return Response({'status': 'error', 'data': serializer.errors},
                        status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, id=None):
        if not es_moderador(request.user):
            return sin_login() if not request.user.is_authenticated else sin_permiso()
        resultado = get_object_or_404(TiposUsuario, id_tipo_usuario=id)
        resultado.delete()
        return Response({'status': 'success', 'data': 'Tipo de usuario eliminado'})


# ===========================================================================
# /api/departamentos/ y /api/localidades/
# Catalogo oficial para los desplegables del registro y del perfil.
# Se busca por nombre porque en ubicaciones guardamos los nombres.
# ===========================================================================
class DepartamentosView(APIView):
    """/api/departamentos/?provincia=Santa Fe"""

    def get(self, request):
        provincia = request.query_params.get('provincia', '').strip()
        if not provincia:
            return Response({'status': 'error', 'data': 'Indicá la provincia'},
                            status=status.HTTP_400_BAD_REQUEST)
        nombres = Departamentos.objects.filter(
            provincia__nombre__iexact=provincia
        ).order_by('nombre').values_list('nombre', flat=True)
        return Response({'status': 'success', 'data': list(nombres)}, status=200)


class LocalidadesView(APIView):
    """/api/localidades/?provincia=Santa Fe&departamento=Rosario"""

    def get(self, request):
        provincia = request.query_params.get('provincia', '').strip()
        departamento = request.query_params.get('departamento', '').strip()
        if not provincia or not departamento:
            return Response({'status': 'error', 'data': 'Indicá la provincia y el departamento'},
                            status=status.HTTP_400_BAD_REQUEST)
        # Hay departamentos que se llaman igual en distintas provincias
        # (ej: "San Martín"), por eso filtramos por los dos.
        nombres = Localidades.objects.filter(
            departamento__nombre__iexact=departamento,
            departamento__provincia__nombre__iexact=provincia
        ).order_by('nombre').values_list('nombre', flat=True)
        return Response({'status': 'success', 'data': list(nombres)}, status=200)


# ===========================================================================
# /api/ubicaciones/
# ===========================================================================
class UbicacionesView(APIView):
    """Tiene la direccion completa, que es privada: solo la ve y la cambia su dueño
    (o un moderador). Crearla es libre porque el registro la crea antes que el usuario.
    """

    def puede_gestionar(self, request, ubicacion, permitir_huerfana=False):
        duenos = list(ubicacion.usuarios.values_list('id_usuario', flat=True))
        # Una ubicacion sin usuario queda cuando el registro falla a mitad de camino;
        # el front la borra sin estar logueado.
        if permitir_huerfana and not duenos:
            return None
        if not request.user.is_authenticated:
            return sin_login()
        if request.user.id_usuario not in duenos and not es_moderador(request.user):
            return sin_permiso()
        return None

    def get(self, request, *args, **kwargs):
        id = kwargs.get('id', None)
        if id:
            resultado = get_object_or_404(Ubicaciones, id_ubicacion=id)
            error = self.puede_gestionar(request, resultado)
            if error:
                return error
            serializer = UbicacionesSerializer(resultado)
            return Response({'status': 'success', 'data': serializer.data}, status=200)

        # La lista tiene las direcciones de todos: solo moderadores.
        if not es_moderador(request.user):
            return sin_login() if not request.user.is_authenticated else sin_permiso()
        resultado = Ubicaciones.objects.all()
        serializer = UbicacionesSerializer(resultado, many=True)
        return Response({'status': 'success', 'data': serializer.data}, status=200)

    def post(self, request):
        serializer = UbicacionesSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'status': 'success', 'data': serializer.data},
                            status=status.HTTP_201_CREATED)
        return Response({'status': 'error', 'data': serializer.errors},
                        status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, id):
        resultado = get_object_or_404(Ubicaciones, id_ubicacion=id)
        error = self.puede_gestionar(request, resultado)
        if error:
            return error
        # partial=True = "puede venir solo una parte de los campos"
        serializer = UbicacionesSerializer(resultado, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'status': 'success', 'data': serializer.data})
        return Response({'status': 'error', 'data': serializer.errors},
                        status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, id=None):
        resultado = get_object_or_404(Ubicaciones, id_ubicacion=id)
        error = self.puede_gestionar(request, resultado, permitir_huerfana=True)
        if error:
            return error
        resultado.delete()
        return Response({'status': 'success', 'data': 'Ubicación eliminada'})


# ===========================================================================
# /api/usuarios/     
# ===========================================================================
class UsuariosView(APIView):
    """Datos completos de los usuarios (email, telefono, direccion).
    Solo los ve el propio usuario o un moderador. Para ver a otro usuario
    esta /api/usuarios/<id>/perfil-publico/.
    """

    def get(self, request, *args, **kwargs):
        id = kwargs.get('id', None)
        if id:
            error = puede_gestionar_usuario(request, id)
            if error:
                return error
            resultado = get_object_or_404(Usuarios, id_usuario=id)
            serializer = UsuariosSerializer(resultado)
            return Response({'status': 'success', 'data': serializer.data}, status=200)

        # La lista completa de usuarios es solo para moderadores.
        if not request.user.is_authenticated:
            return sin_login()
        if not es_moderador(request.user):
            return sin_permiso()

        resultado = Usuarios.objects.all()

        # request.query_params son los filtros que vienen en la URL después del "?"
        # Ejemplo: /api/usuarios/?tipo=Rescatista&estado=ACTIVO
        tipo = request.query_params.get('tipo', None)
        estado = request.query_params.get('estado', None)

        if tipo:
            # El doble guion bajo "__" sirve para meterse dentro de la tabla relacionada.
            # tipo_usuario__nombre = la columna nombre de la tabla tipos_usuario.
            # iexact = compara sin importar mayusculas/minusculas.
            resultado = resultado.filter(tipo_usuario__nombre__iexact=tipo)
        if estado:
            resultado = resultado.filter(estado__iexact=estado)
        # /api/usuarios/?sancionados=true -> los que tienen una sancion vigente
        # (suspension, baja o strikes). Lo usa el panel de moderacion.
        if request.query_params.get('sancionados') == 'true':
            resultado = resultado.filter(
                Q(suspendido_hasta__gt=timezone.now()) |
                Q(estado=Usuarios.BAJA) |
                Q(strikes_reporte__gt=0)
            )

        serializer = UsuariosSerializer(resultado, many=True)
        return Response({'status': 'success', 'data': serializer.data}, status=200)

    def post(self, request):
        # Registro de un usuario nuevo. El serializer se encarga de encriptar la password.
        # Desde el registro solo se pueden crear adoptantes y rescatistas: si no,
        # cualquiera podria crearse una cuenta de moderador.
        tipo = TiposUsuario.objects.filter(id_tipo_usuario=request.data.get('tipo_usuario_id')).first()
        if tipo and tipo.nombre.lower() not in ('adoptante', 'rescatista') and not es_moderador(request.user):
            return Response({'status': 'error', 'data': 'Solo podés crear cuentas de adoptante o rescatista'},
                            status=status.HTTP_403_FORBIDDEN)
        # Que la ubicacion no sea de otro usuario (si no, se le podria "robar" la direccion).
        ubicacion_id = request.data.get('ubicacion_id')
        if ubicacion_id and Usuarios.objects.filter(ubicacion_id=ubicacion_id).exists():
            return Response({'status': 'error', 'data': 'Esa ubicación ya pertenece a otro usuario'},
                            status=status.HTTP_400_BAD_REQUEST)
        serializer = UsuariosSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'status': 'success', 'data': serializer.data},
                            status=status.HTTP_201_CREATED)
        return Response({'status': 'error', 'data': serializer.errors},
                        status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, id):
        # Los datos de un usuario los edita solo el mismo usuario.
        if not request.user.is_authenticated:
            return sin_login()
        if request.user.id_usuario != int(id):
            return sin_permiso()
        resultado = get_object_or_404(Usuarios, id_usuario=id)
        serializer = UsuariosSerializer(resultado, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'status': 'success', 'data': serializer.data})
        return Response({'status': 'error', 'data': serializer.errors},
                        status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, id=None):
        error = puede_gestionar_usuario(request, id)
        if error:
            return error
        resultado = get_object_or_404(Usuarios, id_usuario=id)
        resultado.delete()
        return Response({'status': 'success', 'data': 'Usuario eliminado'})


class LoginView(APIView):
    """POST /api/login/  -> chequea email + contraseña.
    Devuelve los datos del usuario y un token que el front tiene que mandar
    en los siguientes pedidos (ver autenticacion.py).
    """

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({'status': 'error', 'data': serializer.errors},
                            status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data['email']
        password = serializer.validated_data['password']

        # .filter().first() devuelve el usuario o None si no existe.
        # Usamos esto en vez de .get() porque .get() tira excepción si no encuentra nada.
        usuario = Usuarios.objects.filter(email=email).first()

        # check_password compara la contraseña escrita contra el hash guardado.
        # No desencripta nada: vuelve a hashear lo que escribió el usuario y compara.
        if usuario is None or not check_password(password, usuario.password_encriptada):
            return Response({'status': 'error', 'data': 'Email o contraseña incorrectos'},
                            status=status.HTTP_401_UNAUTHORIZED)

        if usuario.estado == Usuarios.BAJA:
            return Response({'status': 'error', 'data': 'El usuario está dado de baja'},
                            status=status.HTTP_403_FORBIDDEN)
        if usuario.esta_suspendido():
            return Response({'status': 'error', 'data': mensaje_suspension(usuario)},
                            status=status.HTTP_403_FORBIDDEN)

        return Response({'status': 'success', 'data': UsuariosSerializer(usuario).data,
                         'token': generar_token(usuario)},
                        status=200)


class CambiarPasswordView(APIView):
    def post(self, request, id):
        # La contraseña la cambia solo el mismo usuario.
        if not request.user.is_authenticated:
            return sin_login()
        if request.user.id_usuario != int(id):
            return sin_permiso()
        usuario = get_object_or_404(Usuarios, id_usuario=id)
        serializer = CambiarPasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({'status': 'error', 'data': serializer.errors},
                            status=status.HTTP_400_BAD_REQUEST)

        password_actual = serializer.validated_data['password_actual']
        password_nueva = serializer.validated_data['password_nueva']
        if not check_password(password_actual, usuario.password_encriptada):
            return Response({'status': 'error', 'data': 'La contraseña actual es incorrecta'},
                            status=status.HTTP_400_BAD_REQUEST)

        usuario.password_encriptada = make_password(password_nueva)
        usuario.save(update_fields=['password_encriptada'])
        return Response({'status': 'success', 'data': 'Contraseña actualizada'})


class PerfilPublicoView(APIView):
    """GET /api/usuarios/<id>/perfil-publico/
    El perfil que ve otro usuario: solo nombre, ubicacion y (si es rescatista)
    descripcion. Sin email, telefono ni direccion.
    """

    def get(self, request, id):
        if not request.user.is_authenticated:
            return sin_login()
        usuario = get_object_or_404(
            Usuarios.objects.select_related('ubicacion', 'tipo_usuario'), id_usuario=id
        )
        return Response({'status': 'success', 'data': PerfilPublicoSerializer(usuario).data}, status=200)


class DarDeBajaUsuarioView(APIView):
    """POST /api/usuarios/<id>/baja/   
    Es el metodo darDeBajaUsuario(usuario) del Moderador en el diagrama de dominio.
    No borramos el registro: le cambiamos el estado a BAJA para no perder el historial.
    El moderador se identifica por su token (antes venia en el body y cualquiera
    podia poner el id de un moderador).
    """

    def post(self, request, id):
        # Chequeo de rol: solo un moderador puede dar de baja
        if not request.user.is_authenticated:
            return sin_login()
        if not es_moderador(request.user):
            return Response({'status': 'error', 'data': 'Solo un moderador puede dar de baja usuarios'},
                            status=status.HTTP_403_FORBIDDEN)

        usuario = get_object_or_404(Usuarios, id_usuario=id)
        usuario.estado = Usuarios.BAJA
        usuario.save()
        return Response({'status': 'success', 'data': UsuariosSerializer(usuario).data})


# ===========================================================================
# /api/animales/
# ===========================================================================
class AnimalesView(APIView):

    def get(self, request, *args, **kwargs):
        id = kwargs.get('id', None)
        if id:
            resultado = get_object_or_404(Animales, id_animal=id)
            serializer = AnimalesSerializer(resultado)
            return Response({'status': 'success', 'data': serializer.data}, status=200)


        resultado = Animales.objects.all()
        serializer = AnimalesSerializer(resultado, many=True)
        return Response({'status': 'success', 'data': serializer.data}, status=200)

    def post(self, request):
        # Los animales los cargan los rescatistas, y quedan a su nombre.
        if not request.user.is_authenticated:
            return sin_login()
        if rol(request.user) != 'rescatista':
            return Response({'status': 'error', 'data': 'Solo un rescatista puede cargar animales'},
                            status=status.HTTP_403_FORBIDDEN)
        serializer = AnimalesSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(rescatista=request.user)
            return Response({'status': 'success', 'data': serializer.data},
                            status=status.HTTP_201_CREATED)
        return Response({'status': 'error', 'data': serializer.errors},
                        status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, id):
        resultado = get_object_or_404(Animales, id_animal=id)
        error = puede_editar_animal(request, resultado)
        if error:
            return error
        serializer = AnimalesSerializer(resultado, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'status': 'success', 'data': serializer.data})
        return Response({'status': 'error', 'data': serializer.errors},
                        status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, id=None):
        resultado = get_object_or_404(Animales, id_animal=id)
        if not es_moderador(request.user):
            error = puede_editar_animal(request, resultado)
            if error:
                return error
        fotos = list(resultado.fotos.all())
        resultado.delete()
        media_prefix = settings.MEDIA_URL.lstrip('/')
        for foto in fotos:
            path = foto.url_foto.lstrip('/')
            if path.startswith(media_prefix):
                storage_name = path[len(media_prefix):]
                if storage_name.startswith('fotos_animales/') and '..' not in Path(storage_name).parts:
                    default_storage.delete(storage_name)
        return Response({'status': 'success', 'data': 'Animal eliminado'})


class SubirFotosAnimalView(APIView):
    parser_classes = (MultiPartParser, FormParser)
    max_fotos = 5
    max_tamano = 5 * 1024 * 1024
    # El formato se detecta por los primeros bytes del archivo y no por su nombre:
    # muchas imagenes descargadas se llaman .png pero en realidad son JPG o WEBP.
    formatos = {
        '.jpg': lambda header: header.startswith(b'\xff\xd8\xff'),
        '.png': lambda header: header.startswith(b'\x89PNG\r\n\x1a\n'),
        '.gif': lambda header: header.startswith((b'GIF87a', b'GIF89a')),
        '.webp': lambda header: header.startswith(b'RIFF') and header[8:12] == b'WEBP',
    }

    def detectar_extension(self, imagen):
        encabezado = imagen.read(12)
        imagen.seek(0)
        for extension, coincide in self.formatos.items():
            if coincide(encabezado):
                return extension
        return None

    def post(self, request, id):
        animal = get_object_or_404(Animales, id_animal=id)
        error = puede_editar_animal(request, animal)
        if error:
            return error
        imagenes = request.FILES.getlist('imagenes')
        if not imagenes:
            return Response({'status': 'error', 'data': 'Seleccioná al menos una imagen'},
                            status=status.HTTP_400_BAD_REQUEST)
        if len(imagenes) > self.max_fotos:
            return Response({'status': 'error', 'data': 'Podés subir hasta 5 imágenes por animal'},
                            status=status.HTTP_400_BAD_REQUEST)
        if animal.fotos.count() + len(imagenes) > self.max_fotos:
            return Response({'status': 'error', 'data': 'El animal puede tener hasta 5 imágenes en total'},
                            status=status.HTTP_400_BAD_REQUEST)

        extensiones = []
        for imagen in imagenes:
            if imagen.size > self.max_tamano:
                return Response({'status': 'error', 'data': 'Cada imagen debe pesar como máximo 5 MB'},
                                status=status.HTTP_400_BAD_REQUEST)
            extension = self.detectar_extension(imagen)
            if not extension:
                return Response({'status': 'error', 'data': 'Usá imágenes JPG, PNG, GIF o WEBP'},
                                status=status.HTTP_400_BAD_REQUEST)
            extensiones.append(extension)

        archivos_guardados = []
        fotos_creadas = []
        try:
            with transaction.atomic():
                for imagen, extension in zip(imagenes, extensiones):
                    nombre = default_storage.save(f'fotos_animales/{uuid4().hex}{extension}', imagen)
                    archivos_guardados.append(nombre)
                    foto = FotosAnimal.objects.create(
                        animal=animal,
                        url_foto=default_storage.url(nombre)
                    )
                    fotos_creadas.append(foto)
        except Exception:
            for nombre in archivos_guardados:
                default_storage.delete(nombre)
            raise

        serializer = FotosAnimalSerializer(fotos_creadas, many=True)
        return Response({'status': 'success', 'data': serializer.data},
                        status=status.HTTP_201_CREATED)


class FotosAnimalView(APIView):
    """Para agregar o borrar fotos sueltas de un animal."""

    def get(self, request, *args, **kwargs):
        resultado = FotosAnimal.objects.all()
        # Filtro opcional: /api/fotos-animal/?id_animal=1
        id_animal = request.query_params.get('id_animal', None)
        if id_animal:
            resultado = resultado.filter(animal_id=id_animal)
        serializer = FotosAnimalSerializer(resultado, many=True)
        return Response({'status': 'success', 'data': serializer.data}, status=200)

    def post(self, request):
        animal = get_object_or_404(Animales, id_animal=request.data.get('animal_id') or 0)
        error = puede_editar_animal(request, animal)
        if error:
            return error
        serializer = FotosAnimalSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'status': 'success', 'data': serializer.data},
                            status=status.HTTP_201_CREATED)
        return Response({'status': 'error', 'data': serializer.errors},
                        status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, id=None):
        resultado = get_object_or_404(FotosAnimal, id_foto=id)
        if not es_moderador(request.user):
            error = puede_editar_animal(request, resultado.animal)
            if error:
                return error
        resultado.delete()
        return Response({'status': 'success', 'data': 'Foto eliminada'})


# ===========================================================================
# /api/publicaciones/   
# ===========================================================================
def nombres_distintos(valores):
    """Saca vacios y repetidos (sin importar mayusculas) y ordena alfabeticamente.
    Hace falta porque las publicaciones viejas tienen la ciudad escrita a mano."""
    nombres = {}
    for valor in valores:
        nombre = (valor or '').strip()
        if nombre and nombre.lower() not in nombres:
            nombres[nombre.lower()] = nombre
    return sorted(nombres.values(), key=str.lower)


class DepartamentosPublicacionesView(APIView):
    """
    Departamentos de una provincia donde hay mascotas en adopcion, para el
    desplegable del filtro del catalogo:
    /api/publicaciones/departamentos/?provincia=Santa Fe
    """

    def get(self, request):
        provincia = request.query_params.get('provincia', '').strip()
        if not provincia:
            return Response({'status': 'error', 'data': 'Indicá la provincia'},
                            status=status.HTTP_400_BAD_REQUEST)
        valores = Publicaciones.objects.filter(
            estado=Publicaciones.EN_ADOPCION,
            provincia__iexact=provincia
        ).values_list('departamento', flat=True).distinct()
        return Response({'status': 'success', 'data': nombres_distintos(valores)}, status=200)


class LocalidadesPublicacionesView(APIView):
    """
    Localidades de un departamento donde hay mascotas en adopcion:
    /api/publicaciones/localidades/?provincia=Santa Fe&departamento=Rosario
    """

    def get(self, request):
        provincia = request.query_params.get('provincia', '').strip()
        departamento = request.query_params.get('departamento', '').strip()
        if not provincia or not departamento:
            return Response({'status': 'error', 'data': 'Indicá la provincia y el departamento'},
                            status=status.HTTP_400_BAD_REQUEST)
        valores = Publicaciones.objects.filter(
            estado=Publicaciones.EN_ADOPCION,
            provincia__iexact=provincia,
            departamento__iexact=departamento
        ).values_list('localidad', flat=True).distinct()
        return Response({'status': 'success', 'data': nombres_distintos(valores)}, status=200)


class PublicacionesView(APIView):

    def get(self, request, *args, **kwargs):
        id = kwargs.get('id', None)
        if id:
            resultado = get_object_or_404(Publicaciones, id_publicacion=id)
            serializer = PublicacionesSerializer(resultado)
            return Response({'status': 'success', 'data': serializer.data}, status=200)

        # select_related trae de una sola vez los datos del animal, del rescatista
        # y de su ubicacion. Sin esto Django haria una consulta por cada publicacion
        # y con muchas publicaciones el catalogo se pondria lento.
        resultado = Publicaciones.objects.select_related(
            'animal', 'rescatista', 'rescatista__ubicacion'
        ).all()

        # ---- Filtros del catalogo ----
        provincia = request.query_params.get('provincia', None)
        departamento = request.query_params.get('departamento', None)
        localidad = request.query_params.get('localidad', None)
        estado = request.query_params.get('estado', None)
        castrado = request.query_params.get('castrado', None)
        id_rescatista = request.query_params.get('id_rescatista', None)
        # Para esconder publicaciones de gente bloqueada usamos al usuario del token.
        id_usuario = request.user.id_usuario if request.user.is_authenticated else None

        # La ubicacion se filtra por la que heredo la publicacion al crearse.
        if provincia:
            resultado = resultado.filter(provincia__iexact=provincia)
        if departamento:
            resultado = resultado.filter(departamento__iexact=departamento)
        if localidad:
            resultado = resultado.filter(localidad__iexact=localidad)
        if estado:
            resultado = resultado.filter(estado__iexact=estado)
        if castrado is not None:
            # "castrado" está en la tabla animales, por eso el animal__castrado.
            # Ademas, de la URL todo llega como texto: hay que pasar "true" a booleano.
            resultado = resultado.filter(animal__castrado=(castrado.lower() == 'true'))
        if id_rescatista:
            resultado = resultado.filter(rescatista_id=id_rescatista)

        # Si nos dicen quien este mirando el catalogo, escondemos las publicaciones
        # de la gente con la que hay un bloqueo de por medio.
        if id_usuario:
            bloqueos = Bloqueos.objects.filter(
                # Q permite armar condiciones con "O". Aca: bloqueos donde yo bloqueé
                # a alguien O donde alguien me bloqueo a mi.
                Q(usuario_bloqueador_id=id_usuario) | Q(usuario_bloqueado_id=id_usuario),
                estado=Bloqueos.ACTIVO
            )
            usuarios_bloqueados = []
            for bloqueo in bloqueos:
                usuarios_bloqueados.append(bloqueo.usuario_bloqueador_id)
                usuarios_bloqueados.append(bloqueo.usuario_bloqueado_id)
            # exclude es lo contrario de filter: saca de la lista.
            # __in significa "que este dentro de esta lista de ids".
            resultado = resultado.exclude(rescatista_id__in=usuarios_bloqueados)

        serializer = PublicacionesSerializer(resultado, many=True)
        return Response({'status': 'success', 'data': serializer.data}, status=200)

    def post(self, request):
        # Como Publicacion-Animal es 1 a 1, chequeamos primero que ese animal
        # no tenga ya una publicacion. Si no lo hacemos, MySQL rebota el insert
        # y al front le llega un error 500 en vez de un mensaje entendible.
        # El rescatista es el del token, no el que mande el front.
        if not request.user.is_authenticated:
            return sin_login()
        rescatista = request.user
        if rol(rescatista) != 'rescatista':
            return Response({'status': 'error', 'data': 'Solo una cuenta de rescatista puede crear publicaciones'},
                            status=status.HTTP_403_FORBIDDEN)
        # La publicacion hereda la ubicacion del rescatista, asi que tiene que estar completa.
        # Los que se registraron antes de que existiera el departamento no lo tienen.
        if not rescatista.ubicacion.departamento or not rescatista.ubicacion.ciudad:
            return Response({'status': 'error',
                             'data': 'Completá tu departamento y localidad en Mi Perfil antes de publicar'},
                            status=status.HTTP_400_BAD_REQUEST)

        # Chequeamos que el animal exista. Si no, MySQL rebota el insert por la
        # clave foranea y al front le llega un error 500.
        id_animal = request.data.get('animal_id', None)
        if not str(id_animal or '').isdigit():
            return Response({'status': 'error', 'data': 'Indicá el animal de la publicación'},
                            status=status.HTTP_400_BAD_REQUEST)
        animal = Animales.objects.filter(id_animal=id_animal).first()
        if animal is None:
            return Response({'status': 'error', 'data': 'El animal indicado no existe'},
                            status=status.HTTP_404_NOT_FOUND)
        if animal.rescatista_id != rescatista.id_usuario:
            return Response({'status': 'error', 'data': 'Solo podés publicar animales que cargaste vos'},
                            status=status.HTTP_403_FORBIDDEN)
        if Publicaciones.objects.filter(animal_id=id_animal).exists():
            return Response({'status': 'error', 'data': 'Ese animal ya tiene una publicación'},
                            status=status.HTTP_400_BAD_REQUEST)

        serializer = PublicacionesSerializer(data=datos_con(request, rescatista_id=rescatista.id_usuario))
        if serializer.is_valid():
            serializer.save()
            return Response({'status': 'success', 'data': serializer.data},
                            status=status.HTTP_201_CREATED)
        return Response({'status': 'error', 'data': serializer.errors},
                        status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, id):
        # El rescatista edita su publicacion (el estado va por EstadoPublicacionView).
        resultado = get_object_or_404(Publicaciones, id_publicacion=id)
        if not request.user.is_authenticated:
            return sin_login()
        if resultado.rescatista_id != request.user.id_usuario:
            return Response({'status': 'error', 'data': 'Solo el rescatista propietario puede modificar esta publicación'},
                            status=status.HTTP_403_FORBIDDEN)
        # El dueño y el animal de una publicacion no se cambian. El estado se cambia
        # con /api/publicaciones/<id>/estado/, que controla los pasos.
        datos = request.data.copy()
        datos.pop('rescatista_id', None)
        datos.pop('animal_id', None)
        datos.pop('estado', None)
        serializer = PublicacionesSerializer(resultado, data=datos, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'status': 'success', 'data': serializer.data})
        return Response({'status': 'error', 'data': serializer.errors},
                        status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, id=None):
        resultado = get_object_or_404(Publicaciones, id_publicacion=id)
        # La borra su dueño (el del token, no el id que mande el front) o un moderador.
        if not request.user.is_authenticated:
            return sin_login()
        if resultado.rescatista_id != request.user.id_usuario and not es_moderador(request.user):
            return Response({'status': 'error', 'data': 'Solo el rescatista propietario puede eliminar esta publicación'},
                            status=status.HTTP_403_FORBIDDEN)

        resultado.delete()
        return Response({'status': 'success', 'data': 'Publicación eliminada'})


class EstadoPublicacionView(APIView):
    """POST /api/publicaciones/<id>/estado/   Body: { "estado": "EN_PROCESO" }
    El rescatista dueño mueve su publicacion por estos pasos:
      EN_ADOPCION -> EN_PROCESO   (tiene que haber aceptado al menos una solicitud)
      EN_PROCESO  -> ADOPTADO     (se concreto la adopcion; las solicitudes pendientes
                                   se rechazan solas)
      EN_PROCESO  -> EN_ADOPCION  (la adopcion no se concreto)
    ADOPTADO es el final: la publicacion no se borra, solo sale del catalogo.
    """

    PASOS = {
        Publicaciones.EN_ADOPCION: (Publicaciones.EN_PROCESO,),
        Publicaciones.EN_PROCESO: (Publicaciones.ADOPTADO, Publicaciones.EN_ADOPCION),
        Publicaciones.ADOPTADO: (),
    }

    @transaction.atomic
    def post(self, request, id):
        if not request.user.is_authenticated:
            return sin_login()
        publicacion = get_object_or_404(Publicaciones.objects.select_for_update(), id_publicacion=id)
        if publicacion.rescatista_id != request.user.id_usuario:
            return Response({'status': 'error', 'data': 'Solo el rescatista propietario puede cambiar el estado'},
                            status=status.HTTP_403_FORBIDDEN)

        nuevo = str(request.data.get('estado', '')).upper()
        if nuevo not in self.PASOS[publicacion.estado]:
            if publicacion.estado == Publicaciones.ADOPTADO:
                mensaje = 'La mascota ya fue adoptada: la publicación no se puede cambiar'
            else:
                mensaje = 'No se puede pasar de ' + publicacion.get_estado_display() + ' a ese estado'
            return Response({'status': 'error', 'data': mensaje}, status=status.HTTP_400_BAD_REQUEST)

        if nuevo == Publicaciones.EN_PROCESO and not publicacion.solicitudes.filter(
                estado=SolicitudesAdopcion.ACEPTADA).exists():
            return Response({'status': 'error',
                             'data': 'Primero aceptá una solicitud de adopción para ponerla en proceso'},
                            status=status.HTTP_400_BAD_REQUEST)

        if nuevo == Publicaciones.ADOPTADO:
            publicacion.solicitudes.filter(estado=SolicitudesAdopcion.PENDIENTE).update(
                estado=SolicitudesAdopcion.RECHAZADA,
                motivo_rechazo='La mascota ya fue adoptada.'
            )

        publicacion.estado = nuevo
        publicacion.save(update_fields=['estado'])
        return Response({'status': 'success', 'data': PublicacionesSerializer(publicacion).data})


# ===========================================================================
# /api/solicitudes/   
# ===========================================================================
class SolicitudesAdopcionView(APIView):
    """Cada uno ve solo las solicitudes donde participa: el adoptante las que mandó
    y el rescatista las que llegaron a sus publicaciones. El moderador ve todas."""

    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return sin_login()
        id = kwargs.get('id', None)
        if id:
            resultado = get_object_or_404(SolicitudesAdopcion, id_solicitud=id)
            participantes = (resultado.adoptante_id, resultado.publicacion.rescatista_id)
            if request.user.id_usuario not in participantes and not es_moderador(request.user):
                return sin_permiso()
            serializer = SolicitudesAdopcionSerializer(resultado)
            return Response({'status': 'success', 'data': serializer.data}, status=200)

        resultado = SolicitudesAdopcion.objects.select_related(
            'adoptante', 'publicacion', 'publicacion__animal'
        ).all()
        if not es_moderador(request.user):
            resultado = resultado.filter(
                Q(adoptante_id=request.user.id_usuario) |
                Q(publicacion__rescatista_id=request.user.id_usuario)
            )

        id_adoptante = request.query_params.get('id_adoptante', None)
        id_rescatista = request.query_params.get('id_rescatista', None)
        id_publicacion = request.query_params.get('id_publicacion', None)
        estado = request.query_params.get('estado', None)

        # "Ver solicitudes enviadas" del adoptante 
        if id_adoptante:
            resultado = resultado.filter(adoptante_id=id_adoptante)
        # "Gestionar solicitudes" del rescatista: las solicitudes que
        # llegaron a mis publicaciones
        if id_rescatista:
            resultado = resultado.filter(publicacion__rescatista_id=id_rescatista)
        if id_publicacion:
            resultado = resultado.filter(publicacion_id=id_publicacion)
        if estado:
            resultado = resultado.filter(estado__iexact=estado)

        serializer = SolicitudesAdopcionSerializer(resultado, many=True)
        return Response({'status': 'success', 'data': serializer.data}, status=200)

    def post(self, request):
        # El adoptante manda la solicitud 
        id_publicacion = request.data.get('publicacion_id', None)
        publicacion = get_object_or_404(Publicaciones, id_publicacion=id_publicacion)
        # El adoptante es el del token, no el que mande el front.
        if not request.user.is_authenticated:
            return sin_login()
        adoptante = request.user
        adoptante_id = adoptante.id_usuario
        if rol(adoptante) != 'adoptante':
            return Response({'status': 'error', 'data': 'Solo una cuenta de adoptante puede solicitar una adopción'},
                            status=status.HTTP_403_FORBIDDEN)
        if publicacion.rescatista_id == adoptante.id_usuario:
            return Response({'status': 'error', 'data': 'No podés solicitar la adopción de tu propia publicación'},
                            status=status.HTTP_400_BAD_REQUEST)

        # No dejamos pedir un animal que ya fue adoptado
        if publicacion.estado == Publicaciones.ADOPTADO:
            return Response({'status': 'error', 'data': 'Esa publicación ya fue cerrada'},
                            status=status.HTTP_400_BAD_REQUEST)
        if hay_bloqueo(adoptante_id, publicacion.rescatista_id):
            return Response({'status': 'error', 'data': 'No podés enviar una solicitud a este rescatista'},
                            status=status.HTTP_403_FORBIDDEN)
        if SolicitudesAdopcion.objects.filter(adoptante_id=adoptante_id, publicacion=publicacion).exists():
            return Response({'status': 'error', 'data': 'Ya enviaste una solicitud para esta publicación'},
                            status=status.HTTP_400_BAD_REQUEST)

        serializer = SolicitudesAdopcionSerializer(data=datos_con(request, adoptante_id=adoptante_id))
        if serializer.is_valid():
            serializer.save()
            return Response({'status': 'success', 'data': serializer.data},
                            status=status.HTTP_201_CREATED)
        return Response({'status': 'error', 'data': serializer.errors},
                        status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, id):
        resultado = get_object_or_404(SolicitudesAdopcion, id_solicitud=id)
        if not request.user.is_authenticated:
            return sin_login()
        if resultado.adoptante_id != request.user.id_usuario:
            return sin_permiso()
        if 'estado' in request.data:
            return Response(
                {'status': 'error', 'data': 'Usá las acciones aceptar o rechazar para cambiar el estado'},
                status=status.HTTP_400_BAD_REQUEST
            )
        serializer = SolicitudesAdopcionSerializer(resultado, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'status': 'success', 'data': serializer.data})
        return Response({'status': 'error', 'data': serializer.errors},
                        status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, id=None):
        # La cancela el adoptante que la mandó, o la borra un moderador.
        resultado = get_object_or_404(SolicitudesAdopcion, id_solicitud=id)
        if not request.user.is_authenticated:
            return sin_login()
        if resultado.adoptante_id != request.user.id_usuario and not es_moderador(request.user):
            return sin_permiso()
        resultado.delete()
        return Response({'status': 'success', 'data': 'Solicitud eliminada'})


class AceptarSolicitudView(APIView):
    """POST /api/solicitudes/<id>/aceptar/   
    Cuando el rescatista acepta pasan 2 cosas juntas:
      1) la solicitud queda ACEPTADA
      2) se crea el chat entre las dos partes
    La publicacion no cambia de estado: el rescatista la pone EN_PROCESO
    cuando quiera, con /api/publicaciones/<id>/estado/.
    """

    # transaction.atomic hace que las operaciones sean "todo o nada".
    # Si falla la creacion del chat, se deshace tambien el cambio de estado
    # y no nos queda la base a medio actualizar.
    @transaction.atomic
    def post(self, request, id):
        solicitud = get_object_or_404(
            SolicitudesAdopcion.objects.select_for_update().select_related(
                'publicacion', 'publicacion__rescatista', 'publicacion__rescatista__tipo_usuario'
            ),
            id_solicitud=id
        )

        # El rescatista es el del token: tiene que ser el dueño de la publicacion.
        if not request.user.is_authenticated:
            return sin_login()
        if solicitud.publicacion.rescatista_id != request.user.id_usuario:
            return Response({'status': 'error', 'data': 'Solo el rescatista propietario puede aceptar esta solicitud'},
                            status=status.HTTP_403_FORBIDDEN)

        if solicitud.estado == SolicitudesAdopcion.ACEPTADA:
            chat = Chats.objects.filter(solicitud=solicitud).first()
            if chat is None:
                chat = Chats.objects.create(solicitud=solicitud)
            return Response({
                'status': 'success',
                'data': {
                    'solicitud': SolicitudesAdopcionSerializer(solicitud).data,
                    'chat': ChatsSerializer(chat).data,
                }
            }, status=200)
        if solicitud.estado == SolicitudesAdopcion.RECHAZADA:
            return Response({'status': 'error', 'data': 'No se puede aceptar una solicitud rechazada'},
                            status=status.HTTP_400_BAD_REQUEST)
        if solicitud.publicacion.estado == Publicaciones.ADOPTADO:
            return Response({'status': 'error', 'data': 'La publicación ya fue cerrada'},
                            status=status.HTTP_400_BAD_REQUEST)

        solicitud.estado = SolicitudesAdopcion.ACEPTADA
        solicitud.motivo_rechazo = None
        solicitud.save()

        # get_or_create: si ya existe el chat lo trae, y si no lo crea.
        # Asi evitamos crear dos chats para la misma solicitud.
        chat, creado = Chats.objects.get_or_create(solicitud=solicitud)

        return Response({
            'status': 'success',
            'data': {
                'solicitud': SolicitudesAdopcionSerializer(solicitud).data,
                'chat': ChatsSerializer(chat).data,
            }
        }, status=200)


class RechazarSolicitudView(APIView):
    """POST /api/solicitudes/<id>/rechazar/   (CU06)
    Body: { "motivo_rechazo": "ya se entregó el animal" }
    """

    def post(self, request, id):
        solicitud = get_object_or_404(SolicitudesAdopcion, id_solicitud=id)
        # El rescatista es el del token: tiene que ser el dueño de la publicacion.
        if not request.user.is_authenticated:
            return sin_login()
        if solicitud.publicacion.rescatista_id != request.user.id_usuario:
            return Response({'status': 'error', 'data': 'Solo el rescatista propietario puede rechazar esta solicitud'},
                            status=status.HTTP_403_FORBIDDEN)
        if solicitud.estado != SolicitudesAdopcion.PENDIENTE:
            return Response({'status': 'error', 'data': 'Solo se pueden rechazar solicitudes pendientes'},
                            status=status.HTTP_400_BAD_REQUEST)

        solicitud.estado = SolicitudesAdopcion.RECHAZADA
        solicitud.motivo_rechazo = request.data.get('motivo_rechazo', None)
        solicitud.save()
        return Response({'status': 'success',
                         'data': SolicitudesAdopcionSerializer(solicitud).data})


# ===========================================================================
# /api/chats/ y /api/mensajes/   
# ===========================================================================
class ChatsView(APIView):

    def get(self, request, *args, **kwargs):
        # El participante es el del token (antes venia como ?id_usuario= y
        # cualquiera podia leer los chats de otro).
        if not request.user.is_authenticated:
            return sin_login()
        id = kwargs.get('id', None)
        id_usuario = request.user.id_usuario

        if id:
            resultado = get_object_or_404(
                Chats.objects.select_related('solicitud', 'solicitud__publicacion'),
                id_chat=id,
                solicitud__estado=SolicitudesAdopcion.ACEPTADA
            )
            if id_usuario not in participantes_chat(resultado):
                return Response({'status': 'error', 'data': 'No participás en esta conversación'},
                                status=status.HTTP_403_FORBIDDEN)
            serializer = ChatsSerializer(resultado)
            return Response({'status': 'success', 'data': serializer.data}, status=200)

        resultado = Chats.objects.filter(solicitud__estado=SolicitudesAdopcion.ACEPTADA)

        # /api/chats/?id_usuario=5 -> los chats donde participa ese usuario,
        # sea como adoptante o como rescatista de la publicacion.
        resultado = resultado.filter(
            Q(solicitud__adoptante_id=id_usuario) |
            Q(solicitud__publicacion__rescatista_id=id_usuario)
        )

        serializer = ChatsSerializer(resultado, many=True)
        return Response({'status': 'success', 'data': serializer.data}, status=200)

    def post(self, request):
        return Response(
            {'status': 'error', 'data': 'El chat se crea automáticamente al aceptar una solicitud'},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )

    def delete(self, request, id=None):
        # Borrar un chat (con todos sus mensajes) es solo para moderadores.
        if not es_moderador(request.user):
            return sin_login() if not request.user.is_authenticated else sin_permiso()
        resultado = get_object_or_404(Chats, id_chat=id)
        resultado.delete()
        return Response({'status': 'success', 'data': 'Chat eliminado'})


class MensajesView(APIView):

    def get(self, request, *args, **kwargs):
        # El participante es el del token, no el ?id_usuario= que mande el front.
        if not request.user.is_authenticated:
            return sin_login()
        id = kwargs.get('id', None)
        id_usuario = request.user.id_usuario

        if id:
            resultado = get_object_or_404(
                Mensajes.objects.select_related(
                    'chat__solicitud', 'chat__solicitud__publicacion'
                ),
                id_mensaje=id,
                chat__solicitud__estado=SolicitudesAdopcion.ACEPTADA
            )
            if id_usuario not in participantes_chat(resultado.chat):
                return Response({'status': 'error', 'data': 'No participás en esta conversación'},
                                status=status.HTTP_403_FORBIDDEN)
            serializer = MensajesSerializer(resultado)
            return Response({'status': 'success', 'data': serializer.data}, status=200)

        id_chat = request.query_params.get('id_chat')
        if not id_chat:
            return Response({'status': 'error', 'data': 'Se requiere una conversación'},
                            status=status.HTTP_400_BAD_REQUEST)
        chat = get_object_or_404(
            Chats.objects.select_related('solicitud', 'solicitud__publicacion'),
            id_chat=id_chat,
            solicitud__estado=SolicitudesAdopcion.ACEPTADA
        )
        if id_usuario not in participantes_chat(chat):
            return Response({'status': 'error', 'data': 'No participás en esta conversación'},
                            status=status.HTTP_403_FORBIDDEN)

        resultado = Mensajes.objects.filter(chat=chat)
        # /api/mensajes/?id_chat=1 -> la conversacion aceptada.

        serializer = MensajesSerializer(resultado, many=True)
        return Response({'status': 'success', 'data': serializer.data}, status=200)

    def post(self, request):
        # Antes de guardar el mensaje chequeamos que no haya un bloqueo activo
        # entre las dos personas del chat.
        # El emisor es el del token: nadie puede mandar mensajes a nombre de otro.
        if not request.user.is_authenticated:
            return sin_login()
        id_emisor = request.user.id_usuario
        id_chat = request.data.get('chat_id', None)
        if not id_chat:
            return Response({'status': 'error', 'data': 'Se requiere el chat'},
                            status=status.HTTP_400_BAD_REQUEST)
        chat = get_object_or_404(Chats, id_chat=id_chat)

        if chat.solicitud.estado != SolicitudesAdopcion.ACEPTADA:
            return Response({'status': 'error', 'data': 'El chat estará disponible cuando se acepte la solicitud'},
                            status=status.HTTP_403_FORBIDDEN)

        adoptante_id = chat.solicitud.adoptante_id
        rescatista_id = chat.solicitud.publicacion.rescatista_id

        # El emisor tiene que ser uno de los dos participantes del chat
        if id_emisor not in (adoptante_id, rescatista_id):
            return Response({'status': 'error', 'data': 'El emisor no pertenece a este chat'},
                            status=status.HTTP_403_FORBIDDEN)

        if hay_bloqueo(adoptante_id, rescatista_id):
            return Response({'status': 'error', 'data': 'No se puede enviar: hay un bloqueo activo'},
                            status=status.HTTP_403_FORBIDDEN)

        serializer = MensajesSerializer(data=datos_con(request, emisor_id=id_emisor))
        if serializer.is_valid():
            serializer.save()
            return Response({'status': 'success', 'data': serializer.data},
                            status=status.HTTP_201_CREATED)
        return Response({'status': 'error', 'data': serializer.errors},
                        status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, id=None):
        # Un mensaje lo borra quien lo mandó, o un moderador.
        resultado = get_object_or_404(Mensajes, id_mensaje=id)
        if not request.user.is_authenticated:
            return sin_login()
        if resultado.emisor_id != request.user.id_usuario and not es_moderador(request.user):
            return sin_permiso()
        resultado.delete()
        return Response({'status': 'success', 'data': 'Mensaje eliminado'})


# ===========================================================================
# /api/reportes/  
# ===========================================================================
class ReportesView(APIView):
    """El moderador ve y gestiona todos los reportes. Los demas solo pueden
    reportar (a su nombre) y ver los reportes que hicieron."""

    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return sin_login()
        id = kwargs.get('id', None)
        if id:
            resultado = get_object_or_404(Reportes, id_reporte=id)
            if resultado.usuario_reportador_id != request.user.id_usuario and not es_moderador(request.user):
                return sin_permiso()
            serializer = ReportesSerializer(resultado, context={'moderador': es_moderador(request.user)})
            return Response({'status': 'success', 'data': serializer.data}, status=200)

        resultado = Reportes.objects.select_related(
            'usuario_reportador__tipo_usuario', 'usuario_reportador__ubicacion',
            'usuario_reportado__tipo_usuario', 'usuario_reportado__ubicacion',
            'moderador__tipo_usuario', 'moderador__ubicacion'
        ).all()
        if not es_moderador(request.user):
            resultado = resultado.filter(usuario_reportador_id=request.user.id_usuario)
        estado = request.query_params.get('estado', None)
        id_reportado = request.query_params.get('id_reportado', None)
        if estado:
            resultado = resultado.filter(estado__iexact=estado)
        if id_reportado:
            resultado = resultado.filter(usuario_reportado_id=id_reportado)
        # ?pendientes=true -> los que todavia no se resolvieron (PENDIENTE o EN_REVISION)
        if request.query_params.get('pendientes') == 'true':
            resultado = resultado.filter(estado__in=(Reportes.PENDIENTE, Reportes.EN_REVISION))

        serializer = ReportesSerializer(resultado, many=True, context={'moderador': es_moderador(request.user)})
        return Response({'status': 'success', 'data': serializer.data}, status=200)

    def post(self, request):
        # El que reporta es el del token; el moderador lo asigna despues el que lo gestiona.
        if not request.user.is_authenticated:
            return sin_login()
        datos = datos_con(request, usuario_reportador_id=request.user.id_usuario)
        datos.pop('moderador_id', None)
        # Si se reporta una publicacion, el reportado es siempre su rescatista
        # (no el que mande el front).
        id_publicacion = str(datos.get('publicacion_id') or '')
        if id_publicacion:
            publicacion = Publicaciones.objects.filter(
                id_publicacion=id_publicacion
            ).first() if id_publicacion.isdigit() else None
            if publicacion is None:
                return Response({'status': 'error', 'data': 'La publicación que querés reportar no existe'},
                                status=status.HTTP_404_NOT_FOUND)
            datos['usuario_reportado_id'] = publicacion.rescatista_id
        else:
            datos.pop('publicacion_id', None)
        if str(datos.get('usuario_reportado_id')) == str(request.user.id_usuario):
            return Response({'status': 'error', 'data': 'No podés reportarte a vos mismo'},
                            status=status.HTTP_400_BAD_REQUEST)
        # Con 3 strikes por reportar sin motivo se le bloquea la herramienta.
        if not request.user.puede_reportar():
            return Response({'status': 'error',
                             'data': 'Tu herramienta de reportes está bloqueada por reportes sin motivo'},
                            status=status.HTTP_403_FORBIDDEN)
        id_reportado = str(datos.get('usuario_reportado_id') or '')
        reportado = Usuarios.objects.select_related('tipo_usuario').filter(
            id_usuario=id_reportado
        ).first() if id_reportado.isdigit() else None
        if reportado is None:
            return Response({'status': 'error', 'data': 'El usuario que querés reportar no existe'},
                            status=status.HTTP_404_NOT_FOUND)
        if es_moderador(reportado):
            return Response({'status': 'error', 'data': 'No se puede reportar a un moderador'},
                            status=status.HTTP_400_BAD_REQUEST)
        # Un mismo usuario no puede tener dos reportes abiertos contra la misma persona.
        ya_reportado = Reportes.objects.filter(
            usuario_reportador_id=request.user.id_usuario,
            usuario_reportado=reportado,
            estado__in=(Reportes.PENDIENTE, Reportes.EN_REVISION)
        ).exists()
        if ya_reportado:
            return Response({'status': 'error', 'data': 'Ya tenés un reporte pendiente contra este usuario'},
                            status=status.HTTP_400_BAD_REQUEST)
        serializer = ReportesSerializer(data=datos)
        if serializer.is_valid():
            reporte = serializer.save()
            # Guardamos la conversacion entre los dos como evidencia para el moderador.
            reporte.evidencia = reporte.armar_evidencia()
            reporte.publicacion_reportada = reporte.armar_copia_publicacion()
            reporte.save(update_fields=['evidencia', 'publicacion_reportada'])
            return Response({'status': 'success', 'data': serializer.data},
                            status=status.HTTP_201_CREATED)
        return Response({'status': 'error', 'data': serializer.errors},
                        status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, id):
        if not es_moderador(request.user):
            return sin_login() if not request.user.is_authenticated else sin_permiso()
        resultado = get_object_or_404(Reportes, id_reporte=id)
        serializer = ReportesSerializer(resultado, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'status': 'success', 'data': serializer.data})
        return Response({'status': 'error', 'data': serializer.errors},
                        status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, id=None):
        if not es_moderador(request.user):
            return sin_login() if not request.user.is_authenticated else sin_permiso()
        resultado = get_object_or_404(Reportes, id_reporte=id)
        resultado.delete()
        return Response({'status': 'success', 'data': 'Reporte eliminado'})


class GestionarReporteView(APIView):
    """POST /api/reportes/<id>/<accion>/   (solo moderadores)
    Son los metodos del Moderador en el diagrama de dominio:
      revisar   -> lo marca EN_REVISION (lo esta mirando un moderador)
      ignorar   -> RECHAZADO, no pasa nada (el reporte no amerita sancion)
      advertir  -> ACEPTADO, le manda una alerta de comportamiento al reportado
                   Body: { "mensaje": "..." }
      suspender -> ACEPTADO, suspende al reportado X dias (0 = baja definitiva)
                   Body: { "dias": 7, "mensaje": "..." (opcional) }
      strike    -> RECHAZADO, le suma un strike al que reporto sin motivo.
                   Con 3 strikes no puede reportar mas.
    Todas aceptan "nota" (nota interna del moderador). El moderador es el del token.
    """

    DIAS_MAXIMOS = 365

    @transaction.atomic
    def post(self, request, id, accion):
        if not request.user.is_authenticated:
            return sin_login()
        if not es_moderador(request.user):
            return Response({'status': 'error', 'data': 'Solo un moderador puede gestionar reportes'},
                            status=status.HTTP_403_FORBIDDEN)
        moderador = request.user
        # select_for_update bloquea la fila: si dos moderadores resuelven a la vez,
        # el segundo ve el reporte ya resuelto y no se aplica dos veces la sancion.
        reporte = get_object_or_404(
            Reportes.objects.select_for_update().select_related('usuario_reportador', 'usuario_reportado'),
            id_reporte=id
        )

        if accion not in ('revisar', 'ignorar', 'advertir', 'suspender', 'strike'):
            return Response({'status': 'error', 'data': 'Acción inválida'},
                            status=status.HTTP_400_BAD_REQUEST)
        if reporte.estado not in (Reportes.PENDIENTE, Reportes.EN_REVISION):
            return Response({'status': 'error', 'data': 'Este reporte ya fue resuelto'},
                            status=status.HTTP_400_BAD_REQUEST)

        reporte.moderador = moderador
        if accion == 'revisar':
            reporte.estado = Reportes.EN_REVISION
            reporte.save()
            return Response({'status': 'success',
                             'data': ReportesSerializer(reporte, context={'moderador': True}).data})

        reportado = reporte.usuario_reportado
        reportador = reporte.usuario_reportador
        mensaje = str(request.data.get('mensaje') or '').strip()

        if accion == 'ignorar':
            reporte.estado = Reportes.RECHAZADO
            reporte.resolucion = Reportes.IGNORADO

        elif accion == 'advertir':
            if not mensaje:
                return Response({'status': 'error', 'data': 'Escribí el mensaje de la advertencia'},
                                status=status.HTTP_400_BAD_REQUEST)
            reporte.estado = Reportes.ACEPTADO
            reporte.resolucion = Reportes.ADVERTENCIA
            Alertas.objects.create(usuario=reportado, reporte=reporte,
                                   tipo=Alertas.ADVERTENCIA, mensaje=mensaje)

        elif accion == 'suspender':
            dias = str(request.data.get('dias', '')).strip()
            if not dias.isdigit() or int(dias) > self.DIAS_MAXIMOS:
                return Response({'status': 'error',
                                 'data': 'Indicá los días de suspensión (0 a 365; 0 = baja definitiva)'},
                                status=status.HTTP_400_BAD_REQUEST)
            dias = int(dias)
            if dias == 0:
                reportado.estado = Usuarios.BAJA
                reportado.save(update_fields=['estado'])
                aviso = 'Tu cuenta fue dada de baja por un moderador.'
            else:
                reportado.suspendido_hasta = timezone.now() + timedelta(days=dias)
                reportado.save(update_fields=['suspendido_hasta'])
                aviso = 'Tu cuenta estuvo suspendida ' + str(dias) + (' día' if dias == 1 else ' días') + '.'
            reporte.estado = Reportes.ACEPTADO
            reporte.resolucion = Reportes.SUSPENSION
            # La ve cuando vuelve a entrar despues de la suspension.
            Alertas.objects.create(usuario=reportado, reporte=reporte, tipo=Alertas.SUSPENSION,
                                   mensaje=(aviso + ' ' + mensaje).strip())

        elif accion == 'strike':
            reportador.strikes_reporte += 1
            reportador.save(update_fields=['strikes_reporte'])
            reporte.estado = Reportes.RECHAZADO
            reporte.resolucion = Reportes.STRIKE
            texto = ('Un moderador revisó un reporte tuyo y consideró que no tenía motivo. '
                     'Strike ' + str(reportador.strikes_reporte) + ' de ' + str(Usuarios.MAX_STRIKES_REPORTE) + '.')
            if not reportador.puede_reportar():
                texto += ' Tu herramienta de reportes quedó bloqueada.'
            Alertas.objects.create(usuario=reportador, reporte=reporte, tipo=Alertas.STRIKE,
                                   mensaje=(texto + ' ' + mensaje).strip())

        reporte.nota_moderador = str(request.data.get('nota') or '').strip() or None
        reporte.fecha_resolucion = timezone.now()
        reporte.save()
        return Response({'status': 'success',
                         'data': ReportesSerializer(reporte, context={'moderador': True}).data})


class GestionarSancionView(APIView):
    """POST /api/usuarios/<id>/sancion/<accion>/   (solo moderadores)
    Para deshacer sanciones desde el panel:
      levantar-suspension -> borra la suspension y, si estaba de baja, lo reactiva
      reiniciar-strikes   -> vuelve los strikes a 0 y le desbloquea los reportes
    """

    def post(self, request, id, accion):
        if not es_moderador(request.user):
            return sin_login() if not request.user.is_authenticated else sin_permiso()
        usuario = get_object_or_404(Usuarios, id_usuario=id)
        if accion == 'levantar-suspension':
            usuario.suspendido_hasta = None
            usuario.estado = Usuarios.ACTIVO
            usuario.save(update_fields=['suspendido_hasta', 'estado'])
        elif accion == 'reiniciar-strikes':
            usuario.strikes_reporte = 0
            usuario.save(update_fields=['strikes_reporte'])
        else:
            return Response({'status': 'error', 'data': 'Acción inválida'},
                            status=status.HTTP_400_BAD_REQUEST)
        return Response({'status': 'success', 'data': UsuariosSerializer(usuario).data})


# ===========================================================================
# /api/alertas/
# ===========================================================================
class AlertasView(APIView):
    """Cada usuario ve solo sus alertas. /api/alertas/?leida=false -> las que no vio."""

    def get(self, request):
        if not request.user.is_authenticated:
            return sin_login()
        resultado = Alertas.objects.filter(usuario_id=request.user.id_usuario)
        leida = request.query_params.get('leida', None)
        if leida is not None:
            resultado = resultado.filter(leida=(leida.lower() == 'true'))
        serializer = AlertasSerializer(resultado, many=True)
        return Response({'status': 'success', 'data': serializer.data}, status=200)


class MarcarAlertaLeidaView(APIView):
    """POST /api/alertas/<id>/leida/"""

    def post(self, request, id):
        if not request.user.is_authenticated:
            return sin_login()
        alerta = get_object_or_404(Alertas, id_alerta=id, usuario_id=request.user.id_usuario)
        alerta.leida = True
        alerta.save(update_fields=['leida'])
        return Response({'status': 'success', 'data': AlertasSerializer(alerta).data})


# ===========================================================================
# /api/bloqueos/  
# ===========================================================================
class BloqueosView(APIView):
    """Cada uno ve los bloqueos donde participa. Bloquear, desbloquear y borrar
    lo hace el que bloqueó (el del token). El moderador ve y gestiona todos."""

    def es_bloqueador(self, request, bloqueo):
        return bloqueo.usuario_bloqueador_id == request.user.id_usuario or es_moderador(request.user)

    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return sin_login()
        yo = request.user.id_usuario
        id = kwargs.get('id', None)
        if id:
            resultado = get_object_or_404(Bloqueos, id_bloqueo=id)
            if yo not in (resultado.usuario_bloqueador_id, resultado.usuario_bloqueado_id) \
                    and not es_moderador(request.user):
                return sin_permiso()
            serializer = BloqueosSerializer(resultado)
            return Response({'status': 'success', 'data': serializer.data}, status=200)

        resultado = Bloqueos.objects.all()
        if not es_moderador(request.user):
            # Los bloqueos donde participa el usuario, de los dos lados
            resultado = resultado.filter(
                Q(usuario_bloqueador_id=yo) | Q(usuario_bloqueado_id=yo)
            )
        serializer = BloqueosSerializer(resultado, many=True)
        return Response({'status': 'success', 'data': serializer.data}, status=200)

    def post(self, request):
        # El que bloquea es el del token.
        if not request.user.is_authenticated:
            return sin_login()
        datos = datos_con(request, usuario_bloqueador_id=request.user.id_usuario)
        # No dejamos que alguien se bloquee a si mismo
        if str(datos.get('usuario_bloqueado_id')) == str(request.user.id_usuario):
            return Response({'status': 'error', 'data': 'No podés bloquearte a vos mismo'},
                            status=status.HTTP_400_BAD_REQUEST)
        id_bloqueado = str(datos.get('usuario_bloqueado_id') or '')
        bloqueado = Usuarios.objects.select_related('tipo_usuario').filter(
            id_usuario=id_bloqueado
        ).first() if id_bloqueado.isdigit() else None
        if bloqueado is None:
            return Response({'status': 'error', 'data': 'El usuario que querés bloquear no existe'},
                            status=status.HTTP_404_NOT_FOUND)
        if es_moderador(bloqueado):
            return Response({'status': 'error', 'data': 'No se puede bloquear a un moderador'},
                            status=status.HTTP_400_BAD_REQUEST)

        # Hay un solo registro por pareja (unique_together): si ya lo habia
        # desbloqueado, lo volvemos a activar en vez de crear otro.
        existente = Bloqueos.objects.filter(
            usuario_bloqueador_id=request.user.id_usuario, usuario_bloqueado=bloqueado
        ).first()
        if existente is not None:
            if existente.estado == Bloqueos.ACTIVO:
                return Response({'status': 'error', 'data': 'Ya bloqueaste a este usuario'},
                                status=status.HTTP_400_BAD_REQUEST)
            existente.estado = Bloqueos.ACTIVO
            existente.fecha_bloqueo = timezone.now()
            existente.save(update_fields=['estado', 'fecha_bloqueo'])
            return Response({'status': 'success', 'data': BloqueosSerializer(existente).data},
                            status=status.HTTP_201_CREATED)

        serializer = BloqueosSerializer(data=datos)
        if serializer.is_valid():
            serializer.save()
            return Response({'status': 'success', 'data': serializer.data},
                            status=status.HTTP_201_CREATED)
        return Response({'status': 'error', 'data': serializer.errors},
                        status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, id):
        # Sirve para desbloquear: se manda { "estado": "ANULADO" }
        resultado = get_object_or_404(Bloqueos, id_bloqueo=id)
        if not request.user.is_authenticated:
            return sin_login()
        if not self.es_bloqueador(request, resultado):
            return sin_permiso()
        # Solo se puede cambiar el estado: quien bloquea y a quien no se tocan.
        datos = {'estado': request.data.get('estado')} if 'estado' in request.data else {}
        serializer = BloqueosSerializer(resultado, data=datos, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'status': 'success', 'data': serializer.data})
        return Response({'status': 'error', 'data': serializer.errors},
                        status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, id=None):
        resultado = get_object_or_404(Bloqueos, id_bloqueo=id)
        if not request.user.is_authenticated:
            return sin_login()
        if not self.es_bloqueador(request, resultado):
            return sin_permiso()
        resultado.delete()
        return Response({'status': 'success', 'data': 'Bloqueo eliminado'})
