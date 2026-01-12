"""
Routes para Dashboards y Reportes

Endpoints para obtener estadisticas y reportes del negocio.
Solo accesibles para administradores.

Endpoints:
- GET /dashboard - Estadisticas generales del negocio
- GET /reports/sales - Reporte de ventas por rango de fechas
"""

from fastapi import APIRouter, Depends, Query
from typing import Optional
from sqlalchemy.orm import Session

from dependencies import get_db, get_current_admin_user, get_current_seller_user
from db.base import User
from schemas.dashboards import DashboardStats, SalesReport, SellerMarketingDashboardStats
from crud.crud_dashboard import get_admin_dashboard_stats, get_sales_report, get_seller_marketing_dashboard_stats


router = APIRouter()


@router.get("/dashboard", response_model=DashboardStats)
def get_dashboard_stats(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    # Obtiene estadisticas generales del dashboard
    
    return get_admin_dashboard_stats(db)


@router.get("/dashboard/seller-marketing", response_model=SellerMarketingDashboardStats)
def get_seller_marketing_dashboard_stats_route(
    current_user: User = Depends(get_current_seller_user),
    db: Session = Depends(get_db)
):
    # Obtiene estadisticas del dashboard para vendedores de marketing
    return get_seller_marketing_dashboard_stats(db)


@router.get("/reports/sales", response_model=SalesReport)
def sales_report(
    start_date: Optional[str] = Query(
        None,
        description="Fecha inicio (YYYY-MM-DD). Default: primer dia del mes actual"
    ),
    end_date: Optional[str] = Query(
        None,
        description="Fecha fin (YYYY-MM-DD). Default: hoy"
    ),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    # Genera reporte de ventas por rango de fechas
    return get_sales_report(db, start_date, end_date)
