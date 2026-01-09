"""
Routes de Administracion de Usuarios Internos

Endpoints CRUD para gestion de usuarios del sistema:
- GET /users - Lista de usuarios con filtros
- POST /users - Crear usuario
- GET /users/{id} - Detalle de usuario
- PUT /users/{id} - Actualizar usuario
- DELETE /users/{id} - Eliminar usuario

Permisos: Solo administradores

Nota: Este modulo gestiona usuarios INTERNOS (admin, marketing, seller).
Para clientes, ver routes/customers.py
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from sqlalchemy.orm import Session

from dependencies import get_db, get_current_admin_user
from db.base import User, UserRole
from crud.crud_customer import get_customer_by_email, get_customer_by_username
from schemas.user import User as UserSchema, UserUpdate, UserCreate
from crud.crud_user import (
    get_users, get_user, update_user, delete_user,
    create_user, get_user_by_username, get_user_by_email
)

router = APIRouter()


@router.get("/users", response_model=List[UserSchema])
def read_all_users(
    skip: int = Query(0, ge=0, description="Registros a saltar"),
    limit: int = Query(100, ge=1, le=200, description="Maximo de registros"),
    role: Optional[str] = Query(None, description="Filtrar por rol: admin, marketing, seller"),
    search: Optional[str] = Query(None, description="Buscar por nombre o username"),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    # Lista de usuarios internos con filtros
    role_filter = None
    if role:
        try:
            role_filter = UserRole(role)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Rol invalido: '{role}'. Roles validos: admin, marketing, seller"
            )
    
    users = get_users(db, skip=skip, limit=limit, role=role_filter, search=search)
    return users


@router.post("/users", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
def create_new_user(
    user: UserCreate,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    # Crea un nuevo usuario interno
    # Validar username unico
    db_user = get_user_by_username(db, username=user.username)
    db_customer = get_customer_by_username(db, username=user.username)
    if db_user or db_customer:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El nombre de usuario ya esta registrado"
        )
    
    # Validar email unico
    if user.email:
        db_customer = get_customer_by_email(db, email=user.email)
        db_user = get_user_by_email(db, email=user.email)
        if db_user or db_customer:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El email ya esta registrado"
            )
    
    return create_user(db=db, user=user)


@router.get("/users/{user_id}", response_model=UserSchema)
def read_user_by_id(
    user_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    # Detalle de un usuario especifico
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
    db_customer = get_customer_by_username(db, username=user_update.username) if user_update.username else None
    db_customer_email = get_customer_by_email(db, email=user_update.email) if user_update.email else None
    if  db_customer or db_customer_email:
        raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="El nombre de usuario o email ya esta registrado"
        )

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
    # Elimina un usuario (hard delete)
    from db.base import Order
    
    # No autoeliminacion
    if user_id == current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No puedes eliminar tu propia cuenta"
        )
    
    # Contar pedidos donde el usuario es vendedor asignado
    assigned_orders = db.query(Order).filter(
        Order.assigned_seller_id == user_id
    ).count()
    
    # Contar pedidos donde el usuario hizo la asignacion
    assigned_by_orders = db.query(Order).filter(
        Order.assigned_by_user_id == user_id
    ).count()
    
    total_orders = assigned_orders + assigned_by_orders
    
    if total_orders > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"No se puede eliminar el usuario porque tiene {total_orders} pedido(s) asociado(s) "
                f"({assigned_orders} como vendedor asignado, {assigned_by_orders} como asignador). "
                "Para mantener el historial de pedidos, desactiva el usuario en su lugar "
                "(establecer is_active=False)."
            )
        )
    
    # Eliminar si no tiene pedidos
    user = delete_user(db, user_id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    return {"message": "Usuario eliminado exitosamente"}
