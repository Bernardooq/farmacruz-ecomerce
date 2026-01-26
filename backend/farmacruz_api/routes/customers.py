"""
Routes para Gestion de Clientes (Customers)

Endpoints CRUD para administracion de clientes:

CLIENTES:
- GET / - Lista de clientes con customer_info
- GET /{id} - Detalle de cliente
- POST / - Crear cliente
- PUT /{id} - Actualizar cliente
- DELETE /{id} - Eliminar cliente

INFORMACIoN COMERCIAL:
- GET /{id}/info - Ver customer_info
- PUT /{id}/info - Actualizar/crear customer_info

Permisos: Solo administradores

Nota: Los clientes estan separados de usuarios internos.
Ver routes/users.py para perfil del cliente autenticado.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from dependencies import get_db, get_current_admin_user
from db.base import User, Customer, CustomerInfo
from crud.crud_order import get_order_count_by_customer
from crud.crud_user import get_user_by_email, get_user_by_username
from schemas.customer import (
    Customer as CustomerSchema,
    CustomerCreate,
    CustomerUpdate,
    CustomerWithInfo
)
from schemas.customer_info import (
    CustomerInfo as CustomerInfoSchema,
    CustomerInfoUpdate
)
from crud import crud_customer

router = APIRouter()

""" GET / - Lista de clientes con customer_info """
@router.get("", response_model=List[CustomerWithInfo])
def get_customers(
    skip: int = Query(0, ge=0, description="Registros a saltar"),
    limit: int = Query(100, ge=1, le=200, description="Maximo de registros"),
    search: Optional[str] = Query(None, description="Buscar por nombre, username o email"),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    # Lista de clientes con su informacion comercial
    return crud_customer.get_customers(db, skip=skip, limit=limit, search=search)

""" GET /{id} - Detalle de cliente """
@router.get("/{customer_id}", response_model=CustomerWithInfo)
def get_customer(
    customer_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    # Detalle de un cliente especifico
    customer = crud_customer.get_customer(db, customer_id=customer_id)
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente no encontrado"
        )
    return customer

""" POST / - Crear cliente """
@router.post("", response_model=CustomerSchema, status_code=status.HTTP_201_CREATED)
def create_customer(
    customer: CustomerCreate,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    # Crea un nuevo cliente
    # Validar username unico en customers y users
    db_customer = crud_customer.get_customer_by_username(db, username=customer.username) 
    db_user = get_user_by_username(db, username=customer.username)
    if db_customer or db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El nombre de usuario ya esta registrado"
        )

    # validar email unico
    """if customer.email:
        db_customer = crud_customer.get_customer_by_email(db, email=customer.email)
        db_user = get_user_by_email(db, email=customer.email)
        if db_customer or db_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El email ya esta registrado"
            )"""
    
    return crud_customer.create_customer(db=db, customer=customer)

""" PUT /{id} - Actualizar cliente """
@router.put("/{customer_id}", response_model=CustomerSchema)
def update_customer(
    customer_id: int,
    customer_update: CustomerUpdate,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    # Actualiza un cliente existente
    # db_user_email = get_user_by_email(db, email=customer_update.email) if customer_update.email else None
    db_user = get_user_by_username(db, username=customer_update.username) if customer_update.username else None
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El nombre de usuario ya esta registrado"
        )
    """
    if  db_user or db_user_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El nombre de usuario o email ya esta registrado"
        )
    """
    customer = crud_customer.update_customer(
        db,
        customer_id=customer_id,
        customer=customer_update
    )
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente no encontrado"
        )
    return customer

""" DELETE /{id} - Eliminar cliente """
@router.delete("/{customer_id}")
def delete_customer(
    customer_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    # Elimina un cliente (hard delete)
    order_count = get_order_count_by_customer(db, customer_id=customer_id)
    
    
    if order_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"No se puede eliminar el cliente porque tiene {order_count} pedido(s) asociado(s). "
                "Para mantener el historial de pedidos, desactiva el cliente en su lugar "
                "(establecer is_active=False)."
            )
        )
    
    # Eliminar si no tiene pedidos asociados
    customer = crud_customer.delete_customer(db, customer_id=customer_id)
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente no encontrado"
        )
    
    return {"message": "Cliente eliminado exitosamente"}


# Customers Info Routes
""" GET /{id}/info - Ver customer_info """
@router.get("/{customer_id}/info", response_model=CustomerInfoSchema)
def get_customer_info(
    customer_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    # Obtiene la informacion comercial de un cliente
    customer_info = crud_customer.get_customer_info(db, customer_id=customer_id)
    
    if not customer_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Informacion de cliente no encontrada"
        )
    
    return customer_info

""" PUT /{id}/info - Actualizar/crear customer_info """
@router.put("/{customer_id}/info", response_model=CustomerInfoSchema)
def update_customer_info(
    customer_id: int,
    customer_info_update: CustomerInfoUpdate,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    # Actualiza o crea la informacion comercial de un cliente create_or_update_customer_info
    customer_info = crud_customer.create_or_update_customer_info(
        db,
        customer_info=customer_info_update,
        customer_id=customer_id
    )

    if not customer_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente no encontrado"
        )
    
    return customer_info