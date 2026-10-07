"""Servidor de correo de consola para desarrollo.

Muestra el cuerpo de los mensajes sin codificar y con cada línea completa, para que los
enlaces de verificación y de restablecimiento se puedan copiar desde la consola. El de
Django usa la codificación quoted-printable, que corta las líneas largas con un signo igual
y vuelve inservibles esos enlaces.
"""

import email.policy

from django.core.mail.backends import console

POLITICA_CONSOLA = email.policy.default.clone(max_line_length=998, cte_type="8bit")


class ServidorCorreoConsola(console.EmailBackend):
    def write_message(self, message):
        mensaje = message.message(policy=POLITICA_CONSOLA)
        self.stream.write(f"{mensaje.as_bytes().decode()}\n")
        self.stream.write("-" * 79 + "\n")
