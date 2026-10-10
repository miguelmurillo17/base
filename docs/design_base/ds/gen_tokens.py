"""Genera tokens.json (W3C DTCG), themes.css y contrast.json para el design system.

Tres capas:
  primitive  -> valores crudos por tema (rampa de neutros teñida + muestras de color)
  semantic   -> lo único que consumen los componentes; cada tema la redefine
  component  -> alturas de control, filas de tabla, objetivos táctiles (por densidad)
"""
import json, math, os

OUT = os.path.dirname(os.path.abspath(__file__))  # escribe junto a este archivo

# ---------------------------------------------------------------- color math
def hex2rgb(h):
    h = h.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))

def rgb2hex(c):
    return "#" + "".join(f"{round(max(0, min(1, v)) * 255):02X}" for v in c)

def s2l(v):
    return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4

def l2s(v):
    v = max(0.0, min(1.0, v))
    return 12.92 * v if v <= 0.0031308 else 1.055 * v ** (1 / 2.4) - 0.055

def lum(h):
    r, g, b = (s2l(v) for v in hex2rgb(h))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b

def contrast(a, b):
    la, lb = lum(a), lum(b)
    if la < lb:
        la, lb = lb, la
    return (la + 0.05) / (lb + 0.05)

def to_oklab(h):
    r, g, b = (s2l(v) for v in hex2rgb(h))
    l = 0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b
    m = 0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b
    s = 0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b
    l, m, s = (math.copysign(abs(x) ** (1 / 3), x) for x in (l, m, s))
    return (0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * s,
            1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s,
            0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s)

def from_oklab(L, a, b):
    l = (L + 0.3963377774 * a + 0.2158037573 * b) ** 3
    m = (L - 0.1055613458 * a - 0.0638541728 * b) ** 3
    s = (L - 0.0894841775 * a - 1.2914855480 * b) ** 3
    r = 4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s
    g = -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s
    bb = -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s
    return (r, g, bb)

def in_gamut(rgb):
    return all(-1e-4 <= v <= 1 + 1e-4 for v in rgb)

def oklch(h):
    L, a, b = to_oklab(h)
    return L, math.hypot(a, b), (math.degrees(math.atan2(b, a)) % 360)

def from_oklch(L, C, H):
    """Convierte OKLCH a hex reduciendo croma hasta entrar en gamut sRGB."""
    for _ in range(60):
        rgb = from_oklab(L, C * math.cos(math.radians(H)), C * math.sin(math.radians(H)))
        if in_gamut(rgb):
            break
        C *= 0.95
    return rgb2hex(tuple(l2s(v) for v in rgb))

def mix(a, b, t):
    """Mezcla en OKLab: t=0 -> a, t=1 -> b."""
    A, B = to_oklab(a), to_oklab(b)
    rgb = from_oklab(*(A[i] + (B[i] - A[i]) * t for i in range(3)))
    return rgb2hex(tuple(l2s(v) for v in rgb))

def composite(fg_hex_alpha, bg):
    """fg '#RRGGBBAA' sobre bg opaco -> hex opaco."""
    h = fg_hex_alpha.lstrip("#")
    a = int(h[6:8], 16) / 255 if len(h) == 8 else 1
    f = hex2rgb(h[:6]); g = hex2rgb(bg)
    return rgb2hex(tuple(f[i] * a + g[i] * (1 - a) for i in range(3)))

def fit(color, bgs, target, direction):
    """Ajusta la luminosidad OKLCH de `color` (conservando tono) hasta que
    alcance `target` contra TODOS los fondos. direction: -1 oscurece, +1 aclara."""
    L, C, H = oklch(color)
    c = color
    for _ in range(400):
        if all(contrast(c, b) >= target + 0.02 for b in bgs):
            return c
        L = max(0, min(1, L + 0.004 * direction))
        c = from_oklch(L, C, H)
    raise RuntimeError(f"no se pudo ajustar {color} a {target}:1")

def ramp(paper, ink, Ls):
    """Rampa de neutros: mezcla OKLab papel->tinta buscando la L objetivo."""
    out = {}
    for name, target in Ls.items():
        lo, hi = 0.0, 1.0
        for _ in range(40):
            t = (lo + hi) / 2
            if to_oklab(mix(paper, ink, t))[0] > target:
                lo = t
            else:
                hi = t
        out[name] = mix(paper, ink, (lo + hi) / 2)
    return out

def hue_dist(a, b):
    d = abs(a - b) % 360
    return min(d, 360 - d)

