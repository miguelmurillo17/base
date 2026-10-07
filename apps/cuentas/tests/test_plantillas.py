"""Pruebas de las pantallas y correos de cuentas: política de seguridad de contenido,
menú, textos visibles, variantes de botones y estados, y límite de intentos."""

import re
from html.parser import HTMLParser

from allauth.account.models import EmailAddress
from django.conf import settings
from django.core import mail
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from apps.cuentas.templatetags.elementos import obtener_clase_boton, obtener_clase_estado

from .ayudas import CONTRASENA, CORREO, ajustes_predeterminados, crear_usuario, iniciar_sesion

AJUSTES_LLAVES_ACCESO = {
    "ROOT_URLCONF": "apps.cuentas.tests.rutas_llaves_acceso",
    "MFA_SUPPORTED_TYPES": ["totp", "recovery_codes", "webauthn"],
    "MFA_PASSKEY_LOGIN_ENABLED": True,
}
CLASE_BOTON_PRINCIPAL = 'class="boton boton--principal"'
# Marcas del trato de usted. El proyecto trata de tú (docs/lineamientos/diseno-de-interfaz.md).
FORMAS_DE_USTED = re.compile(
    r"\b(usted|ustedes|su|sus|le|les)\b"
    r"|\b(introduzca|ingrese|escriba|confirme|siga|revise|haga|compruebe|póngase|contáctenos"
    r"|comuníquese|verifique|utilice|inténtelo|vuelva|desea|olvidó)\b"
    r"|¿(ha|está|tiene)\b",
    re.IGNORECASE,
)


class ExtractorTexto(HTMLParser):
    """Reúne el texto visible de una página, sin el contenido de scripts ni estilos."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.partes = []
        self._omitir = 0

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style"}:
            self._omitir += 1

    def handle_endtag(self, tag):
        if tag in {"script", "style"}:
            self._omitir -= 1

    def handle_data(self, data):
        if not self._omitir:
            self.partes.append(data)

    @classmethod
    def extraer(cls, html: str) -> str:
        extractor = cls()
        extractor.feed(html)
        return " ".join(" ".join(extractor.partes).split())


class AuditorPoliticaContenido(HTMLParser):
    """Reúne lo que la política de seguridad de contenido del proyecto bloquearía."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.problemas = []
        self.nonces = []

    def handle_starttag(self, tag, attrs):
        atributos = dict(attrs)
        for nombre, valor in attrs:
            if nombre == "style" or nombre.startswith("on"):
                self.problemas.append(f"atributo {nombre} en <{tag}>")
            if nombre in {"href", "src", "action", "formaction"} and (
                (valor or "").strip().lower().startswith("javascript:")
            ):
                self.problemas.append(f"URL javascript: en <{tag}>")
        if tag == "style":
            self.nonces.append(atributos.get("nonce"))
        # Los bloques de datos JSON no se ejecutan y la política no los evalúa.
        es_datos = (atributos.get("type") or "").lower() == "application/json"
        if tag == "script" and "src" not in atributos and not es_datos:
            self.nonces.append(atributos.get("nonce"))


