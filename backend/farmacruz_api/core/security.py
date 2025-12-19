"""
Módulo de seguridad para FARMACRUZ

Aquí se manejan todas las funciones relacionadas con:
- Hash y verificación de contraseñas usando Argon2
- Creación y decodificación de tokens JWT para autenticación
"""

from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from core.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

# Contexto de hashing de contraseñas usando Argon2 (más seguro que bcrypt)
pwd_context = CryptContext(
    schemes=["argon2"], 
    deprecated="auto"
)

def get_password_hash(password: str) -> str:
    """Genera un hash seguro de la contraseña usando Argon2"""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica que una contraseña en texto plano coincida con su hash"""
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Crea un token JWT para autenticación
    
    Args:
        data: Información a incluir en el token (ej: username, user_type)
        expires_delta: Tiempo de expiración personalizado (opcional)
    
    Returns:
        Token JWT codificado como string
    """
    to_encode = data.copy()
    
    # Determinar tiempo de expiración
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Optional[dict]:
    """
    Decodifica y valida un token JWT
    
    Args:
        token: Token JWT a decodificar
    
    Returns:
        Diccionario con los datos del token si es válido, None si no lo es
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        # Token inválido, expirado o manipulado
        return None