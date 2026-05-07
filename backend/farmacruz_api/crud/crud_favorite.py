from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional
from datetime import datetime, timezone
from uuid import UUID

from db.base import FavoriteList, FavoriteListItem, Product, CartCache
from schemas.favorite import FavoriteListCreate, FavoriteListUpdate, FavoriteListItemCreate
from crud.crud_cart import add_to_cart

def get_favorite_lists(db: Session, customer_id: int) -> List[FavoriteList]:
    return db.query(FavoriteList).filter(FavoriteList.customer_id == customer_id).all()

def get_favorite_list(db: Session, list_id: UUID, customer_id: int) -> Optional[FavoriteList]:
    # Limpiar automáticamente productos inactivos al consultar la lista
    # (Como pidió el usuario: "items se eliminan si se desactiva")
    db.query(FavoriteListItem).filter(
        FavoriteListItem.list_id == list_id,
        FavoriteListItem.product_id.in_(
            db.query(Product.product_id).filter(Product.is_active == False)
        )
    ).delete(synchronize_session=False)
    db.commit()
    
    return db.query(FavoriteList).filter(
        FavoriteList.list_id == list_id,
        FavoriteList.customer_id == customer_id
    ).first()

def create_favorite_list(db: Session, customer_id: int, obj_in: FavoriteListCreate) -> FavoriteList:
    db_obj = FavoriteList(
        customer_id=customer_id,
        name=obj_in.name
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

def update_favorite_list(db: Session, list_id: UUID, customer_id: int, obj_in: FavoriteListUpdate) -> Optional[FavoriteList]:
    db_obj = get_favorite_list(db, list_id, customer_id)
    if not db_obj:
        return None
    
    db_obj.name = obj_in.name
    db_obj.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(db_obj)
    return db_obj

def delete_favorite_list(db: Session, list_id: UUID, customer_id: int) -> bool:
    db_obj = get_favorite_list(db, list_id, customer_id)
    if not db_obj:
        return False
    db.delete(db_obj)
    db.commit()
    return True

# --- Manejo de Items ---

def add_item_to_favorite_list(db: Session, list_id: UUID, customer_id: int, item_in: FavoriteListItemCreate) -> FavoriteListItem:
    # Verificar que la lista pertenezca al cliente
    fav_list = get_favorite_list(db, list_id, customer_id)
    if not fav_list:
        raise ValueError("Lista no encontrada")
    
    # Verificar que el producto exista y esté activo
    product = db.query(Product).filter(Product.product_id == item_in.product_id, Product.is_active == True).first()
    if not product:
        raise ValueError("Producto no disponible")
    
    # Verificar si ya existe en la lista
    existing_item = db.query(FavoriteListItem).filter(
        FavoriteListItem.list_id == list_id,
        FavoriteListItem.product_id == item_in.product_id
    ).first()
    
    if existing_item:
        existing_item.quantity = item_in.quantity # Seteamos la cantidad en lugar de incrementar para listas preestablecidas
        db.commit()
        db.refresh(existing_item)
        return existing_item
    
    db_item = FavoriteListItem(
        list_id=list_id,
        product_id=item_in.product_id,
        quantity=item_in.quantity
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

def remove_item_from_favorite_list(db: Session, list_id: UUID, customer_id: int, product_id: str) -> bool:
    fav_list = get_favorite_list(db, list_id, customer_id)
    if not fav_list:
        return False
        
    db_item = db.query(FavoriteListItem).filter(
        FavoriteListItem.list_id == list_id,
        FavoriteListItem.product_id == product_id
    ).first()
    
    if not db_item:
        return False
        
    db.delete(db_item)
    db.commit()
    return True

def load_favorite_list_to_cart(db: Session, list_id: UUID, customer_id: int) -> dict:
    """
    Carga todos los productos de una lista de favoritos al carrito de compras actual.
    """
    fav_list = get_favorite_list(db, list_id, customer_id)
    if not fav_list:
        raise ValueError("Lista no encontrada")
        
    notifications = []
    added_count = 0
    
    for item in fav_list.items:
        try:
            # Reutilizamos la lógica de add_to_cart que ya valida stock e items existentes
            add_to_cart(db, customer_id=customer_id, product_id=item.product_id, quantity=item.quantity)
            notifications.append(f"'{item.product_name}' agregado al carrito.")
            added_count += 1
        except ValueError as e:
            notifications.append(f"No se pudo agregar '{item.product_name}': {str(e)}")
            
    return {
        "added_count": added_count,
        "notifications": notifications
    }
