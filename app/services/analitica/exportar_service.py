from datetime import datetime
from io import BytesIO

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer


def _label(key: str) -> str:
    return key.replace("_", " ").title()


def _valor(value) -> str:
    if value is None:
        return "—"
    if isinstance(value, dict):
        return ", ".join(f"{_label(k)}: {v}" for k, v in value.items())
    if isinstance(value, float):
        return f"{value:,.2f}"
    return str(value)


def generar_pdf(titulo: str, transcripcion: str, datos: dict) -> BytesIO:
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
    elements.append(
        Paragraph(
            f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
            styles["Normal"],
        )
    )
    elements.append(Spacer(1, 8))
    elements.append(Paragraph(f"<b>Consulta:</b> {transcripcion}", styles["Normal"]))
    elements.append(Spacer(1, 16))

    table_data = [["Métrica", "Valor"]]
    for key, value in datos.items():
        table_data.append([_label(key), _valor(value)])

    col_widths = [9 * cm, 9 * cm]
    table = Table(table_data, colWidths=col_widths, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a237e")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 11),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
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


def generar_excel(titulo: str, transcripcion: str, datos: dict) -> BytesIO:
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

    ws.merge_cells("A1:B1")
    ws["A1"] = "AutoSOS — Reporte Media Voz"
    ws["A1"].font = Font(bold=True, size=14, color="FFFFFF")
    ws["A1"].fill = PatternFill("solid", fgColor=azul)
    ws["A1"].alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[1].height = 28

    ws.merge_cells("A2:B2")
    ws["A2"] = titulo
    ws["A2"].font = Font(bold=True, size=12)
    ws["A2"].alignment = Alignment(horizontal="center")

    ws.merge_cells("A3:B3")
    ws["A3"] = f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}"
    ws["A3"].font = Font(italic=True, size=10, color="555555")
    ws["A3"].alignment = Alignment(horizontal="center")

    ws.merge_cells("A4:B4")
    ws["A4"] = f"Consulta: {transcripcion}"
    ws["A4"].font = Font(size=10)
    ws["A4"].alignment = Alignment(wrap_text=True)
    ws.row_dimensions[4].height = 36

    ws["A5"] = "Métrica"
    ws["B5"] = "Valor"
    for cell in [ws["A5"], ws["B5"]]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor=azul)
        cell.alignment = Alignment(horizontal="center")
        cell.border = borde

    for i, (key, value) in enumerate(datos.items(), start=6):
        ws.cell(row=i, column=1, value=_label(key)).border = borde
        ws.cell(row=i, column=2, value=_valor(value)).border = borde
        if i % 2 == 0:
            ws.cell(row=i, column=1).fill = PatternFill("solid", fgColor=azul_claro)
            ws.cell(row=i, column=2).fill = PatternFill("solid", fgColor=azul_claro)

    ws.column_dimensions["A"].width = 30
    ws.column_dimensions["B"].width = 35

    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer