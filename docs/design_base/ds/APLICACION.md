# APLICACIÓN — instrucciones para un agente que arranca un sistema nuevo

Este documento es para ti, agente de IA. Léelo completo antes de escribir la primera plantilla o el primer componente. Es la fundación común del ERP web, la app móvil, la app de inspección de bodega y la app de RH. Su contrato son **variables CSS**, no un framework.

## 1. Archivos

| Archivo | Uso |
|---|---|
| `tokens.json` | Fuente de verdad (W3C Design Tokens). Solo se lee; no se edita desde un producto. |
| `themes.css` | Variables CSS de las tres capas. **Obligatorio.** |
| `components.css` | Clases `ds-*`. **Obligatorio.** Requiere `themes.css` antes. |
| `ds.js` | Opcional. Teclado y ARIA para combobox, listbox, pestañas, menú, tabla, stepper, archivo, notificaciones. |
| `icons.svg` | Sprite de íconos IBM Carbon (Apache 2.0). Pégalo inline al inicio de `<body>`. |
| `fonts/` | Rubik, Public Sans y JetBrains Mono en woff2 variable + `fonts.css`. **Obligatorio.** Nada se descarga de internet. Licencia SIL OFL (`OFL-*.txt`). |
| `design-system.html` | Referencia visual con todos los componentes, estados, 8 temas y 3 densidades; funciona sin internet. Cópiale el marcado. |

## 2. Cargar

```html
<!doctype html>
<html lang="es-MX" data-theme="signal-blue" data-density="compact">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link rel="stylesheet" href="/static/ds/fonts/fonts.css">   <!-- fuentes locales -->
  <link rel="stylesheet" href="/static/ds/themes.css">
  <link rel="stylesheet" href="/static/ds/components.css">
  <link rel="stylesheet" href="/static/<producto>/<producto>.css">  <!-- dialecto, si existe -->
  <script src="/static/ds/ds.js" defer></script>                  <!-- opcional -->
</head>
<body class="ds-root">
  <!-- contenido de icons.svg aquí, con style="display:none" -->
  <a class="ds-skip-link" href="#contenido">Saltar al contenido</a>
  ...
  <main id="contenido">...</main>
</body>
</html>
```

- **Sin dependencias externas**: no cargues fuentes, íconos, scripts ni estilos desde ninguna URL (Google Fonts, CDNs). Todo lo necesario está en esta carpeta.
- **Django**: copia los archivos (incluida la carpeta `fonts/`) a `static/ds/` y usa `{% static 'ds/themes.css' %}`. Configura `LANGUAGE_CODE = "es-mx"`, `USE_TZ = True`, `TIME_ZONE = "America/Mazatlan"` (o la que aplique), `USE_THOUSAND_SEPARATOR = True`.
- **Vue 3 / React**: importa `fonts/fonts.css`, `themes.css` y `components.css` una vez en el punto de entrada (`main.ts`). No uses `ds.js` si el framework ya maneja el estado: replica su ARIA y su teclado (está documentado en `design-system.html`, sección 12). Si lo usas, llama `DS.init(elemento)` después de montar HTML dinámico.

## 3. Elegir tema y densidad

Atributos en `<html>` (o en un contenedor, para una zona con otro tema):

- `data-theme`: `claro` · `oscuro` · `signal-blue` · `ultra-violet` · `dragonfruit` · `lime-spark` · `emerald-ink` · `butter-yellow`. Sin atributo = `claro`.
- `data-density`: `comfortable` · `compact` · `field`. Sin atributo = `comfortable`.

Si el usuario no lo dice: ERP → `compact`; app móvil y RH → `comfortable`; inspección en bodega → `field` con `claro` o `signal-blue` (mejor lectura bajo el sol). Los temas pueden cambiar en tiempo de ejecución cambiando el atributo; no hay que recargar CSS.

## 4. Qué clases usar

Copia el marcado exacto de `design-system.html`. Resumen:

| Necesidad | Marcado |
|---|---|
| Campo | `div.ds-field > label.ds-field__label[for] + control + p.ds-field__error + p.ds-field__help` |
| Requerido / opcional | `span.ds-field__required[aria-hidden]` (*) · `span.ds-field__optional` |
| Texto, textarea, select | `input.ds-input` · `textarea.ds-textarea` · `span.ds-select-wrap > select.ds-select` |
| Error | `aria-invalid="true"` en el control + `p.ds-field__error` con ícono `#i-x-circle` + `aria-describedby` |
| Éxito / cargando | `.is-success` + `p.ds-field__success` · `span.ds-input-wrap.is-loading` + `aria-busy="true"` |
| Prefijo/sufijo (MXN, búsqueda, contraseña) | `div.ds-input-group > span.ds-input-group__addon + input.ds-input + …` |
| Checkbox / radio / switch | `label.ds-check > input.ds-checkbox` · `input.ds-radio` · `input.ds-switch[role=switch]` |
| Agrupar | `fieldset.ds-fieldset > legend.ds-fieldset__legend` |
| Botones | `button.ds-btn.ds-btn--primary|--secondary|--outline|--ghost|--danger` + `--sm|--lg|--icon` |
| Tabla | `div.ds-table-wrap[tabindex=0][role=region][aria-labelledby] > table.ds-table[data-ds-table]` |
| Estado en tabla o lista | `span.ds-status.ds-status--success|warning|danger|info|neutral` (figura + texto) |
| Estado en tarjeta o detalle | `span.ds-badge.ds-badge--success|warning|danger|info|neutral` (etiqueta rectangular con texto) |
| Mensajes | `.ds-alert--*` · `DS.toast({type,title,text})` · `.ds-banner` · `dialog.ds-modal` |
| IA | Todo dentro de `section.ds-ai` con `span.ds-ai__label` (monograma `ds-ai__mark` + «Sugerido por Atlas (IA)»). En formularios: `ds-input ds-ai-field` + `p.ds-ai-hint` |

