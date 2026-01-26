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

from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from sqlalchemy.orm import Session
from pydantic import BaseModel
from uuid import UUID

from dependencies import get_db, get_current_user, get_current_seller_user
from crud.crud_customer import get_customer_info
from crud.crud_user import get_user
from schemas.order import Order, OrderUpdate, OrderWithAddress, OrderAssign
from schemas.order_edit import OrderEditRequest
from schemas.cart import CartItem
from db.base import OrderStatus, User, UserRole, Customer, CustomerInfo, PriceListItem

from crud.crud_order import (assign_order_seller, calculate_order_shipping_address, get_order, get_orders_by_customer, get_orders, 
    get_orders_for_user_groups, create_order_from_cart, update_order_status, cancel_order, generate_order_txt)

from crud.crud_order_edit import edit_order_items

from crud.crud_cart import (get_cart, add_to_cart, update_cart_item, remove_from_cart, clear_cart)

from crud.crud_sales_group import get_user_groups, user_can_manage_order

router = APIRouter()

# === CARRITO DE COMPRAS ===

class CartItemAdd(BaseModel):
    product_id: str 
    quantity: int = 1

class CartItemUpdate(BaseModel):
    quantity: int

""" GET /cart - Ver carrito por el cliente autenticado """
@router.get("/cart")
def read_cart(current_user = Depends(get_current_user), db: Session = Depends(get_db)):    
    if isinstance(current_user, Customer):
        customer_id = current_user.customer_id
    else:
        customer_id = getattr(current_user, 'user_id', None)
    
    if not customer_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se pudo identificar el cliente"
        )
    
    cart_items = get_cart(db, customer_id=customer_id)
    return cart_items

""" POST /cart - Agregar producto al carrito """
@router.post("/cart")
def add_item_to_cart(item: CartItemAdd, current_user = Depends(get_current_user), db: Session = Depends(get_db)):    
    if isinstance(current_user, Customer):
        customer_id = current_user.customer_id
    else:
        customer_id = getattr(current_user, 'user_id', None)
    
    if not customer_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No se pudo identificar el cliente")
    
    try:
        cart_item = add_to_cart(db, customer_id=customer_id, product_id=item.product_id, quantity=item.quantity)
        return cart_item
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

""" PUT /cart/{id} - Actualizar cantidad de un item en el carrito """
@router.put("/cart/{cart_id}")
def update_cart_item_quantity(cart_id: int, item: CartItemUpdate, current_user = Depends(get_current_user),
    db: Session = Depends(get_db)):
    """
    Actualiza la cantidad de un producto en el carrito.
    Si quantity <= 0, el item se elimina del carrito.
    """    
    if isinstance(current_user, Customer):
        customer_id = current_user.customer_id
    else:
        customer_id = getattr(current_user, 'user_id', None)
    
    if not customer_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se pudo identificar el cliente"
        )

    cart_item = update_cart_item(db, cart_id=cart_id, quantity=item.quantity)
    if cart_item is None and item.quantity > 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item no encontrado en el carrito")
    
    if cart_item is None:
        return {"message": "Item eliminado del carrito"}
    return cart_item

""" DELETE /cart/{id} - Eliminar item del carrito """
@router.delete("/cart/{cart_id}")
def delete_cart_item(cart_id: int, current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)):
    # Elimina un item del carrito
    success = remove_from_cart(db, cart_id=cart_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item no encontrado")
    return {"message": "Item eliminado del carrito"}

""" DELETE /cart - Vaciar carrito """
@router.delete("/cart")
def clear_user_cart(current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    # Limpia el carrito del usuario    
    if isinstance(current_user, Customer):
        customer_id = current_user.customer_id
    else:
        customer_id = getattr(current_user, 'user_id', None)
    
    if not customer_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No se pudo identificar el cliente")

    clear_cart(db, customer_id=customer_id)
    return {"message": "Carrito limpiado"}

# --- Pedidos ---
class CheckoutRequest(BaseModel):
    shipping_address_number: int = 1  # Default to address 1

""" POST /checkout - Crear pedido desde el carrito """
@router.post("/checkout", response_model=Order)
def checkout_cart(checkout_data: CheckoutRequest,
    current_user = Depends(get_current_user), db: Session = Depends(get_db)):

    # Get customer_id based on user type
    if isinstance(current_user, Customer):
        customer_id = current_user.customer_id
    else:
        customer_id = getattr(current_user, 'user_id', None)
    
    if not customer_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No se pudo identificar el cliente")
    
    try:
        order = create_order_from_cart(db, customer_id=customer_id, shipping_address_number=checkout_data.shipping_address_number)
        return order
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail=str(e))

""" GET / - Ver mis pedidos """
@router.get("/", response_model=List[OrderWithAddress])
def read_orders(
    skip: int = 0,limit: int = 100, status: Optional[OrderStatus] = None, current_user = Depends(get_current_user),
    db: Session = Depends(get_db)):    
    if isinstance(current_user, Customer):
        customer_id = current_user.customer_id
    else:
        customer_id = getattr(current_user, 'user_id', None)
    
    if not customer_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se pudo identificar el cliente"
        )
    
    orders = get_orders_by_customer(db, customer_id=customer_id, skip=skip, limit=limit, status=status)
    
    # Calcular direccion de envio para cada pedido
    customer_info = get_customer_info(db, customer_id=customer_id)
    
    for order in orders:
        if order.shipping_address_number and customer_info:
            address_key = f"address_{order.shipping_address_number}"
            shipping_address = getattr(customer_info, address_key, None)
            
            if not shipping_address:
                # Fallback a address_1
                shipping_address = customer_info.address_1 or customer_info.address_2 or customer_info.address_3
            
            order.shipping_address = shipping_address or "No especificada"
        else:
            order.shipping_address = "No especificada"
    
    return orders

