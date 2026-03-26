import sys
import os
sys.path.append(os.getcwd())
from backend.farmacruz_api.db.session import SessionLocal
from backend.farmacruz_api.db.base import Product, Category, PriceList

def restore():
    db = SessionLocal()
    try:
        print("Restoring Products...")
        products_count = db.query(Product).filter(Product.is_active == False).update({Product.is_active: True})
        
        print("Restoring Categories...")
        categories_count = db.query(Category).filter(Category.updated_at != None).update({Category.updated_at: Category.updated_at}) # Just touching them or setting is_active if it existed
        
        print("Restoring Price Lists...")
        pricelists_count = db.query(PriceList).filter(PriceList.is_active == False).update({PriceList.is_active: True})
        
        db.commit()
        print(f"Success! {products_count} products reactivated.")
        print(f"{pricelists_count} price lists reactivated.")
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    restore()
