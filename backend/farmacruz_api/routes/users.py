"""
Routes para Perfil y Configuracion de Usuario

Endpoints para que los usuarios gestionen su propio perfil:

PERFIL:
- GET /me - Ver mi perfil
- PUT /me - Actualizar mi perfil

INFORMACIoN DE CLIENTE:
- GET /me/customer-info - Ver mi informacion comercial
- PUT /me/customer-info - Actualizar informacion comercial

UTILIDADES:
- GET /sellers - Lista de vendedores disponibles

Funciona para:
- Customers (gestion de perfil y customer_info)
- Users internos (gestion de perfil basico)
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from dependencies import get_db, get_current_user, get_current_seller_user
from db.base import User, Customer, CustomerInfo, UserRole, GroupSeller
from schemas.user import UserUpdate
from schemas.customer_info import CustomerInfo as CustomerInfoSchema, CustomerInfoUpdate
from crud.crud_user import get_sellers, get_sellers_in_marketing_groups, get_user, update_user
from crud.crud_customer import get_customer_info, update_customer

router = APIRouter()

""" GET /me - Obtener perfil del usuario autenticado actual """
@router.get("/me")
def read_current_user_profile(current_user = Depends(get_current_user)):
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

""" PUT /me - Actualizar perfil del usuario autenticado actual """
@router.put("/me")
def update_current_user_profile(user_update: UserUpdate, current_user = Depends(get_current_user),
    db: Session = Depends(get_db)):
    if isinstance(current_user, Customer):
        update_data = user_update.model_dump(exclude_unset=True)

        # Validar que solo se este cambiando la contraseña
        disallowed_fields = set(update_data.keys()) - {'password'}
        if disallowed_fields:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Los clientes solo pueden cambiar su contraseña. No se pueden modificar: {', '.join(disallowed_fields)}"
            )
        
        # Solo permitir cambio de contraseña
        if 'password' not in update_data or not update_data['password']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Debe proporcionar una nueva contraseña"
            )

        updated = update_customer(db, customer_id=current_user.customer_id, customer=user_update)
        if not updated:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente no encontrado")
        return JSONResponse(content={
            "customer_id": updated.customer_id, "username": updated.username, "email": updated.email,
            "full_name": updated.full_name, "is_active": updated.is_active,"role": "customer"})
    elif current_user.role in {UserRole.admin}:
        # === ACTUALIZAR USER ===
        user = update_user(db, user_id=current_user.user_id, user=user_update)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )
        return JSONResponse(content={"user_id": user.user_id, "username": user.username, "email": user.email, 
            "full_name": user.full_name, "role": user.role.value, "is_active": user.is_active})

""" GET /me/customer-info - Obtener la informacion comercial del cliente actual """
@router.get("/me/customer-info", response_model=CustomerInfoSchema)
def read_current_user_customer_info(current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    if not isinstance(current_user, Customer):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acceso denegado. Este endpoint es solo para clientes.")

    customer_id = current_user.customer_id

    customer_info = get_customer_info(db, customer_id)

    if not customer_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Informacion de cliente no encontrada"
        )
    
    return customer_info

"""GET /sellers - Lista de vendedores disponibles segun permisos """
@router.get("/sellers")
def get_available_sellers(current_user = Depends(get_current_seller_user), db: Session = Depends(get_db)):
    if current_user.role == UserRole.seller:
        # Vendedor: solo a si mismo
        sellers = [current_user]
    elif current_user.role == UserRole.marketing:
        sellers = get_sellers_in_marketing_groups(db, current_user.user_id)
    elif current_user.role == UserRole.admin:
        sellers = get_sellers(db)
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso denegado. Solo usuarios internos pueden acceder a esta informacion."
        )
    return [{
        "user_id": seller.user_id,
        "username": seller.username,
        "full_name": seller.full_name,
        "email": seller.email
    } for seller in sellers]
