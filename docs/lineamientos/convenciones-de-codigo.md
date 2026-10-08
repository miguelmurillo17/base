# Convenciones de código

Se aplica al código Python, a las plantillas y a los archivos de configuración. Lo que no se
indica aquí sigue PEP 8 y el estilo de código de Django. Las reglas de idioma de los
identificadores y de los textos están en [Autoría y redacción](autoria-y-redaccion.md).

El criterio general: el código nuevo se escribe igual que el código existente que lo rodea.
Antes de agregar un módulo, una clase o una función se revisa cómo resuelve el proyecto un
caso parecido y se sigue el mismo patrón.

## Nombres

| Elemento | Forma | Ejemplo |
|---|---|---|
| Paquetes y módulos | minúsculas con guion bajo | `apps/facturas`, `servicios.py` |
| Clases | sustantivo, palabras con inicial mayúscula | `Factura`, `GestorUsuarios` |
| Funciones y métodos | verbo en infinitivo, minúsculas con guion bajo | `calcular_total`, `enviar_recordatorio` |
| Variables y atributos | sustantivo, minúsculas con guion bajo | `fecha_vencimiento`, `importe_total` |
| Booleanos | afirmación que se lee como verdadera o falsa | `activo`, `pagada`, `tiene_saldo`, `puede_facturar` |
| Constantes de módulo | mayúsculas con guion bajo | `MENSAJE_CORREO_DUPLICADO` |
| Elementos internos de un módulo | prefijo `_` | `_coincide_correo` |

- Las entidades del dominio se nombran en singular (`Factura`) y sus colecciones en plural
  (`facturas`). El mismo nombre se usa en el modelo, la aplicación, las URL, las plantillas
  y las pruebas.
- Sin abreviaturas, salvo las de uso general en el dominio (`rfc`, `iva`, `url`). Se escribe
  `cantidad`, no `cant`; `usuario`, no `usr`.
- Las clases llevan primero su función y después la entidad, en español: `FormularioFactura`,
  `FormularioAltaUsuario`, `GestorFacturas`, `ConsultasFacturas`, `VistaListaFacturas`,
  `PruebasGestorUsuarios`. Por convención de Django, las clases de configuración de
  aplicación y de administración terminan en `Config` y `Admin`: `FacturasConfig`,
  `FacturaAdmin`.
- Vocabulario de las operaciones habituales, siempre con estas palabras:

  | Operación | Palabra | No se usa |
  |---|---|---|
  | Registrar un elemento nuevo | crear | agregar, añadir, nuevo, insertar |
  | Cambiar sus datos | editar | modificar, actualizar, cambiar |
  | Borrarlo de forma definitiva | eliminar | borrar, quitar, remover |
  | Mostrar varios | lista | listado, índice, todos |
  | Mostrar uno | detalle | ver, mostrar, ficha |
  | Desactivarlo sin borrarlo | dar de baja | desactivar, archivar |

  "Alta" se reserva para el registro de cuentas y personas (`FormularioAltaUsuario`,
  `fecha_alta`), en correspondencia con "dar de baja".

## Formato

- Sangría de cuatro espacios, comillas dobles y líneas de hasta 100 caracteres. Los
  comentarios y docstrings se cortan antes, alrededor de 90, para que se lean sin
  desplazamiento.
- En una estructura que ocupa varias líneas (lista, diccionario, llamada con muchos
  argumentos) cada elemento va en su propia línea y el último lleva coma final.
- Interpolación con f-strings, excepto en registros y en textos traducibles, que tienen sus
  propias reglas (ver más abajo).
- Archivos en UTF-8 con fin de línea LF; `.gitattributes` lo aplica en el repositorio.
- Sin código comentado ni importaciones sin usar.
- Ruff aplica el formato y las reglas automatizables de esta guía con la configuración de
  `pyproject.toml`: largo de línea, orden de importaciones, `print`, `except Exception`,
  fechas sin zona horaria, f-strings en registros y código comentado. Las migraciones
  quedan fuera, porque se versionan tal como las genera Django.

## Importaciones

- Tres grupos separados por una línea en blanco, cada uno en orden alfabético: biblioteca
  estándar, bibliotecas de terceros (Django incluido) y módulos del proyecto.
