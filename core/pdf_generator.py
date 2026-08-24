"""
Generador de PDFs profesionales para Inspectoría General
Escuela Alemana Paillaco — Colores institucionales (rojo, negro, dorado)
"""
import io
import os
from datetime import date
from collections import Counter

from django.conf import settings
from django.db.models import Count

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import mm, cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer,
    Image, HRFlowable, PageBreak, KeepTogether,
)
from reportlab.platypus.doctemplate import PageTemplate, BaseDocTemplate, Frame
from reportlab.lib.utils import ImageReader

from .models import Alumno, Retiro, Atraso, ControlUniforme, Celular

# ── Colores institucionales ──
ROJO = colors.HexColor("#C8102E")
ROJO_OSCURO = colors.HexColor("#9B0000")
DORADO = colors.HexColor("#C5A000")
NEGRO = colors.HexColor("#1A1A1A")
GRIS = colors.HexColor("#666666")
GRIS_CLARO = colors.HexColor("#F5F5F5")
BLANCO = colors.white

MESES = {
    1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
    5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
    9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre",
}


def _get_logo_path():
    return os.path.join(settings.BASE_DIR, "static", "img", "logo.jpg")


def _build_styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        "TituloEscuela", parent=styles["Title"],
        fontName="Helvetica-Bold", fontSize=18, textColor=ROJO,
        alignment=TA_CENTER, spaceAfter=2*mm,
    ))
    styles.add(ParagraphStyle(
        "Subtitulo", parent=styles["Normal"],
        fontName="Helvetica-Bold", fontSize=12, textColor=NEGRO,
        alignment=TA_CENTER, spaceAfter=4*mm,
    ))
    styles.add(ParagraphStyle(
        "SubtituloCurso", parent=styles["Normal"],
        fontName="Helvetica-Bold", fontSize=14, textColor=ROJO,
        alignment=TA_CENTER, spaceAfter=2*mm,
    ))
    styles.add(ParagraphStyle(
        "Interno", parent=styles["Normal"],
        fontName="Helvetica-Oblique", fontSize=9, textColor=GRIS,
        alignment=TA_CENTER, spaceAfter=6*mm,
    ))
    styles.add(ParagraphStyle(
        "SeccionTitulo", parent=styles["Heading2"],
        fontName="Helvetica-Bold", fontSize=12, textColor=BLANCO,
        backColor=ROJO, leftIndent=4*mm, spaceBefore=6*mm, spaceAfter=3*mm,
        borderPadding=(2*mm, 4*mm, 2*mm, 4*mm),
    ))
    styles.add(ParagraphStyle(
        "ResumenTitulo", parent=styles["Heading2"],
        fontName="Helvetica-Bold", fontSize=13, textColor=ROJO,
        spaceBefore=4*mm, spaceAfter=3*mm,
        borderWidth=0, borderColor=DORADO,
    ))
    styles.add(ParagraphStyle(
        "SubSeccion", parent=styles["Normal"],
        fontName="Helvetica-Bold", fontSize=10, textColor=ROJO,
        spaceBefore=4*mm, spaceAfter=2*mm,
    ))
    styles.add(ParagraphStyle(
        "Normal9", parent=styles["Normal"],
        fontName="Helvetica", fontSize=9, textColor=NEGRO,
    ))
    styles.add(ParagraphStyle(
        "Normal9Gray", parent=styles["Normal"],
        fontName="Helvetica", fontSize=9, textColor=GRIS,
    ))
    styles.add(ParagraphStyle(
        "AlertaInfo", parent=styles["Normal"],
        fontName="Helvetica", fontSize=9, textColor=colors.HexColor("#0056b3"),
        leftIndent=6*mm, spaceBefore=2*mm,
    ))
    styles.add(ParagraphStyle(
        "AlertaWarning", parent=styles["Normal"],
        fontName="Helvetica-Bold", fontSize=9, textColor=colors.HexColor("#cc6600"),
        leftIndent=6*mm, spaceBefore=2*mm,
    ))
    return styles


def _header_footer(canvas, doc, curso_label, mes_label):
    """Dibuja encabezado y pie en cada página"""
    canvas.saveState()
    w, h = letter
    logo_path = _get_logo_path()

    # ── Encabezado ──
    # Texto izquierda
    canvas.setFont("Helvetica-Bold", 9)
    canvas.setFillColor(ROJO)
    canvas.drawString(20*mm, h - 12*mm, "ESCUELA ALEMANA PAILLACO")
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(GRIS)
    canvas.drawString(20*mm, h - 16*mm, f"Inspectoría General · {curso_label} · {mes_label}")

    # Logo derecha
    if os.path.exists(logo_path):
        canvas.drawImage(logo_path, w - 30*mm, h - 22*mm, width=18*mm, height=18*mm, preserveAspectRatio=True, mask='auto')

    # ── Pie de página ──
    # Línea dorada
    canvas.setStrokeColor(DORADO)
    canvas.setLineWidth(1)
    canvas.line(20*mm, 14*mm, w - 20*mm, 14*mm)

    # Texto pie
    canvas.setFont("Helvetica-Oblique", 7)
    canvas.setFillColor(ROJO)
    pie = f"Informe {curso_label}  ·  Inspectoría General  ·  {mes_label}"
    canvas.drawString(20*mm, 9*mm, pie)
    canvas.setFont("Helvetica-Bold", 8)
    canvas.drawRightString(w - 20*mm, 9*mm, f"Pág. {doc.page}")

    canvas.restoreState()


