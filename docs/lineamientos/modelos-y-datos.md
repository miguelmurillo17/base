# Modelos y datos

Reglas para definir modelos, consultar la base de datos y escribir migraciones. La base de
datos es PostgreSQL en todos los entornos, así que se pueden usar sus funciones cuando
aportan, sin mantener compatibilidad con otros motores.

## Modelos

- El nombre del modelo es un sustantivo en singular (`Factura`, `LineaFactura`). Se conserva
  el nombre de tabla que asigna Django; `db_table` solo se define para tablas que ya existen.
- Cada campo lleva su nombre visible en español, en minúsculas y traducible, como primer
  argumento: `models.DateField(_("fecha de vencimiento"))`. Se agrega `help_text` cuando el
  significado o el efecto del campo no es evidente.
- `Meta` declara siempre `verbose_name` y `verbose_name_plural`. Declara `ordering` cuando
  las listas necesitan un orden estable y las restricciones e índices del modelo.
- Cada modelo define `__str__` con un texto que identifica al registro para una persona
  (folio, nombre), no la clave primaria.
- Los campos de fecha se nombran con el prefijo `fecha_` (`fecha_alta`, `fecha_vencimiento`).
- Orden dentro de la clase: campos, gestor (`objects`), constantes de Django
  (`USERNAME_FIELD`), `Meta`, `__str__`, `clean`, `save` y después los métodos propios.

## Tipos de campo

- Los campos de texto no usan `null=True`: un texto vacío se guarda como cadena vacía.
- Los importes usan `DecimalField` con `max_digits` y `decimal_places` explícitos.
- Las opciones fijas se definen con `models.TextChoices` dentro del modelo o en el mismo
  módulo. El valor guardado es estable, en minúsculas y ASCII (`"pendiente"`); la etiqueta
  es el texto visible y traducible.
- Cuando un registro debe identificarse en una URL accesible sin sesión o compartida con
  terceros, se agrega un campo `UUIDField` único para ese uso y la clave primaria no se
  expone.

## Relaciones

- `on_delete` se elige según el significado de la relación:
  - `PROTECT` por defecto, para registros con valor propio que no deben desaparecer en
    cadena (un cliente con facturas).
  - `CASCADE` solo para partes que no existen sin su contenedor (las líneas de una factura).
  - `SET_NULL`, con `null=True`, cuando la relación es opcional y el registro debe
    conservarse.
- Cada relación declara `related_name` en español y en plural: `cliente.facturas`.
- Las relaciones con el usuario usan `settings.AUTH_USER_MODEL`.

## Bajas e historial

- Los registros que tienen historial o que otros registros referencian se dan de baja con un
  campo booleano (`activo`, o `is_active` en el modelo de usuario) en lugar de eliminarse.
  Las listas y los selectores muestran solo los activos.
- La eliminación definitiva se reserva para registros sin referencias ni valor histórico, y
  la pantalla correspondiente pide confirmación.

## Integridad

- Las reglas que deben cumplirse siempre se garantizan en la base de datos con
  `unique=True`, `UniqueConstraint` o `CheckConstraint`, además de validarse en el
  formulario. La validación del formulario da el mensaje claro; la restricción protege
  frente a escrituras que no pasan por él.
- Las restricciones se nombran `<aplicacion>_<modelo>_<descripcion>`
  (`cuentas_usuario_correo_unico`) y declaran `violation_error_message` en español.
- La unicidad sin distinguir mayúsculas se define sobre `Lower(<campo>)`, como en el modelo
  `Usuario`. Las búsquedas que deben usar ese índice comparan con la misma expresión y no
  con `__iexact`.

## Consultas

- Las consultas se escriben con el ORM. Si hace falta SQL directo, los valores se pasan como
  parámetros, nunca interpolados en la cadena.
- Las listas que muestran datos de relaciones usan `select_related` (claves foráneas) o
  `prefetch_related` (relaciones múltiples) para no lanzar una consulta por fila.
- Para saber si hay resultados se usa `exists()`; para contarlos, `count()`. No se cargan
  registros solo para eso.
- Los cambios que dependen del valor actual de un campo, como contadores o saldos, se hacen
  con expresiones `F()` en la base de datos, o con `select_for_update()` dentro de una
  transacción cuando la operación necesita leer antes de escribir.

## Transacciones

- Una operación que escribe en varias tablas se ejecuta dentro de `transaction.atomic()`,
  normalmente en el servicio que la implementa.
- Los efectos externos que dependen de que los datos se guarden, como enviar un correo, se
  programan con `transaction.on_commit()` para que no ocurran si la transacción se revierte.

## Migraciones

- Se generan con `python manage.py makemigrations` y se versionan en el mismo commit que el
  cambio de modelo que las origina.
- Después de la inicial, cada migración lleva un nombre descriptivo en español con
  `--name`: `0002_agregar_fecha_vencimiento`.
- Una migración que ya está en la rama principal no se edita: los errores se corrigen con una
  migración nueva. Las de una rama en desarrollo se pueden regenerar antes de integrarla.
- Las migraciones de datos usan `RunPython` con los modelos históricos (`apps.get_model`),
  nunca importando los modelos del código, e incluyen la función inversa. Si la operación no
  puede revertirse, se indica en un comentario por qué.
- Eliminar un campo o un modelo con datos se hace en dos pasos: primero se deja de usar en el
  código y en una entrega posterior se elimina de la base de datos.
- Antes de dar un cambio por terminado no debe haber migraciones pendientes:
  `python manage.py makemigrations --check --dry-run`.
