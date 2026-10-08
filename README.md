# base

Plantilla base para proyectos web con Django. Las convenciones del proyecto están en
[`docs/lineamientos/`](docs/lineamientos/README.md).

## Requisitos

- Python 3.14, en su última versión de corrección
- Docker con Docker Compose, para PostgreSQL en desarrollo
- GNU gettext, solo para compilar las traducciones propias. Git para Windows lo incluye
  en su consola Bash; en Linux es el paquete `gettext`.

## Puesta en marcha

1. Crear el archivo de variables de entorno a partir del ejemplo y reemplazar los valores
   de `DJANGO_SECRET_KEY` y `POSTGRES_PASSWORD`. Los comandos para generarlos están en los
   comentarios de `.env.example`.

   ```bash
   cp .env.example .env
   ```

2. Iniciar PostgreSQL:

   ```bash
   docker compose up -d --wait
   ```

3. Crear el entorno virtual e instalar las dependencias.

   Windows (PowerShell). Si PowerShell no permite ejecutar scripts, la primera línea lo
   habilita solo para la sesión actual:

   ```powershell
   Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
   py -3.14 -m venv .venv
   .venv\Scripts\Activate.ps1
   python -m pip install -r requirements-dev.txt
   ```

   Linux y macOS:

   ```bash
   python3.14 -m venv .venv
   source .venv/bin/activate
   python -m pip install -r requirements-dev.txt
   ```

4. Aplicar las migraciones, crear la tabla de la caché compartida y un superusuario, e
   iniciar el servidor de desarrollo:

   ```bash
   python manage.py migrate
   python manage.py createcachetable
   python manage.py createsuperuser
   python manage.py runserver
   ```

   El sitio queda en `http://127.0.0.1:8000/` y el de administración en
   `http://127.0.0.1:8000/admin/`. En el primer inicio de sesión del superusuario se pide
   confirmar su correo con el enlace que el servidor de desarrollo muestra en la consola.
   Para entrar al sitio de administración se configura antes la autenticación de dos
   factores.

## Cuentas de usuario

El inicio de sesión usa el correo electrónico y django-allauth. Cada función se activa con
una variable de entorno, descrita en `.env.example`; el valor por defecto es el más
seguro.

| Variable | Por defecto | Efecto |
|---|---|---|
| `CUENTAS_REGISTRO_ABIERTO` | `false` | Permite crear cuentas desde la página de registro |
| `CUENTAS_VERIFICACION_CORREO` | `obligatoria` | Exige confirmar el correo para iniciar sesión (`obligatoria`, `opcional` o `ninguna`) |
| `CUENTAS_DOBLE_FACTOR_ACTIVO` | `true` | Permite activar la autenticación de dos factores |
| `CUENTAS_ADMINISTRACION_EXIGE_DOBLE_FACTOR` | `true` | Exige la autenticación de dos factores para entrar al sitio de administración. Requiere `CUENTAS_DOBLE_FACTOR_ACTIVO=true` |
| `CUENTAS_LLAVES_ACCESO_ACTIVAS` | `false` | Permite usar llaves de acceso (passkeys). Requiere `CUENTAS_DOBLE_FACTOR_ACTIVO=true` |

Con el registro abierto, solo la verificación `obligatoria` evita que la página de registro
revele qué direcciones ya tienen cuenta.

El sitio de administración no tiene un inicio de sesión propio: redirige al del sitio, que
aplica la verificación del correo, los límites de intentos y el segundo factor. El cambio
de contraseña también pasa por las pantallas de la cuenta.

Toda página exige sesión iniciada salvo las de inicio de sesión, registro y recuperación de
la cuenta. Los inicios y cierres de sesión, los intentos fallidos, los cambios de
contraseña y de correo y los cambios en la autenticación de dos factores quedan en el
registro `apps.cuentas.auditoria`, con la clave del usuario y la dirección IP, sin el
correo ni las credenciales.