def _portada(elements, styles, curso_label, mes_label, simple=False):
    """Genera la portada del informe.

    Si simple=True, omite las líneas secundarias (informe específico, label de
    curso, leyenda de uso interno). Útil para reportes puntuales que no
    requieren la portada institucional completa.
    """
    elements.append(Spacer(1, 30*mm))

    # Logo centrado grande
    logo_path = _get_logo_path()
    if os.path.exists(logo_path):
        elements.append(Image(logo_path, width=45*mm, height=45*mm))
        elements.append(Spacer(1, 10*mm))

    elements.append(Paragraph("ESCUELA ALEMANA PAILLACO", styles["TituloEscuela"]))
    elements.append(Spacer(1, 8*mm))

    # Línea dorada
    elements.append(HRFlowable(width="60%", thickness=1, color=DORADO, spaceBefore=2*mm, spaceAfter=4*mm, hAlign="CENTER"))

    elements.append(Paragraph("INSPECTORÍA GENERAL", styles["Subtitulo"]))

    if not simple:
        elements.append(Paragraph(f"Informe de Convivencia Escolar — {mes_label}", styles["Normal9Gray"]))
        elements.append(Spacer(1, 2*mm))
        elements.append(Paragraph(curso_label, styles["SubtituloCurso"]))
        elements.append(Spacer(1, 15*mm))
        elements.append(Paragraph("Documento de uso interno — Jefatura de Curso", styles["Interno"]))
    else:
        elements.append(Spacer(1, 6*mm))

    elements.append(PageBreak())


def _stat_table(data_pairs):
    """Crea cuadro resumen tipo tarjetas con estadísticas"""
    values = []
    labels = []
    n = len(data_pairs)
    for i, (val, label) in enumerate(data_pairs):
        is_last = (i == n - 1)
        txt_color = BLANCO if is_last else ROJO
        lbl_color = colors.HexColor("#FFCCCC") if is_last else GRIS
        values.append(Paragraph(f'<b>{val}</b>', ParagraphStyle(f"v{i}", fontSize=22, alignment=TA_CENTER, textColor=txt_color)))
        labels.append(Paragraph(f'{label}', ParagraphStyle(f"l{i}", fontSize=8, alignment=TA_CENTER, textColor=lbl_color)))

    col_w = 150 / n * mm
    t = Table([values, labels], colWidths=[col_w] * n)
    t.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOX", (0, 0), (-1, -1), 0.5, ROJO),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E0E0E0")),
        ("TOPPADDING", (0, 0), (-1, 0), 4*mm),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 2*mm),
        ("TOPPADDING", (0, 1), (-1, 1), 1*mm),
        ("BOTTOMPADDING", (0, 1), (-1, 1), 3*mm),
        ("BACKGROUND", (-1, 0), (-1, -1), ROJO),
    ]))
    return t


def _data_table(headers, rows, col_widths=None):
    """Crea tabla de datos con estilo institucional"""
    header_paras = [Paragraph(f'<b>{h}</b>', ParagraphStyle("th", fontSize=8, textColor=BLANCO, alignment=TA_CENTER)) for h in headers]
    data = [header_paras]
    for row in rows:
        data.append([Paragraph(str(c), ParagraphStyle("td", fontSize=8, textColor=NEGRO)) for c in row])

    t = Table(data, colWidths=col_widths, repeatRows=1)
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), ROJO),
        ("TEXTCOLOR", (0, 0), (-1, 0), BLANCO),
        ("FONTSIZE", (0, 0), (-1, 0), 8),
        ("FONTSIZE", (0, 1), (-1, -1), 8),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#CCCCCC")),
        ("TOPPADDING", (0, 0), (-1, -1), 2*mm),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2*mm),
    ]
    # Alternate row colors
    for i in range(1, len(data)):
        if i % 2 == 0:
            style.append(("BACKGROUND", (0, i), (-1, i), GRIS_CLARO))
    t.setStyle(TableStyle(style))
    return t


def _freq_table(title, data_list):
    """Tabla de frecuencia por estudiante o por motivo"""
    headers = [title, "Cantidad"]
    rows = [[name, str(count)] for name, count in data_list]
    t = _data_table(headers, rows, col_widths=[100*mm, 40*mm])
    return t


# ════════════════════════════════════════════
#  PDF POR CURSO (formato informe completo)
# ════════════════════════════════════════════

