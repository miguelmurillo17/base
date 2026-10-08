"""Revisa un commit antes de registrarlo, según las reglas de autoría y redacción.

Lo ejecutan los hooks de Git de ``.githooks/`` y también puede ejecutarse a mano. Rechaza:

- atribuciones a herramientas de IA: trailers ``Co-authored-by`` de un asistente, líneas
  del tipo "Generated with", enlaces a sesiones de trabajo con la herramienta, y autores,
  committers o ramas con el nombre de una herramienta;
- emojis y símbolos que se usan como íconos (marcas de verificación, cruces, estrellas,
  flechas, figuras);
- una primera línea del mensaje de más de 72 caracteres;
- archivos de Python preparados que no pasan ``ruff check`` o ``ruff format --check``.

En los archivos solo se revisan las líneas agregadas, para que un cambio no se rechace
por contenido que ya estaba en el repositorio. Los documentos que describen las reglas de
atribución, y este script con sus pruebas, citan los textos prohibidos como ejemplo; en
ellos solo se revisan los símbolos.

Uso, con el intérprete del entorno virtual:

    python scripts/revisar_commit.py mensaje <archivo>   (hook commit-msg)
    python scripts/revisar_commit.py cambios             (hook pre-commit)
    python scripts/revisar_commit.py archivos [ruta ...] (archivos completos; sin rutas,
                                                          todos los versionados)
"""

import argparse
import importlib.util
import re
import subprocess
import sys
from collections.abc import Iterable
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
LARGO_MAXIMO_PRIMERA_LINEA = 72
# Git elimina del mensaje todo lo que sigue a esta línea en "git commit --verbose".
LINEA_DE_CORTE = "# ------------------------ >8 ------------------------"

ARCHIVOS_QUE_CITAN_ATRIBUCIONES = frozenset(
    {
        "CLAUDE.md",
        "docs/lineamientos/autoria-y-redaccion.md",
        "scripts/revisar_commit.py",
        "scripts/tests.py",
    }
)

# Bloques de Unicode de emojis, pictogramas y símbolos que suelen usarse como íconos. Los
# signos de la escritura en español (letras acentuadas, ñ, ¿, ¡, comillas, rayas) están
# fuera de estos rangos.
_RANGOS_SIMBOLOS = (
    (0x2190, 0x21FF),  # Flechas
    (0x2300, 0x23FF),  # Símbolos técnicos: relojes, controles de reproducción
    (0x25A0, 0x25FF),  # Figuras geométricas
    (0x2600, 0x27BF),  # Símbolos varios y dingbats: marcas, cruces, estrellas
    (0x2B00, 0x2BFF),  # Símbolos y flechas varios
    (0xFE0F, 0xFE0F),  # Selector que pide mostrar el carácter anterior como emoji
    (0x1F000, 0x1FAFF),  # Emojis, pictogramas y banderas
)

_HERRAMIENTAS = r"claude|anthropic|copilot|chatgpt|openai|gemini|codex"
# "cursor" y las siglas de IA solo cuentan junto a un verbo de autoría: por sí solas son
# palabras comunes en el código y en las ramas.
_HERRAMIENTAS_EN_AUTORIA = rf"{_HERRAMIENTAS}|cursor|ai|ia"
_PATRON_HERRAMIENTA = re.compile(rf"\b({_HERRAMIENTAS})\b", re.IGNORECASE)
_PATRONES_ATRIBUCION = (
    re.compile(
        rf"^\s*co-authored-by:.*\b({_HERRAMIENTAS_EN_AUTORIA})\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(generated|created|written|made|built|assisted)\s+(with|by|using)\b"
        rf".*\b({_HERRAMIENTAS_EN_AUTORIA})\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(generado|creado|escrito|redactado|hecho|asistido)\s+(con|por|usando|mediante)\b"
        rf".*\b({_HERRAMIENTAS_EN_AUTORIA})\b",
        re.IGNORECASE,
    ),
    re.compile(r"\bclaude\.(ai|com)/", re.IGNORECASE),
)
_PATRON_FRAGMENTO = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@")
# Una línea de ruff check --output-format concise: "ruta:línea:columna: código mensaje".
_PATRON_DIAGNOSTICO_RUFF = re.compile(r"^.+:\d+:\d+: ")


def buscar_simbolos(texto: str) -> list[str]:
    """Devuelve los emojis y símbolos de ``texto`` como códigos ``U+XXXX``, sin repetir.

    Se informan como códigos porque la consola en la que corre el hook puede no admitir
    esos caracteres.
    """
    encontrados = []
    for caracter in texto:
        punto = ord(caracter)
        if any(inicio <= punto <= fin for inicio, fin in _RANGOS_SIMBOLOS):
            codigo = f"U+{punto:04X}"
            if codigo not in encontrados:
                encontrados.append(codigo)
    return encontrados


