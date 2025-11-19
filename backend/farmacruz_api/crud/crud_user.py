from datetime import datetime
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from core.security import get_password_hash, verify_password
from db.base import Order, OrderStatus, Product, User, UserRole
from schemas.user import UserCreate, UserUpdate
from schemas.dashboards import DashboardStats, SalesReport, SalesReportItem


def get_user(db: Session, user_id: int) -> Optional[User]:
    """Obtiene un usuario por ID"""
    return db.query(User).filter(User.user_id == user_id).first()

def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """Obtiene un usuario por username"""
    return db.query(User).filter(User.username == username).first()

def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Obtiene un usuario por email"""
    return db.query(User).filter(User.email == email).first()

def get_users(db: Session, skip: int = 0, limit: int = 100, role: Optional[UserRole] = None, search: Optional[str] = None):
    """Obtiene lista de usuarios con filtro opcional por rol y búsqueda por nombre"""
    from sqlalchemy import or_
    
    query = db.query(User)
    
    if role and role != 'admin':
        query = query.filter(User.role == role)
    
    # Búsqueda por nombre completo o username
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                User.full_name.ilike(search_term),
                User.username.ilike(search_term)
            )
        )
    
    return query.offset(skip).limit(limit).all()

def create_user(db: Session, user: UserCreate) -> User:
    """Crea un nuevo usuario"""
    hashed_password = get_password_hash(user.password)
    db_user = User(
        username=user.username,
        email=user.email,
        password_hash=hashed_password,
        full_name=user.full_name,
        role=user.role,
        is_active=True
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user(db: Session, user_id: int, user: UserUpdate) -> Optional[User]:
    """Actualiza un usuario"""
    db_user = get_user(db, user_id)
    if not db_user:
        return None
    
    update_data = user.dict(exclude_unset=True)
    
    # Si se está actualizando la contraseña, hashearla
    if 'password' in update_data and update_data['password']:
        update_data['password_hash'] = get_password_hash(update_data['password'])
        del update_data['password']
    
    for field, value in update_data.items():
        setattr(db_user, field, value)
    
    db.commit()
    db.refresh(db_user)
    return db_user

def delete_user(db: Session, user_id: int) -> Optional[User]:
    """Elimina un usuario"""
    db_user = get_user(db, user_id)
    if db_user:
        db.delete(db_user)
        db.commit()
    return db_user

def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """Autentica un usuario"""
    user = get_user_by_username(db, username)
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


def get_admin_dash(db: Session):
    
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




def get_sales_report_data(start_date: Optional[str], end_date: Optional[str], db: Session) -> SalesReport:
    try:
        if start_date:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        else:
            start_dt = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        if end_date:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
        else:
            end_dt = datetime.now().replace(hour=23, minute=59, second=59)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Formato de fecha inválido. Use YYYY-MM-DD"
        )

    orders = db.query(Order).filter(
        Order.created_at >= start_dt,
        Order.created_at <= end_dt,
        Order.status.in_([
            OrderStatus.approved,
            OrderStatus.shipped,
            OrderStatus.delivered
        ])
    ).order_by(Order.created_at.desc()).all()

    total_orders = len(orders)
    total_revenue = sum(float(order.total_amount) for order in orders)

    report_items: List[SalesReportItem] = []
    for order in orders:
        customer = db.query(User).filter(User.user_id == order.user_id).first()
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
