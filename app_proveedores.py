from config import EMPRESA_NOMBRE, EMPRESA_RIF, EMPRESA_CIUDAD, ruta_salida, abrir_archivo  # noqa: F401
import customtkinter as ctk
from tkinter import ttk, messagebox
from base_datos import obtener_proveedores, agregar_proveedor, actualizar_proveedor, eliminar_proveedor

class VentanaProveedores(ctk.CTkToplevel):
    def __init__(self, master): # Ahora recibe el master correctamente
        super().__init__(master)
        self.title(f"Directorio de Proveedores - {EMPRESA_NOMBRE}")
        self.after(0, lambda: self.state('zoomed'))
        
        # --- CONFIGURACIÓN DE VENTANA HIJA ---
        self.focus_force()
        self.grab_set() 
        
        self.id_seleccionado = None

        # --- BOTÓN REGRESAR ---
        self.btn_regresar = ctk.CTkButton(
            self, 
            text="← VOLVER AL MENÚ", 
            width=140, 
            height=35,
            fg_color="#7f8c8d", 
            hover_color="#95a5a6",
            font=("Arial", 12, "bold"),
            command=self.destroy # Libera el wait_window del main.py
        )
        self.btn_regresar.place(x=20, y=20)

        # Título Principal (con margen superior para el botón)
        ctk.CTkLabel(self, text="GESTIÓN DE PROVEEDORES", font=("Arial", 24, "bold")).pack(pady=(40, 20))

        # --- FORMULARIO ---
        self.frame_inputs = ctk.CTkFrame(self)
        self.frame_inputs.pack(pady=10, padx=20, fill="x")

        # Columnas proporcionales
        self.frame_inputs.columnconfigure((1, 3), weight=1)

        # Fila 1: Empresa y RIF
        ctk.CTkLabel(self.frame_inputs, text="Empresa:", font=("Arial", 13, "bold")).grid(row=0, column=0, padx=10, pady=10, sticky="e")
        self.ent_empresa = ctk.CTkEntry(self.frame_inputs)
        self.ent_empresa.grid(row=0, column=1, padx=10, pady=10, sticky="ew")

        ctk.CTkLabel(self.frame_inputs, text="RIF:", font=("Arial", 13, "bold")).grid(row=0, column=2, padx=10, pady=10, sticky="e")
        self.frame_rif = ctk.CTkFrame(self.frame_inputs, fg_color="transparent") # Contenedor para RIF
        self.frame_rif.grid(row=0, column=3, padx=10, pady=10, sticky="ew") 
        self.combo_rif_tipo = ctk.CTkComboBox(self.frame_rif, values=["V", "J", "E", "G", "P", "C"], width=60)
        self.combo_rif_tipo.pack(side="left", padx=(0, 5))
        self.ent_rif_num = ctk.CTkEntry(self.frame_rif)
        self.ent_rif_num.pack(side="left", fill="x", expand=True)
        
        # Fila 2: Dirección y Teléfono
        ctk.CTkLabel(self.frame_inputs, text="Dirección:", font=("Arial", 13, "bold")).grid(row=1, column=0, padx=10, pady=10, sticky="e")
        self.ent_dir = ctk.CTkEntry(self.frame_inputs)
        self.ent_dir.grid(row=1, column=1, padx=10, pady=10, sticky="ew")

        ctk.CTkLabel(self.frame_inputs, text="Teléfono:", font=("Arial", 13, "bold")).grid(row=1, column=2, padx=10, pady=10, sticky="e")
        self.frame_telefono = ctk.CTkFrame(self.frame_inputs, fg_color="transparent") # Contenedor para Teléfono
        self.frame_telefono.grid(row=1, column=3, padx=10, pady=10, sticky="ew")
        phone_codes = ["0412", "0422", "0414", "0416", "0424", "0426", "0212", "0241", "0261", "0251", "0286", "0295"]
        self.combo_tel_cod = ctk.CTkComboBox(self.frame_telefono, values=phone_codes, width=80)
        self.combo_tel_cod.set("0412") # Valor por defecto
        self.combo_tel_cod.pack(side="left", padx=(0, 5))
        self.ent_tel_num = ctk.CTkEntry(self.frame_telefono, placeholder_text="Ej: 1234567")
        self.ent_tel_num.pack(side="left", fill="x", expand=True)

        # Fila 3: Persona de Contacto
        ctk.CTkLabel(self.frame_inputs, text="Persona Contacto:", font=("Arial", 13, "bold")).grid(row=2, column=0, padx=10, pady=10, sticky="e")
        self.ent_cont = ctk.CTkEntry(self.frame_inputs)
        self.ent_cont.grid(row=2, column=1, padx=10, pady=10, sticky="ew")

        # --- BOTONES ---
        self.frame_btns = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_btns.pack(pady=10)

        ctk.CTkButton(self.frame_btns, text="Registrar Proveedor", fg_color="#27ae60", command=self.guardar).grid(row=0, column=0, padx=10)
        ctk.CTkButton(self.frame_btns, text="Modificar Datos", fg_color="#2980b9", command=self.modificar).grid(row=0, column=1, padx=10)
        ctk.CTkButton(self.frame_btns, text="Eliminar Registro", fg_color="#e74c3c", command=self.borrar).grid(row=0, column=2, padx=10)

        # --- TABLA ---
        self.tabla_frame = ctk.CTkFrame(self)
        self.tabla_frame.pack(pady=20, padx=20, fill="both", expand=True)

        columnas = ("ID", "Empresa", "RIF", "Dirección", "Teléfono", "Contacto")
        self.tabla = ttk.Treeview(self.tabla_frame, columns=columnas, show="headings")
        
        for col in columnas:
            self.tabla.heading(col, text=col)
            self.tabla.column(col, anchor="center", width=120)
        
        self.tabla.pack(side="left", fill="both", expand=True)
        
        scrollbar = ttk.Scrollbar(self.tabla_frame, orient="vertical", command=self.tabla.yview)
        self.tabla.configure(yscroll=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        self.tabla.bind("<<TreeviewSelect>>", self.cargar_seleccion)
        self.cargar_tabla()

    def cargar_tabla(self):
        for i in self.tabla.get_children(): self.tabla.delete(i)
        for fila in obtener_proveedores(): self.tabla.insert("", "end", values=fila)

    def cargar_seleccion(self, event):
        seleccion = self.tabla.selection()
        if seleccion:
            item = self.tabla.item(seleccion)['values']
            self.id_seleccionado = item[0]
            self.ent_empresa.delete(0, "end"); self.ent_empresa.insert(0, item[1])
            
            rif_completo = str(item[2])
            if len(rif_completo) > 0:
                self.combo_rif_tipo.set(rif_completo[0])
                self.ent_rif_num.delete(0, "end"); self.ent_rif_num.insert(0, rif_completo[1:])
            else:
                self.combo_rif_tipo.set("J") # Default para proveedores
                self.ent_rif_num.delete(0, "end")
            self.ent_dir.delete(0, "end"); self.ent_dir.insert(0, item[3])
            
            tel_completo = str(item[4])
            if len(tel_completo) == 11:
                self.combo_tel_cod.set(tel_completo[0:4])
                self.ent_tel_num.delete(0, "end"); self.ent_tel_num.insert(0, tel_completo[4:])
            else:
                self.combo_tel_cod.set("0412") # Default
                self.ent_tel_num.delete(0, "end")
            self.ent_cont.delete(0, "end"); self.ent_cont.insert(0, item[5])

    def guardar(self):
        if self.ent_empresa.get():
            rif_completo = self.combo_rif_tipo.get() + self.ent_rif_num.get().strip()
            tel_completo = self.combo_tel_cod.get() + self.ent_tel_num.get().strip()
            exito = agregar_proveedor(self.ent_empresa.get(), rif_completo, self.ent_dir.get(), tel_completo, self.ent_cont.get())
            if exito:
                messagebox.showinfo("Éxito", "Proveedor registrado.")
                self.limpiar_y_refrescar()
            else:
                messagebox.showwarning("Formato Inválido", "Verifique el RIF (J123456789) y el Teléfono (11 dígitos).")

    def modificar(self):
        if self.id_seleccionado:
            rif_completo = self.combo_rif_tipo.get() + self.ent_rif_num.get().strip()
            tel_completo = self.combo_tel_cod.get() + self.ent_tel_num.get().strip()
            exito = actualizar_proveedor(self.id_seleccionado, self.ent_empresa.get(), rif_completo, self.ent_dir.get(), tel_completo, self.ent_cont.get())
            if exito:
                messagebox.showinfo("Éxito", "Datos actualizados.")
                self.limpiar_y_refrescar()
            else:
                messagebox.showwarning("Formato Inválido", "Verifique el RIF y el Teléfono.")

    def borrar(self):
        if self.id_seleccionado and messagebox.askyesno("Confirmar", "¿Eliminar este proveedor?"):
            eliminar_proveedor(self.id_seleccionado)
            self.limpiar_y_refrescar()

    def limpiar_y_refrescar(self):
        self.id_seleccionado = None
        self.ent_empresa.delete(0, "end")
        self.ent_rif_num.delete(0, "end")
        self.combo_rif_tipo.set("J") # Default para proveedores
        self.ent_dir.delete(0, "end")
        self.ent_tel_num.delete(0, "end")
        self.combo_tel_cod.set("0412") # Default
        self.ent_cont.delete(0, "end")
        self.cargar_tabla()

if __name__ == "__main__":
    # Prueba independiente
    root = ctk.CTk()
    app = VentanaProveedores(root)
    root.mainloop()