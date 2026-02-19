"""
Routes de Autenticacion

Endpoints para autenticacion y gestion de sesion:
- POST /register - Registrar nuevo usuario interno (admin only)
- POST /login - Login (customers o users internos)
- GET /me - Informacion del usuario actual

Sistema de Autenticacion:
- Soporta tanto Customers como Users internos
- Usa JWT tokens con OAuth2
- Token incluye role y user_type
- Expiracion configurable (default: 30 minutos)

Flujo de Login:
1. Intenta autenticar como Customer
2. Si falla, intenta como User interno
3. Genera token con role apropiado
"""

from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from dependencies import get_db, get_current_user, get_current_admin_user
from core.config import ACCESS_TOKEN_EXPIRE_MINUTES, SYNC_TOKEN_EXPIRE_MINUTES
from core.security import create_access_token, verify_password
from crud.crud_user import authenticate_user, create_user, get_user_by_username, get_user_by_email
from schemas.user import User, UserCreate
from db.base import Customer

router = APIRouter()

"""Schemas de respuesta de token"""
class Token(BaseModel):
    access_token: str
    token_type: str

"""Schemas de datos del token"""
class TokenData(BaseModel):
    username: Optional[str] = None

""" POST /register - Registrar nuevo usuario interno """
@router.post("/register", response_model=User, status_code=status.HTTP_201_CREATED)
def register(
    user: UserCreate,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
):
    # Registra un nuevo usuario interno (admin, marketing, seller)
    # Validar username unico
    db_user = get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El nombre de usuario ya esta registrado"
        )
    
    # Validar email unico
    if user.email:
        db_user = get_user_by_email(db, email=user.email)
        if db_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El email ya esta registrado"
            )
    return create_user(db=db, user=user)

""" POST /login - Login (customers o users internos) """
@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    # Autenticacion con username y password
    authenticated_user = None
    is_customer = False
    
    # Intentar como customer
    customer = db.query(Customer).filter(
        Customer.username == form_data.username
    ).first()
    
    if customer and verify_password(form_data.password, customer.password_hash):
        authenticated_user = customer
        is_customer = True
    
    # Si no es customer, es user
    if not authenticated_user:
        user = authenticate_user(db, form_data.username, form_data.password)
        if user:
            authenticated_user = user
            is_customer = False
    
    # Validar auth
    if not authenticated_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Validar que este activo
    if not authenticated_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuario inactivo. Contacta al administrador."
        )
    
    # Generar token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    if is_customer:
        # Token para Customer
        token_data = {
            "sub": authenticated_user.username,
            "role": "customer",
            "user_type": "customer",
            "customer_id": authenticated_user.customer_id
        }
    else:
        # Token para User interno
        token_data = {
            "sub": authenticated_user.username,
            "role": authenticated_user.role.value,
            "user_type": "user",
            "user_id": authenticated_user.user_id
        }
    
    access_token = create_access_token(
        data=token_data,
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


""" POST /login/sync - Login con token de corta duracion (5 min) para sincronizaciones """
@router.post("/login/sync", response_model=Token)
def login_sync(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    # Siempre es user admin
    user = authenticate_user(db, form_data.username, form_data.password)
    if user:
        authenticated_user = user
    
    # Validar auth
    if not authenticated_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Validar que este activo
    if not authenticated_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuario inactivo. Contacta al administrador."
        )
    
    # Generar token DE CORTA DURACION (5 minutos)
    access_token_expires = timedelta(minutes=SYNC_TOKEN_EXPIRE_MINUTES)
    
    # Token para User interno
    token_data = {
        "sub": authenticated_user.username,
        "role": authenticated_user.role.value,
        "user_type": "user",
        "user_id": authenticated_user.user_id
    }
    
    access_token = create_access_token(
        data=token_data,
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


""" GET /me - Informacion del usuario actual """
@router.get("/me")
def read_users_me(current_user = Depends(get_current_user)):
    # Obtiene informacion del usuario autenticado actual
    if isinstance(current_user, Customer):
        # Es un Customer
        user_dict = {
            "customer_id": current_user.customer_id,
            "username": current_user.username,
            "email": current_user.email,
            "full_name": current_user.full_name,
            "is_active": current_user.is_active,
            "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
            "role": "customer"  # Role explicito para frontend
        }
    else:
        # Es un User interno
        user_dict = {
            "user_id": current_user.user_id,
            "username": current_user.username,
            "email": current_user.email,
            "full_name": current_user.full_name,
            "role": current_user.role.value,  # admin, seller, o marketing
            "is_active": current_user.is_active,
            "created_at": current_user.created_at.isoformat() if current_user.created_at else None
        }
    
    return JSONResponse(content=user_dict)