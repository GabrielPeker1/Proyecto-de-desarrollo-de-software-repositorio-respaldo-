"""
Tablas de la base de datos.
Cada clase que hereda de models.Model se transforma en una tabla cuando corremos
makemigrations + migrate.
Los nombres de tablas y columnas son los del diagrama Entidad-Relación.
"""

from django.db import models


# ---------------------------------------------------------------------------
# tabla tipos_usuario
# Es la tabla que dice si alguien es Adoptante, Rescatista o Moderador.
# ---------------------------------------------------------------------------
class TiposUsuario(models.Model):
    id_tipo_usuario = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=50, unique=True)

    class Meta:
        # db_table le dice a Django como se tiene que llamar la tabla en MySQL.
        # Si no lo ponemos, Django la llamaria "adopciones_tiposusuario" y no
        # coincidiria con nuestro diagrama E-R.
        db_table = 'tipos_usuario'
        verbose_name_plural = 'Tipos de usuario'

    def __str__(self):
        return self.nombre


# ---------------------------------------------------------------------------
# tablas provincias, departamentos y localidades
# Es el catalogo oficial de Argentina (API Georef del IGN/INDEC). No lo cargan
# los usuarios: se llena solo con la migracion 0006 a partir del archivo
# data/georef_argentina.json. Sirve para los desplegables del registro y el perfil.
# Usamos como clave el codigo oficial de Georef (ej: Santa Fe = "82").
# ---------------------------------------------------------------------------
class Provincias(models.Model):
    id_provincia = models.CharField(max_length=2, primary_key=True)
    nombre = models.CharField(max_length=100, unique=True)

    class Meta:
        db_table = 'provincias'
        verbose_name_plural = 'Provincias'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Departamentos(models.Model):
    id_departamento = models.CharField(max_length=5, primary_key=True)
    provincia = models.ForeignKey(
        Provincias,
        on_delete=models.CASCADE,
        db_column='id_provincia',
        related_name='departamentos'
    )
    nombre = models.CharField(max_length=100)

    class Meta:
        db_table = 'departamentos'
        verbose_name_plural = 'Departamentos'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre + ', ' + self.provincia.nombre


class Localidades(models.Model):
    id_localidad = models.CharField(max_length=10, primary_key=True)
    departamento = models.ForeignKey(
        Departamentos,
        on_delete=models.CASCADE,
        db_column='id_departamento',
        related_name='localidades'
    )
    nombre = models.CharField(max_length=100)

    class Meta:
        db_table = 'localidades'
        verbose_name_plural = 'Localidades'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre + ', ' + self.departamento.nombre


# ---------------------------------------------------------------------------
# tabla ubicaciones
# Guarda donde vive el usuario. direccion_completa es dato privado,
# zona_aproximada es lo unico que se muestra en las publicaciones.
# provincia, departamento y ciudad (la localidad) se eligen del catalogo de arriba.
# Los guardamos como texto para que el filtro del catalogo siga igual.
# ---------------------------------------------------------------------------
class Ubicaciones(models.Model):
    id_ubicacion = models.AutoField(primary_key=True)
    provincia = models.CharField(max_length=100)
    # null=True porque los usuarios que se registraron antes no lo tienen.
    departamento = models.CharField(max_length=100, blank=True, null=True)
    # En la ciudad guardamos el nombre de la localidad.
    ciudad = models.CharField(max_length=100)
    # La direccion se carga en tres partes. null=True porque los usuarios que se
    # registraron antes solo tienen direccion_completa. El piso es opcional (casas).
    calle = models.CharField(max_length=150, blank=True, null=True)
    numero = models.CharField(max_length=10, blank=True, null=True)
    piso = models.CharField(max_length=10, blank=True, null=True)
    # Se arma sola con calle + numero + piso (ver UbicacionesSerializer).
    direccion_completa = models.CharField(max_length=200)
    # blank=True + null=True significa "este campo puede venir vacio".
    # Si no lo mandan, en el serializer lo completamos solos con la ciudad.
    zona_aproximada = models.CharField(max_length=150, blank=True, null=True)

    class Meta:
        db_table = 'ubicaciones'
        verbose_name_plural = 'Ubicaciones'

    def __str__(self):
        return self.ciudad + ', ' + self.provincia


