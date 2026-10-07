"""Pruebas del sitio de administración: acceso a través de django-allauth, exigencia de la
autenticación de dos factores y administración de usuarios y autenticadores."""

from allauth.mfa.models import Authenticator
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from .ayudas import (
    CONTRASENA,
    CORREO,
    activar_doble_factor,
    ajustes_predeterminados,
    crear_usuario,
    fijar_reloj_totp,
    generar_codigo_totp,
    iniciar_sesion,
    tiene_sesion_iniciada,
)

Usuario = get_user_model()

CORREO_ADMINISTRADOR = "admin@example.com"
MENSAJE_DUPLICADO = "Ya existe un usuario con esa dirección de correo electrónico."


@ajustes_predeterminados
class PruebasAccesoAdministracion(TestCase):
    def test_persona_anonima_va_al_inicio_de_sesion_del_sitio(self):
        respuesta = self.client.get(reverse("admin:index"), follow=True)
        url_final, _ = respuesta.redirect_chain[-1]
        self.assertTrue(url_final.startswith(reverse("account_login")))
        self.assertIn("next=", url_final)

    def test_formulario_de_acceso_del_admin_no_autentica(self):
        crear_usuario(is_staff=True, is_superuser=True)
        respuesta = self.client.post(
            reverse("admin:login"),
            {"username": CORREO, "password": CONTRASENA},
        )
        self.assertEqual(respuesta.status_code, 302)
        self.assertTrue(respuesta["Location"].startswith(reverse("account_login")))
        self.assertFalse(tiene_sesion_iniciada(self.client))

    def test_usuario_sin_acceso_al_sitio_de_administracion_recibe_403(self):
        self.client.force_login(crear_usuario())
        with self.assertLogs("django.request", "WARNING"):
            respuesta = self.client.get(reverse("admin:login"))
        self.assertEqual(respuesta.status_code, 403)

    def test_personal_sin_doble_factor_debe_configurarlo(self):
        self.client.force_login(crear_usuario(is_staff=True))
        respuesta = self.client.get(reverse("admin:login"))
        self.assertRedirects(respuesta, reverse("mfa_index"), fetch_redirect_response=False)

    @override_settings(CUENTAS_ADMINISTRACION_EXIGE_DOBLE_FACTOR=False)
    def test_personal_sin_doble_factor_entra_si_no_se_exige(self):
        self.client.force_login(crear_usuario(is_staff=True))
        self.assertEqual(self.client.get(reverse("admin:index")).status_code, 200)

    def test_personal_con_doble_factor_entra_despues_del_codigo(self):
        usuario = crear_usuario(is_staff=True, is_superuser=True)
        secreto, _ = activar_doble_factor(usuario)
        with fijar_reloj_totp():
            respuesta = iniciar_sesion(self.client, siguiente=reverse("admin:index"))
            self.assertRedirects(
                respuesta,
                reverse("mfa_authenticate"),
                fetch_redirect_response=False,
            )
            respuesta = self.client.post(
                reverse("mfa_authenticate"),
                {"code": generar_codigo_totp(secreto)},
            )
        self.assertRedirects(respuesta, reverse("admin:index"), fetch_redirect_response=False)
        self.assertEqual(self.client.get(reverse("admin:index")).status_code, 200)

    def test_superusuario_sin_direccion_registrada_debe_verificar_su_correo(self):
        # createsuperuser no registra la dirección en django-allauth: con la verificación
        # obligatoria, el primer inicio de sesión pide confirmar el correo.
        Usuario.objects.create_superuser(CORREO_ADMINISTRADOR, CONTRASENA)
        respuesta = iniciar_sesion(self.client, correo=CORREO_ADMINISTRADOR)
        self.assertRedirects(
            respuesta,
            reverse("account_email_verification_sent"),
            fetch_redirect_response=False,
        )
        self.assertFalse(tiene_sesion_iniciada(self.client))


@ajustes_predeterminados
class PruebasAdminUsuarios(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.administrador = crear_usuario(
            CORREO_ADMINISTRADOR,
            is_staff=True,
            is_superuser=True,
        )
        activar_doble_factor(cls.administrador)

    def setUp(self):
        self.client.force_login(self.administrador)

    def test_lista_y_edicion_cargan(self):
        lista = reverse("admin:cuentas_usuario_changelist")
        self.assertEqual(self.client.get(lista).status_code, 200)
        edicion = reverse("admin:cuentas_usuario_change", args=[self.administrador.pk])
        self.assertEqual(self.client.get(edicion).status_code, 200)

    def test_correo_es_de_solo_lectura_al_editar(self):
        edicion = reverse("admin:cuentas_usuario_change", args=[self.administrador.pk])
        self.assertNotContains(self.client.get(edicion), 'name="correo"')

    def test_alta_de_usuario_desde_el_admin_guarda_el_correo_normalizado(self):
        respuesta = self.client.post(
            reverse("admin:cuentas_usuario_add"),
            {
                "correo": "Nuevo@Example.com",
                "usable_password": "true",
                "password1": CONTRASENA,
                "password2": CONTRASENA,
            },
        )
        self.assertEqual(respuesta.status_code, 302)
        self.assertTrue(Usuario.objects.filter(correo="nuevo@example.com").exists())

    def test_alta_desde_el_admin_rechaza_duplicado_sin_distinguir_mayusculas(self):
        respuesta = self.client.post(
            reverse("admin:cuentas_usuario_add"),
            {
                "correo": "ADMIN@example.com",
                "usable_password": "true",
                "password1": CONTRASENA,
                "password2": CONTRASENA,
            },
        )
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, MENSAJE_DUPLICADO)
        self.assertEqual(Usuario.objects.count(), 1)

    def test_cambio_de_contrasena_pasa_por_django_allauth(self):
        respuesta = self.client.get(reverse("admin:password_change"))
        self.assertRedirects(
            respuesta,
            reverse("account_change_password"),
            fetch_redirect_response=False,
        )

    def test_autenticadores_se_muestran_sin_sus_secretos(self):
        autenticador = Authenticator.objects.get(
            user=self.administrador,
            type=Authenticator.Type.TOTP,
        )
        edicion = reverse("admin:mfa_authenticator_change", args=[autenticador.pk])
        respuesta = self.client.get(edicion)
        self.assertEqual(respuesta.status_code, 200)
        self.assertNotContains(respuesta, autenticador.data["secret"])
        self.assertEqual(self.client.get(reverse("admin:mfa_authenticator_add")).status_code, 403)