# ------------------------------------------------------------- theme specs
LIGHT_STEPS = {"0": 1.0, "25": .985, "50": .968, "100": .94, "150": .905, "200": .865,
               "300": .79, "400": .69, "500": .59, "600": .50, "700": .42,
               "800": .34, "850": .295, "900": .255, "950": .215}

THEMES = {
    "claro": dict(name="Claro", mode="light",
        paper="#FFFFFF", ink="#141518",
        accent="#1E1F23", accent_hover="#3A3C42", accent_text="#FFFFFF",
        link="#1F54C9",
        secondary_hint=None,
        highlight="#F1F1EF",
        success="#1F7A3A", warning="#B26A00", danger="#C8312B", info="#1D63C9", ai="#7A3FE0",
        notes="Escala de blanco a negro sin color de marca. El acento es un neutro casi negro; los enlaces usan un azul funcional, siempre subrayados."),
    "oscuro": dict(name="Oscuro", mode="dark",
        paper="#E9EDF3", ink="#171B21",
        accent="#93A8EE", accent_hover="#AABBF3", accent_text="#11151B",
        link="#A9BBF4",
        highlight="#262C36",
        success="#6CC490", warning="#E3B75C", danger="#EF8585", info="#6FB4DE", ai="#D39CE6",
        text_alpha=True,
        notes="Fondo #171B21, nunca negro. Texto principal al 87 % de opacidad. Colores desaturados; la elevación se expresa aclarando la superficie."),
    "signal-blue": dict(name="Signal Blue", mode="light",
        paper="#F8F7F4", ink="#0D1830",
        accent="#0057FF", accent_hover="#0045CC", accent_text="#FFFFFF",
        link="#0057FF",
        highlight="#E6EEFF",
        success="#22792F", warning="#A65A00", danger="#C42D2D", info="#0B6E87", ai="#9A2FC8",
        notes="Signal Blue como acción sobre Porcelain. Info se movió a cian petróleo y la IA a violeta-magenta para separarse del azul de marca."),
    "ultra-violet": dict(name="Ultra Violet", mode="light",
        paper="#FBFAFD", ink="#1A1030",
        accent="#6A00F4", accent_hover="#5500C4", accent_text="#FFFFFF",
        link="#6A00F4",
        highlight="#FFD6A5",
        success="#1F7A43", warning="#A15800", danger="#C42B3A", info="#0B6A9C", ai="#0B7F78",
        notes="Ultra Violet como acción. Soft Apricot solo como acento secundario y fondo de destaque (chips, filas destacadas), nunca como superficie de lectura."),
    "dragonfruit": dict(name="Dragonfruit", mode="dark",
        paper="#F6EEFB", ink="#1E1033",
        accent="#FF4696", accent_hover="#FF70AD", accent_text="#1E1033",
        link="#FF8DBF",
        highlight="#3A1F55",
        success="#5ED39A", warning="#F2C14E", danger="#FF7A52", info="#8EA8FF", ai="#4FD6DF",
        notes="Night Violet como base y Dragonfruit como acento. Danger se desplazó a bermellón (≈40° de tono de distancia) y el botón destructivo es delineado."),
    "lime-spark": dict(name="Lime Spark", mode="dark",
        paper="#EEF0F4", ink="#23262F",
        accent="#B6FF2E", accent_hover="#CBFF6B", accent_text="#1A1C22",
        link="#A3CFFF",
        highlight="#323726",
        success="#4FD1A5", warning="#FFC24D", danger="#FF7D7D", info="#7DBBFF", ai="#C4A6FF",
        notes="Graphite como base. El lima solo rellena botones, indicadores y bordes de foco; nunca es texto de cuerpo. Los enlaces son azul claro subrayado."),
    "emerald-ink": dict(name="Emerald Ink", mode="light",
        paper="#FCF8F1", ink="#0B241D",
        accent="#064E3B", accent_hover="#0B6B51", accent_text="#FFFFFF",
        link="#0B6E52",
        accent_mid="#0F8A66",
        highlight="#F8E7C9",
        success="#3A7A16", warning="#9E5A00", danger="#B4232F", info="#1F5FBF", ai="#6A3FC8",
        notes="Emerald Ink funciona casi como neutro; se añade un verde intermedio (#0B6B51 / #0F8A66) para hover, enlaces y acentos. Champagne es el destaque."),
    "butter-yellow": dict(name="Butter Yellow", mode="light",
        paper="#FBFAFE", ink="#1B1238",
        accent="#3A0CA3", accent_hover="#4C20C2", accent_text="#FFFFFF",
        link="#3A0CA3",
        highlight="#FFF275",
        success="#1E7A3C", warning="#9A5600", danger="#BF2C2C", info="#0B6C9A", ai="#0B7D74",
        warning_bg="#FDEAD8",
        notes="Royal Iris es la acción. Butter Yellow es solo destaque (marcatextos, chips, banners de novedad) y nunca significa advertencia; warning usa ocre sobre crema anaranjada y siempre lleva △."),
}