# ---------------------------------------------------------------------------
# tabla usuarios
# El usuario base del diagrama de dominio. El rol lo define tipo_usuario.
# ---------------------------------------------------------------------------
class Usuarios(models.Model):
    # Estos son los estados posibles del usuario. Los dejamos como constantes
    # para no andar escribiendo el texto a mano en cada vista y equivocarnos.
    ACTIVO = 'ACTIVO'
    BAJA = 'BAJA'
    ESTADOS = [
        (ACTIVO, 'Activo'),
        (BAJA, 'Dado de baja'),
    ]

    # No es una columna: Django REST Framework lo pregunta para saber si
    # request.user es un usuario logueado (los anonimos devuelven False).
    is_authenticated = True

    id_usuario = models.AutoField(primary_key=True)

    # ForeignKey = "este usuario apunta a una ubicacion".
    # db_column hace que la columna se llame id_ubicacion y no ubicacion_id.
    # related_name es el nombre con el que se hace el camino inverso:
    # desde una ubicacion podemos hacer ubicacion.usuarios.all()
    ubicacion = models.ForeignKey(
        Ubicaciones,
        on_delete=models.CASCADE,
        db_column='id_ubicacion',
        related_name='usuarios'
    )
    tipo_usuario = models.ForeignKey(
        TiposUsuario,
        on_delete=models.CASCADE,
        db_column='id_tipo_usuario',
        related_name='usuarios'
    )

    # unique=True hace que MySQL no deje repetir el mail.
    # EmailField ademas chequea que tenga formato de mail.
    email = models.EmailField(max_length=200, unique=True)

    # Aca no guardamos la contraseña como la escribio el usuario, guardamos el
    # hash que genera Django.
    password_encriptada = models.CharField(max_length=255)

    telefono = models.CharField(max_length=20, blank=True, null=True)
    nombre_completo = models.CharField(max_length=150)
    # Descripcion opcional que el usuario escribe sobre si mismo.
    descripcion = models.TextField(max_length=500, blank=True, null=True)
    # Si la calle, numero y piso se muestran en el perfil publico. Privada por defecto;
    # el usuario la cambia desde Mi Perfil.
    direccion_publica = models.BooleanField(default=False)
    estado = models.CharField(max_length=20, choices=ESTADOS, default=ACTIVO)

    class Meta:
        db_table = 'usuarios'
        verbose_name_plural = 'Usuarios'

    def __str__(self):
        return self.nombre_completo + ' (' + self.email + ')'


# ---------------------------------------------------------------------------
# tabla animales
# ---------------------------------------------------------------------------
class Animales(models.Model):
    id_animal = models.AutoField(primary_key=True)
    # El rescatista que cargo el animal. Hace falta porque el animal se crea antes
    # que su publicacion, y mientras tanto solo su dueño puede editarlo o subirle fotos.
    # null=True por los animales que se cargaron antes de que existiera esta columna.
    rescatista = models.ForeignKey(
        'Usuarios',
        on_delete=models.CASCADE,
        db_column='id_rescatista',
        related_name='animales',
        blank=True,
        null=True
    )
    nombre = models.CharField(max_length=100)
    especie = models.CharField(max_length=50, default='Perro')
    raza = models.CharField(max_length=100, blank=True, null=True)
    edad = models.CharField(max_length=50)
    sexo = models.CharField(max_length=20, blank=True, null=True)
    peso = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    vacunas_administradas = models.CharField(max_length=255, blank=True, null=True)
    castrado = models.BooleanField(default=False)
    compatible_ninos = models.BooleanField(default=False)
    compatible_otros_animales = models.BooleanField(default=False)
    desparasitado = models.BooleanField(default=False)
    tiene_microchip = models.BooleanField(default=False)
    entrenamiento_basico = models.BooleanField(default=False)

    class Meta:
        db_table = 'animales'
        verbose_name_plural = 'Animales'

    def __str__(self):
        return self.nombre


# ---------------------------------------------------------------------------
# tabla fotos_animal
# ---------------------------------------------------------------------------
class FotosAnimal(models.Model):
    id_foto = models.AutoField(primary_key=True)
    animal = models.ForeignKey(
        Animales,
        on_delete=models.CASCADE,   # si se borra el animal, se borran sus fotos
        db_column='id_animal',
        related_name='fotos'
    )
    url_foto = models.CharField(max_length=500)

    class Meta:
        db_table = 'fotos_animal'
        verbose_name_plural = 'Fotos de animales'

    def __str__(self):
        return self.url_foto


