"""
CRUD para Dashboards y Reportes

Funciones para generar estadísticas y reportes del sistema:
- Dashboard de administrador con métricas generales
- Reporte de ventas con desglose de pedidos
"""

from datetime import datetime
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from db.base import Order, OrderStatus, Product, User, UserRole, Customer
from schemas.dashboards import DashboardStats, SalesReport, SalesReportItem


def get_admin_dashboard_stats(db: Session) -> DashboardStats:
    """
    Obtiene estadísticas generales para el dashboard de administrador
    
    Calcula métricas clave del negocio:
    - Total de usuarios internos y clientes
    - Total de productos y pedidos
    - Ingresos totales (pedidos completados)
    - Productos con bajo inventario
    
    Args:
        db: Sesión de base de datos
        
    Returns:
        DashboardStats con todas las métricas
    """
    
    # === USUARIOS ===
    # Total de usuarios internos (admin, marketing, seller)
    total_users = db.query(func.count(User.user_id)).scalar()
    
    # Total de clientes registrados (tabla separada)
    total_customers = db.query(func.count(Customer.customer_id)).scalar()
    
    # Total de vendedores activos
    total_sellers = db.query(func.count(User.user_id)).filter(
        User.role == UserRole.seller
    ).scalar()
    
    # === PRODUCTOS ===
    # Total de productos activos en catálogo
    total_products = db.query(func.count(Product.product_id)).filter(
        Product.is_active == True
    ).scalar()
    
    # Productos con bajo stock (menos de 10 unidades)
    # Esto es útil para alertas de reabastecimiento
    low_stock_count = db.query(func.count(Product.product_id)).filter(
        Product.stock_count < 10,
        Product.stock_count > 0,  # No contar productos sin stock
        Product.is_active == True
    ).scalar()
    
    # === PEDIDOS ===
    # Total de pedidos históricos
    total_orders = db.query(func.count(Order.order_id)).scalar()
    
    # Pedidos pendientes de asignación a vendedor
    # Estos requieren atención inmediata del admin/marketing
    pending_orders = db.query(func.count(Order.order_id)).filter(
        Order.status == OrderStatus.pending_validation
    ).scalar()
    
    # === INGRESOS ===
    # Calcular revenue total de órdenes completadas
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
        total_products=total_products,
        total_orders=total_orders,
        pending_orders=pending_orders,
        total_revenue=float(total_revenue),
        low_stock_count=low_stock_count
    )


def get_sales_report(
    db: Session,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> SalesReport:
    """
    Genera un reporte de ventas para un rango de fechas
    
    El reporte incluye:
    - Estadísticas agregadas (total de pedidos y revenue)
    - Desglose detallado de cada pedido
    - Información del cliente para cada pedido
    
    Args:
        db: Sesión de base de datos
        start_date: Fecha inicial (formato: "YYYY-MM-DD"). Default: primer día del mes actual
        end_date: Fecha final (formato: "YYYY-MM-DD"). Default: hoy
        
    Returns:
        SalesReport con totales y lista de pedidos
        
    Raises:
        HTTPException 400: Si el formato de fecha es inválido
    """
    
    # === PARSEAR FECHAS ===
    try:
        if start_date:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        else:
            # Default: primer día del mes actual a las 00:00:00
            start_dt = datetime.now().replace(
                day=1, hour=0, minute=0, second=0, microsecond=0
            )

        if end_date:
            # Incluir todo el día final (hasta las 23:59:59)
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
            detail="Formato de fecha inválido. Use YYYY-MM-DD"
        )

    # === OBTENER PEDIDOS ===
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
    ).order_by(Order.created_at.desc()).all()  # Más recientes primero

    # === CALCULAR TOTALES ===
    total_orders = len(orders)
    total_revenue = sum(float(order.total_amount) for order in orders)

    # === CONSTRUIR ITEMS DEL REPORTE ===
    report_items: List[SalesReportItem] = []
    
    for order in orders:
        # Obtener información del cliente
        # IMPORTANTE: Buscar en tabla Customer, no User (después de la separación)
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
