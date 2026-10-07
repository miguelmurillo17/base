"""Pruebas de los flujos de django-allauth: registro, verificación del correo, inicio de
sesión, restablecimiento de contraseña, cambio de correo y autenticación de dos factores."""

import re

from allauth.account.models import EmailAddress
from allauth.mfa.models import Authenticator
from django.contrib.auth import get_user_model
from django.core import mail
from django.core.exceptions import NON_FIELD_ERRORS
from django.test import Client, RequestFactory, TestCase, override_settings
from django.urls import reverse
from django.utils.http import int_to_base36

from apps.cuentas.adaptadores import AdaptadorCuentas

from .ayudas import (
    CONTRASENA,
    CORREO,
    INSTANTE,
    activar_doble_factor,
    ajustes_predeterminados,
    crear_usuario,
    fijar_reloj_totp,
    generar_codigo_totp,
    iniciar_sesion,
    iniciar_sesion_con_doble_factor,
    tiene_sesion_iniciada,
)

Usuario = get_user_model()

CONTRASENA_INCORRECTA = "otra-clave"
DOMINIO_ANCHO_COMPLETO = "ＥＸＡＭＰＬＥ.com"
CORREO_ANCHO_COMPLETO = f"ana@{DOMINIO_ANCHO_COMPLETO}"
CORREO_SUPERUSUARIO = "admin@example.com"
RUTA_CONFIRMACION = re.compile(r"/cuentas/confirm-email/[-:\w]+/")
RUTA_RESTABLECIMIENTO = re.compile(r"/cuentas/password/reset/key/([0-9a-z]+)-[^/\s]+/")
DATOS_REGISTRO = {"email": "Ana@Example.com", "password1": CONTRASENA, "password2": CONTRASENA}


@ajustes_predeterminados
class PruebasRegistro(TestCase):
    def test_registro_cerrado_por_defecto(self):
        respuesta = self.client.post(reverse("account_signup"), DATOS_REGISTRO)
        self.assertTemplateUsed(respuesta, "account/signup_closed.html")
        self.assertFalse(Usuario.objects.exists())

    @override_settings(CUENTAS_REGISTRO_ABIERTO=True)
    def test_registro_abierto_crea_usuario_y_envia_verificacion(self):
        respuesta = self.client.post(reverse("account_signup"), DATOS_REGISTRO)
        self.assertRedirects(
            respuesta,
            reverse("account_email_verification_sent"),
            fetch_redirect_response=False,
        )
        self.assertFalse(tiene_sesion_iniciada(self.client))
        self.assertEqual(Usuario.objects.get().correo, CORREO)
        self.assertEqual(len(mail.outbox), 1)
        self.assertRegex(mail.outbox[0].body, RUTA_CONFIRMACION)

    @override_settings(CUENTAS_REGISTRO_ABIERTO=True)
    def test_registro_normaliza_caracteres_de_ancho_completo(self):
        datos = {**DATOS_REGISTRO, "email": CORREO_ANCHO_COMPLETO}
        self.client.post(reverse("account_signup"), datos)
        self.assertEqual(Usuario.objects.get().correo, CORREO)

    @override_settings(CUENTAS_REGISTRO_ABIERTO=True)
    def test_enlace_de_verificacion_confirma_el_correo_e_inicia_sesion(self):
        self.client.post(reverse("account_signup"), DATOS_REGISTRO)
        ruta = RUTA_CONFIRMACION.search(mail.outbox[0].body)[0]
        # El GET solo muestra la confirmación; el correo se verifica con el POST.
        self.assertEqual(self.client.get(ruta).status_code, 200)
        self.assertFalse(EmailAddress.objects.get().verified)
        respuesta = self.client.post(ruta)
        self.assertRedirects(respuesta, reverse("inicio"), fetch_redirect_response=False)
        self.assertTrue(EmailAddress.objects.get().verified)
        self.assertTrue(tiene_sesion_iniciada(self.client))

    @override_settings(CUENTAS_REGISTRO_ABIERTO=True)
    def test_registro_con_correo_existente_no_revela_la_cuenta(self):
        crear_usuario()
        respuesta = self.client.post(reverse("account_signup"), DATOS_REGISTRO)
        self.assertRedirects(
            respuesta,
            reverse("account_email_verification_sent"),
            fetch_redirect_response=False,
        )
        self.assertEqual(Usuario.objects.count(), 1)


