from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
from db.base import Order, OrderItem, OrderStatus, Product, CartCache
from schemas.order import OrderCreate, OrderUpdate, OrderItemCreate

def get_order(db: Session, order_id: int) -> Optional[Order]:
    """Obtiene un pedido por ID"""
    return db.query(Order).filter(Order.order_id == order_id).first()

def get_orders_by_user(
    db: Session, 
    user_id: int, 
    skip: int = 0, 
    limit: int = 100,
    status: Optional[OrderStatus] = None
) -> List[Order]:
    """Obtiene los pedidos de un usuario"""
    query = db.query(Order).filter(Order.user_id == user_id)
    
    if status:
        query = query.filter(Order.status == status)
    
    return query.offset(skip).limit(limit).all()

def get_orders(
    db: Session, 
    skip: int = 0, 
    limit: int = 100,
    status: Optional[OrderStatus] = None
) -> List[Order]:
    """Obtiene todos los pedidos (admin/seller)"""
    query = db.query(Order)
    
    if status:
        query = query.filter(Order.status == status)
    
    return query.order_by(Order.created_at.desc()).offset(skip).limit(limit).all()

def create_order_from_cart(db: Session, user_id: int) -> Order:
    """Crea un pedido desde el carrito del usuario"""
    # Obtener items del carrito
    cart_items = db.query(CartCache).filter(CartCache.user_id == user_id).all()
    
    if not cart_items:
        raise ValueError("El carrito está vacío")
    
    # Crear orden
    db_order = Order(
        user_id=user_id,
        status=OrderStatus.pending_validation,
        total_amount=0
    )
    db.add(db_order)
    db.flush()  # Para obtener el order_id
    
    # Crear items de la orden
    total = 0
    for cart_item in cart_items:
        product = db.query(Product).filter(Product.product_id == cart_item.product_id).first()
        
        if not product or not product.is_active:
            continue
        
        if product.stock_count < cart_item.quantity:
            raise ValueError(f"Stock insuficiente para {product.name}")
        
        order_item = OrderItem(
            order_id=db_order.order_id,
            product_id=cart_item.product_id,
            quantity=cart_item.quantity,
            price_at_purchase=product.price
        )
        db.add(order_item)
        
        # Reducir stock
        product.stock_count -= cart_item.quantity
        
        total += float(product.price) * cart_item.quantity
    
    db_order.total_amount = total
    
    # Limpiar carrito
    db.query(CartCache).filter(CartCache.user_id == user_id).delete()
    
    db.commit()
    db.refresh(db_order)
    return db_order

def update_order_status(
    db: Session, 
    order_id: int, 
    status: OrderStatus,
    seller_id: Optional[int] = None
) -> Optional[Order]:
    """Actualiza el estado de un pedido"""
    db_order = get_order(db, order_id)
    if not db_order:
        return None
    
    db_order.status = status
    
    if seller_id and status == OrderStatus.approved:
        db_order.seller_id = seller_id
        db_order.validated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(db_order)
    return db_order

def cancel_order(db: Session, order_id: int) -> Optional[Order]:
    """Cancela un pedido y restaura el stock"""
    db_order = get_order(db, order_id)
    if not db_order:
        return None
    
    # Solo se puede cancelar si está pendiente o aprobado
    if db_order.status not in [OrderStatus.pending_validation, OrderStatus.approved]:
        raise ValueError("No se puede cancelar este pedido")
    
    # Restaurar stock
    for item in db_order.items:
        product = db.query(Product).filter(Product.product_id == item.product_id).first()
        if product:
            product.stock_count += item.quantity
    
    db_order.status = OrderStatus.cancelled
    db.commit()
    db.refresh(db_order)
    return db_order

# --- Cart Cache Functions ---

def get_cart(db: Session, user_id: int) -> List[CartCache]:
    """Obtiene el carrito de un usuario"""
    return db.query(CartCache).filter(CartCache.user_id == user_id).all()

def add_to_cart(db: Session, user_id: int, product_id: int, quantity: int) -> CartCache:
    """Agrega un producto al carrito"""
    product = db.query(Product).filter(Product.product_id == product_id).first()
    
    if not product or not product.is_active:
        raise ValueError("Producto no disponible")
    
    # Verificar si ya existe en el carrito
    cart_item = db.query(CartCache).filter(
        CartCache.user_id == user_id,
        CartCache.product_id == product_id
    ).first()
    
    if cart_item:
        cart_item.quantity += quantity
        cart_item.updated_at = datetime.utcnow()
    else:
        cart_item = CartCache(
            user_id=user_id,
            product_id=product_id,
            quantity=quantity,
            price_at_addition=product.price
        )
        db.add(cart_item)
    
    db.commit()
    db.refresh(cart_item)
    return cart_item

def update_cart_item(db: Session, cart_id: int, quantity: int) -> Optional[CartCache]:
    """Actualiza la cantidad de un item del carrito"""
    cart_item = db.query(CartCache).filter(CartCache.cart_cache_id == cart_id).first()
    
    if cart_item:
        if quantity <= 0:
            db.delete(cart_item)
        else:
            cart_item.quantity = quantity
            cart_item.updated_at = datetime.utcnow()
        db.commit()
    
    return cart_item

def remove_from_cart(db: Session, cart_id: int) -> bool:
    """Elimina un item del carrito"""
    cart_item = db.query(CartCache).filter(CartCache.cart_cache_id == cart_id).first()
    
    if cart_item:
        db.delete(cart_item)
        db.commit()
        return True
    return False

def clear_cart(db: Session, user_id: int) -> bool:
    """Limpia el carrito de un usuario"""
    db.query(CartCache).filter(CartCache.user_id == user_id).delete()
    db.commit()
    return True