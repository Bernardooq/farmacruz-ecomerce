from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from dependencies import get_db, get_current_user
from db.base import User, CustomerInfo
from schemas.user import User as UserSchema, UserUpdate
from schemas.customer_info import CustomerInfo as CustomerInfoSchema, CustomerInfoUpdate
from crud.crud_user import get_user, update_user

router = APIRouter()

# --- Perfil del Usuario Actual ---

@router.get("/me", response_model=UserSchema)
def read_current_user_profile(
    current_user: User = Depends(get_current_user),
):
    """
    Obtiene el perfil del usuario actual
    """
    return current_user

@router.put("/me", response_model=UserSchema)
def update_current_user_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Actualiza el perfil del usuario actual
    """
    user = update_user(db, user_id=current_user.user_id, user=user_update)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    return user

# --- Customer Info del Usuario Actual ---

@router.get("/me/customer-info", response_model=CustomerInfoSchema)
def read_current_user_customer_info(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtiene la información de cliente del usuario actual
    """
    customer_info = db.query(CustomerInfo).filter(
        CustomerInfo.user_id == current_user.user_id
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
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Actualiza la información de cliente del usuario actual
    """
    customer_info = db.query(CustomerInfo).filter(
        CustomerInfo.user_id == current_user.user_id
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
