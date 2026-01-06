"""
CRUD para Listas de Precios (PriceLists) y sus Items

Sistema de precios con markup por producto:
- PriceList: Contenedor de listas (ej: "Premium", "Distribuidores")
- PriceListItem: Markup específico por producto en cada lista

Flujo típico:
1. Crear PriceList (ej: "Farmacias Premium")
2. Agregar productos con markup (ej: Producto A = 25%, Producto B = 30%)
3. Asignar lista a clientes en CustomerInfo
4. Los clientes ven precios calculados con su markup

El markup se aplica al precio base:
precio_final = (base_price * (1 + markup/100)) * (1 + iva/100)
"""

from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_
from decimal import Decimal

from db.base import PriceList, PriceListItem, Product
from schemas.price_list import (
    PriceListCreate, PriceListUpdate,
    PriceListItemCreate, PriceListItemUpdate
)


# ==========================================
# PRICE LIST (Contenedor de listas)
# ==========================================

def get_price_list(db: Session, price_list_id: int) -> Optional[PriceList]:
    """
    Obtiene una lista de precios por ID
    
    Args:
        db: Sesión de base de datos
        price_list_id: ID de la lista
        
    Returns:
        Lista de precios o None si no existe
    """
    return db.query(PriceList).filter(
        PriceList.price_list_id == price_list_id
    ).first()


def get_price_lists(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    is_active: Optional[bool] = None
) -> List[PriceList]:
    """
    Obtiene todas las listas de precios con filtrado opcional
    
    Args:
        db: Sesión de base de datos
        skip: Registros a saltar (paginación)
        limit: Máximo de registros
        is_active: Filtrar por estado activo (opcional)
        
    Returns:
        Lista de listas de precios
    """
    query = db.query(PriceList)
    
    if is_active is not None:
        query = query.filter(PriceList.is_active == is_active)
    
    return query.offset(skip).limit(limit).all()


def create_price_list(
    db: Session,
    price_list: PriceListCreate
) -> PriceList:
    """
    Crea una nueva lista de precios
    
    El ID puede ser proporcionado por el admin o auto-generado.
    
    Args:
        db: Sesión de base de datos
        price_list: Schema con datos de la lista
        
    Returns:
        Lista de precios creada
    """
    db_price_list = PriceList(
        list_name=price_list.list_name,
        description=price_list.description,
        is_active=price_list.is_active if price_list.is_active is not None else True
    )
    
    # Si se proporciona un ID, usarlo (para sincronización externa)
    if price_list.price_list_id:
        db_price_list.price_list_id = price_list.price_list_id
    
    db.add(db_price_list)
    db.commit()
    db.refresh(db_price_list)
    return db_price_list


def update_price_list(
    db: Session,
    price_list_id: int,
    price_list_update: PriceListUpdate
) -> Optional[PriceList]:
    """
    Actualiza una lista de precios existente
    
    Args:
        db: Sesión de base de datos
        price_list_id: ID de la lista a actualizar
        price_list_update: Campos a actualizar
        
    Returns:
        Lista actualizada o None si no existe
    """
    db_price_list = get_price_list(db, price_list_id)
    if not db_price_list:
        return None
    
    update_data = price_list_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_price_list, field, value)
    
    db.commit()
    db.refresh(db_price_list)
    return db_price_list


def delete_price_list(db: Session, price_list_id: int) -> Optional[PriceList]:
    """
    Elimina una lista de precios (hard delete)
    
    Warning:
        También elimina todos los PriceListItems asociados por CASCADE.
        Los clientes con esta lista quedarán sin precios asignados.
    
    Args:
        db: Sesión de base de datos
        price_list_id: ID de la lista a eliminar
        
    Returns:
        Lista eliminada o None si no existía
    """
    db_price_list = get_price_list(db, price_list_id)
    if db_price_list:
        db.delete(db_price_list)
        db.commit()
    return db_price_list


# ==========================================
# PRICE LIST ITEMS (Markup por producto)
# ==========================================

def get_price_list_items(
    db: Session,
    price_list_id: int
) -> List[PriceListItem]:
    """
    Obtiene todos los items de una lista de precios
    
    Pre-carga información del producto para cada item.
    
    Args:
        db: Sesión de base de datos
        price_list_id: ID de la lista
        
    Returns:
        Lista de items con productos precargados
    """
    return db.query(PriceListItem).options(
        joinedload(PriceListItem.product)
    ).filter(PriceListItem.price_list_id == price_list_id).all()


def get_price_list_item(
    db: Session,
    price_list_id: int,
    product_id: str
) -> Optional[PriceListItem]:
    """
    Obtiene un item específico de una lista de precios
    
    Args:
        db: Sesión de base de datos
        price_list_id: ID de la lista
        product_id: ID del producto
        
    Returns:
        Item encontrado o None si no existe
    """
    return db.query(PriceListItem).filter(
        and_(
            PriceListItem.price_list_id == price_list_id,
            PriceListItem.product_id == product_id
        )
    ).first()


def create_price_list_item(
    db: Session,
    price_list_id: int,
    item: PriceListItemCreate
) -> PriceListItem:
    """
    Crea o actualiza un item en la lista de precios
    
    Si el producto ya existe en la lista, actualiza el markup.
    Si no existe, crea un nuevo item.
    
    Args:
        db: Sesión de base de datos
        price_list_id: ID de la lista
        item: Schema con product_id y markup_percentage
        
    Returns:
        Item creado o actualizado
    """
    # Verificar si ya existe
    existing = get_price_list_item(db, price_list_id, item.product_id)
    
    if existing:
        # Actualizar markup existente
        existing.markup_percentage = item.markup_percentage
        db.commit()
        db.refresh(existing)
        return existing
    else:
        # Crear nuevo item
        db_item = PriceListItem(
            price_list_id=price_list_id,
            product_id=item.product_id,
            markup_percentage=item.markup_percentage
        )
        db.add(db_item)
        db.commit()
        db.refresh(db_item)
        return db_item


