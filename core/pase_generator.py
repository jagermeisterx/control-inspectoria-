"""
Generador del Pase de autorización de ingreso a clases — Inspectoría General

Reproduce el pase físico de la carpeta actualizacion-datps/pase-ejemplo.jpeg
en formato vertical de 80 mm para impresora POS (bobina térmica).

El pase original es apaisado; acá los campos se reordenan en vertical porque
la bobina POS imprime de lado a lado. La sección "TIMBRE Y FIRMA" se imprime
como línea punteada vacía, para completar a mano.

Diseño pensado para térmico en blanco y negro:
  · solo negro puro (#000000): los grises se tramadan y salen borrosos
  · los valores van en negrita a 11 pt, los rótulos a 9 pt
  · los campos no llevan línea punteada, así el texto nunca pisa una línea
  · el logo se usa en una copia binaria (static/img/logo_pase.png) para que
    se imprima como mancha negra sólida y no como gris ditherizado
"""
import io
import os

from django.conf import settings

from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas as pdfcanvas

# ── Configuración de la bobina ──
ANCHO_MM = 80
ALTO_MM = 110
# Los cabezales POS no imprimen hasta el borde de la bobina de 80 mm y el
# corte a la izquierda salía más marcado, así que el margen va generoso.
MARGEN_X = 11
MARGEN_Y = 4

# ── Encabezado ──
LOGO_ALTO_MM = 15
GAP_LOGO_TITULO = 6.0 * mm   # borde inferior del logo → baseline del título
GAP_TITULO_REGLA = 3.5 * mm  # baseline del título → regla
GAP_REGLA_ROTULO = 4.5 * mm  # regla → primer rótulo

TITULO = "AUTORIZACION INGRESO A CLASES"

# ── Tipografía ──
FUENTE = "Helvetica"
FUENTE_BOLD = "Helvetica-Bold"
F_TITULO = 9  # 11 pt mide 69,4 mm y 10 pt 63,1 mm; con 58 mm útiles solo entra 9 pt (56,8 mm)
F_ROTULO = 9
F_VALOR = 11

# ── Ritmo vertical ──
SALTO_ROTULO = 5.0 * mm   # rótulo → primer valor
ALTO_CAMPO = 9.2 * mm     # rótulo → siguiente rótulo
INTERLINEADO = 4.5 * mm    # valor → valor extra (wrap)

# ── Firma y corte ──
GAP_CORTE = 6 * mm         # borde inferior → marca de corte
GROSOR_FIRMA = 0.5         # línea de firma
GROSOR_REGLA = 1.0         # regla bajo el título
GROSOR_CORTE = 0.4

NEGRO = colors.black

ANCHO_UTIL = ANCHO_MM * mm - 2 * MARGEN_X * mm
X_ETIQUETAS = MARGEN_X * mm


def _logo_pase_path():
    return os.path.join(settings.BASE_DIR, "static", "img", "logo_pase.png")


def _dibujar_logo(c, x_centro, y_top, alto=LOGO_ALTO_MM):
    """Dibuja el logo binario centrado. Devuelve la Y de su borde inferior."""
    path = _logo_pase_path()
    if not os.path.exists(path):
        return y_top
    try:
        iw, ih = ImageReader(path).getSize()
    except Exception:
        return y_top
    if not iw or not ih:
        return y_top
    h = alto * mm
    w = h * iw / ih
    c.drawImage(path, x_centro - w / 2, y_top - h, width=w, height=h)
    return y_top - h


def _linea(c, x, y, x2, grosor=GROSOR_REGLA, color=NEGRO, punteada=False):
    c.saveState()
    c.setStrokeColor(color)
    c.setLineWidth(grosor)
    if punteada:
        c.setDash(0.9 * mm, 1.2 * mm)
    c.line(x, y, x2, y)
    c.restoreState()


def _centrado(c, texto, y, fuente=FUENTE_BOLD, size=F_TITULO, color=NEGRO):
    c.setFont(fuente, size)
    c.setFillColor(color)
    c.drawCentredString(ANCHO_MM * mm / 2, y, texto)


def _cortar(c, texto, ancho_max, fuente, size):
    """Recorta con puntos suspensivos si la línea excede el ancho disponible."""
    if c.stringWidth(texto, fuente, size) <= ancho_max:
        return texto
    while texto and c.stringWidth(texto + "…", fuente, size) > ancho_max:
        texto = texto[:-1].rstrip()
    return texto + "…" if texto else ""


