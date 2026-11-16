"""Generacion del cuadro comparativo de faltas por curso en PPTX y PDF."""

import io
import os
import re
from datetime import date

from django.conf import settings
from django.db.models import Count

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.barcharts import HorizontalBarChart, VerticalBarChart
from reportlab.graphics.charts.piecharts import Pie
from reportlab.platypus import (
    HRFlowable,
    Image,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.lib.utils import ImageReader

from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE, XL_LABEL_POSITION, XL_LEGEND_POSITION
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

from .models import Alumno, Atraso, Celular, ControlUniforme, CURSOS
from .pdf_generator import MESES


ROJO = "#C8102E"
ROJO_OSCURO = "#9B0000"
DORADO = "#C5A000"
NEGRO = "#1A1A1A"
GRIS = "#666666"
GRIS_CLARO = "#F5F5F5"
BLANCO = "#FFFFFF"
UNIFORME_COLOR = "#7C3AED"
CELULAR_COLOR = "#0E7490"
ATRASO_COLOR = ROJO

SERIES_COLORS = [ATRASO_COLOR, UNIFORME_COLOR, CELULAR_COLOR]

CURSO_LABELS = dict(CURSOS)
CURSO_ORDER = {value: i for i, (value, _) in enumerate(CURSOS)}


def _rgb(value):
    return RGBColor.from_string(value.lstrip("#").upper())


def _como_fecha(valor):
    if not valor:
        return None
    if isinstance(valor, date):
        return valor
    try:
        return date.fromisoformat(str(valor))
    except ValueError:
        return None


def _periodo_label(mes, anio, fecha_desde, fecha_hasta):
    if fecha_desde or fecha_hasta:
        desde = fecha_desde.strftime("%d/%m/%Y") if fecha_desde else "Inicio"
        hasta = fecha_hasta.strftime("%d/%m/%Y") if fecha_hasta else "Hoy"
        return f"{desde} al {hasta}"
    return f"{MESES.get(mes, '')} {anio}".strip()


def obtener_datos_comparativo(mes=None, anio=None, fecha_desde=None, fecha_hasta=None):
    """Agrega atrasos, faltas de uniforme y celulares por curso.

    No incluye datos individuales de alumnos. Los atrasos con motivo CAMPO se
    excluyen, igual que en el informe de Frecuencia de Faltas.
    """
    hoy = date.today()
    fecha_desde = _como_fecha(fecha_desde)
    fecha_hasta = _como_fecha(fecha_hasta)
    usa_rango = bool(fecha_desde or fecha_hasta)

    if usa_rango:
        mes = hoy.month
        anio = hoy.year
    else:
        mes = int(mes or hoy.month)
        anio = int(anio or hoy.year)
        if not 1 <= mes <= 12:
            mes = hoy.month

    cursos = list(
        Alumno.objects.filter(activo=True)
        .exclude(curso="")
        .values_list("curso", flat=True)
        .distinct()
    )
    cursos.sort(key=lambda c: (CURSO_ORDER.get(c, 999), c))

    q_atrasos = Atraso.objects.filter(alumno__curso__in=cursos, alumno__activo=True).exclude(motivo="CAMPO")
    q_uniformes = ControlUniforme.objects.filter(alumno__curso__in=cursos, alumno__activo=True)
    q_celulares = Celular.objects.filter(alumno__curso__in=cursos, alumno__activo=True)

    if usa_rango:
        if fecha_desde:
            q_atrasos = q_atrasos.filter(fecha__gte=fecha_desde)
            q_uniformes = q_uniformes.filter(fecha__gte=fecha_desde)
            q_celulares = q_celulares.filter(fecha__gte=fecha_desde)
        if fecha_hasta:
            q_atrasos = q_atrasos.filter(fecha__lte=fecha_hasta)
            q_uniformes = q_uniformes.filter(fecha__lte=fecha_hasta)
            q_celulares = q_celulares.filter(fecha__lte=fecha_hasta)
    else:
        q_atrasos = q_atrasos.filter(fecha__month=mes, fecha__year=anio)
        q_uniformes = q_uniformes.filter(fecha__month=mes, fecha__year=anio)
        q_celulares = q_celulares.filter(fecha__month=mes, fecha__year=anio)

    conteo_atrasos = dict(q_atrasos.values_list("alumno__curso").annotate(n=Count("id")))
    conteo_uniformes = dict(q_uniformes.values_list("alumno__curso").annotate(n=Count("id")))
    conteo_celulares = dict(q_celulares.values_list("alumno__curso").annotate(n=Count("id")))

    filas = []
    for curso in cursos:
        atrasos = conteo_atrasos.get(curso, 0)
        uniformes = conteo_uniformes.get(curso, 0)
        celulares = conteo_celulares.get(curso, 0)
        total = atrasos + uniformes + celulares
        if total == 0:
            continue
        filas.append({
            "curso": curso,
            "curso_label": CURSO_LABELS.get(curso, curso),
            "atrasos": atrasos,
            "uniformes": uniformes,
            "celulares": celulares,
            "total": total,
        })

    filas.sort(key=lambda f: (-f["total"], CURSO_ORDER.get(f["curso"], 999), f["curso"]))

    totales = {
        "cursos": len(filas),
        "atrasos": sum(f["atrasos"] for f in filas),
        "uniformes": sum(f["uniformes"] for f in filas),
        "celulares": sum(f["celulares"] for f in filas),
    }
    totales["total"] = totales["atrasos"] + totales["uniformes"] + totales["celulares"]

    return {
        "filas": filas,
        "totales": totales,
        "periodo_label": _periodo_label(mes, anio, fecha_desde, fecha_hasta),
        "mes": mes,
        "anio": anio,
        "fecha_desde": fecha_desde,
        "fecha_hasta": fecha_hasta,
        "usa_rango": usa_rango,
    }


def nombre_archivo_comparativo(datos, extension):
    periodo = re.sub(r"[^A-Za-z0-9]+", "_", datos["periodo_label"]).strip("_")
    if not periodo:
        periodo = "periodo"
    return f"Comparativo_Cursos_{periodo}.{extension}"


def _logo_pptx(slide, prs):
    logo_path = os.path.join(settings.BASE_DIR, "static", "img", "logo.jpg")
    if os.path.exists(logo_path):
        slide.shapes.add_picture(logo_path, prs.slide_width - Inches(1.35), Inches(0.18), height=Inches(0.62))


def _rect_pptx(slide, left, top, width, height, fill_hex, line_hex=None):
    from pptx.enum.shapes import MSO_SHAPE

    shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, width, height)
    shape.fill.solid()
    shape.fill.fore_color.rgb = _rgb(fill_hex)
    if line_hex:
        shape.line.color.rgb = _rgb(line_hex)
    else:
        shape.line.fill.background()
    return shape


