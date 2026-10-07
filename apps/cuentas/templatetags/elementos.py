"""Filtros que traducen las etiquetas (tags) de los elementos de django-allauth a las
clases de la hoja de estilos del proyecto.

django-allauth marca sus botones con etiquetas como ``prominent``, ``danger`` u ``outline``,
y sus estados con ``success``, ``warning`` o ``danger``. Las plantillas de
templates/allauth/elements/ usan estos filtros para elegir la clase correspondiente.
"""

from django import template

register = template.Library()

_ETIQUETAS_PELIGRO = {"danger", "delete"}
_ETIQUETAS_SECUNDARIAS = {"outline", "secondary", "link"}
_ETIQUETAS_PRINCIPALES = {"prominent", "primary"}
_CLASES_ESTADO = {
    "success": "estado--exito",
    "warning": "estado--advertencia",
    "danger": "estado--error",
}


@register.filter(name="clase_boton")
def obtener_clase_boton(etiquetas: list[str] | None, tipo: str | None) -> str:
    """Devuelve la clase de variante de un botón, o una cadena vacía para el secundario.

    Un botón de envío sin etiquetas es la acción principal de su página: django-allauth
    etiqueta siempre los botones secundarios y destructivos.
    """
    etiquetas = set(etiquetas or ())
    if etiquetas & _ETIQUETAS_PELIGRO:
        return "boton--peligro"
    if etiquetas & _ETIQUETAS_SECUNDARIAS:
        return ""
    if etiquetas & _ETIQUETAS_PRINCIPALES or (not etiquetas and tipo == "submit"):
        return "boton--principal"
    return ""


@register.filter(name="clase_estado")
def obtener_clase_estado(etiquetas: list[str] | None) -> str:
    """Devuelve la clase del indicador de un estado, o una cadena vacía si no tiene."""
    for etiqueta in etiquetas or ():
        if etiqueta in _CLASES_ESTADO:
            return _CLASES_ESTADO[etiqueta]
    return ""