def _envolver(c, texto, ancho_max, max_lineas, fuente, size):
    """Parte el texto en líneas que entran en ancho_max, hasta max_lineas.

    Si sobran palabras, la última línea se corta con "…".
    """
    palabras = (texto or "").split()
    if not palabras:
        return []
    lineas, actual = [], ""
    for p in palabras:
        candidata = f"{actual} {p}".strip()
        if not actual or c.stringWidth(candidata, fuente, size) <= ancho_max:
            actual = candidata
        else:
            lineas.append(actual)
            actual = p
    if actual:
        lineas.append(actual)

    if len(lineas) > max_lineas:
        lineas = lineas[:max_lineas]
        corte = lineas[-1]
        while corte and c.stringWidth(corte + "…", fuente, size) > ancho_max:
            corte = corte[:-1].rstrip()
        lineas[-1] = corte + "…" if corte else "…"
        return lineas

    return [_cortar(c, l, ancho_max, fuente, size) for l in lineas]


def _campo(c, rotulo, valor, y, max_lineas=1):
    """Rótulo en negrita + valor en negrita debajo, sin línea punteada.

    Devuelve la Y para el siguiente rótulo.
    """
    c.setFont(FUENTE_BOLD, F_ROTULO)
    c.setFillColor(NEGRO)
    c.drawString(X_ETIQUETAS, y, rotulo)

    if not valor:
        return y - ALTO_CAMPO

    lineas = _envolver(c, valor, ANCHO_UTIL, max_lineas, FUENTE_BOLD, F_VALOR)
    c.setFont(FUENTE_BOLD, F_VALOR)
    c.setFillColor(NEGRO)
    y_val = y - SALTO_ROTULO
    for linea in lineas:
        c.drawString(X_ETIQUETAS, y_val, linea)
        y_val -= INTERLINEADO

    extra = INTERLINEADO * max(0, len(lineas) - 1)
    return y - ALTO_CAMPO - extra


def datos_pase(alumno, atraso=None):
    """Campos del pase (en mayúsculas) para compartir entre el PDF y el HTML.

    alumno : instancia de core.models.Alumno
    atraso : instancia de core.models.Atraso (opcional; si falta, los campos
             de fecha y hora quedan en blanco)
    """
    fecha = atraso.fecha.strftime("%d/%m/%Y") if atraso else ""
    hora = atraso.hora.strftime("%H:%M") if atraso and atraso.hora else ""
    curso = (alumno.curso or "").strip()
    if alumno.es_campo:
        curso = f"{curso} (CAMPO)".strip()

    motivo = (atraso.motivo if atraso else "").strip()
    if atraso:
        lugar = (atraso.lugar or "").strip()
        if lugar and lugar.upper() not in motivo.upper():
            motivo = f"{motivo} · {lugar}".strip(" ·")

    return {
        "fecha": fecha,
        "hora": hora,
        "curso": curso.upper(),
        "motivo": motivo.upper(),
        "nombre": alumno.nombre_completo.upper(),
    }


def generar_pdf_pase(alumno, atraso=None):
    """Genera el pase de autorización en PDF de 80 mm y devuelve un BytesIO.

    alumno : instancia de core.models.Alumno
    atraso : instancia de core.models.Atraso (opcional; si falta, los campos
             de fecha y hora quedan en blanco)
    """
    d = datos_pase(alumno, atraso)

    buf = io.BytesIO()
    c = pdfcanvas.Canvas(buf, pagesize=(ANCHO_MM * mm, ALTO_MM * mm))
    c.setTitle(f"Pase {alumno.nombre_completo}")

    ancho = ANCHO_MM * mm
    alto = ALTO_MM * mm
    x0 = MARGEN_X * mm
    x1 = ancho - MARGEN_X * mm

    y = alto - MARGEN_Y * mm - 1 * mm

    # ── Encabezado: logo binario centrado ──
    y = _dibujar_logo(c, ancho / 2, y)

    # ── Título + regla ──
    y -= GAP_LOGO_TITULO
    _centrado(c, TITULO, y, FUENTE_BOLD, F_TITULO, NEGRO)
    y -= GAP_TITULO_REGLA
    _linea(c, x0, y, x1, GROSOR_REGLA, NEGRO)

    y -= GAP_REGLA_ROTULO
    y = _campo(c, "FECHA:", d["fecha"], y)
    y = _campo(c, "NOMBRE ALUMNO:", d["nombre"], y, max_lineas=2)
    y = _campo(c, "CURSO:", d["curso"], y)
    y = _campo(c, "HORA:", d["hora"], y)
    y = _campo(c, "MOTIVO:", d["motivo"], y, max_lineas=2)

    # ── Timbre y firma: se deja en blanco para completar a mano ──
    c.setFont(FUENTE_BOLD, F_ROTULO)
    c.setFillColor(NEGRO)
    c.drawString(X_ETIQUETAS, y, "TIMBRE Y FIRMA:")
    _linea(c, x0, y - SALTO_ROTULO, x1, GROSOR_FIRMA, NEGRO, punteada=True)

    # ── Marca de corte para la impresora POS ──
    _linea(c, x0, GAP_CORTE, x1, GROSOR_CORTE, NEGRO, punteada=True)

    c.showPage()
    c.save()
    buf.seek(0)
    return buf
