import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


@pytest.fixture()
def bd(tmp_path, monkeypatch):
    """Base de datos temporal y vacía para cada prueba."""
    ruta = tmp_path / "prueba.db"
    import base_datos
    monkeypatch.setattr(base_datos, "DB_NAME", str(ruta))
    base_datos.crear_base_datos()
    return base_datos
