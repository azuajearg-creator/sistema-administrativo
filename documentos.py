"""Generación de documentos PDF (nota de entrega y factura) con ReportLab.

No depende de la interfaz gráfica ni de bibliotecas del sistema, por lo que se
puede usar y probar sin abrir la aplicación.
"""
import datetime
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from config import EMPRESA_NOMBRE, EMPRESA_RIF, EMPRESA_CIUDAD, ruta_salida

def _p(texto):
    """Escapa texto del usuario para usarlo dentro de un Paragraph de ReportLab."""
    return escape(str(texto if texto is not None else ""))


def generar_pdf_nota(cliente_datos, direccion_cliente, items, observaciones, nro_nota):
    fecha_hoy = datetime.datetime.now().strftime("%d/%m/%Y")
    azul = colors.HexColor("#2980b9")
    estilos = getSampleStyleSheet()
    normal = ParagraphStyle("n", parent=estilos["Normal"], fontSize=10, leading=13)
    pequeno = ParagraphStyle("p", parent=normal, fontSize=9, leading=11)
    titulo = ParagraphStyle("t", parent=normal, fontName="Helvetica-Bold", fontSize=18,
                            leading=22, textColor=azul, alignment=1)
    centro = ParagraphStyle("c", parent=pequeno, alignment=1)
    derecha = ParagraphStyle("d", parent=normal, alignment=2)

    nombre_archivo = ruta_salida(f"Nota_{nro_nota}.pdf")

    def firmas(canvas, doc):
        """Dibuja las líneas de firma al pie de la primera página."""
        canvas.saveState()
        canvas.setFont("Helvetica", 9)
        y = 22 * mm
        for x0, x1, l1, l2 in (
            (15 * mm, 85 * mm, f"Por {EMPRESA_NOMBRE}", "Firma y Sello Autorizado"),
            (125 * mm, 195 * mm, "Recibido por el Cliente", "Nombre / C.I. / Fecha"),
        ):
            canvas.line(x0, y + 12, x1, y + 12)
            canvas.drawCentredString((x0 + x1) / 2, y, l1[:60])
            canvas.drawCentredString((x0 + x1) / 2, y - 11, l2)
        canvas.restoreState()

    doc = SimpleDocTemplate(nombre_archivo, pagesize=letter, leftMargin=15 * mm, rightMargin=15 * mm,
                            topMargin=15 * mm, bottomMargin=38 * mm)
    historia = [
        Paragraph(_p(EMPRESA_NOMBRE.upper()), titulo),
        Paragraph(f"<b>RIF:</b> {_p(EMPRESA_RIF)}", centro),
        Paragraph(_p(EMPRESA_CIUDAD), centro),
        Spacer(1, 4),
    ]
    cabecera = Table([[
        Paragraph(f"<b>CLIENTE:</b> {_p(cliente_datos)}<br/><b>DIRECCIÓN:</b> {_p(direccion_cliente)}", normal),
        Paragraph(f"<b>NOTA DE ENTREGA:</b> <font color='#c0392b'># {_p(nro_nota)}</font><br/><b>FECHA:</b> {fecha_hoy}", derecha),
    ]], colWidths=[115 * mm, 65 * mm])
    cabecera.setStyle(TableStyle([("LINEABOVE", (0, 0), (-1, 0), 1.5, azul),
                                  ("VALIGN", (0, 0), (-1, -1), "TOP"),
                                  ("TOPPADDING", (0, 0), (-1, -1), 8)]))
    historia += [cabecera, Spacer(1, 10)]

    filas = [["ITEM", "DESCRIPCIÓN DEL INSUMO / SERVICIO", "CANTIDAD"]]
    for i, it in enumerate(items, 1):
        filas.append([str(i), Paragraph(_p(it["nombre"]), pequeno), str(it["cantidad"])])
    tabla = Table(filas, colWidths=[18 * mm, 124 * mm, 38 * mm], repeatRows=1)
    tabla.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), azul), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"), ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (0, 0), (0, -1), "CENTER"), ("ALIGN", (2, 0), (2, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dddddd")),
    ]))
    historia += [tabla, Spacer(1, 12), Paragraph("<b>OBSERVACIONES Y CONDICIONES:</b>", normal)]
    obs = Table([[Paragraph(_p(observaciones) if observaciones else "Sin observaciones adicionales.", pequeno)]],
                colWidths=[180 * mm])
    obs.setStyle(TableStyle([("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
                             ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f9f9f9")),
                             ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 14)]))
    historia += [Spacer(1, 3), obs]
    doc.build(historia, onFirstPage=firmas)
    return nombre_archivo


