from dbfread import DBF
import pandas as pd
from pathlib import Path

def leer_dbf_auto(dbf_path, encoding="latin-1"):
    dbf_path = Path(dbf_path)
    fpt_path = dbf_path.with_suffix(".fpt")  # Memo file

    try:
        if fpt_path.exists():
            print(f"Leyendo {dbf_path.name} con {fpt_path.name} (memo habilitado)")
            table = DBF(dbf_path, load=True, encoding=encoding)
        else:
            print(f"Leyendo {dbf_path.name} (sin memo, {fpt_path.name} no encontrado)")
            table = DBF(dbf_path, load=True, ignore_missing_memofile=True, encoding=encoding)

        df = pd.DataFrame(iter(table))
        # Guardar el DataFrame en un archivo CSV
        df.to_csv(dbf_path.with_suffix(".csv"), index=False)
        print(f"Leidas {len(df)} filas y {len(df.columns)} columnas.")
        return df, df.columns

    except Exception as e:
        print(f"Error leyendo {dbf_path.name}: {e}")
        return pd.DataFrame() 
if __name__ == "__main__":
    archivo_especifico = Path(r"C:\Users\berna\Documents\GitProjects\farmacruz-ecomerce\backend\dbfs\pro_desc.dbf")
    
    df, cols = leer_dbf_auto(archivo_especifico)
    print(cols)
    print(df.head(5))