def _text_pptx(slide, text, left, top, width, height, size=16, bold=False,
               color=NEGRO, align=PP_ALIGN.LEFT, font="Arial"):
    box = slide.shapes.add_textbox(left, top, width, height)
    tf = box.text_frame
    tf.clear()
    tf.word_wrap = True
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.name = font
    run.font.color.rgb = _rgb(color)
    return box


def _header_pptx(slide, prs, title, periodo_label):
    _rect_pptx(slide, 0, 0, prs.slide_width, Inches(0.10), ROJO)
    _text_pptx(slide, title, Inches(0.55), Inches(0.35), Inches(10.4), Inches(0.55),
               size=25, bold=True, color=NEGRO)
    _text_pptx(slide, periodo_label, Inches(0.55), Inches(0.88), Inches(10.4), Inches(0.30),
               size=11, color=GRIS)
    _logo_pptx(slide, prs)
    _rect_pptx(slide, Inches(0.55), Inches(1.22), prs.slide_width - Inches(1.10), Inches(0.015), DORADO)


def _footer_pptx(slide, prs, numero):
    _rect_pptx(slide, Inches(0.55), Inches(7.06), prs.slide_width - Inches(1.10), Inches(0.012), DORADO)
    _text_pptx(slide, "Escuela Alemana Paillaco · Inspectoría General",
               Inches(0.55), Inches(7.10), Inches(8.5), Inches(0.25), size=8, color=GRIS)
    _text_pptx(slide, str(numero), prs.slide_width - Inches(1.15), Inches(7.10),
               Inches(0.60), Inches(0.25), size=8, bold=True, color=ROJO, align=PP_ALIGN.RIGHT)


def _nueva_slide(prs):
    return prs.slides.add_slide(prs.slide_layouts[6])


def _set_cell(cell, text, size=11, bold=False, color=NEGRO, align=PP_ALIGN.LEFT,
              fill_hex=None):
    cell.text = ""
    tf = cell.text_frame
    tf.clear()
    tf.word_wrap = True
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = str(text)
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.name = "Arial"
    run.font.color.rgb = _rgb(color)
    cell.margin_left = Inches(0.08)
    cell.margin_right = Inches(0.08)
    cell.margin_top = Inches(0.02)
    cell.margin_bottom = Inches(0.02)
    if fill_hex:
        cell.fill.solid()
        cell.fill.fore_color.rgb = _rgb(fill_hex)


