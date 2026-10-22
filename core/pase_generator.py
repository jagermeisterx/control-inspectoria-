"""
Generador de fichas de 80 mm para impresora POS (bobina térmica) — Inspectoría General

Documentos que produce:
  · Pase de autorización de ingreso a clases  → core.models.Atraso
  · Comunicación de falta de uniforme          → core.models.ControlUniforme

El pase reproduce el documento físico de la carpeta actualizacion-datps/pase-ejemplo.jpeg
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

El alto de la bobina es variable: la ficha crece cuando un valor ocupa varias
líneas (por ejemplo la observación de un atraso o el detalle de una falta de
uniforme), de modo que el texto nunca queda cortado ni encima de la marca de
corte. El PDF y la versión HTML comparten el mismo cálculo.
"""
import io
import math
import os

from django.conf import settings

from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
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

TITULO_PASE = "AUTORIZACION INGRESO A CLASES"
TITULO_COMUNICADO = "COMUNICACION FALTA DE UNIFORME"

# ── Tipografía ──
FUENTE = "Helvetica"
FUENTE_BOLD = "Helvetica-Bold"
F_TITULO = 9  # 11 pt mide 69,4 mm y 10 pt 63,1 mm; con 58 mm útiles solo entra 9 pt (56,8 mm)
F_TITULO_MINIMO = 6  # el título se achica hasta este punto antes que no entrar
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

# Holgura extra bajo la línea de firma, para que la marca de corte quede
# separada del texto y no haya que ampliar la bobina a mano.
HOLGURA_PIE_MM = 4

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


def _ancho(texto, fuente, size):
    """Ancho del texto en puntos. No necesita un canvas, así que el alto de la
    bobina se puede calcular antes de crear la página."""
    return pdfmetrics.stringWidth(texto or "", fuente, size)


def _tamaño_titulo(texto):
    """Tamaño de fuente con el que el título entra en el ancho útil."""
    size = F_TITULO
    while size > F_TITULO_MINIMO and _ancho(texto, FUENTE_BOLD, size) > ANCHO_UTIL:
        size -= 0.5
    return size


def _centrado(c, texto, y, fuente=FUENTE_BOLD, size=None, color=NEGRO):
    if size is None:
        size = _tamaño_titulo(texto)
    c.setFont(fuente, size)
    c.setFillColor(color)
    c.drawCentredString(ANCHO_MM * mm / 2, y, texto)


def _cortar(texto, ancho_max, fuente, size):
    """Recorta con puntos suspensivos si la línea excede el ancho disponible."""
    if _ancho(texto, fuente, size) <= ancho_max:
        return texto
    while texto and _ancho(texto + "…", fuente, size) > ancho_max:
        texto = texto[:-1].rstrip()
    return texto + "…" if texto else ""


def _envolver(texto, ancho_max, max_lineas, fuente, size):
    """Parte el texto en líneas que entran en ancho_max, hasta max_lineas.

    Si sobran palabras, la última línea se corta con "…".
    """
    palabras = (texto or "").split()
    if not palabras:
        return []
    lineas, actual = [], ""
    for p in palabras:
        candidata = f"{actual} {p}".strip()
        if not actual or _ancho(candidata, fuente, size) <= ancho_max:
            actual = candidata
        else:
            lineas.append(actual)
            actual = p
    if actual:
        lineas.append(actual)

    if len(lineas) > max_lineas:
        lineas = lineas[:max_lineas]
        corte = lineas[-1]
        while corte and _ancho(corte + "…", fuente, size) > ancho_max:
            corte = corte[:-1].rstrip()
        lineas[-1] = corte + "…" if corte else "…"
        return lineas

    return [_cortar(l, ancho_max, fuente, size) for l in lineas]


