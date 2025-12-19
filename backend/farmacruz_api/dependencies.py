"""
Dependencias de FastAPI para FARMACRUZ

Este módulo define las dependencias que se inyectan en los endpoints:
- get_db: Proporciona una sesión de base de datos
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
from crud.crud_user import get_user_by_username

# Esquema de autenticación OAuth2 con bearer token
# El token se obtiene desde el endpoint /auth/login
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_db() -> Generator:
    """
    Dependency que proporciona una sesión de base de datos
    
    La sesión se cierra automáticamente después de usarse gracias al finally.
    Esto asegura que no haya conexiones colgadas.
    
    Yields:
        Session: Sesión de SQLAlchemy para interactuar con la base de datos
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """
    Obtiene el usuario autenticado actual desde el token JWT
    
    Esta función maneja tanto usuarios internos (User) como clientes (Customer).
    El tipo de usuario se determina por el campo 'user_type' en el payload del JWT.
    
    Args:
        token: Token JWT del header Authorization
        db: Sesión de base de datos
    
    Returns:
        User o Customer: El usuario autenticado
    
    Raises:
        HTTPException 401: Si el token es inválido o el usuario no existe
        HTTPException 400: Si el usuario está inactivo
    """
    from db.base import Customer
    from crud.crud_customer import get_customer_by_username
    
    # Excepción que se lanza si hay problemas con las credenciales
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudo validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Decodificar el token JWT
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception
    
    # Extraer información del payload
    username: str = payload.get("sub")  # El 'subject' es el username
    user_type: str = payload.get("user_type")  # 'user' o 'customer'
    
    if username is None:
        raise credentials_exception
    
    # Buscar en la tabla correspondiente según el tipo de usuario
    if user_type == "customer":
        # Buscar en la tabla de clientes
        authenticated_user = get_customer_by_username(db, username=username)
    else:
        # Buscar en la tabla de usuarios internos (admin, marketing, seller)
        authenticated_user = get_user_by_username(db, username=username)
    
    if authenticated_user is None:
        raise credentials_exception
    
    # Verificar que el usuario esté activo
    if not authenticated_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuario inactivo"
        )
    
    return authenticated_user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Verifica que el usuario actual esté activo
    
    NOTA: Esta verificación es redundante ya que get_current_user
    ya verifica is_active, pero se mantiene por compatibilidad.
    
    Args:
        current_user: Usuario autenticado
    
    Returns:
        User: El usuario activo
    
    Raises:
        HTTPException 400: Si el usuario está inactivo
    """
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Usuario inactivo")
    return current_user


async def get_current_admin_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Verifica que el usuario actual sea administrador
    
    Solo permite acceso a usuarios con rol 'admin'.
    
    Args:
        current_user: Usuario autenticado
    
    Returns:
        User: El usuario administrador
    
    Raises:
        HTTPException 403: Si el usuario no es administrador
    """
    if current_user.role != UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos de administrador"
        )
    return current_user


async def get_current_seller_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Verifica que el usuario tenga permisos de vendedor
    
    Permite acceso a usuarios con rol 'admin', 'seller' o 'marketing'.
    Esto se usa en endpoints donde el vendedor necesita acceso.
    
    Args:
        current_user: Usuario autenticado
    
    Returns:
        User: El usuario con permisos de vendedor
    
    Raises:
        HTTPException 403: Si el usuario no tiene permisos de vendedor
    """
    if current_user.role not in [UserRole.admin, UserRole.seller, UserRole.marketing]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos de vendedor"
        )
    return current_user