def update_price_list_item(
    db: Session,
    price_list_id: int,
    product_id: str,
    item_update: PriceListItemUpdate
) -> Optional[PriceListItem]:
    """
    Actualiza el markup de un producto en la lista
    
    Args:
        db: Sesión de base de datos
        price_list_id: ID de la lista
        product_id: ID del producto
        item_update: Nuevo markup_percentage
        
    Returns:
        Item actualizado o None si no existe
    """
    db_item = get_price_list_item(db, price_list_id, product_id)
    if not db_item:
        return None
    
    db_item.markup_percentage = item_update.markup_percentage
    db.commit()
    db.refresh(db_item)
    return db_item


def delete_price_list_item(
    db: Session,
    price_list_id: int,
    product_id: str
) -> bool:
    """
    Elimina un producto de la lista de precios
    
    Al eliminar, el producto deja de estar disponible
    para clientes con esta lista.
    
    Args:
        db: Sesión de base de datos
        price_list_id: ID de la lista
        product_id: ID del producto a eliminar
        
    Returns:
        True si se eliminó, False si no existía
    """
    db_item = get_price_list_item(db, price_list_id, product_id)
    if db_item:
        db.delete(db_item)
        db.commit()
        return True
    return False


def bulk_update_price_list_items(
    db: Session,
    price_list_id: int,
    items: List[PriceListItemCreate]
) -> List[PriceListItem]:
    """
    Actualización masiva de items de la lista
    
    Crea o actualiza múltiples productos a la vez.
    Útil para importaciones o actualizaciones masivas.
    
    Args:
        db: Sesión de base de datos
        price_list_id: ID de la lista
        items: Lista de items a crear/actualizar
        
    Returns:
        Lista de items creados/actualizados
    """
    result = []
    for item in items:
        db_item = create_price_list_item(db, price_list_id, item)
        result.append(db_item)
    return result


def get_product_markup(
    db: Session,
    price_list_id: int,
    product_id: str
) -> Optional[Decimal]:
    """
    Obtiene SOLO el markup de un producto en una lista
    
    Útil para cálculos rápidos sin cargar todo el item.
    
    Args:
        db: Sesión de base de datos
        price_list_id: ID de la lista
        product_id: ID del producto
        
    Returns:
        Markup percentage como Decimal, o None si no está en la lista
    """
    item = get_price_list_item(db, price_list_id, product_id)
    if item:
        return Decimal(str(item.markup_percentage))
    return None


# ==========================================
# FUNCIONES PARA MODALES (UI)
# ==========================================

def get_products_not_in_price_list(
    db: Session,
    price_list_id: int,
    skip: int = 0,
    limit: int = 10,
    search: Optional[str] = None
) -> List[Product]:
    """
    Obtiene productos que NO están en una lista de precios
    
    Útil para modal de "Agregar Productos" mostrando solo
    productos disponibles para agregar.
    
    Args:
        db: Sesión de base de datos
        price_list_id: ID de la lista
        skip: Registros a saltar
        limit: Máximo de registros
        search: Buscar por nombre o SKU (opcional)
        
    Returns:
        Lista de productos no incluidos en la lista
    """
    # Subquery: IDs de productos YA en la lista
    product_ids_in_list = db.query(PriceListItem.product_id).filter(
        PriceListItem.price_list_id == price_list_id
    ).subquery()
    
    # Query: productos que NO están en esa subquery
    query = db.query(Product).filter(
        ~Product.product_id.in_(product_ids_in_list),
        Product.is_active == True  # Solo productos activos
    )
    
    # Búsqueda opcional
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Product.name.ilike(search_term),
                Product.sku.ilike(search_term)
            )
        )
    
    return query.offset(skip).limit(limit).all()


def get_products_in_price_list_with_details(
    db: Session,
    price_list_id: int,
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None
) -> List[dict]:
    """
    Obtiene productos que SÍ están en una lista con sus detalles
    
    Devuelve producto completo + markup percentage.
    Útil para mostrar tabla de productos con sus markups.
    
    Args:
        db: Sesión de base de datos
        price_list_id: ID de la lista
        skip: Registros a saltar
        limit: Máximo de registros
        search: Buscar por nombre o SKU (opcional)
        
    Returns:
        Lista de dicts con {product, markup_percentage, price_list_item_id}
    """
    # Join entre PriceListItem y Product
    query = db.query(PriceListItem, Product).join(
        Product,
        PriceListItem.product_id == Product.product_id
    ).filter(
        PriceListItem.price_list_id == price_list_id,
        Product.is_active == True
    )
    
    # Búsqueda opcional
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Product.name.ilike(search_term),
                Product.sku.ilike(search_term)
            )
        )
    
    # Ejecutar query con paginación
    results = query.offset(skip).limit(limit).all()
    
    # Formatear resultados
    return [
        {
            "product": product,
            "markup_percentage": float(price_list_item.markup_percentage),
            "price_list_item_id": price_list_item.price_list_item_id
        }
        for price_list_item, product in results
    ]