# ---------------------------------------------------------------------------
# tabla publicaciones
# La publicacion que arma el rescatista con un animal.
# ---------------------------------------------------------------------------
class Publicaciones(models.Model):
    EN_ADOPCION = 'EN_ADOPCION'
    EN_PROCESO = 'EN_PROCESO'
    ADOPTADO = 'ADOPTADO'
    ESTADOS = [
        (EN_ADOPCION, 'En adopción'),
        (EN_PROCESO, 'En proceso'),
        (ADOPTADO, 'Adoptado'),
    ]

    id_publicacion = models.AutoField(primary_key=True)
    rescatista = models.ForeignKey(
        Usuarios,
        on_delete=models.CASCADE,
        db_column='id_rescatista',
        related_name='publicaciones'
    )
    # Usamos OneToOneField debido a que la relacion de animal con publicacion es 1 a 1.
    animal = models.OneToOneField(
        Animales,
        on_delete=models.CASCADE,
        db_column='id_animal',
        related_name='publicacion'
    )
    descripcion = models.TextField(blank=True, null=True)
    # La ubicacion se hereda del rescatista cuando se crea la publicacion (la copia
    # el serializer). Si despues el rescatista se muda, la publicacion no cambia.
    # Con estas columnas filtra el catalogo.
    provincia = models.CharField(max_length=100, blank=True, null=True)
    departamento = models.CharField(max_length=100, blank=True, null=True)
    localidad = models.CharField(max_length=100, blank=True, null=True)
    # auto_now_add=True carga la fecha y hora sola cuando se crea el registro.
    # Así el front no tiene que mandar la fecha.
    fecha_publicacion = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, choices=ESTADOS, default=EN_ADOPCION)

    class Meta:
        db_table = 'publicaciones'
        verbose_name_plural = 'Publicaciones'
        # ordering hace que las consultas vengan siempre de la mas nueva a la mas vieja.
        # El '-' adelante significa orden descendente.
        ordering = ['-fecha_publicacion']

    def __str__(self):
        return 'Publicación ' + str(self.id_publicacion) + ' - ' + self.animal.nombre


# ---------------------------------------------------------------------------
# tabla solicitudes_adopcion
# El adoptante manda una solicitud sobre una publicacion.
# ---------------------------------------------------------------------------
class SolicitudesAdopcion(models.Model):
    PENDIENTE = 'PENDIENTE'
    ACEPTADA = 'ACEPTADA'
    RECHAZADA = 'RECHAZADA'
    ESTADOS = [
        (PENDIENTE, 'Pendiente'),
        (ACEPTADA, 'Aceptada'),
        (RECHAZADA, 'Rechazada'),
    ]

    id_solicitud = models.AutoField(primary_key=True)
    adoptante = models.ForeignKey(
        Usuarios,
        on_delete=models.CASCADE,
        db_column='id_adoptante',
        related_name='solicitudes'
    )
    publicacion = models.ForeignKey(
        Publicaciones,
        on_delete=models.CASCADE,
        db_column='id_publicacion',
        related_name='solicitudes'
    )
    fecha_solicitud = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, choices=ESTADOS, default=PENDIENTE)
    motivo_rechazo = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'solicitudes_adopcion'
        verbose_name_plural = 'Solicitudes de adopción'
        ordering = ['-fecha_solicitud']
        # unique_together evita que el mismo adoptante mande 20 veces la misma
        # solicitud a la misma publicacion.
        unique_together = ('adoptante', 'publicacion')

    def __str__(self):
        return 'Solicitud ' + str(self.id_solicitud) + ' - ' + self.estado


