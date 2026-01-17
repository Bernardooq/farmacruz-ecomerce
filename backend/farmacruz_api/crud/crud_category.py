"""
CRUD para Categorias de Productos (Categories)

Funciones para manejar categorias del catalogo:
- Operaciones CRUD basicas
- Busqueda
- Conteo de productos por categoria

Las categorias organizan productos en grupos logicos como:
"Analgesicos", "Antibioticos", "Vitaminas", etc.
"""

from typing import List, Optional
from sqlalchemy.orm import Session

from db.base import Category, Product
from schemas.category import CategoryCreate, CategoryUpdate

"""Obtiene una categoria por ID"""
def get_category(db: Session, category_id: int) -> Optional[Category]:
    return db.query(Category).filter(
        Category.category_id == category_id
    ).first()

"""Obtiene una categoria por nombre exacto"""
def get_category_by_name(db: Session, name: str) -> Optional[Category]:    
    return db.query(Category).filter(Category.name == name).first()

"""Obtiene todas las categorias con paginacion"""
def get_categories(db: Session, skip: int = 0, limit: int = 100) -> List[Category]:
    return db.query(Category).offset(skip).limit(limit).all()

"""Busca categorias por nombre o descripcion"""
def search_categories(db: Session, search: str, skip: int = 0, limit: int = 100) -> List[Category]:    
    return db.query(Category).filter(
        (Category.name.ilike(f"%{search}%")) | 
        (Category.description.ilike(f"%{search}%"))
    ).offset(skip).limit(limit).all()

"""Crea una nueva categoria"""
def create_category(db: Session, category: CategoryCreate) -> Category:
    db_category = Category(**category.model_dump())
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category

"""Actualiza una categoria existente"""
def update_category(db: Session, category_id: int, category: CategoryUpdate) -> Optional[Category]:
    db_category = get_category(db, category_id)
    if not db_category:
        return None
    
    update_data = category.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_category, field, value)
    
    db.commit()
    db.refresh(db_category)
    return db_category

"""Elimina una categoria por ID"""
def delete_category(db: Session, category_id: int) -> Optional[Category]:    
    db_category = get_category(db, category_id)
    if db_category:
        db.delete(db_category)
        db.commit()
    return db_category

"""Cuenta cuantos productos tiene una categoria"""
def count_products_in_category(db: Session, category_id: int) -> int:
    return db.query(Product).filter(
        Product.category_id == category_id,
        Product.is_active == True
    ).count()

"""Obtiene todas las categorias con conteo de productos"""
def get_categories_with_product_count(db: Session) -> List[dict]:      
    categories = db.query(Category).all()
    result = []
    
    for category in categories:
        product_count = count_products_in_category(db, category.category_id)
        result.append({
            "category": category,
            "product_count": product_count
        })
    
    return result