def generar_pdf_curso(curso, mes=None, anio=None, fecha_desde=None, fecha_hasta=None):
    """Genera PDF profesional de informe por curso, replicando el formato institucional"""
    hoy = date.today()
    usa_rango = bool(fecha_desde or fecha_hasta)
    if not usa_rango:
        if mes is None:
            mes = hoy.month
        if anio is None:
            anio = hoy.year
        mes_label = f"{MESES[mes]} {anio}"
    else:
        mes_label = f"{fecha_desde or 'Inicio'} al {fecha_hasta or 'Hoy'}"
    curso_label = curso

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=letter,
        topMargin=25*mm, bottomMargin=20*mm,
        leftMargin=20*mm, rightMargin=20*mm,
    )

    elements = []
    styles = _build_styles()

    # ── Portada ──
    _portada(elements, styles, curso_label, mes_label)

    # ── Datos del mes ──
    alumnos_curso = Alumno.objects.filter(curso=curso, activo=True)
    if usa_rango:
        atrasos = Atraso.objects.filter(alumno__curso=curso)
        retiros = Retiro.objects.filter(alumno__curso=curso)
        uniformes = ControlUniforme.objects.filter(alumno__curso=curso)
        celulares = Celular.objects.filter(alumno__curso=curso)
        if fecha_desde:
            atrasos = atrasos.filter(fecha__gte=fecha_desde)
            retiros = retiros.filter(fecha__gte=fecha_desde)
            uniformes = uniformes.filter(fecha__gte=fecha_desde)
            celulares = celulares.filter(fecha__gte=fecha_desde)
        if fecha_hasta:
            atrasos = atrasos.filter(fecha__lte=fecha_hasta)
            retiros = retiros.filter(fecha__lte=fecha_hasta)
            uniformes = uniformes.filter(fecha__lte=fecha_hasta)
            celulares = celulares.filter(fecha__lte=fecha_hasta)
    else:
        atrasos = Atraso.objects.filter(alumno__curso=curso, fecha__month=mes, fecha__year=anio)
        retiros = Retiro.objects.filter(alumno__curso=curso, fecha__month=mes, fecha__year=anio)
        uniformes = ControlUniforme.objects.filter(alumno__curso=curso, fecha__month=mes, fecha__year=anio)
        celulares = Celular.objects.filter(alumno__curso=curso, fecha__month=mes, fecha__year=anio)

    total_atrasos = atrasos.count()
    atrasos_llegada = atrasos.filter(tipo="LLEGADA").count()
    atrasos_recreo = total_atrasos - atrasos_llegada
    total_retiros = retiros.count()
    total_uniformes = uniformes.count()

    # ── Resumen ──
    elements.append(Paragraph(f"Resumen del Curso — {mes_label}", styles["ResumenTitulo"]))
    elements.append(Spacer(1, 2*mm))

    stat = _stat_table([
        (total_atrasos, "Total Atrasos"),
        (atrasos_llegada, "Llegada tardía"),
        (atrasos_recreo, "Recreo/Pasillo"),
        (total_retiros, "Total Retiros"),
        (total_uniformes, "Faltas Uniforme"),
    ])
    elements.append(stat)
    elements.append(Spacer(1, 3*mm))

    # Alertas inteligentes
    motivos_salud = ["ENFERMO/A", "CONTROL MÉDICO", "ACC. ESCOLAR", "TERAPIA", "KINESIÓLOGO"]
    retiros_salud = retiros.filter(motivo__in=motivos_salud).count()

    if total_atrasos > 0:
        top_atraso = atrasos.values("alumno__nombre", "alumno__apellido").annotate(n=Count("id")).order_by("-n").first()
        if top_atraso and top_atraso["n"] >= 5:
            elements.append(Paragraph(
                f'⚠ {top_atraso["alumno__nombre"]} {top_atraso["alumno__apellido"]} lidera los atrasos del curso con {top_atraso["n"]} registros.',
                styles["AlertaWarning"]))

    if total_atrasos > 30:
        elements.append(Paragraph(
            "⚠ El curso supera los 30 atrasos mensuales. Se recomienda intervención con apoderados.",
            styles["AlertaWarning"]))

    if total_retiros > 40:
        elements.append(Paragraph(
            f"⚠ Alto número de retiros ({total_retiros}). Revisar causas con Orientación.",
            styles["AlertaWarning"]))

    if retiros_salud > 0:
        elements.append(Paragraph(
            f"ℹ {retiros_salud} retiros asociados a salud. Informar a UTP para seguimiento académico.",
            styles["AlertaInfo"]))

    elements.append(Spacer(1, 4*mm))

    # ── 1. Atrasos ──
    elements.append(Paragraph("1.  Registro de Atrasos y Pases", styles["SeccionTitulo"]))
    elements.append(Spacer(1, 2*mm))

    if total_atrasos == 0:
        elements.append(Paragraph(
            f"No se registraron atrasos ni pases de recreo para este curso durante el mes de {MESES[mes].lower()} de {anio}.",
            styles["Normal9"]))
    else:
        elements.append(Paragraph(
            f"Se registraron {total_atrasos} atrasos y pases durante {MESES[mes].lower()}, de los cuales "
            f"{atrasos_llegada} corresponden a llegadas tardías y {atrasos_recreo} a pases de recreo o pasillo.",
            styles["Normal9"]))
        elements.append(Spacer(1, 3*mm))

        # Detalle
        elements.append(Paragraph("Detalle de registros", styles["SubSeccion"]))
        rows = []
        for a in atrasos.select_related("alumno").order_by("fecha", "hora"):
            rows.append([
                a.fecha.strftime("%d/%m/%Y"),
                a.alumno.nombre_completo,
                a.hora.strftime("%H:%M") if a.hora else "",
                a.tipo,
                a.lugar or "",
            ])
        rows.append(["", "TOTAL", str(total_atrasos), f"{atrasos_llegada} llegadas", f"{atrasos_recreo} recreo"])
        t = _data_table(["Fecha", "Alumno/a", "Hora", "Tipo", "Razón"], rows,
                        col_widths=[22*mm, 50*mm, 18*mm, 22*mm, 40*mm])
        elements.append(t)
        elements.append(Spacer(1, 3*mm))

        # Frecuencia por estudiante
        elements.append(Paragraph("Frecuencia por estudiante", styles["SubSeccion"]))
        freq = atrasos.values("alumno__nombre", "alumno__apellido").annotate(n=Count("id")).order_by("-n")
        freq_data = [(f'{f["alumno__nombre"]} {f["alumno__apellido"]}', f["n"]) for f in freq]
        elements.append(_freq_table("Alumno/a", freq_data))

    elements.append(Spacer(1, 4*mm))

    # ── 2. Retiros ──
    elements.append(Paragraph("2.  Registro de Retiros Anticipados", styles["SeccionTitulo"]))
    elements.append(Spacer(1, 2*mm))

    if total_retiros == 0:
        elements.append(Paragraph(
            f"No se registraron retiros anticipados durante {MESES[mes].lower()}.",
            styles["Normal9"]))
    else:
        elements.append(Paragraph(
            f"Se registraron {total_retiros} retiros anticipados durante {MESES[mes].lower()}.",
            styles["Normal9"]))
        elements.append(Spacer(1, 3*mm))

        elements.append(Paragraph("Detalle de registros", styles["SubSeccion"]))
        rows = []
        for r in retiros.select_related("alumno").order_by("fecha", "hora"):
            rows.append([
                r.fecha.strftime("%d/%m/%Y"),
                r.alumno.nombre_completo,
                r.hora.strftime("%H:%M") if r.hora else "",
                r.motivo,
            ])
        rows.append(["", "TOTAL", "", f"{total_retiros}  retiros"])
        t = _data_table(["Fecha", "Alumno/a", "Hora", "Motivo"], rows,
                        col_widths=[24*mm, 55*mm, 20*mm, 50*mm])
        elements.append(t)
        elements.append(Spacer(1, 3*mm))

        # Resumen por motivo
        elements.append(Paragraph("Resumen por motivo", styles["SubSeccion"]))
        mot_freq = retiros.values("motivo").annotate(n=Count("id")).order_by("-n")
        mot_data = [(m["motivo"], m["n"]) for m in mot_freq]
        mot_data.append(("TOTAL", total_retiros))
        elements.append(_freq_table("Motivo", mot_data))
        elements.append(Spacer(1, 3*mm))

        # Frecuencia por estudiante
        elements.append(Paragraph("Frecuencia por estudiante", styles["SubSeccion"]))
        freq = retiros.values("alumno__nombre", "alumno__apellido").annotate(n=Count("id")).order_by("-n")
        freq_data = [(f'{f["alumno__nombre"]} {f["alumno__apellido"]}', f["n"]) for f in freq]
        elements.append(_freq_table("Alumno/a", freq_data))

    # ── 3. Uniformes (siempre visible) ──
    elements.append(Spacer(1, 4*mm))
    elements.append(Paragraph("3.  Control de Uniformes", styles["SeccionTitulo"]))
    elements.append(Spacer(1, 2*mm))

    if total_uniformes == 0:
        elements.append(Paragraph(
            f"No se registraron situaciones de uniforme incompleto en el curso durante {mes_label}.",
            styles["Normal9"]))
    else:
        elements.append(Paragraph(
            f"Se registraron {total_uniformes} situación(es) de uniforme incompleto en el curso durante {mes_label}.",
            styles["Normal9"]))
        elements.append(Spacer(1, 3*mm))

        # Frecuencia por estudiante
        elements.append(Paragraph("Faltas por estudiante", styles["SubSeccion"]))
        freq_u = uniformes.values("alumno__nombre", "alumno__apellido").annotate(n=Count("id")).order_by("-n")
        elements.append(_freq_table("Alumno/a", [(f'{f["alumno__nombre"]} {f["alumno__apellido"]}', f["n"]) for f in freq_u]))
        elements.append(Spacer(1, 3*mm))

        rows = []
        for u in uniformes.select_related("alumno").order_by("fecha"):
            rows.append([
                u.fecha.strftime("%d/%m/%Y"),
                u.alumno.nombre_completo,
                u.falta,
                u.determinacion or "-",
            ])
        rows.append(["", "TOTAL", f"{total_uniformes} faltas", ""])
        t = _data_table(["Fecha", "Alumno/a", "Falta", "Determinación"], rows,
                        col_widths=[24*mm, 55*mm, 35*mm, 40*mm])
        elements.append(t)

    # ── 4. Celulares (si hay) ──
    total_celulares = celulares.count()
    if total_celulares > 0:
        elements.append(Spacer(1, 4*mm))
        elements.append(Paragraph("4.  Retención de Celulares", styles["SeccionTitulo"]))
        elements.append(Spacer(1, 2*mm))
        elements.append(Paragraph(
            f"Se registraron {total_celulares} caso(s) de retención de celular durante {MESES[mes].lower()}.",
            styles["Normal9"]))
        elements.append(Spacer(1, 3*mm))

        rows = []
        for c in celulares.select_related("alumno").order_by("fecha"):
            rows.append([
                c.fecha.strftime("%d/%m/%Y"),
                c.alumno.nombre_completo,
                c.lugar_entregado,
                c.retiro,
            ])
        t = _data_table(["Fecha", "Alumno/a", "Lugar entregado", "Retiro"], rows,
                        col_widths=[24*mm, 55*mm, 35*mm, 40*mm])
        elements.append(t)

    # ── Build ──
    def on_page(canvas, doc):
        _header_footer(canvas, doc, curso_label, mes_label)

    doc.build(elements, onFirstPage=on_page, onLaterPages=on_page)
    buf.seek(0)
    return buf


