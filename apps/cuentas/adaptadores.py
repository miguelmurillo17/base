"""Adaptadores de django-allauth para el modelo de usuario y los ajustes del proyecto.

Leen los ajustes ``CUENTAS_*`` en cada llamada, de modo que el comportamiento sigue a la
configuración vigente.
"""

from allauth.account.adapter import DefaultAccountAdapter
from allauth.mfa.adapter import DefaultMFAAdapter
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils.translation import gettext

from .models import GestorUsuarios


class AdaptadorCuentas(DefaultAccountAdapter):
    def is_open_for_signup(self, request):
        return settings.CUENTAS_REGISTRO_ABIERTO

    def clean_email(self, email):
        # django-allauth solo convierte el correo a minúsculas. Se aplica la misma
        # normalización que al guardar el usuario.
        return GestorUsuarios.normalize_email(super().clean_email(email))

    def confirm_email(self, request, email_address):
        # django-allauth solo busca conflictos entre las direcciones verificadas que
        # registra. Las cuentas creadas con createsuperuser o desde el sitio de
        # administración no tienen ese registro hasta su primer inicio de sesión: sin esta
        # comprobación, otra cuenta podría verificar ese correo como propio.
        otras_cuentas = (
            get_user_model()
            .objects.con_correo(email_address.email)
            .exclude(pk=email_address.user_id)
        )
        if otras_cuentas.exists():
            self.add_message(
                request,
                messages.ERROR,
                "account/messages/email_confirmation_failed.txt",
                {"email": email_address.email},
            )
            return False
        # La verificación guarda varias filas; si una falla, no queda ninguna a medias.
        with transaction.atomic():
            return super().confirm_email(request, email_address)

    def _get_login_attempts_cache_key(self, request, **credentials):
        # django-allauth antepone el dominio de la petición, que sin django.contrib.sites es
        # el encabezado Host tal como lo envía el cliente: cada variante de mayúsculas o de
        # puerto tendría su propio contador de intentos. Es un método interno de
        # django-allauth; las pruebas de PruebasInicioSesion lo vigilan al actualizarlo.
        login = credentials.get("email", credentials.get("username", ""))
        return GestorUsuarios.normalize_email(login)

    def get_http_user_agent(self, request):
        # django-allauth usa el texto fijo en inglés "Unspecified" en los avisos de
        # seguridad cuando la petición no indica el navegador.
        return request.META.get("HTTP_USER_AGENT") or gettext("No disponible")


class AdaptadorDobleFactor(DefaultMFAAdapter):
    def is_mfa_enabled(self, user, types=None):
        # Con la autenticación de dos factores desactivada se ignoran también los
        # autenticadores ya registrados.
        if not settings.CUENTAS_DOBLE_FACTOR_ACTIVO:
            return False
        # Al consultar un único tipo desactivado, como las llaves de acceso, se responde que
        # no está activo: django-allauth usa esa consulta para ofrecer pantallas cuyas rutas
        # no existen. Las consultas de varios tipos, como la que decide si se pide el segundo
        # factor al iniciar sesión, siguen contando los autenticadores registrados, para que
        # desactivar un tipo no deje esas cuentas sin segundo factor.
        if types is not None and len(types) == 1 and types[0] not in settings.MFA_SUPPORTED_TYPES:
            return False
        return super().is_mfa_enabled(user, types=types)
