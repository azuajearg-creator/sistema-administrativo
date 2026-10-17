from config import EMPRESA_NOMBRE
import customtkinter as ctk
from app_notas import VentanaNotas
from app_reportes import VentanaReportes
from app_presupuestos import VentanaPresupuestos
from app_facturacion import VentanaFacturacion
from app_proveedores import VentanaProveedores
from app_clientes import VentanaClientes
from app_inventario import VentanaInventario
from app_cxp import VentanaCxP
from base_datos import crear_base_datos

ctk.set_appearance_mode("dark")

class AppPrincipal(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(f"{EMPRESA_NOMBRE} - Sistema Administrativo")
        self.after(0, lambda: self.state('zoomed'))
        
        # Asegurar que las tablas de la base de datos existan al iniciar
        crear_base_datos()

        ctk.CTkLabel(self, text="SISTEMA ADMINISTRATIVO", font=("Arial", 26, "bold")).pack(pady=(30, 20))

        # Contenedor para organizar los botones en dos columnas
        frame_menu = ctk.CTkFrame(self, fg_color="transparent")
        frame_menu.pack(pady=10, padx=20)

        # Lista de opciones del menú (Texto, Clase de Ventana, Color)
        opciones = [
            ("📄 NOTAS DE ENTREGA", VentanaNotas, "#2980b9"),
            ("🧾 FACTURACIÓN", VentanaFacturacion, "#2980b9"),
            ("📝 PRESUPUESTOS", VentanaPresupuestos, "#3498db"),
            ("📦 INVENTARIO", VentanaInventario, "#16a085"),
            ("👥 CLIENTES", VentanaClientes, "#27ae60"),
            ("🚚 PROVEEDORES", VentanaProveedores, "#27ae60"),
            ("💰 CUENTAS POR PAGAR", VentanaCxP, "#d35400"),
            ("📊 REPORTES GENERALES", VentanaReportes, "#8e44ad")
        ]

        for i, (texto, Ventana, color) in enumerate(opciones):
            btn = ctk.CTkButton(frame_menu, text=texto, width=280, height=45, 
                                fg_color=color, font=("Arial", 12, "bold"),
                                command=lambda v=Ventana: v(self))
            btn.grid(row=i//2, column=i%2, padx=10, pady=10)

        ctk.CTkButton(self, text="SALIR DEL SISTEMA", fg_color="#c0392b", hover_color="#e74c3c", 
                      width=200, height=40, font=("Arial", 12, "bold"), command=self.destroy).pack(pady=30)

if __name__ == "__main__":
    app = AppPrincipal()
    app.mainloop()