def es_atribucion(linea: str) -> bool:
    """Indica si ``linea`` atribuye el contenido a una herramienta de IA."""
    return any(patron.search(linea) for patron in _PATRONES_ATRIBUCION)


def revisar_lineas(ruta: str, lineas: Iterable[tuple[int, str]]) -> list[str]:
    """Revisa las líneas numeradas de un archivo y devuelve un problema por línea."""
    revisar_atribucion = ruta not in ARCHIVOS_QUE_CITAN_ATRIBUCIONES
    problemas = []
    for numero, linea in lineas:
        simbolos = buscar_simbolos(linea)
        if simbolos:
            problemas.append(
                f"{ruta}:{numero}: emojis o símbolos usados como íconos: {', '.join(simbolos)}"
            )
        if revisar_atribucion and es_atribucion(linea):
            problemas.append(f"{ruta}:{numero}: atribución a una herramienta de IA")
    return problemas


def revisar_mensaje(texto: str) -> list[str]:
    """Revisa un mensaje de commit tal como Git lo entrega al hook ``commit-msg``."""
    lineas = []
    for linea in texto.splitlines():
        if linea.startswith(LINEA_DE_CORTE):
            break
        if not linea.startswith("#"):
            lineas.append(linea)
    contenido = [linea for linea in lineas if linea.strip()]
    if not contenido:
        # Git cancela por sí mismo un commit con el mensaje vacío.
        return []
    problemas = []
    primera_linea = contenido[0]
    if len(primera_linea) > LARGO_MAXIMO_PRIMERA_LINEA:
        problemas.append(
            f"La primera línea tiene {len(primera_linea)} caracteres; el máximo es "
            f"{LARGO_MAXIMO_PRIMERA_LINEA}."
        )
    for numero, linea in enumerate(lineas, start=1):
        simbolos = buscar_simbolos(linea)
        if simbolos:
            problemas.append(
                f"Línea {numero}: emojis o símbolos usados como íconos: {', '.join(simbolos)}"
            )
        if es_atribucion(linea):
            problemas.append(f"Línea {numero}: atribución a una herramienta de IA.")
    return problemas


def revisar_identidad(autor: str, committer: str, rama: str) -> list[str]:
    """Rechaza un autor, un committer o una rama que lleven el nombre de una herramienta."""
    problemas = []
    for papel, identidad in (("autor", autor), ("committer", committer)):
        if _PATRON_HERRAMIENTA.search(identidad) or "[bot]" in identidad.lower():
            problemas.append(
                f"El {papel} del commit es una herramienta o un bot; el commit se registra "
                "con la identidad de Git de la persona que lo hace."
            )
    if _PATRON_HERRAMIENTA.search(rama):
        problemas.append(f"El nombre de la rama {rama} menciona una herramienta de IA.")
    return problemas


def extraer_lineas_agregadas(diff: str) -> dict[str, list[tuple[int, str]]]:
    """Devuelve, por archivo, las líneas agregadas de un diff sin contexto (``-U0``)."""
    agregadas: dict[str, list[tuple[int, str]]] = {}
    ruta = None
    numero = 0
    # Las líneas "+++" y "---" solo son encabezados antes del primer fragmento de cada
    # archivo; dentro de un fragmento son líneas agregadas o eliminadas que empiezan así.
    en_encabezado = False
    for linea in diff.splitlines():
        if linea.startswith("diff --git "):
            en_encabezado = True
            ruta = None
            continue
        if en_encabezado:
            if linea.startswith("+++ "):
                destino = linea[4:]
                ruta = destino[2:] if destino.startswith("b/") else None
                continue
            fragmento = _PATRON_FRAGMENTO.match(linea)
            if fragmento:
                en_encabezado = False
                numero = int(fragmento.group(1))
            continue
        fragmento = _PATRON_FRAGMENTO.match(linea)
        if fragmento:
            numero = int(fragmento.group(1))
            continue
        if ruta is not None and linea.startswith("+"):
            agregadas.setdefault(ruta, []).append((numero, linea[1:]))
            numero += 1
    return agregadas


