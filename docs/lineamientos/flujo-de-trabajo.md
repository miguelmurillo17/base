# Flujo de trabajo

Cómo se prepara, se acota y se verifica un cambio. Se aplica a quien desarrolla y a los
agentes de IA.

## Antes de cambiar el código

- Se leen los lineamientos que aplican al cambio y el código cercano al que se va a
  modificar. El código nuevo sigue los patrones que ya existen en el proyecto.
- Se busca si el proyecto, Django o una dependencia instalada ya resuelve lo que se necesita,
  antes de escribirlo.
- Si la tarea requiere una decisión que los lineamientos no resuelven (agregar una
  dependencia, elegir entre dos diseños con consecuencias distintas, cambiar una política),
  se consulta a la persona responsable en lugar de asumirla.

## Alcance de un cambio

- Un cambio resuelve una sola cosa. No incluye reformateos, cambios de nombre ni
  reorganizaciones de código que no son necesarios para resolverla.
- Los problemas que se detectan fuera del alcance se informan para atenderlos por separado,
  en lugar de corregirlos dentro del mismo cambio.
- Requieren una decisión explícita y van en su propio commit:
  - agregar, quitar o cambiar de serie una dependencia;
  - cambiar de versión de Python, Django o PostgreSQL;
  - ampliar la política de seguridad de contenido o relajar otro ajuste de seguridad;
  - cambiar un lineamiento.

## Ramas y commits

- Cada cambio se desarrolla en una rama que parte de `main` y se integra mediante un pull
  request.
- Las ramas se nombran con el prefijo `feature/` y una descripción breve en español, en
  minúsculas, sin tildes y separada por guiones: `feature/registro-de-facturas`.
- Los mensajes de commit y las descripciones de pull request siguen
  [Autoría y redacción](autoria-y-redaccion.md).
- Un agente de IA no crea commits, ramas remotas ni pull requests si la persona responsable
  no lo indica.

## Documentación que acompaña al cambio

En el mismo cambio se actualiza:

- `.env.example`, si se agrega o cambia una variable de entorno.
- `README.md`, si cambian los requisitos, los comandos, la puesta en marcha o la estructura
  del repositorio.
- `pyproject.toml` y los archivos `requirements*.txt` regenerados, si cambian las
  dependencias.
- `docs/lineamientos/`, si el cambio establece una convención general nueva.

## Verificación antes de terminar

Un cambio se da por terminado cuando, con PostgreSQL en ejecución, se cumple todo lo
siguiente:

1. `python -m ruff check .` y `python -m ruff format --check .` no informan problemas.
2. `python manage.py test` termina sin fallos.
3. `python manage.py check` no informa problemas.
4. `python manage.py makemigrations --check --dry-run` no detecta migraciones pendientes.
5. Si el cambio toca ajustes de seguridad o de producción, la revisión `check --deploy`
   indicada en `CLAUDE.md` termina sin advertencias.
6. Si el cambio incluye pantallas, cumple la lista de revisión de
   [Diseño de interfaz](diseno-de-interfaz.md).
7. Los textos nuevos cumplen [Autoría y redacción](autoria-y-redaccion.md): sin marcas de
   autoría de herramientas, sin emojis y sin referencias al proceso.

Si algún paso no puede ejecutarse, se indica cuál y por qué al entregar el cambio, en lugar
de darlo por verificado.
