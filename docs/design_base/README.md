# design_base — Design system de la empresa

Fundación visual común para los sistemas internos: ERP web, app móvil general, app de inspección de bodega y app de Recursos Humanos. Tiene 8 temas de color, 3 densidades y una capa de clases `ds-*` que funciona sin frameworks de JavaScript: en plantillas de Django, en Vue 3 o en React.

**Funciona sin internet.** Fuentes, íconos, estilos y scripts vienen dentro de esta carpeta; nada se carga desde una URL externa (ni Google Fonts ni CDN).

Este README sirve para dos lectores:

- **La persona** que arranca un proyecto. Para ti son la sección 1 y la sección 2.
- **El agente de IA** que va a aplicar la apariencia. Para él es la sección 3; debe seguirla al pie de la letra.

---

## 0. Configuración de este proyecto

Edita estos cuatro valores antes de pedirle al agente que aplique el design system. Si la indicación que le das al agente trae otros valores, mandan los de la indicación.

```yaml
tema: signal-blue       # claro | oscuro | signal-blue | ultra-violet | dragonfruit | lime-spark | emerald-ink | butter-yellow
densidad: comfortable   # comfortable | compact | field
stack: django           # django | vue | react
prefijo: erp            # prefijo de las clases propias del producto: erp | mob | fld | rh | otro
```

| Producto | Densidad sugerida | Prefijo |
|---|---|---|
| ERP web (mouse y teclado, tablas densas) | `compact` | `erp` |
| App móvil general | `comfortable` | `mob` |
| Inspección de mercancía y bodega (guantes, sol) | `field` | `fld` |
| Recursos Humanos | `comfortable` | `rh` |

| Tema | Base | Nota |
|---|---|---|
| `claro` | Clara | Neutro, sin color de marca. |
| `oscuro` | Oscura | Fondo grafito, texto al 87 %; nunca negro puro. |
| `signal-blue` | Clara | Azul de acción sobre porcelana. Recomendado para uso bajo el sol. |
| `ultra-violet` | Clara | Violeta con durazno como destaque. |
| `dragonfruit` | Oscura | Rosa sobre violeta noche; el error es bermellón. |
| `lime-spark` | Oscura | Lima sobre grafito; el lima nunca es texto. |
| `emerald-ink` | Clara | Esmeralda profundo con champagne. |
| `butter-yellow` | Clara | Iris real; el amarillo solo es destaque, nunca advertencia. |

Para ver cualquier combinación antes de decidir, abre `ds/design-system.html` en el navegador y usa los selectores de tema y densidad de arriba.

---

## 1. Contenido de la carpeta

```
design_base/
├── README.md               ← este archivo
└── ds/
    ├── APLICACION.md       reglas operativas para agentes (léelo completo)
    ├── design-system.html  documentación visual completa; abrir en el navegador
    ├── themes.css          variables CSS de los 8 temas y 3 densidades    → se copia al proyecto
    ├── components.css      clases ds-* (campos, botones, tablas, IA…)      → se copia al proyecto
    ├── ds.js               teclado y ARIA opcionales (combobox, tabla…)   → se copia al proyecto
    ├── icons.svg           íconos IBM Carbon en sprite                     → se copia al proyecto
    ├── fonts/              Rubik, Public Sans y JetBrains Mono (woff2)     → se copia al proyecto
    │   ├── fonts.css       declara las @font-face con rutas relativas
    │   ├── *.woff2         fuentes variables, subconjuntos latin y latin-ext
    │   └── OFL-*.txt       licencias de las fuentes
    ├── tokens.json         fuente de verdad (formato W3C Design Tokens)
    └── gen_tokens.py       regenera tokens.json y themes.css y verifica contraste
```

`design_base/` es la **fuente**. Nada dentro se edita desde un proyecto: el agente copia lo necesario al directorio de estáticos y trabaja sobre esas copias.

---

## 2. Uso (para la persona)

1. Copia la carpeta `design_base/` completa a la raíz del proyecto recién creado.
2. Edita la sección 0 de este README con el tema, la densidad, el stack y el prefijo.
3. Pídele al agente:

   > Aplica el design system de `design_base/` siguiendo su README.

   Si quieres dar los valores en la misma frase:

   > Aplica el design system de `design_base/` siguiendo su README. Tema `emerald-ink`, densidad `compact`, stack Django, prefijo `erp`.

4. Revisa el reporte que entrega al final (sección 3, paso 9) y abre una pantalla en el navegador.

**Cambiar de tema después:** cambia el atributo `data-theme` en `<html>` de la plantilla base. No hay que tocar CSS.

