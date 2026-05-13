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
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import logging
import httpx

from dependencies import get_db, get_current_user, get_current_admin_user
from core.config import ACCESS_TOKEN_EXPIRE_MINUTES, SYNC_TOKEN_EXPIRE_MINUTES, TURNSTILE_SECRET_KEY
from core.security import create_access_token, verify_password, decode_access_token
from core import token_blacklist
from crud.crud_user import authenticate_user, create_user, get_user_by_username, get_user_by_email
from schemas.user import User, UserCreate
from db.base import Customer

router = APIRouter()

# Configuración de logger para este módulo
logger = logging.getLogger(__name__)

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
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    # Validar Turnstile CAPTCHA (si está configurado)
    if TURNSTILE_SECRET_KEY:
        captcha_token = request.headers.get("X-Turnstile-Token", "")
        
        # Validar contra la API de Cloudflare con estrategia Fail-Open
        try:
            # Siempre intentamos contactar a Cloudflare. 
            # Si el token falta, mandamos un valor dummy para verificar si el servicio está en línea.
            response = httpx.post(
                "https://challenges.cloudflare.com/turnstile/v0/siteverify",
                data={
                    "secret": TURNSTILE_SECRET_KEY,
                    "response": captcha_token or "ping-healthcheck"
                },
                timeout=5.0 # Timeout reducido para no bloquear al usuario en caso de lentitud de red
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Caso 1: El usuario envió un token pero Cloudflare dice que es INVÁLIDO
                # Bloqueamos porque es un posible ataque o token expirado.
                if captcha_token and not result.get("success"):
                    logger.warning(f"Turnstile rechazó el token: {result.get('error-codes')}")
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Verificación CAPTCHA fallida. Intenta de nuevo."
                    )
                
                # Caso 2: NO se envió token y Cloudflare está FUNCIONANDO (respondió 200 OK)
                # Bloqueamos porque el usuario se saltó el captcha intencionalmente.
                elif not captcha_token:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Verificación CAPTCHA requerida"
                    )
                
                # Caso 3: Todo bien (token válido) -> El flujo continúa normal.
            else:
                # Si Cloudflare responde un error 500 o rate limit (429), permitimos el paso por precaución operativa
                logger.warning(f"Turnstile API falló con status {response.status_code}. Permitiendo login por fallback de seguridad.")
                
        except (httpx.RequestError, httpx.TimeoutException) as e:
            # FALLBACK CRÍTICO: Si no se puede contactar a Cloudflare (caída de red, DNS, caída de CF), 
            # permitimos el login para no detener la operación del negocio.
            logger.warning(f"Cloudflare inalcanzable ({type(e).__name__}). Bypass de seguridad activado por resiliencia.")
            pass
    
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
    authenticated_user = authenticate_user(db, form_data.username, form_data.password)
    
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
    
    # Validar que sea admin (sync solo para admins)
    from db.base import UserRole
    if not hasattr(authenticated_user, 'role') or authenticated_user.role != UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo administradores pueden usar el endpoint de sincronizacion"
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


""" POST /logout - Revocar token actual (logout real) """
@router.post("/logout", status_code=status.HTTP_200_OK)
def logout(request: Request, current_user = Depends(get_current_user)):
    """Revoca el token JWT actual agregando su JTI a la blacklist.
    El token queda inmediatamente inutilizable aunque no haya expirado."""
    auth_header = request.headers.get("Authorization", "")
    token = auth_header.removeprefix("Bearer ").strip()
    payload = decode_access_token(token)
    if payload:
        jti = payload.get("jti")
        exp = payload.get("exp")   # unix timestamp — usado para auto-prune
        if jti:
            token_blacklist.add(jti, exp)
    return {"message": "Sesión cerrada exitosamente"}


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