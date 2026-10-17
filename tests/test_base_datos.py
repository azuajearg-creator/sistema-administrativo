import pytest


def test_producto_alta_baja_y_movimiento(bd):
    bd.agregar_producto("P1", "Producto", "M", "desc", 10.0, 15.0, 5, 2)
    assert [p[0] for p in bd.obtener_productos()] == ["P1"]
    assert bd.obtener_info_producto_por_nombre("Producto") == ("P1", 15.0)
    bd.eliminar_producto("P1")
    assert bd.obtener_productos() == []


def test_venta_descuenta_stock_y_rechaza_exceso(bd):
    bd.agregar_producto("P1", "Producto", "M", "", 10.0, 15.0, 5, 2)
    assert bd.registrar_venta("P1", 3) is True
    assert bd.obtener_productos()[0][6] == 2
    assert bd.registrar_venta("P1", 3) is False
    assert bd.obtener_productos()[0][6] == 2


@pytest.mark.parametrize("rif,ok", [("J123456789", True), ("v000000001", True), ("J12345678", False),
                                    ("123456789", False), ("", False), (None, False)])
def test_validar_rif(bd, rif, ok):
    assert bd.validar_formato_rif(rif) is ok


@pytest.mark.parametrize("tel,ok", [("02120000001", True), ("0212-000-0001", True),
                                    ("12345", False), ("", False)])
def test_validar_telefono(bd, tel, ok):
    assert bd.validar_formato_telefono(tel) is ok


def test_cliente_invalido_no_se_guarda(bd):
    assert bd.agregar_cliente("X", "mal", "dir", "02120000001", "c") is False
    assert bd.agregar_cliente("X", "J123456789", "dir", "02120000001", "c") is not False
    assert len(bd.obtener_datos_clientes()) == 1


def test_factura_de_compra_suma_stock_y_registra_pagos(bd):
    bd.agregar_producto("P1", "Producto", "M", "", 10.0, 15.0, 0, 2)
    bd.agregar_proveedor("Prov", "J234567890", "dir", "02120000002", "c")
    bd.registrar_factura_compra_con_stock("F-1", 1, "2026-01-01", "2026-02-01", 100.0, 16.0, 116.0, "",
                                          [{"codigo": "P1", "cantidad": 10, "costo": 10.0}])
    assert bd.obtener_productos()[0][6] == 10
    assert len(bd.obtener_cxp_pendientes()) == 1

    bd.registrar_pago_cxp(1, "2026-01-15", 16.0, "EFECTIVO", "R1")
    assert bd.obtener_cxp_pendientes()[0][6] == pytest.approx(100.0)
    assert bd.obtener_cxp_pendientes()[0][7] == "ABONADA"

    bd.registrar_pago_cxp(1, "2026-01-20", 100.0, "EFECTIVO", "R2")
    assert bd.obtener_cxp_pendientes() == []


def test_pago_mayor_al_saldo_no_deja_saldo_negativo(bd):
    bd.agregar_proveedor("Prov", "J234567890", "dir", "02120000002", "c")
    bd.agregar_producto("P1", "Producto", "M", "", 1.0, 2.0, 0, 1)
    bd.registrar_factura_compra_con_stock("F-1", 1, "2026-01-01", "2026-02-01", 10.0, 0.0, 10.0, "",
                                          [{"codigo": "P1", "cantidad": 1, "costo": 10.0}])
    bd.registrar_pago_cxp(1, "2026-01-02", 50.0, "EFECTIVO", "R")
    assert bd.obtener_cxp_pendientes() == []


def test_factura_de_compra_con_producto_inexistente_no_deja_registros(bd):
    bd.agregar_proveedor("Prov", "J234567890", "dir", "02120000002", "c")
    with pytest.raises(Exception):
        bd.registrar_factura_compra_con_stock("F-1", 1, "2026-01-01", "2026-02-01", 10.0, 0.0, 10.0, "",
                                              [{"codigo": "P1", "cantidad": "no-numero", "costo": 1.0}])
    assert bd.obtener_cxp_pendientes() == []


def test_presupuesto_y_nota_de_entrega(bd):
    pid = bd.guardar_presupuesto("Cliente", "J123456789", [{"nombre": "A", "cantidad": 1}], 10.0, "15 días")
    assert pid == 1
    assert bd.obtener_presupuestos()[0][2] == "Cliente"
    bd.guardar_nota_entrega("N-1", "Cliente", "dir", [{"nombre": "A", "cantidad": 1}], "obs")
    assert bd.obtener_nota_por_numero("N-1") is not None
