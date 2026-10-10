# Autoría y redacción

Se aplica a mensajes de commit, descripciones de pull request, comentarios, docstrings,
documentación y cualquier otro texto que quede en el repositorio o en su historial.

## Autoría

La autoría de cada cambio corresponde a la persona que lo registra, con su propia identidad
de Git (`user.name` y `user.email`). Los asistentes de IA no figuran como autores ni dejan
marcas de autoría en commits, pull requests, código o documentación.

No se permiten:

- En commits y pull requests: trailers `Co-authored-by:` que atribuyan coautoría a un
  asistente o modelo de IA (Claude, Copilot, ChatGPT, Gemini u otros), líneas del tipo
  "Generated with ...", "Created with ..." o "Written with the help of ...", ni enlaces a la
  herramienta de IA o a la sesión en la que se produjo el cambio.
- En la identidad de Git: commits cuyo autor o committer sea una herramienta o un bot, y
  ramas, etiquetas o títulos de pull request que mencionen la herramienta (por ejemplo,
  `claude/...`).
- En código y documentación: encabezados, comentarios o docstrings que indiquen que el
  contenido fue generado o asistido por IA.

Quedan fuera de esta regla los archivos que se versionan tal como se producen y que el
proyecto no redacta: los que una herramienta genera y mantiene por sí misma, como las
migraciones de Django o los archivos de bloqueo de dependencias, y el material que llega de
una fuente propia, como el design system de `docs/design_base/`. Las rutas exentas se
declaran en `DIRECTORIOS_QUE_NO_SE_REVISAN` de `scripts/revisar_commit.py` y en
`extend-exclude` de `pyproject.toml`; ampliar esa lista es una decisión del proyecto, no un
atajo para evitar una revisión.

Si una herramienta agrega estas marcas por defecto, se desactivan en su configuración y, en
cualquier caso, se eliminan antes de hacer commit. En Claude Code, el archivo
`.claude/settings.json` del proyecto las desactiva en commits y pull requests.

Los hooks de Git de `.githooks/` rechazan los commits cuyo mensaje, líneas agregadas,
autor, committer o rama contienen estas marcas, así como emojis y símbolos usados como
íconos. Se activan en cada clon con `git config core.hooksPath .githooks`.

## Redacción

Todo texto debe entenderse por sí mismo, sin conocer la conversación, el ticket o la sesión
de trabajo de la que salió, y redactarse como texto definitivo: preciso, completo y revisado.

- Ortografía, acentuación y puntuación correctas en todo texto, incluidos mensajes de commit
  y comentarios.
- Todo en español: identificadores de código, comentarios, docstrings, documentación,
  mensajes de commit y descripciones de pull request. Un mismo concepto se nombra siempre
  igual.
- Los identificadores (variables, funciones, clases, módulos, campos de modelos,
  restricciones) usan solo caracteres ASCII: sin ñ ni tildes, por ejemplo `contrasena`,
  `anio`, `direccion`.
- Se conservan en inglés los nombres que impone Django, Python o una biblioteca: métodos y
  atributos que el framework espera (`save`, `clean`, `Meta`, `objects`, `is_active`,
  `is_staff`, `create_user`, `get_full_name`), los nombres de settings, el prefijo `test_`
  de las pruebas y los nombres de directorio convencionales (`templates`, `static`,
  `migrations`). También las convenciones generalizadas de Django: `BASE_DIR`, los sufijos
  `Config` y `Admin` de las clases de configuración de aplicación y de administración, los
  nombres de entorno `dev` y `prod`, y las variables de entorno con prefijo `DJANGO_` o
  `POSTGRES_`.
- Tono técnico y neutro. Sin entusiasmo artificial ("¡Listo!", "potente", "increíble"), sin
  signos de exclamación y sin emojis ni símbolos decorativos.
- Sin referencias al proceso: se evitan expresiones como "como se pidió", "según lo
  indicado", "ahora sí", "versión corregida" o "mejorado". El texto describe el estado
  actual, no cómo se llegó a él.
- Los comentarios explican el porqué cuando no es evidente. No narran lo que el código ya
  dice ni llevan un registro de cambios; para eso está el historial de Git.
- Sin código comentado, notas personales ni `TODO` sin contexto. Un `TODO` indica qué falta
  y por qué no se resolvió en ese momento.

## Mensajes de commit

- La primera línea empieza con un verbo en infinitivo y resume el cambio en 72 caracteres o
  menos.
- El cuerpo, cuando hace falta, explica el motivo del cambio y sus consecuencias, no el
  detalle línea por línea que ya muestra el diff.
- Un commit agrupa un cambio coherente. Los cambios no relacionados van en commits separados.
