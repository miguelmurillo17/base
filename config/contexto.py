"""Procesadores de contexto del proyecto."""

from django.conf import settings
from django.http import HttpRequest


def exponer_datos_sitio(request: HttpRequest) -> dict[str, object]:
    """Expone a las plantillas el nombre del sitio y las funciones de cuenta activas."""
    return {
        "nombre_sitio": settings.NOMBRE_SITIO,
        "registro_abierto": settings.CUENTAS_REGISTRO_ABIERTO,
        "doble_factor_activo": settings.CUENTAS_DOBLE_FACTOR_ACTIVO,
    }