FEEDBACK = ["success", "warning", "danger", "info"]

def build_theme(tid, s):
    dark = s["mode"] == "dark"
    prim = {}          # primitive name -> hex
    sem = {}           # semantic name -> primitive name (o valor literal con alpha)

    def P(name, value):
        prim[name] = value
        return name

    paper, ink = s["paper"], s["ink"]
    # --- rampa de neutros teñida hacia el color oscuro del tema
    if dark:
        steps = dict(LIGHT_STEPS)
        n = ramp(paper, ink, steps)
        L_ink = to_oklab(ink)[0]
        # pasos extra por debajo de la tinta para superficies hundidas
        n["975"] = ink
        n["990"] = mix(ink, "#000000", 0.18)
        # superficies elevadas por luminancia
        n["930"] = mix(ink, paper, 0.055)
        n["910"] = mix(ink, paper, 0.10)
        n["880"] = mix(ink, paper, 0.15)
    else:
        n = ramp(paper, ink, LIGHT_STEPS)
        n["0"] = paper
        n["950"] = ink
    for k, v in n.items():
        P(f"neutral-{k}", v)

    # --- superficies
    if dark:
        base, sunken, raised, overlay = n["975"], n["990"], n["930"], n["910"]
        sem["surface/hover"] = P("neutral-hover", mix(base, paper, 0.075))
    else:
        base = paper
        raised = mix(paper, "#FFFFFF", 0.85) if paper != "#FFFFFF" else "#FFFFFF"
        sunken = n["100"] if paper != "#FFFFFF" else n["50"]
        overlay = raised
        sem["surface/hover"] = P("neutral-hover", mix(paper, ink, 0.045))
    sem["surface/base"] = P("surface-base", base)
    sem["surface/raised"] = P("surface-raised", raised)
    sem["surface/sunken"] = P("surface-sunken", sunken)
    sem["surface/overlay"] = P("surface-overlay", overlay)
    sem["surface/scrim"] = P("scrim", (ink if not dark else "#000000") + ("8C" if not dark else "A6"))
    reading = [base, raised, sunken, overlay]

    # --- texto
    if dark and s.get("text_alpha"):
        tp, ts, tm = paper + "DE", paper + "B3", paper + "94"   # 87 %, 70 %, 58 %
        sem["text/primary"] = P("text-87", tp)
        sem["text/secondary"] = P("text-70", ts)
        sem["text/muted"] = P("text-58", tm)
    elif dark:
        sem["text/primary"] = P("neutral-25", n["25"])
        sem["text/secondary"] = P("text-secondary", fit(n["150"], reading, 7.0, +1))
        sem["text/muted"] = P("text-muted", fit(n["300"], reading, 4.5, +1))
    else:
        sem["text/primary"] = P("neutral-950", n["950"])
        sem["text/secondary"] = P("text-secondary", fit(n["700"], reading, 7.0, -1))
        sem["text/muted"] = P("text-muted", fit(n["500"], reading, 4.5, -1))
    sem["text/inverse"] = P("text-inverse", base if dark else paper)
    link = fit(s["link"], reading, 4.5, +1 if dark else -1)
    sem["text/link"] = P("link", link)
    sem["text/link-hover"] = P("link-hover", fit(mix(link, paper if dark else ink, 0.25), reading, 4.5, +1 if dark else -1))

    # --- bordes
    sem["border/subtle"] = P("border-subtle", mix(base, paper if dark else ink, 0.12 if dark else 0.10))
    sem["border/default"] = P("border-default", fit(mix(base, paper if dark else ink, 0.30), [base, raised, sunken], 3.0, +1 if dark else -1))
    sem["border/strong"] = P("border-strong", fit(mix(base, paper if dark else ink, 0.55), [base, raised, sunken], 4.5, +1 if dark else -1))

    # --- acciones
    acc = s["accent"]
    sem["action/primary"] = P("accent", acc)
    sem["action/primary-hover"] = P("accent-hover", s["accent_hover"])
    sem["action/primary-active"] = P("accent-active", mix(s["accent_hover"], ink if not dark else paper, 0.12))
    sem["action/primary-text"] = P("accent-text", s["accent_text"])
    if s.get("accent_mid"):
        sem["accent/mid"] = P("accent-mid", s["accent_mid"])
    sec_bg = mix(base, acc, 0.16 if dark else 0.08) if tid != "claro" else n["100"]
    sem["action/secondary"] = P("secondary", sec_bg)
    sem["action/secondary-hover"] = P("secondary-hover", mix(base, acc, 0.26 if dark else 0.14) if tid != "claro" else n["150"])
    sec_txt_seed = s.get("accent_mid", acc) if tid == "emerald-ink" else acc
    sem["action/secondary-text"] = P("secondary-text", fit(sec_txt_seed, [sec_bg, mix(base, acc, 0.26 if dark else 0.14) if tid != "claro" else n["150"], base], 4.5, +1 if dark else -1))
    sem["action/ghost"] = P("transparent", "#00000000")
    sem["action/ghost-hover"] = P("ghost-hover", mix(base, acc if tid != "claro" else ink, 0.12 if dark else 0.06))
    sem["action/disabled"] = P("disabled", mix(base, paper if dark else ink, 0.10 if dark else 0.07))
    sem["action/disabled-text"] = P("disabled-text", mix(base, paper if dark else ink, 0.42))

    # --- foco: anillo de 2px con separación de 2px sobre la superficie
    focus_seed = acc if tid not in ("claro",) else "#1F54C9"
    if tid == "emerald-ink":
        focus_seed = s["accent_mid"]
    sem["border/focus"] = P("focus", fit(focus_seed, reading, 3.0, +1 if dark else -1))

    # --- acento secundario / destaque
    hl = s["highlight"]
    sem["accent/highlight-bg"] = P("highlight", hl)
    sem["accent/highlight-text"] = P("highlight-text", fit(n["950"] if not dark else n["25"], [hl], 7.0, -1 if not dark else +1))
    sem["surface/selected"] = P("selected", mix(base, acc, 0.20 if dark else 0.09) if tid != "claro" else n["100"])
    sem["border/selected"] = P("selected-border", fit(acc, [base, raised], 3.0, +1 if dark else -1) if tid != "lime-spark" else acc)

    # --- feedback (redefinido por tema)
    for f in FEEDBACK:
        seed = s[f]
        solid = fit(seed, [base, raised, sunken], 3.0, +1 if dark else -1)
        bg = s.get(f + "_bg") or mix(base, seed, 0.17 if dark else 0.10)
        border = mix(bg, solid, 0.55)
        txt = fit(seed, [bg, base, raised, sunken], 4.5, +1 if dark else -1)
        sem[f"feedback/{f}"] = P(f"{f}", solid)
        sem[f"feedback/{f}-bg"] = P(f"{f}-bg", bg)
        sem[f"feedback/{f}-border"] = P(f"{f}-border", border)
        sem[f"feedback/{f}-text"] = P(f"{f}-text", txt)
    # texto sobre relleno sólido (badges sólidos, botón destructivo)
    sem["feedback/danger-solid-text"] = P("danger-solid-text", "#FFFFFF" if not dark else ink)
    # --- acción destructiva. En dragonfruit es delineada para no competir con el rosa de marca.
    if tid == "dragonfruit":
        sem["action/danger"] = "transparent"
        sem["action/danger-hover"] = "danger-bg"
        sem["action/danger-text"] = "danger-text"
        sem["action/danger-border"] = "danger"
    else:
        sem["action/danger"] = "danger"
        dh = mix(prim["danger"], ink if not dark else paper, 0.18)
        sem["action/danger-hover"] = P("danger-hover", dh)
        sem["action/danger-text"] = "danger-solid-text"
        sem["action/danger-border"] = "danger"

    # --- IA
    # La IA no tiene color propio: es neutra (de la rampa del tema) y se reconoce por FORMA:
    # borde punteado (= borrador hasta que una persona lo acepta) + monograma del asistente.
    far = paper if dark else ink
    ai_surface = mix(raised, far, 0.06 if dark else 0.025)
    sem["ai/surface"] = P("ai-surface", ai_surface)
    sem["ai/border"] = P("ai-border", fit(mix(ai_surface, far, 0.45), [base, raised, ai_surface], 3.0, +1 if dark else -1))
    sem["ai/accent"] = P("ai-accent", fit(n["800"] if not dark else n["150"], [base, raised, ai_surface], 4.5, -1 if not dark else +1))
    sem["ai/accent-text"] = P("ai-text", fit(n["700"] if not dark else n["200"], [ai_surface, base, raised], 4.5, -1 if not dark else +1))

    # --- elevación
    if dark:
        elev = {
            "elevation/1": "0 0 0 1px rgb(255 255 255 / 0.06)",
            "elevation/2": "0 0 0 1px rgb(255 255 255 / 0.08), 0 4px 12px rgb(0 0 0 / 0.28)",
            "elevation/3": "0 0 0 1px rgb(255 255 255 / 0.10), 0 12px 32px rgb(0 0 0 / 0.40)",
        }
    else:
        r, g, b = (round(v * 255) for v in hex2rgb(ink))
        elev = {
            "elevation/1": f"0 1px 2px rgb({r} {g} {b} / 0.08), 0 0 0 1px rgb({r} {g} {b} / 0.04)",
            "elevation/2": f"0 2px 6px rgb({r} {g} {b} / 0.10), 0 8px 20px rgb({r} {g} {b} / 0.08)",
            "elevation/3": f"0 8px 24px rgb({r} {g} {b} / 0.14), 0 24px 56px rgb({r} {g} {b} / 0.14)",
        }
    return prim, sem, elev

