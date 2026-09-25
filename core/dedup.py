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


def _tokens(a):
    """Tokens normalizados (minúsculas, sin acentos) del nombre+apellido completos."""
    return _norm(f"{a.nombre} {a.apellido}").split()


def fusionar_alumnos_por_subset(dry_run=True, solo_mismo_curso=True):
    """Fusión de alumnos 'cortos' hacia el canónico de nombre completo.

    Detecta alumnos con nombre abreviado (solo primer nombre + primer apellido,
    p.ej. 'AGUSTIN VEGA') frente a un canónico de matrícula con nombre completo
    ('AGUSTIN CRISTOBAL VEGA ALARCON'). Ya no depende del id: el "corto" es el
    registro con menos tokens y el canónico el que los contiene y tiene más.

    Criterio: mismo anio + mismo curso (salvo solo_mismo_curso=False) + el
    conjunto de tokens del corto está CONTENIDO en el del canónico (que debe
    tener más tokens). Se conserva el canónico de nombre completo, se reasignan
    todos sus registros vinculados y se elimina el corto.

    Devuelve (informe, pendientes):
      informe  : lista de dicts con keeper/perdedores/movidos por grupo.
      pendientes: lista de IDs cortos que no matchearon ningún canónico
                  (con solo_mismo_curso=True los de curso distinto quedan aquí).
    """
    conteos = _conteos_por_alumno()

    alumnos = [a for a in Alumno.objects.order_by("id")]

    informe = []
    pendientes = []
    ya_procesado = set()
    for corto in alumnos:
        if corto.id in ya_procesado:
            continue
        t_corto = _tokens(corto)
        candidatos = [
            c for c in alumnos if c.pk != corto.pk
            if c.anio == corto.anio
            and (not solo_mismo_curso or c.curso == corto.curso)
            and len(t_corto) < len(_tokens(c))
            and set(t_corto) <= set(_tokens(c))
        ]
        if not candidatos:
            pendientes.append(corto.id)
            continue

        def pn(c):
            return _norm(c.nombre).split()[0]

        candidatos.sort(
            key=lambda c: (c.curso != corto.curso, pn(c) != pn(corto), c.id)
        )
        keeper = candidatos[0]
        perdedores = [corto]

        movidos = {r: conteos.get(corto.id, {}).get(r, 0) for r in RELACIONES}
        informe.append({
            "keeper": keeper,
            "perdedores": perdedores,
            "anio": corto.anio,
            "movidos": movidos,
        })
        ya_procesado.add(corto.id)

        if dry_run:
            continue

        curso_canon = normalizar_curso(keeper.curso)
        if curso_canon:
            keeper.curso = curso_canon
            keeper.save(update_fields=["curso"])

        for rel in RELACIONES:
            getattr(corto, rel).update(alumno=keeper)

        corto.delete()

    return informe, pendientes


def _levenshtein(a, b, max_dist=1):
    """Distancia de Levenshtein recortada a max_dist (max_dist+1 si la excede)."""
    if a == b:
        return 0
    if abs(len(a) - len(b)) > max_dist:
        return max_dist + 1
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i] + [0] * len(b)
        for j, cb in enumerate(b, 1):
            cur[j] = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb))
        prev = cur
    return prev[len(b)]


def _fuzzy_equiv(tokens_a, tokens_b):
    """True si cada token de A matchea un token DISTINTO de B (sin orden) a <=1 edición."""
    restantes = list(tokens_b)
    for ta in tokens_a:
        for i, tb in enumerate(restantes):
            if _levenshtein(ta, tb) <= 1:
                restantes.pop(i)
                break
        else:
            return False
    return True


GENERO = {
    "FRANCISCA": "FRANCISCO", "FRANCISCO": "FRANCISCA",
    "RENATA": "RENATO", "RENATO": "RENATA",
    "JAVIERA": "JAVIER", "JAVIER": "JAVIERA",
    "MARTINA": "MARTIN", "MARTIN": "MARTINA",
    "PAOLA": "PAOLO", "PAOLO": "PAOLA",
}


def _es_genero(tokens_a, tokens_b):
    """True si el matching entre tokens sugiere un cambio de género (p.ej. FRANCISCA/FRANCISCO)."""
    restantes = list(tokens_b)
    for ta in tokens_a:
        for i, tb in enumerate(restantes):
            if _levenshtein(ta, tb) <= 1:
                restantes.pop(i)
                if GENERO.get(ta) == tb or GENERO.get(tb) == ta:
                    return True
                break
    return False


def fusionar_alumnos_fuzzy(dry_run=True):
    """Fusión de alumnos del MISMO curso cuyo nombre+apellido difieren por typos
    o variantes ortográficas: se matchea cada token a <=1 edición (sin importar
    el orden), agrupando en componentes conexas por (anio, curso).

    Se conserva el registro con MÁS tokens (el de mayor información); a él se
    le reasignan atrasos/retiros/uniformes/celulares/llamadas y se eliminan los
    sobrantes.

    Devuelve (auto, manual):
      auto   : [(keeper, [perdedores, ...]), ...] de alta confianza (el keeper
               tiene estrictamente más tokens y no hay cambio de género).
      manual : lista de grupos (listas de Alumno) que requieren decisión humana:
               igual cantidad de tokens o diferencia de género entre registros.
    """
    alumnos = list(Alumno.objects.order_by("id"))
    por_curso = {}
    for a in alumnos:
        por_curso.setdefault((a.anio, a.curso), []).append(a)

    conteos = _conteos_por_alumno()
    auto, manual = [], []
    for (anio, curso), lista in por_curso.items():
        if len(lista) < 2:
            continue
        tokens = [_tokens(a) for a in lista]
        padre = list(range(len(lista)))

        def find(x):
            while padre[x] != x:
                padre[x] = padre[padre[x]]
                x = padre[x]
            return x

        def mismos_tokens(ti, tj):
            if ti == tj:
                return False
            if len(ti) < len(tj):
                return _fuzzy_equiv(ti, tj)
            if len(tj) < len(ti):
                return _fuzzy_equiv(tj, ti)
            return _fuzzy_equiv(ti, tj)

        for i in range(len(lista)):
            for j in range(i + 1, len(lista)):
                if mismos_tokens(tokens[i], tokens[j]):
                    ri, rj = find(i), find(j)
                    if ri != rj:
                        padre[rj] = ri

        componentes = {}
        for i in range(len(lista)):
            componentes.setdefault(find(i), []).append(lista[i])

        for miembros in componentes.values():
            if len(miembros) < 2:
                continue
            mx = max(len(_tokens(m)) for m in miembros)
            completos = [m for m in miembros if len(_tokens(m)) == mx]
            if len(completos) != 1:
                manual.append(miembros)
                continue
            keeper = completos[0]
            perdedores = [m for m in miembros if m is not keeper]
            if any(len(_tokens(p)) == mx for p in perdedores) or any(
                _es_genero(_tokens(p), _tokens(keeper)) for p in perdedores
            ):
                manual.append(miembros)
                continue

            movidos = {
                r: sum(conteos.get(p.id, {}).get(r, 0) for p in perdedores)
                for r in RELACIONES
            }
            auto.append({"keeper": keeper, "perdedores": perdedores, "anio": anio, "movidos": movidos})

            if dry_run:
                continue
            for rel in RELACIONES:
                for p in perdedores:
                    getattr(p, rel).update(alumno=keeper)
            Alumno.objects.filter(pk__in=[p.pk for p in perdedores]).delete()

    return auto, manual


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