def _ppt_table(slide, prs, datos):
    filas = datos["filas"]
    totales = datos["totales"]
    n_rows = len(filas) + 2
    top = Inches(1.48)
    width = prs.slide_width - Inches(1.10)
    height = Inches(5.38)
    shape = slide.shapes.add_table(n_rows, 5, Inches(0.55), top, width, height)
    table = shape.table
    table.first_row = False
    table.horz_banding = False

    widths = [Inches(4.55), Inches(1.80), Inches(1.80), Inches(1.80), Inches(1.98)]
    for i, col_w in enumerate(widths):
        table.columns[i].width = col_w

    row_h = min(0.34, 5.20 / n_rows)
    for row in table.rows:
        row.height = Inches(row_h)

    headers = ["Curso", "Atrasos", "Uniformes", "Celulares", "Total"]
    for i, header in enumerate(headers):
        _set_cell(table.cell(0, i), header, size=12, bold=True, color=BLANCO,
                  align=PP_ALIGN.CENTER if i else PP_ALIGN.LEFT, fill_hex=ROJO)

    for r, fila in enumerate(filas, start=1):
        bg = GRIS_CLARO if r % 2 == 0 else BLANCO
        _set_cell(table.cell(r, 0), fila["curso_label"], size=11, bold=True, fill_hex=bg)
        for c, key in enumerate(("atrasos", "uniformes", "celulares", "total"), start=1):
            _set_cell(table.cell(r, c), fila[key], size=11,
                      bold=(key == "total"), align=PP_ALIGN.CENTER, fill_hex=bg)

    total_row = n_rows - 1
    _set_cell(table.cell(total_row, 0), f"Total general ({totales['cursos']} cursos)",
              size=11, bold=True, fill_hex="#FBE9EC", color=ROJO_OSCURO)
    for c, key in enumerate(("atrasos", "uniformes", "celulares", "total"), start=1):
        _set_cell(table.cell(total_row, c), totales[key], size=11, bold=True,
                  align=PP_ALIGN.CENTER, fill_hex="#FBE9EC", color=ROJO_OSCURO)


def _ppt_summary(slide, prs, datos):
    totales = datos["totales"]
    cards = [
        (totales["cursos"], "Cursos con faltas", NEGRO),
        (totales["atrasos"], "Total atrasos", ATRASO_COLOR),
        (totales["uniformes"], "Faltas de uniforme", UNIFORME_COLOR),
        (totales["celulares"], "Celulares requisados", CELULAR_COLOR),
    ]
    left = Inches(0.55)
    gap = Inches(0.22)
    card_w = (prs.slide_width - Inches(1.10) - gap * 3) / 4
    for i, (valor, etiqueta, color) in enumerate(cards):
        x = left + i * (card_w + gap)
        _rect_pptx(slide, x, Inches(1.55), card_w, Inches(1.45), GRIS_CLARO, "#E5E5E5")
        _text_pptx(slide, str(valor), x, Inches(1.68), card_w, Inches(0.75),
                   size=34, bold=True, color=color, align=PP_ALIGN.CENTER)
        _text_pptx(slide, etiqueta, x, Inches(2.42), card_w, Inches(0.38),
                   size=11, color=GRIS, align=PP_ALIGN.CENTER)

    _text_pptx(slide, f"Período analizado: {datos['periodo_label']}",
               Inches(0.55), Inches(3.35), Inches(11.9), Inches(0.35), size=14, bold=True)
    _text_pptx(slide, f"Total de faltas registradas: {totales['total']}",
               Inches(0.55), Inches(3.78), Inches(11.9), Inches(0.35), size=14, bold=True,
               color=ROJO_OSCURO)
    _text_pptx(slide, "El cuadro incluye únicamente información agregada por curso. "
                      "No contiene nombres ni datos individuales de alumnos.",
               Inches(0.55), Inches(4.35), Inches(11.9), Inches(0.60), size=12, color=GRIS)


def _ppt_bar_chart(slide, datos):
    categorias = [f["curso_label"] for f in datos["filas"]]
    chart_data = CategoryChartData()
    chart_data.categories = categorias
    chart_data.add_series("Atrasos", [f["atrasos"] for f in datos["filas"]])
    chart_data.add_series("Uniformes", [f["uniformes"] for f in datos["filas"]])
    chart_data.add_series("Celulares", [f["celulares"] for f in datos["filas"]])

    chart = slide.shapes.add_chart(
        XL_CHART_TYPE.COLUMN_CLUSTERED,
        Inches(0.55), Inches(1.48), Inches(12.23), Inches(5.20), chart_data,
    ).chart
    chart.has_title = False
    chart.has_legend = True
    chart.legend.position = XL_LEGEND_POSITION.BOTTOM
    chart.legend.include_in_layout = False
    chart.legend.font.size = Pt(10)
    chart.font.size = Pt(9)

    for i, color in enumerate(SERIES_COLORS):
        serie = chart.series[i]
        serie.format.fill.solid()
        serie.format.fill.fore_color.rgb = _rgb(color)
        serie.format.line.fill.background()

    try:
        chart.category_axis.tick_labels.font.size = Pt(8)
        chart.value_axis.tick_labels.font.size = Pt(8)
    except AttributeError:
        pass


