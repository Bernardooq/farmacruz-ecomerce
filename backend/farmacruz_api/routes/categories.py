from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from sqlalchemy.orm import Session

from dependencies import get_db, get_current_admin_user
from schemas.category import CategoryCreate, CategoryUpdate, Category
from crud.crud_category import (
    get_categories, 
    get_category, 
    get_category_by_name,
    create_category,
    update_category,
    delete_category,
    search_categories,
    count_products_in_category
)

router = APIRouter()

@router.get("/", response_model=List[Category])
def read_categories(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Obtiene lista de categorías (público)
    """
    if search:
        categories = search_categories(db, search=search, skip=skip, limit=limit)
    else:
        categories = get_categories(db, skip=skip, limit=limit)
    return categories

@router.get("/{category_id}", response_model=Category)
def read_category(category_id: int, db: Session = Depends(get_db)):
    """
    Obtiene una categoría específica por su ID (público)
    """
    category = get_category(db, category_id=category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Categoría no encontrada"
        )
    return category

@router.post("/", response_model=Category, status_code=status.HTTP_201_CREATED)
def create_new_category(
    category: CategoryCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """
    Crea una nueva categoría (solo admin)
    """
    # Verificar que el nombre no exista
    db_category = get_category_by_name(db, name=category.name)
    if db_category:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe una categoría con ese nombre"
        )
    
    return create_category(db=db, category=category)

@router.put("/{category_id}", response_model=Category)
def update_existing_category(
    category_id: int,
    category: CategoryUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """
    Actualiza una categoría existente (solo admin)
    """
    # Si se está actualizando el nombre, verificar que no exista
    if category.name:
        existing = get_category_by_name(db, name=category.name)
        if existing and existing.category_id != category_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya existe una categoría con ese nombre"
            )
    
    db_category = update_category(db, category_id=category_id, category=category)
    if not db_category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Categoría no encontrada"
        )
    return db_category

@router.delete("/{category_id}")
def delete_existing_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """
    Elimina una categoría (solo admin)
    """
    # Verificar si tiene productos asociados
    product_count = count_products_in_category(db, category_id)
    if product_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No se puede eliminar. La categoría tiene {product_count} producto(s) asociado(s)"
        )
    
    db_category = delete_category(db, category_id=category_id)
    if not db_category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Categoría no encontrada"
        )
    return {"message": "Categoría eliminada exitosamente"}