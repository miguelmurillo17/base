"""Utilidades comunes de las pruebas de cuentas.

Las funciones de ``allauth.mfa.*.internal`` no son API pública de django-allauth: se
concentran aquí para que un cambio de versión solo obligue a revisar este módulo.

Las pruebas fijan los ajustes de cuentas con ``ajustes_predeterminados`` para no depender
del archivo .env de quien las ejecuta. Las rutas de la autenticación de dos factores se
registran al cargar el proyecto, así que las pruebas necesitan
``CUENTAS_DOBLE_FACTOR_ACTIVO=true``, su valor por defecto.
"""

from collections.abc import Iterator
from contextlib import contextmanager
from unittest import mock

from allauth.account.models import EmailAddress
from allauth.mfa import app_settings as ajustes_doble_factor
from allauth.mfa.recovery_codes.internal.auth import RecoveryCodes
from allauth.mfa.totp.internal.auth import (
    TOTP,
    format_hotp_value,
    generate_totp_secret,
    hotp_value,
)
from django.contrib.auth import get_user_model
from django.contrib.auth.base_user import AbstractBaseUser
from django.http import HttpResponse
from django.test import Client, override_settings
from django.urls import reverse

CORREO = "ana@example.com"
CONTRASENA = "Clave-de-prueba-2026"
# Instante fijo para los códigos TOTP, de modo que no dependan del reloj de la máquina.
INSTANTE = 1_800_000_000

ajustes_predeterminados = override_settings(
    CUENTAS_REGISTRO_ABIERTO=False,
    ACCOUNT_EMAIL_VERIFICATION="mandatory",
    CUENTAS_DOBLE_FACTOR_ACTIVO=True,
    CUENTAS_ADMINISTRACION_EXIGE_DOBLE_FACTOR=True,
    MFA_SUPPORTED_TYPES=["totp", "recovery_codes"],
    ALLAUTH_TRUSTED_PROXY_COUNT=0,
    ALLAUTH_TRUSTED_CLIENT_IP_HEADER=None,
)


def crear_usuario(
    correo: str = CORREO,
    verificado: bool = True,
    **campos: object,
) -> AbstractBaseUser:
    """Crea un usuario con su dirección registrada en django-allauth."""
    usuario = get_user_model().objects.create_user(correo, CONTRASENA, **campos)
    EmailAddress.objects.create(
        user=usuario,
        email=usuario.correo,
        verified=verificado,
        primary=True,
    )
    return usuario


def activar_doble_factor(usuario: AbstractBaseUser) -> tuple[str, list[str]]:
    """Activa TOTP y códigos de recuperación sin pasar por las vistas.

    Devuelve el secreto TOTP y los códigos de recuperación.
    """
    secreto = generate_totp_secret()
    TOTP.activate(usuario, secreto)
    codigos = RecoveryCodes.activate(usuario).generate_codes()
    return secreto, codigos


def generar_codigo_totp(secreto: str, instante: int = INSTANTE) -> str:
    """Devuelve el código TOTP válido para ``secreto`` en ``instante``."""
    periodo = instante // ajustes_doble_factor.TOTP_PERIOD
    return format_hotp_value(hotp_value(secreto, periodo))


@contextmanager
def fijar_reloj_totp(instante: int = INSTANTE) -> Iterator[None]:
    """Fija el reloj con el que django-allauth valida los códigos TOTP."""
    with mock.patch("allauth.mfa.totp.internal.auth.time") as reloj:
        reloj.time.return_value = instante
        yield


def iniciar_sesion(
    cliente: Client,
    correo: str = CORREO,
    contrasena: str = CONTRASENA,
    siguiente: str | None = None,
    **encabezados: str,
) -> HttpResponse:
    """Envía el formulario de inicio de sesión de django-allauth."""
    url = reverse("account_login")
    if siguiente:
        url += f"?next={siguiente}"
    return cliente.post(url, {"login": correo, "password": contrasena}, **encabezados)


def iniciar_sesion_con_doble_factor(
    cliente: Client,
    secreto: str,
    correo: str = CORREO,
) -> HttpResponse:
    """Inicia sesión con contraseña y código TOTP, con el reloj fijado."""
    with fijar_reloj_totp():
        iniciar_sesion(cliente, correo=correo)
        return cliente.post(reverse("mfa_authenticate"), {"code": generar_codigo_totp(secreto)})


def tiene_sesion_iniciada(cliente: Client) -> bool:
    """Indica si el cliente tiene una sesión iniciada."""
    return "_auth_user_id" in cliente.session