# ════════════════════════════════════════════
#  PDF POR ALUMNO (con resumen + detalle)
# ════════════════════════════════════════════

def generar_pdf_alumno(alumno):
    """Genera PDF profesional del historial de un alumno"""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=letter,
        topMargin=25*mm, bottomMargin=20*mm,
        leftMargin=20*mm, rightMargin=20*mm,
    )

    elements = []
    styles = _build_styles()
    curso_label = alumno.curso or "Sin curso"
    mes_label = date.today().strftime("%B %Y").capitalize()

    # ── Encabezado ──
    elements.append(Spacer(1, 5*mm))

    logo_path = _get_logo_path()
    if os.path.exists(logo_path):
        elements.append(Image(logo_path, width=25*mm, height=25*mm))
        elements.append(Spacer(1, 4*mm))

    elements.append(Paragraph("ESCUELA ALEMANA PAILLACO", styles["TituloEscuela"]))
    elements.append(HRFlowable(width="60%", thickness=1, color=DORADO, spaceBefore=2*mm, spaceAfter=4*mm, hAlign="CENTER"))
    elements.append(Paragraph("INSPECTORÍA GENERAL", styles["Subtitulo"]))
    elements.append(Paragraph(f"Reporte Individual — {alumno.nombre_completo}", styles["SubtituloCurso"]))
    elements.append(Spacer(1, 4*mm))

    # ── Datos del alumno ──
    info_data = [
        ["Alumno/a:", alumno.nombre_completo, "Curso:", alumno.curso],
        ["RUT:", alumno.rut or "N/A", "Apoderado:", alumno.apoderado_nombre or "N/A"],
        ["Teléfono:", alumno.apoderado_telefono or "N/A", "Generado:", date.today().strftime("%d/%m/%Y")],
    ]
    info_t = Table(info_data, colWidths=[22*mm, 55*mm, 22*mm, 55*mm])
    info_t.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
        ("TEXTCOLOR", (0, 0), (0, -1), GRIS),
        ("TEXTCOLOR", (2, 0), (2, -1), GRIS),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2*mm),
    ]))
    elements.append(info_t)
    elements.append(Spacer(1, 4*mm))

    # ── Resumen (cuadro) ──
    retiros_q = Retiro.objects.filter(alumno=alumno)
    atrasos_q = Atraso.objects.filter(alumno=alumno)
    uniformes_q = ControlUniforme.objects.filter(alumno=alumno)
    celulares_q = Celular.objects.filter(alumno=alumno)

    elements.append(Paragraph("Resumen General", styles["ResumenTitulo"]))
    stat = _stat_table([
        (retiros_q.count(), "Retiros"),
        (atrasos_q.count(), "Atrasos"),
        (uniformes_q.count(), "Uniformes"),
        (celulares_q.count(), "Celulares"),
    ])
    elements.append(stat)
    elements.append(Spacer(1, 4*mm))

    # ── Retiros ──
    if retiros_q.exists():
        elements.append(Paragraph("Retiros Anticipados", styles["SeccionTitulo"]))
        elements.append(Spacer(1, 2*mm))
        rows = []
        for r in retiros_q.order_by("-fecha"):
            rows.append([
                r.fecha.strftime("%d/%m/%Y"),
                r.hora.strftime("%H:%M") if r.hora else "",
                r.motivo,
                r.persona_retira,
                (r.observacion or "")[:40],
            ])
        t = _data_table(["Fecha", "Hora", "Motivo", "Retira", "Obs."], rows,
                        col_widths=[22*mm, 16*mm, 30*mm, 40*mm, 42*mm])
        elements.append(t)

    # ── Atrasos ──
    if atrasos_q.exists():
        elements.append(Spacer(1, 3*mm))
        elements.append(Paragraph("Atrasos y Pases", styles["SeccionTitulo"]))
        elements.append(Spacer(1, 2*mm))
        rows = []
        for a in atrasos_q.order_by("-fecha"):
            rows.append([
                a.fecha.strftime("%d/%m/%Y"),
                a.hora.strftime("%H:%M") if a.hora else "",
                a.tipo,
                a.lugar or "",
            ])
        t = _data_table(["Fecha", "Hora", "Tipo", "Lugar/Razón"], rows,
                        col_widths=[25*mm, 20*mm, 25*mm, 80*mm])
        elements.append(t)

    # ── Uniformes ──
    if uniformes_q.exists():
        elements.append(Spacer(1, 3*mm))
        elements.append(Paragraph("Control de Uniformes", styles["SeccionTitulo"]))
        elements.append(Spacer(1, 2*mm))
        rows = []
        for u in uniformes_q.order_by("-fecha"):
            rows.append([
                u.fecha.strftime("%d/%m/%Y"),
                u.falta,
                "Sí" if u.tiene_uniforme_comprado else "No",
                u.determinacion or "-",
            ])
        t = _data_table(["Fecha", "Falta", "Comprado", "Determinación"], rows,
                        col_widths=[25*mm, 40*mm, 20*mm, 65*mm])
        elements.append(t)

    # ── Celulares ──
    if celulares_q.exists():
        elements.append(Spacer(1, 3*mm))
        elements.append(Paragraph("Retención de Celulares", styles["SeccionTitulo"]))
        elements.append(Spacer(1, 2*mm))
        rows = []
        for c in celulares_q.order_by("-fecha"):
            rows.append([
                c.fecha.strftime("%d/%m/%Y"),
                c.lugar_entregado,
                c.retiro,
                "Sí" if c.aviso_apoderado else "No",
            ])
        t = _data_table(["Fecha", "Lugar", "Retiro", "Aviso"], rows,
                        col_widths=[25*mm, 45*mm, 40*mm, 40*mm])
        elements.append(t)

    # Sin registros
    if not any([retiros_q.exists(), atrasos_q.exists(), uniformes_q.exists(), celulares_q.exists()]):
        elements.append(Spacer(1, 10*mm))
        elements.append(Paragraph("No se encontraron registros para este alumno.", styles["Normal9Gray"]))

    # ── Build ──
    def on_page(canvas, doc):
        _header_footer(canvas, doc, curso_label, f"Reporte Individual")

    doc.build(elements, onFirstPage=on_page, onLaterPages=on_page)
    buf.seek(0)
    return buf


