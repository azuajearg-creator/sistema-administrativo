import re

import pytest

import documentos


@pytest.fixture(autouse=True)
def carpeta_salida(tmp_path, monkeypatch):
    monkeypatch.setattr(documentos, "ruta_salida", lambda nombre: str(tmp_path / nombre))


def _texto_pdf(ruta):
    """Extrae el texto del PDF con pypdf si está instalado; si no, omite la prueba."""
    pypdf = pytest.importorskip("pypdf")
    return "\n".join(p.extract_text() for p in pypdf.PdfReader(ruta).pages)


def test_nota_de_entrega_genera_pdf_con_datos(tmp_path):
    ruta = documentos.generar_pdf_nota(
        "Cliente Uno (J123456789)", "Calle Ficticia 123",
        [{"nombre": "Tóner negro", "cantidad": 3}], "Entrega de prueba", "N-0001")
    assert ruta.endswith("Nota_N-0001.pdf")
    assert open(ruta, "rb").read(5) == b"%PDF-"
    texto = _texto_pdf(ruta)
    assert "Tóner negro" in texto and "N-0001" in texto and "Calle Ficticia 123" in texto


def test_factura_genera_pdf_con_totales(tmp_path):
    items = [{"nombre": "Tóner negro", "cantidad": 3, "precio": 65.0, "subtotal": 195.0}]
    cliente = {"nombre": "Cliente Uno", "rif": "J123456789", "direccion": "Calle 1", "telefono": "02120000001"}
    ruta = documentos.generar_pdf_factura(cliente, items, 10, 19.5, 195.0, 28.08, 203.58, "F-0001")
    assert open(ruta, "rb").read(5) == b"%PDF-"
    texto = _texto_pdf(ruta)
    assert "F-0001" in texto and "203.58" in texto and "J123456789" in texto


def test_texto_con_caracteres_especiales_no_rompe_el_pdf(tmp_path):
    ruta = documentos.generar_pdf_nota(
        "A & B <Cía> S.A.", "Av. <1> & 2", [{"nombre": "Cable <USB> & 'mouse'", "cantidad": 1}],
        "obs <b>no negrita</b> & más", "N-2")
    assert open(ruta, "rb").read(5) == b"%PDF-"


def test_nota_con_muchos_items_ocupa_varias_paginas(tmp_path):
    items = [{"nombre": f"Producto {i}", "cantidad": i} for i in range(1, 90)]
    ruta = documentos.generar_pdf_nota("Cliente", "Dir", items, "", "N-3")
    pypdf = pytest.importorskip("pypdf")
    assert len(pypdf.PdfReader(ruta).pages) >= 2