# ---------------------------------------------------------------------------
# tabla chats
# Se crea recien cuando el rescatista acepta una solicitud.
# ---------------------------------------------------------------------------
class Chats(models.Model):
    id_chat = models.AutoField(primary_key=True)
    # OneToOneField = uno a uno. 
    # Una solicitud como mucho tiene un chat.
    solicitud = models.OneToOneField(
        SolicitudesAdopcion,
        on_delete=models.CASCADE,
        db_column='id_solicitud',
        related_name='chat'
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'chats'
        verbose_name_plural = 'Chats'
        ordering = ['-fecha_creacion']

    def __str__(self):
        return 'Chat ' + str(self.id_chat)


# ---------------------------------------------------------------------------
# tabla mensajes
# Los mensajes que se mandan dentro de un chat.
# ---------------------------------------------------------------------------
class Mensajes(models.Model):
    id_mensaje = models.AutoField(primary_key=True)
    chat = models.ForeignKey(
        Chats,
        on_delete=models.CASCADE,
        db_column='id_chat',
        related_name='mensajes'
    )
    emisor = models.ForeignKey(
        Usuarios,
        on_delete=models.CASCADE,
        db_column='id_emisor',
        related_name='mensajes_enviados'
    )
    contenido = models.TextField()
    fecha_envio = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'mensajes'
        verbose_name_plural = 'Mensajes'
        # Aca sin el '-' porque un chat se lee del mensaje mas viejo al ma nuevo.
        ordering = ['fecha_envio']

    def __str__(self):
        return 'Mensaje ' + str(self.id_mensaje)


# ---------------------------------------------------------------------------
# tabla reportes
# Un usuario reporta a otro y un moderador lo gestiona.
# ---------------------------------------------------------------------------
class Reportes(models.Model):
    PENDIENTE = 'PENDIENTE'
    EN_REVISION = 'EN_REVISION'
    ACEPTADO = 'ACEPTADO'
    RECHAZADO = 'RECHAZADO'
    ESTADOS = [
        (PENDIENTE, 'Pendiente'),
        (EN_REVISION, 'En revisión'),
        (ACEPTADO, 'Aceptado'),
        (RECHAZADO, 'Rechazado'),
    ]

    id_reporte = models.AutoField(primary_key=True)
    # hay 2 ForeignKey a la misma tabla (usuarios). Por eso el
    # related_name es obligatorio y distinto en cada una, si no Django no sabe
    # cual es cual cuando hacemos el camino inverso.
    usuario_reportador = models.ForeignKey(
        Usuarios,
        on_delete=models.CASCADE,
        db_column='id_usuario_reportador',
        related_name='reportes_hechos'
    )
    usuario_reportado = models.ForeignKey(
        Usuarios,
        on_delete=models.CASCADE,
        db_column='id_usuario_reportado',
        related_name='reportes_recibidos'
    )
    # El moderador arranca vacio (todavia nadie lo reviso), por eso null=True.
    # SET_NULL por si se borra el moderador, el reporte no se borra, solo queda sin moderador.
    moderador = models.ForeignKey(
        Usuarios,
        on_delete=models.SET_NULL,
        db_column='id_moderador',
        related_name='reportes_moderados',
        blank=True,
        null=True
    )
    motivo = models.TextField()
    fecha_reporte = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, choices=ESTADOS, default=PENDIENTE)

    class Meta:
        db_table = 'reportes'
        verbose_name_plural = 'Reportes'
        ordering = ['-fecha_reporte']

    def __str__(self):
        return 'Reporte ' + str(self.id_reporte) + ' - ' + self.estado


# ---------------------------------------------------------------------------
# tabla bloqueos
# Un usuario bloquea a otro.
# ---------------------------------------------------------------------------
class Bloqueos(models.Model):
    ACTIVO = 'ACTIVO'
    ANULADO = 'ANULADO'
    ESTADOS = [
        (ACTIVO, 'Activo'),
        (ANULADO, 'Anulado'),
    ]

    id_bloqueo = models.AutoField(primary_key=True)
    usuario_bloqueador = models.ForeignKey(
        Usuarios,
        on_delete=models.CASCADE,
        db_column='id_usuario_bloqueador',
        related_name='bloqueos_hechos'
    )
    usuario_bloqueado = models.ForeignKey(
        Usuarios,
        on_delete=models.CASCADE,
        db_column='id_usuario_bloqueado',
        related_name='bloqueos_recibidos'
    )
    fecha_bloqueo = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, choices=ESTADOS, default=ACTIVO)

    class Meta:
        db_table = 'bloqueos'
        verbose_name_plural = 'Bloqueos'
        ordering = ['-fecha_bloqueo']
        # No tiene sentido bloquear dos veces a la misma persona.
        unique_together = ('usuario_bloqueador', 'usuario_bloqueado')

    def __str__(self):
        return str(self.usuario_bloqueador_id) + ' bloqueó a ' + str(self.usuario_bloqueado_id)
