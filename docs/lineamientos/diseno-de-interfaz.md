# Diseño de interfaz

Las interfaces de los proyectos creados a partir de esta plantilla son herramientas de
trabajo: formularios, listados, tableros y flujos administrativos. Deben leerse rápido,
usarse sin explicación y verse consistentes entre pantallas. La sobriedad es una decisión de
diseño deliberada.

## Recursos que no se usan

Estos recursos se volvieron el sello de las interfaces generadas automáticamente: hacen que
una pantalla se vea genérica y agregan ruido sin aportar información.

- Píldoras, chips o insignias (fondo o borde redondeado alrededor de una palabra o cifra)
  para resaltar texto, estados, categorías, contadores o novedades como "Nuevo" o "Beta", en
  cualquier color. Solo se admiten como control interactivo que muestra un valor
  seleccionado que se puede quitar, como un filtro activo.
- Emojis o símbolos usados como íconos (marcas de verificación, cruces, estrellas, flechas
  decorativas) en cualquier parte: títulos, botones, mensajes, estados vacíos o
  notificaciones.
- Íconos decorativos junto a cada título, tarjeta o elemento de lista.
- Degradados de color en fondos, botones o texto.
- Tarjetas anidadas, sombras pronunciadas y esquinas muy redondeadas como estilo por defecto.
- Bordes laterales de color para destacar bloques de contenido.
- Efectos de vidrio, brillos, destellos y animaciones que no comunican un cambio de estado.
  Esto incluye el ícono de "chispas" para señalar funciones con IA.
- Secciones de portada con títulos enormes, texto centrado y llamados a la acción de
  marketing en pantallas de trabajo.
- Mosaicos de métricas con cifras gigantes cuando el dato no requiere esa prominencia.
- Etiquetas en mayúsculas con espaciado amplio sobre los títulos.
- Cuadrículas de tarjetas como formato por defecto para listados de registros; los listados
  se muestran como tablas o listas.
- Textos de tono publicitario: "Potencia tu productividad", "Todo en un solo lugar",
  "¡Comencemos!".

## Principios

### Jerarquía y composición

- La jerarquía se construye con tamaño, peso tipográfico y espacio, no con color.
- Una sola acción principal por pantalla o sección.
- Texto y formularios alineados a la izquierda. Se centran solo elementos aislados, como un
  diálogo de confirmación.
- Espaciado basado en una escala fija (por ejemplo, múltiplos de 4 px).
- Las regiones se separan con espacio o bordes finos, no con sombras.
- Radio de esquinas pequeño y uniforme en todos los componentes.

### Color

- Paleta restringida: neutros para casi toda la interfaz y un único color de acento para la
  acción principal, los enlaces y el foco.
- Los colores semánticos (error, advertencia, éxito, información) se usan solo para comunicar
  ese significado, nunca como decoración.
- Los colores se definen como variables en un solo lugar. Los componentes no llevan valores
  hexadecimales sueltos.
- Si el proyecto usa un framework CSS o una biblioteca de componentes, sus valores por
  defecto de color, radio, sombra y tipografía se sustituyen por las variables del proyecto.
  El color de acento se elige para el proyecto; no se hereda de la biblioteca.
- Contraste mínimo WCAG 2.2 nivel AA: 4.5:1 para texto normal y 3:1 para texto grande y
  componentes de interfaz.
- El significado nunca depende solo del color; siempre se acompaña de texto.

### Tipografía

- Una sola familia tipográfica, o la pila de fuentes del sistema, para toda la interfaz. Una
  monoespaciada solo para código o identificadores.
- Escala tipográfica corta (cuatro o cinco tamaños) y aplicada de forma consistente.
- Cifras tabulares en tablas y columnas numéricas.
- Mayúsculas solo donde la ortografía las exige, también en títulos y botones: no se escribe
  cada palabra con mayúscula inicial.

### Íconos

- Un único conjunto de íconos en todo el proyecto, con trazo y tamaño uniformes.
- Un ícono aparece solo si ayuda a reconocer una acción (editar, eliminar, buscar), un
  destino de navegación o el estado de un registro. Nunca como adorno.
- Los botones que solo muestran un ícono llevan una etiqueta accesible (`aria-label`).

### Estados de registros

- El estado de un registro (por ejemplo, "Pendiente" o "Pagado") se muestra como texto,
  opcionalmente acompañado de un indicador pequeño (punto o ícono) en el color semántico.
- Sin fondo, borde ni forma de píldora.

### Formularios

- Etiqueta visible siempre, encima del campo. El texto de ejemplo (`placeholder`) no la
  sustituye.
- Los errores se muestran junto al campo que los provoca, con texto que explica cómo
  corregirlos. Si hay varios, se agrega un resumen al inicio del formulario.
- Los campos obligatorios u opcionales se marcan con el mismo criterio en todo el proyecto.
- Los formularios de Django se renderizan con las plantillas de formulario comunes del
  proyecto, no con estilos definidos pantalla por pantalla.

### Textos de interfaz

- Botones con verbos que describen la acción concreta: "Guardar cambios", "Eliminar
  factura". Se evitan "Aceptar" u "OK" cuando la acción tiene nombre propio.
- Los estados vacíos explican qué falta y cuál es la siguiente acción, sin ilustraciones ni
  emojis.
- Los mensajes de error dicen qué pasó y cómo resolverlo, sin culpar a quien usa el sistema
  y sin códigos técnicos sin explicación.
- Se trata de tú a la persona usuaria en todas las pantallas, mensajes y correos: "Revisa
  tu correo", no "Revise su correo". Los textos de Django y de las bibliotecas que usan
  usted se reemplazan en las traducciones propias del proyecto.
- Sin signos de exclamación.

### Movimiento

- Transiciones breves, de 200 ms o menos, y solo para comunicar un cambio de estado, como
  abrir o cerrar un menú. La única animación continua permitida es el indicador de carga,
  que se detiene al terminar la operación.
- Se respeta la preferencia `prefers-reduced-motion`.

### Accesibilidad y adaptación

- HTML semántico: `button` para acciones, `a` para navegación, encabezados en orden.
- Foco visible en todos los elementos interactivos y navegación completa con teclado.
- Las pantallas funcionan desde 320 px de ancho sin desplazamiento horizontal de la página;
  las tablas anchas se desplazan dentro de su propio contenedor.

## Revisión antes de entregar una pantalla

- [ ] No aparece ninguno de los recursos de la sección "Recursos que no se usan".
- [ ] Cada pantalla o sección tiene una sola acción principal, y es evidente.
- [ ] Los formularios tienen etiqueta visible y muestran los errores junto a cada campo.
- [ ] Todos los colores salen de las variables definidas y alcanzan el contraste mínimo del
      nivel AA.
- [ ] Toda la pantalla puede usarse con el teclado y funciona a 320 px de ancho.
- [ ] Los textos describen acciones concretas, sin tono publicitario ni exclamaciones.