# ------------------------------------------------------------- contrast spec
def resolve(prim, sem, key, bg=None):
    v = prim[sem[key]]
    if len(v.lstrip("#")) == 8:
        return composite(v, bg) if bg else v
    return v

CHECKS = [
    # (fg, bg, min, tipo)
    *[(t, s, 4.5, "texto") for t in ("text/primary", "text/secondary", "text/muted", "text/link")
      for s in ("surface/base", "surface/raised", "surface/sunken")],
    ("text/primary", "surface/overlay", 4.5, "texto"),
    ("text/primary", "surface/hover", 4.5, "texto"),
    ("text/primary", "surface/selected", 4.5, "texto"),
    ("text/inverse", "text/primary", 4.5, "texto (tooltip)"),
    ("action/primary-text", "action/primary", 4.5, "texto"),
    ("action/primary-text", "action/primary-hover", 4.5, "texto"),
    ("action/secondary-text", "action/secondary", 4.5, "texto"),
    ("action/secondary-text", "action/secondary-hover", 4.5, "texto"),
    ("text/primary", "action/ghost-hover", 4.5, "texto"),
    ("accent/highlight-text", "accent/highlight-bg", 4.5, "texto"),
    *[(f"feedback/{f}-text", f"feedback/{f}-bg", 4.5, "texto") for f in FEEDBACK],
    *[(f"feedback/{f}-text", "surface/base", 4.5, "texto") for f in FEEDBACK],
    *[(f"feedback/{f}", "surface/base", 3.0, "no textual") for f in FEEDBACK],
    ("feedback/danger-solid-text", "feedback/danger", 4.5, "texto"),
    ("action/danger-text", "action/danger", 4.5, "texto"),
    ("action/danger-text", "action/danger-hover", 4.5, "texto"),
    ("action/danger-border", "surface/base", 3.0, "borde de control"),
    ("text/primary", "ai/surface", 4.5, "texto"),
    ("ai/accent-text", "ai/surface", 4.5, "texto"),
    ("ai/accent", "surface/base", 4.5, "monograma IA"),
    ("surface/base", "ai/accent", 4.5, "letra del monograma"),
    ("ai/border", "surface/base", 3.0, "borde punteado IA"),
    ("ai/border", "ai/surface", 3.0, "borde punteado IA"),
    ("border/default", "surface/base", 3.0, "borde de control"),
    ("border/default", "surface/raised", 3.0, "borde de control"),
    ("border/default", "surface/sunken", 3.0, "borde de control"),
    ("border/focus", "surface/base", 3.0, "foco"),
    ("border/focus", "surface/raised", 3.0, "foco"),
    ("action/primary", "surface/base", 3.0, "no textual"),
    ("border/selected", "surface/base", 3.0, "no textual"),
]

