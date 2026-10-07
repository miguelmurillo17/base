"""Pruebas del registro de auditoría de las cuentas: eventos registrados y ausencia de
correos y credenciales en los mensajes."""

from django.test import TestCase
from django.urls import reverse

from .ayudas import (
    CONTRASENA,
    CORREO,
    activar_doble_factor,
    ajustes_predeterminados,
    crear_usuario,
    fijar_reloj_totp,
    iniciar_sesion,
)

REGISTRO_AUDITORIA = "apps.cuentas.auditoria"
CONTRASENA_NUEVA = "Otra-clave-de-prueba-2026"
CODIGO_INCORRECTO = "000000"


@ajustes_predeterminados
class PruebasAuditoria(TestCase):
    def setUp(self):
        self.usuario = crear_usuario()

    def test_inicio_de_sesion_registra_usuario_e_ip_sin_el_correo(self):
        with self.assertLogs(REGISTRO_AUDITORIA, "INFO") as registro:
            iniciar_sesion(self.client)
        esperado = f"Inicio de sesión del usuario {self.usuario.pk} desde 127.0.0.1"
        self.assertEqual(registro.output, [f"INFO:{REGISTRO_AUDITORIA}:{esperado}"])

    def test_inicio_de_sesion_fallido_no_registra_credenciales(self):
        with self.assertLogs(REGISTRO_AUDITORIA, "WARNING") as registro:
            iniciar_sesion(self.client, contrasena="clave-incorrecta")
        texto = "\n".join(registro.output)
        self.assertIn("Intento de inicio de sesión fallido desde 127.0.0.1", texto)
        self.assertNotIn(CORREO, texto)
        self.assertNotIn("clave-incorrecta", texto)

    def test_cierre_de_sesion_se_registra(self):
        self.client.force_login(self.usuario)
        with self.assertLogs(REGISTRO_AUDITORIA, "INFO") as registro:
            self.client.post(reverse("account_logout"))
        self.assertIn(f"Cierre de sesión del usuario {self.usuario.pk}", registro.output[0])

    def test_cambio_de_contrasena_se_registra(self):
        iniciar_sesion(self.client)
        with self.assertLogs(REGISTRO_AUDITORIA, "INFO") as registro:
            self.client.post(
                reverse("account_change_password"),
                {
                    "oldpassword": CONTRASENA,
                    "password1": CONTRASENA_NUEVA,
                    "password2": CONTRASENA_NUEVA,
                },
            )
        self.assertIn(f"Cambio de contraseña del usuario {self.usuario.pk}", registro.output[0])

    def test_codigo_de_verificacion_rechazado_se_registra(self):
        activar_doble_factor(self.usuario)
        with fijar_reloj_totp():
            iniciar_sesion(self.client)
            with self.assertLogs(REGISTRO_AUDITORIA, "WARNING") as registro:
                self.client.post(reverse("mfa_authenticate"), {"code": CODIGO_INCORRECTO})
        self.assertIn(
            f"Código de verificación rechazado para el usuario {self.usuario.pk}",
            registro.output[0],
        )
