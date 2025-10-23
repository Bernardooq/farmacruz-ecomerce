from dbfread import DBF
import pandas as pd
from pathlib import Path

def leer_dbf_auto(dbf_path, encoding="latin-1"):
    dbf_path = Path(dbf_path)
    base_name = dbf_path.stem  
    fpt_path = dbf_path.with_suffix(".fpt")

    try:
        if fpt_path.exists():
            print(f"Leyendo {dbf_path.name} con {fpt_path.name} (memo habilitado)")
            table = DBF(dbf_path, load=True, encoding=encoding)
        else:
            print(f"Leyendo {dbf_path.name} (sin memo, {fpt_path.name} no encontrado)")
            table = DBF(dbf_path, load=True, ignore_missing_memofile=True, encoding=encoding)

        df = pd.DataFrame(iter(table))
        print(f"Leídas {len(df)} filas y {len(df.columns)} columnas.")
        return df

    except Exception as e:
        print(f"Error leyendo {dbf_path.name}: {e}")
        return pd.DataFrame()

if __name__ == "__main__":
    carpeta = Path(r"C:\Users\berna\Downloads\desarrollo")
    archivos = carpeta.glob("*.dbf")

    for archivo in archivos:
        print("=" * 80)
        df = leer_dbf_auto(archivo)
        print(df.head(3))