# ════════════════════════════════════════════
#  PDF TODOS LOS CURSOS (un informe por curso, concatenados)
# ════════════════════════════════════════════

def generar_pdf_todos_cursos(mes=None, anio=None, fecha_desde=None, fecha_hasta=None):
    """Genera un PDF con informes de todos los cursos concatenados"""
    hoy = date.today()
    usa_rango = bool(fecha_desde or fecha_hasta)
    if not usa_rango:
        if mes is None:
            mes = hoy.month
        if anio is None:
            anio = hoy.year
        mes_label = f"{MESES[mes]} {anio}"
    else:
        mes_label = f"{fecha_desde or 'Inicio'} al {fecha_hasta or 'Hoy'}"

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=letter,
        topMargin=25*mm, bottomMargin=20*mm,
        leftMargin=20*mm, rightMargin=20*mm,
    )

    elements = []
    styles = _build_styles()

    cursos = Alumno.objects.filter(activo=True).exclude(curso="").values_list("curso", flat=True).distinct().order_by("curso")

    for i, curso in enumerate(cursos):
        # Portada por curso
        _portada(elements, styles, curso, mes_label)

        # Datos
        if usa_rango:
            atrasos = Atraso.objects.filter(alumno__curso=curso)
            retiros = Retiro.objects.filter(alumno__curso=curso)
            uniformes = ControlUniforme.objects.filter(alumno__curso=curso)
            celulares = Celular.objects.filter(alumno__curso=curso)
            if fecha_desde:
                atrasos = atrasos.filter(fecha__gte=fecha_desde)
                retiros = retiros.filter(fecha__gte=fecha_desde)
                uniformes = uniformes.filter(fecha__gte=fecha_desde)
                celulares = celulares.filter(fecha__gte=fecha_desde)
            if fecha_hasta:
                atrasos = atrasos.filter(fecha__lte=fecha_hasta)
                retiros = retiros.filter(fecha__lte=fecha_hasta)
                uniformes = uniformes.filter(fecha__lte=fecha_hasta)
                celulares = celulares.filter(fecha__lte=fecha_hasta)
        else:
            atrasos = Atraso.objects.filter(alumno__curso=curso, fecha__month=mes, fecha__year=anio)
            retiros = Retiro.objects.filter(alumno__curso=curso, fecha__month=mes, fecha__year=anio)
            uniformes = ControlUniforme.objects.filter(alumno__curso=curso, fecha__month=mes, fecha__year=anio)
            celulares = Celular.objects.filter(alumno__curso=curso, fecha__month=mes, fecha__year=anio)

        total_atrasos = atrasos.count()
        atrasos_llegada = atrasos.filter(tipo="LLEGADA").count()
        atrasos_recreo = total_atrasos - atrasos_llegada
        total_retiros = retiros.count()
        total_uniformes_curso = uniformes.count()

        # Resumen
        elements.append(Paragraph(f"Resumen del Curso — {mes_label}", styles["ResumenTitulo"]))
        stat = _stat_table([
            (total_atrasos, "Total Atrasos"),
            (atrasos_llegada, "Llegada tardía"),
            (atrasos_recreo, "Recreo/Pasillo"),
            (total_retiros, "Total Retiros"),
            (total_uniformes_curso, "Faltas Uniforme"),
        ])
        elements.append(stat)
        elements.append(Spacer(1, 3*mm))

        # Alertas
        motivos_salud = ["ENFERMO/A", "CONTROL MÉDICO", "ACC. ESCOLAR", "TERAPIA", "KINESIÓLOGO"]
        retiros_salud = retiros.filter(motivo__in=motivos_salud).count()
        if total_atrasos > 30:
            elements.append(Paragraph("⚠ El curso supera los 30 atrasos mensuales.", styles["AlertaWarning"]))
        if retiros_salud > 0:
            elements.append(Paragraph(f"ℹ {retiros_salud} retiros asociados a salud.", styles["AlertaInfo"]))

        # Atrasos
        elements.append(Paragraph("1.  Registro de Atrasos y Pases", styles["SeccionTitulo"]))
        if total_atrasos == 0:
            elements.append(Paragraph("No se registraron atrasos.", styles["Normal9"]))
        else:
            elements.append(Paragraph(f"Se registraron {total_atrasos} atrasos.", styles["Normal9"]))
            rows = [[a.fecha.strftime("%d/%m/%Y"), a.alumno.nombre_completo, a.hora.strftime("%H:%M") if a.hora else "", a.tipo, a.lugar or ""]
                    for a in atrasos.select_related("alumno").order_by("fecha", "hora")]
            elements.append(_data_table(["Fecha", "Alumno/a", "Hora", "Tipo", "Razón"], rows,
                                        col_widths=[22*mm, 50*mm, 18*mm, 22*mm, 40*mm]))
            # Frecuencia
            elements.append(Paragraph("Frecuencia por estudiante", styles["SubSeccion"]))
            freq = atrasos.values("alumno__nombre", "alumno__apellido").annotate(n=Count("id")).order_by("-n")
            elements.append(_freq_table("Alumno/a", [(f'{f["alumno__nombre"]} {f["alumno__apellido"]}', f["n"]) for f in freq]))

        # Retiros
        elements.append(Paragraph("2.  Registro de Retiros Anticipados", styles["SeccionTitulo"]))
        if total_retiros == 0:
            elements.append(Paragraph("No se registraron retiros.", styles["Normal9"]))
        else:
            elements.append(Paragraph(f"Se registraron {total_retiros} retiros.", styles["Normal9"]))
            rows = [[r.fecha.strftime("%d/%m/%Y"), r.alumno.nombre_completo, r.hora.strftime("%H:%M") if r.hora else "", r.motivo]
                    for r in retiros.select_related("alumno").order_by("fecha", "hora")]
            elements.append(_data_table(["Fecha", "Alumno/a", "Hora", "Motivo"], rows,
                                        col_widths=[24*mm, 55*mm, 20*mm, 50*mm]))
            elements.append(Paragraph("Resumen por motivo", styles["SubSeccion"]))
            mot = retiros.values("motivo").annotate(n=Count("id")).order_by("-n")
            elements.append(_freq_table("Motivo", [(m["motivo"], m["n"]) for m in mot]))
            elements.append(Paragraph("Frecuencia por estudiante", styles["SubSeccion"]))
            freq = retiros.values("alumno__nombre", "alumno__apellido").annotate(n=Count("id")).order_by("-n")
            elements.append(_freq_table("Alumno/a", [(f'{f["alumno__nombre"]} {f["alumno__apellido"]}', f["n"]) for f in freq]))

        # Uniformes (siempre visible)
        elements.append(Spacer(1, 4*mm))
        elements.append(Paragraph("3.  Control de Uniformes", styles["SeccionTitulo"]))
        if total_uniformes_curso == 0:
            elements.append(Paragraph("No se registraron situaciones de uniforme incompleto en el curso.", styles["Normal9"]))
        else:
            elements.append(Paragraph(f"Se registraron {total_uniformes_curso} situación(es) de uniforme incompleto.", styles["Normal9"]))
            elements.append(Spacer(1, 2*mm))
            freq_u = uniformes.values("alumno__nombre", "alumno__apellido").annotate(n=Count("id")).order_by("-n")
            elements.append(_freq_table("Alumno/a", [(f'{f["alumno__nombre"]} {f["alumno__apellido"]}', f["n"]) for f in freq_u]))
            elements.append(Spacer(1, 2*mm))
            rows = [[u.fecha.strftime("%d/%m/%Y"), u.alumno.nombre_completo, u.falta, u.determinacion or "-"]
                    for u in uniformes.select_related("alumno").order_by("fecha")]
            rows.append(["", "TOTAL", f"{total_uniformes_curso} faltas", ""])
            elements.append(_data_table(["Fecha", "Alumno/a", "Falta", "Determinación"], rows,
                                        col_widths=[24*mm, 55*mm, 35*mm, 40*mm]))

        # Celulares
        if celulares.exists():
            elements.append(Paragraph("4.  Retención de Celulares", styles["SeccionTitulo"]))
            elements.append(Paragraph(f"Se registraron {celulares.count()} caso(s) de retención.", styles["Normal9"]))
            rows = [[c.fecha.strftime("%d/%m/%Y"), c.alumno.nombre_completo, c.lugar_entregado, c.retiro]
                    for c in celulares.select_related("alumno").order_by("fecha")]
            elements.append(_data_table(["Fecha", "Alumno/a", "Lugar entregado", "Retiro"], rows,
                                        col_widths=[24*mm, 55*mm, 35*mm, 40*mm]))

        if i < len(cursos) - 1:
            elements.append(PageBreak())

    def on_page(canvas, doc):
        _header_footer(canvas, doc, "Todos los Cursos", mes_label)

    doc.build(elements, onFirstPage=on_page, onLaterPages=on_page)
    buf.seek(0)
    return buf


