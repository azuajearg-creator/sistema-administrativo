from config import EMPRESA_NOMBRE, EMPRESA_RIF, EMPRESA_CIUDAD, ruta_salida, abrir_archivo  # noqa: F401
import customtkinter as ctk
from tkinter import messagebox, ttk
from base_datos import (registrar_venta, guardar_factura, 
                        obtener_datos_clientes, obtener_productos, 
                        obtener_info_producto_por_nombre,
                        obtener_nota_por_numero, marcar_nota_como_facturada)
from documentos import generar_pdf_factura
import datetime
import os

class VentanaFacturacion(ctk.CTkToplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title(f"Facturación Forma Libre - {EMPRESA_NOMBRE}")
        self.after(0, lambda: self.state('zoomed'))
        self.grab_set()

        self.carrito = [] 
        self.cliente_completo = {}
        self.nro_nota_asociada = None

        self.btn_regresar = ctk.CTkButton(self, text="← VOLVER", fg_color="#7f8c8d", command=self.destroy)
        self.btn_regresar.place(x=20, y=20)

        ctk.CTkLabel(self, text="FACTURACIÓN FORMA LIBRE", font=("Arial", 26, "bold")).pack(pady=(40, 10))

        # --- SECCIÓN SUPERIOR: VINCULACIÓN Y NRO FACTURA ---
        self.frame_top_bar = ctk.CTkFrame(self, fg_color="#2c3e50")
        self.frame_top_bar.pack(pady=10, padx=50, fill="x")
        
        ctk.CTkLabel(self.frame_top_bar, text="Nota de Entrega #:", text_color="white").grid(row=0, column=0, padx=10, pady=10)
        self.ent_busqueda_nota = ctk.CTkEntry(self.frame_top_bar, width=150)
        self.ent_busqueda_nota.grid(row=0, column=1, padx=5)
        
        self.btn_vincular = ctk.CTkButton(self.frame_top_bar, text="VINCULAR", fg_color="#16a085", width=100, command=self.cargar_desde_nota)
        self.btn_vincular.grid(row=0, column=2, padx=5)

        ctk.CTkLabel(self.frame_top_bar, text="|   NRO FACTURA (FORMA LIBRE):", text_color="white", font=("Arial", 12, "bold")).grid(row=0, column=3, padx=(30, 10))
        self.ent_nro_factura = ctk.CTkEntry(self.frame_top_bar, width=150, border_color="#e74c3c", fg_color="#fdf2f2", text_color="black")
        self.ent_nro_factura.grid(row=0, column=4, padx=10)

        # --- FRAME DATOS CLIENTE Y PRODUCTO ---
        self.frame_inputs = ctk.CTkFrame(self)
        self.frame_inputs.pack(pady=10, padx=50, fill="x")

        # Cliente
        ctk.CTkLabel(self.frame_inputs, text="Cliente:").grid(row=0, column=0, padx=10, pady=10)
        self.lista_clientes_db = obtener_datos_clientes()
        nombres_clientes = [c[1] for c in self.lista_clientes_db]
        self.combo_clientes = ctk.CTkComboBox(self.frame_inputs, values=nombres_clientes, width=250, command=self.seleccionar_cliente)
        self.combo_clientes.set("Seleccionar Cliente")
        self.combo_clientes.grid(row=0, column=1, padx=10)

        ctk.CTkLabel(self.frame_inputs, text="Desc (%):").grid(row=0, column=2, padx=5)
        self.ent_porc_desc = ctk.CTkEntry(self.frame_inputs, width=60)
        self.ent_porc_desc.insert(0, "0")
        self.ent_porc_desc.grid(row=0, column=3, padx=5)
        self.ent_porc_desc.bind("<KeyRelease>", lambda e: self.actualizar_calculos())

        # Producto
        ctk.CTkLabel(self.frame_inputs, text="Producto:").grid(row=1, column=0, padx=10, pady=10)
        lista_p = [p[1] for p in obtener_productos()]
        self.combo_prods = ctk.CTkComboBox(self.frame_inputs, values=lista_p, width=250, command=self.autocompletar_prod)
        self.combo_prods.set("Seleccionar Producto")
        self.combo_prods.grid(row=1, column=1, padx=10)

        ctk.CTkLabel(self.frame_inputs, text="Precio $:").grid(row=1, column=2, padx=5)
        self.ent_precio = ctk.CTkEntry(self.frame_inputs, width=80)
        self.ent_precio.grid(row=1, column=3, padx=5)

        ctk.CTkLabel(self.frame_inputs, text="Cant:").grid(row=1, column=4, padx=5)
        self.ent_cant = ctk.CTkEntry(self.frame_inputs, width=60)
        self.ent_cant.grid(row=1, column=5, padx=5)

        self.btn_agregar = ctk.CTkButton(self.frame_inputs, text="➕ AÑADIR", fg_color="#3498db", command=self.agregar_item)
        self.btn_agregar.grid(row=1, column=6, padx=10)

        # --- TABLA Y TOTALES ---
        self.f_tabla = ctk.CTkFrame(self)
        self.f_tabla.pack(pady=10, padx=50, fill="both", expand=True)

        cols = ("ITEM", "DESCRIPCIÓN", "P. UNIT", "CANT", "SUBTOTAL")
        self.tabla = ttk.Treeview(self.f_tabla, columns=cols, show="headings")
        for col in cols: 
            self.tabla.heading(col, text=col)
            self.tabla.column(col, anchor="center")
        self.tabla.pack(fill="both", expand=True)

        self.lbl_total = ctk.CTkLabel(self, text="TOTAL A PAGAR: $0.00", font=("Arial", 28, "bold"), text_color="#2ecc71")
        self.lbl_total.pack(pady=10)

        self.btn_finalizar = ctk.CTkButton(self, text="📄 GENERAR FACTURA PDF", 
                                          fg_color="#2980b9", height=50, width=400,
                                          font=("Arial", 18, "bold"), command=self.finalizar)
        self.btn_finalizar.pack(pady=(10, 20))

    def seleccionar_cliente(self, nombre):
        for c in self.lista_clientes_db:
            if c[1] == nombre:
                self.cliente_completo = {
                    "id": c[0], "nombre": c[1], "rif": c[2], "direccion": c[3], "telefono": c[4]
                }
                break

    def cargar_desde_nota(self):
        nro = self.ent_busqueda_nota.get().strip()
        datos = obtener_nota_por_numero(nro)
        if datos:
            self.nro_nota_asociada = nro
            self.combo_clientes.set(datos['cliente'])
            self.seleccionar_cliente(datos['cliente'])
            self.carrito = []
            for item in datos['items']:
                info = obtener_info_producto_por_nombre(item['nombre'])
                p_unit = info[1] if info else 0.0
                self.carrito.append({"nombre": item['nombre'], "precio": p_unit, "cantidad": item['cantidad'], "subtotal": p_unit * item['cantidad']})
            self.redibujar_tabla()
            self.actualizar_calculos()
        else:
            messagebox.showerror("Error", "Nota no encontrada.")

    def autocompletar_prod(self, nombre):
        res = obtener_info_producto_por_nombre(nombre)
        if res:
            self.ent_precio.delete(0, "end")
            self.ent_precio.insert(0, str(res[1]))

    def agregar_item(self):
        try:
            nombre = self.combo_prods.get()
            pre = float(self.ent_precio.get())
            can = int(self.ent_cant.get())
            self.carrito.append({"nombre": nombre, "precio": pre, "cantidad": can, "subtotal": pre * can})
            self.redibujar_tabla()
            self.actualizar_calculos()
        except Exception: pass

    def redibujar_tabla(self):
        for r in self.tabla.get_children(): self.tabla.delete(r)
        for i, item in enumerate(self.carrito, 1):
            self.tabla.insert("", "end", values=(i, item['nombre'], f"{item['precio']:.2f}", item['cantidad'], f"{item['subtotal']:.2f}"))

    def actualizar_calculos(self):
        sub = sum(i['subtotal'] for i in self.carrito)
        try: desc_p = float(self.ent_porc_desc.get() or 0)
        except ValueError: desc_p = 0
        m_desc = sub * (desc_p / 100)
        iva = (sub - m_desc) * 0.16
        total = (sub - m_desc) + iva
        self.lbl_total.configure(text=f"TOTAL A PAGAR: ${total:.2f}")
        return desc_p, m_desc, sub, iva, total

    def finalizar(self):
        nro_f = self.ent_nro_factura.get().strip()
        if not nro_f:
            messagebox.showwarning("Atención", "Debe ingresar el número de factura manual.")
            return
        
        if not self.cliente_completo or not self.carrito:
            messagebox.showwarning("Atención", "Seleccione un cliente y añada productos.")
            return

        try:
            p, md, s, iva, tot = self.actualizar_calculos()
            guardar_factura(self.cliente_completo['nombre'], tot)
            
            if self.nro_nota_asociada:
                marcar_nota_como_facturada(self.nro_nota_asociada)
            
            archivo = generar_pdf_factura(self.cliente_completo, self.carrito, p, md, s, iva, tot, nro_f)
            messagebox.showinfo("Éxito", f"Factura {nro_f} generada exitosamente.")
            abrir_archivo(archivo)
            self.destroy()
        except Exception as e: messagebox.showerror("Error", str(e))

if __name__ == "__main__":
    root = ctk.CTk(); VentanaFacturacion(root); root.mainloop()