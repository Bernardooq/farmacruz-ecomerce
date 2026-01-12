"""
Routes para Gestion de Pedidos y Carrito

Endpoints para el ciclo completo de pedidos:

CARRITO (Clientes):
- GET /cart - Ver carrito
- POST /cart - Agregar producto
- PUT /cart/{id} - Actualizar cantidad
- DELETE /cart/{id} - Eliminar item
- DELETE /cart - Vaciar carrito

PEDIDOS (Clientes):
- POST /checkout - Crear pedido desde carrito
- GET / - Ver mis pedidos
- GET /{id} - Ver detalle de pedido
- POST /{id}/cancel - Cancelar pedido

PEDIDOS (Admin/Marketing/Seller):
- GET /all - Ver todos los pedidos (segun permisos)
- PUT /{id}/status - Actualizar estado
- POST /{id}/assign - Asignar vendedor

Sistema de Permisos:
- Clientes: Solo sus propios pedidos
- Sellers: Pedidos asignados a ellos
- Marketing: Pedidos de clientes en sus grupos
- Admin: Todos los pedidos
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from sqlalchemy.orm import Session
from pydantic import BaseModel
from uuid import UUID

from dependencies import get_db, get_current_user, get_current_seller_user
from crud.crud_customer import get_customer_info
from crud.crud_user import get_user
from schemas.order import Order, OrderUpdate, OrderWithAddress, OrderAssign
from schemas.cart import CartItem
from db.base import OrderStatus, User

from crud.crud_order import (
    assign_order_seller,
    calculate_order_shipping_address,
    get_order,
    get_orders_by_customer,
    get_orders,
    get_orders_for_user_groups,
    create_order_from_cart,
    update_order_status,
    cancel_order
)

from crud.crud_cart import (
    get_cart,
    add_to_cart,
    update_cart_item,
    remove_from_cart,
    clear_cart
)

from crud.crud_sales_group import user_can_manage_order

router = APIRouter()

# === CARRITO DE COMPRAS ===

class CartItemAdd(BaseModel):
    product_id: str 
    quantity: int = 1

class CartItemUpdate(BaseModel):
    quantity: int

@router.get("/cart")
def read_cart(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtiene el carrito del usuario actual con informacion de productos
    """
    from db.base import Customer
    
    # Get customer_id based on user type
    if isinstance(current_user, Customer):
        customer_id = current_user.customer_id
    else:
        # For backwards compatibility with old User-based customers
        customer_id = getattr(current_user, 'user_id', None)
    
    if not customer_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se pudo identificar el cliente"
        )
    
    cart_items = get_cart(db, customer_id=customer_id)
    
    # Get customer's price list to calculate final prices
    from db.base import Customer, CustomerInfo, PriceListItem
    from decimal import Decimal
    
    customer_info = db.query(CustomerInfo).filter(
        CustomerInfo.customer_id == customer_id
    ).first()
    
    # Enriquecer con informacion del producto en formato anidado
    result = []
    for item in cart_items:
        # Calculate final price based on customer's price list
        final_price = None
        markup_percentage = 0.0
        
        if customer_info and customer_info.price_list_id and item.product:
            # Get markup from price list
            price_item = db.query(PriceListItem).filter(
                PriceListItem.price_list_id == customer_info.price_list_id,
                PriceListItem.product_id == item.product_id
            ).first()
            
            if price_item:
                base_price = Decimal(str(item.product.base_price or 0))
                markup = Decimal(str(price_item.markup_percentage or 0))
                iva = Decimal(str(item.product.iva_percentage or 0))
                
                price_with_markup = base_price * (1 + markup / 100)
                final_price = float(price_with_markup * (1 + iva / 100))
                markup_percentage = float(markup)
        
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