def bg_of(prim, sem, key, base):
    v = prim[sem[key]]
    return composite(v, base) if len(v.lstrip("#")) == 8 else v

def run_checks(prim, sem):
    base = prim[sem["surface/base"]]
    rows = []
    for fg, bg, mn, kind in CHECKS:
        if fg == "feedback/danger-solid-text" and False:
            pass
        bgv = bg_of(prim, sem, bg, base)
        fgv = prim[sem[fg]]
        if len(fgv.lstrip("#")) == 8:
            fgv = composite(fgv, bgv)
        r = contrast(fgv, bgv)
        rows.append(dict(fg=fg, bg=bg, fgHex=fgv, bgHex=bgv, ratio=round(r, 2), min=mn, kind=kind, ok=r >= mn))
    return rows

def hue_report(prim, sem):
    """La IA se distingue por forma, no por tono: se reporta su croma (casi neutra)
    y el contraste del borde punteado contra la base."""
    base = prim[sem["surface/base"]]
    return {"aiAccent": prim[sem["ai/accent"]], "chroma": round(oklch(prim[sem["ai/accent"]][:7])[1], 3),
            "accentChroma": round(oklch(prim[sem["action/primary"]][:7])[1], 3),
            "borderRatio": round(contrast(prim[sem["ai/border"]], base), 2)}

