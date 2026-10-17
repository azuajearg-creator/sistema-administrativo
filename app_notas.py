from config import EMPRESA_NOMBRE, EMPRESA_RIF, EMPRESA_CIUDAD, ruta_salida, abrir_archivo  # noqa: F401
import customtkinter as ctk
from tkinter import messagebox, ttk
from base_datos import (obtener_datos_clientes, obtener_productos, 
                        obtener_info_producto_por_nombre, registrar_venta,
                        guardar_nota_entrega, obtener_todas_las_notas) # Se agregó la nueva función
from weasyprint import HTML
import datetime
import os

# --- 1. FUNCIÓN PARA GENERAR EL PDF CON DISEÑO CORREGIDO ---
def generar_pdf_nota(cliente_datos, direccion_cliente, items, observaciones, nro_nota):
    # Formato de fecha solo día/mes/año
    fecha_hoy = datetime.datetime.now().strftime("%d/%m/%Y")
    
    estilos = """
    <style>
        @page { size: letter; margin: 15mm; }
        html, body { height: 100%; margin: 0; padding: 0; }
        body { font-family: 'Arial', sans-serif; color: #333; line-height: 1.4; position: relative; }
        
        .header-container { border-bottom: 2px solid #2980b9; padding-bottom: 10px; text-align: center; }
        .header-text { width: 100%; }
        .header-text h1 { margin: 0; color: #2980b9; font-size: 22px; }
        .header-text p { margin: 1px 0; font-size: 10px; }
        
        .info-seccion { margin: 15px 0; }
        .info-table { width: 100%; border: none; }
        .info-table td { border: none; padding: 2px; text-align: left; vertical-align: top; font-size: 11px; }
        
        .tabla-productos { width: 100%; border-collapse: collapse; margin-top: 10px; }
        .tabla-productos th { background-color: #2980b9; color: white; padding: 8px; font-size: 11px; border: 1px solid #2980b9; }
        .tabla-productos td { border: 1px solid #ddd; padding: 6px; text-align: center; font-size: 10px; }
        
        .obs-container { margin-top: 15px; }
        .obs-cuadro { border: 1px solid #eee; padding: 8px; margin-top: 5px; min-height: 40px; font-size: 10px; color: #444; background-color: #f9f9f9; }
        
        .firma-box { position: absolute; bottom: 10px; width: 100%; border: none; }
        .linea-firma { border-top: 1px solid #333; padding-top: 8px; font-size: 10px; text-align: center; }
    </style>
    """

    filas_tabla = ""
    for i, it in enumerate(items, 1):
        filas_tabla += f"<tr><td>{i}</td><td style='text-align: left;'>{it['nombre']}</td><td>{it['cantidad']}</td></tr>"

    html_content = f"""
    <html>
    <head>{estilos}</head>
    <body>
        <div class="header-container">
            <div class="header-text">
                <h1>{EMPRESA_NOMBRE.upper()}</h1>
                <p><strong>RIF:</strong> {EMPRESA_RIF}</p>
                <p>{EMPRESA_CIUDAD}</p>
            </div>
        </div>
        <div class="info-seccion">
            <table class="info-table">
                <tr>
                    <td style="width: 65%;">
                        <strong>CLIENTE:</strong> {cliente_datos}<br>
                        <strong>DIRECCIÓN:</strong> {direccion_cliente}
                    </td>
                    <td style="width: 35%; text-align: right;">
                        <strong>NOTA DE ENTREGA:</strong> <span style="color: #c0392b;"># {nro_nota}</span><br>
                        <strong>FECHA:</strong> {fecha_hoy}
                    </td>
                </tr>
            </table>
        </div>
        <table class="tabla-productos">
            <thead><tr><th style="width: 10%;">ITEM</th><th style="width: 70%;">DESCRIPCIÓN DEL INSUMO / SERVICIO</th><th style="width: 20%;">CANTIDAD</th></tr></thead>
            <tbody>{filas_tabla}</tbody>
        </table>
        <div class="obs-container">
            <strong>OBSERVACIONES Y CONDICIONES:</strong>
            <div class="obs-cuadro">{observaciones if observaciones else 'Sin observaciones adicionales.'}</div>
        </div>
        <table class="firma-box">
            <tr>
                <td style="width: 40%;" class="linea-firma"><strong>Por {EMPRESA_NOMBRE}</strong><br>Firma y Sello Autorizado</td>
                <td style="width: 20%; border: none;"></td>
                <td style="width: 40%;" class="linea-firma"><strong>Recibido por el Cliente</strong><br>Nombre / C.I. / Fecha</td>
            </tr>
        </table>
    </body>
    </html>"""
    
    nombre_archivo = ruta_salida(f"Nota_{nro_nota}.pdf")
    HTML(string=html_content, base_url=".").write_pdf(nombre_archivo)
    return nombre_archivo

