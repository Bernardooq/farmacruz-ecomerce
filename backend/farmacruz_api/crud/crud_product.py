from typing import List, Optional
from sqlalchemy.orm import Session
from db.base import Product
from schemas.product import ProductCreate, ProductUpdate

def get_product(db: Session, product_id: int) -> Optional[Product]:
    """Obtiene un producto por ID"""
    return db.query(Product).filter(Product.product_id == product_id).first()

def get_product_by_sku(db: Session, sku: str) -> Optional[Product]:
    """Obtiene un producto por SKU"""
    return db.query(Product).filter(Product.sku == sku).first()

def get_products(
    db: Session, 
    skip: int = 0, 
    limit: int = 100,
    category_id: Optional[int] = None,
    is_active: Optional[bool] = None
) -> List[Product]:
    """Obtiene lista de productos con filtros opcionales"""
    query = db.query(Product)
    
    if category_id is not None:
        query = query.filter(Product.category_id == category_id)
    
    if is_active is not None:
        query = query.filter(Product.is_active == is_active)
    
    return query.offset(skip).limit(limit).all()

def search_products(db: Session, search: str, skip: int = 0, limit: int = 100) -> List[Product]:
    """Busca productos por nombre o descripción"""
    return db.query(Product).filter(
        (Product.name.ilike(f"%{search}%")) | 
        (Product.description.ilike(f"%{search}%"))
    ).offset(skip).limit(limit).all()

def create_product(db: Session, product: ProductCreate) -> Product:
    """Crea un nuevo producto"""
    db_product = Product(**product.dict())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

def update_product(db: Session, product_id: int, product: ProductUpdate) -> Optional[Product]:
    """Actualiza un producto"""
    db_product = get_product(db, product_id)
    if not db_product:
        return None
    
    update_data = product.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_product, field, value)
    
    db.commit()
    db.refresh(db_product)
    return db_product

def delete_product(db: Session, product_id: int) -> Optional[Product]:
    """Elimina un producto (soft delete - marca como inactivo)"""
    db_product = get_product(db, product_id)
    if db_product:
        db_product.is_active = False
        db.commit()
        db.refresh(db_product)
    return db_product

def update_stock(db: Session, product_id: int, quantity: int) -> Optional[Product]:
    """Actualiza el stock de un producto"""
    db_product = get_product(db, product_id)
    if db_product:
        db_product.stock_count += quantity
        db.commit()
        db.refresh(db_product)
    return db_product