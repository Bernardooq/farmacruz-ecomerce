"""
CRUD para Categorías de Productos (Categories)

Funciones para manejar categorías del catálogo:
- Operaciones CRUD básicas
- Búsqueda
- Conteo de productos por categoría

Las categorías organizan productos en grupos lógicos como:
"Analgésicos", "Antibióticos", "Vitaminas", etc.
"""

from typing import List, Optional
from sqlalchemy.orm import Session

from db.base import Category, Product
from schemas.category import CategoryCreate, CategoryUpdate


def get_category(db: Session, category_id: int) -> Optional[Category]:
    """
    Obtiene una categoría por ID
    
    Args:
        db: Sesión de base de datos
        category_id: ID de la categoría
        
    Returns:
        Categoría encontrada o None si no existe
    """
    return db.query(Category).filter(
        Category.category_id == category_id
    ).first()


def get_category_by_name(db: Session, name: str) -> Optional[Category]:
    """
    Obtiene una categoría por nombre exacto
    
    Útil para verificar duplicados antes de crear.
    
    Args:
        db: Sesión de base de datos
        name: Nombre exacto de la categoría
        
    Returns:
        Categoría encontrada o None si no existe
    """
    return db.query(Category).filter(Category.name == name).first()


def get_categories(
    db: Session, 
    skip: int = 0, 
    limit: int = 100
) -> List[Category]:
    """
    Obtiene lista de todas las categorías
    
    Args:
        db: Sesión de base de datos
        skip: Número de registros a saltar (paginación)
        limit: Máximo de registros a devolver
        
    Returns:
        Lista de categorías
    """
    return db.query(Category).offset(skip).limit(limit).all()


def search_categories(
    db: Session,
    search: str,
    skip: int = 0,
    limit: int = 100
) -> List[Category]:
    """
    Busca categorías por nombre o descripción
    
    La búsqueda es insensible a mayúsculas/minúsculas.
    
    Args:
        db: Sesión de base de datos
        search: Término de búsqueda
        skip: Número de registros a saltar
        limit: Máximo de registros a devolver
        
    Returns:
        Lista de categorías que coinciden con la búsqueda
    """
    return db.query(Category).filter(
        (Category.name.ilike(f"%{search}%")) | 
        (Category.description.ilike(f"%{search}%"))
    ).offset(skip).limit(limit).all()


def create_category(db: Session, category: CategoryCreate) -> Category:
    """
    Crea una nueva categoría
    
    Args:
        db: Sesión de base de datos
        category: Schema con datos de la categoría a crear
        
    Returns:
        Categoría creada con ID generado
    """
    db_category = Category(**category.dict())
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category


def update_category(
    db: Session,
    category_id: int,
    category: CategoryUpdate
) -> Optional[Category]:
    """
    Actualiza una categoría existente
    
    Args:
        db: Sesión de base de datos
        category_id: ID de la categoría a actualizar
        category: Schema con campos a actualizar
        
    Returns:
        Categoría actualizada o None si no existe
    """
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
    """
    Elimina una categoría
    
    Warning:
        Los productos en esta categoría quedarán sin categoría
        (category_id = NULL). Consider reasignarlos primero.
    
    Args:
        db: Sesión de base de datos
        category_id: ID de la categoría a eliminar
        
    Returns:
        Categoría eliminada o None si no existía
    """
    db_category = get_category(db, category_id)
    if db_category:
        db.delete(db_category)
        db.commit()
    return db_category


def count_products_in_category(db: Session, category_id: int) -> int:
    """
    Cuenta cuántos productos tiene una categoría
    
    Útil para verificar antes de eliminar una categoría
    o mostrar estadísticas.
    
    Args:
        db: Sesión de base de datos
        category_id: ID de la categoría
        
    Returns:
        Número de productos activos en la categoría
    """
    return db.query(Product).filter(
        Product.category_id == category_id,
        Product.is_active == True
    ).count()


def get_categories_with_product_count(db: Session) -> List[dict]:
    """
    Obtiene todas las categorías con el conteo de productos de cada una
    
    Útil para mostrar en el admin dashboard.
    
    Args:
        db: Sesión de base de datos
        
    Returns:
        Lista de dicts con {category, product_count}
    """
    from sqlalchemy import func
    
    categories = db.query(Category).all()
    result = []
    
    for category in categories:
        product_count = count_products_in_category(db, category.category_id)
        result.append({
            "category": category,
            "product_count": product_count
        })
    
    return result