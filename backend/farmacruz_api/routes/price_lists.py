"""
Routes para Listas de Precios (PriceLists)

Gestión completa de listas de precios y sus items(markups por producto):

LISTAS DE PRECIOS:
- GET / - Listar todas las listas
- GET /{id} - Ver lista con sus items
- POST / - Crear lista
- PUT /{id} - Actualizar lista
- DELETE /{id} - Eliminar lista

ITEMS (Markups por producto):
- GET /{id}/items - Ver todos los items
- POST /{id}/items - Agregar/actualizar item
- POST /{id}/items/bulk - Agregar/actualizar múltiples items
- PUT /{id}/items/{product_id} - Actualizar markup específico
- DELETE /{id}/items/{product_id} - Eliminar item

UTILIDADES PARA UI:
- GET /{id}/available-products - Productos no en lista (para agregar)
- GET /{id}/items-with-details - Items con info completa del producto

Sistema de Precios:
- Cada lista tiene múltiples items
- Cada item define un markup% para un producto
- Precio final = (base_price * (1 + markup/100)) * (1 + iva/100)
- Los clientes ven precios según su lista asignada

Permisos: Solo administradores
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from dependencies import get_db, get_current_admin_user
from db.base import User
from schemas.price_list import (
    PriceList, PriceListCreate, PriceListUpdate, PriceListWithItems,
    PriceListItem, PriceListItemCreate, PriceListItemUpdate,
    PriceListItemsBulkUpdate
)
from schemas.product import Product as ProductSchema
from crud import crud_price_list

router = APIRouter(prefix="/price-lists", tags=["price-lists"])


# ==========================================
# PriceList Endpoints
# ==========================================

@router.get("", response_model=List[PriceList])
def get_price_lists(
    skip: int = 0,
    limit: int = 100,
    is_active: bool = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Get all price lists (admin only)"""
    return crud_price_list.get_price_lists(db, skip=skip, limit=limit, is_active=is_active)


@router.get("/{price_list_id}", response_model=PriceListWithItems)
def get_price_list(
    price_list_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Get a specific price list with its items (admin only)"""
    
    price_list = crud_price_list.get_price_list(db, price_list_id)
    
    if not price_list:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lista de precios no encontrada"
        )
    
    # Get items
    items = crud_price_list.get_price_list_items(db, price_list_id)
    
    return PriceListWithItems(
        **price_list.__dict__,
        items=items
    )


@router.post("", response_model=PriceList, status_code=status.HTTP_201_CREATED)
def create_price_list(
    price_list: PriceListCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Create a new price list (admin only)"""
    return crud_price_list.create_price_list(db, price_list)


@router.put("/{price_list_id}", response_model=PriceList)
def update_price_list(
    price_list_id: int,
    price_list_update: PriceListUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Update a price list (admin only)"""
    
    updated_list = crud_price_list.update_price_list(db, price_list_id, price_list_update)
    
    if not updated_list:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lista de precios no encontrada"
        )
    
    return updated_list


@router.delete("/{price_list_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_price_list(
    price_list_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Delete a price list (admin only)"""
    
    success = crud_price_list.delete_price_list(db, price_list_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lista de precios no encontrada"
        )
    
    return None


# ==========================================
# PriceListItem Endpoints
# ==========================================

@router.get("/{price_list_id}/items", response_model=List[PriceListItem])
def get_price_list_items(
    price_list_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Get all items for a price list (admin only)"""
    
    # Verify price list exists
    price_list = crud_price_list.get_price_list(db, price_list_id)
    if not price_list:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lista de precios no encontrada"
        )
    
    return crud_price_list.get_price_list_items(db, price_list_id)


@router.post("/{price_list_id}/items", response_model=PriceListItem, status_code=status.HTTP_201_CREATED)
def create_price_list_item(
    price_list_id: int,
    item: PriceListItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Create or update a price list item (admin only)"""
    
    # Verify price list exists
    price_list = crud_price_list.get_price_list(db, price_list_id)
    if not price_list:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lista de precios no encontrada"
        )
    
    return crud_price_list.create_price_list_item(db, price_list_id, item)


@router.post("/{price_list_id}/items/bulk", response_model=List[PriceListItem])
def bulk_update_price_list_items(
    price_list_id: int,
    bulk_update: PriceListItemsBulkUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Bulk create/update price list items (admin only)"""
    
    # Verify price list exists
    price_list = crud_price_list.get_price_list(db, price_list_id)
    if not price_list:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lista de precios no encontrada"
        )
    
    return crud_price_list.bulk_update_price_list_items(db, price_list_id, bulk_update.items)


@router.put("/{price_list_id}/items/{product_id}", response_model=PriceListItem)
def update_price_list_item(
    price_list_id: int,
    product_id: str,
    item_update: PriceListItemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Update a specific price list item (admin only)"""
    
    updated_item = crud_price_list.update_price_list_item(db, price_list_id, product_id, item_update)
    
    if not updated_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item no encontrado en la lista de precios"
        )
    
    return updated_item


@router.delete("/{price_list_id}/items/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_price_list_item(
    price_list_id: int,
    product_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Delete a price list item (will use default markup) (admin only)"""
    
    success = crud_price_list.delete_price_list_item(db, price_list_id, product_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item no encontrado en la lista de precios"
        )
    
    return None


# ==========================================
# NEW ENDPOINTS FOR MODAL
# ==========================================

@router.get("/{price_list_id}/available-products", response_model=List[ProductSchema])
def get_available_products(
    price_list_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Get products that are NOT in the price list (available to add).
    With pagination and optional search by name, codebar, or description.
    (admin only)
    """
    # Verify price list exists
    price_list = crud_price_list.get_price_list(db, price_list_id)
    if not price_list:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lista de precios no encontrada"
        )
    
    return crud_price_list.get_products_not_in_price_list(
        db=db,
        price_list_id=price_list_id,
        skip=skip,
        limit=limit,
        search=search
    )


@router.get("/{price_list_id}/items-with-details")
def get_items_with_details(
    price_list_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Get products that ARE in the price list with full product details.
    Returns product info + markup percentage.
    With pagination and optional search by name, codebar, or description.
    (admin only)
    """
    # Verify price list exists
    price_list = crud_price_list.get_price_list(db, price_list_id)
    if not price_list:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lista de precios no encontrada"
        )
    
    return crud_price_list.get_products_in_price_list_with_details(
        db=db,
        price_list_id=price_list_id,
        skip=skip,
        limit=limit,
        search=search
    )
