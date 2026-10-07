"""Modelo de usuario del proyecto.

El correo electrónico es el identificador de inicio de sesión. Se guarda completo en
minúsculas y normalizado con NFKC, y es único sin distinguir mayúsculas.

Los nombres en inglés (``is_active``, ``is_staff``, ``create_user``, ``get_full_name``,
entre otros) son los que Django espera encontrar en un modelo de usuario.
"""

import unicodedata

from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from django.db.models import Value
from django.db.models.functions import Lower
from django.db.models.lookups import Exact
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

MENSAJE_CORREO_DUPLICADO = _("Ya existe un usuario con esa dirección de correo electrónico.")


class GestorUsuarios(BaseUserManager):
    use_in_migrations = True

    @classmethod
    def normalize_email(cls, email):
        # La dirección completa se guarda en minúsculas porque django-allauth busca a los
        # usuarios comparándola exactamente en minúsculas. NFKC unifica las formas Unicode
        # equivalentes, como hace Django con los nombres de usuario.
        return unicodedata.normalize("NFKC", email or "").strip().lower()

    def _coincide_correo(self, correo: str) -> Exact:
        # Misma expresión que la restricción única cuentas_usuario_correo_unico: a lo
        # sumo una fila coincide y la consulta usa ese índice. No se usa correo__iexact
        # porque en PostgreSQL compara con UPPER(), que no equivale a LOWER() para
        # algunos caracteres no ASCII que el validador de correo acepta.
        return Exact(Lower(self.model.USERNAME_FIELD), Lower(Value(correo)))

    def con_correo(self, correo: str) -> models.QuerySet:
        """Devuelve los usuarios con ``correo``, sin distinguir mayúsculas."""
        return self.filter(self._coincide_correo(correo))

    def get_by_natural_key(self, username):
        return self.get(self._coincide_correo(username))

    async def aget_by_natural_key(self, username):
        return await self.aget(self._coincide_correo(username))

    def _crear_usuario(
        self,
        correo: str,
        password: str | None,
        **campos_extra: object,
    ) -> "Usuario":
        if not correo:
            raise ValueError("El correo electrónico es obligatorio.")
        usuario = self.model(correo=self.normalize_email(correo), **campos_extra)
        # make_password en lugar de set_password: los modelos históricos que reciben las
        # migraciones de datos no tienen los métodos del modelo.
        usuario.password = make_password(password)
        usuario.save(using=self._db)
        return usuario

    def create_user(self, correo, password=None, **campos_extra):
        campos_extra.setdefault("is_staff", False)
        campos_extra.setdefault("is_superuser", False)
        return self._crear_usuario(correo, password, **campos_extra)

    def create_superuser(self, correo, password=None, **campos_extra):
        campos_extra.setdefault("is_staff", True)
        campos_extra.setdefault("is_superuser", True)
        if campos_extra.get("is_staff") is not True:
            raise ValueError("Un superusuario debe tener is_staff=True.")
        if campos_extra.get("is_superuser") is not True:
            raise ValueError("Un superusuario debe tener is_superuser=True.")
        return self._crear_usuario(correo, password, **campos_extra)


class Usuario(AbstractBaseUser, PermissionsMixin):
    correo = models.EmailField(
        _("correo electrónico"),
        unique=True,
        error_messages={"unique": MENSAJE_CORREO_DUPLICADO},
    )
    nombre = models.CharField(_("nombre"), max_length=150, blank=True)
    apellidos = models.CharField(_("apellidos"), max_length=150, blank=True)
    is_staff = models.BooleanField(
        _("acceso al sitio de administración"),
        default=False,
        help_text=_("Indica si el usuario puede entrar al sitio de administración."),
    )
    is_active = models.BooleanField(
        _("activo"),
        default=True,
        help_text=_(
            "Indica si el usuario puede iniciar sesión. Para dar de baja una cuenta se "
            "desmarca esta opción en lugar de eliminarla."
        ),
    )
    fecha_alta = models.DateTimeField(_("fecha de alta"), default=timezone.now)

    objects = GestorUsuarios()

    EMAIL_FIELD = "correo"
    USERNAME_FIELD = "correo"
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = _("usuario")
        verbose_name_plural = _("usuarios")
        constraints = [
            models.UniqueConstraint(
                Lower("correo"),
                name="cuentas_usuario_correo_unico",
                violation_error_message=MENSAJE_CORREO_DUPLICADO,
            ),
        ]

    def __str__(self):
        return self.correo

    def clean(self):
        super().clean()
        self.correo = self.__class__.objects.normalize_email(self.correo)

    def get_full_name(self):
        return f"{self.nombre} {self.apellidos}".strip()

    def get_short_name(self):
        return self.nombre
