import sys
import os
import random
from pathlib import Path
import pandas as pd

# Configuración de rutas para que encuentre los módulos de la app
script_dir = Path(__file__).resolve().parent
api_dir = script_dir.parent
project_root = api_dir.parent.parent

sys.path.insert(0, str(project_root))
sys.path.insert(0, str(api_dir))

try:
    from db.session import SessionLocal
    from db.base import Product
except ImportError:
    # Fallback si se corre desde otra carpeta
    from backend.farmacruz_api.db.session import SessionLocal
    from backend.farmacruz_api.db.base import Product

def generate_excel():
    db = SessionLocal()
    try:
        print("Consultando productos activos de la base de datos...")
        # Obtenemos solo productos activos y que tengan código de barras
        products = db.query(Product.codebar).filter(
            Product.is_active == True,
            Product.codebar != None,
            Product.codebar != ""
        ).all()
        
        if not products:
            print("No se encontraron productos activos con código de barras.")
            return

        print(f"Se encontraron {len(products)} productos. Generando datos aleatorios...")
        
        # Crear lista de diccionarios para el DataFrame
        data = []
        for p in products:
            data.append({
                "Codigo Barras": p.codebar,
                "Cantidad": random.randint(1, 1000)
            })
            
        # Crear DataFrame
        df = pd.DataFrame(data)
        
        # Nombre del archivo
        output_file = script_dir / "test_import_farmacruz.xlsx"
        
        # Guardar a Excel (sin encabezados para probar la robustez del importador)
        df.to_excel(output_file, index=False, header=False)
        
        print(f"\n¡ÉXITO!")
        print(f"Se ha generado el archivo: {output_file}")
        print(f"Total de filas: {len(df)}")
        print("Puedes usar este archivo para probar la función 'Importar Excel' en el carrito.")
        
    except Exception as e:
        print(f"Error durante la generación: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    generate_excel()
