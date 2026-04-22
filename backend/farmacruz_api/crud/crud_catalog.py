"""
Catalogo de Productos para Clientes

Maneja la obtencion de productos con precios personalizados segun la lista
de precios asignada a cada cliente.

Precio final = (precio_base × (1 + markup%)) × (1 + IVA%)
"""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_
from typing import List, Optional

from db.base import Customer, CustomerInfo, Product, PriceListItem
from utils.price_utils import calculate_catalog_price, build_catalog_product_dict


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
        search_terms = search.strip().lower().split()
        if search_terms:
            word_filters = []
            for term in search_terms:
                pattern = f"%{term}%"
                word_filters.append(
                    (func.lower(Product.name).ilike(pattern)) |
                    (func.lower(Product.description).ilike(pattern)) |
                    (func.lower(Product.descripcion_2).ilike(pattern)) |
                    (func.lower(Product.codebar).ilike(pattern)) |
                    (Product.product_id.ilike(pattern))
                )
            query = query.filter(and_(*word_filters))
    
    if category_id:
        query = query.filter(Product.category_id == category_id)
    
    # CASO ESPECIAL: Ordenamiento por precio en Python (Middleware Style)
    # Esto asegura 100% de consistencia con las reglas de negocio centralizadas
    if sort_by == "price":
        # Traer todos los resultados filtrados para ordenar el set completo
        all_results = query.all()
        
        catalog_products = []
        for product, price_item in all_results:
            final_price = calculate_catalog_price(product, price_item)
            catalog_products.append(build_catalog_product_dict(product, final_price))
            
        # Ordenar lista en memoria
        catalog_products.sort(
            key=lambda x: x['final_price'], 
            reverse=(sort_order == "desc")
        )
        
        # Aplicar paginacion manual
        return catalog_products[skip : skip + limit]
    
    # OTROS CASOS: Ordenamiento en SQL (más eficiente para nombres/IDs)
    if sort_by == "name":
        query = query.order_by(Product.name.desc() if sort_order == "desc" else Product.name.asc())
    else:
        query = query.order_by(Product.product_id.desc())
    
    # Ejecutar query con paginacion
    results = query.offset(skip).limit(limit).all()
    
    # Construir lista usando las utilidades estandarizadas
    return [
        build_catalog_product_dict(product, calculate_catalog_price(product, price_item))
        for product, price_item in results
    ]

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
    
    product, price_item = result
    final_price = calculate_catalog_price(product, price_item)
    return build_catalog_product_dict(product, final_price)


"""Obtiene productos del catalogo con precios personalizados de un cliente especifico (para admin/marketing)"""
def get_customer_catalog_products(db: Session, customer_id: int, skip: int = 0, limit: int = 50, search: Optional[str] = None, category_id: Optional[int] = None, sort_by: Optional[str] = None, sort_order: Optional[str] = "asc") -> List[dict]:
    """
    Similar a get_catalog_products pero para un customer_id especifico.
    Usado por admin/marketing al editar pedidos para ver productos con precios del cliente.
    """
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
    
    # Filtros opcionales (mismo que get_catalog_products)
    if search:
        search_terms = search.strip().lower().split()
        if search_terms:
            word_filters = []
            for term in search_terms:
                pattern = f"%{term}%"
                word_filters.append(
                    (func.lower(Product.name).ilike(pattern)) |
                    (func.lower(Product.description).ilike(pattern)) |
                    (func.lower(Product.descripcion_2).ilike(pattern)) |
                    (func.lower(Product.codebar).ilike(pattern)) |
                    (Product.product_id.ilike(pattern))
                )
            query = query.filter(and_(*word_filters))
    
    if category_id:
        query = query.filter(Product.category_id == category_id)
    
    # Aplicar lógica de ordenamiento (Middleware Style)
    if sort_by == "price":
        all_results = query.all()
        catalog_products = []
        for product, price_item in all_results:
            final_price = calculate_catalog_price(product, price_item)
            catalog_products.append(build_catalog_product_dict(product, final_price))
            
        catalog_products.sort(key=lambda x: x['final_price'], reverse=(sort_order == "desc"))
        return catalog_products[skip : skip + limit]
    
    if sort_by == "name":
        query = query.order_by(Product.name.desc() if sort_order == "desc" else Product.name.asc())
    else:
        query = query.order_by(Product.product_id.desc())
        
    results = query.offset(skip).limit(limit).all()
    
    return [
        build_catalog_product_dict(product, calculate_catalog_price(product, price_item))
        for product, price_item in results
    ]
