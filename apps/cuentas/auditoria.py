"""Registro de auditoría de los eventos de seguridad de las cuentas.

Registra los inicios y cierres de sesión, los intentos fallidos, los cambios de contraseña y
de correo, y los cambios en la autenticación de dos factores. Cada registro identifica a la
persona por la clave primaria de su usuario y nunca incluye el correo ni las credenciales;
la dirección IP es la misma que usan los límites de intentos de django-allauth, de modo que
respeta los ajustes de proxies de confianza.

Se implementa con señales porque son el punto de extensión que ofrecen Django y
django-allauth para estos eventos. Los receptores se conectan en ``CuentasConfig.ready``.
"""

import logging

from allauth.account import signals as senales_cuentas
from allauth.account.adapter import get_adapter
from allauth.mfa import signals as senales_doble_factor
from django.contrib.auth import signals as senales_autenticacion
from django.core.exceptions import PermissionDenied
from django.dispatch import receiver
from django.http import HttpRequest

logger = logging.getLogger(__name__)

IP_DESCONOCIDA = "desconocida"


def _obtener_ip(request: HttpRequest | None) -> str:
    """Devuelve la dirección IP del cliente, o ``IP_DESCONOCIDA`` si no puede determinarse."""
    if request is None:
        return IP_DESCONOCIDA
    try:
        return get_adapter(request).get_client_ip(request)
    except PermissionDenied:
        # django-allauth la rechaza cuando los encabezados del proxy no coinciden con la
        # configuración; el registro de auditoría no debe interrumpir la petición.
        return IP_DESCONOCIDA


@receiver(senales_autenticacion.user_logged_in)
def registrar_inicio_sesion(sender, request, user, **kwargs) -> None:
    logger.info("Inicio de sesión del usuario %s desde %s", user.pk, _obtener_ip(request))


@receiver(senales_autenticacion.user_logged_out)
def registrar_cierre_sesion(sender, request, user, **kwargs) -> None:
    if user is not None:
        logger.info("Cierre de sesión del usuario %s desde %s", user.pk, _obtener_ip(request))


@receiver(senales_autenticacion.user_login_failed)
def registrar_inicio_sesion_fallido(sender, credentials, request=None, **kwargs) -> None:
    # Las credenciales no se registran: incluyen el correo y, en ocasiones, una contraseña
    # escrita por error en el campo del correo.
    logger.warning("Intento de inicio de sesión fallido desde %s", _obtener_ip(request))


@receiver(senales_doble_factor.authentication_failed)
def registrar_codigo_rechazado(sender, request, user, **kwargs) -> None:
    logger.warning(
        "Código de verificación rechazado para el usuario %s desde %s",
        user.pk,
        _obtener_ip(request),
    )


@receiver(senales_cuentas.password_changed)
def registrar_cambio_contrasena(sender, request, user, **kwargs) -> None:
    logger.info("Cambio de contraseña del usuario %s desde %s", user.pk, _obtener_ip(request))


@receiver(senales_cuentas.password_reset)
def registrar_restablecimiento_contrasena(sender, request, user, **kwargs) -> None:
    logger.info(
        "Restablecimiento de contraseña del usuario %s desde %s",
        user.pk,
        _obtener_ip(request),
    )


@receiver(senales_cuentas.email_changed)
def registrar_cambio_correo(sender, request, user, **kwargs) -> None:
    logger.info("Cambio de correo del usuario %s desde %s", user.pk, _obtener_ip(request))


@receiver(senales_doble_factor.authenticator_added)
def registrar_autenticador_agregado(sender, request, user, authenticator, **kwargs) -> None:
    logger.info(
        "Autenticador %s activado por el usuario %s desde %s",
        authenticator.type,
        user.pk,
        _obtener_ip(request),
    )


@receiver(senales_doble_factor.authenticator_removed)
def registrar_autenticador_eliminado(sender, request, user, authenticator, **kwargs) -> None:
    logger.warning(
        "Autenticador %s eliminado por el usuario %s desde %s",
        authenticator.type,
        user.pk,
        _obtener_ip(request),
    )


@receiver(senales_doble_factor.authenticator_reset)
def registrar_autenticador_regenerado(sender, request, user, authenticator, **kwargs) -> None:
    logger.info(
        "Autenticador %s regenerado por el usuario %s desde %s",
        authenticator.type,
        user.pk,
        _obtener_ip(request),
    )
