"""
CRUD para Pedidos (Orders)

Funciones para manejar el ciclo completo de pedidos:
- Crear pedido desde carrito
- Consultar pedidos (cliente, admin, seller)
- Actualizar estado de pedidos
- Asignar pedidos a vendedores
- Cancelar pedidos con restauracion de stock
- Filtrado por grupos de ventas (permisos)

Flujo tipico de un pedido:
1. Cliente crea pedido desde carrito → pending_validation
2. Admin/Marketing asigna vendedor → assigned
3. Vendedor aprueba → approved
4. Se envia → shipped
5. Se entrega → delivered
"""

from typing import List, Optional
from datetime import datetime, timezone
from decimal import Decimal
from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_, or_

from db.base import Order, OrderItem, OrderStatus, Product, CartCache, CustomerInfo, PriceListItem, User, UserRole
from farmacruz_api.crud.crud_sales_group import get_user_groups, user_can_manage_order
from farmacruz_api.crud.crud_user import get_user
from schemas.order import OrderAssign, OrderCreate, OrderUpdate, OrderItemCreate


def get_order(db: Session, order_id: int) -> Optional[Order]:
    # Obtiene un pedido por ID con todas sus relaciones

    return db.query(Order).options(
        joinedload(Order.items).joinedload(OrderItem.product),
        joinedload(Order.customer),
        joinedload(Order.assigned_seller)
    ).filter(Order.order_id == order_id).first()


def get_orders_by_customer(db: Session, customer_id: int, skip: int = 0, limit: int = 100, status: Optional[OrderStatus] = None) -> List[Order]:
    # Obtiene pedidos de un cliente especifico
    
    query = db.query(Order).options(
        joinedload(Order.items).joinedload(OrderItem.product),
        joinedload(Order.customer),
        joinedload(Order.assigned_seller)
    ).filter(Order.customer_id == customer_id)
    
    if status:
        query = query.filter(Order.status == status)
    
    return query.order_by(Order.created_at.desc()).offset(skip).limit(limit).all()


def get_orders(db: Session, skip: int = 0, limit: int = 100, status: Optional[OrderStatus] = None, search: Optional[str] = None) -> List[Order]:
    # Obtiene todos los pedidos (admin/seller) con busqueda opcional
    
    from db.base import Customer
    
    query = db.query(Order).options(
        joinedload(Order.items).joinedload(OrderItem.product),
        joinedload(Order.customer),
        joinedload(Order.assigned_seller)
    )
    
    # Filtrar por status
    if status:
        query = query.filter(Order.status == status)
    
    # Busqueda
    if search:
        query = query.join(Order.customer)
        
        if search.isdigit():
            # Buscar por numero de pedido o nombre
            query = query.filter(
                or_(
                    Order.order_id == int(search),
                    Customer.full_name.ilike(f"%{search}%"),
                    Customer.username.ilike(f"%{search}%")
                )
            )
        else:
            # Buscar solo por nombre
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    Customer.full_name.ilike(search_term),
                    Customer.username.ilike(search_term)
                )
            )
    
    return query.order_by(Order.created_at.desc()).offset(skip).limit(limit).all()


def create_order_from_cart(db: Session, customer_id: int, shipping_address_number: int = 1) -> Order:
    # Crea un pedido a partir del carrito del cliente
    
    # Validar direccion
    if shipping_address_number not in [1, 2, 3]:
        raise ValueError("Numero de direccion invalido. Debe ser 1, 2 o 3.")
    
    # Obtener items del carrito
    cart_items = db.query(CartCache).filter(
        CartCache.customer_id == customer_id
    ).all()
    
    if not cart_items:
        raise ValueError("El carrito esta vacio")
    
    # Validar lista de precios
    customer_info = db.query(CustomerInfo).filter(
        CustomerInfo.customer_id == customer_id
    ).first()
    
    if not customer_info or not customer_info.price_list_id:
        raise ValueError("No tienes una lista de precios asignada. Contacta al administrador.")
    
    # Crear pedido
    db_order = Order(
        customer_id=customer_id,
        status=OrderStatus.pending_validation,
        total_amount=0,  # Se calculara despues
        shipping_address_number=shipping_address_number
    )
    db.add(db_order)
    db.flush()  # Para obtener order_id
    
    # CREAR ITEMS Y CALCULAR TOTAL
    total = Decimal('0')
    
    for cart_item in cart_items:
        # Obtener producto
        product = db.query(Product).filter(
            Product.product_id == cart_item.product_id
        ).first()
        
        # Validar producto activo
        if not product or not product.is_active:
            continue
        
        # Validar stock suficiente
        if product.stock_count < cart_item.quantity:
            raise ValueError(f"Stock insuficiente para {product.name}")
        
        # Obtener markup de la lista de precios del cliente
        price_item = db.query(PriceListItem).filter(
            PriceListItem.price_list_id == customer_info.price_list_id,
            PriceListItem.product_id == cart_item.product_id
        ).first()
        
        if not price_item:
            raise ValueError(f"El producto {product.name} no esta en tu lista de precios")
        
        # CALCULAR PRECIO FINAL
        # Formula: final = (base * (1 + markup/100)) * (1 + iva/100)
        base_price = Decimal(str(product.base_price or 0))
        markup = Decimal(str(price_item.markup_percentage or 0))
        iva = Decimal(str(product.iva_percentage or 0))
        
        price_with_markup = base_price * (1 + markup / 100)
        final_price = price_with_markup * (1 + iva / 100)
        
        # Crear item del pedido (precios "congelados")
        order_item = OrderItem(
            order_id=db_order.order_id,
            product_id=cart_item.product_id,
            quantity=cart_item.quantity,
            base_price=float(base_price),
            markup_percentage=float(markup),
            iva_percentage=float(iva),
            final_price=float(final_price)
        )
        db.add(order_item)
        
        # Reducir stock
        # product.stock_count -= cart_item.quantity
        
        # Acumular total
        total += final_price * cart_item.quantity
    
    # Actualizar total del pedido
    db_order.total_amount = float(total)
    
    # === LIMPIAR CARRITO ===
    db.query(CartCache).filter(CartCache.customer_id == customer_id).delete()
    
    db.commit()
    db.refresh(db_order)
    return db_order


