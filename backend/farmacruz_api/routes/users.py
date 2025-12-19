"""
Routes para Perfil y Configuración de Usuario

Endpoints para que los usuarios gestionen su propio perfil:

PERFIL:
- GET /me - Ver mi perfil
- PUT /me - Actualizar mi perfil

INFORMACIÓN DE CLIENTE:
- GET /me/customer-info - Ver mi información comercial
- PUT /me/customer-info - Actualizar información comercial

UTILIDADES:
- GET /sellers - Lista de vendedores disponibles

Funciona para:
- Customers (gestión de perfil y customer_info)
- Users internos (gestión de perfil básico)
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from dependencies import get_db, get_current_user, get_current_seller_user
from db.base import User, Customer, CustomerInfo, UserRole, GroupSeller
from schemas.user import UserUpdate
from schemas.customer_info import CustomerInfo as CustomerInfoSchema, CustomerInfoUpdate
from crud.crud_user import get_user, update_user
from crud.crud_customer import update_customer

router = APIRouter()


@router.get("/me")
def read_current_user_profile(current_user = Depends(get_current_user)):
    """
    Obtiene el perfil del usuario autenticado actual
    
    Retorna información según el tipo:
    - Customer: customer_id, username, email, full_name, role="customer"
    - User: user_id, username, email, full_name, role=<admin|seller|marketing>
    
    Permisos: Cualquier usuario autenticado
    """
    # === CONVERTIR A DICT SEGÚN TIPO ===
    if isinstance(current_user, Customer):
        user_dict = {
            "customer_id": current_user.customer_id,
            "username": current_user.username,
            "email": current_user.email,
            "full_name": current_user.full_name,
            "is_active": current_user.is_active,
            "role": "customer"
        }
    else:
        user_dict = {
            "user_id": current_user.user_id,
            "username": current_user.username,
            "email": current_user.email,
            "full_name": current_user.full_name,
            "role": current_user.role.value,
            "is_active": current_user.is_active
        }
    
    return JSONResponse(content=user_dict)


@router.put("/me")
def update_current_user_profile(
    user_update: UserUpdate,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Actualiza el perfil del usuario actual
    
    Campos actualizables:
    - email
    - full_name
    - password (se hashea automáticamente)
    
    Permisos: Cualquier usuario autenticado
    
    Raises:
        404: Usuario/Cliente no encontrado
    """
    if isinstance(current_user, Customer):
        # === ACTUALIZAR CUSTOMER ===
        updated = update_customer(
            db, 
            customer_id=current_user.customer_id,
            customer=user_update
        )
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cliente no encontrado"
            )
        return JSONResponse(content={
            "customer_id": updated.customer_id,
            "username": updated.username,
            "email": updated.email,
            "full_name": updated.full_name,
            "is_active": updated.is_active,
            "role": "customer"
        })
    else:
        # === ACTUALIZAR USER ===
        user = update_user(db, user_id=current_user.user_id, user=user_update)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )
        return JSONResponse(content={
            "user_id": user.user_id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role.value,
            "is_active": user.is_active
        })


@router.get("/me/customer-info", response_model=CustomerInfoSchema)
def read_current_user_customer_info(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtiene la información comercial del cliente actual
    
    Incluye:
    - Datos fiscales (RFC, razón social)
    - Direcciones (hasta 3)
    - Grupo de ventas asignado
    - Lista de precios asignada
    
    Permisos: Solo clientes
    
    Raises:
        403: Acceso denegado (usuario no es cliente)
        404: CustomerInfo no encontrado
    """
    # === VERIFICAR QUE SEA UN CLIENTE ===
    if not isinstance(current_user, Customer):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso denegado. Este endpoint es solo para clientes."
        )
    
    customer_id = current_user.customer_id
    
    # === BUSCAR CUSTOMER_INFO ===
    customer_info = db.query(CustomerInfo).filter(
        CustomerInfo.customer_id == customer_id
    ).first()
    
    if not customer_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Información de cliente no encontrada"
        )
    
    return customer_info


@router.put("/me/customer-info", response_model=CustomerInfoSchema)
def update_current_user_customer_info(
    customer_info_update: CustomerInfoUpdate,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Actualiza la información comercial del cliente actual
    
    Campos actualizables:
    - address_1, address_2, address_3 (direcciones)
    - Otros campos comerciales
    
    Nota: price_list_id y sales_group_id solo los puede cambiar admin.
    
    Permisos: Solo clientes
    
    Raises:
        403: Acceso denegado (usuario no es cliente)
        404: CustomerInfo no encontrado
    """
    # === VERIFICAR QUE SEA UN CLIENTE ===
    if not isinstance(current_user, Customer):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso denegado. Este endpoint es solo para clientes."
        )
    
    customer_id = current_user.customer_id
    
    # === BUSCAR Y ACTUALIZAR ===
    customer_info = db.query(CustomerInfo).filter(
        CustomerInfo.customer_id == customer_id
    ).first()
    
    if not customer_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Información de cliente no encontrada"
        )
    
    # Actualizar campos
    update_data = customer_info_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(customer_info, field, value)
    
    db.commit()
    db.refresh(customer_info)
    return customer_info


@router.get("/sellers")
def get_available_sellers(
    current_user = Depends(get_current_seller_user),
    db: Session = Depends(get_db)
):
    """
    Lista de vendedores disponibles según permisos
    
    Retorna vendedores según el rol:
    - Admin: Todos los vendedores activos
    - Marketing: Solo vendedores de sus grupos asignados
    - Seller: N/A (no debería poder ver esto)
    
    Útil para asignar pedidos a vendedores.
    
    Permisos: Admin y Marketing
    
    Returns:
        Lista de dicts con user_id, username, full_name, email
    """
    query = db.query(User).filter(
        User.role == UserRole.seller,
        User.is_active == True
    )
    
    # === FILTRAR POR GRUPOS SI NO ES ADMIN ===
    if current_user.role != UserRole.admin:
        from crud.crud_sales_group import get_user_groups
        
        # Obtener grupos del usuario marketing
        user_groups = get_user_groups(db, current_user.user_id)
        
        if not user_groups:
            # Marketing sin grupos no puede ver vendedores
            return []
        
        # Filtrar vendedores que estén en esos grupos
        seller_ids = db.query(GroupSeller.seller_id).filter(
            GroupSeller.sales_group_id.in_(user_groups)
        ).distinct().all()
        
        seller_ids = [sid[0] for sid in seller_ids]
        query = query.filter(User.user_id.in_(seller_ids))
    
    sellers = query.all()
    
    # === FORMATEAR RESPUESTA ===
    return [{
        "user_id": seller.user_id,
        "username": seller.username,
        "full_name": seller.full_name,
        "email": seller.email
    } for seller in sellers]
