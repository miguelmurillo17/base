# Arquitectura de Django

Cómo se organiza un proyecto creado a partir de esta plantilla: dónde va cada pieza de
código, cómo se nombran las rutas y las plantillas, y cómo se agrega configuración.

## Distribución del repositorio

| Ubicación | Contenido |
|---|---|
| `apps/<aplicacion>/` | Cada aplicación de Django del proyecto |
| `config/` | Configuración global: ajustes, rutas principales, sitio de administración, procesadores de contexto, renderizador de formularios y puntos de entrada WSGI y ASGI |
| `config/settings/` | `base.py` con lo común, `dev.py` y `prod.py` con lo propio de cada entorno |
| `templates/` | Plantilla base y plantillas compartidas por varias aplicaciones, o que reemplazan las de una biblioteca |
| `static/` | Archivos estáticos compartidos; al crearlo se agrega a `STATICFILES_DIRS` |
| `scripts/` | Utilidades del repositorio que no necesitan cargar Django |
| `docs/` | Documentación del proyecto |

## Aplicaciones

- Una aplicación agrupa un área del negocio con sus modelos, pantallas y reglas (`cuentas`,
  `facturas`, `inventario`), no un tipo de archivo ni una capa técnica. No se crean
  aplicaciones `core`, `common` o `utils`.
- El nombre es un sustantivo en español, en minúsculas y en ASCII, normalmente en plural.
- Se crea con `python manage.py startapp <aplicacion> apps/<aplicacion>`, después de crear el
  directorio. Su `AppConfig` sigue el patrón de `apps/cuentas/apps.py`: `name =
  "apps.<aplicacion>"`, `label = "<aplicacion>"` y `verbose_name` traducible.
- En `INSTALLED_APPS` van primero las aplicaciones de Django, después las de terceros y al
  final las del proyecto.
- Las dependencias entre aplicaciones van en un solo sentido y no forman ciclos. Si dos
  aplicaciones necesitan importarse mutuamente, el límite entre ellas está mal trazado.

## Módulos de una aplicación

| Módulo | Contenido |
|---|---|
| `models.py` | Modelos, sus gestores y sus `QuerySet` |
| `servicios.py` | Operaciones del negocio que no pertenecen a un solo modelo |
| `forms.py` | Formularios |
| `views.py` | Vistas |
| `urls.py` | Rutas de la aplicación, con `app_name` |
| `admin.py` | Registro en el sitio de administración |
| `templates/<aplicacion>/` | Plantillas de la aplicación |
| `static/<aplicacion>/` | Archivos estáticos de la aplicación |
| `management/commands/` | Comandos de mantenimiento, con nombre en español (`importar_clientes`) |
| `tests.py` o `tests/` | Pruebas (ver [Pruebas](pruebas.md)) |

Cuando un módulo crece hasta mezclar temas distintos, se convierte en un paquete con un
archivo por tema (`models/facturas.py`, `models/pagos.py`) y su `__init__.py` reexporta lo
público, de modo que las importaciones existentes no cambian.

## Dónde va la lógica

- **Modelo**: las reglas que dependen solo de los datos de una instancia, como propiedades
  calculadas, `clean` y métodos que cambian su propio estado.
- **`QuerySet` y gestor**: las consultas que se repiten, con nombre propio
  (`Factura.objects.vencidas()`), en lugar de repetir filtros en las vistas.
- **Servicio**: las operaciones que modifican varios modelos, necesitan una transacción,
  envían correo o llaman a un sistema externo. Son funciones con nombre en infinitivo
  (`timbrar_factura`) que reciben sus datos como parámetros, sin depender de la petición.
- **Formulario**: la validación de los datos de entrada.
- **Vista**: comprueba el acceso, valida con el formulario, llama al modelo o al servicio y
  devuelve la respuesta. No contiene reglas del negocio.
- **Plantilla**: presentación. Sin consultas ni reglas del negocio.

Las señales de Django no se usan para la lógica propia, porque ocultan el orden en que
ocurren los efectos. Se reservan para reaccionar a eventos de Django o de bibliotecas de
terceros cuando no hay otro punto de extensión.

## Rutas

- Cada aplicación declara `app_name = "<aplicacion>"` en su `urls.py` y se incluye en
  `config/urls.py` con un prefijo igual a su nombre:
  `path("facturas/", include("apps.facturas.urls"))`.
