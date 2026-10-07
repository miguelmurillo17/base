"""Filtro de los informes de errores que se envían por correo a ``ADMINS``.

Oculta siempre los campos con contraseñas y códigos de verificación, porque varias vistas
de django-allauth (reautenticación, restablecimiento de contraseña y autenticación de dos
factores) no los marcan como sensibles.
"""

from django.views.debug import SafeExceptionReporterFilter

CAMPOS_SENSIBLES = frozenset(
    {
        "code",
        "credential",
        "key",
        "oldpassword",
        "password",
        "password1",
        "password2",
        "token",
    },
)


class FiltroInformesErrores(SafeExceptionReporterFilter):
    def get_post_parameters(self, request):
        parametros = super().get_post_parameters(request)
        if request is None or not self.is_active(request):
            return parametros
        parametros = parametros.copy()
        for nombre in CAMPOS_SENSIBLES & set(parametros):
            parametros[nombre] = self.cleansed_substitute
        return parametros
