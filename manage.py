#!/usr/bin/env python
"""Utilidad de línea de comandos de Django.

Usa la configuración de desarrollo salvo que DJANGO_SETTINGS_MODULE indique otra. En el
servidor de producción se define DJANGO_SETTINGS_MODULE=config.settings.prod.
"""

import os
import sys


def principal():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as error:
        raise ImportError(
            "No se pudo importar Django. Verificar que el entorno virtual del proyecto "
            "esté activado y que las dependencias estén instaladas."
        ) from error
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    principal()
