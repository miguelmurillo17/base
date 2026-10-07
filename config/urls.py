"""Rutas principales del proyecto.

``LoginRequiredMiddleware`` exige sesión iniciada en todas las rutas; las públicas, como las
de django-allauth, se marcan con ``@login_not_required``.
"""

from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView

urlpatterns = [
    path("", TemplateView.as_view(template_name="inicio.html"), name="inicio"),
    path("admin/", admin.site.urls),
    path("cuentas/", include("allauth.account.urls")),
]

# Las rutas de la autenticación de dos factores solo existen cuando la función está activa.
if settings.CUENTAS_DOBLE_FACTOR_ACTIVO:
    urlpatterns.append(path("cuentas/doble-factor/", include("allauth.mfa.urls")))
