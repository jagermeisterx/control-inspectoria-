from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

ADMIN = "admin"
INSPECTOR_GENERAL = "inspector_general"
INSPECTOR = "inspector"
PROFESOR = "profesor"
DIRECTOR = "director"

GRUPOS = (INSPECTOR_GENERAL, INSPECTOR, PROFESOR, DIRECTOR)


def es_admin(user):
    if not user or not getattr(user, "is_authenticated", False):
        return False
    return bool(user.is_superuser)


def tiene_rol(user, *roles):
    if es_admin(user):
        return True
    if not user or not getattr(user, "is_authenticated", False):
        return False
    return user.groups.filter(name__in=roles).exists()


def rol_requerido(*roles):
    """Restringe una vista a los roles indicados (el superusuario siempre pasa)."""
    def decorator(view):
        @wraps(view)
        @login_required
        def wrapper(request, *args, **kwargs):
            if tiene_rol(request.user, *roles):
                return view(request, *args, **kwargs)
            messages.error(request, "No tienes permisos para acceder a esta sección.")
            return redirect("dashboard")
        return wrapper
    return decorator
