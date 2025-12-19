"""
CRUD para Pedidos (Orders)

Funciones para manejar el ciclo completo de pedidos:
- Crear pedido desde carrito
- Consultar pedidos (cliente, admin, seller)
- Actualizar estado de pedidos
- Asignar pedidos a vendedores
- Cancelar pedidos con restauración de stock
- Filtrado por grupos de ventas (permisos)

Flujo típico de un pedido:
1. Cliente crea pedido desde carrito → pending_validation
2. Admin/Marketing asigna vendedor → assigned
3. Vendedor aprueba → approved
4. Se envía → shipped
5. Se entrega → delivered
"""

from typing import List, Optional
from datetime import datetime
from decimal import Decimal
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_, or_

from db.base import Order, OrderItem, OrderStatus, Product, CartCache, CustomerInfo, PriceListItem
from schemas.order import OrderCreate, OrderUpdate, OrderItemCreate


def get_order(db: Session, order_id: int) -> Optional[Order]:
    """
    Obtiene un pedido por ID con todas sus relaciones
    
    Pre-carga:
    - Items del pedido con información de productos
    - Información del cliente
    - Información del vendedor asignado (si existe)
    
    Args:
        db: Sesión de base de datos
        order_id: ID del pedido
        
    Returns:
        Pedido completo o None si no existe
    """
    return db.query(Order).options(
        joinedload(Order.items).joinedload(OrderItem.product),
        joinedload(Order.customer),
        joinedload(Order.assigned_seller)
    ).filter(Order.order_id == order_id).first()


def get_orders_by_customer(
    db: Session, 
    customer_id: int, 
    skip: int = 0, 
    limit: int = 100,
    status: Optional[OrderStatus] = None
) -> List[Order]:
    """
    Obtiene pedidos de un cliente específico
    
    Útil para el historial de pedidos del cliente.
    
    Args:
        db: Sesión de base de datos
        customer_id: ID del cliente
        skip: Registros a saltar (paginación)
        limit: Máximo de registros
        status: Filtrar por estado específico (opcional)
        
    Returns:
        Lista de pedidos del cliente ordenados por fecha (más recientes primero)
    """
    query = db.query(Order).options(
        joinedload(Order.items).joinedload(OrderItem.product),
        joinedload(Order.customer),
        joinedload(Order.assigned_seller)
    ).filter(Order.customer_id == customer_id)
    
    if status:
        query = query.filter(Order.status == status)
    
    return query.order_by(Order.created_at.desc()).offset(skip).limit(limit).all()


def get_orders(
    db: Session, 
    skip: int = 0, 
    limit: int = 100,
    status: Optional[OrderStatus] = None,
    search: Optional[str] = None
) -> List[Order]:
    """
    Obtiene todos los pedidos (admin/seller) con búsqueda opcional
    
    Búsqueda por:
    - Número de pedido (si el término es numérico)
    - Nombre completo del cliente
    - Username del cliente
    
    Args:
        db: Sesión de base de datos
        skip: Registros a saltar
        limit: Máximo de registros
        status: Filtrar por estado (opcional)
        search: Término de búsqueda (opcional)
        
    Returns:
        Lista de pedidos ordenados por fecha (más recientes primero)
    """
    from db.base import Customer
    
    query = db.query(Order).options(
        joinedload(Order.items).joinedload(OrderItem.product),
        joinedload(Order.customer),
        joinedload(Order.assigned_seller)
    )
    
    # === FILTRAR POR ESTADO ===
    if status:
        query = query.filter(Order.status == status)
    
    # === BÚSQUEDA ===
    if search:
        query = query.join(Order.customer)
        
        if search.isdigit():
            # Buscar por número de pedido o nombre
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


