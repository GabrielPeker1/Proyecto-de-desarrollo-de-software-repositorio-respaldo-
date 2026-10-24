"""
serializers.py es el traductor entre los objetos de Python y el JSON que viaja
por la API .
Usamos las dos ideas de la practica Backend 2:
  1) SerializerMethodField es para devolver el objeto relacionado completo.
  2) Campos "write_only" tipo tema_id para recibir los ids cuando hacemos
     POST/PATCH. Como esos campos no existen en el modelo, hay que escribir
     los metodos create() y update() a mano.
"""

from rest_framework import serializers
from django.contrib.auth.hashers import make_password
from django.db import transaction
from django.core.validators import RegexValidator

from .models import (
    TiposUsuario,
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
    Bloqueos,
)


# ---------------------------------------------------------------------------
# Serializers simples
# ---------------------------------------------------------------------------
class TiposUsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = TiposUsuario
        fields = '__all__'


def validar_localidad(provincia, departamento, ciudad):
    """Chequea que provincia, departamento y localidad existan en el catalogo
    y que vayan juntos (que la localidad sea de ese departamento y provincia).
    Devuelve los nombres tal cual estan en el catalogo, con mayusculas y tildes.
    """
    localidad = Localidades.objects.select_related('departamento__provincia').filter(
        nombre__iexact=(ciudad or '').strip(),
        departamento__nombre__iexact=(departamento or '').strip(),
        departamento__provincia__nombre__iexact=(provincia or '').strip(),
    ).first()
    if localidad is None:
        raise serializers.ValidationError(
            {'ciudad': 'La localidad elegida no corresponde a esa provincia y departamento.'}
        )
    return (localidad.departamento.provincia.nombre,
            localidad.departamento.nombre,
            localidad.nombre)


def armar_direccion(calle, numero, piso):
    """Valida calle + numero (+ piso opcional) y arma la direccion completa.
    Devuelve (calle, numero, piso, direccion_completa)."""
    calle = (calle or '').strip()
    numero = (numero or '').strip()
    piso = (piso or '').strip() or None
    errores = {}
    if not calle:
        errores['calle'] = 'Ingresá la calle.'
    if not numero.isdigit() or len(numero) > 6:
        errores['numero'] = 'El número debe tener solo dígitos.'
    if errores:
        raise serializers.ValidationError(errores)
    # Ej: "Av. Pellegrini 1250, piso 3"
    completa = f'{calle} {numero}' + (f', piso {piso}' if piso else '')
    return calle, numero, piso, completa


class UbicacionesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ubicaciones
        fields = '__all__'
        extra_kwargs = {
            'departamento': {'required': True, 'allow_blank': False, 'allow_null': False},
            'calle': {'required': True, 'allow_blank': False, 'allow_null': False},
            'numero': {'required': True, 'allow_blank': False, 'allow_null': False,
                       'validators': [RegexValidator(r'^\d{1,6}$', 'El número debe tener solo dígitos.')]},
            'piso': {'required': False},
            # No se manda: la armamos con calle + numero + piso.
            'direccion_completa': {'read_only': True},
        }

    def validate(self, attrs):
        # En un PATCH pueden mandar solo algunos campos: completamos con los que ya tenia.
        def valor(campo):
            if campo in attrs:
                return attrs[campo]
            return getattr(self.instance, campo, None)

        if self.instance is None or {'provincia', 'departamento', 'ciudad'} & attrs.keys():
            provincia, departamento, ciudad = validar_localidad(
                valor('provincia'), valor('departamento'), valor('ciudad')
            )
            attrs.update(provincia=provincia, departamento=departamento, ciudad=ciudad)

        if self.instance is None or {'calle', 'numero', 'piso'} & attrs.keys():
            calle, numero, piso, completa = armar_direccion(valor('calle'), valor('numero'), valor('piso'))
            attrs.update(calle=calle, numero=numero, piso=piso, direccion_completa=completa)
        return attrs

    def create(self, validated_data):
        # Si no mandaron zona_aproximada, la completamos con la ciudad.
        # Así siempre hay algo publico para mostrar.
        if not validated_data.get('zona_aproximada'):
            validated_data['zona_aproximada'] = validated_data.get('ciudad')
        return Ubicaciones.objects.create(**validated_data)


