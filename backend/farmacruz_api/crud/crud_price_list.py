"""
CRUD para Listas de Precios (PriceLists) y sus Items

Sistema de precios con markup por producto:
- PriceList: Contenedor de listas (ej: "Premium", "Distribuidores")
- PriceListItem: Markup especifico por producto en cada lista

Flujo tipico:
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


def get_price_list(db: Session, price_list_id: int) -> Optional[PriceList]:
    # Obtiene una lista de precios por ID
    return db.query(PriceList).filter(
        PriceList.price_list_id == price_list_id
    ).first()


def get_price_lists(db: Session, skip: int = 0, limit: int = 100, is_active: Optional[bool] = None) -> List[PriceList]:
    # Obtiene todas las listas de precios con filtrado opcional
    
    query = db.query(PriceList)
    
    if is_active is not None:
        query = query.filter(PriceList.is_active == is_active)
    
    return query.offset(skip).limit(limit).all()


def create_price_list(db: Session, price_list: PriceListCreate) -> PriceList:
    # Crea una nueva lista de precios
    
    db_price_list = PriceList(
        list_name=price_list.list_name,
        description=price_list.description,
        is_active=price_list.is_active if price_list.is_active is not None else True
    )
    
    # Si se proporciona un ID, usarlo (para sincronizacion externa)
    if price_list.price_list_id:
        db_price_list.price_list_id = price_list.price_list_id
    
    db.add(db_price_list)
    db.commit()
    db.refresh(db_price_list)
    return db_price_list


def update_price_list(db: Session, price_list_id: int, price_list_update: PriceListUpdate) -> Optional[PriceList]:
    # Actualiza una lista de precios existente
    
    db_price_list = get_price_list(db, price_list_id)
    if not db_price_list:
        return None
    
    update_data = price_list_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_price_list, field, value)
    
    db.commit()
    db.refresh(db_price_list)
    return db_price_list


def delete_price_list(db: Session, price_list_id: int) -> Optional[PriceList]:
    # Elimina una lista de precios (hard delete)
    db_price_list = get_price_list(db, price_list_id)
    if db_price_list:
        db.delete(db_price_list)
        db.commit()
    return db_price_list


def get_price_list_items(db: Session, price_list_id: int) -> List[PriceListItem]:
    # Obtiene todos los items de una lista de precios
    
    return db.query(PriceListItem).options(
        joinedload(PriceListItem.product)
    ).filter(PriceListItem.price_list_id == price_list_id).all()


def get_price_list_item(db: Session, price_list_id: int, product_id: str) -> Optional[PriceListItem]:
    # Obtiene un item especifico de una lista de precios

    return db.query(PriceListItem).filter(
        and_(
            PriceListItem.price_list_id == price_list_id,
            PriceListItem.product_id == product_id
        )
    ).first()


def create_price_list_item(db: Session, price_list_id: int, item: PriceListItemCreate) -> PriceListItem:
    # Crea o actualiza un item en la lista de precios
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


def update_price_list_item(db: Session, price_list_id: int, product_id: str, item_update: PriceListItemUpdate) -> Optional[PriceListItem]:
    # Actualiza el markup de un producto en la lista
    
    db_item = get_price_list_item(db, price_list_id, product_id)
    if not db_item:
        return None
    
    db_item.markup_percentage = item_update.markup_percentage
    db.commit()
    db.refresh(db_item)
    return db_item


def delete_price_list_item(db: Session, price_list_id: int, product_id: str) -> bool:
    # Elimina un producto de la lista de precios
    
    db_item = get_price_list_item(db, price_list_id, product_id)
    if db_item:
        db.delete(db_item)
        db.commit()
        return True
    return False


def bulk_update_price_list_items(db: Session, price_list_id: int, items: List[PriceListItemCreate]) -> List[PriceListItem]:
    # Actualizacion masiva de items de la lista

    result = []
    for item in items:
        db_item = create_price_list_item(db, price_list_id, item)
        result.append(db_item)
    return result


def get_product_markup(db: Session, price_list_id: int, product_id: str) -> Optional[Decimal]:
    # Obtiene SOLO el markup de un producto en una lista
    item = get_price_list_item(db, price_list_id, product_id)
    if item:
        return Decimal(str(item.markup_percentage))
    return None


def get_products_not_in_price_list(db: Session, price_list_id: int, skip: int = 0, limit: int = 10, search: Optional[str] = None) -> List[Product]:
    # Obtiene productos que NO estan en una lista de precios
    # Subquery: IDs de productos YA en la lista
    product_ids_in_list = db.query(PriceListItem.product_id).filter(
        PriceListItem.price_list_id == price_list_id
    ).subquery()
    
    # Query: productos que NO estan en esa subquery
    query = db.query(Product).filter(
        ~Product.product_id.in_(product_ids_in_list),
        Product.is_active == True  # Solo productos activos
    )
    
    # Busqueda opcional
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Product.name.ilike(search_term),
                Product.codebar.ilike(search_term)
            )
        )
    
    return query.offset(skip).limit(limit).all()


def get_products_in_price_list_with_details(db: Session, price_list_id: int, skip: int = 0, limit: int = 100, search: Optional[str] = None) -> List[dict]:
    # Obtiene productos que Si estan en una lista con sus detalles
    # Join entre PriceListItem y Product
    query = db.query(PriceListItem, Product).join(
        Product,
        PriceListItem.product_id == Product.product_id
    ).filter(
        PriceListItem.price_list_id == price_list_id,
        Product.is_active == True
    )
    
    # Busqueda opcional
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Product.name.ilike(search_term),
                Product.codebar.ilike(search_term)
            )
        )
    
    # Ejecutar query con paginacion
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
