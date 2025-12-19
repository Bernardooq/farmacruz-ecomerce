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

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from decimal import Decimal

from dependencies import get_db, get_current_user
from db.base import Customer, CustomerInfo, Product, PriceListItem
from schemas.product import Product as ProductSchema

router = APIRouter()


class CatalogProduct(ProductSchema):
    """
    Producto del catálogo con precios calculados para el cliente
    
    Incluye:
    - Todos los campos del producto base
    - final_price: Precio con markup e IVA aplicados
    - markup_percentage: % de ganancia del cliente
    """
    final_price: Decimal
    markup_percentage: Decimal
    
    class Config:
        from_attributes = True


@router.get("/products", response_model=List[CatalogProduct])
def get_catalog_products(
    skip: int = Query(0, ge=0, description="Registros a saltar (paginación)"),
    limit: int = Query(50, ge=1, le=100, description="Máximo de registros (1-100)"),
    search: Optional[str] = Query(None, description="Buscar por nombre, descripción o SKU"),
    category_id: Optional[int] = Query(None, description="Filtrar por categoría"),
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
    - search: Busca en nombre, descripción y SKU
    - category_id: Filtra por categoría
    
    Permisos: Solo clientes
    
    Raises:
        403: Si el usuario no es cliente
        400: Si el cliente no tiene lista de precios
    """
    # === VALIDAR QUE SEA CLIENTE ===
    if not isinstance(current_user, Customer):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Este endpoint es solo para clientes"
        )
    
    # === OBTENER LISTA DE PRECIOS DEL CLIENTE ===
    customer_info = db.query(CustomerInfo).filter(
        CustomerInfo.customer_id == current_user.customer_id
    ).first()
    
    if not customer_info or not customer_info.price_list_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No tienes una lista de precios asignada. Contacta al administrador."
        )
    
    # === CONSTRUIR QUERY BASE ===
    # Join Products con PriceListItems para obtener solo productos en la lista
    query = db.query(Product, PriceListItem).join(
        PriceListItem,
        Product.product_id == PriceListItem.product_id
    ).options(
        joinedload(Product.category)  # Pre-cargar categoría
    ).filter(
        PriceListItem.price_list_id == customer_info.price_list_id,
        Product.is_active == True
    )
    
    # === APLICAR BÚSQUEDA ===
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (Product.name.ilike(search_term)) |
            (Product.description.ilike(search_term)) |
            (Product.sku.ilike(search_term))
        )
    
    # === FILTRAR POR CATEGORÍA ===
    if category_id:
        query = query.filter(Product.category_id == category_id)
    
    # === ORDENAR Y PAGINAR ===
    query = query.order_by(Product.name.asc())
    results = query.offset(skip).limit(limit).all()
    
    # === CALCULAR PRECIOS FINALES ===
    catalog_products = []
    for product, price_item in results:
        # Fórmula: final = (base * (1 + markup/100)) * (1 + iva/100)
        base_price = Decimal(str(product.base_price or 0))
        markup = Decimal(str(price_item.markup_percentage or 0))
        iva = Decimal(str(product.iva_percentage or 0))
        
        price_with_markup = base_price * (1 + markup / 100)
        final_price = price_with_markup * (1 + iva / 100)
        
        # Construir producto del catálogo
        product_dict = {
            **product.__dict__,
            'final_price': final_price,
            'markup_percentage': markup
        }
        catalog_products.append(CatalogProduct(**product_dict))
    
    return catalog_products


@router.get("/products/{product_id}", response_model=CatalogProduct)
def get_catalog_product(
    product_id: int,
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
        product_id: ID del producto
    
    Returns:
        Producto con precio calculado
    
    Permisos: Solo clientes
    
    Raises:
        403: Si el usuario no es cliente
        400: Si el cliente no tiene lista de precios
        404: Si el producto no existe o no está en la lista
    """
    # === VALIDAR QUE SEA CLIENTE ===
    if not isinstance(current_user, Customer):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Este endpoint es solo para clientes"
        )
    
    # === OBTENER LISTA DE PRECIOS ===
    customer_info = db.query(CustomerInfo).filter(
        CustomerInfo.customer_id == current_user.customer_id
    ).first()
    
    if not customer_info or not customer_info.price_list_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No tienes una lista de precios asignada"
        )
    
    # === BUSCAR PRODUCTO EN LA LISTA ===
    result = db.query(Product, PriceListItem).join(
        PriceListItem,
        Product.product_id == PriceListItem.product_id
    ).options(
        joinedload(Product.category)
    ).filter(
        Product.product_id == product_id,
        PriceListItem.price_list_id == customer_info.price_list_id,
        Product.is_active == True
    ).first()
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Producto no disponible en tu catálogo"
        )
    
    product, price_item = result
    
    # === CALCULAR PRECIO FINAL ===
    base_price = Decimal(str(product.base_price or 0))
    markup = Decimal(str(price_item.markup_percentage or 0))
    iva = Decimal(str(product.iva_percentage or 0))
    
    price_with_markup = base_price * (1 + markup / 100)
    final_price = price_with_markup * (1 + iva / 100)
    
    # Construir respuesta
    product_dict = {
        **product.__dict__,
        'final_price': final_price,
        'markup_percentage': markup
    }
    
    return CatalogProduct(**product_dict)
