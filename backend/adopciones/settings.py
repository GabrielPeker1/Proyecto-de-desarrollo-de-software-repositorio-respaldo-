"""
Configuracion del proyecto.
Definimos que apps usa el proyecto y a que base de datos se conecta.
"""

import os
from pathlib import Path

# Ruta base del proyecto (la carpeta donde esta manage.py)
BASE_DIR = Path(__file__).resolve().parent.parent

# Clave secreta que usa Django para firmar cosas (sesiones, tokens, etc.)
SECRET_KEY = 'django-insecure-cambiar-esta-clave-antes-de-produccion-dds2026g15'

# En True nos muestra los errores completos en el navegador.
DEBUG = True

# Qué direcciones pueden servir la app. Con '*' aceptamos todas.
ALLOWED_HOSTS = ['*']

# Registramos las apps. Las primeras 6 vienen de Django..
# 'corsheaders' lo agregamos para que Angular pueda pegarle a la API.
# 'adopciones' es nuestro propio proyecto.
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'adopciones',
]

# Los middleware son filtros por los que pasa cada request antes de llegar a la vista.
# CorsMiddleware tiene que ir bien arriba, antes que CommonMiddleware.
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Mientras desarrollamos dejamos que cualquier origen consuma la API.
# Cuando este el front en Angular, conviene cambiarlo por CORS_ALLOWED_ORIGINS
# con la lista de dominios reales (ej: http://localhost:4200).
CORS_ALLOW_ALL_ORIGINS = True

# Autenticacion de la API: el front manda "Authorization: Bearer <token>" y con eso
# sabemos quien hace el pedido (ver adopciones/autenticacion.py). Los pedidos sin
# token siguen funcionando como anonimos; cada vista decide si los deja pasar.
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': ['adopciones.autenticacion.TokenAutenticacion'],
}

ROOT_URLCONF = 'adopciones.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'adopciones.wsgi.application'

# Conexión a MySQL.
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'adopcionesdb',      # nombre del schema 
        'USER': 'root',
        # Con Docker vienen de docker-compose.yml. Sin Docker se usa lo de la derecha.
        'PASSWORD': os.environ.get('DB_PASSWORD', ''), #poner la clave acá
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': '3306',
    }
}

# Validaciones de contraseña de Django 
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Idioma y zona horaria. Los ponemos en Argentina para que las fechas
# que guardamos tengan la hora local.
LANGUAGE_CODE = 'es-ar'
TIME_ZONE = 'America/Argentina/Buenos_Aires'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Tipo de id automatico por defecto 
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