**Django forms**: `forms.TextInput(attrs={"class": "ds-input"})`, `forms.Select(attrs={"class": "ds-select"})` (envuelto en `span.ds-select-wrap` desde la plantilla), `forms.CheckboxInput(attrs={"class": "ds-checkbox"})`. Haz una plantilla `ds/field.html` que pinte la estructura de campo y úsala para todos los campos.

**Íconos**: `<svg class="ds-icon" aria-hidden="true"><use href="#i-check"/></svg>`. Estados: success `check-circle`, warning `alert-triangle`, danger `x-circle`, info `info`. La IA no tiene ícono: usa el monograma del asistente. Si falta un ícono, tómalo de IBM Carbon; no mezcles otra familia.

## 5. Prohibido

1. Colores, medidas, radios o sombras literales en CSS de producto (`#0057FF`, `14px`, `box-shadow: 0 2px…`). Usa `var(--ds-…)`.
2. Usar `--ds-p-*` (primitivos). Solo existen para alimentar la capa semántica.
3. Redefinir un token semántico o una clase `ds-*` en un producto.
4. Comunicar un estado solo con color. Siempre ícono o texto.
5. Usar `--ds-ai-*` fuera de contenido generado por IA, o mostrar contenido de IA sin `.ds-ai` y su etiqueta.
6. Ejecutar una acción irreversible propuesta por IA sin `dialog` de confirmación que nombre la consecuencia.
7. Quitar el foco (`outline: none`) sin reemplazo, o usar `tabindex` positivo.
8. Placeholder como etiqueta. Botones «Aceptar» / «OK» / «Enviar» sin objeto.
9. Usar borde punteado fuera de la IA; usar píldoras con borde para estados; usar barras laterales de color como indicador de selección; usar versalitas; usar la chispa ✦ u otros símbolos genéricos de IA; construir la IA como panel de chat cuando cabe dentro del flujo (campo sugerido).
10. Usar el lima de `lime-spark` como color de texto, el rosa de `dragonfruit` para errores o el amarillo de `butter-yellow` para advertencias.
11. Lorem ipsum. Usa datos realistas en español de México.
12. Tailwind u otro framework como requisito. Si un producto usa Tailwind, que lea las variables `--ds-*`; nunca su paleta propia.
13. Cargar recursos desde internet: fuentes de Google Fonts, íconos o librerías desde CDN.

## 6. Redacción (mínimo indispensable)

Tuteo, voz activa, mayúscula solo inicial. Botón = verbo en infinitivo + objeto («Autorizar orden»). Error = qué pasó + cómo resolverlo. Fechas `7 de octubre de 2026` / `07/10/2026`, hora `17:05 h`. Montos `$128,450.50 MXN` (coma de miles, punto decimal, `Decimal` en el servidor). Unidades `25 kg`, `4 °C`. Detalle completo: `design-system.html`, sección 11.

## 7. Extender sin romper

1. **Busca primero** en `design-system.html`. Si un `ds-*` resuelve el 80 %, úsalo.
2. **Componente nuevo de producto**: clase con prefijo del dialecto (`erp-`, `mob-`, `fld-`, `rh-`) en `<producto>.css`, construida solo con tokens semánticos (`--ds-surface-*`, `--ds-text-*`, `--ds-action-*`, `--ds-border-*`, `--ds-feedback-*`) y de componente (`--ds-control-*`, `--ds-target-min`, `--ds-space-*`). Revísalo en los 8 temas y las 3 densidades con el selector del documento.
3. **Falta un token**: no lo inventes en el producto. Agrégalo a `tokens.json` con valor para los 8 temas, regenera `themes.css`, corre `dsContrastAudit` (sección 3 del documento) y sube la versión menor.
4. **Patrón usado en 2+ productos**: se propone para promoverlo a `ds-*` en la fundación.
5. **Renombrar o borrar** un token o clase es cambio mayor: deja el nombre viejo como alias durante una versión.

## 8. Verificación antes de entregar

- [ ] `lang="es-MX"`, un `h1`, `main` con `id` y enlace «Saltar al contenido».
- [ ] Cero colores literales: `grep -E "#[0-9a-fA-F]{3,8}|rgb\(" <producto>.css` sin resultados.
- [ ] Probado en al menos un tema claro, uno oscuro y en la densidad objetivo.
- [ ] Todo campo con `label`; errores con `aria-invalid` + texto + ícono.
- [ ] Navegable solo con teclado; foco visible siempre.
- [ ] Contenido de IA dentro de `.ds-ai` (o `ds-ai-field`) con el nombre del asistente y «(IA)»; acciones irreversibles confirmadas.
