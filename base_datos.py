import sqlite3
import json
import pandas as pd
import re

# --- CONFIGURACIÓN GLOBAL ---
from config import DB_PATH
DB_NAME = DB_PATH

def conectar():
    """Conexión única a la base de datos oficial."""
    return sqlite3.connect(DB_NAME)

def crear_base_datos():
    """Crea la estructura completa de tablas si no existen."""
    conexion = conectar()
    cursor = conexion.cursor()
    
    # 1. Tabla de productos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS productos (
            codigo TEXT PRIMARY KEY,
            nombre TEXT NOT NULL,
            marca TEXT NOT NULL,
            descripcion TEXT,
            precio_costo REAL,
            precio_venta REAL NOT NULL,
            stock INTEGER NOT NULL,
            stock_minimo INTEGER DEFAULT 5
        )
    ''')

    # 2. Tabla de clientes
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clientes (
            id_cliente INTEGER PRIMARY KEY AUTOINCREMENT,
            empresa TEXT NOT NULL,
            rif TEXT,
            direccion TEXT,
            telefono TEXT,
            contacto TEXT
        )
    ''')

    # 3. Tabla de presupuestos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS presupuestos (
            id_presupuesto INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            cliente TEXT NOT NULL,
            rif TEXT,
            items TEXT NOT NULL, 
            total REAL NOT NULL,
            validez TEXT DEFAULT '15 días',
            estado TEXT DEFAULT 'Borrador'
        )
    ''')

    # 4. Tabla de facturas/ventas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS facturas (
            id_factura INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            cliente TEXT NOT NULL,
            total REAL NOT NULL,
            saldo_pendiente REAL DEFAULT 0
        )
    ''')

    # 5. Tabla para Control de Notas de Entrega
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS notas_entrega (
            nro_nota TEXT PRIMARY KEY,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            cliente TEXT NOT NULL,
            direccion TEXT,
            items TEXT NOT NULL,
            observaciones TEXT,
            estado TEXT DEFAULT 'Pendiente'
        )
    ''')

    # 6. Tabla para Auditoría de Inventario
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS movimientos_inventario (
            id_mov INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo_prod TEXT,
            tipo TEXT, -- 'Ingreso' o 'Egreso'
            cantidad INTEGER,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(codigo_prod) REFERENCES productos(codigo)
        )
    ''')

    # 7. Tabla de proveedores
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS proveedores (
            id_proveedor INTEGER PRIMARY KEY AUTOINCREMENT,
            empresa TEXT NOT NULL,
            rif TEXT,
            direccion TEXT,
            telefono TEXT,
            contacto TEXT
        )
    ''')

    # =========================================================================
    # NUEVAS TABLAS PARA EL MÓDULO DE CUENTAS POR PAGAR (CxP)
    # =========================================================================
    
    # 1. Tabla de Facturas de Compra (Deudas con Proveedores)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS facturas_compra (
            id_factura_compra INTEGER PRIMARY KEY AUTOINCREMENT,
            nro_factura TEXT NOT NULL,
            id_proveedor INTEGER NOT NULL,
            fecha_emision TEXT NOT NULL,
            fecha_vencimiento TEXT NOT NULL,
            subtotal REAL NOT NULL,
            monto_iva REAL NOT NULL,
            monto_total REAL NOT NULL,
            saldo_pendiente REAL NOT NULL,
            estado TEXT DEFAULT 'PENDIENTE', -- PENDIENTE, ABONADA, PAGADA, ANULADA
            observaciones TEXT,
            FOREIGN KEY (id_proveedor) REFERENCES proveedores (id_proveedor)
        )
    ''')

    # 2. Tabla para el Historial de Pagos / Abonos realizados
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pagos_cxp (
            id_pago INTEGER PRIMARY KEY AUTOINCREMENT,
            id_factura_compra INTEGER NOT NULL,
            fecha_pago TEXT NOT NULL,
            monto_pagado REAL NOT NULL,
            metodo_pago TEXT NOT NULL, -- TRANSFERENCIA, EFECTIVO, DIVISAS
            referencia TEXT,
            FOREIGN KEY (id_factura_compra) REFERENCES facturas_compra (id_factura_compra)
        )
    ''')
    
    # 3. Tabla para el detalle de los productos comprados (Itemizado)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS items_factura_compra (
            id_item_compra INTEGER PRIMARY KEY AUTOINCREMENT,
            id_factura_compra INTEGER NOT NULL,
            codigo_prod TEXT NOT NULL,
            cantidad INTEGER NOT NULL,
            costo_unitario REAL NOT NULL,
            FOREIGN KEY (id_factura_compra) REFERENCES facturas_compra (id_factura_compra),
            FOREIGN KEY (codigo_prod) REFERENCES productos (codigo)
        )
    ''')
    
    conexion.commit()
    conexion.close()
    print(f"✅ Base de datos {DB_NAME} Sincronizada.")

