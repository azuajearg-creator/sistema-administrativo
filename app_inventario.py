from config import EMPRESA_NOMBRE, EMPRESA_RIF, EMPRESA_CIUDAD, ruta_salida, abrir_archivo  # noqa: F401
import customtkinter as ctk
from tkinter import ttk, messagebox, filedialog
from base_datos import (obtener_productos, agregar_producto, 
                        actualizar_producto, eliminar_producto, 
                        cargar_productos_desde_excel)

class VentanaInventario(ctk.CTkToplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title(f"Gestión de Inventario - {EMPRESA_NOMBRE}")
        self.after(0, lambda: self.state('zoomed'))
        
        # --- CONFIGURACIÓN DE VENTANA ---
        self.focus_force()
        self.grab_set()
        
        self.codigo_seleccionado = None
        # Cargamos los productos para las búsquedas internas
        self.productos_db = obtener_productos()

        # --- BOTÓN REGRESAR ---
        self.btn_regresar = ctk.CTkButton(
            self, text="← VOLVER AL MENÚ", width=140, height=35,
            fg_color="#7f8c8d", hover_color="#95a5a6",
            font=("Arial", 12, "bold"), command=self.destroy
        )
        self.btn_regresar.place(x=20, y=20)

        ctk.CTkLabel(self, text="GESTIÓN DE INVENTARIO", font=("Arial", 28, "bold")).pack(pady=(40, 10))

        # --- FORMULARIO ---
        self.f_inputs = ctk.CTkFrame(self)
        self.f_inputs.pack(pady=10, padx=20, fill="x")
        self.f_inputs.columnconfigure((1, 3, 5), weight=1)

        # Fila 1
        ctk.CTkLabel(self.f_inputs, text="Código Técnico:").grid(row=0, column=0, padx=10, pady=10, sticky="e")
        self.ent_cod = ctk.CTkEntry(self.f_inputs)
        self.ent_cod.grid(row=0, column=1, padx=10, pady=10, sticky="ew")

        ctk.CTkLabel(self.f_inputs, text="Nombre Producto:").grid(row=0, column=2, padx=10, pady=10, sticky="e")
        self.ent_nom = ctk.CTkEntry(self.f_inputs)
        self.ent_nom.grid(row=0, column=3, padx=10, pady=10, sticky="ew")

        # Fila 2
        ctk.CTkLabel(self.f_inputs, text="Marca:").grid(row=1, column=0, padx=10, pady=10, sticky="e")
        self.ent_marca = ctk.CTkEntry(self.f_inputs)
        self.ent_marca.grid(row=1, column=1, padx=10, pady=10, sticky="ew")

        ctk.CTkLabel(self.f_inputs, text="Descripción:").grid(row=1, column=2, padx=10, pady=10, sticky="e")
        self.ent_desc = ctk.CTkEntry(self.f_inputs)
        self.ent_desc.grid(row=1, column=3, padx=10, pady=10, sticky="ew")

        # Fila 3
        ctk.CTkLabel(self.f_inputs, text="Costo $:").grid(row=2, column=0, padx=5, pady=10, sticky="e")
        self.ent_costo = ctk.CTkEntry(self.f_inputs, width=100)
        self.ent_costo.grid(row=2, column=1, padx=5, pady=10, sticky="w")

        ctk.CTkLabel(self.f_inputs, text="Venta $:").grid(row=2, column=2, padx=5, pady=10, sticky="e")
        self.ent_venta = ctk.CTkEntry(self.f_inputs, width=100)
        self.ent_venta.grid(row=2, column=3, padx=5, pady=10, sticky="w")

        ctk.CTkLabel(self.f_inputs, text="Stock Mín:").grid(row=2, column=4, padx=5, pady=10, sticky="e")
        self.ent_min = ctk.CTkEntry(self.f_inputs, width=100)
        self.ent_min.grid(row=2, column=5, padx=5, pady=10, sticky="w")

        ctk.CTkLabel(self.f_inputs, text="Stock:").grid(row=2, column=4, padx=5, pady=10, sticky="e")
        self.ent_stock = ctk.CTkEntry(self.f_inputs, width=80)
        self.ent_stock.grid(row=3, column=1, padx=5, pady=10, sticky="w")

        # --- PANEL DE BOTONES ---
        self.f_btns = ctk.CTkFrame(self, fg_color="transparent")
        self.f_btns.pack(pady=20)

        ctk.CTkButton(self.f_btns, text="💾 Guardar", fg_color="#27ae60", command=self.guardar).grid(row=0, column=0, padx=10)
        ctk.CTkButton(self.f_btns, text="🔄 Actualizar", fg_color="#2980b9", command=self.modificar).grid(row=0, column=1, padx=10)
        ctk.CTkButton(self.f_btns, text="🗑️ Eliminar", fg_color="#e74c3c", command=self.borrar).grid(row=0, column=2, padx=10)
        
        # BOTÓN DE IMPORTAR
        ctk.CTkButton(self.f_btns, text="📥 Importar Excel", fg_color="#16a085", command=self.ejecutar_carga_masiva).grid(row=0, column=3, padx=10)

        # --- TABLA ---
        self.f_tabla = ctk.CTkFrame(self)
        self.f_tabla.pack(pady=10, padx=20, fill="both", expand=True)

        cols = ("Código", "Nombre", "Marca", "Descripción", "Costo", "Venta", "Stock")
        self.tabla = ttk.Treeview(self.f_tabla, columns=cols, show="headings")
        for col in cols:
            self.tabla.heading(col, text=col)
            self.tabla.column(col, anchor="center", width=100)
        self.tabla.pack(side="left", fill="both", expand=True)
        
        scb = ttk.Scrollbar(self.f_tabla, orient="vertical", command=self.tabla.yview)
        self.tabla.configure(yscroll=scb.set)
        scb.pack(side="right", fill="y")

        self.tabla.bind("<<TreeviewSelect>>", self.cargar_seleccion)
        self.actualizar_tabla()

    def ejecutar_carga_masiva(self):
        ruta = filedialog.askopenfilename(
            title="Seleccionar Inventario",
            filetypes=[("Archivos Excel", "*.xlsx"), ("Archivos CSV", "*.csv")]
        )
        if ruta:
            resultado = cargar_productos_desde_excel(ruta)
            messagebox.showinfo("Resultado de Importación", resultado)
            self.actualizar_tabla()

    def actualizar_tabla(self):
        for i in self.tabla.get_children(): self.tabla.delete(i)
        self.productos_db = obtener_productos()
        for fila in self.productos_db: self.tabla.insert("", "end", values=fila)

    def cargar_seleccion(self, event):
        sel = self.tabla.selection()
        if sel:
            item = self.tabla.item(sel)['values']
            self.codigo_seleccionado = item[0]
            # Obtenemos el stock mínimo de la DB ya que el treeview no lo muestra todo
            # Para simplificar, asumimos el orden de la tabla: Cod, Nom, Marca, Desc, Costo, Venta, Stock
            entries = [self.ent_cod, self.ent_nom, self.ent_marca, self.ent_desc, self.ent_costo, self.ent_venta, self.ent_stock]
            for i, entry in enumerate(entries):
                entry.delete(0, "end")
                entry.insert(0, str(item[i]))

    def guardar(self):
        try:
            c, n, m, d = self.ent_cod.get(), self.ent_nom.get(), self.ent_marca.get(), self.ent_desc.get()
            co, v, s = float(self.ent_costo.get()), float(self.ent_venta.get()), int(self.ent_stock.get())
            sm = int(self.ent_min.get() or 5)
            
            if not c or not n:
                messagebox.showwarning("Atención", "Código y Nombre son obligatorios.")
                return
                
            agregar_producto(c, n, m, d, co, v, s, sm)
            messagebox.showinfo("Éxito", "Producto guardado correctamente.")
            self.limpiar_campos()
            self.actualizar_tabla()
        except ValueError:
            messagebox.showerror("Error", "Costo, Venta y Stock deben ser números.")

    def modificar(self):
        if not self.codigo_seleccionado:
            messagebox.showwarning("Atención", "Seleccione un producto de la tabla.")
            return
        try:
            c, n, m, d = self.ent_cod.get(), self.ent_nom.get(), self.ent_marca.get(), self.ent_desc.get()
            co, v, s = float(self.ent_costo.get()), float(self.ent_venta.get()), int(self.ent_stock.get())
            sm = int(self.ent_min.get() or 5)

            actualizar_producto(self.codigo_seleccionado, n, m, d, co, v, s, sm)
            messagebox.showinfo("Éxito", "Producto actualizado.")
            self.limpiar_campos()
            self.actualizar_tabla()
        except ValueError:
            messagebox.showerror("Error", "Verifique los valores numéricos.")

    def borrar(self):
        if not self.codigo_seleccionado:
            return
        if messagebox.askyesno("Confirmar", f"¿Eliminar el producto {self.codigo_seleccionado}?"):
            eliminar_producto(self.codigo_seleccionado)
            self.limpiar_campos()
            self.actualizar_tabla()

    def limpiar_campos(self):
        self.codigo_seleccionado = None
        for entry in [self.ent_cod, self.ent_nom, self.ent_marca, self.ent_desc, self.ent_costo, self.ent_venta, self.ent_stock, self.ent_min]:
            entry.delete(0, "end")