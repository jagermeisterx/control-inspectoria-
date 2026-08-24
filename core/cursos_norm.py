"""Normalización de nombres de curso al formato canónico de CURSOS.

Acepta variantes reales encontradas en producción:
"Sexto Básico A", "cuarto medio A", "IV MEDIO", "5° BASICO", "7 BASICO",
"Prekinder A", "Kinder A", "MEDIO II", etc.
Devuelve None cuando no puede mapear (el llamador decide qué hacer).
"""
import re
import unicodedata

PALABRAS_A_NIVEL = {
    "PRIMERO": 1, "PRIMER": 1,
    "SEGUNDO": 2,
    "TERCERO": 3,
    "CUARTO": 4,
    "QUINTO": 5,
    "SEXTO": 6,
    "SEPTIMO": 7,
    "OCTAVO": 8,
    "NOVENO": 9,
    "DECIMO": 10,
}

ROMANOS = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5, "VI": 6, "VII": 7, "VIII": 8, "IX": 9, "X": 10}
ROMANOS_INVERSO = {v: k for k, v in ROMANOS.items()}


def _limpiar(texto):
    t = unicodedata.normalize("NFD", str(texto or ""))
    t = "".join(c for c in t if not unicodedata.combining(c)).upper()
    t = re.sub(r"[.\u00ba\u00b0°º_\-]", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def normalizar_curso(texto):
    """Convierte variantes de curso al código canónico; None si no reconoce."""
    if texto is None:
        return None
    t = _limpiar(texto)
    if not t:
        return None

    tokens = [
        tok for tok in t.split()
        if not (len(tok) == 1 and tok.isalpha() and tok not in ROMANOS)
    ]
    joined = "".join(tokens)
    if joined == "PREKINDER":
        return "PRE-KINDER"
    if joined == "KINDER":
        return "KINDER"

    etapa = None
    nivel = None
    patron_ordinal = re.compile(r"^(\d{1,2})(?:RO|DO|ER|TO|MO|VO|NO)?$")
    for tok in tokens:
        if "BASIC" in tok:
            etapa = "BASICO"
        elif "MEDI" in tok:
            etapa = "MEDIO"
            continue
        m = patron_ordinal.match(tok)
        if m and 1 <= int(m.group(1)) <= 10 and nivel is None:
            nivel = int(m.group(1))
        elif tok in PALABRAS_A_NIVEL and nivel is None:
            nivel = PALABRAS_A_NIVEL[tok]
        elif tok in ROMANOS and nivel is None:
            nivel = ROMANOS[tok]

    if etapa == "BASICO" and nivel:
        return f"{nivel}\u00b0 BÁSICO"
    if etapa == "MEDIO" and nivel:
        return f"{ROMANOS_INVERSO[nivel]}\u00b0 MEDIO"
    return None
