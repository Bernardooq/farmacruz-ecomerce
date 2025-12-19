"""
Routes de Autenticación

Endpoints para autenticación y gestión de sesión:
- POST /register - Registrar nuevo usuario interno (admin only)
- POST /login - Login (customers o users internos)
- GET /me - Información del usuario actual

Sistema de Autenticación:
- Soporta tanto Customers como Users internos
- Usa JWT tokens con OAuth2
- Token incluye role y user_type
- Expiración configurable (default: 30 minutos)

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

from dependencies import get_db, get_current_user, get_current_admin_user
from core.config import ACCESS_TOKEN_EXPIRE_MINUTES
from core.security import create_access_token, verify_password
from crud.crud_user import authenticate_user, create_user, get_user_by_username, get_user_by_email
from schemas.user import User, UserCreate
from db.base import Customer

router = APIRouter()


class Token(BaseModel):
    """
    Response del endpoint de login
    
    Contiene el JWT access token y el tipo (siempre 'bearer').
    """
    access_token: str
    token_type: str


class TokenData(BaseModel):
    """
    Datos decodificados del token JWT
    
    Usado internamente para validación.
    """
    username: str | None = None


@router.post("/register", response_model=User, status_code=status.HTTP_201_CREATED)
def register(
    user: UserCreate,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
):
    """
    Registra un nuevo usuario interno (admin, marketing, seller)
    
    IMPORTANTE:
    - Este endpoint es para usuarios INTERNOS, no clientes
    - Los clientes se registran por el admin directamente
    - Solo administradores pueden crear usuarios
    
    Validaciones:
    - Username único
    - Email único (si se proporciona)
    - Role válido
    
    Permisos: Solo administradores
    
    Raises:
        400: Username o email ya existe
    """
    # === VALIDAR USERNAME ÚNICO ===
    db_user = get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El nombre de usuario ya está registrado"
        )
    
    # === VALIDAR EMAIL ÚNICO ===
    if user.email:
        db_user = get_user_by_email(db, email=user.email)
        if db_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El email ya está registrado"
            )
    
    return create_user(db=db, user=user)


@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Autenticación con username y password
    
    Retorna un JWT access token válido por ACCESS_TOKEN_EXPIRE_MINUTES.
    
    Flujo de autenticación:
    1. Intenta autenticar como Customer (tabla customers)
    2. Si falla, intenta como User interno (tabla users)
    3. Verifica que el usuario esté activo
    4. Genera token con role apropiado
    
    El token incluye:
    - Customer: role="customer", customer_id
    - User: role=<admin|seller|marketing>, user_id
    
    Args:
        form_data: OAuth2 form (username, password)
    
    Returns:
        Token JWT válido con tipo 'bearer'
    
    Raises:
        401: Credenciales inválidas
        400: Usuario inactivo
    """
    authenticated_user = None
    is_customer = False
    
    # === PASO 1: INTENTAR COMO CUSTOMER ===
    customer = db.query(Customer).filter(
        Customer.username == form_data.username
    ).first()
    
    if customer and verify_password(form_data.password, customer.password_hash):
        authenticated_user = customer
        is_customer = True
    
    # === PASO 2: SI NO ES CUSTOMER, INTENTAR COMO USER ===
    if not authenticated_user:
        user = authenticate_user(db, form_data.username, form_data.password)
        if user:
            authenticated_user = user
            is_customer = False
    
    # === PASO 3: VALIDAR AUTENTICACIÓN ===
    if not authenticated_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # === PASO 4: VERIFICAR QUE ESTÉ ACTIVO ===
    if not authenticated_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuario inactivo. Contacta al administrador."
        )
    
    # === PASO 5: GENERAR TOKEN ===
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


@router.get("/me")
def read_users_me(current_user = Depends(get_current_user)):
    """
    Obtiene información del usuario autenticado actual
    
    Funciona para:
    - Customers (role="customer")
    - Users internos (role=admin|seller|marketing)
    
    La respuesta incluye:
    - Identificador (customer_id o user_id)
    - Información básica (username, email, nombre)
    - Role
    - Estado (is_active)
    - Fecha de creación
    
    Permisos: Cualquier usuario autenticado
    
    Returns:
        Dict con información del usuario actual
    """
    # === CONVERTIR A DICT SEGÚN EL TIPO ===
    
    if isinstance(current_user, Customer):
        # Es un Customer
        user_dict = {
            "customer_id": current_user.customer_id,
            "username": current_user.username,
            "email": current_user.email,
            "full_name": current_user.full_name,
            "is_active": current_user.is_active,
            "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
            "role": "customer"  # Role explícito para frontend
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