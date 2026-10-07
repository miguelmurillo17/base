# Pruebas

Las pruebas usan el ejecutor de Django (`django.test`) sobre PostgreSQL, el mismo motor que
en producción.

## Cuándo se escriben

- Todo cambio de comportamiento llega con pruebas que lo cubren, en el mismo commit.
- La corrección de un error incluye una prueba que falla sin la corrección.
- Las pruebas verifican el comportamiento observable (lo que devuelve una función, lo que se
  guarda, lo que responde una vista), no los detalles internos de la implementación.

## Ubicación y nombres

- Las pruebas de una aplicación están en `apps/<aplicacion>/tests.py`. Cuando crece, se
  convierte en el paquete `tests/` con un módulo por tema: `test_modelos.py`,
  `test_formularios.py`, `test_vistas.py`, `test_servicios.py`.
- Las clases se nombran `Pruebas<Tema>` (`PruebasGestorUsuarios`) y heredan de `TestCase`, o
  de `SimpleTestCase` cuando no usan la base de datos.
- Cada método describe en español el caso y el resultado esperado, después del prefijo
  `test_` que exige el ejecutor: `test_crear_usuario_guarda_el_correo_en_minusculas`,
  `test_lista_de_facturas_exige_sesion`.
- Cada prueba verifica un solo comportamiento.

## Datos de prueba

- Los datos son ficticios. Los correos usan dominios reservados como `example.com` y los
  nombres no corresponden a personas reales identificables.
- Los valores que se repiten en un módulo se definen una vez como constantes al inicio
  (`CONTRASENA`, `MENSAJE_DUPLICADO`).
- Los datos que comparten todas las pruebas de una clase se crean en `setUpTestData`; los que
  cada prueba modifica, en `setUp` o en la propia prueba.
- Los registros se crean con los gestores del modelo o con funciones auxiliares del módulo de
  pruebas, no con archivos de datos (`fixtures`). No se agregan bibliotecas de generación de
  datos sin una decisión del proyecto.

## Qué se prueba en cada capa

- **Modelos y gestores**: valores por defecto, normalización, `clean`, restricciones de la
  base de datos y métodos propios.
- **Formularios**: datos válidos, cada regla de validación y el mensaje de error que produce.
- **Vistas**: respuesta a una persona sin sesión (redirige al inicio de sesión), a una sin
  permiso (403, o 404 si el registro no le pertenece) y a una con permiso; la plantilla
  usada; la redirección y el mensaje después de un `POST` correcto; y que un `GET` no
  modifica datos.
- **Servicios**: el resultado, los registros afectados y la reversión completa cuando una
  parte de la operación falla.
- **Configuración**: los ajustes de seguridad que el proyecto debe mantener, como la
  política de seguridad de contenido de `config/tests.py`.
- Las listas que cargan relaciones incluyen una prueba con `assertNumQueries` que impide que
  el número de consultas crezca con el número de filas.

## Aislamiento

- Las pruebas no acceden a la red ni a servicios externos. Las llamadas a sistemas externos
  se sustituyen con `unittest.mock` en el punto donde el proyecto las hace.
- El correo enviado se revisa en `django.core.mail.outbox`, que Django usa durante las
  pruebas.
- Las pruebas que dependen de la fecha u hora la fijan, en lugar de depender del momento en
  que se ejecutan.
- Ninguna prueba depende del orden de ejecución ni de datos que deja otra prueba.

## Ejecución

- Todas las pruebas: `python manage.py test`. Una aplicación: `python manage.py test
  apps.facturas`. Una clase o un método, con su ruta completa.
- Requieren PostgreSQL en ejecución (`docker compose up -d --wait`).
- Antes de dar un cambio por terminado se ejecuta el conjunto completo, no solo las pruebas
  de la aplicación modificada.
