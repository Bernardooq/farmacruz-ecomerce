from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime

from dependencies import get_db, get_current_admin_user
from db.base import User, Order, Product, OrderStatus, CustomerInfo
from schemas.user import User as UserSchema, UserUpdate, UserCreate
from schemas.customer_info import CustomerInfo as CustomerInfoSchema, CustomerInfoUpdate
from schemas.dashboards import DashboardStats, SalesReport, SalesReportItem
from crud.crud_user import get_admin_dash, get_sales_report_data, get_users, get_user, update_user, delete_user, create_user, get_user_by_username, get_user_by_email
from pydantic import BaseModel


router = APIRouter()


@router.get("/dashboard", response_model=DashboardStats)
def get_dashboard_stats(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Obtiene estadísticas del dashboard (solo administradores)
    """
    return get_admin_dash(db)
    


# --- Reportes de Ventas ---

@router.get("/reports/sales", response_model=SalesReport)
def get_sales_report(
    start_date: Optional[str] = Query(None, description="Fecha inicio (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Fecha fin (YYYY-MM-DD)"),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Genera un reporte de ventas por rango de fechas (solo administradores)
    """
    return get_sales_report_data(start_date, end_date, db)
