"""
Catalogo de Productos para Clientes

Maneja la obtencion de productos con precios personalizados segun la lista
de precios asignada a cada cliente.

Precio final = (precio_base × (1 + markup%)) × (1 + IVA%)
"""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional, Tuple
from decimal import Decimal
from utils.price_utils import get_product_final_price, calculate_final_price_with_markup


from db.base import Customer, CustomerInfo, Product, PriceListItem
# from schemas.product import CatalogProduct  # Ya no se usa, retornamos dict


"""Obtiene el ID de la lista de precios del cliente actual o lanza excepcion si no es cliente o no tiene lista asignada"""
def _get_customer_price_list(current_user, db: Session) -> int:
    # Valida que sea cliente y retorna su price_list_id 
    if not isinstance(current_user, Customer):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo clientes pueden acceder al catalogo"
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

"""Calcula el precio final de un producto aplicando markup (IVA ya incluido en base_price)"""
def _calculate_price(product: Product, price_item: PriceListItem) -> Tuple[Decimal, Decimal]:
    # Retorna (precio_final, markup)
    
    base_price = Decimal(str(product.base_price or 0))
    markup_percentage = Decimal(str(price_item.markup_percentage or 0))
    stored_final_price = Decimal(str(price_item.final_price)) if price_item.final_price else None
    
    final_price = calculate_final_price_with_markup(
        base_price=base_price,
        markup_percentage=markup_percentage,
        stored_final_price=stored_final_price
    )
    
    return final_price, markup_percentage

"""Construye un CatalogProduct desde el ORM Product y precios calculados (sin exponer base_price)"""
def _build_catalog_product(product: Product, final_price: Decimal, markup: Decimal) -> dict:
    # Construye un dict con información de producto SIN base_price para clientes
    # Los clientes SOLO necesitan final_price, no deben ver costos (base_price)
    
    catalog_product_data = {
        'product_id': product.product_id,
        'codebar': product.codebar,
        'name': product.name,
        'description': product.description,
        'descripcion_2': product.descripcion_2,  
        'unidad_medida': product.unidad_medida,  
        # base_price: EXCLUIDO - información sensible
        # iva_percentage: EXCLUIDO - ya está incluido en final_price
        'image_url': product.image_url,
        'stock_count': product.stock_count,
        'is_active': product.is_active,
        'category_id': product.category_id,
        'category': product.category,
        'final_price': final_price,  # ← Precio que el cliente paga
        'markup_percentage': markup  # ← % de ganancia (puede ser útil para el cliente)
    }
    
    return catalog_product_data


# API FUNCTIONS
"""Lista productos del catalogo con precios personalizados del cliente"""
def get_catalog_products(db: Session, current_user, skip: int = 0, limit: int = 50, search: Optional[str] = None, category_id: Optional[int] = None, sort_by: Optional[str] = None, sort_order: Optional[str] = "asc" ) -> List[dict]:    
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
            (Product.descripcion_2.ilike(term)) |
            (Product.codebar.ilike(term))
        )
    
    if category_id:
        query = query.filter(Product.category_id == category_id)
    
    # Aplicar ordenamiento
    if sort_by == "name":
        # Ordenar por nombre
        if sort_order == "desc":
            query = query.order_by(Product.name.desc())
        else:
            query = query.order_by(Product.name.asc())
    else:
        # Orden por defecto: mas recientes primero (product_id descendente)
        query = query.order_by(Product.product_id.desc())
    
    # Ejecutar query con paginacion
    results = query.offset(skip).limit(limit).all()
    
    # Construir lista de productos con precios calculados
    catalog_products = []
    for product, price_item in results:
        final_price, markup = _calculate_price(product, price_item)
        catalog_product = _build_catalog_product(product, final_price, markup)
        catalog_products.append(catalog_product)
    
    return catalog_products

"""Obtiene un producto especifico del catalogo con precio personalizado del cliente"""
def get_catalog_product(db: Session, current_user, product_id: str  ) -> dict:    
    # Obtener lista de precios del cliente
    price_list_id = _get_customer_price_list(current_user, db)
    
    # Buscar producto en la lista del cliente
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
            detail="Producto no disponible en tu catalogo"
        )
    
    # Calcular precio y construir respuesta
    product, price_item = result
    final_price, markup = _calculate_price(product, price_item)
    
    return _build_catalog_product(product, final_price, markup)


"""Obtiene productos del catalogo con precios personalizados de un cliente especifico (para admin/marketing)"""
def get_customer_catalog_products(db: Session, customer_id: int, skip: int = 0, limit: int = 50, search: Optional[str] = None, category_id: Optional[int] = None, sort_by: Optional[str] = None, sort_order: Optional[str] = "asc") -> List[dict]:
    """
    Similar a get_catalog_products pero para un customer_id especifico.
    Usado por admin/marketing al editar pedidos para ver productos con precios del cliente.
    """
    from fastapi import HTTPException, status
    
    # Obtener customer_info y verificar que tenga price_list
    customer_info = db.query(CustomerInfo).filter(
        CustomerInfo.customer_id == customer_id
    ).first()
    
    if not customer_info or not customer_info.price_list_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El cliente no tiene lista de precios asignada"
        )
    
    price_list_id = customer_info.price_list_id
    
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
            (Product.product_id == search) |
            (Product.codebar.ilike(term)) |
            (Product.name.ilike(term)) |
            (Product.description.ilike(term)) |
            (Product.descripcion_2.ilike(term))
        )
    
    if category_id:
        query = query.filter(Product.category_id == category_id)
    
    # Aplicar ordenamiento
    if sort_by == "name":
        if sort_order == "desc":
            query = query.order_by(Product.name.desc())
        else:
            query = query.order_by(Product.name.asc())
    else:
        query = query.order_by(Product.product_id.desc())
    
    # Ejecutar query con paginacion
    results = query.offset(skip).limit(limit).all()
    
    # Construir lista de productos con precios calculados
    catalog_products = []
    for product, price_item in results:
        final_price, markup = _calculate_price(product, price_item)
        catalog_product = _build_catalog_product(product, final_price, markup)
        catalog_products.append(catalog_product)
    
    return catalog_products