def _ppt_ranking_y_pie(slide, prs, datos):
    filas = datos["filas"]
    categorias = [f["curso_label"] for f in reversed(filas)]
    valores = [f["total"] for f in reversed(filas)]

    chart_data = CategoryChartData()
    chart_data.categories = categorias
    chart_data.add_series("Total de faltas", valores)
    chart = slide.shapes.add_chart(
        XL_CHART_TYPE.BAR_CLUSTERED,
        Inches(0.55), Inches(1.48), Inches(7.55), Inches(5.20), chart_data,
    ).chart
    chart.has_title = False
    chart.has_legend = False
    chart.font.size = Pt(9)
    chart.series[0].format.fill.solid()
    chart.series[0].format.fill.fore_color.rgb = _rgb(ROJO)
    try:
        chart.category_axis.tick_labels.font.size = Pt(8)
        chart.value_axis.tick_labels.font.size = Pt(8)
        plot = chart.plots[0]
        plot.has_data_labels = True
        plot.data_labels.font.size = Pt(8)
        plot.data_labels.position = XL_LABEL_POSITION.OUTSIDE_END
    except (AttributeError, ValueError):
        pass

    pie_data = CategoryChartData()
    pie_data.categories = ["Atrasos", "Uniformes", "Celulares"]
    pie_data.add_series("Distribución", (
        datos["totales"]["atrasos"],
        datos["totales"]["uniformes"],
        datos["totales"]["celulares"],
    ))
    pie = slide.shapes.add_chart(
        XL_CHART_TYPE.PIE,
        Inches(8.25), Inches(1.55), Inches(4.50), Inches(4.65), pie_data,
    ).chart
    pie.has_title = True
    pie.chart_title.text_frame.text = "Distribución por tipo"
    pie.chart_title.text_frame.paragraphs[0].font.size = Pt(14)
    pie.chart_title.text_frame.paragraphs[0].font.bold = True
    pie.has_legend = True
    pie.legend.position = XL_LEGEND_POSITION.BOTTOM
    pie.legend.include_in_layout = False
    pie.legend.font.size = Pt(9)
    for i, color in enumerate(SERIES_COLORS):
        point = pie.series[0].points[i]
        point.format.fill.solid()
        point.format.fill.fore_color.rgb = _rgb(color)
    try:
        plot = pie.plots[0]
        plot.has_data_labels = True
        plot.data_labels.show_percentage = True
        plot.data_labels.show_value = False
        plot.data_labels.font.size = Pt(9)
    except (AttributeError, ValueError):
        pass


