"""
Generador de tickets ESC/POS para impresoras térmicas de 58 mm.

A diferencia del PDF o del HTML, este generador no pasa por el driver de
impresión de Windows ni por el diálogo del navegador: arma el flujo de bytes
que entiende el cabezal (texto, negritas, logo raster y avance final) y el
agente local lo manda con el tipo de datos RAW. Así no hay escala, márgenes
del sistema ni alimentación de papel de una página completa.

Ancho de referencia: POS-58 (bobina de 58 mm, ~48 mm imprimibles).
Fuente A: 32 columnas. Codificación CP850, que incluye tildes y ñ.

El logo se lee de static/img/logo_pase_escpos.bin, generado con
core/generar_logo_escpos.py (no requiere Pillow en producción).

Los datos del ticket salen de pase_generator.datos_pase/datos_comunicado,
igual que el PDF y el HTML, para que los tres formatos muestren lo mismo.
"""
import os
import textwrap

from django.conf import settings

from .pase_generator import datos_comunicado, datos_pase

ANCHO_COLUMNAS = 32
ANCHO_DOTS = 384              # 48 mm imprimibles a 203 dpi (POS-58)
LOGO_RELATIVO = os.path.join("static", "img", "logo_pase_escpos.bin")

ESC = b"\x1b"
GS = b"\x1d"


def _abs(dots):
    """Comando ESC $ (posición horizontal absoluta en puntos)."""
    return ESC + b"$" + bytes([dots & 0xFF, (dots >> 8) & 0xFF])


# Cada línea se ancla al borde izquierdo con ESC $ 0 (posición horizontal
# absoluta). Así el ticket no depende de ESC a / GS L / GS W ni del área de
# impresión que el firmware tenga configurada (algunas POS conservan 80 mm y
# corren todo el texto a la derecha).
POS_IZQUIERDA = _abs(0)

# Margen izquierdo 0, ancho de área de impresión de 384 puntos, Fuente A
# (32 columnas = 384 puntos) y espaciado 0. Se envían igualmente porque
# algunos modelos los respetan y evitan un área de 80 mm por defecto.
FIJAR_MARGEN = GS + b"L\x00\x00"
FIJAR_ANCHO = GS + b"W" + bytes([ANCHO_DOTS & 0xFF, ANCHO_DOTS >> 8])
FUENTE_A = ESC + b"M\x00"
ESPACIADO_0 = ESC + b" \x00"

INICIALIZAR = (
    ESC + b"@"                               # reset
    + FIJAR_MARGEN                           # margen izquierdo = 0
    + FIJAR_ANCHO                            # área imprimible = 384 dots
    + FUENTE_A                               # 32 columnas = 384 dots
    + ESPACIADO_0
    + ESC + b"t\x02"                         # página de códigos CP850
    + b"\n"                                  # aplica margen/ancho antes del logo
)
NEGRITA_ON = ESC + b"E\x01"
NEGRITA_OFF = ESC + b"E\x00"
DOBLE_ALTO_ON = GS + b"!\x01"                # alto x2, ancho normal
DOBLE_ALTO_OFF = GS + b"!\x00"
AVANZAR = ESC + b"d\x04"                     # 4 líneas de margen de corte
CORTE = GS + b"V\x00"                        # corte en la posición actual (si hay cuchilla)

SEPARADOR = "-" * ANCHO_COLUMNAS
LINEA_FIRMA = "." * ANCHO_COLUMNAS


def _texto(valor):
    """Codifica en CP850: tildes y ñ correctos en impresoras POS."""
    return (valor or "").encode("cp850", "replace")


def _centrar(valor):
    """Centra dentro de las 32 columnas con espacios.

    Se usa relleno manual en vez de ESC a 1 para que el centrado no dependa
    del ancho de área que tenga configurado el firmware.
    """
    return (valor or "").center(ANCHO_COLUMNAS)


def _linea(valor=""):
    """Línea anclada al borde izquierdo del cabezal (ESC $ 0)."""
    return POS_IZQUIERDA + _texto(valor) + b"\n"


