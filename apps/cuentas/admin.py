from allauth.mfa.models import Authenticator
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import AdminUserCreationForm, UserChangeForm
from django.utils.translation import gettext_lazy as _

from .models import Usuario


class FormularioAltaUsuario(AdminUserCreationForm):
    class Meta:
        model = Usuario
        fields = ("correo",)


class FormularioCambioUsuario(UserChangeForm):
    class Meta:
        model = Usuario
        fields = "__all__"


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    form = FormularioCambioUsuario
    add_form = FormularioAltaUsuario
    fieldsets = (
        (None, {"fields": ("correo", "password")}),
        (_("Datos personales"), {"fields": ("nombre", "apellidos")}),
        (
            _("Permisos"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        (_("Fechas"), {"fields": ("last_login", "fecha_alta")}),
    )
    add_fieldsets = (
        (None, {"fields": ("correo", "usable_password", "password1", "password2")}),
    )
    list_display = ("correo", "nombre", "apellidos", "is_staff", "is_active")
    list_filter = ("is_staff", "is_superuser", "is_active", "groups")
    search_fields = ("correo", "nombre", "apellidos")
    ordering = ("correo",)
    filter_horizontal = ("groups", "user_permissions")

    def get_readonly_fields(self, request, obj=None):
        # En una cuenta existente, el correo se cambia desde la propia cuenta: django-allauth
        # verifica la dirección nueva antes de usarla para iniciar sesión.
        if obj is not None:
            return ("correo",)
        return ()


# El administrador que registra django-allauth muestra el campo data, que contiene el secreto
# TOTP y la semilla de los códigos de recuperación. Este solo muestra a quién pertenece cada
# autenticador y permite eliminarlo para restablecer la autenticación de dos factores.
admin.site.unregister(Authenticator)


@admin.register(Authenticator)
class AutenticadorAdmin(admin.ModelAdmin):
    list_display = ("user", "type", "created_at", "last_used_at")
    list_filter = ("type", "created_at", "last_used_at")
    fields = ("user", "type", "created_at", "last_used_at")
    readonly_fields = fields

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
