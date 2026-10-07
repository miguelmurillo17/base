"""Rutas del proyecto con las de llaves de acceso.

Las pruebas de las pantallas con ``CUENTAS_LLAVES_ACCESO_ACTIVAS`` las usan como
``ROOT_URLCONF``, porque las rutas de llaves de acceso se registran al cargar el proyecto y
no existen con el valor por defecto.
"""

from django.urls import include, path

from config.urls import urlpatterns as rutas_proyecto

urlpatterns = [
    *rutas_proyecto,
    path("cuentas/doble-factor/webauthn/", include("allauth.mfa.webauthn.urls")),
]
