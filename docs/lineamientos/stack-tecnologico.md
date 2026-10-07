# Stack tecnológico

Base común de los proyectos que parten de esta plantilla.

| Capa | Elección |
|---|---|
| Lenguaje | Python 3.14 |
| Backend | Django 6.1 |
| Base de datos | PostgreSQL 18, en desarrollo y en producción, con psycopg 3 |
| Dependencias | pip y venv, con versiones exactas generadas a partir de `pyproject.toml` |
| Interfaz | Plantillas y formularios de Django; Vue o React para los componentes que requieren interactividad en el cliente |
| Cuentas de usuario | django-allauth: inicio de sesión por correo, registro, verificación del correo y autenticación de dos factores |
| Caché | Caché de base de datos de Django, compartida por todos los procesos |
| Acceso a modelos de IA | LiteLLM |
| Correo | `MAILERS` de Django: consola en desarrollo y SMTP en producción |

## Política de versiones

### Python

Se usa la serie de Python más reciente que cumpla ambas condiciones:

1. Ya cuenta con al menos una versión de corrección posterior a la inicial (x.y.1 o
   posterior).
2. La versión de Django que usa el proyecto la soporta oficialmente.

Así se trabaja con lo más reciente sin absorber los problemas propios de una serie recién
publicada ni depender de un soporte que el framework todavía no declara. Dentro de la serie
elegida se usa siempre la última versión de corrección, que es la única que Django soporta
oficialmente para cada serie de Python.

Vigente a octubre de 2026: **Python 3.14**. Python 3.15 se reevalúa cuando se publique 3.15.1
y Django la incluya entre sus versiones soportadas.

### Django

Se usa la versión de Django más reciente que ya cuente con al menos una versión de
corrección (x.y.1 o posterior), por el mismo motivo que en Python. Las versiones de
corrección y de seguridad se aplican en cuanto se publican. Vigente a octubre de 2026:
**Django 6.1**. Como no es una versión LTS, cada proyecto pasa a la siguiente versión antes
de que termine su soporte de seguridad.

### PostgreSQL

Se usa la versión mayor más reciente que Django y psycopg soporten oficialmente, con su
última versión menor. Vigente a octubre de 2026: **PostgreSQL 18**. En desarrollo corre en
un contenedor definido en `compose.yaml`.

### Proyectos existentes

Las versiones indicadas aquí son las de un proyecto nuevo. En un proyecto existente rigen
las que declara su `pyproject.toml`. Pasar a una nueva serie de Python o a una nueva versión
de Django es un cambio propio, en su propio commit, y no se hace como parte de otra tarea.

## Dependencias

- Las dependencias directas se declaran con rangos de versión en los grupos de
  `pyproject.toml`: `prod` para lo que necesita la aplicación en ejecución y `dev` para las
  herramientas de desarrollo, que incluye a `prod`.
- `requirements.txt` y `requirements-dev.txt` contienen las versiones exactas de todas las
  dependencias, incluidas las transitivas. Se generan con `scripts/fijar_versiones.py` y no
  se editan a mano.
- Para agregar o actualizar una dependencia se edita `pyproject.toml`, se ejecuta el script,
  se reinstala el entorno y se ejecutan las pruebas. Los tres archivos se versionan en el
  mismo commit.
- No se usan `pip lock` ni `pylock.toml` mientras pip los marque como experimentales.

## Interfaz

- Django sirve las pantallas; la captura y validación de datos se hace con formularios de
  Django.
- Vue o React se incorporan solo en los componentes cuya interactividad lo justifique. Cada
  proyecto usa uno de los dos, no ambos. La elección la toma la persona responsable del
  proyecto y se registra en su README; tampoco se agregan otras bibliotecas de interfaz sin
  esa decisión.