Con la autenticación de dos factores activa, django-allauth no permite cambiar el correo
mientras la verificación se haga por enlace. Para cambiarlo se desactiva la aplicación de
autenticación, se cambia y verifica el correo, y se vuelve a activar; el personal no puede
entrar al sitio de administración mientras tanto.

## Comandos habituales

Con el entorno virtual activado:

| Tarea | Comando |
|---|---|
| Ejecutar las pruebas | `python manage.py test` |
| Revisar el código con Ruff | `python -m ruff check .` |
| Aplicar el formato de Ruff | `python -m ruff format .` |
| Regenerar las versiones exactas de las dependencias | `python scripts/fijar_versiones.py` |
| Compilar las traducciones propias de `locale/` | `python manage.py compilemessages --locale es_MX --ignore ".venv*"` |
| Detener PostgreSQL | `docker compose stop` |
| Eliminar PostgreSQL junto con sus datos | `docker compose down -v` |

Las pruebas necesitan PostgreSQL en ejecución y `CUENTAS_DOBLE_FACTOR_ACTIVO=true` (su valor
por defecto), porque las rutas de la autenticación de dos factores se registran al cargar
el proyecto.

En Windows, `msgfmt` está en la consola Bash de Git: desde ahí, las traducciones se
compilan con el intérprete del entorno virtual,
`.venv/Scripts/python.exe manage.py compilemessages --locale es_MX --ignore ".venv*"`.

### Revisión de la configuración de producción

La revisión exige las variables obligatorias de producción, que en desarrollo quedan
vacías, así que se definen solo para el comando.

Linux y macOS:

```bash
DJANGO_ALLOWED_HOSTS=www.example.com DJANGO_SMTP_HOST=smtp.example.com DJANGO_DEFAULT_FROM_EMAIL=no-responder@example.com python manage.py check --deploy --settings=config.settings.prod --fail-level WARNING
```

Windows (PowerShell):

```powershell
$env:DJANGO_ALLOWED_HOSTS = "www.example.com"; $env:DJANGO_SMTP_HOST = "smtp.example.com"; $env:DJANGO_DEFAULT_FROM_EMAIL = "no-responder@example.com"
python manage.py check --deploy --settings=config.settings.prod --fail-level WARNING
Remove-Item Env:DJANGO_ALLOWED_HOSTS, Env:DJANGO_SMTP_HOST, Env:DJANGO_DEFAULT_FROM_EMAIL
```

## Estructura

```text
apps/                 Aplicaciones de Django del proyecto
  cuentas/            Modelo de usuario, django-allauth y registro de auditoría
config/               Configuración del proyecto
  settings/           base.py (común), dev.py (desarrollo), prod.py (producción)
  entorno.py          Lectura de variables de entorno
  sitio_administracion.py  Sitio de administración con acceso por django-allauth
docs/lineamientos/    Convenciones del proyecto
locale/               Traducciones propias, con prioridad sobre las de las bibliotecas
static/               Hoja de estilos base
templates/            Plantilla base, formularios, páginas de error y pantallas de django-allauth
scripts/              Utilidades de mantenimiento
compose.yaml          PostgreSQL para desarrollo
pyproject.toml        Dependencias directas y metadatos
requirements*.txt     Versiones exactas, generadas por scripts/fijar_versiones.py
```

## Producción

- Se define `DJANGO_SETTINGS_MODULE=config.settings.prod` y las variables de entorno
  descritas en `.env.example`. Los puntos de entrada WSGI y ASGI usan esa configuración
  por defecto.
- Las dependencias se instalan solo desde el archivo de versiones exactas:

  ```bash
  python -m pip install --no-deps --only-binary :all: -r requirements.txt
  python -m pip check
  ```

- En cada despliegue se ejecutan `python manage.py migrate`,
  `python manage.py createcachetable` y `python manage.py collectstatic --noinput`.
- Todos los procesos de la aplicación usan la caché de la base de datos: los límites de
  intentos de inicio de sesión dependen de que sea compartida.