""" GET /all - Ver todos los pedidos (Admin/Marketing/Seller) """
@router.get("/all", response_model=List[Order])
def read_all_orders(skip: int = 0, limit: int = 100, status: Optional[str] = None, 
    search: Optional[str] = None, current_user: User = Depends(get_current_seller_user), db: Session = Depends(get_db)):

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
    
    orders = get_orders_for_user_groups(db=db, user_id=current_user.user_id, user_role=current_user.role,
        skip=skip, limit=limit, status=order_status, status_filter=status_filter, search=search)
    return orders

""" GET /{id} - Ver detalle de un pedido """
@router.get("/{order_id}", response_model=OrderWithAddress)
def read_order(order_id: UUID, current_user = Depends(get_current_user), db: Session = Depends(get_db)):

    order = get_order(db, order_id=order_id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pedido no encontrado")

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
    
    # Calcular direccion de envio
    return calculate_order_shipping_address(db, order)

""" PUT /{id}/status - Actualizar estado del pedido (Admin/Marketing/Seller) """
@router.put("/{order_id}/status", response_model=Order)
def update_order_status_route(order_id: UUID, order_update: OrderUpdate,
    current_user: User = Depends(get_current_seller_user), db: Session = Depends(get_db)):    
    # Obtener el pedido actual
    order = get_order(db, order_id=order_id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pedido no encontrado")
    
    is_admin = current_user.role == UserRole.admin
    is_marketing = current_user.role == UserRole.marketing
    is_seller = current_user.role == UserRole.seller
    
    # Verificar permisos por grupo (si no es admin)
    if not is_admin:
        if not user_can_manage_order(db, current_user.user_id, order.customer_id, current_user.role):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene permiso para gestionar este pedido. El cliente no pertenece a sus grupos.")
    
    current_status = order.status
    new_status = order_update.status
    
    # Validar que nadie puede modificar pedidos ya cancelados o entregados
    if current_status == OrderStatus.cancelled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se puede modificar un pedido que ya está cancelado"
        )
    
    if current_status == OrderStatus.delivered:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se puede modificar un pedido que ya fue entregado"
        )
    
    # Jerarquía de permisos:
    # - SELLER: NO puede aprobar pedidos, NO puede cancelar, solo puede marcar como shipped/delivered
    # - MARKETING: Puede hacer TODO excepto cancelar pedidos que ya fueron enviados (shipped)
    # - ADMIN: Puede cancelar TODO excepto pedidos entregados (delivered)
    
    # Definir transiciones válidas base (flujo normal sin cancelación)
    valid_transitions = {
        OrderStatus.pending_validation: [],
        OrderStatus.approved: [OrderStatus.shipped],
        OrderStatus.shipped: [OrderStatus.delivered],
        OrderStatus.delivered: [],
        OrderStatus.cancelled: []
    }
    
    # Agregar transiciones según rol
    if is_admin:
        # Admin puede: aprobar, cancelar (excepto delivered que ya se valida arriba), y todo el flujo normal
        valid_transitions[OrderStatus.pending_validation].extend([OrderStatus.approved, OrderStatus.cancelled])
        valid_transitions[OrderStatus.approved].append(OrderStatus.cancelled)
        valid_transitions[OrderStatus.shipped].append(OrderStatus.cancelled)
        
    elif is_marketing:
        # Marketing puede: aprobar, cancelar solo pending_validation y approved (NO shipped), y todo el flujo normal
        valid_transitions[OrderStatus.pending_validation].extend([OrderStatus.approved, OrderStatus.cancelled])
        valid_transitions[OrderStatus.approved].append(OrderStatus.cancelled)
        # Marketing NO puede cancelar shipped
        
    elif is_seller:
        # Seller NO puede aprobar (pending_validation -> approved)
        # Seller NO puede cancelar
        # Seller solo puede avanzar en el flujo: approved -> shipped -> delivered
        # Las transiciones approved->shipped y shipped->delivered ya están en valid_transitions base
        pass
    
    # Verificar si la transición es válida
    if new_status not in valid_transitions[current_status]:
        # Mensajes de error específicos según el caso
        if is_seller and current_status == OrderStatus.pending_validation and new_status == OrderStatus.approved:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Los vendedores no pueden aprobar pedidos. Solo marketing y administradores pueden hacerlo."
            )
        elif is_seller and new_status == OrderStatus.cancelled:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Los vendedores no pueden cancelar pedidos. Solo marketing y administradores pueden hacerlo."
            )
        elif is_marketing and current_status == OrderStatus.shipped and new_status == OrderStatus.cancelled:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Marketing no puede cancelar pedidos que ya fueron enviados. Solo administradores pueden hacerlo."
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Transición de estado inválida de '{current_status.value}' a '{new_status.value}'"
            )
    
    # Actualizar el estado del pedido
    updated_order = update_order_status(db, order_id=order_id, status=new_status)
    return updated_order

