"""Configuración del sistema.

Los datos de la empresa que aparecen en los documentos (nombre, RIF, ciudad) y la
ubicación de la base de datos se definen aquí o con variables de entorno.
Los valores por defecto son FICTICIOS: cámbielos para su propio negocio.
"""
import os
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

EMPRESA_NOMBRE = os.environ.get("EMPRESA_NOMBRE", "Comercial Ejemplo, C.A.")
EMPRESA_RIF = os.environ.get("EMPRESA_RIF", "J-00000000-0")
EMPRESA_CIUDAD = os.environ.get("EMPRESA_CIUDAD", "Ciudad Ejemplo, País Ejemplo")

# Base de datos: data/sistema_administrativo.db (o la ruta de SISTEMA_DB).
DB_PATH = os.environ.get("SISTEMA_DB") or str(BASE_DIR / "data" / "sistema_administrativo.db")
Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)

# Carpeta donde se guardan los PDF generados.
CARPETA_SALIDA = Path(os.environ.get("SISTEMA_SALIDA") or BASE_DIR / "salida")


def ruta_salida(nombre: str) -> str:
    """Devuelve la ruta completa de un PDF dentro de la carpeta de salida."""
    CARPETA_SALIDA.mkdir(parents=True, exist_ok=True)
    return str(CARPETA_SALIDA / nombre)


def abrir_archivo(ruta: str) -> None:
    """Abre un archivo con el programa predeterminado (Windows, macOS o Linux)."""
    if os.environ.get("SISTEMA_NO_ABRIR"):
        return
    if sys.platform.startswith("win"):
        os.startfile(ruta)  # noqa: S606
    elif sys.platform == "darwin":
        subprocess.run(["open", ruta], check=False)
    else:
        subprocess.run(["xdg-open", ruta], check=False)