- Dentro de una misma aplicación se usan importaciones relativas (`from .models import
  Factura`). Entre aplicaciones y desde `config`, absolutas (`from apps.facturas.models import
  Factura`).
- El modelo de usuario no se importa directamente: se obtiene con `get_user_model()` y las
  relaciones lo referencian con `settings.AUTH_USER_MODEL`.
- No se usa `import *`, salvo en los módulos de `config/settings/` que extienden `base.py`.

## Anotaciones de tipo

- Las funciones propias que no sobrescriben un método de Django (servicios, utilidades,
  lectura de configuración) llevan anotaciones en parámetros y valor de retorno.
- Los métodos que Django define (`save`, `clean`, `get_queryset`, `form_valid`) conservan la
  firma del framework y no necesitan anotaciones.
- Se usa la sintaxis actual de Python: `list[str]`, `str | None`, sin `typing.List` ni
  `Optional`.

## Docstrings y comentarios

- Cada módulo que no sea uno de los convencionales de Django (`models.py`, `admin.py`,
  `apps.py`, `urls.py`) empieza con un docstring que dice qué contiene y qué reglas sigue.
  Los convencionales lo llevan cuando contienen decisiones que no se deducen del código,
  como el docstring de `apps/cuentas/models.py`.
- Las funciones y clases públicas llevan docstring cuando su comportamiento no se deduce del
  nombre. Empieza con un verbo en tercera persona del presente ("Devuelve", "Calcula") y
  marca los nombres de código con dobles comillas invertidas: ``` ``por_defecto`` ```.
- Los comentarios explican el motivo de una decisión que no es evidente: una restricción de
  una biblioteca, un caso límite, una alternativa descartada y por qué. No repiten lo que el
  código ya dice.

## Errores y excepciones

- Se capturan excepciones concretas. No se usa `except Exception` ni `except:` para ocultar
  un error; si un error se captura para continuar, se registra.
- Al convertir una excepción en otra se encadena con `raise ... from error`, o con
  `from None` cuando la original no aporta información.
- Los datos que captura una persona se validan con `ValidationError` en formularios y en
  `clean` de los modelos, con un mensaje que explica cómo corregirlos.
- Una configuración faltante o inválida lanza `ImproperlyConfigured` con el nombre del
  ajuste, como hace `config/entorno.py`.
- `assert` solo se usa en pruebas, nunca para validar en tiempo de ejecución.

## Registros

- Cada módulo que registra eventos define `logger = logging.getLogger(__name__)`. No se usa
  `print`.
- Los mensajes se escriben con argumentos y no con f-strings, para que el texto se construya
  solo si el nivel está activo: `logger.info("Factura %s timbrada", factura.pk)`.
- Niveles: `DEBUG` para diagnóstico, `INFO` para eventos normales relevantes, `WARNING` para
  situaciones anómalas recuperables, `ERROR` para fallos que requieren atención.
- Los registros no incluyen contraseñas, tokens, claves, datos de pago ni datos personales
  completos. Para identificar un registro se usa su clave primaria.

## Fechas, horas e importes

- La fecha y hora actual se obtiene con `django.utils.timezone.now()` y la fecha local con
  `timezone.localdate()`. No se usan `datetime.now()` ni `date.today()`, que ignoran la zona
  horaria del proyecto.
- Las fechas con hora se guardan con zona horaria (`USE_TZ = True`); la conversión a hora
  local se hace al mostrarlas.
- Los importes se representan con `Decimal` y se guardan en `DecimalField`. No se usa `float`
  para dinero ni cantidades que deben cuadrar.

## Textos visibles

- Los textos que ve una persona usuaria se escriben en español en el código y se marcan con
  `gettext_lazy` (importado como `_`) en modelos, formularios y otros valores que se evalúan
  al cargar el módulo, y con `gettext` dentro de vistas y funciones. Así se usan los
  mecanismos de Django para plurales, formatos y traducciones de bibliotecas.
- Los valores variables se insertan con marcadores con nombre:
  `_("Se eliminó la factura %(folio)s.") % {"folio": factura.folio}`. Los plurales usan
  `ngettext`.
- Los mensajes de error técnicos (excepciones de configuración, comandos de mantenimiento)
  no se marcan para traducción.
