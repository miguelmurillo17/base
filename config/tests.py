"""Pruebas de la configuración: política de seguridad de contenido, lectura de variables de
entorno, ajustes y rutas de cuentas, filtro de informes de errores, servidor de correo de
desarrollo y traducciones propias."""

import ast
import os
import re
import runpy
from io import StringIO
from pathlib import Path
from unittest import mock

import allauth
import django
from django.core.exceptions import ImproperlyConfigured
from django.core.mail import EmailMessage
from django.test import RequestFactory, SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from config.correo import ServidorCorreoConsola
from config.entorno import entorno_booleano, entorno_lista, entorno_opcion
from config.errores import FiltroInformesErrores

DIRECTORIO_CONFIGURACION = Path(__file__).resolve().parent
AJUSTES_BASE = DIRECTORIO_CONFIGURACION / "settings" / "base.py"
RUTAS = DIRECTORIO_CONFIGURACION / "urls.py"
CATALOGO_PROPIO = DIRECTORIO_CONFIGURACION.parent / "locale" / "es_MX" / "LC_MESSAGES" / "django.po"
VARIABLES_CUENTAS = (
    "CUENTAS_REGISTRO_ABIERTO",
    "CUENTAS_VERIFICACION_CORREO",
    "CUENTAS_DOBLE_FACTOR_ACTIVO",
    "CUENTAS_ADMINISTRACION_EXIGE_DOBLE_FACTOR",
    "CUENTAS_LLAVES_ACCESO_ACTIVAS",
)


def cargar_ajustes_base(**variables: str) -> dict[str, object]:
    """Ejecuta config/settings/base.py con ``variables`` añadidas al entorno.

    Las variables ``CUENTAS_*`` que no se indican quedan vacías, es decir, con su valor por
    defecto, sin importar lo que contenga el archivo .env.
    """
    entorno_prueba = {nombre: "" for nombre in VARIABLES_CUENTAS} | variables
    with mock.patch.dict(os.environ, entorno_prueba):
        return runpy.run_path(str(AJUSTES_BASE))


def cargar_rutas(**ajustes: object) -> list[str]:
    """Ejecuta config/urls.py con ``ajustes`` y devuelve los prefijos de sus rutas."""
    with override_settings(**ajustes):
        rutas = runpy.run_path(str(RUTAS))["urlpatterns"]
    return [str(ruta.pattern) for ruta in rutas]


def leer_msgids(ruta: Path) -> set[str]:
    """Devuelve los msgid sin contexto de un catálogo .po."""
    msgids, actual, clave = set(), {}, None
    for linea in [*ruta.read_text(encoding="utf-8").splitlines(), ""]:
        linea = linea.strip()
        coincidencia = re.match(r'^(msgctxt|msgid|msgid_plural|msgstr(?:\[\d\])?) (".*")$', linea)
        if coincidencia:
            clave = coincidencia.group(1)
            actual[clave] = ast.literal_eval(coincidencia.group(2))
        elif linea.startswith('"') and clave:
            actual[clave] += ast.literal_eval(linea)
        elif not linea and actual:
            if actual.get("msgid") and "msgctxt" not in actual:
                msgids.add(actual["msgid"])
            actual, clave = {}, None
    return msgids


class PruebasPoliticaContenido(TestCase):
    def test_respuestas_incluyen_politica_de_seguridad_de_contenido(self):
        respuesta = self.client.get(reverse("account_login"))
        self.assertEqual(respuesta.status_code, 200)
        politica = respuesta.headers["Content-Security-Policy"]
        self.assertIn("default-src 'self'", politica)
        self.assertIn("frame-ancestors 'none'", politica)


class PruebasEntorno(SimpleTestCase):
    def test_booleano_acepta_valores_habituales(self):
        for valor, esperado in [("true", True), ("1", True), ("off", False), ("No", False)]:
            with self.subTest(valor=valor), mock.patch.dict(os.environ, {"PRUEBA": valor}):
                self.assertIs(entorno_booleano("PRUEBA"), esperado)

    def test_booleano_rechaza_otros_valores(self):
        with mock.patch.dict(os.environ, {"PRUEBA": "quizas"}):
            with self.assertRaisesMessage(ImproperlyConfigured, "PRUEBA"):
                entorno_booleano("PRUEBA")

    def test_variable_vacia_usa_el_valor_por_defecto(self):
        with mock.patch.dict(os.environ, {"PRUEBA": ""}):
            self.assertEqual(entorno_lista("PRUEBA", por_defecto=[]), [])

    def test_opcion_rechaza_valores_fuera_de_la_lista(self):
        with mock.patch.dict(os.environ, {"PRUEBA": "otra"}):
            with self.assertRaisesMessage(ImproperlyConfigured, "PRUEBA"):
                entorno_opcion("PRUEBA", ("una", "dos"))