def generar_pptx_comparativo(datos):
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)

    slide = _nueva_slide(prs)
    _rect_pptx(slide, 0, 0, Inches(0.22), prs.slide_height, ROJO)
    logo_path = os.path.join(settings.BASE_DIR, "static", "img", "logo.jpg")
    if os.path.exists(logo_path):
        slide.shapes.add_picture(logo_path, Inches(5.55), Inches(0.75), height=Inches(1.55))
    _text_pptx(slide, "ESCUELA ALEMANA PAILLACO", Inches(0.85), Inches(2.60),
               Inches(11.7), Inches(0.55), size=20, bold=True, color=ROJO, align=PP_ALIGN.CENTER)
    _text_pptx(slide, "INSPECTORÍA GENERAL", Inches(0.85), Inches(3.10),
               Inches(11.7), Inches(0.40), size=14, bold=True, color=NEGRO, align=PP_ALIGN.CENTER)
    _text_pptx(slide, "CUADRO COMPARATIVO DE FALTAS POR CURSO", Inches(0.85), Inches(3.75),
               Inches(11.7), Inches(0.70), size=30, bold=True, color=ROJO, align=PP_ALIGN.CENTER)
    _text_pptx(slide, datos["periodo_label"], Inches(0.85), Inches(4.52),
               Inches(11.7), Inches(0.45), size=18, color=GRIS, align=PP_ALIGN.CENTER)
    _rect_pptx(slide, Inches(4.40), Inches(5.10), Inches(4.55), Inches(0.018), DORADO)
    _text_pptx(slide, "Documento de uso interno · Información agregada por curso, sin datos de alumnos",
               Inches(0.85), Inches(5.35), Inches(11.7), Inches(0.45),
               size=11, color=GRIS, align=PP_ALIGN.CENTER)
    _footer_pptx(slide, prs, 1)

    slide = _nueva_slide(prs)
    _header_pptx(slide, prs, "Resumen General", datos["periodo_label"])
    _ppt_summary(slide, prs, datos)
    _footer_pptx(slide, prs, 2)

    slide = _nueva_slide(prs)
    _header_pptx(slide, prs, "Cuadro comparativo por curso", datos["periodo_label"])
    if datos["filas"]:
        _ppt_table(slide, prs, datos)
    else:
        _text_pptx(slide, "No se registraron faltas en el período seleccionado.",
                   Inches(0.55), Inches(2.70), Inches(12.2), Inches(0.60),
                   size=18, color=GRIS, align=PP_ALIGN.CENTER)
    _footer_pptx(slide, prs, 3)

    if datos["filas"]:
        slide = _nueva_slide(prs)
        _header_pptx(slide, prs, "Comparación por tipo de falta", datos["periodo_label"])
        _ppt_bar_chart(slide, datos)
        _footer_pptx(slide, prs, 4)

        slide = _nueva_slide(prs)
        _header_pptx(slide, prs, "Ranking y distribución", datos["periodo_label"])
        _ppt_ranking_y_pie(slide, prs, datos)
        _footer_pptx(slide, prs, 5)

    buf = io.BytesIO()
    prs.save(buf)
    buf.seek(0)
    return buf


def _slide_styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        "SlideTitle", parent=styles["Heading1"], fontName="Helvetica-Bold",
        fontSize=24, leading=28, textColor=colors.HexColor(ROJO), spaceAfter=4,
    ))
    styles.add(ParagraphStyle(
        "SlideSub", parent=styles["Normal"], fontName="Helvetica",
        fontSize=11, leading=14, textColor=colors.HexColor(GRIS), spaceAfter=10,
    ))
    styles.add(ParagraphStyle(
        "CoverTitle", parent=styles["Title"], fontName="Helvetica-Bold",
        fontSize=32, leading=38, textColor=colors.HexColor(ROJO), alignment=TA_CENTER,
        spaceBefore=10, spaceAfter=8,
    ))
    styles.add(ParagraphStyle(
        "CoverSub", parent=styles["Normal"], fontName="Helvetica",
        fontSize=17, leading=22, textColor=colors.HexColor(GRIS), alignment=TA_CENTER,
        spaceAfter=6,
    ))
    styles.add(ParagraphStyle(
        "CoverSchool", parent=styles["Normal"], fontName="Helvetica-Bold",
        fontSize=18, leading=22, textColor=colors.HexColor(ROJO), alignment=TA_CENTER,
        spaceAfter=4,
    ))
    styles.add(ParagraphStyle(
        "CoverArea", parent=styles["Normal"], fontName="Helvetica-Bold",
        fontSize=13, leading=16, textColor=colors.HexColor(NEGRO), alignment=TA_CENTER,
        spaceAfter=18,
    ))
    styles.add(ParagraphStyle(
        "SlideNote", parent=styles["Normal"], fontName="Helvetica",
        fontSize=11, leading=15, textColor=colors.HexColor(GRIS), alignment=TA_LEFT,
    ))
    styles.add(ParagraphStyle(
        "KpiValue", parent=styles["Normal"], fontName="Helvetica-Bold",
        fontSize=30, leading=34, alignment=TA_CENTER,
    ))
    styles.add(ParagraphStyle(
        "KpiLabel", parent=styles["Normal"], fontName="Helvetica",
        fontSize=10, leading=13, textColor=colors.HexColor(GRIS), alignment=TA_CENTER,
    ))
    styles.add(ParagraphStyle(
        "TableHead", parent=styles["Normal"], fontName="Helvetica-Bold",
        fontSize=11, leading=14, textColor=colors.white, alignment=TA_CENTER,
    ))
    styles.add(ParagraphStyle(
        "TableCell", parent=styles["Normal"], fontName="Helvetica",
        fontSize=10, leading=13, textColor=colors.HexColor(NEGRO),
    ))
    styles.add(ParagraphStyle(
        "TableCellCenter", parent=styles["Normal"], fontName="Helvetica",
        fontSize=10, leading=13, textColor=colors.HexColor(NEGRO), alignment=TA_CENTER,
    ))
    styles.add(ParagraphStyle(
        "TableTotal", parent=styles["Normal"], fontName="Helvetica-Bold",
        fontSize=10, leading=13, textColor=colors.HexColor(ROJO_OSCURO),
    ))
    styles.add(ParagraphStyle(
        "TableTotalCenter", parent=styles["Normal"], fontName="Helvetica-Bold",
        fontSize=10, leading=13, textColor=colors.HexColor(ROJO_OSCURO), alignment=TA_CENTER,
    ))
    styles.add(ParagraphStyle(
        "Legend", parent=styles["Normal"], fontName="Helvetica",
        fontSize=10, leading=14, textColor=colors.HexColor(NEGRO), alignment=TA_CENTER,
    ))
    return styles


