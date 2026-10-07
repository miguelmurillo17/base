"""Rutas principales del proyecto."""

from django.conf import settings
from django.contrib import admin
from django.contrib.auth.decorators import login_required
from django.urls import include, path
from django.views.generic import TemplateView

urlpatterns = [
    path(
        "",
        login_required(TemplateView.as_view(template_name="inicio.html")),
        name="inicio",
    ),
    path("admin/", admin.site.urls),
    path("cuentas/", include("allauth.account.urls")),
]

# Las rutas de la autenticación de dos factores solo existen cuando la función está activa.
if settings.CUENTAS_DOBLE_FACTOR_ACTIVO:
    urlpatterns.append(path("cuentas/doble-factor/", include("allauth.mfa.urls")))
