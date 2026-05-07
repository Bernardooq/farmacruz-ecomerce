from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from sqlalchemy.exc import IntegrityError

from typing import List, Optional
from datetime import datetime, timezone
from uuid import UUID

from db.base import FavoriteList, FavoriteListItem, Product, CartCache
from schemas.favorite import FavoriteListCreate, FavoriteListUpdate, FavoriteListItemCreate
from crud.crud_cart import add_to_cart

def get_favorite_lists(db: Session, customer_id: int) -> List[FavoriteList]:
    return db.query(FavoriteList).filter(FavoriteList.customer_id == customer_id).all()

def get_favorite_list(db: Session, list_id: UUID, customer_id: int) -> Optional[FavoriteList]:
    return db.query(FavoriteList).filter(
        FavoriteList.list_id == list_id,
        FavoriteList.customer_id == customer_id
    ).first()

def get_favorite_list_details(db: Session, list_id: UUID, customer_id: int, skip: int = 0, limit: int = 15) -> Optional[dict]:
    # Limpiar automáticamente productos inactivos
    db.query(FavoriteListItem).filter(
        FavoriteListItem.list_id == list_id,
        FavoriteListItem.product_id.in_(
            db.query(Product.product_id).filter(Product.is_active == False)
        )
    ).delete(synchronize_session=False)
    db.commit()
    
    # Obtener lista base
    fav_list = get_favorite_list(db, list_id, customer_id)
    if not fav_list:
        return None
        
    # Obtener total de items
    total_items = db.query(func.count(FavoriteListItem.list_item_id)).filter(FavoriteListItem.list_id == list_id).scalar()
    
    # Obtener items paginados
    items = db.query(FavoriteListItem).filter(
        FavoriteListItem.list_id == list_id
    ).offset(skip).limit(limit).all()
    
    # Construir objeto para el schema
    return {
        "list_id": fav_list.list_id,
        "customer_id": fav_list.customer_id,
        "name": fav_list.name,
        "created_at": fav_list.created_at,
        "updated_at": fav_list.updated_at,
        "items": items,
        "total_items": total_items
    }


def create_favorite_list(db: Session, customer_id: int, obj_in: FavoriteListCreate) -> FavoriteList:
    db_obj = FavoriteList(
        customer_id=customer_id,
        name=obj_in.name
    )
    try:
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    except IntegrityError:
        db.rollback()
        raise ValueError(f"Ya tienes una lista llamada '{obj_in.name}'. Por favor elige otro nombre.")

def update_favorite_list(db: Session, list_id: UUID, customer_id: int, obj_in: FavoriteListUpdate) -> Optional[FavoriteList]:
    db_obj = get_favorite_list(db, list_id, customer_id)
    if not db_obj:
        return None
    
    if obj_in.name:
        db_obj.name = obj_in.name
    
    try:
        db_obj.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    except IntegrityError:
        db.rollback()
        raise ValueError(f"Ya tienes una lista llamada '{obj_in.name}'. Por favor elige otro nombre.")


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
    
    try:
        db_item = FavoriteListItem(
            list_id=list_id,
            product_id=item_in.product_id,
            quantity=item_in.quantity
        )
        db.add(db_item)
        db.commit()
        db.refresh(db_item)
        return db_item
    except IntegrityError:
        db.rollback()
        # Si llega aquí es porque otro proceso lo insertó justo antes
        return db.query(FavoriteListItem).filter(
            FavoriteListItem.list_id == list_id,
            FavoriteListItem.product_id == item_in.product_id
        ).first()


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
            prod_name = item.product.name if item.product else item.product_id
            
            # Obtener cantidad actual en carrito para comparar después
            current_cart_item = db.query(CartCache).filter(
                CartCache.customer_id == customer_id,
                CartCache.product_id == item.product_id
            ).first()
            current_qty = current_cart_item.quantity if current_cart_item else 0
            
            # Intentar agregar
            db_cart = add_to_cart(db, customer_id=customer_id, product_id=item.product_id, quantity=item.quantity, cap_at_stock=True)
            
            # Si lo que hay ahora es menos de lo que debería haber (actual + pedido), es que hubo ajuste
            if db_cart.quantity < (current_qty + item.quantity):
                notifications.append(f"⚠️ '{prod_name}': Cantidad ajustada al máximo disponible ({db_cart.quantity}).")
            else:
                notifications.append(f"✅ '{prod_name}' agregado al carrito.")
                
            added_count += 1
        except ValueError as e:
            notifications.append(f"❌ No se pudo agregar '{item.product_id}': {str(e)}")


            
    return {
        "added_count": added_count,
        "notifications": notifications
    }