# --- MÓDULO DE PRODUCTOS ---

def obtener_productos():
    conexion = conectar()
    cursor = conexion.cursor()
    cursor.execute("SELECT codigo, nombre, marca, descripcion, precio_costo, precio_venta, stock FROM productos")
    datos = cursor.fetchall()
    conexion.close()
    return datos

def agregar_producto(codigo, nombre, marca, descripcion, costo, venta, stock, stock_min):
    conexion = conectar()
    cursor = conexion.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO productos 
        (codigo, nombre, marca, descripcion, precio_costo, precio_venta, stock, stock_minimo) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (codigo, nombre, marca, descripcion, costo, venta, stock, stock_min)) 
    cursor.execute("INSERT INTO movimientos_inventario (codigo_prod, tipo, cantidad) VALUES (?, 'Ingreso', ?)", (codigo, stock))
    conexion.commit()
    conexion.close()

def actualizar_producto(codigo, nombre, marca, descripcion, costo, venta, stock, stock_min):
    conexion = conectar()
    cursor = conexion.cursor()
    cursor.execute("""
        UPDATE productos SET nombre=?, marca=?, descripcion=?, precio_costo=?, 
        precio_venta=?, stock=?, stock_minimo=? WHERE codigo=?
    """, (nombre, marca, descripcion, costo, venta, stock, stock_min, codigo))
    conexion.commit()
    conexion.close()

def eliminar_producto(codigo):
    conexion = conectar()
    cursor = conexion.cursor()
    cursor.execute("DELETE FROM productos WHERE codigo=?", (codigo,))
    conexion.commit()
    conexion.close()

def obtener_info_producto_por_nombre(nombre):
    conexion = conectar()
    cursor = conexion.cursor()
    cursor.execute("SELECT codigo, precio_venta FROM productos WHERE nombre = ?", (nombre,))
    resultado = cursor.fetchone()
    conexion.close()
    return resultado

# --- MÓDULO DE PRESUPUESTOS ---

def guardar_presupuesto(cliente, rif, items, total, validez):
    conexion = conectar()
    cursor = conexion.cursor()
    items_json = json.dumps(items)
    cursor.execute("""
        INSERT INTO presupuestos (cliente, rif, items, total, validez) 
        VALUES (?, ?, ?, ?, ?)
    """, (cliente, rif, items_json, total, validez))
    id_presu = cursor.lastrowid
    conexion.commit()
    conexion.close()
    return id_presu

def obtener_presupuestos():
    conexion = conectar()
    cursor = conexion.cursor()
    cursor.execute("SELECT id_presupuesto, fecha, cliente, total, estado FROM presupuestos ORDER BY id_presupuesto DESC")
    datos = cursor.fetchall()
    conexion.close()
    return datos

# --- MÓDULO DE CLIENTES ---

def validar_formato_rif(rif):
    """Valida que el RIF tenga una letra al inicio y 9 números."""
    if not rif: return False
    # Patrón: Una letra (A-Z) seguida de exactamente 9 dígitos
    return bool(re.match(r'^[a-zA-Z]\d{9}$', str(rif).strip()))

def validar_formato_telefono(telefono):
    """Valida que el teléfono tenga exactamente 11 números (4 código + 7 número)."""
    if not telefono: return False
    # Extraer solo los dígitos numéricos
    numeros = "".join(filter(str.isdigit, str(telefono)))
    return len(numeros) == 11

def obtener_datos_clientes():
    conexion = conectar()
    cursor = conexion.cursor()
    cursor.execute("SELECT id_cliente, empresa, rif, direccion, telefono, contacto FROM clientes")
    datos = cursor.fetchall()
    conexion.close()
    return datos