class FotosAnimalSerializer(serializers.ModelSerializer):
    #Recibimos el id del animal por un campo write_only.
    animal_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = FotosAnimal
        fields = ('id_foto', 'url_foto', 'animal_id')

    def create(self, validated_data):
        animal_id = validated_data.pop('animal_id')
        return FotosAnimal.objects.create(animal_id=animal_id, **validated_data)


class AnimalesSerializer(serializers.ModelSerializer):
    edad = serializers.CharField(
        max_length=50,
        validators=[RegexValidator(r'^\d+$', 'La edad debe contener solo números.')]
    )
    # El animal tiene una lista de fotos (viene de la otra tabla).
    # Con SerializerMethodField armamos esa lista a mano.
    fotos = serializers.SerializerMethodField()
    # Cuando creamos el animal podemos mandar las urls de las fotos de una,
    # en una lista. 
    fotos_urls = serializers.ListField(
        child=serializers.CharField(),
        write_only=True,
        required=False
    )

    class Meta:
        model = Animales
        fields = ('id_animal', 'nombre', 'especie', 'raza', 'edad', 'sexo',
                  'peso', 'vacunas_administradas', 'castrado', 'compatible_ninos',
                  'compatible_otros_animales', 'desparasitado', 'tiene_microchip',
                  'entrenamiento_basico', 'fotos', 'fotos_urls')
        extra_kwargs = {
            'especie': {'required': True, 'allow_blank': False, 'allow_null': False},
            'raza': {'required': True, 'allow_blank': False, 'allow_null': False},
            'sexo': {'required': True, 'allow_blank': False, 'allow_null': False},
            'peso': {'required': True, 'allow_null': False},
            'vacunas_administradas': {'required': True, 'allow_blank': False, 'allow_null': False},
        }

    def get_fotos(self, obj):
        # obj.fotos viene del related_name que pusimos en el modelo FotosAnimal.
        # .all() trae todas las fotos de ese animal.
        fotos = obj.fotos.all()
        return FotosAnimalSerializer(fotos, many=True).data

    def create(self, validated_data):
        # Sacamos las urls de la lista antes de crear el animal, porque
        # "fotos_urls" no es una columna de la tabla animales.
        fotos_urls = validated_data.pop('fotos_urls', [])
        animal = Animales.objects.create(**validated_data)
        #Creamos una fila en fotos_animal por cada url.
        for url in fotos_urls:
            FotosAnimal.objects.create(animal=animal, url_foto=url)
        return animal

    def update(self, instance, validated_data):
        fotos_urls = validated_data.pop('fotos_urls', None)
        # Actualizamos los campos normales del animal
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        # Si mandaron fotos nuevas, se las agregamos (no borramos las viejas)
        if fotos_urls is not None:
            for url in fotos_urls:
                FotosAnimal.objects.create(animal=instance, url_foto=url)
        return instance


# ---------------------------------------------------------------------------
# USUARIOS
# ---------------------------------------------------------------------------
class UsuarioPublicoSerializer(serializers.ModelSerializer):
    """Version 'recortada' del usuario, la que ve cualquiera desde el front.
    No muestra email, telefono ni direccion completa). Solo mostramos la zona aproximada.
    """
    tipo_usuario = serializers.SerializerMethodField()
    zona = serializers.SerializerMethodField()

    class Meta:
        model = Usuarios
        fields = ('id_usuario', 'nombre_completo', 'tipo_usuario', 'zona', 'estado')

    def get_tipo_usuario(self, obj):
        return obj.tipo_usuario.nombre

    def get_zona(self, obj):
        # Devolvemos solo provincia, ciudad y zona aproximada.
        # La direccion exacta nunca sale por aca.
        return {
            'provincia': obj.ubicacion.provincia,
            'ciudad': obj.ubicacion.ciudad,
            'zona_aproximada': obj.ubicacion.zona_aproximada,
        }