- Los segmentos de las rutas van en español, en minúsculas, en ASCII, separados por guiones y
  terminados en barra: `facturas/<int:pk>/editar/`, `facturas/notas-de-credito/`.
- Los nombres de ruta son la operación, dentro del espacio de nombres de la aplicación:
  `facturas:lista`, `facturas:detalle`, `facturas:crear`, `facturas:editar`,
  `facturas:eliminar`.
- Las rutas se generan con `reverse()`, `redirect()` o `{% url %}`. No se escriben URL fijas
  en el código ni en las plantillas.

## Vistas

- Las pantallas de lista, detalle, creación, edición y eliminación usan las vistas genéricas
  de Django. Un flujo que no encaja en una vista genérica, o que obligaría a sobrescribir
  varios de sus métodos, se escribe como función.
- Las vistas basadas en clases se nombran `Vista<Operación><Entidad>`
  (`VistaListaFacturas`, `VistaEditarFactura`) y las funciones, con la operación en
  infinitivo (`timbrar_factura`).
- Toda vista exige sesión iniciada y el permiso que corresponde a la operación, con
  `LoginRequiredMixin` y `PermissionRequiredMixin` o sus decoradores equivalentes. Una vista
  pública lo es por decisión explícita y su docstring lo indica.
- Una petición `GET` nunca modifica datos. Una petición `POST` que termina bien redirige a
  otra página y deja un mensaje con el framework de mensajes de Django.
- Las listas se paginan.
- Las vistas genéricas declaran `template_name` explícito, porque los nombres de plantilla
  del proyecto están en español (ver más abajo).

## Formularios

- Los formularios de modelo declaran la lista explícita de campos en `fields`. No se usan
  `fields = "__all__"` ni `exclude`, para que un campo nuevo del modelo no quede expuesto
  sin decidirlo. Los formularios del sitio de administración pueden usar `"__all__"`,
  porque reproducen los de Django.
- Las validaciones de un campo van en `clean_<campo>` y las que involucran varios campos, en
  `clean`.
- Los formularios se muestran con las plantillas de formulario comunes del proyecto, según
  [Diseño de interfaz](diseno-de-interfaz.md).

## Plantillas

- La plantilla base del proyecto está en `templates/` y todas las pantallas la extienden.
- Las plantillas de una aplicación están en `apps/<aplicacion>/templates/<aplicacion>/` y se
  nombran por la operación: `lista.html`, `detalle.html`, `formulario.html` (para crear y
  editar), `eliminar.html`. Los fragmentos que se incluyen en otras plantillas van en un
  subdirectorio `fragmentos/`.
- Los nombres de bloques y de variables de contexto propios van en español. Se conservan los
  que exige Django o una biblioteca, como `object_list`, `page_obj` o los bloques de las
  plantillas que se reemplazan.
- Sin estilos ni scripts en línea: el CSS y el JavaScript van en archivos estáticos y se
  enlazan con `{% static %}`. Cuando un bloque en línea es inevitable, lleva el atributo
  `nonce="{{ csp_nonce }}"` (ver [Seguridad](seguridad.md)).
- No se desactiva el escapado automático. `|safe` y `mark_safe` solo se aplican a contenido
  que genera el propio código, nunca a datos capturados por una persona.

## Configuración

- Un ajuste nuevo va en `config/settings/base.py`. Solo va en `dev.py` o `prod.py` si su
  valor difiere entre entornos.
- Los valores secretos o que cambian entre instalaciones se leen con las funciones de
  `config/entorno.py` (`entorno`, `entorno_booleano`, `entorno_entero`, `entorno_lista`,
  `entorno_opcion`). No
  se lee `os.environ` en otros módulos.
- Cada variable de entorno nueva se agrega a `.env.example` en la sección que le corresponde,
  con un comentario que explica su efecto y sus valores válidos, y con un valor de ejemplo
  ficticio.
- Las variables de entorno de ajustes de Django llevan el prefijo `DJANGO_` y las de la base
  de datos, `POSTGRES_`. Los ajustes propios del proyecto se nombran en español y en
  mayúsculas (`NIVEL_REGISTRO`).
- Una función opcional del proyecto se activa con un ajuste booleano leído del entorno. Su
  valor por defecto es el más seguro, y el comportamiento con el ajuste activo y desactivado
  queda cubierto por pruebas.