""" POST /{id}/assign - Asignar vendedor a un pedido (Marketing/Admin) """
@router.post("/{order_id}/assign", response_model=Order)
def assign_order_to_seller(order_id: UUID, assign_data: OrderAssign,
    current_user: User = Depends(get_current_seller_user), db: Session = Depends(get_db)):
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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vendedor no encontrado")
    
    # Verificar que el usuario a asignar sea un vendedor
    if seller.role != UserRole.seller:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"El usuario seleccionado no es un vendedor (rol: {seller.role.value})")

    # Obtener el grupo del cliente del pedido
    customer_info = get_customer_info(db, order.customer_id)
    
    if not customer_info or not customer_info.sales_group_id:
        # Cliente sin grupo - solo admin puede gestionar, pero no puede asignar
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


""" POST /{id}/cancel - Cancelar un pedido """
@router.post("/{order_id}/cancel", response_model=Order)
def cancel_order_route(order_id: UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Cancela un pedido.
    order = get_order(db, order_id=order_id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pedido no encontrado")    

    if isinstance(current_user, Customer):
        current_user_id = current_user.customer_id
        is_customer = True
        user_role = None  
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
    
    # Validacion basada en rol
    if is_customer:
        # Los clientes solo pueden cancelar antes de que sea validado
        if order.status != OrderStatus.pending_validation:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Los clientes solo pueden cancelar pedidos pendientes de validación"
            )
    elif user_role == UserRole.seller:
        # SELLERS NO PUEDEN CANCELAR PEDIDOS
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Los vendedores no tienen permiso para cancelar pedidos. Solo marketing y administradores pueden hacerlo."
        )
    elif user_role == UserRole.marketing:
        # Marketing puede cancelar antes de enviado
        if order.status == OrderStatus.shipped:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Marketing solo puede cancelar pedidos antes de que sean enviados"
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


""" PUT /{id}/edit - Editar un pedido (Marketing/Admin) """
@router.put("/{order_id}/edit", response_model=Order)
def edit_order_route(order_id: UUID, edit_data: OrderEditRequest, current_user: User = Depends(get_current_seller_user),
    db: Session = Depends(get_db)):
    # Verificar que el usuario sea marketing o admin
    if current_user.role not in [UserRole.marketing, UserRole.admin]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo marketing y administradores pueden editar pedidos"
        )
    
    # Obtener el pedido
    order = get_order(db, order_id=order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pedido no encontrado"
        )
    
    # Verificar permisos por grupo (si no es admin)
    is_admin = current_user.role == UserRole.admin
    if not is_admin:
        if not user_can_manage_order(db, current_user.user_id, order.customer_id, current_user.role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene permiso para editar este pedido. El cliente no pertenece a sus grupos."
            )
    
    # Editar el pedido
    try:
        edited_order = edit_order_items(db, order_id=order_id, items=edit_data.items, customer_id=order.customer_id)
        return edited_order
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


""" GET /{id}/download-txt - Descargar pedido en formato TXT """
@router.get("/{order_id}/download-txt")
def download_order_txt(
    order_id: UUID,
    current_user: User = Depends(get_current_seller_user),
    db: Session = Depends(get_db)
):
    """
    Descarga un archivo TXT con formato de ancho fijo para el pedido especificado.
    Solo accesible para admin, marketing y el vendedor asignado.
    """
    # Obtener el pedido
    order = get_order(db, order_id=order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pedido no encontrado"
        )
    
    # Verificar permisos por grupo (si no es admin)
    is_admin = current_user.role == UserRole.admin
    if not is_admin:
        if not user_can_manage_order(db, current_user.user_id, order.customer_id, current_user.role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene permiso para descargar este pedido. El cliente no pertenece a sus grupos."
            )
    
    # Generar contenido TXT
    try:
        txt_content = generate_order_txt(db, order_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    # Retornar archivo TXT
    from fastapi.responses import Response
    
    filename = f"pedido_{order_id}.txt"
    
    return Response(
        content=txt_content,
        media_type="text/plain",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )

