from config import EMPRESA_NOMBRE, EMPRESA_RIF, EMPRESA_CIUDAD, ruta_salida, abrir_archivo  # noqa: F401
import customtkinter as ctk
from tkinter import ttk, messagebox
from datetime import datetime
from base_datos import (obtener_proveedores, obtener_productos, 
                        registrar_factura_compra_con_stock, 
                        obtener_cxp_pendientes, registrar_pago_cxp)

class VentanaCxP(ctk.CTkToplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title(f"Cuentas por Pagar e Ingreso de Stock - {EMPRESA_NOMBRE}")
        self.after(0, lambda: self.state('zoomed'))
        
        # --- CONFIGURACIÓN DE VENTANA MODAL MAXIMIZADA ---
        self.focus_force()
        self.grab_set() 
        
        self.carrito_compra = [] # Almacena temporalmente los productos a ingresar por factura
        self.prov_dict = {}
        self.prod_dict = {}

        # --- BOTÓN REGRESAR ---
        self.btn_regresar = ctk.CTkButton(self, text="← VOLVER AL MENÚ", width=140, height=35,
                                           fg_color="#7f8c8d", hover_color="#95a5a6",
                                           font=("Arial", 12, "bold"), command=self.destroy)
        self.btn_regresar.place(x=20, y=20)

        ctk.CTkLabel(self, text="MÓDULO DE CUENTAS POR PAGAR (CxP)", font=("Arial", 24, "bold")).pack(pady=(40, 10))

        # --- SISTEMA DE PESTAÑAS ---
        self.tabview = ctk.CTkTabview(self, segmented_button_selected_color="#d35400", segmented_button_selected_hover_color="#e67e22")
        self.tabview.pack(pady=10, padx=20, fill="both", expand=True)

        self.tab_registro = self.tabview.add("📝 REGISTRAR COMPRA / FACTURA")
        self.tab_control = self.tabview.add("💰 CONTROL DE DEUDAS Y ABONOS")

        self.setup_tab_registro()
        self.setup_tab_control()
        self.cargar_datos_iniciales()

    # =========================================================================
    # PESTAÑA 1: REGISTRO DE FACTURAS E INGRESO DE STOCK
    # =========================================================================
    def setup_tab_registro(self):
        # Frame de Datos de Factura
        frame_factura = ctk.CTkFrame(self.tab_registro)
        frame_factura.pack(pady=10, padx=10, fill="x")

        ctk.CTkLabel(frame_factura, text="Proveedor:", font=("Arial", 12, "bold")).grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.combo_proveedor = ctk.CTkComboBox(frame_factura, width=250, values=[])
        self.combo_proveedor.grid(row=0, column=1, padx=10, pady=10)

        ctk.CTkLabel(frame_factura, text="Nro Factura:", font=("Arial", 12, "bold")).grid(row=0, column=2, padx=10, pady=10, sticky="w")
        self.ent_nro_factura = ctk.CTkEntry(frame_factura, width=150)
        self.ent_nro_factura.grid(row=0, column=3, padx=10, pady=10)

        ctk.CTkLabel(frame_factura, text="F. Vencimiento (AAAA-MM-DD):", font=("Arial", 12, "bold")).grid(row=0, column=4, padx=10, pady=10, sticky="w")
        self.ent_vencimiento = ctk.CTkEntry(frame_factura, width=120)
        self.ent_vencimiento.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.ent_vencimiento.grid(row=0, column=5, padx=10, pady=10)

        # Frame de Carga de Ítems
        frame_items = ctk.CTkFrame(self.tab_registro)
        frame_items.pack(pady=5, padx=10, fill="x")

        ctk.CTkLabel(frame_items, text="Producto:", font=("Arial", 12, "bold")).grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.combo_producto = ctk.CTkComboBox(frame_items, width=300, values=[])
        self.combo_producto.grid(row=0, column=1, padx=10, pady=10)

        ctk.CTkLabel(frame_items, text="Costo Unit ($):", font=("Arial", 12, "bold")).grid(row=0, column=2, padx=10, pady=10, sticky="w")
        self.ent_costo_prod = ctk.CTkEntry(frame_items, width=100)
        self.ent_costo_prod.grid(row=0, column=3, padx=10, pady=10)

        ctk.CTkLabel(frame_items, text="Cant:", font=("Arial", 12, "bold")).grid(row=0, column=4, padx=10, pady=10, sticky="w")
        self.ent_cantidad_prod = ctk.CTkEntry(frame_items, width=80)
        self.ent_cantidad_prod.insert(0, "1")
        self.ent_cantidad_prod.grid(row=0, column=5, padx=10, pady=10)

        self.btn_agregar_item = ctk.CTkButton(frame_items, text="+ AÑADIR", fg_color="#27ae60", command=self.agregar_item_al_carrito)
        self.btn_agregar_item.grid(row=0, column=6, padx=20, pady=10)

        # Tabla del Carrito Temporal
        frame_tabla = ctk.CTkFrame(self.tab_registro)
        frame_tabla.pack(pady=10, padx=10, fill="both", expand=True)

        columnas_car = ("CÓDIGO", "PRODUCTO", "COSTO UNIT.", "CANTIDAD", "SUBTOTAL")
        self.tabla_carrito = ttk.Treeview(frame_tabla, columns=columnas_car, show="headings")
        for col in columnas_car:
            self.tabla_carrito.heading(col, text=col)
            self.tabla_carrito.column(col, anchor="center")
        self.tabla_carrito.pack(side="left", fill="both", expand=True)
        
        scroll = ttk.Scrollbar(frame_tabla, orient="vertical", command=self.tabla_carrito.yview)
        self.tabla_carrito.configure(yscroll=scroll.set)
        scroll.pack(side="right", fill="y")

        # Cierre e Importes netos
        frame_totales = ctk.CTkFrame(self.tab_registro)
        frame_totales.pack(pady=10, padx=10, fill="x")

        ctk.CTkLabel(frame_totales, text="Monto Total Factura ($):", font=("Arial", 14, "bold")).grid(row=0, column=0, padx=10, pady=10)
        self.ent_monto_total = ctk.CTkEntry(frame_totales, width=150, font=("Arial", 14, "bold"))
        self.ent_monto_total.grid(row=0, column=1, padx=10, pady=10)

        self.btn_guardar_compra = ctk.CTkButton(frame_totales, text="💾 PROCESAR E INGRESAR COMPRA", 
                                                fg_color="#d35400", font=("Arial", 12, "bold"),
                                                height=40, command=self.guardar_compra_completa)
        self.btn_guardar_compra.grid(row=0, column=2, padx=40, pady=10)

    def agregar_item_al_carrito(self):
        prod_sel = self.combo_producto.get()
        cant = self.ent_cantidad_prod.get()
        costo = self.ent_costo_prod.get()
        if prod_sel not in self.prod_dict or not cant.isdigit() or not costo:
            return messagebox.showwarning("Aviso", "Verifique el producto, el costo y la cantidad.")
        
        codigo = self.prod_dict[prod_sel]
        subtotal_item = float(costo) * int(cant)
        self.carrito_compra.append({'codigo': codigo, 'nombre': prod_sel, 'cantidad': int(cant), 'costo': float(costo)})
        self.tabla_carrito.insert("", "end", values=(codigo, prod_sel, f"$ {float(costo):,.2f}", cant, f"$ {subtotal_item:,.2f}"))
        
        self.ent_costo_prod.delete(0, "end")
        self.ent_cantidad_prod.delete(0, "end")
        self.ent_cantidad_prod.insert(0, "1")

    def guardar_compra_completa(self):
        prov_sel = self.combo_proveedor.get()
        nro_f = self.ent_nro_factura.get().strip()
        venc = self.ent_vencimiento.get().strip()
        total_str = self.ent_monto_total.get().strip()

        if prov_sel not in self.prov_dict or not nro_f or not total_str or not self.carrito_compra:
            return messagebox.showwarning("Atención", "Complete los campos obligatorios (Proveedor, Nro Factura, Total) y añada al menos 1 producto.")
        
        try:
            total = float(total_str)
            subtotal = total / 1.16
            iva = total - subtotal
            id_prov = self.prov_dict[prov_sel]
            f_emision = datetime.now().strftime("%Y-%m-%d")

            # Ejecutamos la transacción atómica
            registrar_factura_compra_con_stock(nro_f, id_prov, f_emision, venc, round(subtotal,2), round(iva,2), total, "Ingreso CxP", self.carrito_compra)
            
            messagebox.showinfo("Éxito", f"Factura {nro_f} registrada.\nInventario actualizado y cuenta por pagar generada con éxito.")
            
            # Limpiar campos
            self.ent_nro_factura.delete(0, "end")
            self.ent_monto_total.delete(0, "end")
            self.ent_costo_prod.delete(0, "end")
            self.carrito_compra.clear()
            for i in self.tabla_carrito.get_children(): self.tabla_carrito.delete(i)
            self.actualizar_tabla_deudas()

        except ValueError:
            messagebox.showerror("Error", "El monto total de la factura debe ser un número decimal válido.")
        except Exception as e:
            messagebox.showerror("Error Crítico", f"No se pudo guardar la compra: {e}")

    # =========================================================================
    # PESTAÑA 2: CONTROL DE DEUDAS Y ABONOS (AMORTIZACIÓN)
    # =========================================================================
    def setup_tab_control(self):
        frame_top = ctk.CTkFrame(self.tab_control)
        frame_top.pack(pady=10, padx=10, fill="x")
        
        ctk.CTkLabel(frame_top, text="Doble clic sobre una deuda para registrar un pago o abono financiero:", font=("Arial", 12, "italic", "bold"), text_color="#34495e").pack(side="left", padx=10, pady=5)

        frame_tabla = ctk.CTkFrame(self.tab_control)
        frame_tabla.pack(pady=5, padx=10, fill="both", expand=True)

        columnas = ("ID", "NRO FACTURA", "PROVEEDOR", "EMISIÓN", "VENCIMIENTO", "TOTAL FACTURA", "SALDO PENDIENTE", "ESTADO")
        self.tabla_deudas = ttk.Treeview(frame_tabla, columns=columnas, show="headings")
        for col in columnas:
            self.tabla_deudas.heading(col, text=col)
            self.tabla_deudas.column(col, anchor="center", width=110)
        self.tabla_deudas.column("PROVEEDOR", width=200) # Más espacio para el nombre comercial
        self.tabla_deudas.pack(side="left", fill="both", expand=True)

        scroll = ttk.Scrollbar(frame_tabla, orient="vertical", command=self.tabla_deudas.yview)
        self.tabla_deudas.configure(yscroll=scroll.set)
        scroll.pack(side="right", fill="y")
        
        self.tabla_deudas.bind("<Double-1>", self.abrir_ventana_abono)

    def abrir_ventana_abono(self, event):
        seleccion = self.tabla_deudas.selection()
        if not seleccion: return
        
        valores = self.tabla_deudas.item(seleccion, "values")
        id_factura = valores[0]
        nro_fact = valores[1]
        
        # --- SOLUCCIÓN AL RESTRIPEO DE CARACTERES MONETARIOS ---
        saldo_texto = valores[6].replace("$", "").replace(",", "").strip()
        saldo_actual = float(saldo_texto)

        # Crear una subventana modal pequeña para capturar el pago
        modal = ctk.CTkToplevel(self)
        modal.title(f"Registrar Pago - Factura #{nro_fact}")
        modal.geometry("400x350")
        modal.resizable(False, False)
        # Asegurar que se sitúe por encima de la pantalla maximizada
        modal.transient(self)
        modal.focus_force()
        modal.grab_set()

        ctk.CTkLabel(modal, text=f"Abonar a Factura Nro: {nro_fact}", font=("Arial", 14, "bold")).pack(pady=10)
        ctk.CTkLabel(modal, text=f"Saldo Pendiente Actual: $ {saldo_actual:,.2f}", text_color="#c0392b", font=("Arial", 12, "bold")).pack(pady=5)

        ctk.CTkLabel(modal, text="Monto a Pagar ($):").pack()
        ent_monto = ctk.CTkEntry(modal, width=200)
        ent_monto.insert(0, str(saldo_actual))
        ent_monto.pack(pady=5)

        ctk.CTkLabel(modal, text="Método de Pago:").pack()
        combo_metodo = ctk.CTkComboBox(modal, width=200, values=["TRANSFERENCIA", "EFECTIVO", "DIVISAS"])
        combo_metodo.pack(pady=5)

        ctk.CTkLabel(modal, text="Referencia / Soporte:").pack()
        ent_ref = ctk.CTkEntry(modal, width=200)
        ent_ref.pack(pady=5)

        def ejecutar_transaccion_pago():
            monto_str = ent_monto.get().strip()
            metodo = combo_metodo.get()
            referencia = ent_ref.get().strip()
            
            try:
                monto = float(monto_str)
                if monto <= 0 or monto > saldo_actual:
                    return messagebox.showwarning("Monto Incorrecto", f"El monto a abonar debe ser mayor a 0 y no puede exceder el saldo residual de la deuda ($ {saldo_actual}).")
                
                fecha_hoy = datetime.now().strftime("%Y-%m-%d")
                registrar_pago_cxp(id_factura, fecha_hoy, monto, metodo, referencia)
                
                messagebox.showinfo("Éxito", "El pago fue amortizado correctamente en la cuenta corriente del proveedor.")
                modal.destroy()
                self.actualizar_tabla_deudas()
            except ValueError:
                messagebox.showerror("Error", "Ingrese un valor de pago numérico válido.")

        ctk.CTkButton(modal, text="🤝 CONFIRMAR ABONO", fg_color="#27ae60", font=("Arial", 12, "bold"), command=ejecutar_transaccion_pago).pack(pady=20)

    # =========================================================================
    # LOGICA DE CARGA Y REFRESCO
    # =========================================================================
    def cargar_datos_iniciales(self):
        # Poblar Proveedores
        proveedores = obtener_proveedores()
        if proveedores:
            self.prov_dict = {f"{p[1]} (RIF: {p[2]})": p[0] for p in proveedores}
            self.combo_proveedor.configure(values=list(self.prov_dict.keys()))
            if list(self.prov_dict.keys()):
                self.combo_proveedor.set(list(self.prov_dict.keys())[0])

        # Poblar Productos
        productos = obtener_productos()
        if productos:
            self.prod_dict = {f"{p[1]} [{p[2]}]": p[0] for p in productos}
            self.combo_producto.configure(values=list(self.prod_dict.keys()))
            if list(self.prod_dict.keys()):
                self.combo_producto.set(list(self.prod_dict.keys())[0])

        self.actualizar_tabla_deudas()

    def actualizar_tabla_deudas(self):
        for i in self.tabla_deudas.get_children(): self.tabla_deudas.delete(i)
        deudas = obtener_cxp_pendientes()
        if deudas:
            for d in deudas:
                # Formatear montos para despliegue visual limpio
                d_lista = list(d)
                d_lista[5] = f"$ {float(d[5]):,.2f}"
                d_lista[6] = f"$ {float(d[6]):,.2f}"
                self.tabla_deudas.insert("", "end", values=d_lista)