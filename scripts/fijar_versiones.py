"""Regenera requirements.txt y requirements-dev.txt a partir de pyproject.toml.

Cada archivo es la salida de ``pip freeze`` de un entorno virtual temporal en el que
solo se instaló el grupo de dependencias correspondiente. Se escribe en UTF-8 con fin
de línea LF para que el resultado no dependa de la consola ni del sistema operativo.

Las dependencias que otro paquete exige solo en algunos sistemas operativos se declaran
explícitamente en pyproject.toml; de lo contrario, el resultado depende del sistema en el
que se ejecuta el script.

Uso, desde cualquier directorio y con el intérprete de la serie del proyecto:

    py -3.14 scripts/fijar_versiones.py        (Windows)
    python3.14 scripts/fijar_versiones.py      (Linux y macOS)
"""

import shutil
import subprocess
import sys
import venv
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
VENV_TEMPORAL = RAIZ / ".venv-versiones"
SERIE_PYTHON = (3, 14)
ENCABEZADO = (
    "# Archivo generado por scripts/fijar_versiones.py a partir de pyproject.toml. "
    "No se edita a mano.\n"
)


def python_del_venv() -> Path:
    if sys.platform == "win32":
        return VENV_TEMPORAL / "Scripts" / "python.exe"
    return VENV_TEMPORAL / "bin" / "python"


def congelar_grupo(grupo: str, salida: str, *argumentos_pip: str) -> None:
    # upgrade_deps actualiza pip: --refresh-package necesita pip 26.2 o posterior.
    venv.EnvBuilder(clear=True, with_pip=True, upgrade_deps=True).create(VENV_TEMPORAL)
    python = str(python_del_venv())
    # --refresh-package evita que pip use respuestas del índice guardadas en caché y
    # omita una versión de seguridad recién publicada.
    subprocess.run(
        [
            python,
            "-m",
            "pip",
            "install",
            "--refresh-package",
            ":all:",
            *argumentos_pip,
            "--group",
            grupo,
        ],
        cwd=RAIZ,
        check=True,
    )
    congelado = subprocess.run(
        [python, "-m", "pip", "freeze"],
        cwd=RAIZ,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    lineas = [linea.strip() for linea in congelado.splitlines() if linea.strip()]
    contenido = ENCABEZADO + "\n".join(lineas) + "\n"
    (RAIZ / salida).write_text(contenido, encoding="utf-8", newline="\n")


def principal() -> None:
    if sys.version_info[:2] != SERIE_PYTHON:
        sys.exit("Este script debe ejecutarse con Python 3.14.")
    try:
        # Solo paquetes binarios, igual que la instalación de producción.
        congelar_grupo("prod", "requirements.txt", "--only-binary", ":all:")
        # Las dependencias comunes quedan en las mismas versiones que en requirements.txt.
        congelar_grupo("dev", "requirements-dev.txt", "--constraint", "requirements.txt")
    finally:
        shutil.rmtree(VENV_TEMPORAL, ignore_errors=True)


if __name__ == "__main__":
    principal()