def _campo(c, rotulo, lineas, y):
    """Rótulo en negrita + valor en negrita debajo, sin línea punteada.

    lineas: líneas del valor ya ajustadas al ancho útil.
    Devuelve la Y para el siguiente rótulo.
    """
    c.setFont(FUENTE_BOLD, F_ROTULO)
    c.setFillColor(NEGRO)
    c.drawString(X_ETIQUETAS, y, rotulo)

    if not lineas:
        return y - ALTO_CAMPO

    c.setFont(FUENTE_BOLD, F_VALOR)
    c.setFillColor(NEGRO)
    y_val = y - SALTO_ROTULO
    for linea in lineas:
        c.drawString(X_ETIQUETAS, y_val, linea)
        y_val -= INTERLINEADO

    extra = INTERLINEADO * max(0, len(lineas) - 1)
    return y - ALTO_CAMPO - extra


def _preparar_campos(campos):
    """Normaliza los campos: descarta los vacíos y ajusta los valores.

    campos: lista de dicts {"rotulo", "valor", "max_lineas"}
    """
    ajustados = []
    for campo in campos:
        valor = (campo.get("valor") or "").strip()
        if not valor:
            continue
        max_lineas = campo.get("max_lineas", 1)
        ajustados.append({
            "rotulo": campo["rotulo"],
            "valor": valor,
            "max_lineas": max_lineas,
            "lineas": _envolver(valor, ANCHO_UTIL, max_lineas, FUENTE_BOLD, F_VALOR),
        })
    return ajustados


def _alto_requerido(campos):
    """Alto (en mm) que necesita la ficha con esos campos."""
    alto = MARGEN_Y + 1 + LOGO_ALTO_MM
    alto += (GAP_LOGO_TITULO + GAP_TITULO_REGLA + GAP_REGLA_ROTULO) / mm
    for campo in campos:
        alto += (ALTO_CAMPO + INTERLINEADO * max(0, len(campo["lineas"]) - 1)) / mm
    alto += (SALTO_ROTULO + GAP_CORTE) / mm
    return alto


def _alto_ficha(campos):
    """Alto final de la bobina (mm): el que pide el contenido más la holgura
    del pie, y nunca menor que la bobina estándar."""
    return max(ALTO_MM, math.ceil((_alto_requerido(campos) + HOLGURA_PIE_MM) * 2) / 2)


def _datos_comunes(titulo, campos):
    """Datos compartidos por el PDF y el HTML de cualquier ficha."""
    return {
        "titulo": titulo,
        "titulo_size": f"{_tamaño_titulo(titulo):g}",
        "campos": campos,
        "alto_mm": f"{_alto_ficha(_preparar_campos(campos)):g}",
    }


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

    observacion = ((atraso.observacion if atraso else "") or "").strip()

    campos = [
        {"rotulo": "FECHA:", "valor": fecha, "max_lineas": 1},
        {"rotulo": "NOMBRE ALUMNO:", "valor": alumno.nombre_completo.upper(), "max_lineas": 2},
        {"rotulo": "CURSO:", "valor": curso.upper(), "max_lineas": 1},
        {"rotulo": "HORA:", "valor": hora, "max_lineas": 1},
        {"rotulo": "MOTIVO:", "valor": motivo.upper(), "max_lineas": 2},
    ]
    # La observación solo aparece si el inspector la escribió.
    if observacion:
        campos.append({"rotulo": "OBSERVACION:", "valor": observacion.upper(), "max_lineas": 5})

    datos = _datos_comunes(TITULO_PASE, campos)
    datos.update({
        "fecha": fecha,
        "hora": hora,
        "curso": curso.upper(),
        "motivo": motivo.upper(),
        "nombre": alumno.nombre_completo.upper(),
        "observacion": observacion.upper(),
    })
    return datos