def _logo():
    """Devuelve el comando raster del logo ya empaquetado, o b''."""
    ruta = os.path.join(settings.BASE_DIR, LOGO_RELATIVO)
    try:
        with open(ruta, "rb") as fh:
            return fh.read()
    except OSError:
        return b""


def _ancho_logo(comando):
    """Ancho en puntos del raster según su cabecera GS v 0.

    Cabecera: 1d 76 30 00 xL xH yL yH; xL/xH son los bytes por fila.
    """
    if len(comando) < 8 or comando[:4] != b"\x1dv0\x00":
        return 0
    return (comando[4] | (comando[5] << 8)) * 8


def _posicion_logo(comando):
    """Posición horizontal para centrar el logo dentro de los 384 puntos."""
    ancho = _ancho_logo(comando)
    if not ancho:
        return POS_IZQUIERDA
    return _abs(max(0, (ANCHO_DOTS - ancho) // 2))


def _envolver(valor, max_lineas=None):
    """Parte el texto en líneas de ANCHO_COLUMNAS columnas.

    Si se pasa max_lineas y sobran líneas, la última se corta con "...".
    """
    lineas = textwrap.wrap(
        (valor or "").strip(),
        width=ANCHO_COLUMNAS,
        break_long_words=True,
        break_on_hyphens=False,
    )
    if not lineas:
        return []
    if max_lineas and len(lineas) > max_lineas:
        lineas = lineas[:max_lineas]
        ultima = lineas[-1]
        while ultima and len(ultima) + 3 > ANCHO_COLUMNAS:
            ultima = ultima[:-1].rstrip()
        lineas[-1] = (ultima + "...") if ultima else "..."
    return lineas


def _ficha(titulo, campos, centrado=False):
    """Arma el flujo ESC/POS completo de una ficha de 58 mm."""
    salida = bytearray(INICIALIZAR)

    logo = _logo()
    if logo:
        salida += _posicion_logo(logo) + logo + b"\n"

    # Título centrado con espacios, en negrita y doble alto (el ancho se
    # mantiene en 32 columnas para que no se corte en la bobina).
    salida += NEGRITA_ON + DOBLE_ALTO_ON
    for linea in _envolver(titulo):
        salida += _linea(_centrar(linea))
    salida += DOBLE_ALTO_OFF + NEGRITA_OFF
    salida += _linea() + _linea(SEPARADOR)

    for campo in campos:
        valor = (campo.get("valor") or "").strip()
        if not valor:
            continue
        rotulo = campo["rotulo"]
        salida += NEGRITA_ON + _linea(_centrar(rotulo) if centrado else rotulo)
        salida += NEGRITA_OFF
        for linea in _envolver(valor, campo.get("max_lineas")):
            salida += NEGRITA_ON
            salida += _linea(_centrar(linea) if centrado else linea)
            salida += NEGRITA_OFF
        salida += _linea()

    salida += _linea()
    firma = _centrar("TIMBRE Y FIRMA:") if centrado else "TIMBRE Y FIRMA:"
    salida += NEGRITA_ON + _linea(firma) + NEGRITA_OFF
    salida += _linea(_centrar(LINEA_FIRMA) if centrado else LINEA_FIRMA)
    salida += _linea() + _linea()

    # Sin marcas de corte del navegador: guía impresa + avance + corte.
    salida += _linea(SEPARADOR)
    salida += AVANZAR
    salida += CORTE
    return bytes(salida)


def generar_escpos_pase(atraso):
    """Ticket ESC/POS del pase de ingreso (Atraso)."""
    datos = datos_pase(atraso.alumno, atraso)
    return _ficha(datos["titulo"], datos["campos"])


def generar_escpos_comunicado(uniforme):
    """Ticket ESC/POS del comunicado de falta de uniforme."""
    datos = datos_comunicado(uniforme)
    return _ficha(datos["titulo"], datos["campos"], centrado=datos["centrado"])
