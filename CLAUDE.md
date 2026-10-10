# CLAUDE.md

Instrucciones para agentes de IA que trabajan en este repositorio. Las reglas detalladas
están en [`docs/lineamientos/`](docs/lineamientos/README.md); las referencias con `@` de la
sección "Lineamientos" importan esos documentos para que formen parte del contexto de cada
sesión.

## Contexto

Plantilla base para proyectos web con Django. Mientras se trabaje en la plantilla, todo lo
que se agregue debe ser general y reutilizable. Al crear un proyecto a partir de ella, esta
sección se reemplaza por la descripción de ese proyecto; el resto del archivo se conserva.

## Reglas sin excepción

1. **Sin atribución a herramientas de IA.** Ningún commit, pull request, comentario,
   docstring, encabezado de archivo ni documento incluye `Co-authored-by` de un asistente,
   líneas "Generated with ..." ni menciones equivalentes, y ningún commit se crea con la
   identidad de una herramienta. La autoría es de la persona que hace el commit, con su
   propia identidad de Git.
2. **Sin emojis ni símbolos usados como íconos** (marcas de verificación, cruces, estrellas,
   flechas decorativas) en código, interfaz, mensajes de commit, descripciones de pull
   request, documentación ni logs.
3. **Interfaz sobria.** No se usan los recursos visuales genéricos de las interfaces
   generadas automáticamente: píldoras, chips o insignias para resaltar texto o estados,
   degradados decorativos, íconos de adorno y similares.
4. **Textos autocontenidos y definitivos.** Todo lo que se escribe en el repositorio se
   entiende sin conocer la conversación ni el proceso con el que se produjo: sin expresiones
   como "como se pidió" o "según lo acordado", ni explicaciones dirigidas a quien dio la
   instrucción. Se redacta como texto definitivo, con ortografía correcta y tono técnico.
5. **Sin credenciales ni datos privados en el repositorio.** Claves de API, contraseñas,
   tokens y la `SECRET_KEY` de Django se leen de variables de entorno; solo se versiona un
   `.env.example` con valores ficticios. No se versionan `.env`, bases de datos locales ni
   archivos subidos. Los datos de prueba son ficticios, y el código y la documentación no
   incluyen rutas absolutas del equipo ni nombres de usuario del sistema.

## Entorno de trabajo

- Python 3.14 en el entorno virtual `.venv` de la raíz. En Windows, el intérprete del
  sistema se invoca con `py -3.14`.
- Los comandos se ejecutan con el intérprete del entorno virtual, sin depender de que esté
  activado: `.venv/Scripts/python.exe` en Windows y `.venv/bin/python` en Linux y macOS. Los
  ejemplos con `python` suponen ese intérprete.
- PostgreSQL de desarrollo: `docker compose up -d --wait`. Las pruebas lo necesitan.
- Pruebas: `python manage.py test`.
- Verificación completa de un cambio: `python scripts/verificar.py`. Ejecuta en orden Ruff,
  las pruebas, `manage.py check`, la comprobación de migraciones pendientes, la revisión de
  producción `check --deploy` con las variables que ese entorno exige, y la revisión de
  autoría y símbolos de todos los archivos versionados. Se detiene en el primer paso que
  falla y lo nombra.
- Traducciones propias en `locale/es_MX/`: después de editar el `.po` se compila con
  `python manage.py compilemessages --locale es_MX --ignore ".venv*"` (en Windows, desde la
  consola Bash de Git, que incluye `msgfmt`) y se versionan el `.po` y el `.mo`.
- Código: `python -m ruff check .` y `python -m ruff format .`, con la configuración de
  `pyproject.toml`. Los hooks de `.githooks/` (`git config core.hooksPath .githooks`)
  rechazan commits con atribución a herramientas de IA, emojis o archivos que no pasan Ruff.
  Queda fuera el material que se versiona tal como se produce: las migraciones y el design
  system de `docs/design_base/`.
- Dependencias: se editan en `pyproject.toml` y se regeneran las versiones exactas con
  `python scripts/fijar_versiones.py`. `requirements*.txt` no se editan a mano.
- Antes de dar un cambio por terminado se completa la verificación descrita en
  [Flujo de trabajo](docs/lineamientos/flujo-de-trabajo.md). `python scripts/verificar.py`
  cubre sus pasos automatizables; la lista de revisión de interfaz y la lectura de los
  textos nuevos se hacen aparte.

## Lineamientos

- Autoría y redacción: @docs/lineamientos/autoria-y-redaccion.md
- Diseño de interfaz: @docs/lineamientos/diseno-de-interfaz.md
- Stack tecnológico: @docs/lineamientos/stack-tecnologico.md
- Convenciones de código: @docs/lineamientos/convenciones-de-codigo.md
- Arquitectura de Django: @docs/lineamientos/arquitectura-de-django.md
- Modelos y datos: @docs/lineamientos/modelos-y-datos.md
- Pruebas: @docs/lineamientos/pruebas.md
- Seguridad: @docs/lineamientos/seguridad.md
- Flujo de trabajo: @docs/lineamientos/flujo-de-trabajo.md
