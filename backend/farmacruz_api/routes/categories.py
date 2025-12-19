"""
Routes para Categorías de Productos

Endpoints CRUD para gestión de categorías:
- GET / - Lista de categorías (público)
- GET /{id} - Detalle de categoría (público)
- POST / - Crear categoría (admin)
- PUT /{id} - Actualizar categoría (admin)
- DELETE /{id} - Eliminar categoría (admin)

Permisos:
- GET: Todos los usuarios (público)
- POST/PUT/DELETE: Solo administradores

Las categorías organizan productos en grupos lógicos.
"""

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
    skip: int = Query(0, ge=0, description="Registros a saltar"),
    limit: int = Query(100, ge=1, le=200, description="Máximo de registros"),
    search: Optional[str] = Query(None, description="Buscar por nombre o descripción"),
    db: Session = Depends(get_db)
):
    """
    Lista de categorías
    
    Búsqueda opcional por nombre o descripción.
    
    Permisos: Público (todos los usuarios)
    """
    if search:
        categories = search_categories(db, search=search, skip=skip, limit=limit)
    else:
        categories = get_categories(db, skip=skip, limit=limit)
    return categories


@router.get("/{category_id}", response_model=Category)
def read_category(category_id: int, db: Session = Depends(get_db)):
    """
    Detalle de una categoría específica
    
    Permisos: Público (todos los usuarios)
    
    Raises:
        404: Categoría no encontrada
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
    Crea una nueva categoría
    
    Validaciones:
    - Nombre único
    
    Permisos: Solo administradores
    
    Raises:
        400: Categoría con ese nombre ya existe
    """
    # === VALIDAR NOMBRE ÚNICO ===
    db_category = get_category_by_name(db, name=category.name)
    if db_category:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ya existe una categoría con el nombre '{category.name}'"
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
    Actualiza una categoría existente
    
    Validaciones:
    - Si se cambia el nombre, debe ser único
    
    Permisos: Solo administradores
    
    Raises:
        400: Nombre ya existe
        404: Categoría no encontrada
    """
    # === VALIDAR NOMBRE ÚNICO ===
    if category.name:
        existing = get_category_by_name(db, name=category.name)
        if existing and existing.category_id != category_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ya existe una categoría con el nombre '{category.name}'"
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
    Elimina una categoría (hard delete)
    
    Validaciones:
    - No puede tener productos asociados
    
    Recomendación:
    Reasignar productos a otra categoría antes de eliminar.
    
    Permisos: Solo administradores
    
    Raises:
        400: Categoría tiene productos asociados
        404: Categoría no encontrada
    """
    # === VALIDAR QUE NO TENGA PRODUCTOS ===
    product_count = count_products_in_category(db, category_id)
    if product_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No se puede eliminar. La categoría tiene {product_count} producto(s) asociado(s). Reasigna los productos primero."
        )
    
    db_category = delete_category(db, category_id=category_id)
    if not db_category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Categoría no encontrada"
        )
    
    return {"message": "Categoría eliminada exitosamente"}