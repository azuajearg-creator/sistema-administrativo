#!/usr/bin/env python3
"""Carga datos FICTICIOS de ejemplo en la base de datos del sistema.

Uso:
    python seed_demo.py            # solo si la base está vacía
    python seed_demo.py --reset    # borra la base y la recrea con datos de ejemplo

Todos los nombres, RIF, direcciones y teléfonos son inventados.
"""
import argparse
import os
import sys
from pathlib import Path

import config
import base_datos as bd

PRODUCTOS = [
    # código, nombre, marca, costo, venta, stock, mínimo
    ("TON-001", "Tóner negro para impresora láser", "MarcaA", 42.0, 65.0, 25, 5),
    ("TON-002", "Tóner cian para impresora láser", "MarcaA", 48.0, 74.0, 12, 4),
    ("TON-003", "Tóner magenta para impresora láser", "MarcaA", 48.0, 74.0, 3, 4),
    ("TON-004", "Tóner amarillo para impresora láser", "MarcaA", 48.0, 74.0, 10, 4),
    ("CIL-001", "Unidad de imagen (cilindro)", "MarcaA", 85.0, 130.0, 8, 2),
    ("REV-001", "Revelador negro", "MarcaB", 60.0, 95.0, 6, 2),
    ("FUS-001", "Unidad de fusión", "MarcaB", 150.0, 230.0, 2, 2),
    ("RODI-01", "Kit de rodillos de alimentación", "MarcaB", 22.0, 38.0, 30, 8),
    ("PAP-A4", "Papel carta/A4 resma 500 hojas", "MarcaC", 3.5, 5.5, 200, 50),
    ("CAB-USB", "Cable USB para impresora 1,8 m", "MarcaC", 2.0, 4.0, 40, 10),
]
CLIENTES = [
    ("Cliente Uno, C.A.", "J123456789", "Calle Ficticia 123, Ciudad Ejemplo", "02120000001", "Ana Ejemplo"),
    ("Cliente Dos, S.A.", "J234567890", "Avenida Imaginaria 45, Ciudad Ejemplo", "02120000002", "Bruno Ejemplo"),
    ("Servicios Tres, C.A.", "J345678901", "Zona Industrial Norte, Local 7", "04120000003", "Carla Ejemplo"),
]
PROVEEDORES = [
    ("Distribuidora Alfa (demo)", "J456789012", "Parque Industrial Sur, Galpón 3", "02120000011", "Diego Ejemplo"),
    ("Suministros Beta (demo)", "J567890123", "Avenida Demo 100", "04120000012", "Elena Ejemplo"),
]


def main() -> int:
    ap = argparse.ArgumentParser(description="Carga datos ficticios de ejemplo.")
    ap.add_argument("--reset", action="store_true", help="Borra la base y la recrea")
    args = ap.parse_args()

    db = Path(config.DB_PATH)
    if args.reset and db.exists():
        db.unlink()
    bd.crear_base_datos()
    if bd.obtener_productos():
        print("La base ya tiene productos. Use --reset para recrearla.", file=sys.stderr)
        return 1

    for cod, nom, marca, costo, venta, stock, minimo in PRODUCTOS:
        bd.agregar_producto(cod, nom, marca, nom, costo, venta, stock, minimo)
    for c in CLIENTES:
        bd.agregar_cliente(*c)
    for p in PROVEEDORES:
        bd.agregar_proveedor(*p)

    # Una venta, un presupuesto, una factura de compra con un abono.
    bd.registrar_venta("TON-001", 3)
    bd.guardar_presupuesto("Cliente Uno, C.A.", "J123456789",
                           [{"nombre": PRODUCTOS[0][1], "cantidad": 2, "precio": 65.0, "subtotal": 130.0}], 130.0, "15 días")
    bd.registrar_factura_compra_con_stock(
        "F-0001", 1, "2026-01-10", "2026-02-10", 420.0, 67.2, 487.2, "Compra de ejemplo",
        [{"codigo": "TON-001", "cantidad": 10, "costo": 42.0}])
    bd.registrar_pago_cxp(1, "2026-01-20", 200.0, "TRANSFERENCIA", "REF-0001")

    print(f"Datos de ejemplo cargados en {db}")
    print(f"  productos: {len(PRODUCTOS)} | clientes: {len(CLIENTES)} | proveedores: {len(PROVEEDORES)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