class PruebasAjustesCuentas(SimpleTestCase):
    def test_valores_por_defecto_son_los_mas_seguros(self):
        ajustes = cargar_ajustes_base()
        self.assertFalse(ajustes["CUENTAS_REGISTRO_ABIERTO"])
        self.assertEqual(ajustes["ACCOUNT_EMAIL_VERIFICATION"], "mandatory")
        self.assertEqual(ajustes["MFA_SUPPORTED_TYPES"], ["totp", "recovery_codes"])
        self.assertTrue(ajustes["CUENTAS_ADMINISTRACION_EXIGE_DOBLE_FACTOR"])
        self.assertFalse(ajustes["MFA_PASSKEY_LOGIN_ENABLED"])
        self.assertTrue(ajustes["ACCOUNT_EMAIL_UNKNOWN_ACCOUNTS"])

    def test_verificacion_de_correo_se_traduce_al_valor_de_allauth(self):
        for valor, esperado in [("opcional", "optional"), ("ninguna", "none")]:
            with self.subTest(valor=valor):
                ajustes = cargar_ajustes_base(CUENTAS_VERIFICACION_CORREO=valor)
                self.assertEqual(ajustes["ACCOUNT_EMAIL_VERIFICATION"], esperado)

    def test_verificacion_de_correo_rechaza_otros_valores(self):
        with self.assertRaisesMessage(ImproperlyConfigured, "CUENTAS_VERIFICACION_CORREO"):
            cargar_ajustes_base(CUENTAS_VERIFICACION_CORREO="mandatory")

    def test_doble_factor_desactivado_no_admite_autenticadores(self):
        ajustes = cargar_ajustes_base(
            CUENTAS_DOBLE_FACTOR_ACTIVO="false",
            CUENTAS_ADMINISTRACION_EXIGE_DOBLE_FACTOR="false",
        )
        self.assertEqual(ajustes["MFA_SUPPORTED_TYPES"], [])

    def test_doble_factor_desactivado_exige_desactivar_lo_que_depende_de_el(self):
        with self.assertRaisesMessage(ImproperlyConfigured, "CUENTAS_DOBLE_FACTOR_ACTIVO"):
            cargar_ajustes_base(CUENTAS_DOBLE_FACTOR_ACTIVO="false")

    def test_llaves_de_acceso_activan_webauthn_y_su_inicio_de_sesion(self):
        ajustes = cargar_ajustes_base(CUENTAS_LLAVES_ACCESO_ACTIVAS="true")
        self.assertIn("webauthn", ajustes["MFA_SUPPORTED_TYPES"])
        self.assertTrue(ajustes["MFA_PASSKEY_LOGIN_ENABLED"])


class PruebasRutas(SimpleTestCase):
    def test_rutas_de_doble_factor_existen_si_esta_activo(self):
        self.assertIn("cuentas/doble-factor/", cargar_rutas(CUENTAS_DOBLE_FACTOR_ACTIVO=True))

    def test_rutas_de_doble_factor_no_existen_si_esta_desactivado(self):
        rutas = cargar_rutas(CUENTAS_DOBLE_FACTOR_ACTIVO=False)
        self.assertNotIn("cuentas/doble-factor/", rutas)


class PruebasInformesErrores(SimpleTestCase):
    def test_filtro_oculta_codigos_y_contrasenas(self):
        peticion = RequestFactory().post("/", {"code": "123456", "password": "x", "otro": "y"})
        parametros = FiltroInformesErrores().get_post_parameters(peticion)
        self.assertNotEqual(parametros["code"], "123456")
        self.assertNotEqual(parametros["password"], "x")
        self.assertEqual(parametros["otro"], "y")


class PruebasCorreoDesarrollo(SimpleTestCase):
    def test_consola_muestra_los_enlaces_completos_y_sin_codificar(self):
        salida = StringIO()
        enlace = "http://localhost:8000/cuentas/confirm-email/" + "a" * 100 + "/"
        mensaje = EmailMessage(
            "Verificación",
            f"Confirme su dirección de correo electrónico: {enlace}\n",
            "remitente@example.com",
            ["destinatario@example.com"],
        )
        ServidorCorreoConsola(stream=salida).send_messages([mensaje])
        texto = salida.getvalue()
        self.assertTrue(any(enlace in linea for linea in texto.splitlines()))
        self.assertIn("electrónico", texto)
        self.assertNotIn("quoted-printable", texto)


class PruebasTraducciones(SimpleTestCase):
    def test_traducciones_propias_corresponden_a_textos_existentes(self):
        # Una entrada cuyo msgid no existe en ninguna biblioteca no corrige nada: suele
        # indicar que la biblioteca cambió el texto original al actualizarse.
        catalogos = [
            *Path(allauth.__file__).parent.glob("locale/es/LC_MESSAGES/django.po"),
            *Path(django.__file__).parent.glob("**/locale/es*/LC_MESSAGES/django.po"),
        ]
        existentes = set().union(*(leer_msgids(catalogo) for catalogo in catalogos))
        self.assertEqual(leer_msgids(CATALOGO_PROPIO) - existentes, set())