# --- 2. INTERFAZ ---
class VentanaNotas(ctk.CTkToplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title(f"Sistema de Notas - {EMPRESA_NOMBRE}")
        self.after(0, lambda: self.state('zoomed'))
        self.grab_set()

        self.datos_clientes = obtener_datos_clientes()
        self.nombres_cli = [c[1] for c in self.datos_clientes]
        self.items_nota = []
        self.codigo_actual = None
        self.nombre_actual = None

        # --- BOTÓN REGRESAR ---
        self.btn_regresar = ctk.CTkButton(self, text="← VOLVER AL MENÚ", width=140, height=35,
                                           fg_color="#7f8c8d", hover_color="#95a5a6",
                                           font=("Arial", 12, "bold"), command=self.destroy)
        self.btn_regresar.place(x=20, y=20)

        ctk.CTkLabel(self, text="MÓDULO DE NOTAS DE ENTREGA", font=("Arial", 24, "bold")).pack(pady=(40, 10))

        # --- SISTEMA DE PESTAÑAS ---
        self.tabview = ctk.CTkTabview(self, segmented_button_selected_color="#2980b9", segmented_button_selected_hover_color="#3498db")
        self.tabview.pack(pady=10, padx=20, fill="both", expand=True)

        self.tab_crear = self.tabview.add("📝 CREAR NUEVA NOTA")
        self.tab_historial = self.tabview.add("📑 HISTORIAL DE NOTAS")

        self.setup_tab_crear_nota()
        self.setup_tab_historial()
        self.actualizar_tabla_historial_notas() # Cargar datos al iniciar

    # =========================================================================
    # PESTAÑA 1: CREAR NUEVA NOTA
    # =========================================================================
    def setup_tab_crear_nota(self):
        self.frame_top = ctk.CTkFrame(self.tab_crear)
        self.frame_top.pack(pady=10, padx=50, fill="x")

        # Selección de Cliente
        ctk.CTkLabel(self.frame_top, text="Cliente:").grid(row=0, column=0, padx=10, pady=5)
        self.combo_clientes = ctk.CTkComboBox(self.frame_top, values=self.nombres_cli, width=350, command=self.cargar_datos_auto)
        self.combo_clientes.set("Seleccionar Cliente")
        self.combo_clientes.grid(row=0, column=1, padx=10, pady=5)
    
        # Campo Dirección
        ctk.CTkLabel(self.frame_top, text="Dirección:").grid(row=1, column=0, padx=10, pady=5)
        self.ent_direccion = ctk.CTkEntry(self.frame_top, width=350)
        self.ent_direccion.grid(row=1, column=1, padx=10, pady=5)
    
        # Insumo y Cantidad
        ctk.CTkLabel(self.frame_top, text="Insumo:").grid(row=2, column=0, padx=10, pady=5)
        prods = [p[1] for p in obtener_productos()]
        self.combo_prods = ctk.CTkComboBox(self.frame_top, values=prods, width=350, command=self.autocompletar_p)
        self.combo_prods.set("Seleccionar Producto")
        self.combo_prods.grid(row=2, column=1, padx=10, pady=5)
    
        ctk.CTkLabel(self.frame_top, text="Cant:").grid(row=2, column=2, padx=5)
        self.ent_cant = ctk.CTkEntry(self.frame_top, width=70)
        self.ent_cant.grid(row=2, column=3, padx=5)
    
        ctk.CTkButton(self.frame_top, text="➕ AÑADIR", command=self.agregar_item).grid(row=2, column=4, padx=10)
    
        # Tabla
        self.f_tabla = ctk.CTkFrame(self.tab_crear)
        self.f_tabla.pack(pady=10, padx=50, fill="both", expand=True)
        self.tabla = ttk.Treeview(self.f_tabla, columns=("IT", "Desc", "Cant"), show="headings")
        self.tabla.heading("IT", text="ITEM"); self.tabla.heading("Desc", text="DESCRIPCIÓN"); self.tabla.heading("Cant", text="CANT")
        self.tabla.column("IT", width=50); self.tabla.column("Cant", width=80)
        self.tabla.pack(fill="both", expand=True)
    
        self.txt_obs = ctk.CTkTextbox(self.tab_crear, height=70, width=600)
        self.txt_obs.pack(pady=10)
    
        ctk.CTkButton(self.tab_crear, text="📄 GENERAR NOTA", fg_color="#2980b9", height=45, command=self.finalizar_nota).pack(pady=20)

    # =========================================================================
    # PESTAÑA 2: HISTORIAL DE NOTAS
    # =========================================================================
    def setup_tab_historial(self):
        frame_botones = ctk.CTkFrame(self.tab_historial)
        frame_botones.pack(pady=10, padx=10, fill="x")

        ctk.CTkLabel(frame_botones, text="Historial de Notas de Entrega Generadas", font=("Arial", 14, "bold")).pack(side="left", padx=10)
        ctk.CTkButton(frame_botones, text="🔄 Actualizar Historial", command=self.actualizar_tabla_historial_notas).pack(side="right", padx=10)

        frame_tabla_historial = ctk.CTkFrame(self.tab_historial)
        frame_tabla_historial.pack(pady=5, padx=10, fill="both", expand=True)

        columnas_historial = ("Nro Nota", "Fecha", "Cliente", "Dirección", "Estado")
        self.tabla_historial = ttk.Treeview(frame_tabla_historial, columns=columnas_historial, show="headings")
        for col in columnas_historial:
            self.tabla_historial.heading(col, text=col)
            self.tabla_historial.column(col, anchor="center")
        self.tabla_historial.pack(side="left", fill="both", expand=True)

        scroll_historial = ttk.Scrollbar(frame_tabla_historial, orient="vertical", command=self.tabla_historial.yview)
        self.tabla_historial.configure(yscroll=scroll_historial.set)
        scroll_historial.pack(side="right", fill="y")

    def actualizar_tabla_historial_notas(self):
        for i in self.tabla_historial.get_children(): self.tabla_historial.delete(i)
        notas = obtener_todas_las_notas()
        if notas:
            for nota in notas:
                self.tabla_historial.insert("", "end", values=nota)

    # =========================================================================
    # LÓGICA DE NEGOCIO
    # =========================================================================
    def cargar_datos_auto(self, nombre):
        for c in self.datos_clientes:
            if c[1] == nombre:
                self.ent_direccion.delete(0, "end")
                self.ent_direccion.insert(0, c[3]) 
                break

    def autocompletar_p(self, n):
        res = obtener_info_producto_por_nombre(n)
        if res: self.codigo_actual, self.nombre_actual = res[0], n

    def agregar_item(self):
        if not self.nombre_actual:
            messagebox.showwarning("Error", "Seleccione un producto válido.")
            return
        try:
            c = int(self.ent_cant.get())
            self.items_nota.append({"codigo": self.codigo_actual, "nombre": self.nombre_actual, "cantidad": c})
            self.tabla.insert("", "end", values=(len(self.items_nota), self.nombre_actual, c))
        except ValueError: messagebox.showwarning("Error", "Verifique cantidad.")

    def finalizar_nota(self):
        cli = self.combo_clientes.get()
        dir_cli = self.ent_direccion.get()
        obs = self.txt_obs.get("1.0", "end-1c")

        if cli == "Seleccionar Cliente" or not self.items_nota:
            messagebox.showwarning("Atención", "Debe completar los datos del cliente y añadir productos.")
            return

        nro = datetime.datetime.now().strftime("%Y%m%d%H%M")
        
        try:
            # 1. Generar el PDF
            pdf = generar_pdf_nota(cli, dir_cli, self.items_nota, obs, nro)
            
            # 2. Registrar en la Base de Datos para control de facturación
            guardar_nota_entrega(nro, cli, dir_cli, self.items_nota, obs)
            
            # 3. Descontar stock de inventario
            for i in self.items_nota:
                registrar_venta(i['codigo'], i['cantidad'])
            
            # 4. Notificar al usuario y abrir archivo
            messagebox.showinfo("Control de Ventas", 
                                f"Nota #{nro} generada correctamente.\n"
                                "Se ha registrado como PENDIENTE para facturar.")
            abrir_archivo(pdf)
            self.actualizar_tabla_historial_notas() # Refrescar historial después de generar
            self.destroy()
            
        except Exception as e:
            messagebox.showerror("Error de Sistema", f"Ocurrió un error al procesar la nota: {e}")

if __name__ == "__main__":
    root = ctk.CTk(); VentanaNotas(root); root.mainloop()