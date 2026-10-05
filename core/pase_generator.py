"""
Generador del Pase de autorización de ingreso a clases — Inspectoría General

Reproduce el pase físico de la carpeta actualizacion-datps/pase-ejemplo.jpeg
en formato vertical de 80 mm para impresora POS (bobina térmica).

El pase original es apaisado; acá los campos se reordenan en vertical porque
la bobina POS imprime de lado a lado. La sección "TIMBRE Y FIRMA" se imprime
como línea punteada vacía, para completar a mano.
"""
import io

from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas as pdfcanvas

# ── Configuración de la bobina ──
ANCHO_MM = 80
ALTO_MM = 100          # altura del pase; deja ~16 mm libres bajo la firma
MARGEN_MM = 4
SANGRIA_MM = 3          # sangría de los rótulos respecto del borde

# ── Datos de cabecera del colegio (según pase físico) ──
COLEGIO = "Escuela Particular Alemana"
DIRECCION = "Camilo Henriquez 125-Pallaco"
EMAIL = "Email: escalemana@gmail.com"
TITULO = "AUTORIZACION INGRESO A CLASES"

# ── Tipografía ──
FUENTE = "Helvetica"
FUENTE_BOLD = "Helvetica-Bold"
F_TITULO_PASSE = 10
F_CABECERA = 9
F_SUBTITULO = 7
F_ROTULO = 8
F_VALOR = 9

NEGRO = colors.HexColor("#1A1A1A")
GRIS = colors.HexColor("#666666")
DORADO = colors.HexColor("#C5A000")

# Separación vertical entre bloques de campos
SALTO_ROTULO = 3.2 * mm      # rótulo → línea de relleno
ALTO_CAMPO = 9.0 * mm       # línea de relleno → siguiente rótulo

ANCHO_UTIL = ANCHO_MM * mm - 2 * MARGEN_MM * mm
X_ETIQUETAS = MARGEN_MM * mm + SANGRIA_MM * mm
X_VALOR = X_ETIQUETAS
X_Linea = ANCHO_MM * mm - MARGEN_MM * mm

_CORTE_Y = 6 * mm            # marca de corte inferior
_ALTO_TRAZO = 0.3


def _linea_punteada(c, x, y, x2, color=NEGRO, grosor=_ALTO_TRAZO, guion=0.9):
    """Línea punteada horizontal, usada para rellenar a mano los campos."""
    c.saveState()
    c.setStrokeColor(color)
    c.setLineWidth(grosor)
    c.setDash(guion * mm, 1.2 * mm)
    c.line(x, y, x2, y)
    c.restoreState()


def _recortar(c, texto, ancho_max, fuente=FUENTE, size=F_VALOR):
    """Corta el texto con puntos suspensivos si excede el ancho disponible."""
    texto = (texto or "").strip()
    if not texto:
        return ""
    if c.stringWidth(texto, fuente, size) <= ancho_max:
        return texto
    puntos = "…"
    while texto and c.stringWidth(texto + puntos, fuente, size) > ancho_max:
        texto = texto[:-1].rstrip()
    return (texto + puntos) if texto else ""


def _centrado(c, texto, y, fuente=FUENTE_BOLD, size=F_CABECERA, color=NEGRO):
    c.setFont(fuente, size)
    c.setFillColor(color)
    c.drawCentredString(ANCHO_MM * mm / 2, y, texto)


def _campo(c, rotulo, valor, y, linea=True):
    """Dibuja rótulo en negrita + línea punteada con el valor.

    Si valor viene en lista, se dibuja en varias líneas (una por elemento).
    Devuelve la coordenada Y lista para el siguiente campo.
    """
    c.setFont(FUENTE_BOLD, F_ROTULO)
    c.setFillColor(NEGRO)
    c.drawString(X_ETIQUETAS, y, rotulo)

    y_linea = y - SALTO_ROTULO
    if linea:
        _linea_punteada(c, X_Linea, y_linea, X_Linea, NEGRO)

    if valor:
        valores = valor if isinstance(valor, (list, tuple)) else [valor]
        c.setFont(FUENTE, F_VALOR)
        c.setFillColor(NEGRO)
        for v in valores:
            c.drawString(X_VALOR, y_linea, _recortar(c, v, ANCHO_UTIL, FUENTE, F_VALOR))
            y_linea -= 4.4 * mm

    return y - ALTO_CAMPO


def generar_pdf_pase(alumno, atraso=None):
    """Genera el pase de autorización en PDF de 80 mm y devuelve un BytesIO.

    alumno : instancia de core.models.Alumno
    atraso : instancia de core.models.Atraso (opcional; si falta, usa fecha/hora
             vacías y el motivo por defecto)
    """
    buf = io.BytesIO()
    c = pdfcanvas.Canvas(buf, pagesize=(ANCHO_MM * mm, ALTO_MM * mm))
    c.setTitle(f"Pase {alumno.nombre_completo}")

    margen = MARGEN_MM * mm
    y = ALTO_MM * mm - margen - 2 * mm

    # ── Encabezado del colegio ──
    _centrado(c, COLEGIO, y, FUENTE_BOLD, F_CABECERA, NEGRO)
    y -= 3.6 * mm
    _centrado(c, DIRECCION, y, FUENTE, F_SUBTITULO, GRIS)
    y -= 3.2 * mm
    _centrado(c, EMAIL, y, FUENTE, F_SUBTITULO, GRIS)
    y -= 3.2 * mm

    _linea_punteada(c, margen, y, ANCHO_MM * mm - margen, DORADO, 0.5, guion=2.0)
    y -= 5.5 * mm

    # ── Título ──
    _centrado(c, TITULO, y, FUENTE_BOLD, F_TITULO_PASSE, NEGRO)
    y -= 8 * mm

    # ── Datos del pase ──
    fecha = atraso.fecha.strftime("%d/%m/%Y") if atraso else ""
    hora = atraso.hora.strftime("%H:%M") if atraso and atraso.hora else ""
    curso = alumno.curso or ""
    if alumno.es_campo:
        curso = f"{curso} (CAMPO)".strip()

    motivo = atraso.motivo if atraso else ""
    if atraso and atraso.lugar:
        motivo = f"{motivo} · {atraso.lugar}".strip(" ·")
    if atraso and atraso.observacion:
        motivo = f"{motivo} · {atraso.observacion}".strip(" ·")

    y = _campo(c, "FECHA:", fecha, y)
    y = _campo(c, "NOMBRE ALUMNO:", alumno.nombre_completo.upper(), y)
    y = _campo(c, "CURSO:", curso, y)
    y = _campo(c, "HORA:", hora, y)
    y = _campo(c, "MOTIVO:", motivo, y)

    # ── Timbre y firma (se deja en blanco para completar a mano) ──
    _campo(c, "TIMBRE Y FIRMA:", None, y)

    # ── Marca de corte para la impresora POS ──
    _linea_punteada(c, margen, _CORTE_Y, ANCHO_MM * mm - margen, GRIS, 0.3, guion=3.0)

    c.showPage()
    c.save()
    buf.seek(0)
    return buf