class PerfilPublicoSerializer(serializers.ModelSerializer):
    """Lo que ve un usuario cuando entra al perfil de otro:
    - el adoptante ve al rescatista: nombre, ubicacion y descripcion.
    - el rescatista ve al adoptante: nombre y ubicacion (sin descripcion).
    - calle, numero y piso: solo si el usuario eligio hacer publica su direccion.
    Nunca sale el email ni el telefono.
    """
    tipo_usuario = serializers.SerializerMethodField()
    provincia = serializers.CharField(source='ubicacion.provincia')
    departamento = serializers.CharField(source='ubicacion.departamento', allow_null=True)
    ciudad = serializers.CharField(source='ubicacion.ciudad')

    class Meta:
        model = Usuarios
        fields = ('id_usuario', 'nombre_completo', 'tipo_usuario',
                  'provincia', 'departamento', 'ciudad', 'descripcion')

    def get_tipo_usuario(self, obj):
        return obj.tipo_usuario.nombre

    def to_representation(self, obj):
        data = super().to_representation(obj)
        # La descripcion solo se muestra en el perfil de los rescatistas.
        if obj.tipo_usuario.nombre.lower() != 'rescatista':
            data.pop('descripcion')
        # La direccion es privada salvo que el usuario la haya hecho publica.
        if obj.direccion_publica:
            data.update(calle=obj.ubicacion.calle, numero=obj.ubicacion.numero, piso=obj.ubicacion.piso)
        return data


class UsuariosSerializer(serializers.ModelSerializer):
    """Version completa: la usa el propio usuario para ver/editar su perfil
    y el moderador para gestionar. Aca si van telefono y ubicacion completa.
    """
    # Para leer: devolvemos los objetos relacionados enteros.
    ubicacion = serializers.SerializerMethodField()
    tipo_usuario = serializers.SerializerMethodField()

    # Para escribir: recibimos los ids.
    ubicacion_id = serializers.IntegerField(write_only=True)
    tipo_usuario_id = serializers.IntegerField(write_only=True)
    provincia = serializers.CharField(max_length=100, required=False, write_only=True)
    departamento = serializers.CharField(max_length=100, required=False, write_only=True)
    ciudad = serializers.CharField(max_length=100, required=False, write_only=True)
    zona_aproximada = serializers.CharField(max_length=150, required=False, allow_blank=True, write_only=True)
    calle = serializers.CharField(max_length=150, required=False, write_only=True)
    numero = serializers.CharField(max_length=10, required=False, write_only=True)
    piso = serializers.CharField(max_length=10, required=False, allow_blank=True, allow_null=True, write_only=True)

    # La contraseña entra en texto plano pero nunca sale (write_only=True).
    # En la base guardamos el hash en password_encriptada.
    password = serializers.CharField(write_only=True, min_length=6)

    def validate_password(self, value):
        if self.instance is not None:
            raise serializers.ValidationError('Usá el cambio de contraseña para actualizarla.')
        return value

    class Meta:
        model = Usuarios
        fields = ('id_usuario', 'email', 'nombre_completo', 'telefono', 'descripcion',
                  'direccion_publica', 'estado',
                  'ubicacion', 'tipo_usuario',
                  'ubicacion_id', 'tipo_usuario_id', 'provincia', 'departamento', 'ciudad',
                  'zona_aproximada', 'calle', 'numero', 'piso', 'password')
        # El estado (ACTIVO/BAJA) solo lo cambia un moderador, con /usuarios/<id>/baja/.
        read_only_fields = ('estado',)

    def validate(self, attrs):
        # Calle, numero y piso: si cambia alguno desde el perfil, se valida y se rearma
        # la direccion completa. (En el registro se ignoran: van por /api/ubicaciones/.)
        if self.instance is not None and {'calle', 'numero', 'piso'} & attrs.keys():
            ubicacion = self.instance.ubicacion
            def valor(campo):
                return attrs[campo] if campo in attrs else getattr(ubicacion, campo, None)
            calle, numero, piso, completa = armar_direccion(valor('calle'), valor('numero'), valor('piso'))
            attrs.update(calle=calle, numero=numero, piso=piso, direccion_completa=completa)

        # Si cambian la ubicacion desde el perfil, tienen que mandar las tres
        # cosas juntas y tienen que existir en el catalogo.
        campos = ('provincia', 'departamento', 'ciudad')
        enviados = [campo for campo in campos if campo in attrs]
        if enviados:
            if len(enviados) != len(campos):
                raise serializers.ValidationError(
                    {'ciudad': 'Para cambiar la ubicación elegí provincia, departamento y localidad.'}
                )
            provincia, departamento, ciudad = validar_localidad(
                attrs['provincia'], attrs['departamento'], attrs['ciudad']
            )
            attrs.update(provincia=provincia, departamento=departamento, ciudad=ciudad)
        return attrs

    def get_ubicacion(self, obj):
        return UbicacionesSerializer(obj.ubicacion).data

    def get_tipo_usuario(self, obj):
        return TiposUsuarioSerializer(obj.tipo_usuario).data

    def create(self, validated_data):
        # Sacamos los campos que no son columnas de la tabla usuarios
        ubicacion_id = validated_data.pop('ubicacion_id')
        tipo_usuario_id = validated_data.pop('tipo_usuario_id')
        password = validated_data.pop('password')
        # Los datos de la ubicacion se cargan antes, con /api/ubicaciones/.
        for campo in ('provincia', 'departamento', 'ciudad', 'zona_aproximada',
                      'calle', 'numero', 'piso', 'direccion_completa'):
            validated_data.pop(campo, None)

        usuario = Usuarios.objects.create(
            ubicacion_id=ubicacion_id,
            tipo_usuario_id=tipo_usuario_id,
            # make_password convierte "1234" en algo tipo "pbkdf2_sha256$870000$..."
            # Es de una sola via, es decir, no se puede volver atras.
            password_encriptada=make_password(password),
            **validated_data
        )
        return usuario

    @transaction.atomic
    def update(self, instance, validated_data):
        # El rol y la ubicacion asignada NO se cambian desde el perfil: si no,
        # cualquiera podria hacerse moderador o apuntar a la direccion de otro.
        validated_data.pop('ubicacion_id', None)
        validated_data.pop('tipo_usuario_id', None)
        validated_data.pop('password', None)   # la contraseña tiene su propio endpoint

        # Los campos de la ubicacion van a la tabla ubicaciones, no a usuarios.
        campos_ubicacion = ('provincia', 'departamento', 'ciudad', 'zona_aproximada',
                            'calle', 'numero', 'piso', 'direccion_completa')
        datos_ubicacion = {campo: validated_data.pop(campo) for campo in campos_ubicacion
                           if campo in validated_data}

        # Campos comunes (email, nombre, telefono, descripcion, direccion_publica)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if datos_ubicacion:
            ubicacion = instance.ubicacion
            for attr, value in datos_ubicacion.items():
                setattr(ubicacion, attr, value)
            ubicacion.save()
        return instance


