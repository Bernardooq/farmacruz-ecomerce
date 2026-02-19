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
from db.base import UserRole, CustomerInfo
from crud.crud_product import get_similar_products
from fastapi import APIRouter, Depends, Query, HTTPException, status
from typing import List, Optional
from sqlalchemy.orm import Session

from dependencies import get_db, get_current_user, get_current_seller_user
# from schemas.product import CatalogProduct  # Ya no se usa, retornamos dict
from crud import crud_catalog

router = APIRouter()

""" GET /products - Lista de productos con precios calculados """
@router.get("/products")  # response_model removido - retorna dict sin base_price
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
@router.get("/products/{product_id}")  # response_model removido - retorna dict sin base_price
def get_catalog_product(product_id: str, current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    # Obtiene un producto especifico del catalogo
    return crud_catalog.get_catalog_product(db=db, current_user=current_user, product_id=product_id)

""" GET /customer/{customer_id}/products - Lista de productos con precios del cliente (Admin/Marketing) """
@router.get("/customer/{customer_id}/products")  # response_model removido - retorna dict sin base_price
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


""" GET /customer/{customer_id}/products/{product_id}/similar - Productos similares con precios del cliente """
@router.get("/customer/{customer_id}/products/{product_id}/similar")
def get_product_similar_for_customer(
    customer_id: int,
    product_id: str,
    limit: int = Query(8, ge=1, le=20, description="Numero de productos similares"),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtiene productos similares usando get_similar_products con price_list del cliente"""

    # Verificar permisos
    if current_user.role != UserRole.admin:
        if not user_can_manage_order(db, current_user.user_id, customer_id, current_user.role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene permiso para ver productos de este cliente"
            )
    
    # Obtener price_list_id del cliente
    customer_info = db.query(CustomerInfo).filter(
        CustomerInfo.customer_id == customer_id
    ).first()
    
    if not customer_info or not customer_info.price_list_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El cliente no tiene lista de precios asignada"
        )
    
    # Llamar a get_similar_products con price_list_id del cliente
    results = get_similar_products(
        db=db,
        product_id=product_id,
        price_list_id=customer_info.price_list_id,
        limit=limit
    )
    
    # Retornar productos con su similarity_score inyectado
    response = []
    for item in results:
        product_dict = item["product"]
        # Inyectar el score. Asegurarse de que el objeto sea mutable (dict)
        if hasattr(product_dict, "dict"):
            product_dict = product_dict.dict()
        
        product_dict["similarity_score"] = item["similarity_score"]
        response.append(product_dict)
    
    return response

