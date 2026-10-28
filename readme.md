## Como levantar el proyecto

Se puede levantar con docker a través de docker

crear la imagen por primera vez con
```bash
docker compose build
```
luego levantar la imagen con

```bash
docker compose up -d
```

ver los puertos con

```bash
docker compose ps
```

levantar

FRONT: http://localhost:4200
BACK: http://localhost:8000

O através de la consola con
### Backend

Para levantar el backend hacer estos pasos

Si es la primera vez hacer los pasos del 1 al 6, si hacer el paso 1 y 7
1) Abrir un terminal y ejecutar

    ```bash
    CD backend 
    ```

2) Una vez entramos en la directorio del backend cargamos los requerimientos con
    ```bash
    pip install -r requirements.txt
    ```

    Que instalará los requerimientos de nuestro proyecto (Django, Django REST Framework, mysqlclient y django-cors-headers.)

3) luego abrimos MySQL Workbench en el 
    ```Local instance MySQL80``` escribimos

    ```sql
    CREATE DATABASE adopcionesdb CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
    ```

    y ejecutar (rayito ⚡) con esto creamos la tabla adopcionesbd que estará vacia.

4) ahora abrimos el archivo settings.py que se encuentra en ```backend/adopciones``` y buscamos  ```DATABASE``` esta parte del código

    ```python
    DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'adopcionesdb',      # nombre del schema 
        'USER': 'root',
        'PASSWORD': '', #poner la clave acá
        'HOST': 'localhost',
        'PORT': '3306',
    }
    }
    ```

    y poner nuestra constraseña en 'PASSWORD'

5) Ahora ya podemos crear y migrar las tablas

    ```bash
    python manage.py makemigrations adopciones
    python manage.py migrate
    ```

    y cargamos los tipos de usuario (adoptante, rescatista y moderador) con

    ```bash
    python manage.py loaddata datos_iniciales
    ```

6) creamos el super usuario con
    ```bash
    python manage.py createsuperuser
    ```
7) Ahora finalmente levantamos el backend con
    ```bash
    python manage.py runserver
    ```
Ya tendremos el backend corriendo en http://127.0.0.1:8000/

## Frontend

Si es la primera vez que se levanta el frontend ejecutar todos los pasos si no el 1 y 2

1) Abrir un terminal y ejecutar

    ```bash
    CD frontend
    ```

2) ejecutar el siguiente comando
    ```bash
    npm install
    ```
    en caso de error ejecutar

    ```bash
    npm install --legacy-peer-deps
    ```

3) ejecutar el siguiente comando para levantar el frontend

    ```bash
    ng serve
    ```
    ya tenemos el proyecto levantado en
    http://localhost:4200/

## COMO USAR EL SISTEMA

El sistema cuenta con 3 tipos de usuarios

- Rescatista:

    Este usuario se tiene que registrar en http://localhost:4200/registro

    y puede realizar esta acciones

    * Crear una publicación de un animal
    * Aceptar o rechazar una solicitud de adopción
    * Chatear con un posible adoptante
    * Poner una publicación como en proceso, que sucede cuando ya hay un posible adoptante para un animal. Acá la publicación ya no le aparecerá al resto de adoptantes
    * Poner la publicación como adoptado que es cuando se concretó una adopción
    * Eliminar una publicación

- Adoptante:

    Este usuario se tiene que registrar en http://localhost:4200/registro

    y puede realizar esta acciones
    * Buscar una publicación acorde al animal que quiera adoptar
    * Chatear con un rescatista que tenga una posible mascota que busque


Ambos pueden reportar usuarios, publicaciones y bloquear usuarios

- Moderador 
    Este usuario no se puede registrar se crea a través de ejecutar el siguiente comando

    ```bash
     python manage.py crear_moderador --email (unemail) --nombre (unnombre)
    ```
    Si esta corriendo con Docker

    ```bash
    docker compose exec backend python manage.py crear_moderador --email (unemail) --nombre (unnombre)
    ```

    el moderador entra con su usuario y contraseña a

    http://localhost:4200/moderacion

    aqui mismo puede ver los reportes tanto de publicaciones como de chat y tomar acciones sobre ellos como

    * Ignorar el reporte
    * Advertir al usuario reportado
    * Bloquear al usuario reportado
    * Sancionar al que reporto, esto ocurre si el usuario reporta desmedidamente y genera 3 strikes a la tercera se le bloquea las herramientas de reporte por un tiempo asignado por el mod.

    Ya existen 3 usuarios genericos

    * Adoptante: adoptante1@mail.com clave 123456
    * Rescatista: rescatist1@mail.com clave 123456
    * Moderador: mod1@adoptme.com clave 123456