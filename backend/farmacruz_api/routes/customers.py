"""
Routes para Gestión de Clientes (Customers)

Endpoints CRUD para administración de clientes:

CLIENTES:
- GET / - Lista de clientes con customer_info
- GET /{id} - Detalle de cliente
- POST / - Crear cliente
- PUT /{id} - Actualizar cliente
- DELETE /{id} - Eliminar cliente

INFORMACIÓN COMERCIAL:
- GET /{id}/info - Ver customer_info
- PUT /{id}/info - Actualizar/crear customer_info

Permisos: Solo administradores

Nota: Los clientes están separados de usuarios internos.
Ver routes/users.py para perfil del cliente autenticado.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from dependencies import get_db, get_current_admin_user
from db.base import User, Customer, CustomerInfo
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

router = APIRouter(prefix="/customers", tags=["customers"])


@router.get("", response_model=List[CustomerWithInfo])
def get_customers(
    skip: int = Query(0, ge=0, description="Registros a saltar"),
    limit: int = Query(100, ge=1, le=200, description="Máximo de registros"),
    search: Optional[str] = Query(None, description="Buscar por nombre, username o email"),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Lista de clientes con su información comercial
    
    Búsqueda por nombre, username o email.
    Incluye customer_info precargado.
    
    Permisos: Solo administradores
    """
    return crud_customer.get_customers(db, skip=skip, limit=limit, search=search)


@router.get("/{customer_id}", response_model=CustomerWithInfo)
def get_customer(
    customer_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Detalle de un cliente específico
    
    Incluye customer_info precargado.
    
    Permisos: Solo administradores
    
    Raises:
        404: Cliente no encontrado
    """
    customer = crud_customer.get_customer(db, customer_id=customer_id)
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente no encontrado"
        )
    return customer


@router.post("", response_model=CustomerSchema, status_code=status.HTTP_201_CREATED)
def create_customer(
    customer: CustomerCreate,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Crea un nuevo cliente
    
    El customer_id debe ser proporcionado (para sincronización externa).
    
    Validaciones:
    - Username único
    - Email único
    - customer_id único
    
    La contraseña se hashea con Argon2.
    
    Permisos: Solo administradores
    
    Raises:
        400: Username o email ya existe
    """
    # === VALIDAR USERNAME ÚNICO ===
    db_customer = crud_customer.get_customer_by_username(db, username=customer.username)
    if db_customer:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El nombre de usuario ya está registrado"
        )
    
    # === VALIDAR EMAIL ÚNICO ===
    if customer.email:
        db_customer = crud_customer.get_customer_by_email(db, email=customer.email)
        if db_customer:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El email ya está registrado"
            )
    
    return crud_customer.create_customer(db=db, customer=customer)


@router.put("/{customer_id}", response_model=CustomerSchema)
def update_customer(
    customer_id: int,
    customer_update: CustomerUpdate,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Actualiza un cliente existente
    
    Campos actualizables:
    - email, full_name, password, is_active
    
    Permisos: Solo administradores
    
    Raises:
        404: Cliente no encontrado
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


@router.delete("/{customer_id}")
def delete_customer(
    customer_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Elimina un cliente (hard delete)
    
    Validaciones:
    - No puede tener pedidos asociados
    - Si tiene pedidos, debe desactivarse (is_active=False)
    
    También elimina:
    - CustomerInfo (información comercial)
    - Carrito (CASCADE)
    
    Warning:
        Esto es permanente. Para clientes con historial de pedidos,
        usar desactivación (is_active=False) en su lugar.
    
    Permisos: Solo administradores
    
    Raises:
        400: Cliente tiene pedidos asociados (debe desactivarse)
        404: Cliente no encontrado
    """
    from db.base import Order
    
    # === VERIFICAR SI TIENE PEDIDOS ===
    order_count = db.query(Order).filter(
        Order.customer_id == customer_id
    ).count()
    
    if order_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"No se puede eliminar el cliente porque tiene {order_count} pedido(s) asociado(s). "
                "Para mantener el historial de pedidos, desactiva el cliente en su lugar "
                "(establecer is_active=False)."
            )
        )
    
    # === ELIMINAR SI NO TIENE PEDIDOS ===
    customer = crud_customer.delete_customer(db, customer_id=customer_id)
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente no encontrado"
        )
    
    return {"message": "Cliente eliminado exitosamente"}


# ==========================================
# CUSTOMER INFO (Información Comercial)
# ==========================================

@router.get("/{customer_id}/info", response_model=CustomerInfoSchema)
def get_customer_info(
    customer_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Obtiene la información comercial de un cliente
    
    Incluye:
    - Datos fiscales (RFC, razón social)
    - Direcciones (hasta 3)
    - Grupo de ventas
    - Lista de precios
    
    Permisos: Solo administradores
    
    Raises:
        404: CustomerInfo no encontrado
    """
    customer_info = db.query(CustomerInfo).filter(
        CustomerInfo.customer_id == customer_id
    ).first()
    
    if not customer_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Información de cliente no encontrada"
        )
    
    return customer_info


@router.put("/{customer_id}/info", response_model=CustomerInfoSchema)
def update_customer_info(
    customer_id: int,
    customer_info_update: CustomerInfoUpdate,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Actualiza o crea la información comercial de un cliente
    
    Si no existe CustomerInfo, lo crea.
    Si ya existe, actualiza los campos proporcionados.
    
    Campos actualizables:
    - business_name, rfc (datos fiscales)
    - address_1, address_2, address_3 (direcciones)
    - sales_group_id (grupo de ventas)
    - price_list_id (lista de precios)
    
    Permisos: Solo administradores
    
    Raises:
        404: Cliente no encontrado
    """
    # === VERIFICAR QUE EL CLIENTE EXISTA ===
    customer = crud_customer.get_customer(db, customer_id=customer_id)
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente no encontrado"
        )
    
    # === BUSCAR O CREAR CUSTOMER_INFO ===
    customer_info = db.query(CustomerInfo).filter(
        CustomerInfo.customer_id == customer_id
    ).first()
    
    if not customer_info:
        # Crear nuevo CustomerInfo
        customer_info = CustomerInfo(
            customer_id=customer_id,
            business_name=customer_info_update.business_name or '',
            rfc=customer_info_update.rfc,
            sales_group_id=customer_info_update.sales_group_id,
            price_list_id=customer_info_update.price_list_id,
            address_1=customer_info_update.address_1,
            address_2=customer_info_update.address_2,
            address_3=customer_info_update.address_3
        )
        db.add(customer_info)
    else:
        # Actualizar existente
        update_data = customer_info_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if field != 'customer_info_id':  # No actualizar el ID
                setattr(customer_info, field, value)
    
    db.commit()
    db.refresh(customer_info)
    return customer_info
