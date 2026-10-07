"""Pruebas del modelo de usuario y su gestor: normalización del correo, unicidad sin
distinguir mayúsculas, autenticación por correo y creación de superusuarios."""

import os
from io import StringIO
from unittest import mock

from django.contrib.auth import aauthenticate, authenticate, get_user_model
from django.core.exceptions import ValidationError
from django.core.management import CommandError, call_command
from django.db import IntegrityError, connection, transaction
from django.db.migrations.loader import MigrationLoader
from django.test import TestCase

Usuario = get_user_model()

CORREO = "ana@example.com"
CORREO_ADMINISTRADOR = "admin@example.com"
CONTRASENA = "clave-de-prueba-9481"
CONTRASENA_INCORRECTA = "otra-clave"
MENSAJE_DUPLICADO = "Ya existe un usuario con esa dirección de correo electrónico."


class PruebasGestorUsuarios(TestCase):
    def test_crear_usuario_guarda_el_correo_en_minusculas(self):
        usuario = Usuario.objects.create_user("Ana.Lopez@Example.COM", CONTRASENA)
        self.assertEqual(usuario.correo, "ana.lopez@example.com")

    def test_crear_usuario_valores_por_defecto(self):
        usuario = Usuario.objects.create_user(CORREO, CONTRASENA)
        self.assertTrue(usuario.is_active)
        self.assertFalse(usuario.is_staff)
        self.assertFalse(usuario.is_superuser)
        self.assertTrue(usuario.check_password(CONTRASENA))

    def test_crear_usuario_sin_contrasena_la_deja_inutilizable(self):
        usuario = Usuario.objects.create_user(CORREO)
        self.assertFalse(usuario.has_usable_password())

    def test_crear_usuario_exige_correo(self):
        with self.assertRaises(ValueError):
            Usuario.objects.create_user("", CONTRASENA)

    def test_crear_superusuario_activa_is_staff_e_is_superuser(self):
        usuario = Usuario.objects.create_superuser(CORREO_ADMINISTRADOR, CONTRASENA)
        self.assertTrue(usuario.is_staff)
        self.assertTrue(usuario.is_superuser)

    def test_crear_superusuario_rechaza_is_staff_falso(self):
        with self.assertRaises(ValueError):
            Usuario.objects.create_superuser(CORREO_ADMINISTRADOR, CONTRASENA, is_staff=False)

    def test_crear_superusuario_rechaza_is_superuser_falso(self):
        with self.assertRaises(ValueError):
            Usuario.objects.create_superuser(
                CORREO_ADMINISTRADOR,
                CONTRASENA,
                is_superuser=False,
            )

    def test_gestor_funciona_con_el_modelo_historico_de_las_migraciones(self):
        estado = MigrationLoader(connection).project_state(("cuentas", "0001_initial"))
        historico = estado.apps.get_model("cuentas", "Usuario")
        usuario = historico.objects.create_user("Ana@Example.com", CONTRASENA)
        self.assertEqual(usuario.correo, CORREO)
        self.assertTrue(Usuario.objects.get(pk=usuario.pk).check_password(CONTRASENA))


class PruebasIdentidadPorCorreo(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.usuario = Usuario.objects.create_user(CORREO, CONTRASENA)

    def test_full_clean_normaliza_el_correo(self):
        usuario = Usuario(correo="Pedro.Ruiz@Example.COM")
        usuario.set_password(CONTRASENA)
        usuario.full_clean()
        self.assertEqual(usuario.correo, "pedro.ruiz@example.com")

    def test_correo_duplicado_con_otras_mayusculas_se_rechaza(self):
        with transaction.atomic(), self.assertRaises(IntegrityError):
            Usuario.objects.create_user("ANA@example.com", CONTRASENA)

    def test_restriccion_unica_protege_escrituras_sin_normalizar(self):
        # objects.create no pasa por normalize_email; la restricción sobre Lower(correo)
        # impide el duplicado de todos modos.
        with transaction.atomic(), self.assertRaises(IntegrityError):
            Usuario.objects.create(correo="ANA@Example.com")

    def test_validacion_informa_duplicado_sin_distinguir_mayusculas(self):
        duplicado = Usuario(correo="Ana@Example.com")
        duplicado.set_password(CONTRASENA)
        with self.assertRaisesMessage(ValidationError, MENSAJE_DUPLICADO):
            duplicado.full_clean()

    def test_busqueda_por_clave_natural_ignora_mayusculas(self):
        self.assertEqual(Usuario.objects.get_by_natural_key("ANA@EXAMPLE.COM"), self.usuario)

    def test_busqueda_por_correo_ignora_mayusculas(self):
        self.assertEqual(list(Usuario.objects.con_correo("Ana@Example.COM")), [self.usuario])

    def test_autenticacion_con_correo_en_cualquier_combinacion_de_mayusculas(self):
        self.assertEqual(
            authenticate(username="Ana@Example.com", password=CONTRASENA),
            self.usuario,
        )

    async def test_autenticacion_asincrona_ignora_mayusculas(self):
        usuario = await aauthenticate(username="ANA@EXAMPLE.COM", password=CONTRASENA)
        self.assertEqual(usuario, self.usuario)

    def test_autenticacion_rechaza_contrasena_incorrecta(self):
        self.assertIsNone(authenticate(username=CORREO, password=CONTRASENA_INCORRECTA))

    def test_autenticacion_distingue_correos_que_solo_coinciden_en_mayusculas(self):
        # "ı" (i sin punto) e "i" son distintas en minúsculas pero iguales en mayúsculas.
        # Cada cuenta debe autenticarse sin ambigüedad.
        con_i_sin_punto = Usuario.objects.create_user("ınes@example.com", CONTRASENA)
        con_i = Usuario.objects.create_user("ines@example.com", CONTRASENA)
        self.assertEqual(
            authenticate(username="ınes@example.com", password=CONTRASENA),
            con_i_sin_punto,
        )
        self.assertEqual(authenticate(username="ines@example.com", password=CONTRASENA), con_i)


class PruebasCrearSuperusuario(TestCase):
    def _crear_superusuario(self, correo: str) -> None:
        variables = {"DJANGO_SUPERUSER_CORREO": correo, "DJANGO_SUPERUSER_PASSWORD": CONTRASENA}
        with mock.patch.dict(os.environ, variables):
            call_command("createsuperuser", interactive=False, stdout=StringIO())

    def test_createsuperuser_sin_interaccion_normaliza_el_correo(self):
        self._crear_superusuario("Admin.Root@Example.COM")
        usuario = Usuario.objects.get()
        self.assertEqual(usuario.correo, "admin.root@example.com")
        self.assertTrue(usuario.is_superuser)

    def test_createsuperuser_rechaza_correo_existente_con_otras_mayusculas(self):
        self._crear_superusuario("admin.root@example.com")
        with self.assertRaises(CommandError):
            self._crear_superusuario("ADMIN.ROOT@example.com")