@ajustes_predeterminados
class PruebasVerificacionCorreo(TestCase):
    def test_verificacion_obligatoria_impide_iniciar_sesion_sin_verificar(self):
        crear_usuario(verificado=False)
        respuesta = iniciar_sesion(self.client)
        self.assertRedirects(
            respuesta,
            reverse("account_email_verification_sent"),
            fetch_redirect_response=False,
        )
        self.assertFalse(tiene_sesion_iniciada(self.client))
        self.assertEqual(len(mail.outbox), 1)

    def test_correo_de_verificacion_indica_abrir_el_enlace(self):
        crear_usuario(verificado=False)
        iniciar_sesion(self.client)
        self.assertIn("abre el siguiente enlace", mail.outbox[0].body)
        self.assertNotRegex(mail.outbox[0].body, r"\bvete\b")

    @override_settings(ACCOUNT_EMAIL_VERIFICATION="optional")
    def test_verificacion_opcional_permite_iniciar_sesion_sin_verificar(self):
        crear_usuario(verificado=False)
        respuesta = iniciar_sesion(self.client)
        self.assertRedirects(respuesta, reverse("inicio"), fetch_redirect_response=False)
        self.assertTrue(tiene_sesion_iniciada(self.client))

    @override_settings(ACCOUNT_EMAIL_VERIFICATION="none")
    def test_sin_verificacion_inicia_sesion_sin_enviar_correo(self):
        crear_usuario(verificado=False)
        respuesta = iniciar_sesion(self.client)
        self.assertRedirects(respuesta, reverse("inicio"), fetch_redirect_response=False)
        self.assertEqual(len(mail.outbox), 0)


