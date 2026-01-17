"""
Routes para Categorias de Productos

Endpoints CRUD para gestion de categorias:
- GET / - Lista de categorias (publico)
- GET /{id} - Detalle de categoria (publico)
- POST / - Crear categoria (admin)
- PUT /{id} - Actualizar categoria (admin)
- DELETE /{id} - Eliminar categoria (admin)

Permisos:
- GET: Todos los usuarios (publico)
- POST/PUT/DELETE: Solo administradores

Las categorias organizan productos en grupos logicos.
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

""" GET / - Lista de categorias """
@router.get("/", response_model=List[Category])
def read_categories(
    skip: int = Query(0, ge=0, description="Registros a saltar"),
    limit: int = Query(100, ge=1, le=200, description="Maximo de registros"),
    search: Optional[str] = Query(None, description="Buscar por nombre o descripcion"),
    db: Session = Depends(get_db)
):
    # Lista de categorias
    if search:
        categories = search_categories(db, search=search, skip=skip, limit=limit)
    else:
        categories = get_categories(db, skip=skip, limit=limit)
    return categories

""" GET /{id} - Detalle de categoria """
@router.get("/{category_id}", response_model=Category)
def read_category(category_id: int, db: Session = Depends(get_db)):
    # Detalle de una categoria especifica
    category = get_category(db, category_id=category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Categoria no encontrada"
        )
    return category

""" POST / - Crear categoria """
@router.post("/", response_model=Category, status_code=status.HTTP_201_CREATED)
def create_new_category(
    category: CategoryCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    # Crea una nueva categoria
    # Nom único
    db_category = get_category_by_name(db, name=category.name)
    if db_category:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ya existe una categoria con el nombre '{category.name}'"
        )
    
    return create_category(db=db, category=category)

""" PUT /{id} - Actualizar categoria """
@router.put("/{category_id}", response_model=Category)
def update_existing_category(
    category_id: int,
    category: CategoryUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    # Actualiza una categoria existente
    # Valida nombre unico
    if category.name:
        existing = get_category_by_name(db, name=category.name)
        if existing and existing.category_id != category_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ya existe una categoria con el nombre '{category.name}'"
            )
    
    db_category = update_category(db, category_id=category_id, category=category)
    if not db_category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Categoria no encontrada"
        )
    return db_category

""" DELETE /{id} - Eliminar categoria """
@router.delete("/{category_id}")
def delete_existing_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    # Elimina una categoria (hard delete)
    # Validar que no tenga products
    product_count = count_products_in_category(db, category_id)
    if product_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No se puede eliminar. La categoria tiene {product_count} producto(s) asociado(s). Reasigna los productos primero."
        )
    
    db_category = delete_category(db, category_id=category_id)
    if not db_category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Categoria no encontrada"
        )
    
    return {"message": "Categoria eliminada exitosamente"}