def datos_comunicado(uniforme):
    """Campos del comunicado de falta de uniforme (en mayúsculas).

    uniforme : instancia de core.models.ControlUniforme
    """
    alumno = uniforme.alumno
    curso = (alumno.curso or "").strip()
    if alumno.es_campo:
        curso = f"{curso} (CAMPO)".strip()

    detalle = (uniforme.detalle or "").strip()
    telefono = (uniforme.contacto_apoderado or "").strip()
    determinacion = (uniforme.determinacion or "").strip()
    falta = (uniforme.get_falta_display() or "").strip()

    campos = [
        {"rotulo": "FECHA:", "valor": uniforme.fecha.strftime("%d/%m/%Y"), "max_lineas": 1},
        {"rotulo": "NOMBRE ALUMNO:", "valor": alumno.nombre_completo.upper(), "max_lineas": 2},
        {"rotulo": "CURSO:", "valor": curso.upper(), "max_lineas": 1},
        {"rotulo": "FALTA:", "valor": falta.upper(), "max_lineas": 2},
        {"rotulo": "UNIFORME COMPRADO:", "valor": "SI" if uniforme.tiene_uniforme_comprado else "NO",
         "max_lineas": 1},
        {"rotulo": "SE LLAMO AL APODERADO:", "valor": "SI" if uniforme.llamado else "NO",
         "max_lineas": 1},
    ]
    if detalle:
        campos.append({"rotulo": "OBSERVACION:", "valor": detalle.upper(), "max_lineas": 4})
    if telefono:
        campos.append({"rotulo": "TELEFONO APODERADO:", "valor": telefono, "max_lineas": 1})
    if determinacion:
        campos.append({"rotulo": "DETERMINACION:", "valor": determinacion.upper(), "max_lineas": 2})

    datos = _datos_comunes(TITULO_COMUNICADO, campos)
    datos.update({
        "fecha": uniforme.fecha.strftime("%d/%m/%Y"),
        "nombre": alumno.nombre_completo.upper(),
        "curso": curso.upper(),
        "falta": falta.upper(),
        "observacion": detalle.upper(),
        "telefono": telefono,
    })
    return datos


def generar_pdf_ficha(titulo, campos, nombre="ficha"):
    """Dibuja una ficha de 80 mm con los campos indicados y devuelve un BytesIO.

    titulo : texto centrado bajo el logo
    campos : lista de dicts {"rotulo", "valor", "max_lineas"}
    """
    ajustados = _preparar_campos(campos)
    alto_mm = _alto_ficha(ajustados)

    buf = io.BytesIO()
    c = pdfcanvas.Canvas(buf, pagesize=(ANCHO_MM * mm, alto_mm * mm))
    c.setTitle(nombre)

    ancho = ANCHO_MM * mm
    alto = alto_mm * mm
    x0 = MARGEN_X * mm
    x1 = ancho - MARGEN_X * mm

    y = alto - MARGEN_Y * mm - 1 * mm

    # ── Encabezado: logo binario centrado ──
    y = _dibujar_logo(c, ancho / 2, y)

    # ── Título + regla ──
    y -= GAP_LOGO_TITULO
    _centrado(c, titulo, y, FUENTE_BOLD, _tamaño_titulo(titulo), NEGRO)
    y -= GAP_TITULO_REGLA
    _linea(c, x0, y, x1, GROSOR_REGLA, NEGRO)

    y -= GAP_REGLA_ROTULO
    for campo in ajustados:
        y = _campo(c, campo["rotulo"], campo["lineas"], y)

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


def generar_pdf_pase(alumno, atraso=None):
    """Genera el pase de autorización en PDF de 80 mm y devuelve un BytesIO.

    alumno : instancia de core.models.Alumno
    atraso : instancia de core.models.Atraso (opcional; si falta, los campos
             de fecha y hora quedan en blanco)
    """
    d = datos_pase(alumno, atraso)
    return generar_pdf_ficha(d["titulo"], d["campos"], nombre=f"Pase {alumno.nombre_completo}")


def generar_pdf_comunicado(uniforme):
    """Genera el comunicado de falta de uniforme en PDF de 80 mm (BytesIO)."""
    d = datos_comunicado(uniforme)
    nombre = f"Comunicado uniforme {uniforme.alumno.nombre_completo}"
    return generar_pdf_ficha(d["titulo"], d["campos"], nombre=nombre)