def agregar_cliente(empresa, rif, direccion, telefono, contacto):
    if not validar_formato_rif(rif) or not validar_formato_telefono(telefono):
        return False
    conexion = conectar()
    cursor = conexion.cursor()
    cursor.execute("""
        INSERT INTO clientes (empresa, rif, direccion, telefono, contacto) 
        VALUES (?, ?, ?, ?, ?)
    """, (empresa, rif, direccion, telefono, contacto))
    conexion.commit()
    conexion.close()
    return True

def actualizar_cliente(id_cli, empresa, rif, direccion, telefono, contacto):
    if not validar_formato_rif(rif) or not validar_formato_telefono(telefono):
        return False
    conexion = conectar()
    cursor = conexion.cursor()
    cursor.execute("""
        UPDATE clientes SET empresa=?, rif=?, direccion=?, telefono=?, contacto=? 
        WHERE id_cliente=?
    """, (empresa, rif, direccion, telefono, contacto, id_cli))
    conexion.commit()
    conexion.close()
    return True

def eliminar_cliente(id_cli):
    conexion = conectar()
    cursor = conexion.cursor()
    cursor.execute("DELETE FROM clientes WHERE id_cliente=?", (id_cli,))
    conexion.commit()
    conexion.close()

# --- MÓDULO DE PROVEEDORES ---

def obtener_proveedores():
    conexion = conectar()
    cursor = conexion.cursor()
    cursor.execute("SELECT id_proveedor, empresa, rif, direccion, telefono, contacto FROM proveedores")
    datos = cursor.fetchall()
    conexion.close()
    return datos

def agregar_proveedor(empresa, rif, direccion, telefono, contacto):
    if not validar_formato_rif(rif) or not validar_formato_telefono(telefono):
        return False
    conexion = conectar()
    cursor = conexion.cursor()
    cursor.execute("""
        INSERT INTO proveedores (empresa, rif, direccion, telefono, contacto) 
        VALUES (?, ?, ?, ?, ?)
    """, (empresa, rif, direccion, telefono, contacto))
    conexion.commit()
    conexion.close()
    return True

def actualizar_proveedor(id_prov, empresa, rif, direccion, telefono, contacto):
    if not validar_formato_rif(rif) or not validar_formato_telefono(telefono):
        return False
    conexion = conectar()
    cursor = conexion.cursor()
    cursor.execute("""
        UPDATE proveedores SET empresa=?, rif=?, direccion=?, telefono=?, contacto=? 
        WHERE id_proveedor=?
    """, (empresa, rif, direccion, telefono, contacto, id_prov))
    conexion.commit()
    conexion.close()
    return True

def eliminar_proveedor(id_prov):
    conexion = conectar()
    cursor = conexion.cursor()
    cursor.execute("DELETE FROM proveedores WHERE id_proveedor=?", (id_prov,))
    conexion.commit()
    conexion.close()

# --- MÓDULO DE VENTAS Y NOTAS ---

def registrar_venta(codigo_prod, cantidad):
    conexion = conectar()
    cursor = conexion.cursor()
    cursor.execute("SELECT stock FROM productos WHERE codigo = ?", (codigo_prod,))
    resultado = cursor.fetchone()
    if resultado and resultado[0] >= cantidad:
        nuevo_stock = resultado[0] - cantidad
        cursor.execute("UPDATE productos SET stock = ? WHERE codigo = ?", (nuevo_stock, codigo_prod))
        cursor.execute("INSERT INTO movimientos_inventario (codigo_prod, tipo, cantidad) VALUES (?, 'Egreso', ?)", 
                       (codigo_prod, cantidad))
        conexion.commit()
        conexion.close()
        return True
    conexion.close()
    return False

def guardar_factura(cliente, total):
    conexion = conectar()
    cursor = conexion.cursor()
    cursor.execute("INSERT INTO facturas (cliente, total, saldo_pendiente) VALUES (?, ?, ?)", (cliente, total, total))
    id_gen = cursor.lastrowid
    conexion.commit()
    conexion.close()
    return id_gen

def guardar_nota_entrega(nro_nota, cliente, direccion, items, observaciones):
    conexion = conectar()
    cursor = conexion.cursor()
    items_texto = json.dumps(items)
    cursor.execute("""
        INSERT INTO notas_entrega (nro_nota, cliente, direccion, items, observaciones) 
        VALUES (?, ?, ?, ?, ?)
    """, (nro_nota, cliente, direccion, items_texto, observaciones))
    conexion.commit()
    conexion.close()