def update_order_status(db: Session, order_id: int, status: OrderStatus, seller_id: Optional[int] = None) -> Optional[Order]:
    # Actualiza el estado de un pedido
    db_order = get_order(db, order_id)
    if not db_order:
        return None
    
    db_order.status = status
    
    # Si se aprueba, registrar validacion
    if seller_id and status == OrderStatus.approved:
        db_order.assigned_seller_id = seller_id
        db_order.validated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(db_order)
    return db_order


def cancel_order(db: Session, order_id: int) -> Optional[Order]:
    # Cancela un pedido y puede restaurar el stock
    
    db_order = get_order(db, order_id)
    if not db_order:
        return None
    
    # Validar que se pueda cancelar
    if db_order.status not in [
        OrderStatus.pending_validation,
        OrderStatus.approved,
        OrderStatus.shipped
    ]:
        raise ValueError("No se puede cancelar este pedido")
    
    # RESTAURAR STOCK 
    """
    for item in db_order.items:
        product = db.query(Product).filter(
            Product.product_id == item.product_id
        ).first()
        if product:
            product.stock_count += item.quantity
    """
    
    # Cambiar estado a cancelado
    db_order.status = OrderStatus.cancelled
    db.commit()
    db.refresh(db_order)
    return db_order


def get_orders_for_user_groups(
    db: Session,
    user_id: int,
    user_role,
    skip: int = 0,
    limit: int = 100,
    status: Optional[OrderStatus] = None,
    search: Optional[str] = None
) -> List[Order]:
    # Obtiene pedidos filtrados segun los grupos del usuario
    from db.base import User, Customer, UserRole
    
    query = db.query(Order).options(
        joinedload(Order.items).joinedload(OrderItem.product),
        joinedload(Order.customer),
        joinedload(Order.assigned_seller)
    )
    
    # Filtros segun rol
    if user_role != UserRole.admin:
        from crud.crud_sales_group import get_user_groups
        
        # Obtener grupos del usuario
        user_group_ids = get_user_groups(db, user_id)
        
        # Si no esta en ningun grupo, no puede ver pedidos
        if not user_group_ids:
            return []
        
        if user_role == UserRole.seller:
            # Sellers SOLO ven pedidos asignados a ellos
            query = query.filter(Order.assigned_seller_id == user_id)
        else:
            # Marketing ve pedidos de clientes en sus grupos
            query = query.join(
                CustomerInfo,
                Order.customer_id == CustomerInfo.customer_id
            ).filter(
                CustomerInfo.sales_group_id.in_(user_group_ids)
            )
    
    # Filtro por status
    if status:
        query = query.filter(Order.status == status)
    
    # Busqueda
    if search:
        # Re-join con Customer si no se hizo antes
        if user_role == UserRole.admin:
            query = query.join(Order.customer)
        
        if search.isdigit():
            query = query.filter(
                or_(
                    Order.order_id == int(search),
                    Customer.full_name.ilike(f"%{search}%"),
                    Customer.username.ilike(f"%{search}%")
                )
            )
        else:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    Customer.full_name.ilike(search_term),
                    Customer.username.ilike(search_term)
                )
            )
    
    return query.order_by(Order.created_at.desc()).offset(skip).limit(limit).all()

def get_order_count_by_customer(db: Session, customer_id: int) -> int:
    # Obtiene el conteo de pedidos de un cliente especifico
    corder_count = db.query(Order).filter(
        Order.customer_id == customer_id
    ).count()

    return corder_count


def calculate_order_shipping_address(db: Session, order: Order) -> str:
    # Calcula la direccion de envio completa basada en el numero seleccionado
    if order.shipping_address_number:
        customer_info = db.query(CustomerInfo).filter(
            CustomerInfo.customer_id == order.customer_id
        ).first()
        
        if customer_info:
            address_key = f"address_{order.shipping_address_number}"
            shipping_address = getattr(customer_info, address_key, None)
            
            if not shipping_address:
                # Fallback to address_1
                shipping_address = customer_info.address_1 or customer_info.address_2 or customer_info.address_3
            
            # Add as attribute (won't be in DB, just for response)
            order.shipping_address = shipping_address or "No especificada"
        else:
            order.shipping_address = "No especificada"
    else:
        order.shipping_address = "No especificada"
    
    return order


def assign_order_seller(db: Session, order: Order, assign_data: OrderAssign, current_user: User) -> Order | None:
    # Asignación final
    order.assigned_seller_id = assign_data.assigned_seller_id
    order.assigned_by_user_id = current_user.user_id
    order.assigned_at = datetime.now(timezone.utc)  

    if assign_data.assignment_notes:
        order.assignment_notes = assign_data.assignment_notes

    db.commit()
    db.refresh(order)
    return order