class LoginSerializer(serializers.Serializer):
    """Este no es un ModelSerializer porque no representa una tabla:
    solamente sirve para validar que en el login lleguen email y password.
    """
    email = serializers.EmailField()
    password = serializers.CharField()


class CambiarPasswordSerializer(serializers.Serializer):
    password_actual = serializers.CharField(write_only=True, trim_whitespace=False)
    password_nueva = serializers.CharField(write_only=True, min_length=6, trim_whitespace=False)


# ---------------------------------------------------------------------------
# PUBLICACIONES
# ---------------------------------------------------------------------------
class PublicacionesSerializer(serializers.ModelSerializer):
    # Para leer: el animal completo (con fotos) y el rescatista en version publica
    animal = serializers.SerializerMethodField()
    rescatista = serializers.SerializerMethodField()

    # Para escribir: los ids
    rescatista_id = serializers.IntegerField(write_only=True)
    animal_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Publicaciones
        fields = ('id_publicacion', 'descripcion', 'fecha_publicacion', 'estado',
                  'provincia', 'departamento', 'localidad',
                  'animal', 'rescatista', 'rescatista_id', 'animal_id')
        # La ubicacion no la manda el front: se hereda del rescatista en create().
        read_only_fields = ('provincia', 'departamento', 'localidad')
        extra_kwargs = {
            'descripcion': {'required': True, 'allow_blank': False, 'allow_null': False},
        }

    def get_animal(self, obj):
        return AnimalesSerializer(obj.animal).data

    def get_rescatista(self, obj):
        # Usamos el serializer público para no filtrar el telefono ni la
        # direccion exacta del rescatista en el catalogo.
        return UsuarioPublicoSerializer(obj.rescatista).data

    def create(self, validated_data):
        rescatista_id = validated_data.pop('rescatista_id')
        animal_id = validated_data.pop('animal_id')
        # La publicacion hereda la ubicacion que tiene el rescatista en este momento.
        ubicacion = Usuarios.objects.select_related('ubicacion').get(id_usuario=rescatista_id).ubicacion
        publicacion = Publicaciones.objects.create(
            rescatista_id=rescatista_id,
            animal_id=animal_id,
            provincia=ubicacion.provincia,
            departamento=ubicacion.departamento,
            localidad=ubicacion.ciudad,
            **validated_data
        )
        return publicacion

    def update(self, instance, validated_data):
        rescatista_id = validated_data.pop('rescatista_id', None)
        animal_id = validated_data.pop('animal_id', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if rescatista_id is not None:
            instance.rescatista_id = rescatista_id
        if animal_id is not None:
            instance.animal_id = animal_id

        instance.save()
        return instance


# ---------------------------------------------------------------------------
# SOLICITUDES DE ADOPCIÓN
# ---------------------------------------------------------------------------
class SolicitudesAdopcionSerializer(serializers.ModelSerializer):
    adoptante = serializers.SerializerMethodField()
    publicacion = serializers.SerializerMethodField()
    # Campo calculado: dice si esta solicitud ya tiene un chat abierto y cual es.
    id_chat = serializers.SerializerMethodField()

    adoptante_id = serializers.IntegerField(write_only=True)
    publicacion_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = SolicitudesAdopcion
        fields = ('id_solicitud', 'fecha_solicitud', 'estado', 'motivo_rechazo',
                  'adoptante', 'publicacion', 'id_chat',
                  'adoptante_id', 'publicacion_id')

    def get_adoptante(self, obj):
        return UsuarioPublicoSerializer(obj.adoptante).data

    def get_publicacion(self, obj):
        return PublicacionesSerializer(obj.publicacion).data

    def get_id_chat(self, obj):
        # hasattr chequea si existe el chat relacionado. Como la relacion es
        # OneToOne, si todavia no se creo el chat, obj.chat directamente
        # explota con un error. Por eso preguntamos primero.
        if hasattr(obj, 'chat'):
            return obj.chat.id_chat
        return None

    def create(self, validated_data):
        adoptante_id = validated_data.pop('adoptante_id')
        publicacion_id = validated_data.pop('publicacion_id')
        return SolicitudesAdopcion.objects.create(
            adoptante_id=adoptante_id,
            publicacion_id=publicacion_id,
            **validated_data
        )

    def update(self, instance, validated_data):
        validated_data.pop('adoptante_id', None)       # el adoptante no se cambia
        validated_data.pop('publicacion_id', None)     # la publicacion tampoco
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


# ---------------------------------------------------------------------------
# CHATS Y MENSAJES
# ---------------------------------------------------------------------------
class MensajesSerializer(serializers.ModelSerializer):
    emisor = serializers.SerializerMethodField()

    chat_id = serializers.IntegerField(write_only=True)
    emisor_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Mensajes
        fields = ('id_mensaje', 'contenido', 'fecha_envio', 'emisor',
                  'chat_id', 'emisor_id')

    def get_emisor(self, obj):
        return {
            'id_usuario': obj.emisor.id_usuario,
            'nombre_completo': obj.emisor.nombre_completo,
        }

    def create(self, validated_data):
        chat_id = validated_data.pop('chat_id')
        emisor_id = validated_data.pop('emisor_id')
        return Mensajes.objects.create(
            chat_id=chat_id,
            emisor_id=emisor_id,
            **validated_data
        )


class ChatsSerializer(serializers.ModelSerializer):
    solicitud = serializers.SerializerMethodField()
    participantes = serializers.SerializerMethodField()
    ultimo_mensaje = serializers.SerializerMethodField()

    solicitud_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Chats
        fields = ('id_chat', 'fecha_creacion', 'solicitud', 'participantes',
                  'ultimo_mensaje', 'solicitud_id')

    def get_solicitud(self, obj):
        # Devolvemos los datos justos para que el front arme la lista de chats:
        # el animal y su foto (la pantalla de chats muestra la foto del animal).
        solicitud = obj.solicitud
        animal = solicitud.publicacion.animal
        primera_foto = animal.fotos.first()
        return {
            'id_solicitud': solicitud.id_solicitud,
            'id_publicacion': solicitud.publicacion.id_publicacion,
            'animal': animal.nombre,
            'foto_animal': primera_foto.url_foto if primera_foto else None,
        }

    def get_participantes(self, obj):
        # En un chat siempre están el adoptante y el rescatista de esa publicacion
        return {
            'adoptante': UsuarioPublicoSerializer(obj.solicitud.adoptante).data,
            'rescatista': UsuarioPublicoSerializer(obj.solicitud.publicacion.rescatista).data,
        }

    def get_ultimo_mensaje(self, obj):
        # .last() trae el último de la lista (los mensajes vienen ordenados por fecha)
        mensaje = obj.mensajes.last()
        if mensaje is None:
            return None
        return MensajesSerializer(mensaje).data

    def create(self, validated_data):
        solicitud_id = validated_data.pop('solicitud_id')
        return Chats.objects.create(solicitud_id=solicitud_id, **validated_data)


# ---------------------------------------------------------------------------
# REPORTES Y BLOQUEOS
# ---------------------------------------------------------------------------
class ReportesSerializer(serializers.ModelSerializer):
    usuario_reportador = serializers.SerializerMethodField()
    usuario_reportado = serializers.SerializerMethodField()
    moderador = serializers.SerializerMethodField()

    usuario_reportador_id = serializers.IntegerField(write_only=True)
    usuario_reportado_id = serializers.IntegerField(write_only=True)
    # required=False porque cuando se crea el reporte todavia no hay moderador
    moderador_id = serializers.IntegerField(write_only=True, required=False)

    class Meta:
        model = Reportes
        fields = ('id_reporte', 'motivo', 'fecha_reporte', 'estado',
                  'usuario_reportador', 'usuario_reportado', 'moderador',
                  'usuario_reportador_id', 'usuario_reportado_id', 'moderador_id')

    def get_usuario_reportador(self, obj):
        return UsuarioPublicoSerializer(obj.usuario_reportador).data

    def get_usuario_reportado(self, obj):
        return UsuarioPublicoSerializer(obj.usuario_reportado).data

    def get_moderador(self, obj):
        if obj.moderador is None:
            return None
        return UsuarioPublicoSerializer(obj.moderador).data

    def create(self, validated_data):
        usuario_reportador_id = validated_data.pop('usuario_reportador_id')
        usuario_reportado_id = validated_data.pop('usuario_reportado_id')
        moderador_id = validated_data.pop('moderador_id', None)
        return Reportes.objects.create(
            usuario_reportador_id=usuario_reportador_id,
            usuario_reportado_id=usuario_reportado_id,
            moderador_id=moderador_id,
            **validated_data
        )

    def update(self, instance, validated_data):
        moderador_id = validated_data.pop('moderador_id', None)
        validated_data.pop('usuario_reportador_id', None)
        validated_data.pop('usuario_reportado_id', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if moderador_id is not None:
            instance.moderador_id = moderador_id
        instance.save()
        return instance


class BloqueosSerializer(serializers.ModelSerializer):
    usuario_bloqueador = serializers.SerializerMethodField()
    usuario_bloqueado = serializers.SerializerMethodField()

    usuario_bloqueador_id = serializers.IntegerField(write_only=True)
    usuario_bloqueado_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Bloqueos
        fields = ('id_bloqueo', 'fecha_bloqueo', 'estado',
                  'usuario_bloqueador', 'usuario_bloqueado',
                  'usuario_bloqueador_id', 'usuario_bloqueado_id')

    def get_usuario_bloqueador(self, obj):
        return UsuarioPublicoSerializer(obj.usuario_bloqueador).data

    def get_usuario_bloqueado(self, obj):
        return UsuarioPublicoSerializer(obj.usuario_bloqueado).data

    def create(self, validated_data):
        usuario_bloqueador_id = validated_data.pop('usuario_bloqueador_id')
        usuario_bloqueado_id = validated_data.pop('usuario_bloqueado_id')
        return Bloqueos.objects.create(
            usuario_bloqueador_id=usuario_bloqueador_id,
            usuario_bloqueado_id=usuario_bloqueado_id,
            **validated_data
        )
