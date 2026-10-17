from config import EMPRESA_NOMBRE, EMPRESA_RIF, EMPRESA_CIUDAD, ruta_salida, abrir_archivo  # noqa: F401
import customtkinter as ctk
from tkinter import ttk, messagebox
from datetime import datetime
import os
# Librerías de ReportLab para el motor de PDF
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

# Importamos las consultas desde la base de datos
from base_datos import (obtener_total_ventas_filtrado, obtener_historial_filtrado,
                        obtener_reporte_inventario, obtener_cuentas_por_cobrar,
                        obtener_reporte_notas, obtener_reporte_pdf_cxp, 
                        obtener_reporte_pdf_pagos_cxp, obtener_inventario_completo)

class VentanaReportes(ctk.CTkToplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title(f"Centro de Reportes - {EMPRESA_NOMBRE}")
        self.after(0, lambda: self.state('zoomed'))
        self.focus_force()
        self.grab_set() 

        # --- BOTÓN REGRESAR ---
        self.btn_regresar = ctk.CTkButton(self, text="← VOLVER", width=100, fg_color="#7f8c8d", command=self.destroy)
        self.btn_regresar.place(x=20, y=20)

        ctk.CTkLabel(self, text="PANEL DE CONTROL Y REPORTES", font=("Arial", 24, "bold")).pack(pady=(40, 10))

        # --- FILTRO DE FECHAS (Para Ventas y Notas) ---
        self.frame_filtros = ctk.CTkFrame(self)
        self.frame_filtros.pack(fill="x", padx=20, pady=10)

        fecha_hoy = datetime.now().strftime("%Y-%m-%d")
        ctk.CTkLabel(self.frame_filtros, text="Desde (AAAA-MM-DD):").pack(side="left", padx=10, pady=10)
        self.ent_desde = ctk.CTkEntry(self.frame_filtros, width=120)
        self.ent_desde.insert(0, fecha_hoy)
        self.ent_desde.pack(side="left", padx=5, pady=10)

        ctk.CTkLabel(self.frame_filtros, text="Hasta (AAAA-MM-DD):").pack(side="left", padx=10, pady=10)
        self.ent_hasta = ctk.CTkEntry(self.frame_filtros, width=120)
        self.ent_hasta.insert(0, fecha_hoy)
        self.ent_hasta.pack(side="left", padx=5, pady=10)

        self.btn_buscar = ctk.CTkButton(self.frame_filtros, text="⚡ Actualizar Filtros", fg_color="#2980b9", command=self.actualizar_todo)
        self.btn_buscar.pack(side="left", padx=20, pady=10)

        # --- CONTENEDOR DE PESTAÑAS ---
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=20, pady=10)

        # Creación de pestañas existentes
        self.tab_ventas = self.tabview.add("📊 Ventas Facturadas")
        self.tab_notas = self.tabview.add("📑 Notas de Entrega")
        self.tab_inv = self.tabview.add("📦 Inventario Crítico")
        self.tab_cxc = self.tabview.add("📈 Cuentas por Cobrar")
        self.tab_cxp = self.tabview.add("💰 Cuentas por Pagar (CxP)") # ¡NUEVA PESTAÑA!

        # Configuración de Pestaña: Ventas
        self.lbl_total_ventas = ctk.CTkLabel(self.tab_ventas, text="Total Ventas Facturadas: $0.00", font=("Arial", 16, "bold"), text_color="#27ae60")
        self.lbl_total_ventas.pack(pady=5)
        self.tabla_ventas = self.crear_tabla(self.tab_ventas, ["ID", "Cliente", "Total Facturado", "Fecha"])

        # Configuración de Pestaña: Notas de Entrega
        self.tabla_notas = self.crear_tabla(self.tab_notas, ["Nro Nota", "Cliente", "Dirección", "Observaciones", "Estado", "Fecha"])

        # Configuración de Pestaña: Inventario
        self.frame_botones_inv = ctk.CTkFrame(self.tab_inv)
        self.frame_botones_inv.pack(fill="x", padx=10, pady=10)

        self.btn_pdf_inv_total = ctk.CTkButton(self.frame_botones_inv, text="📄 PDF INVENTARIO COMPLETO", fg_color="#2980b9", hover_color="#3498db", command=self.exportar_pdf_inventario_completo)
        self.btn_pdf_inv_total.pack(side="left", padx=10, pady=5, expand=True, fill="x")

        self.btn_pdf_inv_critico = ctk.CTkButton(self.frame_botones_inv, text="📄 PDF INVENTARIO CRÍTICO", fg_color="#c0392b", hover_color="#e74c3c", command=self.exportar_pdf_inventario_critico)
        self.btn_pdf_inv_critico.pack(side="left", padx=10, pady=5, expand=True, fill="x")

        self.tabla_inv = self.crear_tabla(self.tab_inv, ["Código", "Producto", "Marca", "Costo", "Venta", "Stock", "Mínimo"])

        # Configuración de Pestaña: Cuentas por Cobrar (CxC)
        self.tabla_cxc = self.crear_tabla(self.tab_cxc, ["ID", "Fecha", "Cliente", "Total", "Saldo Pendiente"])

        # Configuración de Pestaña: Cuentas por Pagar (CxP) - NUEVA ESTRUCTURA EN VIVO
        self.frame_botones_cxp = ctk.CTkFrame(self.tab_cxp)
        self.frame_botones_cxp.pack(fill="x", padx=10, pady=10)

        self.btn_pdf_pendientes = ctk.CTkButton(self.frame_botones_cxp, text="📄 PDF DEUDAS PENDIENTES", fg_color="#d35400", hover_color="#e67e22", command=self.exportar_pdf_cxp_pendientes)
        self.btn_pdf_pendientes.pack(side="left", padx=10, pady=5, expand=True, fill="x")

        self.btn_pdf_historico = ctk.CTkButton(self.frame_botones_cxp, text="📄 PDF HISTORIAL DE ABONOS", fg_color="#27ae60", hover_color="#2ecc71", command=self.exportar_pdf_historico_pagos)
        self.btn_pdf_historico.pack(side="left", padx=10, pady=5, expand=True, fill="x")

        self.tabla_cxp = self.crear_tabla(self.tab_cxp, ["Factura", "Proveedor", "F. Emisión", "F. Vencimiento", "Monto Total", "Saldo Residual"])

        # Cargar los datos iniciales al abrir la ventana
        self.actualizar_todo()

    def crear_tabla(self, master, columnas):
        frame = ctk.CTkFrame(master)
        frame.pack(fill="both", expand=True, padx=5, pady=5)
        tabla = ttk.Treeview(frame, columns=columnas, show="headings")
        for col in columnas:
            tabla.heading(col, text=col)
            tabla.column(col, anchor="center", width=120)
        scroll = ttk.Scrollbar(frame, orient="vertical", command=tabla.yview)
        tabla.configure(yscroll=scroll.set)
        tabla.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        return tabla

    def actualizar_todo(self):
        f_i, f_f = self.ent_desde.get(), self.ent_hasta.get()
        
        # Llenado de tablas existentes
        self.limpiar_y_llenar(self.tabla_ventas, obtener_historial_filtrado(f_i, f_f))
        total_v = obtener_total_ventas_filtrado(f_i, f_f)
        self.lbl_total_ventas.configure(text=f"Total Ventas Facturadas: ${float(total_v or 0):,.2f}")
        self.limpiar_y_llenar(self.tabla_notas, obtener_reporte_notas(f_i, f_f))
        self.limpiar_y_llenar(self.tabla_inv, obtener_inventario_completo())
        
        cxc_datos = obtener_cuentas_por_cobrar()
        self.limpiar_y_llenar(self.tabla_cxc, cxc_datos)

        # Llenado dinámico de la nueva tabla de Cuentas por Pagar (CxP)
        cxp_datos = obtener_reporte_pdf_cxp()
        # Mapeamos los datos para dar formato monetario en la vista de la tabla
        cxp_formateado = []
        for row in cxp_datos:
            cxp_formateado.append((row[0], row[1], row[2], row[3], f"$ {row[4]:,.2f}", f"$ {row[5]:,.2f}"))
        self.limpiar_y_llenar(self.tabla_cxp, cxp_formateado)

    def limpiar_y_llenar(self, tabla, datos):
        for item in tabla.get_children():
            tabla.delete(item)
        if datos:
            for fila in datos:
                tabla.insert("", "end", values=fila)

    # =========================================================================
    # MOTOR DE EXPORTACIÓN PDF (REPORTLAB) - CUENTAS POR PAGAR
    # =========================================================================

    def exportar_pdf_cxp_pendientes(self):
        datos = obtener_reporte_pdf_cxp()
        if not datos:
            return messagebox.showinfo("Reporte Vacío", "No existen cuentas por pagar pendientes en este momento.")
        
        nombre_archivo = ruta_salida(f"Reporte_CxP_Pendientes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf")
        doc = SimpleDocTemplate(nombre_archivo, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
        story = []
        styles = getSampleStyleSheet()
        
        # Encabezado Corporativo
        story.append(Paragraph(f"<b>{EMPRESA_NOMBRE.upper()}</b>", styles['Heading1']))
        story.append(Paragraph(f"<b>REPORTE CONSOLIDADO DE CUENTAS POR PAGAR (DEUDAS)</b><br/>Fecha de Emisión: {datetime.now().strftime('%d/%m/%Y %H:%M')}<br/><br/>", styles['Normal']))
        
        # Estructura de la tabla del documento PDF
        tabla_datos = [["Nro Factura", "Proveedor", "F. Emisión", "F. Vence", "Total", "Saldo Residual"]]
        total_deuda = 0
        for row in datos:
            tabla_datos.append([row[0], row[1][:25], row[2], row[3], f"$ {row[4]:,.2f}", f"$ {row[5]:,.2f}"])
            total_deuda += row[5]
            
        tabla_datos.append(["", "", "", "TOTAL PENDIENTE:", "", f"$ {total_deuda:,.2f}"])
        
        t = Table(tabla_datos, colWidths=[80, 150, 75, 75, 75, 80])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#d35400')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0,0), (-1,0), 6),
            ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor('#f2f2f2')),
            ('FONTNAME', (0,-1), (-1,-1), 'Helvetica-Bold'),
            ('GRID', (0,0), (-1,-2), 0.5, colors.grey),
        ]))
        
        story.append(t)
        doc.build(story)
        abrir_archivo(nombre_archivo)

    # =========================================================================
    # MOTOR DE EXPORTACIÓN PDF - INVENTARIO
    # =========================================================================

    def exportar_pdf_inventario_completo(self):
        datos = obtener_inventario_completo()
        if not datos:
            return messagebox.showinfo("Reporte Vacío", "No hay productos registrados en el inventario.")
        
        nombre_archivo = ruta_salida(f"Inventario_General_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf")
        self._generar_pdf_inv_template("REPORTE GENERAL DE PRODUCTOS E INVENTARIO", datos, nombre_archivo, colors.HexColor('#2980b9'))

    def exportar_pdf_inventario_critico(self):
        datos_todos = obtener_inventario_completo()
        # stock (idx 5) <= stock_minimo (idx 6)
        datos_criticos = [d for d in datos_todos if d[5] <= d[6]]
        
        if not datos_criticos:
            return messagebox.showinfo("Todo en Orden", "No se detectaron productos con stock crítico (bajo el mínimo).")
            
        nombre_archivo = ruta_salida(f"Inventario_Critico_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf")
        self._generar_pdf_inv_template("REPORTE DE INVENTARIO CRÍTICO (STOCK BAJO)", datos_criticos, nombre_archivo, colors.HexColor('#c0392b'))

    def _generar_pdf_inv_template(self, titulo, datos, nombre_archivo, color_header):
        doc = SimpleDocTemplate(nombre_archivo, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=40, bottomMargin=40)
        story = []
        styles = getSampleStyleSheet()
        
        story.append(Paragraph(f"<b>{EMPRESA_NOMBRE.upper()}</b>", styles['Heading1']))
        story.append(Paragraph(f"<b>{titulo}</b><br/>Fecha de Emisión: {datetime.now().strftime('%d/%m/%Y %H:%M')}<br/><br/>", styles['Normal']))
        
        tabla_datos = [["Código", "Producto", "Marca", "Costo", "Venta", "Stock", "Mín"]]
        for row in datos:
            tabla_datos.append([row[0], row[1][:30], row[2], f"$ {row[3]:,.2f}", f"$ {row[4]:,.2f}", row[5], row[6]])
            
        t = Table(tabla_datos, colWidths=[70, 160, 80, 60, 60, 60, 60])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), color_header),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            ('FONTSIZE', (0,0), (-1,-1), 9),
        ]))
        
        story.append(t)
        doc.build(story)
        abrir_archivo(nombre_archivo)

    def exportar_pdf_historico_pagos(self):
        datos = obtener_reporte_pdf_pagos_cxp()
        if not datos:
            return messagebox.showinfo("Reporte Vacío", "No se han registrado abonos o pagos en el histórico.")
        
        nombre_archivo = ruta_salida(f"Reporte_Historico_Pagos_CxP_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf")
        doc = SimpleDocTemplate(nombre_archivo, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
        story = []
        styles = getSampleStyleSheet()
        
        # Encabezado Corporativo
        story.append(Paragraph(f"<b>{EMPRESA_NOMBRE.upper()}</b>", styles['Heading1']))
        story.append(Paragraph(f"<b>HISTORIAL DE PAGOS Y AMORTIZACIONES A PROVEEDORES</b><br/>Fecha de Emisión: {datetime.now().strftime('%d/%m/%Y %H:%M')}<br/><br/>", styles['Normal']))
        
        tabla_datos = [["Fecha Pago", "Factura", "Proveedor", "Monto Pagado", "Método", "Referencia"]]
        total_pagado = 0
        for row in datos:
            tabla_datos.append([row[0], row[1], row[2][:25], f"$ {row[3]:,.2f}", row[4], row[5]])
            total_pagado += row[3]
            
        tabla_datos.append(["", "", "TOTAL AMORTIZADO:", f"$ {total_pagado:,.2f}", "", ""])
        
        t = Table(tabla_datos, colWidths=[75, 75, 140, 85, 80, 80])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#27ae60')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0,0), (-1,0), 6),
            ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor('#f2f2f2')),
            ('FONTNAME', (0,-1), (-1,-1), 'Helvetica-Bold'),
            ('GRID', (0,0), (-1,-2), 0.5, colors.grey),
        ]))
        
        story.append(t)
        doc.build(story)
        abrir_archivo(nombre_archivo)