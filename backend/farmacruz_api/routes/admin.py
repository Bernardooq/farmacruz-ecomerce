from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime

from dependencies import get_db, get_current_admin_user
from db.base import User, Order, Product, OrderStatus, CustomerInfo
from schemas.user import User as UserSchema, UserUpdate, UserCreate
from schemas.customer_info import CustomerInfo as CustomerInfoSchema, CustomerInfoUpdate
from crud.crud_user import get_users, get_user, update_user, delete_user, create_user, get_user_by_username, get_user_by_email
from pydantic import BaseModel

router = APIRouter()

# --- Modelos para estadísticas ---

class DashboardStats(BaseModel):
    total_users: int
    total_products: int
    total_orders: int
    pending_orders: int
    total_revenue: float
    low_stock_count: int
    total_customers: int
    total_sellers: int

class SalesReportItem(BaseModel):
    order_id: int
    customer_name: str
    customer_email: str
    order_date: str
    status: str
    total_amount: float
    items_count: int

class SalesReport(BaseModel):
    start_date: str
    end_date: str
    total_orders: int
    total_revenue: float
    orders: List[SalesReportItem]

# --- Gestión de Usuarios ---

@router.get("/users", response_model=List[UserSchema])
def read_all_users(
    skip: int = 0,
    limit: int = 100,
    role: str = None,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Obtiene todos los usuarios con filtro opcional por rol (solo administradores)
    """
    from db.base import UserRole
    
    # Convertir string a enum si se proporciona
    role_filter = None
    if role:
        try:
            role_filter = UserRole(role)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid role: {role}"
            )
    
    users = get_users(db, skip=skip, limit=limit, role=role_filter)
    return users

@router.post("/users", response_model=UserSchema)
def create_new_user(
    user: UserCreate,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Crea un nuevo usuario (solo administradores)
    """
    # Verificar si el username ya existe
    db_user = get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El nombre de usuario ya está registrado"
        )
    
    # Verificar si el email ya existe
    if user.email:
        db_user = get_user_by_email(db, email=user.email)
        if db_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El email ya está registrado"
            )
    
    return create_user(db=db, user=user)

@router.get("/users/{user_id}", response_model=UserSchema)
def read_user_by_id(
    user_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Obtiene un usuario específico por ID (solo administradores)
    """
    user = get_user(db, user_id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    return user

@router.put("/users/{user_id}", response_model=UserSchema)
def update_user_info(
    user_id: int,
    user_update: UserUpdate,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Actualiza información de un usuario (solo administradores)
    """
    user = update_user(db, user_id=user_id, user=user_update)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    return user

@router.delete("/users/{user_id}")
def delete_user_account(
    user_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Elimina un usuario (solo administradores)
    """
    if user_id == current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No puedes eliminar tu propia cuenta"
        )
    
    user = delete_user(db, user_id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    return {"message": "Usuario eliminado exitosamente"}

# --- Gestión de Customer Info ---

@router.get("/users/{user_id}/customer-info", response_model=CustomerInfoSchema)
def read_user_customer_info(
    user_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Obtiene la información de cliente de un usuario específico (solo administradores)
    """
    customer_info = db.query(CustomerInfo).filter(
        CustomerInfo.user_id == user_id
    ).first()
    
    if not customer_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Información de cliente no encontrada"
        )
    
    return customer_info

@router.put("/users/{user_id}/customer-info", response_model=CustomerInfoSchema)
def update_user_customer_info(
    user_id: int,
    customer_info_update: CustomerInfoUpdate,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Actualiza o crea la información de cliente de un usuario específico (solo administradores)
    """
    # Verificar que el usuario existe
    user = get_user(db, user_id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    customer_info = db.query(CustomerInfo).filter(
        CustomerInfo.user_id == user_id
    ).first()
    
    if not customer_info:
        # Crear nuevo registro si no existe
        customer_info = CustomerInfo(
            user_id=user_id,
            business_name=customer_info_update.business_name or '',
            address=customer_info_update.address,
            rfc=customer_info_update.rfc
        )
        db.add(customer_info)
    else:
        # Actualizar campos existentes
        update_data = customer_info_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(customer_info, field, value)
    
    db.commit()
    db.refresh(customer_info)
    return customer_info

# --- Dashboard y Estadísticas ---

@router.get("/dashboard", response_model=DashboardStats)
def get_dashboard_stats(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Obtiene estadísticas del dashboard (solo administradores)
    """
    from db.base import UserRole
    
    total_users = db.query(func.count(User.user_id)).scalar()
    total_customers = db.query(func.count(User.user_id)).filter(
        User.role == UserRole.customer
    ).scalar()
    total_sellers = db.query(func.count(User.user_id)).filter(
        User.role == UserRole.seller
    ).scalar()
    
    total_products = db.query(func.count(Product.product_id)).filter(
        Product.is_active == True
    ).scalar()
    
    # Productos con bajo stock (menos de 10 unidades)
    low_stock_count = db.query(func.count(Product.product_id)).filter(
        Product.stock_count < 10,
        Product.stock_count > 0,
        Product.is_active == True
    ).scalar()
    
    total_orders = db.query(func.count(Order.order_id)).scalar()
    pending_orders = db.query(func.count(Order.order_id)).filter(
        Order.status == OrderStatus.pending_validation
    ).scalar()
    
    # Calcular revenue total de órdenes completadas (approved, shipped, delivered)
    total_revenue = db.query(func.sum(Order.total_amount)).filter(
        Order.status.in_([OrderStatus.approved, OrderStatus.shipped, OrderStatus.delivered])
    ).scalar() or 0
    
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
    # Parse dates
    try:
        if start_date:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        else:
            # Default: primer día del mes actual
            start_dt = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        if end_date:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            # Incluir todo el día final
            end_dt = end_dt.replace(hour=23, minute=59, second=59)
        else:
            # Default: hoy
            end_dt = datetime.now().replace(hour=23, minute=59, second=59)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Formato de fecha inválido. Use YYYY-MM-DD"
        )
    
    # Query orders in date range (only completed orders)
    orders_query = db.query(Order).filter(
        Order.created_at >= start_dt,
        Order.created_at <= end_dt,
        Order.status.in_([OrderStatus.approved, OrderStatus.shipped, OrderStatus.delivered])
    ).order_by(Order.created_at.desc())
    
    orders = orders_query.all()
    
    # Calculate totals
    total_orders = len(orders)
    total_revenue = sum(float(order.total_amount) for order in orders)
    
    # Format orders for report
    report_items = []
    for order in orders:
        # Get customer info
        customer = db.query(User).filter(User.user_id == order.user_id).first()
        
        # Count items
        items_count = len(order.items) if order.items else 0
        
        report_items.append(SalesReportItem(
            order_id=order.order_id,
            customer_name=customer.full_name if customer else "N/A",
            customer_email=customer.email if customer else "N/A",
            order_date=order.created_at.strftime("%Y-%m-%d %H:%M"),
            status=order.status.value,
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
