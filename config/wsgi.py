"""Punto de entrada WSGI.

Usa la configuración de producción salvo que DJANGO_SETTINGS_MODULE indique otra.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.prod")

application = get_wsgi_application()
