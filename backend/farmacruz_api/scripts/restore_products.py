import sys
import os
from pathlib import Path

# Encontrar la raíz del proyecto (la carpeta que contiene 'backend')
# Si el script está en backend/farmacruz_api/scripts/restore_products.py
# La raíz es .parent.parent.parent.parent
current_path = Path(__file__).resolve()
project_root = current_path.parent.parent.parent.parent

sys.path.append(str(project_root))

print(f"DEBUG: Project Root: {project_root}")
print(f"DEBUG: Current Working Dir: {os.getcwd()}")

try:
    from backend.farmacruz_api.db.session import SessionLocal
    from backend.farmacruz_api.db.base import Product, Category, PriceList
except ImportError as e:
    print(f"Error importando módulos: {e}")
    print("Asegúrate de ejecutar el script con python3")
    sys.exit(1)

def restore():
    db = SessionLocal()
    try:
        print("Restoring Products (setting is_active=True)...")
        products_count = db.query(Product).filter(Product.is_active == False).update({Product.is_active: True})
        
        print("Restoring Categories (touching updated_at)...")
        # Categories usually don't have is_active in this schema, just updated_at
        db.query(Category).update({Category.updated_at: Category.updated_at})
        
        print("Restoring Price Lists (setting is_active=True)...")
        pricelists_count = db.query(PriceList).filter(PriceList.is_active == False).update({PriceList.is_active: True})
        
        db.commit()
        print(f"\nSUCCESS!")
        print(f"- {products_count} products reactivated.")
        print(f"- {pricelists_count} price lists reactivated.")
        print("\nVerificar ahora el dashboard de Inventario.")
    except Exception as e:
        print(f"Error during restoration: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    restore()