# ------------------------------------------------------------- static scales
SPACE = [0, 2, 4, 8, 12, 16, 20, 24, 32, 40, 48, 64]
RADIUS = {"none": "0px", "xs": "2px", "sm": "4px", "md": "6px", "lg": "10px", "xl": "16px", "pill": "999px"}
BORDER_W = {"thin": "1px", "thick": "2px", "accent": "3px", "focus-width": "2px", "focus-offset": "2px"}
FONTS = {
    "display": '"Rubik", "Public Sans", system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
    "sans": '"Public Sans", system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
    "mono": '"JetBrains Mono", ui-monospace, "Cascadia Mono", "SF Mono", Menlo, Consolas, "Liberation Mono", monospace',
}
TYPE = {  # rol: (familia, tamaño px, interlineado px, peso, letter-spacing)
    "display":  ("display", 40, 48, 700, "-0.01em"),
    "h1":       ("display", 32, 40, 700, "-0.005em"),
    "h2":       ("display", 24, 32, 600, "0em"),
    "h3":       ("sans",    20, 28, 650, "-0.005em"),
    "h4":       ("sans",    17, 24, 650, "0em"),
    "body-lg":  ("sans",    17, 28, 400, "0em"),
    "body":     ("sans",    15, 24, 400, "0em"),
    "body-sm":  ("sans",    14, 20, 400, "0em"),
    "label":    ("sans",    14, 20, 600, "0.005em"),
    "helptext": ("sans",    13, 18, 400, "0.005em"),
    "caption":  ("sans",    12, 16, 500, "0.02em"),
    "code":     ("mono",    13, 20, 450, "0em"),
}
MOTION = {
    "duration": {"instant": "0ms", "fast": "120ms", "base": "200ms", "slow": "320ms", "slower": "480ms"},
    "easing": {"standard": [0.2, 0, 0, 1], "enter": [0, 0, 0.2, 1], "exit": [0.4, 0, 1, 1], "linear": [0, 0, 1, 1]},
}
DENSITY = {
    # control-height sm/md/lg, padding-x, padding-y(textarea), gap campo, fila tabla, celda x, objetivo mínimo,
    # tamaño de fuente del control, interlineado del cuerpo, gap de stack, icon size
    "comfortable": dict(h_sm=32, h_md=40, h_lg=48, pad_x=12, pad_y=8, field_gap=6, stack=20, row=44, cell_x=12,
                         target=40, font=15, line=1.6, icon=20, label=14, help=13),
    "compact":     dict(h_sm=28, h_md=32, h_lg=40, pad_x=8, pad_y=6, field_gap=4, stack=12, row=32, cell_x=8,
                         target=24, font=14, line=1.45, icon=16, label=13, help=12),
    "field":       dict(h_sm=48, h_md=56, h_lg=64, pad_x=16, pad_y=12, field_gap=8, stack=24, row=60, cell_x=16,
                         target=56, font=18, line=1.55, icon=24, label=16, help=15),
}

