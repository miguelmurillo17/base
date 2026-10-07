# Lineamientos

Convenciones que siguen todos los proyectos creados a partir de esta plantilla. Se aplican
por igual a quien desarrolla y a los agentes de IA que colaboran en el código. En Claude
Code, el archivo [`CLAUDE.md`](../../CLAUDE.md) de la raíz importa estos documentos para que
formen parte del contexto de cada sesión.

| Documento | Alcance |
|---|---|
| [Autoría y redacción](autoria-y-redaccion.md) | Commits, pull requests, comentarios y documentación |
| [Diseño de interfaz](diseno-de-interfaz.md) | Criterios visuales, textos de interfaz y accesibilidad |
| [Stack tecnológico](stack-tecnologico.md) | Lenguaje, frameworks, base de datos, dependencias y política de versiones |
| [Convenciones de código](convenciones-de-codigo.md) | Nombres, formato, importaciones, errores, registros y textos visibles |
| [Arquitectura de Django](arquitectura-de-django.md) | Aplicaciones, ubicación de la lógica, rutas, vistas, formularios, plantillas y configuración |
| [Modelos y datos](modelos-y-datos.md) | Modelos, relaciones, integridad, consultas, transacciones y migraciones |
| [Pruebas](pruebas.md) | Cuándo y cómo se escriben, nombran, aíslan y ejecutan las pruebas |
| [Seguridad](seguridad.md) | Acceso, datos de entrada y salida, política de seguridad de contenido y registros |
| [Flujo de trabajo](flujo-de-trabajo.md) | Alcance de un cambio, ramas, documentación y verificación antes de terminar |

## Cómo agregar o modificar un lineamiento

- Un tema por archivo, con el nombre en minúsculas, sin tildes ni ñ, y las palabras
  separadas por guiones (por ejemplo, `diseno-de-interfaz.md`).
- Las reglas se escriben en forma directa y verificable. Cuando el motivo no es evidente, se
  explica en una línea.
- Cada documento nuevo se agrega a la tabla anterior y a la lista de importaciones de
  `CLAUDE.md`.
- Las reglas son generales: lo que solo atañe a un proyecto concreto se documenta en ese
  proyecto, no en la plantilla.
