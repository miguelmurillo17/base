"""Configuraciones de aplicación que el proyecto aplica a aplicaciones de Django.

No va en apps/cuentas/apps.py: AdminConfig es una configuración por defecto, y declararla
en el módulo de otra aplicación le daría dos configuraciones por defecto.
"""

from django.contrib.admin.apps import AdminConfig


class AdministracionConfig(AdminConfig):
    default_site = "config.sitio_administracion.SitioAdministracion"