# ------------------------------------------------------------- emit
def main():
    os.makedirs(OUT, exist_ok=True)
    theme_data = {}
    for tid, spec in THEMES.items():
        prim, sem, elev = build_theme(tid, spec)
        checks = run_checks(prim, sem)
        fails = [c for c in checks if not c["ok"]]
        theme_data[tid] = dict(prim=prim, sem=sem, elev=elev, checks=checks, hue=hue_report(prim, sem), spec=spec)
        print(f"{tid:14s} checks={len(checks)} fails={len(fails)} ia={theme_data[tid]['hue']}")
        for f in fails:
            print("   FAIL", f)

    # -------- tokens.json (W3C Design Tokens Community Group format)
    def c(v):
        return {"$type": "color", "$value": v}
    doc = {
        "$description": "Fundación del design system. Fuente de verdad. Formato W3C Design Tokens (DTCG). "
                        "Capas: primitive (crudo, por tema) -> semantic (por tema) -> component (por densidad).",
        "primitive": {
            "color": {tid: {k.replace("neutral-", "neutral/") if False else k: c(v) for k, v in d["prim"].items()} for tid, d in theme_data.items()},
            "space": {str(s): {"$type": "dimension", "$value": f"{s}px"} for s in SPACE},
            "radius": {k: {"$type": "dimension", "$value": v} for k, v in RADIUS.items()},
            "border-width": {k: {"$type": "dimension", "$value": v} for k, v in BORDER_W.items()},
            "font-family": {k: {"$type": "fontFamily", "$value": v} for k, v in FONTS.items()},
            "duration": {k: {"$type": "duration", "$value": v} for k, v in MOTION["duration"].items()},
            "easing": {k: {"$type": "cubicBezier", "$value": v} for k, v in MOTION["easing"].items()},
        },
        "typography": {
            r: {"$type": "typography", "$value": {
                "fontFamily": "{primitive.font-family.%s}" % fam, "fontSize": f"{sz}px",
                "lineHeight": round(lh / sz, 3), "fontWeight": wt, "letterSpacing": ls}}
            for r, (fam, sz, lh, wt, ls) in TYPE.items()
        },
        "theme": {},
        "density": {},
    }
    for tid, d in theme_data.items():
        node = {"$description": d["spec"]["notes"], "$extensions": {"mx.ds.mode": d["spec"]["mode"], "mx.ds.name": d["spec"]["name"]}}
        for key, pname in d["sem"].items():
            group, name = key.split("/")
            node.setdefault(group, {})[name] = c("{primitive.color.%s.%s}" % (tid, pname))
        for key, v in d["elev"].items():
            group, name = key.split("/")
            node.setdefault(group, {})[name] = {"$type": "shadow", "$value": v,
                                                "$extensions": {"mx.ds.note": "valor CSS de box-shadow"}}
        doc["theme"][tid] = node
    for did, dd in DENSITY.items():
        doc["density"][did] = {
            "control": {
                "height-sm": {"$type": "dimension", "$value": f"{dd['h_sm']}px"},
                "height-md": {"$type": "dimension", "$value": f"{dd['h_md']}px"},
                "height-lg": {"$type": "dimension", "$value": f"{dd['h_lg']}px"},
                "padding-x": {"$type": "dimension", "$value": f"{dd['pad_x']}px"},
                "padding-y": {"$type": "dimension", "$value": f"{dd['pad_y']}px"},
                "font-size": {"$type": "dimension", "$value": f"{dd['font']}px"},
                "icon-size": {"$type": "dimension", "$value": f"{dd['icon']}px"},
            },
            "field": {
                "gap": {"$type": "dimension", "$value": f"{dd['field_gap']}px"},
                "stack": {"$type": "dimension", "$value": f"{dd['stack']}px"},
                "label-size": {"$type": "dimension", "$value": f"{dd['label']}px"},
                "help-size": {"$type": "dimension", "$value": f"{dd['help']}px"},
            },
            "table": {
                "row-height": {"$type": "dimension", "$value": f"{dd['row']}px"},
                "cell-padding-x": {"$type": "dimension", "$value": f"{dd['cell_x']}px"},
            },
            "target": {"min": {"$type": "dimension", "$value": f"{dd['target']}px"}},
            "text": {"line-height": {"$type": "number", "$value": dd["line"]}},
        }
    with open(os.path.join(OUT, "tokens.json"), "w", encoding="utf-8") as fh:
        json.dump(doc, fh, ensure_ascii=False, indent=2)

    # -------- themes.css
    L = []
    L.append("/* themes.css — generado desde tokens.json. No editar a mano: edite tokens.json/gen_tokens.py.\n"
             "   Uso: <html data-theme=\"signal-blue\" data-density=\"compact\">\n"
             "   Capas: --ds-p-* primitivos (no usar en componentes) · --ds-* semánticos · --ds-control-* etc. de componente. */")
    L.append(":root {")
    L.append("  color-scheme: light;")
    L.append("  /* ---- tipografía */")
    for k, v in FONTS.items():
        L.append(f"  --ds-font-{k}: {v};")
    for r, (fam, sz, lh, wt, ls) in TYPE.items():
        L.append(f"  --ds-type-{r}-family: var(--ds-font-{fam}); --ds-type-{r}-size: {sz/16:.4g}rem; --ds-type-{r}-line: {lh/sz:.4g}; --ds-type-{r}-weight: {wt}; --ds-type-{r}-tracking: {ls};")
    L.append("  /* ---- espaciado (base 4px) */")
    L.append("  " + " ".join(f"--ds-space-{s}: {s/16:g}rem;" if s else "--ds-space-0: 0;" for s in SPACE))
    L.append("  /* ---- radios y bordes */")
    L.append("  " + " ".join(f"--ds-radius-{k}: {v};" for k, v in RADIUS.items()))
    L.append("  " + " ".join(f"--ds-border-{k}: {v};" for k, v in BORDER_W.items()))
    L.append("  /* ---- movimiento */")
    L.append("  " + " ".join(f"--ds-duration-{k}: {v};" for k, v in MOTION["duration"].items()))
    L.append("  " + " ".join(f"--ds-ease-{k}: cubic-bezier({', '.join(str(x) for x in v)});" for k, v in MOTION["easing"].items()))
    L.append("  /* ---- capas de apilamiento */")
    L.append("  --ds-z-sticky: 100; --ds-z-drawer: 400; --ds-z-modal: 500; --ds-z-popover: 600; --ds-z-toast: 700; --ds-z-tooltip: 800;")
    L.append("  /* ---- primitivos de color por tema (NO consumir en componentes) */")
    for tid, d in theme_data.items():
        L.append("  " + " ".join(f"--ds-p-{tid}-{k}: {v};" for k, v in d["prim"].items()))
    L.append("}")
    L.append("")
    L.append("@media (prefers-reduced-motion: reduce) {\n  :root { --ds-duration-fast: 0ms; --ds-duration-base: 0ms; --ds-duration-slow: 0ms; --ds-duration-slower: 0ms; }\n}")
    L.append("")
    first = True
    for tid, d in theme_data.items():
        sel = f':root, [data-theme="{tid}"]' if first else f'[data-theme="{tid}"]'
        first = False
        L.append(f"/* ---- tema {d['spec']['name']} ({'oscuro' if d['spec']['mode']=='dark' else 'claro'}) */")
        L.append(sel + " {")
        L.append(f"  color-scheme: {d['spec']['mode']};")
        for key, pname in d["sem"].items():
            L.append(f"  --ds-{key.replace('/', '-')}: var(--ds-p-{tid}-{pname});")
        for key, v in d["elev"].items():
            L.append(f"  --ds-{key.replace('/', '-')}: {v};")
        L.append("}")
    L.append("")
    for i, (did, dd) in enumerate(DENSITY.items()):
        sel = f':root, [data-density="{did}"]' if i == 0 else f'[data-density="{did}"]'
        L.append(sel + " {")
        L.append(f"  --ds-control-height-sm: {dd['h_sm']/16:g}rem; --ds-control-height-md: {dd['h_md']/16:g}rem; --ds-control-height-lg: {dd['h_lg']/16:g}rem;")
        L.append(f"  --ds-control-padding-x: {dd['pad_x']/16:g}rem; --ds-control-padding-y: {dd['pad_y']/16:g}rem;")
        L.append(f"  --ds-control-font-size: {dd['font']/16:g}rem; --ds-control-icon-size: {dd['icon']/16:g}rem;")
        L.append(f"  --ds-field-gap: {dd['field_gap']/16:g}rem; --ds-field-stack: {dd['stack']/16:g}rem;")
        L.append(f"  --ds-field-label-size: {dd['label']/16:g}rem; --ds-field-help-size: {dd['help']/16:g}rem;")
        L.append(f"  --ds-table-row-height: {dd['row']/16:g}rem; --ds-table-cell-padding-x: {dd['cell_x']/16:g}rem;")
        L.append(f"  --ds-target-min: {dd['target']/16:g}rem; --ds-text-line-height: {dd['line']};")
        L.append("}")
    with open(os.path.join(OUT, "themes.css"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(L) + "\n")

    # -------- contrast.json (para el documento) + datos para el tipo Design System
    with open(os.path.join(OUT, "contrast.json"), "w", encoding="utf-8") as fh:
        json.dump({tid: dict(name=d["spec"]["name"], mode=d["spec"]["mode"], notes=d["spec"]["notes"],
                             checks=d["checks"], hue=d["hue"],
                             sem={k: (resolve(d["prim"], d["sem"], k, d["prim"][d["sem"]["surface/base"]])) for k in d["sem"]},
                             semRaw={k: d["prim"][v] for k, v in d["sem"].items()},
                             prim=d["prim"])
                   for tid, d in theme_data.items()}, fh, ensure_ascii=False, indent=1)
    meta = dict(space=SPACE, radius=RADIUS, border=BORDER_W, fonts=FONTS, type=TYPE, motion=MOTION, density=DENSITY)
    with open(os.path.join(OUT, "meta.json"), "w", encoding="utf-8") as fh:
        json.dump(meta, fh, ensure_ascii=False, indent=1)

if __name__ == "__main__":
    main()
