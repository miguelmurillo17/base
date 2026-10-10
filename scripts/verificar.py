"""Ejecuta la verificación completa de un cambio antes de darlo por terminado.

Reúne en un solo comando los pasos que describe la sección "Verificación antes de
terminar" de docs/lineamientos/flujo-de-trabajo.md. Los ejecuta en orden y se detiene en
el primero que falla, que queda nombrado junto con su código de salida; ese código es
también el del script, de modo que sirve como único paso de revisión en un flujo de
integración continua.

Necesita PostgreSQL en ejecución, porque las pruebas usan la base de datos.

La revisión de la configuración de producción exige variables de entorno que en
desarrollo quedan vacías. El script las define con valores de ejemplo solo en el entorno
del subproceso, así que no quedan definidas en la consola de quien lo ejecuta ni hay que
borrarlas después.

Uso, con el intérprete del entorno virtual:

    python scripts/verificar.py
"""

import os
import subprocess
import sys
from pathlib import Path
from typing import NamedTuple

RAIZ = Path(__file__).resolve().parent.parent

# Las variables obligatorias de config/settings/prod.py. Los valores solo sirven para que
# la configuración cargue: la revisión no atiende peticiones ni envía correo.
ENTORNO_PRODUCCION = {
    "DJANGO_ALLOWED_HOSTS": "www.example.com",
    "DJANGO_SMTP_HOST": "smtp.example.com",
    "DJANGO_DEFAULT_FROM_EMAIL": "no-responder@example.com",
}


class Paso(NamedTuple):
    """Un paso de la verificación, con los argumentos que recibe el intérprete."""

    nombre: str
    argumentos: list[str]
    variables: dict[str, str] | None = None


PASOS = (
    Paso("Reglas de Ruff", ["-m", "ruff", "check", "."]),
    Paso("Formato de Ruff", ["-m", "ruff", "format", "--check", "."]),
    Paso("Pruebas", ["manage.py", "test"]),
    Paso("Revisión del proyecto", ["manage.py", "check"]),
    Paso("Migraciones pendientes", ["manage.py", "makemigrations", "--check", "--dry-run"]),
    Paso(
        "Revisión de la configuración de producción",
        [
            "manage.py",
            "check",
            "--deploy",
            "--settings=config.settings.prod",
            "--fail-level",
            "WARNING",
        ],
        ENTORNO_PRODUCCION,
    ),
    Paso(
        "Autoría y símbolos en los archivos versionados", ["scripts/revisar_commit.py", "archivos"]
    ),
)


def ejecutar(paso: Paso) -> int:
    """Ejecuta ``paso`` con el intérprete actual y devuelve su código de salida."""
    return subprocess.run(
        [sys.executable, *paso.argumentos],
        cwd=RAIZ,
        env={**os.environ, **(paso.variables or {})},
        check=False,
    ).returncode


def principal() -> int:
    # Cuando la salida se redirige, a un archivo de registro o al informe de un servidor,
    # Python usaría en Windows la codificación regional en lugar de UTF-8, y los nombres
    # de los pasos llevan acentos. Las pruebas sustituyen los flujos por objetos en
    # memoria, que no admiten reconfigure.
    for flujo in (sys.stdout, sys.stderr):
        if hasattr(flujo, "reconfigure"):
            flujo.reconfigure(encoding="utf-8", errors="backslashreplace")

    for numero, paso in enumerate(PASOS, start=1):
        sys.stdout.write(f"[{numero}/{len(PASOS)}] {paso.nombre}\n")
        # La salida del script y la del subproceso van al mismo descriptor sin pasar por
        # el búfer de Python, así que el encabezado debe escribirse antes de lanzarlo.
        sys.stdout.flush()
        codigo = ejecutar(paso)
        if codigo != 0:
            sys.stderr.write(
                f"\nLa verificación se detuvo en el paso {numero} de {len(PASOS)}, "
                f"{paso.nombre}, con código {codigo}.\n"
            )
            return codigo
    sys.stdout.write("\nLa verificación terminó sin problemas.\n")
    return 0


if __name__ == "__main__":
    sys.exit(principal())
