import sys
import os
from pathlib import Path

# Configuración de rutas para EC2 / Producción
# 1. Directorio del script
script_dir = Path(__file__).resolve().parent
# 2. Directorio de la API (farmacruz_api)
api_dir = script_dir.parent
# 3. Directorio del proyecto raíz (que contiene 'backend')
project_root = api_dir.parent.parent

# Agregar ambos al path para resolver 'from backend...' y 'from core...'
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(api_dir))

print(f"DEBUG: Project Root: {project_root}")
print(f"DEBUG: API Dir: {api_dir}")

try:
    # Intentar importaciones relativas al root o a la api
    try:
        from backend.farmacruz_api.db.session import SessionLocal
        from backend.farmacruz_api.db.base import Product, Category, PriceList
    except ImportError:
        from db.session import SessionLocal
        from db.base import Product, Category, PriceList
        
except ImportError as e:
    print(f"Error importando módulos: {e}")
    sys.exit(1)

def restore():
    db = SessionLocal()
    try:
        print("\nRestaurando visibilidad del catálogo...")
        products_count = db.query(Product).filter(Product.is_active == False).update({Product.is_active: True})
        
        print("Restaurando categorías...")
        db.query(Category).update({Category.updated_at: Category.updated_at})
        
        print("Restaurando listas de precios...")
        pricelists_count = db.query(PriceList).filter(PriceList.is_active == False).update({PriceList.is_active: True})
        
        db.commit()
        print(f"\n¡ÉXITO TOTAL!")
        print(f"- {products_count} productos reactivados.")
        print(f"- {pricelists_count} listas de precios reactivadas.")
        print("\nYa puedes verificar el Inventario en el Dashboard.")
    except Exception as e:
        print(f"Error durante la restauración: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    restore()