def create_order_from_cart(
    db: Session,
    customer_id: int,
    shipping_address_number: int = 1
) -> Order:
    """
    Crea un pedido a partir del carrito del cliente
    
    Proceso completo:
    1. Validar que el carrito no esté vacío
    2. Validar que el cliente tenga lista de precios
    3. Validar stock suficiente para cada producto
    4. Calcular precios con markup e IVA
    5. Crear pedido y items
    6. Reducir stock de productos
    7. Limpiar carrito
    
    Los precios se "congelan" al momento del pedido para
    mantener historial preciso aunque cambien después.
    
    Args:
        db: Sesión de base de datos
        customer_id: ID del cliente
        shipping_address_number: Qué dirección usar (1, 2 o 3)
        
    Returns:
        Pedido creado con todos sus items
        
    Raises:
        ValueError: Si el carrito está vacío, sin lista de precios,
                   stock insuficiente, o dirección inválida
    """
    # === VALIDAR DIRECCIÓN ===
    if shipping_address_number not in [1, 2, 3]:
        raise ValueError("Número de dirección inválido. Debe ser 1, 2 o 3.")
    
    # === OBTENER ITEMS DEL CARRITO ===
    cart_items = db.query(CartCache).filter(
        CartCache.customer_id == customer_id
    ).all()
    
    if not cart_items:
        raise ValueError("El carrito está vacío")
    
    # === VALIDAR LISTA DE PRECIOS ===
    customer_info = db.query(CustomerInfo).filter(
        CustomerInfo.customer_id == customer_id
    ).first()
    
    if not customer_info or not customer_info.price_list_id:
        raise ValueError("No tienes una lista de precios asignada. Contacta al administrador.")
    
    # === CREAR PEDIDO ===
    db_order = Order(
        customer_id=customer_id,
        status=OrderStatus.pending_validation,
        total_amount=0,  # Se calculará después
        shipping_address_number=shipping_address_number
    )
    db.add(db_order)
    db.flush()  # Para obtener order_id
    
    # === CREAR ITEMS Y CALCULAR TOTAL ===
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
            raise ValueError(f"El producto {product.name} no está en tu lista de precios")
        
        # === CALCULAR PRECIO FINAL ===
        # Fórmula: final = (base * (1 + markup/100)) * (1 + iva/100)
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
        product.stock_count -= cart_item.quantity
        
        # Acumular total
        total += final_price * cart_item.quantity
    
    # Actualizar total del pedido
    db_order.total_amount = float(total)
    
    # === LIMPIAR CARRITO ===
    db.query(CartCache).filter(CartCache.customer_id == customer_id).delete()
    
    db.commit()
    db.refresh(db_order)
    return db_order


def update_order_status(
    db: Session, 
    order_id: int, 
    status: OrderStatus,
    seller_id: Optional[int] = None
) -> Optional[Order]:
    """
    Actualiza el estado de un pedido
    
    Si se aprueba, también registra quién lo validó y cuándo.
    
    Args:
        db: Sesión de base de datos
        order_id: ID del pedido
        status: Nuevo estado
        seller_id: ID del vendedor que aprueba (si aplica)
        
    Returns:
        Pedido actualizado o None si no existe
    """
    db_order = get_order(db, order_id)
    if not db_order:
        return None
    
    db_order.status = status
    
    # Si se aprueba, registrar validación
    if seller_id and status == OrderStatus.approved:
        db_order.assigned_seller_id = seller_id
        db_order.validated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(db_order)
    return db_order


def cancel_order(db: Session, order_id: int) -> Optional[Order]:
    """
    Cancela un pedido y restaura el stock
    
    Solo se pueden cancelar pedidos en estados:
    - pending_validation
    - assigned
    - approved
    
    Al cancelar, se restaura el stock de todos los productos.
    
    Args:
        db: Sesión de base de datos
        order_id: ID del pedido a cancelar
        
    Returns:
        Pedido cancelado
        
    Raises:
        ValueError: Si el pedido no se puede cancelar (ya enviado/entregado)
    """
    db_order = get_order(db, order_id)
    if not db_order:
        return None
    
    # === VALIDAR QUE SE PUEDE CANCELAR ===
    if db_order.status not in [
        OrderStatus.pending_validation,
        OrderStatus.assigned,
        OrderStatus.approved
    ]:
        raise ValueError("No se puede cancelar este pedido")
    
    # === RESTAURAR STOCK ===
    for item in db_order.items:
        product = db.query(Product).filter(
            Product.product_id == item.product_id
        ).first()
        if product:
            product.stock_count += item.quantity
    
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
    """
    Obtiene pedidos filtrados según los grupos del usuario
    
    Lógica de permisos:
    - Admin: ve TODOS los pedidos
    - Marketing: ve pedidos de clientes en sus grupos asignados
    - Seller: ve SOLO pedidos asignados a él
    
    Args:
        db: Sesión de base de datos
        user_id: ID del usuario interno
        user_role: Rol del usuario (UserRole)
        skip: Registros a saltar
        limit: Máximo de registros
        status: Filtrar por estado (opcional)
        search: Buscar por número o nombre (opcional)
        
    Returns:
        Lista de pedidos filtrados según permisos
    """
    from db.base import User, Customer, UserRole
    
    query = db.query(Order).options(
        joinedload(Order.items).joinedload(OrderItem.product),
        joinedload(Order.customer),
        joinedload(Order.assigned_seller)
    )
    
    # === APLICAR FILTROS SEGÚN ROL ===
    if user_role != UserRole.admin:
        from crud.crud_sales_group import get_user_groups
        
        # Obtener grupos del usuario
        user_group_ids = get_user_groups(db, user_id)
        
        # Si no está en ningún grupo, no puede ver pedidos
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
    
    # === FILTRAR POR ESTADO ===
    if status:
        query = query.filter(Order.status == status)
    
    # === BÚSQUEDA ===
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
