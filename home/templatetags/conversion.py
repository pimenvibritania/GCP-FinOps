from django import template

from api.utils.conversion import Conversion

register = template.Library()


@register.filter
def idr_format(value):
    return Conversion.idr_format(value)
