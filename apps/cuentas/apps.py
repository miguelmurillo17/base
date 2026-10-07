from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class CuentasConfig(AppConfig):
    name = "apps.cuentas"
    label = "cuentas"
    verbose_name = _("Cuentas")