@ajustes_predeterminados
class PruebasPoliticaContenido(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.usuario = crear_usuario()

    def auditar(self, url: str) -> None:
        respuesta = self.client.get(url)
        self.assertEqual(respuesta.status_code, 200, url)
        auditor = AuditorPoliticaContenido()
        auditor.feed(respuesta.content.decode())
        self.assertEqual(auditor.problemas, [], url)
        nonce = re.search(r"'nonce-([^']+)'", respuesta.headers["Content-Security-Policy"])
        for valor in auditor.nonces:
            self.assertIsNotNone(nonce, url)
            self.assertEqual(valor, nonce.group(1), url)

    def test_paginas_de_entrada_cumplen_la_politica_de_contenido(self):
        for nombre in ["account_login", "account_signup", "account_reset_password"]:
            with self.subTest(nombre=nombre):
                self.auditar(reverse(nombre))

    def test_paginas_de_la_cuenta_cumplen_la_politica_de_contenido(self):
        # Inicio de sesión por el formulario: las páginas de doble factor exigen una
        # autenticación reciente registrada en la sesión.
        iniciar_sesion(self.client)
        nombres = [
            "inicio",
            "account_email",
            "account_change_password",
            "mfa_index",
            "mfa_activate_totp",
        ]
        for nombre in nombres:
            with self.subTest(nombre=nombre):
                self.auditar(reverse(nombre))

    def test_pagina_de_correo_con_cambio_pendiente_cumple_la_politica_de_contenido(self):
        EmailAddress.objects.create(user=self.usuario, email="nueva@example.com", verified=False)
        iniciar_sesion(self.client)
        self.auditar(reverse("account_email"))

    @override_settings(**AJUSTES_LLAVES_ACCESO)
    def test_inicio_de_sesion_con_llaves_de_acceso_cumple_la_politica_de_contenido(self):
        self.auditar(reverse("account_login"))


@ajustes_predeterminados
class PruebasMenu(TestCase):
    def test_menu_de_la_cuenta_enlaza_doble_factor_y_cierre_de_sesion(self):
        self.client.force_login(crear_usuario())
        respuesta = self.client.get(reverse("inicio"))
        self.assertContains(respuesta, reverse("mfa_index"))
        self.assertContains(respuesta, f'action="{reverse("account_logout")}"')
        self.assertNotContains(respuesta, reverse("admin:index"))

    @override_settings(CUENTAS_DOBLE_FACTOR_ACTIVO=False)
    def test_menu_sin_doble_factor_omite_su_enlace(self):
        self.client.force_login(crear_usuario())
        self.assertNotContains(self.client.get(reverse("inicio")), reverse("mfa_index"))

    def test_menu_del_personal_enlaza_al_sitio_de_administracion(self):
        self.client.force_login(crear_usuario(is_staff=True))
        self.assertContains(self.client.get(reverse("inicio")), reverse("admin:index"))

    def test_inicio_de_sesion_sin_enlace_de_registro_si_esta_cerrado(self):
        respuesta = self.client.get(reverse("account_login"))
        self.assertNotContains(respuesta, reverse("account_signup"))

    @override_settings(CUENTAS_REGISTRO_ABIERTO=True)
    def test_inicio_de_sesion_con_enlace_de_registro_si_esta_abierto(self):
        respuesta = self.client.get(reverse("account_login"))
        self.assertContains(respuesta, reverse("account_signup"))

    def test_inicio_de_sesion_sin_llaves_de_acceso_por_defecto(self):
        respuesta = self.client.get(reverse("account_login"))
        self.assertNotContains(respuesta, 'id="passkey_login"')
        self.assertNotContains(respuesta, 'id="mfa_login"')

    @override_settings(**AJUSTES_LLAVES_ACCESO)
    def test_inicio_de_sesion_ofrece_llaves_de_acceso_si_estan_activas(self):
        respuesta = self.client.get(reverse("account_login"))
        self.assertContains(respuesta, 'id="passkey_login"')
        self.assertContains(respuesta, 'id="mfa_login"')


@ajustes_predeterminados
class PruebasTextos(TestCase):
    def test_etiquetas_sin_mayusculas_de_titulo_ni_dos_puntos(self):
        respuesta = self.client.get(reverse("account_login"))
        self.assertContains(respuesta, ">Correo electrónico</label>")
        self.assertContains(respuesta, ">Contraseña</label>")

    def test_pagina_de_correo_sin_dos_puntos_en_las_etiquetas(self):
        crear_usuario()
        iniciar_sesion(self.client)
        respuesta = self.client.get(reverse("account_email"))
        self.assertNotRegex(respuesta.content.decode(), r":\s*</label>")

    def test_accion_principal_es_evidente_en_paginas_sin_etiquetas(self):
        respuesta = self.client.get(reverse("account_reset_password"))
        self.assertContains(respuesta, CLASE_BOTON_PRINCIPAL)
        crear_usuario()
        iniciar_sesion(self.client)
        respuesta = self.client.get(reverse("account_change_password"))
        self.assertContains(respuesta, CLASE_BOTON_PRINCIPAL)

    def test_correos_llevan_el_nombre_del_sitio(self):
        crear_usuario()
        self.client.post(reverse("account_reset_password"), {"email": CORREO})
        correo = mail.outbox[0]
        self.assertTrue(correo.subject.startswith(f"[{settings.NOMBRE_SITIO}] "))
        # El correo termina con la firma: nombre del sitio y dominio.
        self.assertEqual(correo.body.rstrip().splitlines()[-2], settings.NOMBRE_SITIO)
        self.assertNotIn("!", correo.body)

    @override_settings(CUENTAS_REGISTRO_ABIERTO=True, ACCOUNT_RATE_LIMITS={"signup": "1/m/ip"})
    def test_limite_de_intentos_usa_la_plantilla_del_proyecto(self):
        datos = {"email": CORREO, "password1": CONTRASENA, "password2": CONTRASENA}
        self.client.post(reverse("account_signup"), datos)
        with self.assertLogs("django.request", "WARNING"):
            respuesta = self.client.post(
                reverse("account_signup"),
                {**datos, "email": "otra@example.com"},
            )
        self.assertEqual(respuesta.status_code, 429)
        self.assertTemplateUsed(respuesta, "429.html")


@ajustes_predeterminados
class PruebasTrato(TestCase):
    def assertTrataDeTu(self, texto: str, origen: str) -> None:
        coincidencia = FORMAS_DE_USTED.search(texto)
        self.assertIsNone(coincidencia, f"{origen}: {coincidencia and coincidencia.group(0)!r}")

    def revisar_pagina(self, url: str) -> None:
        respuesta = self.client.get(url)
        self.assertEqual(respuesta.status_code, 200, url)
        self.assertTrataDeTu(ExtractorTexto.extraer(respuesta.content.decode()), url)

    @override_settings(CUENTAS_REGISTRO_ABIERTO=True)
    def test_paginas_de_entrada_tratan_de_tu(self):
        for nombre in ["account_login", "account_signup", "account_reset_password"]:
            with self.subTest(nombre=nombre):
                self.revisar_pagina(reverse(nombre))

    def test_registro_cerrado_trata_de_tu(self):
        self.revisar_pagina(reverse("account_signup"))

    def test_paginas_de_la_cuenta_tratan_de_tu(self):
        crear_usuario()
        iniciar_sesion(self.client)
        nombres = [
            "inicio",
            "account_email",
            "account_change_password",
            "account_reauthenticate",
            "account_logout",
            "mfa_index",
            "mfa_activate_totp",
        ]
        for nombre in nombres:
            with self.subTest(nombre=nombre):
                self.revisar_pagina(reverse(nombre))

    def test_verificacion_pendiente_trata_de_tu(self):
        crear_usuario(verificado=False)
        respuesta = iniciar_sesion(self.client)
        self.revisar_pagina(respuesta["Location"])
        self.assertTrataDeTu(mail.outbox[0].body, "correo de verificación")

    def test_correos_de_contrasena_y_cuenta_inexistente_tratan_de_tu(self):
        crear_usuario()
        self.client.post(reverse("account_reset_password"), {"email": CORREO})
        self.client.post(reverse("account_reset_password"), {"email": "nadie@example.com"})
        self.assertEqual(len(mail.outbox), 2)
        for correo in mail.outbox:
            self.assertTrataDeTu(f"{correo.subject} {correo.body}", correo.subject)

    @override_settings(CUENTAS_REGISTRO_ABIERTO=True)
    def test_correo_de_cuenta_existente_trata_de_tu(self):
        crear_usuario()
        datos = {"email": CORREO, "password1": CONTRASENA, "password2": CONTRASENA}
        self.client.post(reverse("account_signup"), datos)
        correo = mail.outbox[-1]
        self.assertTrataDeTu(f"{correo.subject} {correo.body}", correo.subject)


class PruebasFiltrosElementos(SimpleTestCase):
    def test_clase_de_boton_segun_etiquetas(self):
        casos = [
            (["prominent", "login"], "submit", "boton--principal"),
            (["delete"], "submit", "boton--peligro"),
            (["prominent", "outline"], "submit", ""),
            (None, "submit", "boton--principal"),
            (None, "button", ""),
        ]
        for etiquetas, tipo, esperada in casos:
            with self.subTest(etiquetas=etiquetas, tipo=tipo):
                self.assertEqual(obtener_clase_boton(etiquetas, tipo), esperada)

    def test_clase_de_estado_segun_etiquetas(self):
        self.assertEqual(obtener_clase_estado(["success"]), "estado--exito")
        self.assertEqual(obtener_clase_estado(["primary"]), "")
        self.assertEqual(obtener_clase_estado(None), "")
