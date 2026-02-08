"""
CRUD para Pedidos (Orders)

Funciones para manejar el ciclo completo de pedidos:
- Crear pedido desde carrito
- Consultar pedidos (cliente, admin, seller)
- Actualizar estado de pedidos
- Asignar pedidos a vendedores
- Cancelar pedidos con restauracion de stock
- Filtrado por grupos de ventas (permisos)
- Modificacion de direcciones de ordenes
- Modificaciones de productos en ordenes

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
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_, or_, cast, String

from db.base import Order, OrderItem, OrderStatus, Product, CartCache, CustomerInfo, PriceListItem, User, Customer
from schemas.order import OrderAssign, OrderCreate, OrderUpdate, OrderItemCreate
from utils.price_utils import calculate_final_price_with_markup


""" Obtener pedidos por ID con relaciones """
def get_order(db: Session, order_id: UUID) -> Optional[Order]:
    return db.query(Order).options(
        joinedload(Order.items).joinedload(OrderItem.product),
        joinedload(Order.customer),
        joinedload(Order.assigned_seller)
    ).filter(Order.order_id == order_id).first()

""" Obtener pedidos de un cliente especifico con relaciones """
def get_orders_by_customer(db: Session, customer_id: int, skip: int = 0, limit: int = 100, status: Optional[OrderStatus] = None) -> List[Order]:    
    query = db.query(Order).options(
        joinedload(Order.items).joinedload(OrderItem.product),
        joinedload(Order.customer),
        joinedload(Order.assigned_seller)
    ).filter(Order.customer_id == customer_id)
    
    if status:
        query = query.filter(Order.status == status)
    
    return query.order_by(Order.created_at.desc()).offset(skip).limit(limit).all()

""" Obtener todos los pedidos con filtros opcionales para admin/marketing/seller """
def get_orders(db: Session, skip: int = 0, limit: int = 100, status: Optional[OrderStatus] = None, search: Optional[str] = None) -> List[Order]:        
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
        from uuid import UUID
        query = query.join(Order.customer)
        
        # Intentar parsear como UUID
        order_id_filter = None
        try:
            search_uuid = UUID(search)
            order_id_filter = Order.order_id == search_uuid
        except (ValueError, AttributeError):
            # No es UUID completo, buscar parcialmente convirtiendo a texto
            search_term_uuid = f"%{search}%"
            order_id_filter = cast(Order.order_id, String).ilike(search_term_uuid)
        
        # Buscar por nombre de cliente
        search_term = f"%{search}%"
        name_filters = or_(
            Customer.full_name.ilike(search_term),
            Customer.username.ilike(search_term)
        )
        
        # Combinar filtros (siempre busca en order_id Y nombres)
        query = query.filter(or_(order_id_filter, name_filters))
    
    return query.order_by(Order.created_at.desc()).offset(skip).limit(limit).all()

""" Crear un pedido a partir del carrito del cliente """
def create_order_from_cart(db: Session, customer_id: int, shipping_address_number: int = 1) -> Order:
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
    
    # Obtener el agente del cliente para asignarlo automáticamente
    from db.base import Customer
    customer = db.query(Customer).filter(Customer.customer_id == customer_id).first()
    assigned_seller_id = customer.agent_id if customer and customer.agent_id else None
    
    # Crear pedido con agente asignado automáticamente
    db_order = Order(
        customer_id=customer_id,
        status=OrderStatus.pending_validation,
        total_amount=0,  # Se calculara despues
        shipping_address_number=shipping_address_number,
        assigned_seller_id=assigned_seller_id  # Auto-asignar agente
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
        
        # CALCULAR PRECIO FINAL usando utilidad centralizada        
        base_price = Decimal(str(product.base_price or 0))
        markup_percentage = Decimal(str(price_item.markup_percentage or 0))
        stored_final_price = Decimal(str(price_item.final_price)) if price_item.final_price else None
        
        final_price = calculate_final_price_with_markup(
            base_price=base_price,
            markup_percentage=markup_percentage,
            stored_final_price=stored_final_price
        )
        
        iva = Decimal(str(product.iva_percentage or 0))
        
        # Crear item del pedido (precios "congelados")
        order_item = OrderItem(
            order_id=db_order.order_id,
            product_id=cart_item.product_id,
            quantity=cart_item.quantity,
            base_price=float(base_price),
            markup_percentage=float(markup_percentage),
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


def create_order_direct(db: Session, customer_id: int, items: List[dict], shipping_address_number: int = 1) -> Order:
    """
    Crea un pedido directamente sin pasar por el carrito.
    
    Usado por admin/marketing para crear pedidos en nombre de clientes.
    
    Args:
        db: Sesión de base de datos
        customer_id: ID del cliente para quien se crea el pedido
        items: Lista de dicts con {'product_id': str, 'quantity': int}
        shipping_address_number: Número de dirección (1, 2 o 3)
    
    Returns:
        Order: El pedido creado
    """
    # Validar direccion
    if shipping_address_number not in [1, 2, 3]:
        raise ValueError("Numero de direccion invalido. Debe ser 1, 2 o 3.")
    
    if not items:
        raise ValueError("Debe incluir al menos un producto en el pedido")
    
    # Validar lista de precios del cliente
    customer_info = db.query(CustomerInfo).filter(
        CustomerInfo.customer_id == customer_id
    ).first()
    
    if not customer_info or not customer_info.price_list_id:
        raise ValueError("El cliente no tiene una lista de precios asignada")
    
    # Obtener el agente del cliente para asignarlo automáticamente
    customer = db.query(Customer).filter(Customer.customer_id == customer_id).first()
    if not customer:
        raise ValueError("Cliente no encontrado")
    
    assigned_seller_id = customer.agent_id if customer.agent_id else None
    
    # Crear pedido con agente asignado automáticamente
    db_order = Order(
        customer_id=customer_id,
        status=OrderStatus.pending_validation,
        total_amount=0,  # Se calculara despues
        shipping_address_number=shipping_address_number,
        assigned_seller_id=assigned_seller_id
    )
    db.add(db_order)
    db.flush()  # Para obtener order_id
    
    # CREAR ITEMS Y CALCULAR TOTAL
    total = Decimal('0')
    
    for item_data in items:
        product_id = item_data.get('product_id')
        quantity = item_data.get('quantity', 1)
        
        if not product_id or quantity <= 0:
            continue
        
        # Obtener producto
        product = db.query(Product).filter(
            Product.product_id == product_id
        ).first()
        
        # Validar producto activo
        if not product or not product.is_active:
            raise ValueError(f"Producto {product_id} no encontrado o inactivo")
        
        # Validar stock suficiente
        # if product.stock_count < quantity:
        #     raise ValueError(f"Stock insuficiente para {product.name}")
        
        # Obtener markup de la lista de precios del cliente
        price_item = db.query(PriceListItem).filter(
            PriceListItem.price_list_id == customer_info.price_list_id,
            PriceListItem.product_id == product_id
        ).first()
        
        if not price_item:
            raise ValueError(f"El producto {product.name} no esta en la lista de precios del cliente")
        
        # CALCULAR PRECIO FINAL usando utilidad centralizada        
        base_price = Decimal(str(product.base_price or 0))
        markup_percentage = Decimal(str(price_item.markup_percentage or 0))
        stored_final_price = Decimal(str(price_item.final_price)) if price_item.final_price else None
        
        final_price = calculate_final_price_with_markup(
            base_price=base_price,
            markup_percentage=markup_percentage,
            stored_final_price=stored_final_price
        )
        
        iva = Decimal(str(product.iva_percentage or 0))
        
        # Crear item del pedido (precios "congelados")
        order_item = OrderItem(
            order_id=db_order.order_id,
            product_id=product_id,
            quantity=quantity,
            base_price=float(base_price),
            markup_percentage=float(markup_percentage),
            iva_percentage=float(iva),
            final_price=float(final_price)
        )
        db.add(order_item)
        
        # Acumular total
        total += final_price * quantity
    
    # Actualizar total del pedido
    db_order.total_amount = float(total)
    
    db.commit()
    db.refresh(db_order)
    return db_order

""" Actualizar el estado de un pedido """
def update_order_status(db: Session, order_id: UUID, status: OrderStatus, seller_id: Optional[int] = None) -> Optional[Order]:
    # Actualiza el estado de un pedido
    db_order = get_order(db, order_id)
    if not db_order:
        return None
    
    db_order.status = status
    
    # Si se aprueba, registrar validacion
    if seller_id and status == OrderStatus.approved:
        db_order.validated_at = datetime.now(timezone.utc)
    
    db.commit()
    db.refresh(db_order)
    return db_order

""" Cancelar un pedido y restaurar stock """
def cancel_order(db: Session, order_id: UUID) -> Optional[Order]:
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

""" Obtener pedidos filtrados segun los grupos del usuario """
def get_orders_for_user_groups(db: Session, user_id: int, user_role,
    skip: int = 0, limit: int = 100, status: Optional[OrderStatus] = None, status_filter: Optional[str] = None,  # Filtro raw (puede ser "assigned")
    search: Optional[str] = None) -> List[Order]:
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
        from db.base import Customer
        
        # Obtener grupos del usuario
        user_group_ids = get_user_groups(db, user_id)
        
        if user_role == UserRole.seller:
            # Sellers SOLO ven pedidos asignados a ellos
            # (Los pedidos se asignan automaticamente al agente al crearse)
            query = query.filter(Order.assigned_seller_id == user_id)
        else:
            # Marketing ve pedidos de clientes en sus grupos
            # Si no esta en ningun grupo, no puede ver pedidos
            if not user_group_ids:
                return []
            
            query = query.join(
                CustomerInfo,
                Order.customer_id == CustomerInfo.customer_id
            ).filter(
                CustomerInfo.sales_group_id.in_(user_group_ids)
            )
    
    # Filtro especial: "assigned" significa que tiene vendedor asignado
    if status_filter == "assigned":
        query = query.filter(Order.assigned_seller_id.isnot(None))
    # Filtro por status normal
    elif status:
        query = query.filter(Order.status == status)
    
    # Busqueda
    if search:
        from uuid import UUID
        
        # Re-join con Customer si no se hizo antes
        if user_role == UserRole.admin:
            query = query.join(Order.customer)
        
        # Intentar parsear como UUID
        order_id_filter = None
        try:
            search_uuid = UUID(search)
            order_id_filter = Order.order_id == search_uuid
        except (ValueError, AttributeError):
            # No es UUID completo, buscar parcialmente convirtiendo a texto
            search_term_uuid = f"%{search}%"
            order_id_filter = cast(Order.order_id, String).ilike(search_term_uuid)
        
        # Buscar por nombre de cliente
        search_term = f"%{search}%"
        name_filters = or_(
            Customer.full_name.ilike(search_term),
            Customer.username.ilike(search_term)
        )
        
        # Combinar filtros (siempre busca en order_id Y nombres)
        query = query.filter(or_(order_id_filter, name_filters))
    
    return query.order_by(Order.created_at.desc()).offset(skip).limit(limit).all()
    
""" Obtener el conteo de pedidos de un cliente especifico """
def get_order_count_by_customer(db: Session, customer_id: int) -> int:
    # Obtiene el conteo de pedidos de un cliente especifico
    corder_count = db.query(Order).filter(
        Order.customer_id == customer_id
    ).count()

    return corder_count

""" Calcular y actualizar la direccion de envio de un pedido """
def calculate_order_shipping_address(db: Session, order: Order) -> str:
    # Calcula la direccion de envio completa basada en el numero seleccionado
    customer_info = db.query(CustomerInfo).filter(
        CustomerInfo.customer_id == order.customer_id
    ).first()
    
    if order.shipping_address_number and customer_info:
        address_key = f"address_{order.shipping_address_number}"
        shipping_address = getattr(customer_info, address_key, None)
        
        if not shipping_address:
            # Fallback to address_1
            shipping_address = customer_info.address_1 or customer_info.address_2 or customer_info.address_3
        
        order.shipping_address = shipping_address or "No especificada"
    else:
        order.shipping_address = "No especificada"
    
    # Agregar customerInfo completo al order
    if customer_info:
        order.customerInfo = {
            "business_name": customer_info.business_name,
            "rfc": customer_info.rfc,
            "telefono_1": customer_info.telefono_1,
            "telefono_2": customer_info.telefono_2,
            "address_1": customer_info.address_1,
            "address_2": customer_info.address_2,
            "address_3": customer_info.address_3
        }
    
    return order

""" Asignar un pedido a un vendedor """
def assign_order_seller(db: Session, order: Order, assign_data: OrderAssign, current_user: User) -> Optional[Order]:
    # Asignación final
    order.assigned_seller_id = assign_data.assigned_seller_id
    order.assigned_by_user_id = current_user.user_id
    order.assigned_at = datetime.now(timezone.utc)  

    if assign_data.assignment_notes:
        order.assignment_notes = assign_data.assignment_notes

    db.commit()
    db.refresh(order)
    return order

""" Generar archivo TXT del pedido en formato de ancho fijo """
def generate_order_txt(db: Session, order_id: UUID) -> str:
    """
    Genera el contenido TXT del pedido en formato de ancho fijo.
    
    Formato por línea (basado en EJEMPLOPED.txt):
    - Product ID (40 chars, left-aligned)
    - Unit "PZ" (7 chars, centered/aligned)
    - Campo decimal 1: 0.00000000 (12 chars)
    - Campo decimal 2: 0.00000000 (12 chars)
    - Espacios (48 chars)
    - Cantidad (10 chars, right-aligned)
    - Precio total (20 chars, 8 decimales)
    - Precio unitario (20 chars, 8 decimales)
    - Trailing spaces hasta ~400 chars
    
    Total: ~400 caracteres por línea
    """
    # Obtener pedido con items y productos
    order = get_order(db, order_id)
    if not order:
        raise ValueError(f"Pedido {order_id} no encontrado")
    
    lines = []
    
    for item in order.items:
        if not item.product:
            continue
        
        # Obtener datos del producto y item
        product_id = item.product.product_id or ""
        quantity = item.quantity
        unit_price = Decimal(str(item.final_price))
        total_price = unit_price * Decimal(str(quantity))
        
        # 1. Product ID (40 chars, alineado izquierda)
        product_id_field = product_id[:40].ljust(40)
        
        # 2. Unidad (7 chars, alineado izquierda)
        unit = item.product.unidad_medida or "PZ"  # Default a "PZ" si es None
        unit_field = unit[:7].ljust(7)  # Truncar a 7 chars y alinear izquierda
        
        # 3 y 4. Decimales fijos (12 chars c/u, incluye espaciado)
        decimal1_field = "0.00000000  "
        decimal2_field = "0.00000000  "
        
        # 5. Espaciado central (28 espacios)
        spaces_field = " " * 28
        
        # 6. Columna auxiliar (10 chars, alineado derecha)
        other_field = str(1).rjust(10)
        
        # 7. Cantidad (20 chars, 8 decimales, alineado derecha)
        quantity_str = f"{float(quantity):.8f}".rjust(20)
        
        # 8. Precio Unitario (20 chars, 8 decimales, alineado derecha)
        total_price_str = f"{float(unit_price):.8f}".rjust(20)
        
        # Construir línea completa
        line = (
            product_id_field +
            unit_field +
            decimal1_field + 
            decimal2_field +
            spaces_field +
            other_field +
            quantity_str +
            total_price_str
        )
        
        # Agregar trailing spaces hasta ~404 chars (longitud total de linea en archivo valido)
        line = line.ljust(405)
        
        lines.append(line)
    
    # Unir todas las líneas con salto de línea Windows (\r\n)
    return "\r\n".join(lines) + "\r\n"