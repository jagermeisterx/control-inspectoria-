"""Búsqueda de texto insensible a acentos (y a mayúsculas).

Postgres usa la extensión `unaccent` (creada en la migración 0009).
SQLite (desarrollo/tests) registra una función equivalente en Python,
así el SQL y la semántica son idénticos en ambos motores.
"""
import unicodedata

from django.db.models.lookups import PatternLookup


def django_unaccent(value):
    """Quita diacríticos y pasa a minúsculas (función SQL para SQLite)."""
    if value is None:
        return None
    t = unicodedata.normalize("NFD", str(value))
    t = "".join(c for c in t if not unicodedata.combining(c))
    return t.lower()


def registrar_funciones_sqlite(connection, **kwargs):
    """Señal connection_created: instala django_unaccent() en SQLite."""
    if connection.vendor != "sqlite":
        return
    connection.connection.create_function("django_unaccent", 1, django_unaccent)


class UnaccentIContains(PatternLookup):
    """Igual que `icontains` pero sin distinguir acentos ni mayúsculas.

    Uso: Model.objects.filter(nombre__unaccent_icontains="jose")
    → matchea JOSÉ, josè, JOSE...
    """

    lookup_name = "unaccent_icontains"

    def as_sql(self, compiler, connection):
        lhs, lhs_params = self.process_lhs(compiler, connection)
        rhs, rhs_params = self.process_rhs(compiler, connection)
        params = lhs_params + rhs_params
        if connection.vendor == "postgresql":
            return (
                "lower(unaccent({0})) LIKE lower(unaccent({1}))".format(lhs, rhs),
                params,
            )
        return (
            "lower(django_unaccent({0})) LIKE lower(django_unaccent({1}))".format(lhs, rhs),
            params,
        )


# Registro del lookup en los campos de texto (al importar el módulo).
from django.db import models  # noqa: E402

models.CharField.register_lookup(UnaccentIContains)
models.TextField.register_lookup(UnaccentIContains)
