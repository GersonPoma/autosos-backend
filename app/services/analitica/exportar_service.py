from datetime import datetime
from io import BytesIO
from typing import Optional

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer


def _label(key: str) -> str:
    return key.replace("_", " ").title()


def _valor_str(value) -> str:
    """Convierte cualquier valor a string legible para una celda."""
    if value is None:
        return "—"
    if isinstance(value, float):
        return f"{value:,.2f}"
    if isinstance(value, dict):
        return "\n".join(f"{_label(k)}: {v}" for k, v in value.items())
    if isinstance(value, list):
        if not value:
            return "—"
        if isinstance(value[0], dict):
            partes = []
            for item in value:
                partes.append("  •  " + "  |  ".join(f"{_label(k)}: {v}" for k, v in item.items()))
            return "\n".join(partes)
        return "\n".join(f"• {v}" for v in value)
    return str(value)


def _rango_fechas_str(fecha_inicio: Optional[str], fecha_fin: Optional[str]) -> Optional[str]:
    if fecha_inicio and fecha_fin:
        return f"Período: {fecha_inicio}  →  {fecha_fin}"
    return None


def generar_pdf(
    titulo: str,
    transcripcion: str,
    datos: dict,
    fecha_inicio: Optional[str] = None,
    fecha_fin: Optional[str] = None,
) -> BytesIO:
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        leftMargin=2.5 * cm,
        rightMargin=2.5 * cm,
    )
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("AutoSOS — Reporte Media Voz", styles["Title"]))
    elements.append(Spacer(1, 6))
    elements.append(Paragraph(titulo, styles["Heading2"]))
    elements.append(Spacer(1, 4))
    elements.append(Paragraph(f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles["Normal"]))

    rango = _rango_fechas_str(fecha_inicio, fecha_fin)
    if rango:
        elements.append(Paragraph(rango, styles["Normal"]))

    elements.append(Spacer(1, 8))
    elements.append(Paragraph(f"<b>Consulta:</b> {transcripcion}", styles["Normal"]))
    elements.append(Spacer(1, 16))

    table_data = [["Métrica", "Valor"]]
    for key, value in datos.items():
        table_data.append([_label(key), _valor_str(value)])

    col_widths = [7 * cm, 11 * cm]
    table = Table(table_data, colWidths=col_widths, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a237e")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 11),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 1), (-1, -1), 10),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#e8eaf6")]),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#9e9e9e")),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ]
        )
    )
    elements.append(table)

    doc.build(elements)
    buffer.seek(0)
    return buffer


def generar_excel(
    titulo: str,
    transcripcion: str,
    datos: dict,
    fecha_inicio: Optional[str] = None,
    fecha_fin: Optional[str] = None,
) -> BytesIO:
    wb = Workbook()
    ws = wb.active
    ws.title = "Reporte"

    azul = "1a237e"
    azul_claro = "e8eaf6"
    borde = Border(
        left=Side(style="thin"),
        right=Side(style="thin"),
        top=Side(style="thin"),
        bottom=Side(style="thin"),
    )

    # Fila 1 — título
    ws.merge_cells("A1:B1")
    ws["A1"] = "AutoSOS — Reporte Media Voz"
    ws["A1"].font = Font(bold=True, size=14, color="FFFFFF")
    ws["A1"].fill = PatternFill("solid", fgColor=azul)
    ws["A1"].alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[1].height = 28

    # Fila 2 — subtítulo
    ws.merge_cells("A2:B2")
    ws["A2"] = titulo
    ws["A2"].font = Font(bold=True, size=12)
    ws["A2"].alignment = Alignment(horizontal="center")

    # Fila 3 — fecha generación
    ws.merge_cells("A3:B3")
    ws["A3"] = f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}"
    ws["A3"].font = Font(italic=True, size=10, color="555555")
    ws["A3"].alignment = Alignment(horizontal="center")

    # Fila 4 — rango de fechas (si existe) o consulta
    fila_consulta = 4
    rango = _rango_fechas_str(fecha_inicio, fecha_fin)
    if rango:
        ws.merge_cells("A4:B4")
        ws["A4"] = rango
        ws["A4"].font = Font(italic=True, size=10, color="1a237e")
        ws["A4"].alignment = Alignment(horizontal="center")
        fila_consulta = 5

    ws.merge_cells(f"A{fila_consulta}:B{fila_consulta}")
    ws[f"A{fila_consulta}"] = f"Consulta: {transcripcion}"
    ws[f"A{fila_consulta}"].font = Font(size=10)
    ws[f"A{fila_consulta}"].alignment = Alignment(wrap_text=True)
    ws.row_dimensions[fila_consulta].height = 36

    # Encabezados de tabla
    fila_header = fila_consulta + 1
    ws.cell(row=fila_header, column=1, value="Métrica").font = Font(bold=True, color="FFFFFF")
    ws.cell(row=fila_header, column=2, value="Valor").font = Font(bold=True, color="FFFFFF")
    for col in [1, 2]:
        c = ws.cell(row=fila_header, column=col)
        c.fill = PatternFill("solid", fgColor=azul)
        c.alignment = Alignment(horizontal="center")
        c.border = borde

    # Datos
    for i, (key, value) in enumerate(datos.items(), start=fila_header + 1):
        celda_label = ws.cell(row=i, column=1, value=_label(key))
        celda_valor = ws.cell(row=i, column=2, value=_valor_str(value))
        celda_label.border = borde
        celda_valor.border = borde
        celda_valor.alignment = Alignment(wrap_text=True, vertical="top")
        celda_label.alignment = Alignment(vertical="top")
        if i % 2 == 0:
            celda_label.fill = PatternFill("solid", fgColor=azul_claro)
            celda_valor.fill = PatternFill("solid", fgColor=azul_claro)
        # Altura dinámica para listas largas (técnicos)
        if isinstance(value, list) and len(value) > 1:
            ws.row_dimensions[i].height = max(15 * len(value), 30)

    ws.column_dimensions["A"].width = 30
    ws.column_dimensions["B"].width = 45

    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer