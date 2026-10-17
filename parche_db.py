import sqlite3
from config import DB_PATH

def aplicar_parche():
    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()
    
    print("Iniciando actualización de base de datos...")
    
    # 1. Agregar columna saldo_pendiente a facturas si no existe
    try:
        cursor.execute("ALTER TABLE facturas ADD COLUMN saldo_pendiente REAL DEFAULT 0")
        print("✅ Columna 'saldo_pendiente' agregada a facturas.")
    except sqlite3.OperationalError:
        print("ℹ️ La columna 'saldo_pendiente' ya existía.")

    # 2. Crear la tabla de movimientos de inventario si no existe
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS movimientos_inventario (
            id_mov INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo_prod TEXT,
            tipo TEXT, 
            cantidad INTEGER,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(codigo_prod) REFERENCES productos(codigo)
        )
    ''')
    print("✅ Tabla 'movimientos_inventario' verificada/creada.")

    # 3. (Opcional) Actualizar facturas viejas para que el saldo no sea 0
    cursor.execute("UPDATE facturas SET saldo_pendiente = total WHERE saldo_pendiente = 0")
    
    conexion.commit()
    conexion.close()
    print("🚀 Parche aplicado con éxito. Ya puedes abrir el programa.")

if __name__ == "__main__":
    aplicar_parche()