"""Sitio de administración que solo admite sesiones iniciadas con django-allauth.

El formulario de acceso propio del sitio de administración nunca procesa credenciales: el
inicio de sesión pasa por django-allauth, que aplica la verificación del correo, los
límites de intentos y el segundo factor. El cambio de contraseña también pasa por
django-allauth. Con ``CUENTAS_ADMINISTRACION_EXIGE_DOBLE_FACTOR`` activo, además, el
personal necesita tener configurada la autenticación de dos factores.
"""

from allauth.account.utils import get_next_redirect_url
from allauth.mfa.models import Authenticator
from allauth.mfa.utils import is_mfa_enabled
from django.conf import settings
from django.contrib import admin, messages
from django.contrib.auth.decorators import login_not_required
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.utils.translation import gettext, gettext_lazy
from django.views.decorators.cache import never_cache


class SitioAdministracion(admin.AdminSite):
    site_header = settings.NOMBRE_SITIO
    site_title = settings.NOMBRE_SITIO
    index_title = gettext_lazy("Administración")

    def has_permission(self, request):
        if not super().has_permission(request):
            return False
        if settings.CUENTAS_ADMINISTRACION_EXIGE_DOBLE_FACTOR:
            # Los códigos de recuperación no cuentan: sirven para recuperar el acceso, no
            # como segundo factor configurado.
            return is_mfa_enabled(
                request.user,
                [Authenticator.Type.TOTP, Authenticator.Type.WEBAUTHN],
            )
        return True

    @method_decorator(never_cache)
    @login_not_required
    def login(self, request, extra_context=None):
        usuario = request.user
        destino = get_next_redirect_url(request)
        if not usuario.is_authenticated:
            return redirect_to_login(destino or request.get_full_path())
        if not (usuario.is_active and usuario.is_staff):
            raise PermissionDenied
        if not self.has_permission(request):
            messages.info(
                request,
                gettext(
                    "Para entrar al sitio de administración, configura primero la "
                    "autenticación de dos factores."
                ),
            )
            return redirect("mfa_index")
        return redirect(destino or "admin:index")

    def password_change(self, request, extra_context=None):
        # django-allauth aplica los límites de intentos, la reautenticación y el aviso por
        # correo, que la vista del sitio de administración no tiene.
        return redirect("account_change_password")

    def password_change_done(self, request, extra_context=None):
        return redirect("account_change_password")