def _slide_canvas(canvas, doc):
    canvas.saveState()
    if doc.page == 1:
        canvas.setFillColor(colors.HexColor(ROJO))
        canvas.rect(0, 0, 0.22 * inch, doc.pagesize[1], stroke=0, fill=1)
    else:
        canvas.setFillColor(colors.HexColor(ROJO))
        canvas.rect(0, doc.pagesize[1] - 0.10 * inch, doc.pagesize[0], 0.10 * inch, stroke=0, fill=1)
        logo_path = os.path.join(settings.BASE_DIR, "static", "img", "logo.jpg")
        if os.path.exists(logo_path):
            reader = ImageReader(logo_path)
            iw, ih = reader.getSize()
            h = 0.55 * inch
            w = h * iw / ih
            canvas.drawImage(logo_path, doc.pagesize[0] - 0.55 * inch - w,
                             doc.pagesize[1] - 0.18 * inch - h,
                             width=w, height=h, preserveAspectRatio=True, mask="auto")

    canvas.setStrokeColor(colors.HexColor(DORADO))
    canvas.setLineWidth(0.8)
    canvas.line(0.55 * inch, 0.46 * inch, doc.pagesize[0] - 0.55 * inch, 0.46 * inch)
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor(GRIS))
    canvas.drawString(0.55 * inch, 0.28 * inch, "Escuela Alemana Paillaco · Inspectoría General")
    canvas.setFont("Helvetica-Bold", 8)
    canvas.setFillColor(colors.HexColor(ROJO))
    canvas.drawRightString(doc.pagesize[0] - 0.55 * inch, 0.28 * inch, str(doc.page))
    canvas.restoreState()


def _pdf_cover(elements, styles, datos):
    elements.append(Spacer(1, 0.20 * inch))
    logo_path = os.path.join(settings.BASE_DIR, "static", "img", "logo.jpg")
    if os.path.exists(logo_path):
        reader = ImageReader(logo_path)
        iw, ih = reader.getSize()
        h = 1.45 * inch
        w = h * iw / ih
        elements.append(Image(logo_path, width=w, height=h, hAlign="CENTER"))
        elements.append(Spacer(1, 0.18 * inch))
    elements.append(Paragraph("ESCUELA ALEMANA PAILLACO", styles["CoverSchool"]))
    elements.append(Paragraph("INSPECTORÍA GENERAL", styles["CoverArea"]))
    elements.append(Paragraph("CUADRO COMPARATIVO DE FALTAS POR CURSO", styles["CoverTitle"]))
    elements.append(Paragraph(datos["periodo_label"], styles["CoverSub"]))
    elements.append(Spacer(1, 0.10 * inch))
    elements.append(HRFlowable(
        width="42%", thickness=1, color=colors.HexColor(DORADO),
        spaceBefore=0, spaceAfter=10, hAlign="CENTER",
    ))
    elements.append(Paragraph(
        "Documento de uso interno · Información agregada por curso, sin datos de alumnos",
        ParagraphStyle("cover_note", parent=styles["SlideNote"], alignment=TA_CENTER),
    ))


