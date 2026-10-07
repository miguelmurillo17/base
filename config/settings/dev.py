"""Configuración para desarrollo local."""

from config.entorno import entorno_lista

from .base import *  # noqa: F403

DEBUG = True

# Con DEBUG activo y la lista vacía, Django acepta localhost, 127.0.0.1 y [::1].
ALLOWED_HOSTS = entorno_lista("DJANGO_ALLOWED_HOSTS", por_defecto=[])

# Los correos se muestran en la consola del servidor, con los enlaces completos.
MAILERS = {
    "default": {
        "BACKEND": "config.correo.ServidorCorreoConsola",
    },
}
