"""
CRUD para Dashboards y Reportes

Funciones para generar estadisticas y reportes del sistema:
- Dashboard de administrador con metricas generales
- Reporte de ventas con desglose de pedidos
"""

from datetime import datetime
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
    
    # PEDIDOS
    # Total de pedidos historicos
    total_orders = db.query(func.count(Order.order_id)).scalar()
    
    # Total de pedidos entregados
    delivered_orders = db.query(func.count(Order.order_id)).filter(
        Order.status == OrderStatus.delivered
    ).scalar()
    
    # Total de pedidos en otros estados (no entregados)
    other_orders = total_orders - delivered_orders
    
    # Pedidos pendientes de asignacion a vendedor
    # Estos requieren atencion inmediata del admin/marketing
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
    
    return DashboardStats(
        total_users=total_users,
        total_customers=total_customers,
        total_sellers=total_sellers,
        total_marketing=total_marketing,
        total_products=total_products,
        total_orders=total_orders,
        delivered_orders=delivered_orders,
        other_orders=other_orders,
        pending_orders=pending_orders,
        total_revenue=float(total_revenue),
        low_stock_count=low_stock_count
    )

"""Obtiene estadisticas simplificadas para el dashboard de vendedores y marketing"""
def get_seller_marketing_dashboard_stats(db: Session) -> SellerMarketingDashboardStats:
    # Obtiene estadisticas simplificadas para el dashboard de vendedores y marketing
    
    # Total de productos activos en catalogo
    total_products = db.query(func.count(Product.product_id)).filter(
        Product.is_active == True
    ).scalar()
    
    # Productos con bajo stock (menos de 10 unidades)
    low_stock_count = db.query(func.count(Product.product_id)).filter(
        Product.stock_count < 10,
        Product.stock_count > 0,  # No contar productos sin stock
        Product.is_active == True
    ).scalar()
    
    # Pedidos pendientes de validacion
    pending_orders = db.query(func.count(Order.order_id)).filter(
        Order.status == OrderStatus.pending_validation
    ).scalar()
    
    return SellerMarketingDashboardStats(
        pending_orders=pending_orders,
        total_products=total_products,
        low_stock_count=low_stock_count
    )

"""Genera un reporte de ventas para un rango de fechas"""
def get_sales_report(db: Session, start_date: Optional[str] = None, end_date: Optional[str] = None) -> SalesReport:
    # Genera un reporte de ventas para un rango de fechas
    try:
        if start_date:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        else:
            # Default: primer dia del mes actual a las 00:00:00
            start_dt = datetime.now().replace(
                day=1, hour=0, minute=0, second=0, microsecond=0
            )

        if end_date:
            # Incluir todo el dia final (hasta las 23:59:59)
            end_dt = datetime.strptime(end_date, "%Y-%m-%d").replace(
                hour=23, minute=59, second=59
            )
        else:
            # Default: hoy a las 23:59:59
            end_dt = datetime.now().replace(
                hour=23, minute=59, second=59
            )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Formato de fecha invalido. Use YYYY-MM-DD"
        )

    # OBTENER PEDIDOS
    # Solo incluir pedidos completados (approved, shipped, delivered)
    # Excluir pedidos pendientes o cancelados
    orders = db.query(Order).filter(
        Order.created_at >= start_dt,
        Order.created_at <= end_dt,
        Order.status.in_([
            OrderStatus.approved,
            OrderStatus.shipped,
            OrderStatus.delivered
        ])
    ).order_by(Order.created_at.desc()).all()  # Mas recientes primero

    # CALCULAR TOTALES 
    total_orders = len(orders)
    total_revenue = sum(float(order.total_amount) for order in orders)

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
            items_count=items_count
        ))

    return SalesReport(
        start_date=start_dt.strftime("%Y-%m-%d"),
        end_date=end_dt.strftime("%Y-%m-%d"),
        total_orders=total_orders,
        total_revenue=total_revenue,
        orders=report_items
    )
