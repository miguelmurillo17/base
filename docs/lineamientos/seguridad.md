# Seguridad

Reglas que se aplican a todo el código. Las de credenciales y datos privados en el
repositorio están en [`CLAUDE.md`](../../CLAUDE.md) y en
[Autoría y redacción](autoria-y-redaccion.md).

## Acceso

- Toda vista exige sesión iniciada y el permiso de la operación, salvo las declaradas
  públicas de forma explícita (ver [Arquitectura de Django](arquitectura-de-django.md)).
- Los permisos se comprueban en el servidor, en cada vista. Ocultar un botón o un enlace no
  es una medida de acceso.
- Cuando los registros pertenecen a una persona u organización, la vista obtiene el registro
  desde una consulta ya filtrada por ese propietario
  (`get_object_or_404(Factura.objects.filter(cliente=...), pk=pk)`), nunca solo por su clave
  primaria. Si el registro no le pertenece, la respuesta es 404, para no revelar que existe.
- El sitio de administración se reserva al personal técnico y usa el mismo inicio de sesión
  que el resto del sitio, de modo que no evita el segundo factor de autenticación.

## Datos de entrada

- Todo dato que llega de la petición (formularios, parámetros de la URL, encabezados, campos
  ocultos) se valida con un formulario de Django antes de usarse.
- Las redirecciones a una dirección recibida en la petición, como el parámetro `next`, se
  validan con `url_has_allowed_host_and_scheme`.
- Los archivos subidos se validan por tamaño y por tipo según su contenido, no solo por su
  extensión; se guardan en `MEDIA_ROOT` con un nombre generado por el sistema y nunca en los
  directorios de archivos estáticos. Los archivos con datos confidenciales se entregan
  mediante una vista que comprueba el permiso, no como archivos públicos.

## Datos de salida

- Las plantillas conservan el escapado automático. El HTML que se construye en Python usa
  `format_html`; `mark_safe` y `|safe` no se aplican a datos capturados por una persona.
- Las respuestas JSON se generan con `JsonResponse`, no concatenando texto.

## Política de seguridad de contenido

La política (`SECURE_CSP` en `config/settings/base.py`) solo permite recursos del propio
sitio en todos los entornos. La única excepción es `img-src data:`, para el código QR que
django-allauth genera como imagen al activar la aplicación de autenticación. En
consecuencia:

- No se cargan scripts, hojas de estilo ni fuentes desde CDN u otros dominios. Las
  bibliotecas de cliente se sirven como archivos estáticos del proyecto.
- No se usan atributos `style` ni manejadores de eventos en el HTML (`onclick`,
  `onsubmit`). Los estilos van en hojas de estilo y el comportamiento, en archivos
  JavaScript que registran sus eventos.
- Un bloque `<script>` o `<style>` en línea solo se admite si es indispensable y lleva
  `nonce="{{ csp_nonce }}"`.
- Ampliar la política es una decisión del proyecto: se hace en un commit propio que explica
  qué recurso la necesita y por qué no puede servirse desde el sitio.

## Peticiones que modifican datos

- Todo formulario que envía `POST` incluye `{% csrf_token %}`. No se usa `csrf_exempt`,
  salvo en puntos de entrada para sistemas externos que verifican una firma propia.
- Las peticiones `fetch` desde JavaScript envían el token CSRF en el encabezado
  `X-CSRFToken`.

## Base de datos

- Sin SQL construido con interpolación de cadenas; ver [Modelos y datos](modelos-y-datos.md).
- Los respaldos y volcados de bases de datos no se versionan ni se comparten fuera de los
  canales del proyecto.

## Registros y errores

- Los registros no incluyen contraseñas, tokens, claves, datos de pago ni datos personales
  completos.
- Las páginas de error que ve una persona usuaria no muestran detalles técnicos. `DEBUG`
  solo está activo en `config/settings/dev.py`.

## Configuración y dependencias

- Todo cambio en los ajustes de seguridad o en `config/settings/prod.py` se revisa con el
  comando `check --deploy` indicado en `CLAUDE.md`, que debe terminar sin advertencias.
- Los límites de intentos de inicio de sesión necesitan, en producción, una caché compartida
  entre procesos y la dirección IP real de la persona cuando el sitio está detrás de un
  proxy.
- Las versiones de seguridad de las dependencias se aplican en cuanto se publican, según
  [Stack tecnológico](stack-tecnologico.md).
