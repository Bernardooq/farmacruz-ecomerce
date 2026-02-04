"""
Routes para Catalogo de Clientes

Endpoints para que los clientes naveguen productos con precios personalizados:
- GET /products - Lista de productos con precios calculados
- GET /products/{id} - Detalle de producto con precio calculado

Sistema de Precios:
1. Cada cliente tiene una PriceList asignada (via CustomerInfo)
2. La PriceList contiene PriceListItems con markup por producto
3. Se calcula: final_price = (base_price * (1 + markup/100)) * (1 + iva/100)

Solo clientes autenticados pueden acceder (no admin/seller/marketing).
"""

from crud.crud_sales_group import user_can_manage_order
from db.base import UserRole
from fastapi import APIRouter, Depends, Query, HTTPException, status
from typing import List, Optional
from sqlalchemy.orm import Session

from dependencies import get_db, get_current_user, get_current_seller_user
from schemas.product import CatalogProduct
from crud import crud_catalog

router = APIRouter()

""" GET /products - Lista de productos con precios calculados """
@router.get("/products", response_model=List[CatalogProduct])
def get_catalog_products(
    skip: int = Query(0, ge=0, description="Registros a saltar (paginacion)"),
    limit: int = Query(50, ge=1, le=100, description="Maximo de registros (1-100)"),
    search: Optional[str] = Query(None, description="Buscar por nombre, descripcion o codebar"),
    category_id: Optional[int] = Query(None, description="Filtrar por categoria"),
    sort_by: Optional[str] = Query(None, description="Ordenar por: name"),
    sort_order: Optional[str] = Query("asc", description="Orden: asc o desc"),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Obtiene productos del catalogo con precios personalizados
    return crud_catalog.get_catalog_products(db=db, current_user=current_user, skip=skip, limit=limit,
        search=search, category_id=category_id, sort_by=sort_by, sort_order=sort_order)

""" GET /products/{id} - Detalle de producto con precio calculado """
@router.get("/products/{product_id}", response_model=CatalogProduct)
def get_catalog_product(product_id: str, current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    # Obtiene un producto especifico del catalogo
    return crud_catalog.get_catalog_product(db=db, current_user=current_user, product_id=product_id)

""" GET /customer/{customer_id}/products - Lista de productos con precios del cliente (Admin/Marketing) """
@router.get("/customer/{customer_id}/products", response_model=List[CatalogProduct])
def get_customer_catalog_products(
    customer_id: int,
    skip: int = Query(0, ge=0, description="Registros a saltar (paginacion)"),
    limit: int = Query(50, ge=1, le=100, description="Maximo de registros (1-100)"),
    search: Optional[str] = Query(None, description="Buscar por ID, nombre, descripcion o codebar"),
    category_id: Optional[int] = Query(None, description="Filtrar por categoria"),
    sort_by: Optional[str] = Query(None, description="Ordenar por: name"),
    sort_order: Optional[str] = Query("asc", description="Orden: asc o desc"),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    # Verificar permisos: admin puede ver cualquier cliente, otros deben estar en el mismo grupo
    if current_user.role != UserRole.admin:
        if not user_can_manage_order(db, current_user.user_id, customer_id, current_user.role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene permiso para ver el catalogo de este cliente"
            )
    
    return crud_catalog.get_customer_catalog_products(
        db=db, customer_id=customer_id, skip=skip, limit=limit, search=search, category_id=category_id,
        sort_by=sort_by, sort_order=sort_order)