# ════════════════════════════════════════════
#  PDF DESDE EXCEL (sin persistir en BD)
# ════════════════════════════════════════════

def generar_pdf_atrasos_excel(filas, meta=None):
    """Genera un PDF con los datos leídos de un Excel subido por el usuario.

    filas: lista de dicts con keys: fecha, apellido, nombre, curso, hora, tipo, lugar, errores
    meta: dict con archivo_nombre, generado, total, con_errores
    """
    meta = meta or {}
    total = len(filas)
    con_errores = sum(1 for f in filas if f.get("errores"))
    cursos_unicos = sorted({(f.get("curso") or "(sin curso)") for f in filas})
    tipos_unicos = sorted({(f.get("tipo") or "(sin tipo)") for f in filas})

    # Conteo por curso y por tipo
    from collections import Counter
    cnt_curso = Counter((f.get("curso") or "(sin curso)") for f in filas)
    cnt_tipo = Counter((f.get("tipo") or "(sin tipo)") for f in filas)

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=letter,
        topMargin=25*mm, bottomMargin=20*mm,
        leftMargin=18*mm, rightMargin=18*mm,
    )
    elements = []
    styles = _build_styles()

    mes_label = "Reporte desde Excel"
    curso_label = "Generado desde archivo Excel"

    # ── Portada (versión simple: sin informe específico ni leyenda de uso interno) ──
    _portada(elements, styles, curso_label, mes_label, simple=True)

    # ── Resumen ──
    elements.append(Paragraph("Resumen General", styles["ResumenTitulo"]))
    stat = _stat_table([
        (total, "Total Registros"),
        (con_errores, "Con observaciones"),
        (len(cursos_unicos), "Cursos"),
        (len(tipos_unicos), "Tipos"),
    ])
    elements.append(stat)
    elements.append(Spacer(1, 4*mm))

    # ── Distribución por curso ──
    if cnt_curso:
        elements.append(Paragraph("Distribución por Curso", styles["SubSeccion"]))
        rows = sorted(cnt_curso.items(), key=lambda x: -x[1])
        t_curso = _data_table(
            ["Curso", "Cantidad"],
            [[c, str(n)] for c, n in rows],
            col_widths=[100*mm, 40*mm],
        )
        elements.append(t_curso)
        elements.append(Spacer(1, 3*mm))

    # ── Distribución por tipo ──
    if cnt_tipo:
        elements.append(Paragraph("Distribución por Tipo", styles["SubSeccion"]))
        rows = sorted(cnt_tipo.items(), key=lambda x: -x[1])
        t_tipo = _data_table(
            ["Tipo", "Cantidad"],
            [[c, str(n)] for c, n in rows],
            col_widths=[100*mm, 40*mm],
        )
        elements.append(t_tipo)
        elements.append(Spacer(1, 4*mm))

    # ── Detalle completo ──
    elements.append(Paragraph("Detalle de Registros", styles["SeccionTitulo"]))
    elements.append(Spacer(1, 2*mm))
    if total == 0:
        elements.append(Paragraph("No se encontraron filas en el archivo.", styles["Normal9"]))
    else:
        elements.append(Paragraph(
            f"A continuación se muestran las {total} filas procesadas. "
            f"Las filas marcadas con ⚠ presentan observaciones (ver columna 'Obs.').",
            styles["Normal9"],
        ))
        elements.append(Spacer(1, 3*mm))

        # Ordenar por fecha y luego por apellido
        filas_ord = sorted(
            filas,
            key=lambda f: (
                f.get("fecha") or date.min,
                f.get("apellido") or "",
                f.get("nombre") or "",
            ),
        )

        detail_rows = []
        for f in filas_ord:
            errs = f.get("errores") or []
            obs_txt = "; ".join(errs) if errs else ""
            marker = "⚠ " if errs else ""
            detail_rows.append([
                marker + (f.get("fecha").strftime("%d/%m/%Y") if f.get("fecha") else "—"),
                f.get("apellido") or "",
                f.get("nombre") or "",
                f.get("curso") or "",
                f.get("hora").strftime("%H:%M") if f.get("hora") else "",
                f.get("tipo") or "",
                f.get("lugar") or "",
                obs_txt,
            ])

        t_det = _data_table(
            ["Fecha", "Apellido", "Nombre", "Curso", "Hora", "Tipo", "Lugar", "Obs."],
            detail_rows,
            col_widths=[20*mm, 22*mm, 22*mm, 18*mm, 14*mm, 18*mm, 22*mm, 38*mm],
        )
        elements.append(t_det)
        # Resaltar filas con error sobre el estilo base
        extra_style = []
        for i in range(1, len(detail_rows) + 1):
            errs = filas_ord[i - 1].get("errores") or []
            if errs:
                extra_style.append(("BACKGROUND", (0, i), (-1, i), colors.HexColor("#FFF3CD")))
                extra_style.append(("TEXTCOLOR", (7, i), (7, i), colors.HexColor("#9B0000")))
        if extra_style:
            t_det.setStyle(TableStyle(extra_style))

    # ── Sección de firmas (entrega al apoderado) ──
    elements.append(Spacer(1, 15*mm))

    firma_label_style = ParagraphStyle(
        "FirmaLabel", parent=styles["Normal"], fontName="Helvetica-Bold",
        fontSize=9, textColor=ROJO, alignment=TA_CENTER, spaceAfter=1*mm,
    )
    firma_hint_style = ParagraphStyle(
        "FirmaHint", parent=styles["Normal"], fontName="Helvetica", fontSize=8,
        textColor=GRIS, alignment=TA_CENTER, spaceBefore=1*mm,
    )
    firma_line_style = ParagraphStyle(
        "FirmaLine", parent=styles["Normal"], fontName="Helvetica", fontSize=9,
        textColor=NEGRO, alignment=TA_CENTER,
    )

    col_w = 75 * mm
    firmas_data = [
        [Paragraph("FUNCIONARIO QUE ENTREGA", firma_label_style),
         Paragraph("APODERADO", firma_label_style)],
        ["", ""],
        [Paragraph("________________________________", firma_line_style),
         Paragraph("________________________________", firma_line_style)],
        [Paragraph("Nombre y firma", firma_hint_style),
         Paragraph("Nombre y firma", firma_hint_style)],
        [Paragraph("RUT: __________________________", firma_line_style),
         Paragraph("RUT: __________________________", firma_line_style)],
    ]
    firmas_t = Table(firmas_data, colWidths=[col_w, col_w], rowHeights=[None, 12*mm, None, None, None])
    firmas_t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("LINEABOVE", (0, 0), (-1, 0), 1.2, ROJO),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2*mm),
        ("TOPPADDING", (0, 0), (-1, -1), 1*mm),
    ]))

    fecha_entrega_style = ParagraphStyle(
        "FechaEntrega", parent=styles["Normal"], fontName="Helvetica",
        fontSize=9, textColor=GRIS, alignment=TA_LEFT, spaceBefore=4*mm,
    )
    fecha_p = Paragraph("Fecha de entrega: ____ / ____ / ________", fecha_entrega_style)

    elements.append(KeepTogether([firmas_t, fecha_p]))

    # ── Build ──
    def on_page(canvas, doc):
        _header_footer(canvas, doc, "Reporte Excel", "Generado desde archivo")

    doc.build(elements, onFirstPage=on_page, onLaterPages=on_page)
    buf.seek(0)
    return buf