def _pdf_summary(elements, styles, datos):
    totales = datos["totales"]
    cards = [
        (totales["cursos"], "Cursos con faltas", NEGRO),
        (totales["atrasos"], "Total atrasos", ATRASO_COLOR),
        (totales["uniformes"], "Faltas de uniforme", UNIFORME_COLOR),
        (totales["celulares"], "Celulares requisados", CELULAR_COLOR),
    ]
    values = []
    labels = []
    for valor, etiqueta, color in cards:
        values.append(Paragraph(str(valor), ParagraphStyle(
            "kpi_v", parent=styles["KpiValue"], textColor=colors.HexColor(color),
        )))
        labels.append(Paragraph(etiqueta, styles["KpiLabel"]))
    table = Table([values, labels], colWidths=[(12.13 * inch - 0.6 * inch) / 4] * 4)
    table.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(GRIS_CLARO)),
        ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor("#E0E0E0")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E0E0E0")),
        ("TOPPADDING", (0, 0), (-1, 0), 8),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 2),
        ("TOPPADDING", (0, 1), (-1, 1), 0),
        ("BOTTOMPADDING", (0, 1), (-1, 1), 8),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 0.35 * inch))
    elements.append(Paragraph(
        f"Período analizado: <b>{datos['periodo_label']}</b>",
        ParagraphStyle("sum1", parent=styles["SlideNote"], fontSize=13, leading=17,
                       textColor=colors.HexColor(NEGRO)),
    ))
    elements.append(Paragraph(
        f"Total de faltas registradas: <b>{totales['total']}</b>",
        ParagraphStyle("sum2", parent=styles["SlideNote"], fontSize=13, leading=17,
                       textColor=colors.HexColor(ROJO_OSCURO)),
    ))
    elements.append(Spacer(1, 0.20 * inch))
    elements.append(Paragraph(
        "El cuadro incluye únicamente información agregada por curso. No contiene nombres "
        "ni datos individuales de alumnos.",
        styles["SlideNote"],
    ))


def _pdf_table(datos, styles):
    filas = datos["filas"]
    totales = datos["totales"]
    data = [[
        Paragraph("Curso", ParagraphStyle("th0", parent=styles["TableHead"], alignment=TA_LEFT)),
        Paragraph("Atrasos", styles["TableHead"]),
        Paragraph("Uniformes", styles["TableHead"]),
        Paragraph("Celulares", styles["TableHead"]),
        Paragraph("Total", styles["TableHead"]),
    ]]
    for fila in filas:
        data.append([
            Paragraph(fila["curso_label"], styles["TableCell"]),
            Paragraph(str(fila["atrasos"]), styles["TableCellCenter"]),
            Paragraph(str(fila["uniformes"]), styles["TableCellCenter"]),
            Paragraph(str(fila["celulares"]), styles["TableCellCenter"]),
            Paragraph(str(fila["total"]), styles["TableTotalCenter"]),
        ])
    data.append([
        Paragraph(f"Total general ({totales['cursos']} cursos)", styles["TableTotal"]),
        Paragraph(str(totales["atrasos"]), styles["TableTotalCenter"]),
        Paragraph(str(totales["uniformes"]), styles["TableTotalCenter"]),
        Paragraph(str(totales["celulares"]), styles["TableTotalCenter"]),
        Paragraph(str(totales["total"]), styles["TableTotalCenter"]),
    ])

    n_rows = len(data)
    row_h = min(0.34 * inch, 5.05 * inch / n_rows)
    table = Table(data, colWidths=[4.55 * inch, 1.80 * inch, 1.80 * inch, 1.80 * inch, 1.98 * inch],
                  rowHeights=[row_h] * n_rows)
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(ROJO)),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#D9D9D9")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, colors.HexColor(GRIS_CLARO)]),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#FBE9EC")),
        ("LINEABOVE", (0, -1), (-1, -1), 1.0, colors.HexColor(ROJO)),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
    ]
    table.setStyle(TableStyle(style))
    return table


def _legend(items, styles):
    partes = []
    for texto, color in items:
        partes.append(f'<font color="{color}">■</font> {texto}')
    return Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;".join(partes), styles["Legend"])


def _pdf_bar_chart(datos):
    drawing = Drawing(12.13 * inch, 4.55 * inch)
    chart = VerticalBarChart()
    chart.x = 0.45 * inch
    chart.y = 0.45 * inch
    chart.width = 11.1 * inch
    chart.height = 3.65 * inch
    chart.data = [
        [f["atrasos"] for f in datos["filas"]],
        [f["uniformes"] for f in datos["filas"]],
        [f["celulares"] for f in datos["filas"]],
    ]
    chart.categoryAxis.categoryNames = [f["curso_label"] for f in datos["filas"]]
    chart.categoryAxis.labels.fontName = "Helvetica"
    chart.categoryAxis.labels.fontSize = 7
    chart.categoryAxis.labels.angle = 35
    chart.categoryAxis.labels.dy = -4
    chart.valueAxis.valueMin = 0
    chart.valueAxis.labels.fontName = "Helvetica"
    chart.valueAxis.labels.fontSize = 8
    chart.groupSpacing = 8
    chart.barWidth = 5
    for i, color in enumerate(SERIES_COLORS):
        chart.bars[i].fillColor = colors.HexColor(color)
        chart.bars[i].strokeColor = colors.white
    drawing.add(chart)
    return drawing


