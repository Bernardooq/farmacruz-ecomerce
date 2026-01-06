"""
Catálogo de Productos para Clientes

Maneja la obtención de productos con precios personalizados según la lista
de precios asignada a cada cliente.

Precio final = (precio_base × (1 + markup%)) × (1 + IVA%)
"""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional, Tuple
from decimal import Decimal

from db.base import Customer, CustomerInfo, Product, PriceListItem
from schemas.product import CatalogProduct


# HELPERS

def _get_customer_price_list(current_user, db: Session) -> int:
    """Valida que sea cliente y retorna su price_list_id"""
    
    if not isinstance(current_user, Customer):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo clientes pueden acceder al catálogo"
        )
    
    customer_info = db.query(CustomerInfo).filter(
        CustomerInfo.customer_id == current_user.customer_id
    ).first()
    
    if not customer_info or not customer_info.price_list_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No tienes lista de precios. Contacta al administrador"
        )
    
    return customer_info.price_list_id


def _calculate_price(product: Product, price_item: PriceListItem) -> Tuple[Decimal, Decimal]:
    """Calcula precio final aplicando markup e IVA. Retorna (precio_final, markup)"""
    
    base = Decimal(str(product.base_price or 0))
    markup = Decimal(str(price_item.markup_percentage or 0))
    iva = Decimal(str(product.iva_percentage or 0))
    
    # Aplicar markup, luego IVA
    with_markup = base * (1 + markup / 100)
    final = with_markup * (1 + iva / 100)
    
    return final, markup


def _build_catalog_product(product: Product, final_price: Decimal, markup: Decimal) -> CatalogProduct:
    """Construye un CatalogProduct desde el ORM Product"""
    
    return CatalogProduct.model_validate({
        'product_id': product.product_id,
        'sku': product.sku,
        'name': product.name,
        'description': product.description,
        'descripcion_2': product.descripcion_2,  
        'unidad_medida': product.unidad_medida,  
        'base_price': product.base_price,
        'iva_percentage': product.iva_percentage,
        'image_url': product.image_url,
        'stock_count': product.stock_count,
        'is_active': product.is_active,
        'category_id': product.category_id,
        'category': product.category,
        'final_price': final_price,
        'markup_percentage': markup
    })


# API FUNCTIONS

def get_catalog_products(
    db: Session,
    current_user,
    skip: int = 0,
    limit: int = 50,
    search: Optional[str] = None,
    category_id: Optional[int] = None
) -> List[CatalogProduct]:
    """
    Lista productos del catálogo con precios personalizados del cliente
    
    Solo muestra productos activos que estén en la lista de precios del cliente.
    Soporta búsqueda por nombre/descripción/SKU y filtrado por categoría.
    """
    
    # Obtener lista de precios del cliente
    price_list_id = _get_customer_price_list(current_user, db)
    
    # Query base: productos activos en la lista de precios del cliente
    query = db.query(Product, PriceListItem).join(
        PriceListItem,
        Product.product_id == PriceListItem.product_id
    ).options(
        joinedload(Product.category)
    ).filter(
        PriceListItem.price_list_id == price_list_id,
        Product.is_active == True
    )
    
    # Filtros opcionales
    if search:
        term = f"%{search}%"
        query = query.filter(
            (Product.name.ilike(term)) |
            (Product.description.ilike(term)) |
            (Product.sku.ilike(term))
        )
    
    if category_id:
        query = query.filter(Product.category_id == category_id)
    
    # Ejecutar query con paginación
    results = query.order_by(Product.name).offset(skip).limit(limit).all()
    
    # Construir lista de productos con precios calculados
    catalog_products = []
    for product, price_item in results:
        final_price, markup = _calculate_price(product, price_item)
        catalog_product = _build_catalog_product(product, final_price, markup)
        catalog_products.append(catalog_product)
    
    return catalog_products


def get_catalog_product(
    db: Session,
    current_user,
    product_id: str  # Cambiado a str (tipo "FAR74")
) -> CatalogProduct:
    """
    Obtiene un producto específico con su precio personalizado
    
    Valida que el producto exista, esté activo y pertenezca a la
    lista de precios del cliente.
    """
    
    # Obtener lista de precios del cliente
    price_list_id = _get_customer_price_list(current_user, db)
    
    # Buscar producto específico en la lista del cliente
    result = db.query(Product, PriceListItem).join(
        PriceListItem,
        Product.product_id == PriceListItem.product_id
    ).options(
        joinedload(Product.category)
    ).filter(
        Product.product_id == product_id,
        PriceListItem.price_list_id == price_list_id,
        Product.is_active == True
    ).first()
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Producto no disponible en tu catálogo"
        )
    
    # Calcular precio y construir respuesta
    product, price_item = result
    final_price, markup = _calculate_price(product, price_item)
    
    return _build_catalog_product(product, final_price, markup)
