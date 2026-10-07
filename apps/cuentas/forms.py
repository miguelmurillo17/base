"""Formularios de django-allauth que normalizan el correo igual que el modelo de usuario.

El formulario de inicio de sesión no usa la normalización del adaptador, y el de
restablecimiento de contraseña la usa solo para buscar la cuenta: los dos devuelven el
correo tal como se escribió. Sin estos formularios, un correo con caracteres de ancho
completo en el dominio no coincidiría con el guardado y, con la verificación obligatoria,
el inicio de sesión registraría esa variante como correo principal.
"""

from allauth.account.forms import LoginForm, ResetPasswordForm

from .models import GestorUsuarios


class FormularioInicioSesion(LoginForm):
    def clean_login(self):
        return GestorUsuarios.normalize_email(super().clean_login())


class FormularioRestablecerContrasena(ResetPasswordForm):
    def clean_email(self):
        self.cleaned_data["email"] = GestorUsuarios.normalize_email(self.cleaned_data["email"])
        return super().clean_email()
