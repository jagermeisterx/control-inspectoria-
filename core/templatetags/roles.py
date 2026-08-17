from django import template

from core.roles import tiene_rol

register = template.Library()


@register.filter(name="tiene_rol")
def tiene_rol_filter(user, roles):
    if not roles:
        return False
    return tiene_rol(user, *(r.strip() for r in roles.split(",")))


@register.filter(name="get_item")
def get_item(d, key):
    try:
        return d.get(key)
    except (AttributeError, TypeError):
        return None
