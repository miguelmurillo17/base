"""Renderizador de formularios del proyecto.

Todos los formularios se muestran con las plantillas de templates/formularios/: etiqueta
visible encima del campo, texto de ayuda y errores junto al campo que los provoca, y un
resumen de los errores generales al inicio.
"""

from django.forms.renderers import TemplatesSetting


class RenderizadorFormularios(TemplatesSetting):
    form_template_name = "formularios/formulario.html"
    field_template_name = "formularios/campo.html"