def generar_pdf_factura(datos_cliente, items, porc_desc, monto_desc, subtotal, iva, total, nro_factura_manual):
    fecha_hoy = datetime.datetime.now().strftime("%d/%m/%Y")
    azul = colors.HexColor("#2980b9")
    estilos = getSampleStyleSheet()
    normal = ParagraphStyle("n", parent=estilos["Normal"], fontSize=10, leading=13)
    pequeno = ParagraphStyle("p", parent=normal, fontSize=9, leading=11)
    derecha = ParagraphStyle("d", parent=normal, alignment=2)

    nombre_archivo = ruta_salida(f"Factura_{nro_factura_manual}.pdf")
    # Margen superior amplio: deja espacio para un encabezado pre-impreso.
    doc = SimpleDocTemplate(nombre_archivo, pagesize=letter, leftMargin=15 * mm, rightMargin=15 * mm,
                            topMargin=40 * mm, bottomMargin=15 * mm)
    historia = [
        Paragraph(f"<font color='#e74c3c' size='14'><b>FACTURA NRO: {_p(nro_factura_manual)}</b></font>", derecha),
        Paragraph(f"<b>FECHA DE EMISIÓN: {fecha_hoy}</b>", derecha),
        Spacer(1, 12),
    ]
    comprador = Table([[Paragraph(
        "<b>DATOS DEL CLIENTE</b><br/>"
        f"<b>RAZÓN SOCIAL:</b> {_p(datos_cliente['nombre'])}<br/>"
        f"<b>RIF:</b> {_p(datos_cliente['rif'])}<br/>"
        f"<b>DIRECCIÓN FISCAL:</b> {_p(datos_cliente['direccion'])}<br/>"
        f"<b>TELÉFONO:</b> {_p(datos_cliente['telefono'])}", pequeno)]], colWidths=[180 * mm])
    comprador.setStyle(TableStyle([("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#dddddd")),
                                   ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f9f9f9")),
                                   ("TOPPADDING", (0, 0), (-1, -1), 8), ("BOTTOMPADDING", (0, 0), (-1, -1), 8)]))
    historia += [comprador, Spacer(1, 12)]

    filas = [["ITEM", "DESCRIPCIÓN", "CANT.", "P. UNIT", "TOTAL"]]
    for i, it in enumerate(items, 1):
        filas.append([str(i), Paragraph(_p(it["nombre"]), pequeno), str(it["cantidad"]),
                      f"${it['precio']:.2f}", f"${it['subtotal']:.2f}"])
    tabla = Table(filas, colWidths=[14 * mm, 90 * mm, 20 * mm, 28 * mm, 28 * mm], repeatRows=1)
    tabla.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), azul), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"), ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (0, 0), (0, -1), "CENTER"), ("ALIGN", (2, 0), (-1, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LINEBELOW", (0, 1), (-1, -1), 0.5, colors.HexColor("#eeeeee")),
    ]))
    historia += [tabla, Spacer(1, 16)]

    totales = Table([
        ["SUBTOTAL BRUTO:", f"${subtotal:.2f}"],
        [f"DESCUENTO ({porc_desc}%):", f"-${monto_desc:.2f}"],
        ["BASE IMPONIBLE:", f"${(subtotal - monto_desc):.2f}"],
        ["I.V.A. (16%):", f"${iva:.2f}"],
        ["TOTAL A PAGAR:", f"${total:.2f}"],
    ], colWidths=[45 * mm, 32 * mm], hAlign="RIGHT")
    totales.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "RIGHT"), ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"), ("FONTSIZE", (0, -1), (-1, -1), 12),
        ("LINEABOVE", (0, -1), (-1, -1), 1.5, azul), ("TEXTCOLOR", (0, -1), (-1, -1), colors.HexColor("#1e8449")),
    ]))
    historia.append(KeepTogether(totales))
    doc.build(historia)
    return nombre_archivo
