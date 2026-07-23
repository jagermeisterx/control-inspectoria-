"""Genera un PDF resumen del alumno a partir del Excel
RESUMEN_ATRASOS_AGUSTIN_VEGA.xlsx en la raíz del proyecto.
"""
import os
import sys
from datetime import datetime, date
from collections import Counter
from pathlib import Path

import django
import openpyxl

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "inspectoria.settings")
django.setup()

from core.pdf_generator import _build_styles, _stat_table, _data_table, _header_footer  # noqa: E402
from reportlab.lib.pagesizes import letter  # noqa: E402
from reportlab.lib.units import mm  # noqa: E402
from reportlab.platypus import (  # noqa: E402
    SimpleDocTemplate, Paragraph, Spacer, Image, HRFlowable, PageBreak,
)
from reportlab.lib.enums import TA_CENTER  # noqa: E402
from reportlab.lib.styles import ParagraphStyle  # noqa: E402

XLSX_PATH = BASE_DIR / "RESUMEN_ATRASOS_AGUSTIN_VEGA.xlsx"
OUT_PDF = BASE_DIR / "RESUMEN_ATRASOS_AGUSTIN_VEGA.pdf"


def leer_excel(path):
    wb = openpyxl.load_workbook(path, data_only=True)
    ws = wb["ATRASOS AGUSTIN VEGA"]
    registros = []
    for fila in ws.iter_rows(min_row=2, values_only=True):
        if not fila or fila[0] is None or fila[1] is None:
            continue
        if not isinstance(fila[1], (datetime, date)):
            continue
        if fila[1] == "TOTAL ATRASOS" or (isinstance(fila[0], str) and "TOTAL" in fila[0].upper()):
            continue
        registros.append({
            "mes": fila[0],
            "fecha": fila[1],
            "nombre": fila[2],
            "apellido": fila[3],
            "curso": fila[4],
            "hora": fila[5],
            "tipo": fila[6],
            "lugar": fila[7],
        })
    def _key(r):
        f = r["fecha"] if isinstance(r["fecha"], (datetime, date)) else date.min
        h = r["hora"] if hasattr(r["hora"], "hour") else None
        return (f, h)
    registros.sort(key=_key)
    return registros


def main():
    registros = leer_excel(XLSX_PATH)
    if not registros:
        print("Sin registros en el Excel.")
        return

    nombre = f"{registros[0]['nombre']} {registros[0]['apellido']}"
    curso = registros[0]["curso"] or "Sin curso"
    total = len(registros)
    conteo_mes = Counter(r["mes"] for r in registros)
    orden_meses = ["MARZO", "ABRIL", "MAYO", "JUNIO", "JULIO", "AGOSTO", "SEPTIEMBRE", "OCTUBRE", "NOVIEMBRE", "DICIEMBRE"]
    meses_presentes = [m for m in orden_meses if m in conteo_mes]
    tipos = Counter(r["tipo"] for r in registros)
    lugares = Counter(r["lugar"] for r in registros if r["lugar"])

    styles = _build_styles()
    curso_label = f"Reporte Individual — {nombre}"
    mes_label = "Resumen de Atrasos"

    buf_file = open(OUT_PDF, "wb")
    doc = SimpleDocTemplate(
        str(OUT_PDF), pagesize=letter,
        topMargin=25 * mm, bottomMargin=20 * mm,
        leftMargin=20 * mm, rightMargin=20 * mm,
    )
    elements = []

    elements.append(Spacer(1, 5 * mm))
    from core.pdf_generator import _get_logo_path
    logo_path = _get_logo_path()
    if os.path.exists(logo_path):
        elements.append(Image(logo_path, width=25 * mm, height=25 * mm))
        elements.append(Spacer(1, 4 * mm))

    elements.append(Paragraph("ESCUELA ALEMANA PAILLACO", styles["TituloEscuela"]))
    elements.append(HRFlowable(width="60%", thickness=1, color=styles["ResumenTitulo"].borderColor,
                                spaceBefore=2 * mm, spaceAfter=4 * mm, hAlign="CENTER"))
    elements.append(Paragraph("INSPECTORÍA GENERAL", styles["Subtitulo"]))
    elements.append(Paragraph(f"Reporte Individual — {nombre}", styles["SubtituloCurso"]))
    elements.append(Spacer(1, 4 * mm))

    hoy = date.today().strftime("%d/%m/%Y")
    info_data = [
        ["Alumno/a:", nombre, "Curso:", curso],
        ["Total atrasos:", str(total), "Período:", ", ".join(meses_presentes) or "—"],
        ["Generado:", hoy, "Archivo:", XLSX_PATH.name],
    ]
    from reportlab.platypus import Table, TableStyle
    from core.pdf_generator import GRIS, NEGRO
    info_t = Table(info_data, colWidths=[28 * mm, 55 * mm, 22 * mm, 55 * mm])
    info_t.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
        ("TEXTCOLOR", (0, 0), (0, -1), GRIS),
        ("TEXTCOLOR", (2, 0), (2, -1), GRIS),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2 * mm),
    ]))
    elements.append(info_t)
    elements.append(Spacer(1, 4 * mm))

    elements.append(Paragraph("Resumen General", styles["ResumenTitulo"]))
    stat = _stat_table([
        (total, "Total Atrasos"),
        (tipos.get("LLEGADA", 0), "Llegada tardía"),
        (tipos.get("RECREO", 0), "Recreo/Pasillo"),
        (len(meses_presentes), "Meses con registros"),
    ])
    elements.append(stat)
    elements.append(Spacer(1, 4 * mm))

    if total >= 10:
        warning_style = ParagraphStyle(
            "Warn", parent=styles["Normal"], fontName="Helvetica-Bold",
            fontSize=10, textColor=styles["AlertaWarning"].textColor, leftIndent=6 * mm,
        )
        elements.append(Paragraph(
            f"⚠ {nombre} acumula {total} atrasos. Se recomienda entrevista con apoderado.",
            warning_style))
        elements.append(Spacer(1, 3 * mm))

    elements.append(Paragraph("Distribución por Mes", styles["SubSeccion"]))
    rows_mes = [[m, str(conteo_mes.get(m, 0))] for m in meses_presentes]
    rows_mes.append(["TOTAL", str(total)])
    elements.append(_data_table(["Mes", "Cantidad"], rows_mes,
                                col_widths=[100 * mm, 40 * mm]))
    elements.append(Spacer(1, 3 * mm))

    if tipos:
        elements.append(Paragraph("Distribución por Tipo", styles["SubSeccion"]))
        rows_tipo = [[t, str(n)] for t, n in sorted(tipos.items(), key=lambda x: -x[1])]
        elements.append(_data_table(["Tipo", "Cantidad"], rows_tipo,
                                    col_widths=[100 * mm, 40 * mm]))
        elements.append(Spacer(1, 3 * mm))

    if lugares:
        elements.append(Paragraph("Motivos más frecuentes", styles["SubSeccion"]))
        rows_lug = [[l, str(n)] for l, n in lugares.most_common(8)]
        elements.append(_data_table(["Lugar / Razón", "Cantidad"], rows_lug,
                                    col_widths=[100 * mm, 40 * mm]))
        elements.append(Spacer(1, 4 * mm))

    elements.append(PageBreak())
    elements.append(Paragraph("Detalle de Atrasos", styles["SeccionTitulo"]))
    elements.append(Spacer(1, 2 * mm))
    elements.append(Paragraph(
        f"Listado completo de los {total} registros del alumno ordenados por fecha.",
        styles["Normal9"]))
    elements.append(Spacer(1, 3 * mm))

    filas = []
    for r in registros:
        fecha_txt = r["fecha"].strftime("%d/%m/%Y") if hasattr(r["fecha"], "strftime") else str(r["fecha"])
        hora_txt = r["hora"].strftime("%H:%M") if hasattr(r["hora"], "strftime") else str(r["hora"] or "")
        filas.append([
            fecha_txt, r["mes"], hora_txt, r["tipo"] or "", r["lugar"] or "",
        ])
    elements.append(_data_table(
        ["Fecha", "Mes", "Hora", "Tipo", "Lugar / Razón"],
        filas,
        col_widths=[22 * mm, 18 * mm, 16 * mm, 26 * mm, 68 * mm],
    ))

    def on_page(canvas, d):
        _header_footer(canvas, d, curso_label, mes_label)

    doc.build(elements, onFirstPage=on_page, onLaterPages=on_page)
    buf_file.close()
    print(f"OK -> {OUT_PDF}")
    print(f"Alumno: {nombre} | Curso: {curso} | Total: {total} atrasos")
    for m in meses_presentes:
        print(f"  {m}: {conteo_mes[m]}")


if __name__ == "__main__":
    main()
