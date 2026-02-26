"""
Dependencias de FastAPI para FARMACRUZ

Este modulo define las dependencias que se inyectan en los endpoints:
- get_db: Proporciona una sesion de base de datos
- get_current_user: Autentica usuario o cliente desde JWT
- get_current_admin_user: Verifica permisos de administrador
- get_current_seller_user: Verifica permisos de vendedor
"""

from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError

from db.session import SessionLocal
from db.base import User, UserRole
from core.security import decode_access_token
from core import token_blacklist
from crud.crud_user import get_user_by_username

# Esquema de autenticacion OAuth2 con bearer token
# El token se obtiene desde el endpoint /auth/login
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    # Obtiene el usuario autenticado actual desde el token JWT
    from db.base import Customer
    from crud.crud_customer import get_customer_by_username
    
    # Excepcion que se lanza si hay problemas con las credenciales
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudo validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Decodificar el token JWT
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception

    # Verificar que el token no haya sido revocado (logout)
    jti = payload.get("jti")
    if jti and token_blacklist.contains(jti):
        raise credentials_exception
    
    # Extraer informacion del payload
    username: str = payload.get("sub")  # El 'subject' es el username
    user_type: str = payload.get("user_type")  # 'user' o 'customer'
    
    if username is None:
        raise credentials_exception
    
    # Buscar en la tabla correspondiente segun el tipo de usuario
    if user_type == "customer":
        # Buscar en la tabla de clientes
        authenticated_user = get_customer_by_username(db, username=username)
    else:
        # Buscar en la tabla de usuarios internos (admin, marketing, seller)
        authenticated_user = get_user_by_username(db, username=username)
    
    if authenticated_user is None:
        raise credentials_exception
    
    # Verificar que el usuario este activo
    if not authenticated_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuario inactivo"
        )
    
    return authenticated_user


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    # Verifica que el usuario actual este activo
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Usuario inactivo")
    return current_user


async def get_current_admin_user(current_user: User = Depends(get_current_user)) -> User:
    # Verifica que el usuario actual sea administrador
    if current_user.role != UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos de administrador"
        )
    return current_user


async def get_current_seller_user(current_user: User = Depends(get_current_user)) -> User:
    # Verifica que el usuario tenga permisos de vendedor
    if current_user.role not in [UserRole.admin, UserRole.seller, UserRole.marketing]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos de vendedor"
        )
    return current_user