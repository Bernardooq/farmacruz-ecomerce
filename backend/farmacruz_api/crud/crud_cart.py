"""
Funciones para manejar el carrito temporal de clientes:
- Ver items del carrito
- Agregar productos al carrito
- Actualizar cantidades
- Eliminar items
- Vaciar carrito completo
- Obtener conteo de items en el carrito
El carrito se limpia cuando se crea un pedido.
"""

from decimal import Decimal
from typing import List, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from utils.price_utils import get_product_final_price


from db.base import CartCache, CustomerInfo, PriceListItem, Product

"""Obtiene todos los items en el carrito de un cliente con detalles del producto y precios"""
def get_cart(db: Session, customer_id: int) -> List[CartCache]: 
    cart_items = db.query(CartCache).options(
        joinedload(CartCache.product)
    ).filter(
        CartCache.customer_id == customer_id
    ).all()
    
    customer_info = db.query(CustomerInfo).filter(
        CustomerInfo.customer_id == customer_id
    ).first()
    
    # Enriquecer con informacion del producto en formato anidado
    result = []
    for item in cart_items:
        # Obtener precio del producto para este cliente
        final_price = None
        markup_percentage = 0.0
        
        if item.product and customer_info and customer_info.price_list_id:
            
            price_data = get_product_final_price(
                db=db,
                product=item.product,
                price_list_id=customer_info.price_list_id
            )
            
            if price_data:
                final_price = float(price_data["final_price"])
                markup_percentage = float(price_data["markup_percentage"])
        
        # Si no se pudo calcular precio, usar base_price
        if final_price is None and item.product:
            final_price = float(item.product.base_price or 0)
        
        cart_data = {
            "cart_cache_id": item.cart_cache_id,
            "customer_id": item.customer_id,
            "product_id": item.product_id,
            "quantity": item.quantity,
            "added_at": item.added_at,
            "updated_at": item.updated_at,
            "product": {
                "product_id": item.product.product_id,
                "name": item.product.name,
                "codebar": item.product.codebar,
                "base_price": float(item.product.base_price) if item.product.base_price else 0.0,
                "iva_percentage": float(item.product.iva_percentage) if item.product.iva_percentage else 16.0,
                "final_price": final_price,
                "markup_percentage": markup_percentage,
                "image_url": item.product.image_url,
                "stock_count": item.product.stock_count,
                "is_active": item.product.is_active
            } if item.product else None
        }
        result.append(cart_data)
    
    return result

"""Agrega un producto al carrito o incrementa su cantidad si ya existe"""
def add_to_cart(db: Session, customer_id: int, product_id: str, quantity: int = 1) -> CartCache:
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
        if cart_item.quantity + quantity > product.stock_count:
            raise ValueError("Cantidad excede el stock disponible")
        cart_item.quantity += quantity
        cart_item.updated_at = datetime.now(timezone.utc)
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

"""Actualiza la cantidad de un item en el carrito"""
def update_cart_item(db: Session, cart_id: int, quantity: int) -> Optional[CartCache]:
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
        cart_item.updated_at = datetime.now(timezone.utc)
    
    db.commit()
    return cart_item

"""Elimina un item especifico del carrito"""
def remove_from_cart(db: Session, cart_id: int) -> bool:
    cart_item = db.query(CartCache).filter(
        CartCache.cart_cache_id == cart_id
    ).first()
    
    if cart_item:
        db.delete(cart_item)
        db.commit()
        return True
    
    return False

"""Vacía todo el carrito de un cliente"""
def clear_cart(db: Session, customer_id: int) -> int:
    deleted_count = db.query(CartCache).filter(
        CartCache.customer_id == customer_id
    ).delete()
    
    db.commit()
    return deleted_count

"""Obtiene el numero total de items en el carrito de un cliente"""
def get_cart_item_count(db: Session, customer_id: int) -> int:
    return db.query(func.count(CartCache.cart_cache_id)).filter(
        CartCache.customer_id == customer_id
    ).scalar() or 0
