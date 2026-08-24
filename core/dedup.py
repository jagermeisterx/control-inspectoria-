"""Limpieza de duplicados: normalización de cursos, fusión de alumnos y
eliminación de registros idénticos repetidos.

Todas las funciones aceptan dry_run=True (por defecto) y devuelven un informe
sin modificar datos. Las usa la migración 0005 y el comando fusionar_duplicados.
"""
import re
import unicodedata

from django.db.models import Count, Min

from core.cursos_norm import normalizar_curso
from core.models import (
    Alumno, Retiro, Atraso, ControlUniforme, Celular, VisitaApoderado,
)

RELACIONES = ["retiros", "atrasos", "uniformes", "celulares", "llamadas"]

REGISTROS = [
    (Retiro, ["alumno_id", "fecha", "hora", "motivo", "persona_retira"]),
    (Atraso, ["alumno_id", "fecha", "hora", "tipo", "lugar"]),
    (ControlUniforme, ["alumno_id", "fecha", "falta"]),
    (Celular, ["alumno_id", "fecha", "lugar_entregado", "retiro"]),
    (VisitaApoderado, ["fecha", "hora", "destino", "funcionario"]),
]

def _norm(s):
    t = unicodedata.normalize("NFD", (s or "").strip())
    t = "".join(c for c in t if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", t.upper())


def normalizar_cursos_todos(dry_run=True):
    """Ajusta Alumno.curso al formato canónico cuando es mapeable."""
    cambios, desconocidos = [], set()
    for a in Alumno.objects.exclude(curso=""):
        canon = normalizar_curso(a.curso)
        if canon is None:
            desconocidos.add(a.curso)
        elif canon != a.curso:
            cambios.append((a.pk, a.nombre, a.apellido, a.curso, canon))
            if not dry_run:
                a.curso = canon
                a.save(update_fields=["curso"])
    return {"cambios": cambios, "desconocidos": sorted(desconocidos)}


def _conteos_por_alumno():
    conteo = {}
    for rel in RELACIONES:
        for fila in Alumno.objects.values("id").annotate(n=Count(rel)):
            conteo.setdefault(fila["id"], {})[rel] = fila["n"]
    return conteo


def fusionar_alumnos(dry_run=True):
    """Fusiona alumnos con mismo nombre+apellido+año (normalizados).

    Conserva: activo > más registros vinculados > id más antiguo.
    Re-asigna retiros/atrasos/uniformes/celulares/llamadas al conservado,
    le fija curso canónico y elimina los duplicados.
    """
    grupos = {}
    for a in Alumno.objects.order_by("id"):
        grupos.setdefault((_norm(a.nombre), _norm(a.apellido), a.anio), []).append(a)

    conteos = _conteos_por_alumno()
    informe = []

    for (_nom, _ape, anio), lista in grupos.items():
        if len(lista) < 2:
            continue

        def registros_de(a):
            return sum(conteos.get(a.id, {}).values())

        keeper = sorted(lista, key=lambda a: (not a.activo, -registros_de(a), a.id))[0]
        perdedores = [a for a in lista if a.pk != keeper.pk]
        movidos = {r: sum(conteos.get(a.id, {}).get(r, 0) for a in perdedores) for r in RELACIONES}

        informe.append({
            "keeper": keeper,
            "perdedores": perdedores,
            "anio": anio,
            "movidos": movidos,
        })

        if dry_run:
            continue

        curso_canon = normalizar_curso(keeper.curso)
        if curso_canon:
            keeper.curso = curso_canon
        else:
            for a in perdedores:
                cand = normalizar_curso(a.curso)
                if cand:
                    keeper.curso = cand
                    break
        keeper.save(update_fields=["curso"])

        for rel in RELACIONES:
            for a in perdedores:
                getattr(a, rel).update(alumno=keeper)

        Alumno.objects.filter(pk__in=[a.pk for a in perdedores]).delete()

    return informe


def eliminar_registros_repetidos(dry_run=True):
    """Elimina filas idénticas (mismo contenido) dejando la más antigua."""
    informe = []
    for model, campos in REGISTROS:
        grupos = (
            model.objects.values(*campos)
            .annotate(n=Count("id"), min_id=Min("id"))
            .filter(n__gt=1)
        )
        ids_borrar = []
        for g in grupos:
            filtro = {c: g[c] for c in campos}
            ids_borrar.extend(
                model.objects.filter(**filtro).exclude(id=g["min_id"]).values_list("id", flat=True)
            )
        informe.append({"modelo": model.__name__, "grupos": len(grupos), "borrados": len(ids_borrar)})
        if ids_borrar and not dry_run:
            model.objects.filter(id__in=ids_borrar).delete()
    return informe
