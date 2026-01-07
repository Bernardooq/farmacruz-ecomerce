import pandas as pd
from dbfread import DBF
from pathlib import Path
from typing import List, Dict
import logging

# ==========================================================
# CONFIGURACIÓN DE LOGGING
# ==========================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# ==========================================================
# RUTAS DE ARCHIVOS DBF
# ==========================================================
# macOS / Linux
BASE_DIR = Path("/Users/bernardoorozco/Documents/GitHub/farmacruz-ecomerce/backend/dbfs")

# Windows (ejemplo)
# BASE_DIR = Path(r"C:\Users\berna\Documents\GitHub\farmacruz-ecomerce\backend\dbfs")

DBF_CLIENTES = BASE_DIR / "clientes.dbf"
DBF_PRODUCTOS = BASE_DIR / "producto.dbf"
DBF_PRECIOLIS = BASE_DIR / "PRECIPROD.DBF"

# ==========================================================
# FUNCIONES PARA LEER ARCHIVOS DBF (SIN MEMO)
# ==========================================================
def read_dbf(file_path: Path) -> List[Dict]:
    """Lee un archivo DBF ignorando archivos MEMO faltantes."""
    if not file_path.exists():
        logging.warning(f"Archivo no encontrado: {file_path}")
        return []

    try:
        table = DBF(
            file_path,
            encoding="latin-1",
            ignore_missing_memofile=True
        )
        return list(table)
    except Exception as e:
        logging.error(f"Error al leer DBF {file_path}: {e}")
        return []

def dbf_to_dataframe(file_path: Path) -> pd.DataFrame:
    """Convierte un DBF a DataFrame de pandas."""
    records = read_dbf(file_path)
    if not records:
        return pd.DataFrame()
    return pd.DataFrame(records)

# ==========================================================
# EJECUCIÓN DE PRUEBA
# ==========================================================
if __name__ == "__main__":

    logging.info("Leyendo producto.dbf")
    productos_df = dbf_to_dataframe(DBF_PRODUCTOS)
    productos_df.to_csv(BASE_DIR / "producto.csv", index=False)
    print("\nContenido de producto.dbf:")
    print(productos_df.head())
    print(f"\nColumnas en producto.dbf: {productos_df.columns.tolist()}")

    logging.info("Leyendo PRECIPROD.DBF")
    precios_df = dbf_to_dataframe(DBF_PRECIOLIS)
    precios_df.to_csv(BASE_DIR / "precios.csv", index=False)
    print("\nContenido de PRECIPROD.DBF:")
    print(precios_df.head())
    print(f"\nColumnas en PRECIPROD.DBF: {precios_df.columns.tolist()}")

    logging.info("Leyendo clientes.dbf (sin memo)")
    clientes_df = dbf_to_dataframe(DBF_CLIENTES)
    clientes_df.to_csv(BASE_DIR / "clientes.csv", index=False)
    print("\nContenido de clientes.dbf:")
    print(clientes_df.head())
    print(f"\nColumnas en clientes.dbf: {clientes_df.columns.tolist()}")