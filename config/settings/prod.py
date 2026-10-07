"""Configuración para producción.

Supone que el sitio se sirve solo por HTTPS. Las variables de entorno que usa, además
de las comunes, están descritas en .env.example.
"""

from config.entorno import entorno, entorno_booleano, entorno_entero, entorno_lista

from .base import *  # noqa: F403

DEBUG = False

ALLOWED_HOSTS = entorno_lista("DJANGO_ALLOWED_HOSTS")
CSRF_TRUSTED_ORIGINS = entorno_lista("DJANGO_CSRF_TRUSTED_ORIGINS", por_defecto=[])

SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Se empieza con un valor bajo y se sube a 31536000 (un año) una vez confirmado que
# todo el dominio, incluidos los subdominios, funciona por HTTPS.
SECURE_HSTS_SECONDS = entorno_entero("DJANGO_SECURE_HSTS_SECONDS", por_defecto=3600)
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
# Entrar a la lista de precarga HSTS de los navegadores es una decisión de cada dominio;
# mientras no se tome, se silencia el aviso correspondiente.
SILENCED_SYSTEM_CHECKS = ["security.W021"]

# Solo se activa detrás de un proxy inverso que termina HTTPS y que reemplaza siempre el
# encabezado X-Forwarded-Proto enviado por el cliente.
if entorno_booleano("DJANGO_TRUST_X_FORWARDED_PROTO", por_defecto=False):
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Conexiones persistentes a la base de datos. Con ASGI se deja DJANGO_CONN_MAX_AGE en 0.
DATABASES["default"]["CONN_MAX_AGE"] = entorno_entero(  # noqa: F405
    "DJANGO_CONN_MAX_AGE",
    por_defecto=60,
)
DATABASES["default"]["CONN_HEALTH_CHECKS"] = True  # noqa: F405

# Los enlaces de los correos de django-allauth se generan con HTTPS.
ACCOUNT_DEFAULT_HTTP_PROTOCOL = "https"

DEFAULT_FROM_EMAIL = entorno("DJANGO_DEFAULT_FROM_EMAIL")
SERVER_EMAIL = entorno("DJANGO_SERVER_EMAIL", por_defecto=DEFAULT_FROM_EMAIL)
ADMINS = entorno_lista("DJANGO_ADMINS", por_defecto=[])
MAILERS = {
    "default": {
        "BACKEND": "django.core.mail.backends.smtp.EmailBackend",
        "OPTIONS": {
            "host": entorno("DJANGO_SMTP_HOST"),
            "port": entorno_entero("DJANGO_SMTP_PORT", por_defecto=587),
            "username": entorno("DJANGO_SMTP_USERNAME", por_defecto=""),
            "password": entorno("DJANGO_SMTP_PASSWORD", por_defecto=""),
            "use_tls": entorno_booleano("DJANGO_SMTP_USE_TLS", por_defecto=True),
            "timeout": 10,
        },
    },
}
