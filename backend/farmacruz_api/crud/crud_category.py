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


def get_category(db: Session, category_id: int) -> Optional[Category]:
    # Obtiene una categoria por ID

    return db.query(Category).filter(
        Category.category_id == category_id
    ).first()


def get_category_by_name(db: Session, name: str) -> Optional[Category]:
    
    # Obtiene una categoria por nombre exacto
    return db.query(Category).filter(Category.name == name).first()


def get_categories(db: Session, skip: int = 0, limit: int = 100) -> List[Category]:
    # Obtiene lista de todas las categorias

    return db.query(Category).offset(skip).limit(limit).all()


def search_categories(db: Session, search: str, skip: int = 0, limit: int = 100) -> List[Category]:
    # Busca categorias por nombre o descripcion
    
    return db.query(Category).filter(
        (Category.name.ilike(f"%{search}%")) | 
        (Category.description.ilike(f"%{search}%"))
    ).offset(skip).limit(limit).all()


def create_category(db: Session, category: CategoryCreate) -> Category:
    # Crea una nueva categoria

    db_category = Category(**category.model_dump())
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category


def update_category(db: Session, category_id: int, category: CategoryUpdate) -> Optional[Category]:
    # Actualiza una categoria existente

    db_category = get_category(db, category_id)
    if not db_category:
        return None
    
    update_data = category.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_category, field, value)
    
    db.commit()
    db.refresh(db_category)
    return db_category


def delete_category(db: Session, category_id: int) -> Optional[Category]:
    # Elimina una categoria
    
    db_category = get_category(db, category_id)
    if db_category:
        db.delete(db_category)
        db.commit()
    return db_category


def count_products_in_category(db: Session, category_id: int) -> int:
    # Cuenta cuantos productos tiene una categoria
    return db.query(Product).filter(
        Product.category_id == category_id,
        Product.is_active == True
    ).count()


def get_categories_with_product_count(db: Session) -> List[dict]:
    # Obtiene todas las categorias con el conteo de productos de cada una
      
    categories = db.query(Category).all()
    result = []
    
    for category in categories:
        product_count = count_products_in_category(db, category.category_id)
        result.append({
            "category": category,
            "product_count": product_count
        })
    
    return result