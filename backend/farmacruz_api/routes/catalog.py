"""
Routes para Catálogo de Clientes

Endpoints para que los clientes naveguen productos con precios personalizados:
- GET /products - Lista de productos con precios calculados
- GET /products/{id} - Detalle de producto con precio calculado

Sistema de Precios:
1. Cada cliente tiene una PriceList asignada (vía CustomerInfo)
2. La PriceList contiene PriceListItems con markup por producto
3. Se calcula: final_price = (base_price * (1 + markup/100)) * (1 + iva/100)

Solo clientes autenticados pueden acceder (no admin/seller/marketing).
"""

from fastapi import APIRouter, Depends, Query
from typing import List, Optional
from sqlalchemy.orm import Session

from dependencies import get_db, get_current_user
from schemas.product import CatalogProduct
from crud import crud_catalog

router = APIRouter()


@router.get("/products", response_model=List[CatalogProduct])
def get_catalog_products(
    skip: int = Query(0, ge=0, description="Registros a saltar (paginación)"),
    limit: int = Query(50, ge=1, le=100, description="Máximo de registros (1-100)"),
    search: Optional[str] = Query(None, description="Buscar por nombre, descripción o codebar"),
    category_id: Optional[int] = Query(None, description="Filtrar por categoría"),
    sort_by: Optional[str] = Query(None, description="Ordenar por: name"),
    sort_order: Optional[str] = Query("asc", description="Orden: asc o desc"),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtiene productos del catálogo con precios personalizados
    
    Retorna solo productos:
    - Que estén en la PriceList del cliente
    - Que estén activos
    - Con precios calculados según el markup del cliente
    
    Filtros opcionales:
    - search: Busca en nombre, descripción y codebar
    - category_id: Filtra por categoría
    
    Permisos: Solo clientes
    
    Raises:
        403: Si el usuario no es cliente
        400: Si el cliente no tiene lista de precios
    """
    return crud_catalog.get_catalog_products(
        db=db,
        current_user=current_user,
        skip=skip,
        limit=limit,
        search=search,
        category_id=category_id,
        sort_by=sort_by,
        sort_order=sort_order
    )


@router.get("/products/{product_id}", response_model=CatalogProduct)
def get_catalog_product(
    product_id: str,  # Cambiado a str
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtiene un producto específico del catálogo
    
    Valida que:
    1. El producto esté en la lista de precios del cliente
    2. El producto esté activo
    
    Calcula el precio personalizado según el markup del cliente.
    
    Args:
        product_id: ID del producto (tipo texto, ej: "FAR74")
    
    Returns:
        Producto con precio calculado
    
    Permisos: Solo clientes
    
    Raises:
        403: Si el usuario no es cliente
        400: Si el cliente no tiene lista de precios
        404: Si el producto no existe o no está en la lista
    """
    return crud_catalog.get_catalog_product(
        db=db,
        current_user=current_user,
        product_id=product_id
    )
