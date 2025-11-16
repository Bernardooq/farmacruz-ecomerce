from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from sqlalchemy.orm import Session
from pydantic import BaseModel

from dependencies import get_db, get_current_user, get_current_seller_user, get_current_customer_user
from schemas.order import Order, OrderUpdate
from schemas.cart import CartItem
from db.base import OrderStatus, User
from crud.crud_order import (
    get_order,
    get_orders_by_user,
    get_orders,
    create_order_from_cart,
    update_order_status,
    cancel_order,
    get_cart,
    add_to_cart,
    update_cart_item,
    remove_from_cart,
    clear_cart
)

router = APIRouter()

# --- Carrito de Compras ---

class CartItemAdd(BaseModel):
    product_id: int
    quantity: int = 1

class CartItemUpdate(BaseModel):
    quantity: int

@router.get("/cart")
def read_cart(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtiene el carrito del usuario actual con información de productos
    """
    cart_items = get_cart(db, user_id=current_user.user_id)
    
    # Enriquecer con información del producto en formato anidado
    result = []
    for item in cart_items:
        cart_data = {
            "cart_cache_id": item.cart_cache_id,
            "user_id": item.user_id,
            "product_id": item.product_id,
            "quantity": item.quantity,
            "price_at_addition": float(item.price_at_addition),
            "added_at": item.added_at,
            "updated_at": item.updated_at,
            "product": {
                "product_id": item.product.product_id,
                "name": item.product.name,
                "sku": item.product.sku,
                "price": float(item.product.price),
                "image_url": item.product.image_url,
                "stock_count": item.product.stock_count,
                "is_active": item.product.is_active
            } if item.product else None
        }
        result.append(cart_data)
    
    return result

@router.post("/cart")
def add_item_to_cart(
    item: CartItemAdd,
    current_user: User = Depends(get_current_customer_user),
    db: Session = Depends(get_db)
):
    """
    Agrega un producto al carrito
    """
    try:
        cart_item = add_to_cart(
            db,
            user_id=current_user.user_id,
            product_id=item.product_id,
            quantity=item.quantity
        )
        return cart_item
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.put("/cart/{cart_id}")
def update_cart_item_quantity(
    cart_id: int,
    item: CartItemUpdate,
    current_user: User = Depends(get_current_customer_user),
    db: Session = Depends(get_db)
):
    """
    Actualiza la cantidad de un item en el carrito
    """
    cart_item = update_cart_item(db, cart_id=cart_id, quantity=item.quantity)
    if not cart_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item no encontrado en el carrito"
        )
    return cart_item

@router.delete("/cart/{cart_id}")
def delete_cart_item(
    cart_id: int,
    current_user: User = Depends(get_current_customer_user),
    db: Session = Depends(get_db)
):
    """
    Elimina un item del carrito
    """
    success = remove_from_cart(db, cart_id=cart_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item no encontrado"
        )
    return {"message": "Item eliminado del carrito"}

@router.delete("/cart")
def clear_user_cart(
    current_user: User = Depends(get_current_customer_user),
    db: Session = Depends(get_db)
):
    """
    Limpia el carrito del usuario
    """
    clear_cart(db, user_id=current_user.user_id)
    return {"message": "Carrito limpiado"}

# --- Pedidos ---

@router.post("/checkout", response_model=Order)
def checkout_cart(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Crea un pedido desde el carrito actual
    """
    try:
        order = create_order_from_cart(db, user_id=current_user.user_id)
        return order
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/", response_model=List[Order])
def read_orders(
    skip: int = 0,
    limit: int = 100,
    status: Optional[OrderStatus] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtiene los pedidos del usuario actual
    """
    orders = get_orders_by_user(
        db,
        user_id=current_user.user_id,
        skip=skip,
        limit=limit,
        status=status
    )
    return orders

@router.get("/all", response_model=List[Order])
def read_all_orders(
    skip: int = 0,
    limit: int = 100,
    status: Optional[OrderStatus] = None,
    current_user: User = Depends(get_current_seller_user),
    db: Session = Depends(get_db)
):
    """
    Obtiene todos los pedidos (solo vendedores y administradores)
    """
    orders = get_orders(db, skip=skip, limit=limit, status=status)
    return orders

@router.get("/{order_id}", response_model=Order)
def read_order(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtiene un pedido específico
    """
    order = get_order(db, order_id=order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pedido no encontrado"
        )
    
    # Verificar que el usuario tenga permiso para ver el pedido
    from db.base import UserRole
    if current_user.role not in [UserRole.admin, UserRole.seller]:
        if order.user_id != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene permiso para ver este pedido"
            )
    
    return order

@router.put("/{order_id}/status", response_model=Order)
def update_order_status_route(
    order_id: int,
    order_update: OrderUpdate,
    current_user: User = Depends(get_current_seller_user),
    db: Session = Depends(get_db)
):
    """
    Actualiza el estado de un pedido (solo vendedores y administradores)
    """
    order = update_order_status(
        db,
        order_id=order_id,
        status=order_update.status,
        seller_id=current_user.user_id if order_update.status == OrderStatus.approved else None
    )
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pedido no encontrado"
        )
    
    return order

@router.post("/{order_id}/cancel", response_model=Order)
def cancel_order_route(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Cancela un pedido
    """
    order = get_order(db, order_id=order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pedido no encontrado"
        )
    
    # Solo el cliente o admin/seller pueden cancelar
    from db.base import UserRole
    if current_user.role not in [UserRole.admin, UserRole.seller]:
        if order.user_id != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene permiso para cancelar este pedido"
            )
    
    try:
        cancelled_order = cancel_order(db, order_id=order_id)
        return cancelled_order
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )