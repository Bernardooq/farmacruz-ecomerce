"""
CRUD para Dashboards y Reportes

Funciones para generar estadisticas y reportes del sistema:
- Dashboard de administrador con metricas generales
- Reporte de ventas con desglose de pedidos
"""

from datetime import datetime, timezone
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from db.base import Order, OrderStatus, Product, User, UserRole, Customer
from schemas.dashboards import DashboardStats, SalesReport, SalesReportItem, SellerMarketingDashboardStats

"""Obtiene estadisticas generales para el dashboard de administrador (Total usuarios y clientes, productos y pedidos, ingresos, productos y stock)"""
def get_admin_dashboard_stats(db: Session) -> DashboardStats:
    # USERS
    # Total de usuarios internos (admin, marketing, seller)
    total_users = db.query(func.count(User.user_id)).scalar()
    
    # Total de clientes registrados (tabla separada)
    total_customers = db.query(func.count(Customer.customer_id)).scalar()
    
    # Total de vendedores activos
    total_sellers = db.query(func.count(User.user_id)).filter(
        User.role == UserRole.seller
    ).scalar()
    
    # Total de usuarios marketing activos
    total_marketing = db.query(func.count(User.user_id)).filter(
        User.role == UserRole.marketing
    ).scalar()
    
    # PRODS
    # Total de productos activos en catalogo
    total_products = db.query(func.count(Product.product_id)).filter(
        Product.is_active == True
    ).scalar()
    
    # Productos con bajo stock (menos de 10 unidades)
    # Esto es util para alertas de reabastecimiento
    low_stock_count = db.query(func.count(Product.product_id)).filter(
        Product.stock_count < 10,
        Product.stock_count > 0,  # No contar productos sin stock
        Product.is_active == True
    ).scalar()

    # Productos agotados (stock == 0)
    out_of_stock_count = db.query(func.count(Product.product_id)).filter(
        Product.stock_count <= 0,
        Product.is_active == True
    ).scalar()
    
    # PEDIDOS
    # Total de pedidos historicos
    total_orders = db.query(func.count(Order.order_id)).scalar()
    
    # Total de pedidos entregados
    delivered_orders = db.query(func.count(Order.order_id)).filter(
        Order.status == OrderStatus.delivered
    ).scalar()

    # Total de pedidos enviados
    shipped_orders = db.query(func.count(Order.order_id)).filter(
        Order.status == OrderStatus.shipped
    ).scalar()

    # Total de pedidos aprobados
    approved_orders = db.query(func.count(Order.order_id)).filter(
        Order.status == OrderStatus.approved
    ).scalar()

    # Total de pedidos cancelados
    cancelled_orders = db.query(func.count(Order.order_id)).filter(
        Order.status == OrderStatus.cancelled
    ).scalar()
    
    # Pedidos pendientes de validacion
    pending_orders = db.query(func.count(Order.order_id)).filter(
        Order.status == OrderStatus.pending_validation
    ).scalar()

    # INGRESOS
    # Calcular revenue total de ordenes completadas
    # Solo se cuentan pedidos en estados: approved, shipped, delivered
    total_revenue = db.query(func.sum(Order.total_amount)).filter(
        Order.status.in_([
            OrderStatus.approved,
            OrderStatus.shipped,
            OrderStatus.delivered
        ])
    ).scalar() or 0  # Usar 0 si no hay pedidos completados
    
    # Calcular ganancia total estimada
    total_profit = db.query(func.sum(Order.order_profit)).filter(
        Order.status.in_([
            OrderStatus.approved,
            OrderStatus.shipped,
            OrderStatus.delivered
        ])
    ).scalar() or 0
    
    return DashboardStats(
        total_users=total_users,
        total_customers=total_customers,
        total_sellers=total_sellers,
        total_marketing=total_marketing,
        total_products=total_products,
        total_orders=total_orders,
        delivered_orders=delivered_orders,
        shipped_orders=shipped_orders,
        approved_orders=approved_orders,
        cancelled_orders=cancelled_orders,
        pending_orders=pending_orders,
        total_revenue=float(total_revenue),
        total_profit=float(total_profit),
        low_stock_count=low_stock_count,
        out_of_stock_count=out_of_stock_count
    )

"""Obtiene estadisticas simplificadas para el dashboard de vendedores y marketing"""
def get_seller_marketing_dashboard_stats(db: Session, current_user: User) -> SellerMarketingDashboardStats:
    # Obtiene estadisticas simplificadas para el dashboard de vendedores y marketing
    # Si no es admin, filtramos por sus grupos de venta
    
    # Obtener IDs de grupos del usuario
    group_ids = []
    if current_user.role == UserRole.marketing:
        from db.base import GroupMarketingManager
        group_ids = [g.sales_group_id for g in db.query(GroupMarketingManager).filter(GroupMarketingManager.marketing_id == current_user.user_id).all()]
    elif current_user.role == UserRole.seller:
        from db.base import GroupSeller
        group_ids = [g.sales_group_id for g in db.query(GroupSeller).filter(GroupSeller.seller_id == current_user.user_id).all()]

    # Query base para pedidos
    from db.base import CustomerInfo
    order_query = db.query(func.count(Order.order_id))
    
    if current_user.role != UserRole.admin:
        # Unir con CustomerInfo para filtrar por sales_group_id
        order_query = order_query.join(CustomerInfo, Order.customer_id == CustomerInfo.customer_id).filter(CustomerInfo.sales_group_id.in_(group_ids))

    # Pedidos por estado
    pending_orders = order_query.filter(Order.status == OrderStatus.pending_validation).scalar()
    approved_orders = order_query.filter(Order.status == OrderStatus.approved).scalar()
    shipped_orders = order_query.filter(Order.status == OrderStatus.shipped).scalar()
    delivered_orders = order_query.filter(Order.status == OrderStatus.delivered).scalar()
    cancelled_orders = order_query.filter(Order.status == OrderStatus.cancelled).scalar()
    
    # INVENTARIO (Global por ahora, o podria ser filtrado por productos vendidos por sus grupos si fuera necesario)
    total_products = db.query(func.count(Product.product_id)).filter(Product.is_active == True).scalar()
    low_stock_count = db.query(func.count(Product.product_id)).filter(
        Product.stock_count < 10,
        Product.stock_count > 0,
        Product.is_active == True
    ).scalar()
    out_of_stock_count = db.query(func.count(Product.product_id)).filter(
        Product.stock_count <= 0,
        Product.is_active == True
    ).scalar()
    
    return SellerMarketingDashboardStats(
        pending_orders=pending_orders,
        approved_orders=approved_orders,
        shipped_orders=shipped_orders,
        delivered_orders=delivered_orders,
        cancelled_orders=cancelled_orders,
        total_products=total_products,
        low_stock_count=low_stock_count,
        out_of_stock_count=out_of_stock_count
    )

"""Genera un reporte de ventas para un rango de fechas"""
def get_sales_report(db: Session, start_date: Optional[str] = None, end_date: Optional[str] = None) -> SalesReport:
    # Genera un reporte de ventas para un rango de fechas (Solo por Dia/Mes/Año)
    if not start_date:
        # Default: primer dia del mes actual
        start_date = datetime.now().replace(day=1).strftime("%Y-%m-%d")
    
    if not end_date:
        # Default: hoy
        end_date = datetime.now().strftime("%Y-%m-%d")

    # OBTENER PEDIDOS
    # Solo incluir pedidos completados (approved, shipped, delivered)
    # Filtramos usando func.date() para ignorar las horas
    orders = db.query(Order).filter(
        func.date(Order.created_at) >= start_date,
        func.date(Order.created_at) <= end_date,
        Order.status.in_([
            OrderStatus.approved,
            OrderStatus.shipped,
            OrderStatus.delivered
        ])
    ).order_by(Order.created_at.desc()).all()

    # CALCULAR TOTALES 
    total_orders = len(orders)
    total_revenue = sum(float(order.total_amount) for order in orders)
    total_profit = sum(float(order.order_profit or 0) for order in orders)

    # CONSTRUIR ITEMS DEL REPORTE
    report_items: List[SalesReportItem] = []
    
    for order in orders:
        # Obtener informacion del cliente
        # Buscar en tabla Customer
        customer = db.query(Customer).filter(
            Customer.customer_id == order.customer_id
        ).first()
        
        # Contar items del pedido
        items_count = len(order.items) if order.items else 0

        # Agregar item al reporte
        report_items.append(SalesReportItem(
            order_id=order.order_id,
            customer_name=customer.full_name if customer else "N/A",
            customer_email=customer.email if customer else "N/A",
            order_date=order.created_at.strftime("%Y-%m-%d %H:%M"),
            status=order.status.value,  # Convertir enum a string
            total_amount=float(order.total_amount),
            order_profit=float(order.order_profit or 0),
            items_count=items_count
        ))

    return SalesReport(
        start_date=start_date,
        end_date=end_date,
        total_orders=total_orders,
        total_revenue=total_revenue,
        total_profit=total_profit,
        orders=report_items
    )
