from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import func

from dependencies import get_db, get_current_admin_user
from db.base import User, Order, Product, OrderStatus
from schemas.user import User as UserSchema, UserUpdate
from crud.crud_user import get_users, get_user, update_user, delete_user
from pydantic import BaseModel

router = APIRouter()

# --- Modelos para estadísticas ---

class DashboardStats(BaseModel):
    total_users: int
    total_products: int
    total_orders: int
    pending_orders: int
    total_revenue: float

# --- Gestión de Usuarios ---

@router.get("/users", response_model=List[UserSchema])
def read_all_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Obtiene todos los usuarios (solo administradores)
    """
    users = get_users(db, skip=skip, limit=limit)
    return users

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

# --- Dashboard y Estadísticas ---

@router.get("/dashboard", response_model=DashboardStats)
def get_dashboard_stats(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Obtiene estadísticas del dashboard (solo administradores)
    """
    total_users = db.query(func.count(User.user_id)).scalar()
    total_products = db.query(func.count(Product.product_id)).filter(
        Product.is_active == True
    ).scalar()
    total_orders = db.query(func.count(Order.order_id)).scalar()
    pending_orders = db.query(func.count(Order.order_id)).filter(
        Order.status == OrderStatus.pending_validation
    ).scalar()
    
    # Calcular revenue total de órdenes completadas
    total_revenue = db.query(func.sum(Order.total_amount)).filter(
        Order.status.in_([OrderStatus.delivered, OrderStatus.shipped])
    ).scalar() or 0
    
    return DashboardStats(
        total_users=total_users,
        total_products=total_products,
        total_orders=total_orders,
        pending_orders=pending_orders,
        total_revenue=float(total_revenue)
    )