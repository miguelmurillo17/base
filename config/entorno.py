"""Lectura de variables de entorno para la configuración de Django.

Una variable definida con un valor vacío se trata igual que una variable no definida.
Si falta una variable obligatoria, la configuración se considera incompleta y se lanza
``ImproperlyConfigured`` con el nombre de la variable.
"""

import os
from typing import Any

from django.core.exceptions import ImproperlyConfigured

_OBLIGATORIA = object()
_VALORES_VERDADEROS = {"1", "true", "yes", "on"}
_VALORES_FALSOS = {"0", "false", "no", "off"}


def entorno(nombre: str, por_defecto: Any = _OBLIGATORIA) -> Any:
    """Devuelve el valor de la variable ``nombre`` o ``por_defecto`` si no está definida."""
    valor = os.environ.get(nombre, "")
    if valor == "":
        if por_defecto is _OBLIGATORIA:
            raise ImproperlyConfigured(f"Falta la variable de entorno {nombre}. Ver .env.example.")
        return por_defecto
    return valor


def entorno_booleano(nombre: str, por_defecto: Any = _OBLIGATORIA) -> bool:
    valor = entorno(nombre, por_defecto)
    if isinstance(valor, bool):
        return valor
    normalizado = valor.strip().lower()
    if normalizado in _VALORES_VERDADEROS:
        return True
    if normalizado in _VALORES_FALSOS:
        return False
    raise ImproperlyConfigured(
        f"La variable de entorno {nombre} debe ser booleana (true o false); se recibió {valor!r}."
    )


def entorno_entero(nombre: str, por_defecto: Any = _OBLIGATORIA) -> int:
    valor = entorno(nombre, por_defecto)
    if isinstance(valor, int):
        return valor
    try:
        return int(valor)
    except ValueError:
        raise ImproperlyConfigured(
            f"La variable de entorno {nombre} debe ser un número entero; se recibió {valor!r}."
        ) from None


def entorno_opcion(nombre: str, opciones: tuple[str, ...], por_defecto: Any = _OBLIGATORIA) -> str:
    """Devuelve la variable ``nombre`` si su valor es una de ``opciones``."""
    valor = entorno(nombre, por_defecto)
    if valor not in opciones:
        raise ImproperlyConfigured(
            f"La variable de entorno {nombre} debe ser una de: {', '.join(opciones)}; "
            f"se recibió {valor!r}."
        )
    return valor


def entorno_lista(nombre: str, por_defecto: Any = _OBLIGATORIA) -> list[str]:
    """Devuelve la variable ``nombre`` como lista de valores separados por comas."""
    valor = entorno(nombre, por_defecto)
    if isinstance(valor, list):
        return valor
    return [elemento.strip() for elemento in valor.split(",") if elemento.strip()]
