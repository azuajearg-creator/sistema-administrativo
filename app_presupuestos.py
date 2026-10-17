from config import EMPRESA_NOMBRE, EMPRESA_RIF, EMPRESA_CIUDAD, ruta_salida, abrir_archivo  # noqa: F401
import customtkinter as ctk
import os
from tkinter import messagebox
from base_datos import obtener_productos, obtener_datos_clientes, guardar_presupuesto
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph

class VentanaPresupuestos(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        
        # 1. ATRIBUTOS E INICIALIZACIÓN
        self.lista_items = [] 
        self.productos_db = obtener_productos()
        self.clientes_db = obtener_datos_clientes()

        # 2. CONFIGURACIÓN DE VENTANA
        self.title(f"Generador de Presupuestos - {EMPRESA_NOMBRE}")
        self.after(0, lambda: self.state('zoomed'))
        self.grab_set()

        self.configurar_interfaz()

    def configurar_interfaz(self):
        # --- BARRA SUPERIOR ---
        self.top_bar = ctk.CTkFrame(self, fg_color="transparent")
        self.top_bar.pack(fill="x", padx=20, pady=10)

        ctk.CTkButton(self.top_bar, text="← VOLVER AL MENÚ", command=self.destroy,
                      fg_color="#7f8c8d", width=150).pack(side="left")

        ctk.CTkLabel(self, text="Generación de Presupuestos", 
                      font=("Arial", 28, "bold"), text_color="#3498db").pack(pady=10)

        # --- FORMULARIO DE SELECCIÓN ---
        self.f_seleccion = ctk.CTkFrame(self)
        self.f_seleccion.pack(fill="x", padx=20, pady=10)

        # Cliente
        ctk.CTkLabel(self.f_seleccion, text="Cliente:", font=("Arial", 14, "bold")).grid(row=0, column=0, padx=10, pady=15)
        nombres_clientes = [c[1] for c in self.clientes_db] if self.clientes_db else ["No hay clientes"]
        self.combo_cliente = ctk.CTkComboBox(self.f_seleccion, values=nombres_clientes, width=400)
        self.combo_cliente.grid(row=0, column=1, padx=10, pady=15)

        # Validez
        ctk.CTkLabel(self.f_seleccion, text="Validez:", font=("Arial", 14)).grid(row=0, column=2, padx=10, pady=15)
        self.entry_validez = ctk.CTkEntry(self.f_seleccion, placeholder_text="Ej: 15 días")
        self.entry_validez.insert(0, "15 días")
        self.entry_validez.grid(row=0, column=3, padx=10, pady=15)

        # Producto
        ctk.CTkLabel(self.f_seleccion, text="Producto:", font=("Arial", 14, "bold")).grid(row=1, column=0, padx=10, pady=15)
        nombres_prod = [p[1] for p in self.productos_db] if self.productos_db else ["No hay productos"]
        self.combo_producto = ctk.CTkComboBox(self.f_seleccion, values=nombres_prod, width=400)
        self.combo_producto.grid(row=1, column=1, padx=10, pady=15)

        # Cantidad
        ctk.CTkLabel(self.f_seleccion, text="Cant:", font=("Arial", 14)).grid(row=1, column=2, padx=10, pady=15)
        self.entry_cant = ctk.CTkEntry(self.f_seleccion, width=80)
        self.entry_cant.grid(row=1, column=3, padx=10, pady=15)

        self.btn_añadir = ctk.CTkButton(self.f_seleccion, text="+ AÑADIR", command=self.añadir_item,
                                        fg_color="#2980b9", font=("Arial", 13, "bold"))
        self.btn_añadir.grid(row=1, column=4, padx=20, pady=15)

        # --- TABLA DE ITEMS ---
        self.f_tabla = ctk.CTkScrollableFrame(self, fg_color="#2b2b2b")
        self.f_tabla.pack(fill="both", expand=True, padx=20, pady=10)
        
        headers = ["Producto", "Precio Unit.", "Cantidad", "Subtotal"]
        for i, h in enumerate(headers):
            ctk.CTkLabel(self.f_tabla, text=h, font=("Arial", 13, "bold"), text_color="gray").grid(row=0, column=i, padx=40, pady=5)

        # --- PIE DE PÁGINA ---
        self.f_pie = ctk.CTkFrame(self, fg_color="transparent")
        self.f_pie.pack(fill="x", padx=20, pady=20)

        self.label_total = ctk.CTkLabel(self.f_pie, text="TOTAL: $ 0.00", font=("Arial", 22, "bold"), text_color="#27ae60")
        self.label_total.pack(side="left")

        self.btn_generar = ctk.CTkButton(self.f_pie, text="📄 GENERAR PRESUPUESTO PDF", command=self.finalizar_presupuesto,
                                         fg_color="#27ae60", height=45, font=("Arial", 14, "bold"))
        self.btn_generar.pack(side="right")

    def añadir_item(self):
        nombre_sel = self.combo_producto.get()
        cant_txt = self.entry_cant.get()

        if not cant_txt.isdigit() or int(cant_txt) <= 0:
            messagebox.showwarning("Error", "Ingrese una cantidad válida")
            return

        producto = next((p for p in self.productos_db if p[1] == nombre_sel), None)
        if producto:
            precio = producto[5] 
            cantidad = int(cant_txt)
            item = {"nombre": nombre_sel, "precio": precio, "cantidad": cantidad, "subtotal": precio * cantidad}
            self.lista_items.append(item)
            self.actualizar_tabla()
            self.entry_cant.delete(0, 'end')

    def actualizar_tabla(self):
        for widget in self.f_tabla.winfo_children():
            info = widget.grid_info()
            if info and int(info["row"]) > 0:
                widget.destroy()

        total = 0
        for i, item in enumerate(self.lista_items, start=1):
            ctk.CTkLabel(self.f_tabla, text=item["nombre"]).grid(row=i, column=0, pady=5, padx=10)
            ctk.CTkLabel(self.f_tabla, text=f"$ {item['precio']:.2f}").grid(row=i, column=1, pady=5, padx=10)
            ctk.CTkLabel(self.f_tabla, text=str(item["cantidad"])).grid(row=i, column=2, pady=5, padx=10)
            ctk.CTkLabel(self.f_tabla, text=f"$ {item['subtotal']:.2f}").grid(row=i, column=3, pady=5, padx=10)
            total += item["subtotal"]
        
        self.label_total.configure(text=f"TOTAL: $ {total:,.2f}")

    def finalizar_presupuesto(self):
        if not self.lista_items:
            messagebox.showwarning("Vacío", "No hay productos en el presupuesto")
            return
        
        cliente = self.combo_cliente.get()
        validez = self.entry_validez.get()
        total = sum(i["subtotal"] for i in self.lista_items)
        
        cliente_data = next((c for c in self.clientes_db if c[1] == cliente), None)
        rif = cliente_data[2] if cliente_data else ""

        try:
            # 1. Guardar en Base de Datos
            id_presu = guardar_presupuesto(cliente, rif, self.lista_items, total, validez)
            # 2. Generar el PDF pasándole los datos
            self.generar_pdf(cliente, rif, total, validez, id_presu)
            
            messagebox.showinfo("Éxito", f"Presupuesto #{id_presu} generado y guardado.")
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un error: {e}")

    def generar_pdf(self, cliente, rif, total, validez, id_presu):
        try:
            nombre_archivo = ruta_salida(f"Presupuesto_{id_presu}_{cliente.replace('.', '')[:15]}.pdf")
            ruta_absoluta = os.path.abspath(nombre_archivo)
            
            c = canvas.Canvas(ruta_absoluta, pagesize=letter)
            styles = getSampleStyleSheet()
            
            # Definir un estilo personalizado para el nombre del cliente
            estilo_cliente = styles["Normal"]
            estilo_cliente.fontName = "Helvetica"
            estilo_cliente.fontSize = 11
            estilo_cliente.leading = 14  # Espacio entre líneas si el nombre se divide

            # --- ENCABEZADO ---
            c.setFont("Helvetica-Bold", 16)
            c.drawString(50, 750, EMPRESA_NOMBRE.upper())
            c.setFont("Helvetica", 11)
            c.drawString(50, 735, f"RIF: {EMPRESA_RIF}")
            
            c.setFont("Helvetica-Bold", 14)
            c.drawString(50, 700, f"PRESUPUESTO N°: {id_presu}")
            c.drawRightString(550, 700, f"Validez: {validez}")

            # --- SECCIÓN CLIENTE CON SALTO DE LÍNEA ---
            c.setFont("Helvetica-Bold", 11)
            c.drawString(50, 675, "DATOS DEL CLIENTE:")
            
            p_nombre = Paragraph(f"<b>Nombre/Razón Social:</b> {cliente}", estilo_cliente)
            
            # wrap(ancho, alto)
            w, h = p_nombre.wrap(500, 100) 
            # Dibujamos el nombre. El 655 es nuestra base.
            p_nombre.drawOn(c, 50, 655 - h) 

            # --- LA CLAVE DEL ESPACIO ---
            # Si h es mayor a 14 (más de una línea), aumentamos la separación.
            # Agregamos 10 puntos de margen extra para que no se peguen.
            espacio_entre_lineas = 10 
            pos_y_rif = 655 - h - espacio_entre_lineas - 15 
            
            c.setFont("Helvetica", 11)
            c.drawString(50, pos_y_rif, f"RIF / CI: {rif}")
            
            # Ajustamos el inicio de la tabla para que también baje si el RIF bajó
            y_tabla = pos_y_rif - 30
            
            # --- TABLA DE PRODUCTOS ---
            c.line(50, y_tabla, 550, y_tabla)
            # ... (el resto del código de la tabla permanece igual)
            c.setFont("Helvetica-Bold", 10)
            c.drawString(50, y_tabla - 15, "PRODUCTO")
            c.drawString(300, y_tabla - 15, "CANT.")
            c.drawString(400, y_tabla - 15, "PRECIO UNIT.")
            c.drawString(500, y_tabla - 15, "SUBTOTAL")
            c.line(50, y_tabla - 20, 550, y_tabla - 20)

            y = y_tabla - 35
            c.setFont("Helvetica", 10)
            for item in self.lista_items:
                c.drawString(50, y, item["nombre"][:45])
                c.drawString(300, y, str(item["cantidad"]))
                c.drawString(400, y, f"$ {item['precio']:,.2f}")
                c.drawString(500, y, f"$ {item['subtotal']:,.2f}")
                y -= 20
            
            c.line(50, y, 550, y)
            c.setFont("Helvetica-Bold", 12)
            c.drawRightString(550, y - 25, f"TOTAL A PAGAR: $ {total:,.2f}")
            
            c.save()
            if os.path.exists(ruta_absoluta):
                abrir_archivo(ruta_absoluta)
        except Exception as e:
            raise Exception(f"Error al ajustar margen del cliente: {e}")