@router.post("/cart")
def add_item_to_cart(
    item: CartItemAdd,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    from db.base import Customer
    
    # Get customer_id based on user type
    if isinstance(current_user, Customer):
        customer_id = current_user.customer_id
    else:
        customer_id = getattr(current_user, 'user_id', None)
    
    if not customer_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se pudo identificar el cliente"
        )
    
    try:
        cart_item = add_to_cart(
            db,
            customer_id=customer_id,
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
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Actualiza la cantidad de un producto en el carrito.
    Si quantity <= 0, el item se elimina del carrito.
    """
    from db.base import Customer
    
    # Get customer_id based on user type
    if isinstance(current_user, Customer):
        customer_id = current_user.customer_id
    else:
        customer_id = getattr(current_user, 'user_id', None)
    
    if not customer_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se pudo identificar el cliente"
        )
    
    cart_item = update_cart_item(
        db,
        cart_id=cart_id,
        quantity=item.quantity
    )
    
    # Si quantity <= 0, el item se elimino correctamente
    if cart_item is None:
        return {"message": "Item eliminado del carrito", "deleted": True}
    
    return cart_item

@router.delete("/cart/{cart_id}")
def delete_cart_item(
    cart_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Elimina un item del carrito
    success = remove_from_cart(db, cart_id=cart_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item no encontrado"
        )
    return {"message": "Item eliminado del carrito"}

@router.delete("/cart")
def clear_user_cart(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Limpia el carrito del usuario
    from db.base import Customer
    
    # Get customer_id based on user type
    if isinstance(current_user, Customer):
        customer_id = current_user.customer_id
    else:
        customer_id = getattr(current_user, 'user_id', None)
    
    if not customer_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se pudo identificar el cliente"
        )
    
    clear_cart(db, customer_id=customer_id)
    return {"message": "Carrito limpiado"}

# --- Pedidos ---

class CheckoutRequest(BaseModel):
    shipping_address_number: int = 1  # Default to address 1

@router.post("/checkout", response_model=Order)
def checkout_cart(
    checkout_data: CheckoutRequest,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Crea un pedido desde el carrito actual
    Calcula precios en el servidor basandose en la lista de precios del cliente
    """
    from db.base import Customer
    
    # Get customer_id based on user type
    if isinstance(current_user, Customer):
        customer_id = current_user.customer_id
    else:
        customer_id = getattr(current_user, 'user_id', None)
    
    if not customer_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se pudo identificar el cliente"
        )
    
    try:
        order = create_order_from_cart(
            db, 
            customer_id=customer_id,
            shipping_address_number=checkout_data.shipping_address_number
        )
        return order
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/", response_model=List[OrderWithAddress])
def read_orders(
    skip: int = 0,
    limit: int = 100,
    status: Optional[OrderStatus] = None,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtiene los pedidos del usuario actual
    """
    from db.base import Customer, CustomerInfo
    
    # Get customer_id based on user type
    if isinstance(current_user, Customer):
        customer_id = current_user.customer_id
    else:
        customer_id = getattr(current_user, 'user_id', None)
    
    if not customer_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se pudo identificar el cliente"
        )
    
    orders = get_orders_by_customer(
        db,
        customer_id=customer_id,
        skip=skip,
        limit=limit,
        status=status
    )
    
    # Calculate shipping_address for each order
    customer_info = db.query(CustomerInfo).filter(
        CustomerInfo.customer_id == customer_id
    ).first()
    
    for order in orders:
        if order.shipping_address_number and customer_info:
            address_key = f"address_{order.shipping_address_number}"
            shipping_address = getattr(customer_info, address_key, None)
            
            if not shipping_address:
                # Fallback to address_1
                shipping_address = customer_info.address_1 or customer_info.address_2 or customer_info.address_3
            
            order.shipping_address = shipping_address or "No especificada"
        else:
            order.shipping_address = "No especificada"
    
    return orders

@router.get("/all", response_model=List[Order])
def read_all_orders(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,  # Changed to str to accept "assigned"
    search: Optional[str] = None,
    current_user: User = Depends(get_current_seller_user),
    db: Session = Depends(get_db)
):
    # Obtiene todos los pedidos filtrados segun los grupos del usuario
    # Convertir status a OrderStatus si es válido, o None si es "assigned"
    order_status = None
    status_filter = None
    
    if status:
        if status == "assigned":
            status_filter = "assigned"
        else:
            try:
                order_status = OrderStatus(status)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Status inválido: {status}"
                )
    
    orders = get_orders_for_user_groups(
        db=db,
        user_id=current_user.user_id,
        user_role=current_user.role,
        skip=skip,
        limit=limit,
        status=order_status,
        status_filter=status_filter,
        search=search
    )
    return orders

@router.get("/{order_id}", response_model=OrderWithAddress)
def read_order(
    order_id: UUID,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Obtiene un pedido especifico
    order = get_order(db, order_id=order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pedido no encontrado"
        )
    
    # Verificar permisos
    from db.base import UserRole, Customer
    
    # Get current user's identifier
    if isinstance(current_user, Customer):
        current_user_id = current_user.customer_id
        user_role = None
    else:
        current_user_id = current_user.user_id
        user_role = current_user.role
    
    # Si es el cliente dueño del pedido, puede verlo
    if order.customer_id == current_user_id:
        pass  # Permitir
    # Si es marketing/seller/admin, verificar permisos por grupo
    elif user_role and user_role in [UserRole.admin, UserRole.seller, UserRole.marketing]:
        if not user_can_manage_order(db, current_user_id, order.customer_id, user_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene permiso para ver este pedido"
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permiso para ver este pedido"
        )
    
    # Calculate shipping address
    return calculate_order_shipping_address(db, order)

@router.put("/{order_id}/status", response_model=Order)
def update_order_status_route(
    order_id: UUID,
    order_update: OrderUpdate,
    current_user: User = Depends(get_current_seller_user),
    db: Session = Depends(get_db)
):
    # Actualiza el estado de un pedido con validacion de transiciones.
    
    # Obtener el pedido actual
    order = get_order(db, order_id=order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pedido no encontrado"
        )
    
    from db.base import UserRole
    is_admin = current_user.role == UserRole.admin
    
    # Verificar permisos por grupo (si no es admin)
    if not is_admin:
        if not user_can_manage_order(db, current_user.user_id, order.customer_id, current_user.role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene permiso para gestionar este pedido. El cliente no pertenece a sus grupos."
            )
    
    current_status = order.status
    new_status = order_update.status
    
    # Definir el flujo valido de estados
    # pending_validation -> approved -> shipped -> delivered
    # Solo admin puede cancelar despues de pending_validation
    
    # Transiciones base (sin cancelacion)
    valid_transitions = {
        OrderStatus.pending_validation: [OrderStatus.approved],  # Puede asignarse o aprobarse directamente
        OrderStatus.approved: [OrderStatus.shipped],
        OrderStatus.shipped: [OrderStatus.delivered],
        OrderStatus.delivered: [],  # Estado final, no se puede cambiar
        OrderStatus.cancelled: []   # Estado final, no se puede cambiar
    }
    
    # Agregar opcion de cancelar segun el rol y estado
    if new_status == OrderStatus.cancelled:
        if current_status == OrderStatus.delivered:
            # Nadie puede cancelar un pedido entregado
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se puede cancelar un pedido que ya ha sido entregado"
            )
        elif current_status == OrderStatus.pending_validation:
            # Cualquiera (seller/admin) puede cancelar en pending_validation
            valid_transitions[OrderStatus.pending_validation].append(OrderStatus.cancelled)
        elif current_status in [OrderStatus.approved, OrderStatus.shipped]:
            # Solo admin puede cancelar despues de pending_validation
            if is_admin:
                valid_transitions[current_status].append(OrderStatus.cancelled)
            else:
                status_labels = {
                    OrderStatus.approved: "aprobado",
                    OrderStatus.shipped: "enviado"
                }
                current_label = status_labels.get(current_status, current_status.value)
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Solo los administradores pueden cancelar pedidos que ya han sido {current_label}"
                )
    
    # Validar que la transicion sea valida
    if new_status not in valid_transitions.get(current_status, []):
        status_labels = {
            OrderStatus.pending_validation: "Pendiente de Validacion",
            OrderStatus.approved: "Aprobado",
            OrderStatus.shipped: "Enviado",
            OrderStatus.delivered: "Entregado",
            OrderStatus.cancelled: "Cancelado"
        }
        
        current_label = status_labels.get(current_status, current_status.value)
        new_label = status_labels.get(new_status, new_status.value)
        
        # Mensajes especificos para casos comunes
        if current_status == OrderStatus.delivered:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se puede modificar un pedido que ya ha sido entregado"
            )
        elif current_status == OrderStatus.cancelled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se puede modificar un pedido que ya ha sido cancelado"
            )
        elif current_status == OrderStatus.shipped and new_status == OrderStatus.approved:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se puede regresar un pedido de 'Enviado' a 'Aprobado'. El pedido ya esta en transito."
            )
        elif current_status == OrderStatus.approved and new_status == OrderStatus.pending_validation:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se puede regresar un pedido de 'Aprobado' a 'Pendiente'. El pedido ya fue validado."
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Transicion de estado invalida: no se puede cambiar de '{current_label}' a '{new_label}'"
            )
    
    # Si la validacion pasa, actualizar el estado
    updated_order = update_order_status(
        db,
        order_id=order_id,
        status=new_status,
        seller_id=current_user.user_id if new_status == OrderStatus.approved else None
    )
    
    return updated_order

@router.post("/{order_id}/assign", response_model=Order)
def assign_order_to_seller(
    order_id: UUID,
    assign_data: OrderAssign,
    current_user: User = Depends(get_current_seller_user),
    db: Session = Depends(get_db)
):
    # Asigna un vendedor a un pedido.
    from db.base import UserRole
    from datetime import datetime
    
    # Obtener la orden
    order = get_order(db, order_id=order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pedido no encontrado"
        )
    
    # Verificar que la orden NO este cancelada o entregada
    if order.status in [OrderStatus.cancelled, OrderStatus.delivered]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No se puede asignar un pedido en estado '{order.status.value}'."
        )
    
    # Obtener el vendedor a asignar
    seller = get_user(db, assign_data.assigned_seller_id)
    if not seller:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vendedor no encontrado"
        )
    
    # Verificar que el usuario a asignar sea un vendedor
    if seller.role != UserRole.seller:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El usuario seleccionado no es un vendedor (rol: {seller.role.value})"
        )
    
    # Verificar permisos segun el rol del usuario que asigna
    from crud.crud_sales_group import get_user_groups
    from db.base import CustomerInfo
    
    # Obtener el grupo del cliente del pedido
    customer_info = get_customer_info(db, order.customer_id)
    
    if not customer_info or not customer_info.sales_group_id:
        # Cliente sin grupo - solo admin puede gestionar, pero no puede asignar
        # porque no hay vendedores disponibles sin grupo
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El cliente no pertenece a ningun grupo de ventas. Asigne el cliente a un grupo primero."
        )
    
    customer_group_id = customer_info.sales_group_id
    
    # Obtener los grupos del vendedor a asignar
    seller_groups = get_user_groups(db, seller.user_id)
    
    # Verificar que el vendedor pertenezca al mismo grupo que el cliente
    if customer_group_id not in seller_groups:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No puede asignar este vendedor. El vendedor no pertenece al grupo de ventas del cliente."
        )
    
    # Si es marketing, verificar permisos adicionales
    if current_user.role == UserRole.marketing:
        # Marketing solo puede asignar pedidos de clientes en sus grupos
        if not user_can_manage_order(db, current_user.user_id, order.customer_id, current_user.role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene permiso para asignar este pedido. El cliente no pertenece a sus grupos."
            )
        
        # Marketing solo puede asignar a vendedores de sus grupos
        marketing_groups = get_user_groups(db, current_user.user_id)
        
        if not any(group in seller_groups for group in marketing_groups):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No puede asignar a este vendedor. El vendedor no pertenece a sus grupos."
            )
    # Admin puede asignar pedidos de cualquier grupo, pero debe respetar la regla de grupos    
    return assign_order_seller(db, order, assign_data, current_user)

@router.post("/{order_id}/cancel", response_model=Order)
def cancel_order_route(
    order_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Cancela un pedido.
    order = get_order(db, order_id=order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pedido no encontrado"
        )
    
    from db.base import UserRole, Customer
    
    # Get current user's identifier
    if isinstance(current_user, Customer):
        current_user_id = current_user.customer_id
        is_customer = True
        user_role = None  # Customers don't have roles
    else:
        current_user_id = current_user.user_id
        is_customer = False
        user_role = current_user.role
    
    # Verificar permisos
    is_owner = order.customer_id == current_user_id
    is_admin = user_role == UserRole.admin if user_role else False
    
    # Si es el cliente dueño, puede cancelar
    if is_owner:
        pass  # Permitir, validaciones de estado mas abajo
    # Si es marketing/seller/admin, verificar permisos por grupo
    elif user_role and user_role in [UserRole.admin, UserRole.seller, UserRole.marketing]:
        if not user_can_manage_order(db, current_user_id, order.customer_id, user_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene permiso para cancelar este pedido. El cliente no pertenece a sus grupos."
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permiso para cancelar este pedido"
        )
    
    # VALIDACIoN CRiTICA: Verificar si se puede cancelar segun el estado y rol
    
    # No se puede cancelar si ya esta cancelado
    if order.status == OrderStatus.cancelled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Este pedido ya esta cancelado"
        )
    
    # No se puede cancelar si ya esta entregado
    if order.status == OrderStatus.delivered:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se puede cancelar un pedido que ya ha sido entregado"
        )
    
    # Validación basada en rol
    if is_customer:
        # Los clientes solo pueden cancelar antes de que sea validado
        if order.status != OrderStatus.pending_validation:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Los clientes solo pueden cancelar pedidos pendientes de validación"
            )
    elif user_role in [UserRole.marketing, UserRole.seller]:
        # Marketing y Seller pueden cancelar antes de enviado
        if order.status == OrderStatus.shipped:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Marketing y Vendedores solo pueden cancelar pedidos antes de que sean enviados"
            )
    elif is_admin:
        # Admin puede cancelar hasta antes de entregado (ya validado arriba)
        pass
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para cancelar este pedido"
        )
    
    try:
        cancelled_order = cancel_order(db, order_id=order_id)
        return cancelled_order
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