def obtener_nota_por_numero(nro_nota):
    conexion = conectar()
    cursor = conexion.cursor()
    cursor.execute("SELECT cliente, direccion, items, observaciones FROM notas_entrega WHERE nro_nota = ? AND estado = 'Pendiente'", (nro_nota,))
    resultado = cursor.fetchone()
    conexion.close()
    if resultado:
        return {
            "cliente": resultado[0], "direccion": resultado[1],
            "items": json.loads(resultado[2]), "observaciones": resultado[3]
        }
    return None

def marcar_nota_como_facturada(nro_nota):
    conexion = conectar()
    cursor = conexion.cursor()
    cursor.execute("UPDATE notas_entrega SET estado = 'Facturado' WHERE nro_nota = ?", (nro_nota,))
    conexion.commit()
    conexion.close()

def obtener_todas_las_notas():
    """Retorna todas las notas de entrega registradas para el historial."""
    conexion = conectar()
    cursor = conexion.cursor()
    cursor.execute("SELECT nro_nota, date(fecha), cliente, direccion, estado FROM notas_entrega ORDER BY fecha DESC")
    datos = cursor.fetchall()
    conexion.close()
    return datos

# --- MÓDULO DE REPORTES ---

def obtener_total_ventas_filtrado(fecha_inicio, fecha_fin):
    conexion = conectar()
    cursor = conexion.cursor()
    query = "SELECT COALESCE(SUM(total), 0) FROM facturas WHERE date(fecha) BETWEEN ? AND ?"
    cursor.execute(query, (fecha_inicio, fecha_fin))
    resultado = cursor.fetchone()
    conexion.close()
    return resultado[0] if resultado else 0.0

def obtener_historial_filtrado(fecha_inicio, fecha_fin):
    conexion = conectar()
    cursor = conexion.cursor()
    query = """SELECT id_factura, date(fecha), cliente, total, 
               CASE WHEN saldo_pendiente <= 0 THEN 'Pagado' ELSE 'Pendiente' END 
               FROM facturas WHERE date(fecha) BETWEEN ? AND ? ORDER BY fecha DESC"""
    cursor.execute(query, (fecha_inicio, fecha_fin))
    datos = cursor.fetchall()
    conexion.close()
    return datos

def obtener_reporte_notas(f_inicio, f_fin):
    conexion = conectar()
    cursor = conexion.cursor()
    query = "SELECT nro_nota, date(fecha), cliente, 'Detalle', estado FROM notas_entrega WHERE date(fecha) BETWEEN ? AND ?"
    cursor.execute(query, (f_inicio, f_fin))
    datos = cursor.fetchall()
    conexion.close()
    return datos

def obtener_inventario_completo():
    """Retorna todos los productos con sus detalles de inventario y stock mínimo."""
    conexion = conectar()
    cursor = conexion.cursor()
    # Seleccionamos las columnas que coinciden con el reporte de inventario
    cursor.execute("SELECT codigo, nombre, marca, precio_costo, precio_venta, stock, stock_minimo FROM productos")
    datos = cursor.fetchall()
    conexion.close()
    return datos

def obtener_reporte_inventario():
    conexion = conectar()
    cursor = conexion.cursor()
    query = """
        SELECT p.codigo, p.nombre,
        COALESCE((SELECT SUM(cantidad) FROM movimientos_inventario WHERE codigo_prod = p.codigo AND tipo LIKE 'Ingreso%'), 0),
        COALESCE((SELECT SUM(cantidad) FROM movimientos_inventario WHERE codigo_prod = p.codigo AND tipo = 'Egreso'), 0),
        p.stock FROM productos p
    """
    cursor.execute(query)
    datos = cursor.fetchall()
    conexion.close()
    return datos

def obtener_cuentas_por_cobrar():
    conexion = conectar()
    cursor = conexion.cursor()
    query = "SELECT id_factura, date(fecha), cliente, total, saldo_pendiente FROM facturas WHERE saldo_pendiente > 0"
    cursor.execute(query)
    datos = cursor.fetchall()
    conexion.close()
    return datos