def _pdf_ranking(datos):
    drawing = Drawing(7.55 * inch, 4.85 * inch)
    chart = HorizontalBarChart()
    chart.x = 1.05 * inch
    chart.y = 0.25 * inch
    chart.width = 6.10 * inch
    chart.height = 4.30 * inch
    filas = list(reversed(datos["filas"]))
    chart.data = [[f["total"] for f in filas]]
    chart.categoryAxis.categoryNames = [f["curso_label"] for f in filas]
    chart.categoryAxis.labels.fontName = "Helvetica"
    chart.categoryAxis.labels.fontSize = 8
    chart.valueAxis.valueMin = 0
    chart.valueAxis.labels.fontName = "Helvetica"
    chart.valueAxis.labels.fontSize = 8
    chart.bars[0].fillColor = colors.HexColor(ROJO)
    chart.bars[0].strokeColor = colors.white
    chart.barLabels.fontName = "Helvetica"
    chart.barLabels.fontSize = 8
    chart.barLabels.dx = 3
    drawing.add(chart)
    return drawing


def _pdf_pie(datos):
    drawing = Drawing(4.3 * inch, 4.15 * inch)
    pie = Pie()
    pie.x = 0.75 * inch
    pie.y = 0.20 * inch
    pie.width = 2.75 * inch
    pie.height = 2.75 * inch
    pie.data = [
        datos["totales"]["atrasos"],
        datos["totales"]["uniformes"],
        datos["totales"]["celulares"],
    ]
    pie.slices.strokeWidth = 1
    pie.slices.strokeColor = colors.white
    for i, color in enumerate(SERIES_COLORS):
        pie.slices[i].fillColor = colors.HexColor(color)
    drawing.add(pie)
    return drawing


def generar_pdf_comparativo(datos):
    buf = io.BytesIO()
    slide_size = (13.333 * inch, 7.5 * inch)
    doc = SimpleDocTemplate(
        buf, pagesize=slide_size,
        topMargin=0.78 * inch, bottomMargin=0.65 * inch,
        leftMargin=0.55 * inch, rightMargin=0.55 * inch,
    )
    styles = _slide_styles()
    elements = []

    _pdf_cover(elements, styles, datos)
    elements.append(PageBreak())

    elements.append(Paragraph("Resumen General", styles["SlideTitle"]))
    elements.append(Paragraph(datos["periodo_label"], styles["SlideSub"]))
    _pdf_summary(elements, styles, datos)
    elements.append(PageBreak())

    elements.append(Paragraph("Cuadro comparativo por curso", styles["SlideTitle"]))
    elements.append(Paragraph(datos["periodo_label"], styles["SlideSub"]))
    if datos["filas"]:
        elements.append(_pdf_table(datos, styles))
    else:
        elements.append(Paragraph(
            "No se registraron faltas en el período seleccionado.",
            ParagraphStyle("empty", parent=styles["SlideNote"], fontSize=16,
                           leading=22, alignment=TA_CENTER),
        ))

    if datos["filas"]:
        elements.append(PageBreak())
        elements.append(Paragraph("Comparación por tipo de falta", styles["SlideTitle"]))
        elements.append(Paragraph(datos["periodo_label"], styles["SlideSub"]))
        elements.append(_pdf_bar_chart(datos))
        elements.append(Spacer(1, 0.08 * inch))
        elements.append(_legend([
            ("Atrasos", ATRASO_COLOR),
            ("Uniformes", UNIFORME_COLOR),
            ("Celulares", CELULAR_COLOR),
        ], styles))
        elements.append(PageBreak())

        elements.append(Paragraph("Ranking y distribución", styles["SlideTitle"]))
        elements.append(Paragraph(datos["periodo_label"], styles["SlideSub"]))
        ranking = [
            Paragraph("Ranking de cursos por total de faltas",
                      ParagraphStyle("rank", parent=styles["SlideNote"], fontSize=11,
                                     textColor=colors.HexColor(NEGRO))),
            _pdf_ranking(datos),
        ]
        distribucion = [
            Paragraph("Distribución por tipo",
                      ParagraphStyle("dist", parent=styles["SlideNote"], fontSize=11,
                                     textColor=colors.HexColor(NEGRO))),
            _pdf_pie(datos),
            _legend([
                ("Atrasos", ATRASO_COLOR),
                ("Uniformes", UNIFORME_COLOR),
                ("Celulares", CELULAR_COLOR),
            ], styles),
        ]
        layout = Table([[ranking, distribucion]], colWidths=[7.75 * inch, 4.38 * inch])
        layout.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ]))
        elements.append(layout)

    doc.build(elements, onFirstPage=_slide_canvas, onLaterPages=_slide_canvas)
    buf.seek(0)
    return buf
