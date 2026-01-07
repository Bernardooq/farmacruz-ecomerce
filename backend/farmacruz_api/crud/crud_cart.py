"""
Funciones para manejar el carrito temporal de clientes:
- Ver items del carrito
- Agregar productos al carrito
- Actualizar cantidades
- Eliminar items
- Vaciar carrito completo

El carrito se limpia cuando se crea un pedido.
"""

from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session, joinedload

from db.base import CartCache, Product

def get_cart(db: Session, customer_id: int) -> List[CartCache]:
    # Obtiene todos los items en el carrito de un cliente
    return db.query(CartCache).options(
        joinedload(CartCache.product)  # Pre-cargar info del producto
    ).filter(CartCache.customer_id == customer_id).all()


def add_to_cart(db: Session, customer_id: int, product_id: str, quantity: int = 1) -> CartCache:
    # Agrega un producto al carrito o incrementa su cantidad si ya existe
    # Validaciones 
    product = db.query(Product).filter(
        Product.product_id == product_id
    ).first()
    
    if not product or not product.is_active:
        raise ValueError("Producto no disponible")
    
    # Verificar si el item ya esta en el carrito
    cart_item = db.query(CartCache).filter(
        CartCache.customer_id == customer_id,
        CartCache.product_id == product_id
    ).first()
    
    if cart_item:
        # Ya existe: incrementar cantidad mientras sea menor o igual al stock
        if cart_item.quantity + quantity > product.stock:
            raise ValueError("Cantidad excede el stock disponible")
        cart_item.quantity += quantity
        cart_item.updated_at = datetime.utcnow()
    else:
        # Nuevo item: crear
        cart_item = CartCache(
            customer_id=customer_id,
            product_id=product_id,
            quantity=quantity
        )
        db.add(cart_item)
    
    db.commit()
    db.refresh(cart_item)
    return cart_item


def update_cart_item(db: Session, cart_id: int, quantity: int) -> Optional[CartCache]:
    # Actualiza la cantidad de un item en el carrito
    cart_item = db.query(CartCache).filter(
        CartCache.cart_cache_id == cart_id
    ).first()
    
    if not cart_item:
        return None
    
    if quantity <= 0:
        # Cantidad invalida: eliminar item
        db.delete(cart_item)
        cart_item = None
    else:
        # Actualizar cantidad y timestamp
        cart_item.quantity = quantity
        cart_item.updated_at = datetime.utcnow()
    
    db.commit()
    return cart_item


def remove_from_cart(db: Session, cart_id: int) -> bool:
    """
    Elimina un item específico del carrito
    
    Args:
        db: Sesión de base de datos
        cart_id: ID del item del carrito a eliminar
        
    Returns:
        True si se eliminó, False si no existía
    """
    cart_item = db.query(CartCache).filter(
        CartCache.cart_cache_id == cart_id
    ).first()
    
    if cart_item:
        db.delete(cart_item)
        db.commit()
        return True
    
    return False


def clear_cart(db: Session, customer_id: int) -> int:
    """
    Vacía completamente el carrito de un cliente
    
    Se usa típicamente después de crear un pedido
    o cuando el cliente quiere empezar de nuevo.
    
    Args:
        db: Sesión de base de datos
        customer_id: ID del cliente dueño del carrito
        
    Returns:
        Número de items eliminados
    """
    deleted_count = db.query(CartCache).filter(
        CartCache.customer_id == customer_id
    ).delete()
    
    db.commit()
    return deleted_count


def get_cart_item_count(db: Session, customer_id: int) -> int:
    """
    Obtiene el número total de items en el carrito
    
    Útil para mostrar un contador en el ícono del carrito
    sin cargar todos los items.
    
    Args:
        db: Sesión de base de datos
        customer_id: ID del cliente
        
    Returns:
        Número de items en el carrito
    """
    from sqlalchemy import func
    
    return db.query(func.count(CartCache.cart_cache_id)).filter(
        CartCache.customer_id == customer_id
    ).scalar() or 0
