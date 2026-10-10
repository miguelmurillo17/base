# base

Plantilla base para proyectos web con Django. Las convenciones del proyecto están en
[`docs/lineamientos/`](docs/lineamientos/README.md).

De uso libre bajo la licencia [MIT](LICENSE): se puede usar, copiar y modificar, incluso
con fines comerciales, conservando el aviso de copyright. Un proyecto creado a partir de
esta plantilla reemplaza ese archivo por el suyo.

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

5. Activar los hooks de Git del proyecto, una vez por cada clon:

   ```bash
   git config core.hooksPath .githooks
   ```

   Antes de cada commit revisan con Ruff los archivos de Python preparados y rechazan
   atribuciones a herramientas de IA, emojis y símbolos usados como íconos, y primeras
   líneas del mensaje de más de 72 caracteres. Usan el intérprete de `.venv`.

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
| Verificar un cambio por completo | `python scripts/verificar.py` |
| Ejecutar las pruebas | `python manage.py test` |
| Revisar el código con Ruff | `python -m ruff check .` |
| Aplicar el formato de Ruff | `python -m ruff format .` |
| Revisar emojis y atribuciones en todos los archivos versionados | `python scripts/revisar_commit.py archivos` |
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

### Verificación de un cambio

`python scripts/verificar.py` reúne en un solo comando los pasos automatizables de la
verificación que describe
[Flujo de trabajo](docs/lineamientos/flujo-de-trabajo.md), en este orden:

1. `python -m ruff check .`
2. `python -m ruff format --check .`
3. `python manage.py test`
4. `python manage.py check`
5. `python manage.py makemigrations --check --dry-run`
6. `python manage.py check --deploy --settings=config.settings.prod --fail-level WARNING`
7. `python scripts/revisar_commit.py archivos`

Se detiene en el primer paso que falla, lo nombra y devuelve su código de salida, de modo
que sirve igual en la consola y como único paso de revisión en un servidor.

El paso 6 exige las variables obligatorias de producción, que en desarrollo quedan vacías.
El script las define con valores de ejemplo solo en el entorno de ese subproceso, así que
no quedan definidas en la consola ni hay que borrarlas después.

Los dos pasos de Ruff recorren el árbol de trabajo, incluidos los archivos sin versionar que
no estén ignorados, salvo lo que excluye `pyproject.toml`. El paso 7 recorre, en cambio, los
archivos que Git ya conoce, con el contenido que tienen en el árbol de trabajo: un archivo
nuevo entra en cuanto se agrega con `git add`, y antes de eso lo revisa el hook `pre-commit`
al preparar el commit.

La lista de revisión de [Diseño de interfaz](docs/lineamientos/diseno-de-interfaz.md) y la
lectura de los textos nuevos no se automatizan y se hacen aparte.

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
scripts/              Verificación de un cambio, revisión de commits y fijado de versiones
.githooks/            Hooks de Git que ejecutan scripts/revisar_commit.py
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