def revisar_python(ruta: str, contenido: bytes) -> list[str]:
    """Revisa con Ruff el contenido preparado de un archivo de Python.

    Se revisa el contenido del índice y no el de la copia de trabajo, que puede tener
    cambios que no forman parte del commit.
    """
    if importlib.util.find_spec("ruff") is None:
        return ["Ruff no está instalado en el entorno virtual; instala requirements-dev.txt."]
    problemas = []
    revision = _ejecutar_ruff(
        ["check", "--force-exclude", "--output-format", "concise", "--stdin-filename", ruta],
        contenido,
    )
    if revision.returncode == 1:
        salida = revision.stdout.decode("utf-8", errors="replace")
        problemas.extend(
            linea for linea in salida.splitlines() if _PATRON_DIAGNOSTICO_RUFF.match(linea)
        )
    elif revision.returncode != 0:
        problemas.append(f"{ruta}: ruff check falló: {_errores(revision)}")
    formato = _ejecutar_ruff(
        ["format", "--check", "--force-exclude", "--stdin-filename", ruta],
        contenido,
    )
    if formato.returncode == 1:
        problemas.append(f"{ruta}: falta aplicar el formato: python -m ruff format {ruta}")
    elif formato.returncode != 0:
        problemas.append(f"{ruta}: ruff format falló: {_errores(formato)}")
    return problemas


def revisar_cambios() -> list[str]:
    """Revisa la identidad, la rama y los archivos preparados para el commit."""
    problemas = revisar_identidad(
        _git("var", "GIT_AUTHOR_IDENT"),
        _git("var", "GIT_COMMITTER_IDENT"),
        _git("symbolic-ref", "--short", "-q", "HEAD", verificar=False),
    )
    diff = _git(
        "diff",
        "--cached",
        "--no-color",
        "--no-ext-diff",
        "--unified=0",
        "--src-prefix=a/",
        "--dst-prefix=b/",
        "--diff-filter=ACMR",
    )
    for ruta, lineas in extraer_lineas_agregadas(diff).items():
        problemas.extend(revisar_lineas(ruta, lineas))
    preparados = _git("diff", "--cached", "--name-only", "-z", "--diff-filter=ACMR")
    for ruta in preparados.split("\0"):
        if ruta.endswith(".py"):
            contenido = subprocess.run(
                ["git", "show", f":{ruta}"],
                cwd=RAIZ,
                check=True,
                capture_output=True,
            ).stdout
            problemas.extend(revisar_python(ruta, contenido))
    return problemas


def revisar_archivos(rutas: list[str]) -> list[str]:
    """Revisa archivos completos; sin rutas, todos los versionados. Omite los binarios."""
    if not rutas:
        rutas = [ruta for ruta in _git("ls-files", "-z").split("\0") if ruta]
    problemas = []
    for ruta in rutas:
        try:
            texto = (RAIZ / ruta).read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        problemas.extend(revisar_lineas(ruta, enumerate(texto.splitlines(), start=1)))
    return problemas


def _git(*argumentos: str, verificar: bool = True) -> str:
    resultado = subprocess.run(
        ["git", "-c", "core.quotePath=false", *argumentos],
        cwd=RAIZ,
        check=verificar,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
    )
    return resultado.stdout.strip("\n")


def _ejecutar_ruff(argumentos: list[str], contenido: bytes) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "ruff", *argumentos, "-"],
        cwd=RAIZ,
        input=contenido,
        capture_output=True,
    )


def _errores(resultado: subprocess.CompletedProcess) -> str:
    return resultado.stderr.decode("utf-8", errors="replace").strip()


def principal(argumentos: list[str] | None = None) -> int:
    analizador = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    modos = analizador.add_subparsers(dest="modo", required=True)
    modo_mensaje = modos.add_parser("mensaje", help="revisa el archivo del mensaje de commit")
    modo_mensaje.add_argument("archivo", type=Path)
    modos.add_parser("cambios", help="revisa los cambios preparados para el commit")
    modo_archivos = modos.add_parser("archivos", help="revisa archivos completos")
    modo_archivos.add_argument("rutas", nargs="*")
    opciones = analizador.parse_args(argumentos)

    if opciones.modo == "mensaje":
        texto = opciones.archivo.read_text(encoding="utf-8", errors="replace")
        problemas = revisar_mensaje(texto)
    elif opciones.modo == "cambios":
        problemas = revisar_cambios()
    else:
        problemas = revisar_archivos(opciones.rutas)

    if problemas:
        # Cuando Git redirige la salida del hook, Python usaría la codificación regional de
        # Windows en lugar de UTF-8, que es la que espera la terminal de Git.
        sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")
        sys.stderr.write(
            "No se cumplen los lineamientos de docs/lineamientos/:\n"
            + "".join(f"  {problema}\n" for problema in problemas)
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(principal())