@ajustes_predeterminados
class PruebasInicioSesion(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.usuario = crear_usuario()

    def test_inicio_exige_sesion(self):
        respuesta = self.client.get(reverse("inicio"))
        self.assertRedirects(
            respuesta,
            f"{reverse('account_login')}?next=/",
            fetch_redirect_response=False,
        )

    def test_inicio_de_sesion_ignora_mayusculas_del_correo(self):
        respuesta = iniciar_sesion(self.client, correo="ANA@Example.com")
        self.assertRedirects(respuesta, reverse("inicio"), fetch_redirect_response=False)
        self.assertTrue(tiene_sesion_iniciada(self.client))

    def test_inicio_de_sesion_normaliza_caracteres_de_ancho_completo(self):
        respuesta = iniciar_sesion(self.client, correo=CORREO_ANCHO_COMPLETO)
        self.assertRedirects(respuesta, reverse("inicio"), fetch_redirect_response=False)
        self.usuario.refresh_from_db()
        self.assertEqual(self.usuario.correo, CORREO)
        self.assertEqual(EmailAddress.objects.count(), 1)

    def test_contrasena_incorrecta_no_inicia_sesion(self):
        respuesta = iniciar_sesion(self.client, contrasena=CONTRASENA_INCORRECTA)
        formulario = respuesta.context["form"]
        self.assertTrue(formulario.has_error(NON_FIELD_ERRORS, "email_password_mismatch"))
        self.assertFalse(tiene_sesion_iniciada(self.client))

    def test_intentos_fallidos_bloquean_el_inicio_de_sesion(self):
        for _ in range(5):
            iniciar_sesion(self.client, contrasena=CONTRASENA_INCORRECTA)
        formulario = iniciar_sesion(self.client).context["form"]
        self.assertTrue(formulario.has_error(NON_FIELD_ERRORS, "too_many_login_attempts"))
        self.assertFalse(tiene_sesion_iniciada(self.client))

    def test_bloqueo_por_intentos_no_depende_del_encabezado_host(self):
        for _ in range(5):
            iniciar_sesion(self.client, contrasena=CONTRASENA_INCORRECTA)
        for host in ("TESTSERVER", "testserver:8000"):
            with self.subTest(host=host):
                formulario = iniciar_sesion(self.client, HTTP_HOST=host).context["form"]
                self.assertTrue(
                    formulario.has_error(NON_FIELD_ERRORS, "too_many_login_attempts"),
                )

    def test_formulario_vacio_resume_los_campos_con_error(self):
        respuesta = self.client.post(reverse("account_login"), {"login": "", "password": ""})
        self.assertContains(respuesta, "Revisa los campos marcados")
        self.assertContains(respuesta, 'href="#id_login"')
        self.assertContains(respuesta, 'href="#id_password"')

    def test_cerrar_sesion_exige_post(self):
        iniciar_sesion(self.client)
        self.assertEqual(self.client.get(reverse("account_logout")).status_code, 200)
        self.assertTrue(tiene_sesion_iniciada(self.client))
        respuesta = self.client.post(reverse("account_logout"))
        self.assertRedirects(respuesta, reverse("account_login"), fetch_redirect_response=False)
        self.assertFalse(tiene_sesion_iniciada(self.client))

    def test_avisos_sin_navegador_indicado_dicen_no_disponible(self):
        peticion = RequestFactory().get("/")
        peticion.META.pop("HTTP_USER_AGENT", None)
        adaptador = AdaptadorCuentas(peticion)
        self.assertEqual(adaptador.get_http_user_agent(peticion), "No disponible")


@ajustes_predeterminados
class PruebasRestablecerContrasena(TestCase):
    def test_enlace_de_restablecimiento_cambia_la_contrasena(self):
        usuario = crear_usuario()
        self.client.post(reverse("account_reset_password"), {"email": "ANA@Example.com"})
        self.assertEqual(mail.outbox[0].to, [CORREO])
        ruta = RUTA_RESTABLECIMIENTO.search(mail.outbox[0].body)[0]
        url_formulario = self.client.get(ruta)["Location"]
        nueva = "Otra-clave-de-prueba-2026"
        respuesta = self.client.post(url_formulario, {"password1": nueva, "password2": nueva})
        self.assertRedirects(
            respuesta,
            reverse("account_reset_password_from_key_done"),
            fetch_redirect_response=False,
        )
        usuario.refresh_from_db()
        self.assertTrue(usuario.check_password(nueva))
        self.assertTrue(mail.outbox[-1].subject.endswith("Contraseña restablecida"))

    def test_restablecimiento_normaliza_caracteres_de_ancho_completo(self):
        crear_usuario()
        self.client.post(reverse("account_reset_password"), {"email": CORREO_ANCHO_COMPLETO})
        self.assertEqual(mail.outbox[0].to, [CORREO])

    def test_direccion_sin_cuenta_recibe_aviso_sin_enlace_de_registro(self):
        self.client.post(reverse("account_reset_password"), {"email": "nadie@example.com"})
        self.assertEqual(len(mail.outbox), 1)
        self.assertNotIn(reverse("account_signup"), mail.outbox[0].body)

    @override_settings(CUENTAS_REGISTRO_ABIERTO=True)
    def test_direccion_sin_cuenta_recibe_enlace_de_registro_si_esta_abierto(self):
        self.client.post(reverse("account_reset_password"), {"email": "nadie@example.com"})
        self.assertIn(reverse("account_signup"), mail.outbox[0].body)


@ajustes_predeterminados
class PruebasCambioCorreo(TestCase):
    def setUp(self):
        self.usuario = crear_usuario()

    def test_agregar_correo_normaliza_caracteres_de_ancho_completo(self):
        iniciar_sesion(self.client)
        self.client.post(
            reverse("account_email"),
            {"action_add": "", "email": f"nueva@{DOMINIO_ANCHO_COMPLETO}"},
        )
        self.assertTrue(EmailAddress.objects.filter(email="nueva@example.com").exists())

    def test_correo_de_otra_cuenta_sin_direccion_registrada_no_se_puede_verificar(self):
        # createsuperuser no registra la dirección en django-allauth.
        superusuario = Usuario.objects.create_superuser(CORREO_SUPERUSUARIO, CONTRASENA)
        iniciar_sesion(self.client)
        self.client.post(
            reverse("account_email"),
            {"action_add": "", "email": CORREO_SUPERUSUARIO},
        )
        ruta = RUTA_CONFIRMACION.search(mail.outbox[-1].body)[0]
        respuesta = Client().post(ruta)
        self.assertNotEqual(respuesta.status_code, 500)
        self.usuario.refresh_from_db()
        self.assertEqual(self.usuario.correo, CORREO)
        self.assertFalse(EmailAddress.objects.get(email=CORREO_SUPERUSUARIO).verified)
        # El restablecimiento sigue llegando a la cuenta dueña del correo. La dirección sin
        # verificar también produce un enlace para la otra cuenta, pero se envía al mismo
        # buzón, que solo controla quien es dueño de la dirección.
        mail.outbox.clear()
        Client().post(reverse("account_reset_password"), {"email": CORREO_SUPERUSUARIO})
        self.assertTrue(all(correo.to == [CORREO_SUPERUSUARIO] for correo in mail.outbox))
        cuentas = [RUTA_RESTABLECIMIENTO.search(correo.body)[1] for correo in mail.outbox]
        self.assertIn(int_to_base36(superusuario.pk), cuentas)

    def test_cambio_de_correo_con_doble_factor_se_rechaza(self):
        # django-allauth no permite agregar un correo sin verificar a una cuenta con la
        # autenticación de dos factores activa mientras la verificación se haga por enlace.
        secreto, _ = activar_doble_factor(self.usuario)
        iniciar_sesion_con_doble_factor(self.client, secreto)
        respuesta = self.client.post(
            reverse("account_email"),
            {"action_add": "", "email": "nueva@example.com"},
        )
        self.assertEqual(respuesta.status_code, 200)
        self.assertTrue(respuesta.context["form"].has_error("email", "add_email_blocked"))
        self.assertEqual(EmailAddress.objects.count(), 1)
        self.assertEqual(len(mail.outbox), 0)


@ajustes_predeterminados
class PruebasDobleFactor(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.usuario = crear_usuario()

    def test_activar_totp_y_pedir_codigo_al_iniciar_sesion(self):
        with fijar_reloj_totp(INSTANTE):
            iniciar_sesion(self.client)
            secreto = self.client.get(reverse("mfa_activate_totp")).context["form"].secret
            respuesta = self.client.post(
                reverse("mfa_activate_totp"),
                {"code": generar_codigo_totp(secreto, INSTANTE)},
            )
            self.assertRedirects(
                respuesta,
                reverse("mfa_view_recovery_codes"),
                fetch_redirect_response=False,
            )
            self.client.post(reverse("account_logout"))
        siguiente_periodo = INSTANTE + 30
        with fijar_reloj_totp(siguiente_periodo):
            respuesta = iniciar_sesion(self.client)
            self.assertRedirects(
                respuesta,
                reverse("mfa_authenticate"),
                fetch_redirect_response=False,
            )
            self.assertFalse(tiene_sesion_iniciada(self.client))
            respuesta = self.client.post(
                reverse("mfa_authenticate"),
                {"code": generar_codigo_totp(secreto, siguiente_periodo)},
            )
        self.assertRedirects(respuesta, reverse("inicio"), fetch_redirect_response=False)
        self.assertTrue(tiene_sesion_iniciada(self.client))

    def test_codigo_de_recuperacion_permite_iniciar_sesion(self):
        _, codigos = activar_doble_factor(self.usuario)
        iniciar_sesion(self.client)
        respuesta = self.client.post(reverse("mfa_authenticate"), {"code": codigos[0]})
        self.assertRedirects(respuesta, reverse("inicio"), fetch_redirect_response=False)
        self.assertTrue(tiene_sesion_iniciada(self.client))

    def test_codigo_totp_no_se_puede_reutilizar(self):
        secreto, _ = activar_doble_factor(self.usuario)
        with fijar_reloj_totp():
            iniciar_sesion(self.client)
            primera = self.client.post(
                reverse("mfa_authenticate"),
                {"code": generar_codigo_totp(secreto)},
            )
            self.assertRedirects(primera, reverse("inicio"), fetch_redirect_response=False)
            self.assertTrue(tiene_sesion_iniciada(self.client))
            self.client.post(reverse("account_logout"))
            iniciar_sesion(self.client)
            segunda = self.client.post(
                reverse("mfa_authenticate"),
                {"code": generar_codigo_totp(secreto)},
            )
        self.assertTrue(segunda.context["form"].has_error("code", "incorrect_code"))
        self.assertFalse(tiene_sesion_iniciada(self.client))

    @override_settings(CUENTAS_DOBLE_FACTOR_ACTIVO=False)
    def test_doble_factor_desactivado_no_pide_codigo(self):
        activar_doble_factor(self.usuario)
        respuesta = iniciar_sesion(self.client)
        self.assertRedirects(respuesta, reverse("inicio"), fetch_redirect_response=False)
        self.assertTrue(tiene_sesion_iniciada(self.client))

    def test_llaves_de_acceso_desactivadas_no_rompen_la_reautenticacion(self):
        secreto, _ = activar_doble_factor(self.usuario)
        Authenticator.objects.create(
            user=self.usuario,
            type=Authenticator.Type.WEBAUTHN,
            data={},
        )
        iniciar_sesion_con_doble_factor(self.client, secreto)
        self.assertEqual(self.client.get(reverse("account_reauthenticate")).status_code, 200)

    def test_llave_de_acceso_desactivada_sigue_pidiendo_codigo_de_recuperacion(self):
        _, codigos = activar_doble_factor(self.usuario)
        Authenticator.objects.filter(type=Authenticator.Type.TOTP).delete()
        Authenticator.objects.create(
            user=self.usuario,
            type=Authenticator.Type.WEBAUTHN,
            data={},
        )
        respuesta = iniciar_sesion(self.client)
        self.assertRedirects(
            respuesta,
            reverse("mfa_authenticate"),
            fetch_redirect_response=False,
        )
        respuesta = self.client.post(reverse("mfa_authenticate"), {"code": codigos[0]})
        self.assertRedirects(respuesta, reverse("inicio"), fetch_redirect_response=False)