def obtener_reporte_pdf_cxp():
    """Retorna las facturas de compra pendientes para el reporte PDF."""
    conexion = conectar()
    cursor = conexion.cursor()
    cursor.execute("""
        SELECT f.nro_factura, p.empresa, f.fecha_emision, f.fecha_vencimiento, f.monto_total, f.saldo_pendiente
        FROM facturas_compra f
        JOIN proveedores p ON f.id_proveedor = p.id_proveedor
        WHERE f.saldo_pendiente > 0
        ORDER BY f.fecha_vencimiento ASC
    """)
    datos = cursor.fetchall()
    conexion.close()
    return datos

def obtener_reporte_pdf_pagos_cxp():
    """Retorna el historial de abonos realizados a proveedores."""
    conexion = conectar()
    cursor = conexion.cursor()
    cursor.execute("""
        SELECT h.fecha_pago, f.nro_factura, p.empresa, h.monto_pagado, h.metodo_pago, h.referencia
        FROM pagos_cxp h
        JOIN facturas_compra f ON h.id_factura_compra = f.id_factura_compra
        JOIN proveedores p ON f.id_proveedor = p.id_proveedor
        ORDER BY h.fecha_pago DESC
    """)
    datos = cursor.fetchall()
    conexion.close()
    return datos

def cargar_productos_desde_excel(ruta_archivo):
    """Carga productos masivamente desde un Excel a la base de datos."""
    try:
        # Soporte para CSV y Excel
        if ruta_archivo.lower().endswith('.csv'):
            df = pd.read_csv(ruta_archivo)
        else:
            try:
                df = pd.read_excel(ruta_archivo)
            except Exception:
                df = pd.read_excel(ruta_archivo, engine='openpyxl')
        
        # Normalizar nombres de columnas (minúsculas y cambiar espacios por guiones bajos)
        df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
        
        # Verificar columnas obligatorias mínimas
        columnas_req = ['codigo', 'nombre', 'marca', 'precio_costo', 'precio_venta', 'stock']
        for col in columnas_req:
            if col not in df.columns:
                return f"Error: La columna '{col}' no se encuentra en el archivo Excel."
        
        conexion = conectar()
        cursor = conexion.cursor()
        
        exitos = 0
        errores = 0
        primer_error = ""
        
        for index, row in df.iterrows():
            try:
                # Función auxiliar para limpiar números con comas o símbolos
                def clean_n(val):
                    if pd.isna(val): return 0
                    return float(str(val).replace('$', '').replace(',', '.').strip())

                # Limpieza de datos y valores por defecto para evitar fallos por celdas vacías
                codigo = str(row['codigo']).strip()
                nombre = str(row['nombre']).strip()
                marca = str(row['marca']).strip()
                desc = str(row.get('descripcion', ''))
                costo = clean_n(row.get('precio_costo', 0))
                venta = clean_n(row.get('precio_venta', 0))
                stock = int(clean_n(row.get('stock', 0)))
                stock_min = int(clean_n(row.get('stock_minimo', 5)))

                if not codigo or codigo.lower() == 'nan': continue

                # Insertar o reemplazar si el código ya existe
                cursor.execute("""
                    INSERT OR REPLACE INTO productos 
                    (codigo, nombre, marca, descripcion, precio_costo, precio_venta, stock, stock_minimo) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (codigo, nombre, marca, desc, costo, venta, stock, stock_min))
                
                # Registrar el movimiento inicial en el inventario
                cursor.execute("INSERT INTO movimientos_inventario (codigo_prod, tipo, cantidad) VALUES (?, 'Ingreso', ?)", (codigo, stock))
                exitos += 1
            except Exception as e:
                if not primer_error: primer_error = str(e)
                errores += 1
                
        conexion.commit()
        conexion.close()
        res = f"Proceso finalizado: {exitos} cargados."
        if errores > 0: res += f"\n{errores} filas fallaron. Motivo: {primer_error}"
        return res
        
    except Exception as e:
        return f"Error al leer el archivo: {e}"

# =========================================================================
# FUNCIONES DE LÓGICA DE NEGOCIO PARA CUENTAS POR PAGAR (CxP)
# =========================================================================

def registrar_factura_compra_con_stock(nro_factura, id_proveedor, f_emision, f_venc, subtotal, iva, total, obs, lista_productos):
    """
    Registra de forma atómica una factura de compra y actualiza inmediatamente
    el stock y los movimientos en el módulo de inventario.
    """
    conexion = conectar()
    cursor = conexion.cursor()
    try:
        cursor.execute("BEGIN TRANSACTION;")
        
        # 1. Insertar la Cuenta por Pagar
        cursor.execute("""
            INSERT INTO facturas_compra (nro_factura, id_proveedor, fecha_emision, fecha_vencimiento, subtotal, monto_iva, monto_total, saldo_pendiente, estado, observaciones)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'PENDIENTE', ?)
        """, (nro_factura, id_proveedor, f_emision, f_venc, subtotal, iva, total, total, obs))
        
        id_factura = cursor.lastrowid
        
        # 2. Iterar sobre los productos comprados para sumarlos al inventario
        for prod in lista_productos:
            # prod es un diccionario: {'codigo': '...', 'cantidad': 10, 'costo': 50.0}
            
            # Registrar el detalle del item en la factura
            cursor.execute("""
                INSERT INTO items_factura_compra (id_factura_compra, codigo_prod, cantidad, costo_unitario)
                VALUES (?, ?, ?, ?)
            """, (id_factura, str(prod['codigo']), int(prod['cantidad']), float(prod['costo'])))

            cursor.execute("""
                UPDATE productos 
                SET stock = stock + ? 
                WHERE codigo = ?
            """, (int(prod['cantidad']), str(prod['codigo'])))
            
            # Registrar la trazabilidad del movimiento de ingreso
            cursor.execute("""
                INSERT INTO movimientos_inventario (codigo_prod, tipo, cantidad)
                VALUES (?, 'Ingreso por Compra', ?)
            """, (str(prod['codigo']), int(prod['cantidad'])))
            
        conexion.commit()
        return True
    except Exception as e:
        conexion.rollback()
        print(f"Error en Transacción CxP-Inventario: {e}")
        raise e
    finally:
        conexion.close()

def obtener_cxp_pendientes():
    """Trae todas las facturas de compra cuyo saldo pendiente sea mayor a cero."""
    conexion = conectar()
    cursor = conexion.cursor()
    cursor.execute("""
        SELECT f.id_factura_compra, f.nro_factura, p.empresa, f.fecha_emision, f.fecha_vencimiento, f.monto_total, f.saldo_pendiente, f.estado
        FROM facturas_compra f
        JOIN proveedores p ON f.id_proveedor = p.id_proveedor
        WHERE f.saldo_pendiente > 0
        ORDER BY f.fecha_vencimiento ASC
    """)
    datos = cursor.fetchall()
    conexion.close()
    return datos

def registrar_pago_cxp(id_factura, fecha_pago, monto_abono, metodo, referencia):
    """Registra un abono a una factura de compra y actualiza su saldo residual."""
    conexion = conectar()
    cursor = conexion.cursor()
    try:
        cursor.execute("BEGIN TRANSACTION;")
        
        # 1. Insertar el recibo del abono
        cursor.execute("""
            INSERT INTO pagos_cxp (id_factura_compra, fecha_pago, monto_pagado, metodo_pago, referencia)
            VALUES (?, ?, ?, ?, ?)
        """, (id_factura, fecha_pago, monto_abono, metodo, referencia))
        
        # 2. Descontar del saldo pendiente de la factura
        cursor.execute("""
            UPDATE facturas_compra 
            SET saldo_pendiente = saldo_pendiente - ? 
            WHERE id_factura_compra = ?
        """, (monto_abono, id_factura))
        
        # 3. Validar el nuevo estado de la factura
        cursor.execute("SELECT saldo_pendiente FROM facturas_compra WHERE id_factura_compra = ?", (id_factura,))
        nuevo_saldo = cursor.fetchone()[0]
        
        nuevo_estado = "PAGADA" if nuevo_saldo <= 0 else "ABONADA"
        if nuevo_saldo < 0:
            # Prevenir saldos negativos por errores de digitación
            cursor.execute("UPDATE facturas_compra SET saldo_pendiente = 0 WHERE id_factura_compra = ?", (id_factura,))
            
        cursor.execute("UPDATE facturas_compra SET estado = ? WHERE id_factura_compra = ?", (nuevo_estado, id_factura))
        
        conexion.commit()
        return True
    except Exception as e:
        conexion.rollback()
        raise e
    finally:
        conexion.close()

# --- INICIALIZADOR ---
if __name__ == "__main__":
    crear_base_datos()