**Actualizar la fundación:** reemplaza la carpeta `design_base/ds/` por la versión nueva y pídele al agente que vuelva a copiar los cuatro archivos a estáticos (paso 3). Nunca edites `themes.css` a mano: los colores se cambian en `gen_tokens.py`, que regenera `tokens.json` y `themes.css` y verifica el contraste (`python3 gen_tokens.py`).

---

## 3. Instrucciones para el agente de IA

Sigue estos pasos en orden. No improvises estilos: este design system ya define cómo se ve todo.

### Paso 1. Lee antes de escribir código

1. Lee completo `design_base/ds/APLICACION.md`. Sus reglas tienen prioridad sobre tus preferencias de estilo.
2. Toma tema, densidad, stack y prefijo de la indicación del usuario o, si no los dio, de la sección 0 de este README. Si alguno falta, usa `claro`, `comfortable`, el stack que detectes en el proyecto y `app`, y dilo en tu reporte.
3. `design_base/ds/design-system.html` es la referencia del marcado exacto de cada componente. Pesa ~700 KB: **no lo leas completo**; búscalo por clase o por id de sección (`id="tabla"`, `id="campo"`, `id="moneda"`, `id="ia-flujo"`, `class="ds-btn`…) y copia el marcado del ejemplo.

### Paso 2. No modifiques `design_base/`

Es la fuente. Si algo te falta, créalo en el proyecto con el prefijo del producto (paso 7).

### Paso 3. Copia los archivos a estáticos

Copia `themes.css`, `components.css`, `ds.js`, `icons.svg` y la carpeta `fonts/` completa de `design_base/ds/` a:

| Stack | Destino |
|---|---|
| Django | `<app>/static/ds/` (o el `STATICFILES_DIRS` del proyecto); además, `icons.svg` a `templates/ds/icons.svg` |
| Vue 3 (Vite) | `src/assets/ds/` para los CSS y `fonts/`; `ds.js` e `icons.svg` a `public/ds/` |
| React (Vite) | igual que Vue |

### Paso 4. Plantilla base

Siempre `lang="es-MX"`, los atributos de tema y densidad en `<html>`, las fuentes locales, los dos CSS en este orden y el sprite de íconos al inicio de `<body>`, oculto. **No agregues ninguna URL externa** (Google Fonts, CDN de íconos o librerías).

**Django** (`templates/base.html`):

```html
{% load static %}<!doctype html>
<html lang="es-MX" data-theme="signal-blue" data-density="comfortable">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{% block title %}{% endblock %} · Nombre del sistema</title>
  <link rel="stylesheet" href="{% static 'ds/fonts/fonts.css' %}">
  <link rel="stylesheet" href="{% static 'ds/themes.css' %}">
  <link rel="stylesheet" href="{% static 'ds/components.css' %}">
  <script src="{% static 'ds/ds.js' %}" defer></script>
</head>
<body class="ds-root">
  <div hidden>{% include "ds/icons.svg" %}</div>
  <a class="ds-skip-link" href="#contenido">Saltar al contenido</a>
  {% block header %}{% endblock %}
  <main id="contenido">{% block content %}{% endblock %}</main>
</body>
</html>
```

**Vue 3 o React (Vite):** en `index.html` pon `lang`, `data-theme`, `data-density` y `<script src="/ds/ds.js" defer></script>`. En el punto de entrada (`main.ts`/`main.tsx`) importa en este orden (Vite empaqueta los woff2 junto con el resto):

```js
import "./assets/ds/fonts/fonts.css";
import "./assets/ds/themes.css";
import "./assets/ds/components.css";
```

Inserta el sprite una vez al montar la app (por ejemplo, `fetch("/ds/icons.svg")` e insertarlo en un `<div hidden>` al inicio de `body`). Después de montar HTML dinámico, llama `window.DS?.init(elemento)`. Si el componente del framework ya maneja el teclado y el ARIA, puedes no usar `ds.js`, pero replica el comportamiento descrito en la sección 12 de `design-system.html`.

### Paso 5. Construye con clases `ds-*`

- Usa solo clases `ds-*` y variables `--ds-*` semánticas (`--ds-surface-*`, `--ds-text-*`, `--ds-border-*`, `--ds-action-*`, `--ds-feedback-*`, `--ds-space-*`, `--ds-radius-*`, `--ds-control-*`).
- Copia el marcado de los ejemplos: estructura de campo, botones, tabla, estados, alertas, modal.
- Íconos: `<svg class="ds-icon" aria-hidden="true"><use href="#i-check"/></svg>`. Si falta un ícono, tómalo de IBM Carbon; nunca de otra familia.

