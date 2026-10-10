# Seguridad

Reglas que se aplican a todo el código. Las de credenciales y datos privados en el
repositorio están en [`CLAUDE.md`](../../CLAUDE.md) y en
[Autoría y redacción](autoria-y-redaccion.md).

Las medidas se aplican con los mismos mecanismos en desarrollo y en producción, para que
cualquier problema aparezca antes del despliegue. Entre entornos solo cambian los valores,
como `DEBUG` o los ajustes que dependen de HTTPS, que están en `config/settings/prod.py`.

## Acceso

- Toda vista exige sesión iniciada: `LoginRequiredMiddleware` la exige por defecto, de modo
  que una vista nueva queda protegida aunque no lo declare. Las vistas públicas se marcan
  con `@login_not_required` (ver [Arquitectura de Django](arquitectura-de-django.md)).
- Toda vista exige además el permiso de la operación. Los permisos se comprueban en el
  servidor, en cada vista, tanto al mostrar una pantalla como al procesar el `POST` que la
  envía. Ocultar un botón o un enlace no es una medida de acceso.
- Cuando los registros pertenecen a una persona u organización, la vista obtiene el registro
  desde una consulta ya filtrada por ese propietario
  (`get_object_or_404(Factura.objects.filter(cliente=...), pk=pk)`), nunca solo por su clave
  primaria. Si el registro no le pertenece, la respuesta es 404, para no revelar que existe.
- El sitio de administración se reserva al personal técnico y usa el mismo inicio de sesión
  que el resto del sitio, de modo que no evita el segundo factor de autenticación.
- Las herramientas de diagnóstico, como barras de depuración o perfiladores, se instalan y
  se enrutan solo en `config/settings/dev.py`. Un punto de entrada para comprobar que el
  servicio está en marcha no revela versiones, configuración ni datos.

## Secretos

- Las claves de API, contraseñas y tokens solo existen en el servidor y se leen de variables
  de entorno. El navegador nunca recibe una clave: cuando la interfaz necesita un servicio
  externo, como un modelo de IA, llama a una vista de Django y es el servidor el que llama
  al servicio.
- Ningún secreto va en archivos estáticos, en plantillas ni en las variables que se
  incorporan al compilar el código de cliente, porque todo eso llega al navegador.
- Los archivos `.env` no se versionan; solo `.env.example`, con valores ficticios. En la
  plataforma que aloja el repositorio se activa el escaneo de secretos, que rechaza los
  envíos con claves reconocibles.

## Límites de intentos

- Los límites de intentos de django-allauth (inicio de sesión, registro, restablecimiento de
  contraseña, códigos de verificación y reenvío de correos) se mantienen activos en todos
  los entornos. Las pruebas que los necesitan distintos los ajustan con
  `override_settings`.
- Las vistas que consumen un servicio externo con costo, como un modelo de IA, o que hacen
  operaciones costosas limitan el número de peticiones por usuario. El conteo se guarda en
  la caché compartida del proyecto, y al exceder el límite la respuesta es 429.
- El límite general de peticiones por dirección IP se aplica en el proxy inverso de
  producción, no en Django.
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

- PostgreSQL no es accesible desde internet: en desarrollo solo escucha en el propio
  equipo y en producción solo en la red privada del servicio.
- La aplicación se conecta con un rol propietario de su base de datos, sin los privilegios
  `SUPERUSER`, `CREATEDB` ni `CREATEROLE`.
- Los datos solo se exponen a través de vistas que comprueban sesión y permisos. No se
  publican interfaces generadas automáticamente sobre las tablas; si un proyecto agrega una
  API, su permiso por defecto exige sesión iniciada. Un modelo aparece en el sitio de
  administración solo si se registra de forma explícita.
- No se usa la seguridad por filas de PostgreSQL (RLS): el navegador nunca consulta la base
  de datos, y el aislamiento entre propietarios se garantiza con consultas filtradas en
  cada vista. Un proyecto que comparte la base de datos entre organizaciones con
  requisitos estrictos de aislamiento puede adoptarla como decisión propia.
- Sin SQL construido con interpolación de cadenas; ver [Modelos y datos](modelos-y-datos.md).
- Los respaldos y volcados de bases de datos no se versionan ni se comparten fuera de los
  canales del proyecto.

## Registros y errores

- Los registros no incluyen contraseñas, tokens, claves, datos de pago ni datos personales
  completos.
- Las páginas de error que ve una persona usuaria no muestran detalles técnicos. `DEBUG`
  solo está activo en `config/settings/dev.py`, y las páginas 400, 403, 404 y 500 son
  plantillas propias del proyecto.
- El texto de una excepción no se muestra en mensajes, páginas ni respuestas JSON: se
  registra, y la persona recibe un mensaje que explica qué hacer.

## Registro de auditoría

- Los eventos de seguridad de las cuentas se registran en `apps/cuentas/auditoria.py`:
  inicios y cierres de sesión, intentos fallidos, códigos de verificación rechazados,
  cambios de contraseña y de correo, y cambios en la autenticación de dos factores. Las
  acciones del sitio de administración quedan en su propio historial.
- Cada registro identifica a la persona por la clave primaria de su usuario y a la
  petición por su dirección IP. Nunca incluye el correo ni las credenciales recibidas.
- Un evento de seguridad nuevo, como un cambio de permisos fuera del sitio de
  administración, se registra en ese mismo módulo.
- En producción, los registros se conservan en el sistema que recoge la salida del
  servicio durante el plazo que fije la política de privacidad del proyecto, porque la
  dirección IP es un dato personal.

## Configuración y dependencias

- Todo cambio en los ajustes de seguridad o en `config/settings/prod.py` se revisa con el
  comando `check --deploy` indicado en el `README.md`, que debe terminar sin advertencias.
- Los límites de intentos de inicio de sesión necesitan, en producción, una caché compartida
  entre procesos y la dirección IP real de la persona cuando el sitio está detrás de un
  proxy.
- Las versiones de seguridad de las dependencias se aplican en cuanto se publican, según
  [Stack tecnológico](stack-tecnologico.md).
