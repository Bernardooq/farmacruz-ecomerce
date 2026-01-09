"""
Schemas para Dashboards y Reportes

Define la estructura de datos para:
- Dashboard de administrador (estadisticas generales)
- Reporte de ventas (con desglose de pedidos)
"""

from pydantic import BaseModel, Field
from typing import List, Optional


class DashboardStats(BaseModel):
    """
    Estadisticas generales para el dashboard de administrador
    
    Muestra metricas clave del negocio en tiempo real.
    """
    total_users: int  # Total de usuarios internos (admin, marketing, seller)
    total_customers: int  # Total de clientes registrados
    total_sellers: int  # Total de vendedores activos
    total_marketing: int  # Total de usuarios marketing activos
    total_products: int  # Total de productos en catalogo
    total_orders: int  # Total de pedidos historicos
    delivered_orders: int  # Total de pedidos entregados (delivered)
    other_orders: int  # Total de pedidos en otros estados (no delivered)
    pending_orders: int  # Pedidos pendientes de asignacion
    total_revenue: float  # Ingresos totales (pedidos completados)
    low_stock_count: int  # Productos con bajo inventario (< 10 unidades)


class SalesReportItem(BaseModel):
    """
    Item individual en el reporte de ventas
    
    Representa un pedido con informacion resumida del cliente.
    """
    order_id: int  # ID del pedido
    customer_name: str  # Nombre completo del cliente
    customer_email: str  # Email del cliente
    order_date: str  # Fecha del pedido (formato: "YYYY-MM-DD HH:MM")
    status: str  # Estado actual del pedido
    total_amount: float  # Monto total del pedido
    items_count: int  # Numero de productos en el pedido


class SalesReport(BaseModel):
    """
    Reporte completo de ventas con totales y desglose
    
    Incluye estadisticas agregadas y lista detallada de pedidos.
    """
    start_date: str  # Fecha inicial del reporte (formato: "YYYY-MM-DD")
    end_date: str  # Fecha final del reporte (formato: "YYYY-MM-DD")
    total_orders: int  # Numero total de pedidos en el periodo
    total_revenue: float  # Ingresos totales en el periodo
    orders: List[SalesReportItem]  # Lista de pedidos con detalles