**Django forms:** pon la clase en el widget y pinta la estructura con una plantilla reutilizable.

```python
widgets = {
    "rfc": forms.TextInput(attrs={"class": "ds-input", "autocapitalize": "characters"}),
    "regimen": forms.Select(attrs={"class": "ds-select"}),
    "activo": forms.CheckboxInput(attrs={"class": "ds-checkbox"}),
}
```

Crea `templates/ds/field.html` con etiqueta, requerido, control, error (`aria-invalid="true"` + ícono `#i-x-circle` + texto) y ayuda, enlazados con `aria-describedby`. El marcado de referencia está en la sección «Estructura de campo» de `design-system.html` y en `APLICACION.md`. Los `select` van envueltos en `<span class="ds-select-wrap">`.

### Paso 6. Reglas que no se negocian

Resumen; la lista completa está en `APLICACION.md`, sección 5.

1. Nada de colores, medidas, radios o sombras literales. Nada de `--ds-p-*` (primitivos).
2. No redefinas tokens ni clases `ds-*`.
3. Ningún estado se comunica solo con color: en tablas y listas usa `ds-status` (figura + texto); en tarjetas y detalle, `ds-badge` (etiqueta rectangular).
4. Lo que genera una IA va en `.ds-ai`, o en un campo `.ds-ai-field` con su línea `.ds-ai-hint`, con la etiqueta «Sugerido por Atlas (IA)». Prefiere sugerencias dentro del flujo antes que un panel de chat. Nada irreversible sin un `dialog` de confirmación. «Atlas» es un nombre provisional: si el usuario indicó otro, úsalo.
5. Evita los rasgos genéricos de IA: píldoras con borde para estados, barras laterales de color para la selección, versalitas, la chispa ✦, borde punteado fuera de la IA y chips de sugerencia.
6. Textos en español de México: tuteo, voz activa, mayúscula solo inicial, botones con verbo + objeto, fechas `07/10/2026`, montos `$128,450.50 MXN`. Nada de lorem ipsum.
7. Accesibilidad WCAG 2.2 AA: `label` en todo campo, foco visible, navegación completa con teclado, un `h1` por vista.

### Paso 7. Si algo no existe

1. Búscalo primero en `design-system.html`.
2. Si no existe, crea `static/<prefijo>/<prefijo>.css` (o su equivalente en Vue o React), cárgalo **después** de `components.css` y crea clases con el prefijo del producto (`erp-scan`, `fld-foto`…) usando solo variables `--ds-*`.
3. Si te falta un color o una medida que no existe como token, **no lo inventes**. Usa el token más cercano y anótalo en tu reporte para agregarlo a la fundación.

### Paso 8. Instrucción permanente

Agrega al archivo de instrucciones del proyecto (`CLAUDE.md`, `AGENTS.md` o el que use el proyecto; créalo si no existe) este bloque, con los valores reales:

```markdown
## Interfaz
Este proyecto usa el design system de `design_base/` (tema `signal-blue`, densidad `comfortable`, prefijo `erp`).
Antes de crear o modificar cualquier pantalla, lee `design_base/README.md` y `design_base/ds/APLICACION.md` y síguelos.
```

### Paso 9. Verifica y reporta

Antes de terminar:

- Revisa la lista de la sección 8 de `APLICACION.md`.
- Comprueba que no haya colores literales en el CSS del producto: `grep -rnE "#[0-9a-fA-F]{3,8}\b|rgb\(" static/<prefijo>/`. No debe devolver nada.
- Comprueba que no haya recursos externos en las plantillas: `grep -rnE "googleapis|gstatic|cdn\.|unpkg|jsdelivr" templates/ src/ public/ 2>/dev/null`. No debe devolver nada.
- Abre una pantalla en un tema claro y en uno oscuro, y en la densidad elegida.

Entrega al usuario un reporte corto con:

- tema, densidad, stack y prefijo aplicados (y cuáles tomaste por defecto);
- archivos copiados y archivos creados o modificados;
- clases propias que creaste con el prefijo;
- tokens que hicieron falta, si alguno;
- qué puntos de la lista de verificación quedaron pendientes.

---

## 4. Créditos y licencias

- Íconos: IBM Carbon Design System, licencia Apache 2.0.
- Fuentes: Rubik, Public Sans y JetBrains Mono, incluidas en `ds/fonts/`, licencia SIL Open Font License 1.1 (textos completos en `ds/fonts/OFL-*.txt`). La licencia permite usarlas y redistribuirlas dentro de los sistemas de la empresa.
- Versión de la fundación: 1.0 (octubre de 2026).
