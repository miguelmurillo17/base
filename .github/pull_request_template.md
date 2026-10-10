## Qué resuelve

<!-- El motivo del cambio y sus consecuencias. Se entiende sin leer el diff. -->

## Verificación

`python scripts/verificar.py` cubre los cinco primeros puntos. Los dos últimos se revisan a
mano.

- [ ] Ruff no informa problemas, ni de reglas ni de formato.
- [ ] Las pruebas terminan sin fallos.
- [ ] `manage.py check` no informa problemas.
- [ ] No hay migraciones pendientes.
- [ ] Si el cambio toca ajustes de seguridad o de producción, `check --deploy` termina sin
      advertencias.
- [ ] Si el cambio incluye pantallas, cumplen la lista de revisión de
      `docs/lineamientos/diseno-de-interfaz.md`.
- [ ] Los textos nuevos cumplen `docs/lineamientos/autoria-y-redaccion.md`: sin marcas de
      autoría de herramientas, sin emojis y sin referencias al proceso.

## Documentación que acompaña al cambio

Se marca solo lo que aplica.

- [ ] `.env.example`, por una variable de entorno nueva o cambiada.
- [ ] `README.md`, por un cambio en los requisitos, los comandos, la puesta en marcha o la
      estructura del repositorio.
- [ ] `pyproject.toml` y los `requirements*.txt` regenerados con
      `scripts/fijar_versiones.py`, por un cambio de dependencias.
- [ ] `docs/lineamientos/`, por una convención general nueva.
