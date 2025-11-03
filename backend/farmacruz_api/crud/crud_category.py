from typing import List, Optional
from sqlalchemy.orm import Session
from db.base import Category
from schemas.category import CategoryCreate, CategoryUpdate

def get_category(db: Session, category_id: int) -> Optional[Category]:
    """Obtiene una categoría por ID"""
    return db.query(Category).filter(Category.category_id == category_id).first()

def get_category_by_name(db: Session, name: str) -> Optional[Category]:
    """Obtiene una categoría por nombre"""
    return db.query(Category).filter(Category.name == name).first()

def get_categories(
    db: Session, 
    skip: int = 0, 
    limit: int = 100
) -> List[Category]:
    """Obtiene lista de categorías"""
    return db.query(Category).offset(skip).limit(limit).all()

def search_categories(db: Session, search: str, skip: int = 0, limit: int = 100) -> List[Category]:
    """Busca categorías por nombre o descripción"""
    return db.query(Category).filter(
        (Category.name.ilike(f"%{search}%")) | 
        (Category.description.ilike(f"%{search}%"))
    ).offset(skip).limit(limit).all()

def create_category(db: Session, category: CategoryCreate) -> Category:
    """Crea una nueva categoría"""
    db_category = Category(**category.dict())
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category

def update_category(db: Session, category_id: int, category: CategoryUpdate) -> Optional[Category]:
    """Actualiza una categoría"""
    db_category = get_category(db, category_id)
    if not db_category:
        return None
    
    update_data = category.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_category, field, value)
    
    db.commit()
    db.refresh(db_category)
    return db_category

def delete_category(db: Session, category_id: int) -> Optional[Category]:
    """Elimina una categoría"""
    db_category = get_category(db, category_id)
    if db_category:
        db.delete(db_category)
        db.commit()
    return db_category

def count_products_in_category(db: Session, category_id: int) -> int:
    """Cuenta cuántos productos tiene una categoría"""
    from db.base import Product
    return db.query(Product).filter(Product.category_id == category_id).count()